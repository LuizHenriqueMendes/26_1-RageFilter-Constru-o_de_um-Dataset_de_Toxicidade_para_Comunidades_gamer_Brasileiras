#!/usr/bin/env python3
"""
filter_and_merge.py
───────────────────
Filters ALL CSV files in a folder (removes bots, commands, spam),
then merges the clean results into a single output file.

Usage:
    python src/filter_and_merge.py                                # reads CSVs from data/chat_logs
    python src/filter_and_merge.py --folder ./data/chat_logs      # specific folder
    python src/filter_and_merge.py --output data/final_chat.csv   # custom output name
    python src/filter_and_merge.py --add-bots mybot,otherbot
    python src/filter_and_merge.py --keep-commands                # skip !command removal
    python src/filter_and_merge.py --report                       # show per-file stats
    python src/filter_and_merge.py --min-length 3                 # drop messages shorter than N chars
"""

import argparse
import glob
import os
import re
import sys
import pandas as pd
from collections import Counter


# ── Known bot usernames (case-insensitive exact match) ───────────────────────
DEFAULT_BOT_NAMES: set[str] = {
    "nightbot", "streamlabs", "streamelements", "moobot",
    "botisimo", "fossabot", "wizebot", "coebot",
    "deepbot", "phantombot", "cloudbot", "pretzelbot",
    "anotherttvviewer", "creatisbot", "soundalerts",
    "sery_bot", "kofistreambot", "lurxx", "buttsbot",
    "commanderroot", "comettv", "electricallongboard",
    "logviewer", "streamcapturebot", "staysafebot",
    "twitchstatistics", "winstonbot", "pokemoncommunitygame",
    "own3d", "streamelementsbot",
    # Contas descartaveis identificadas em campanha de spam coordenado
    # ("Live Pix" repetido), canal zagowt, 2026-05-18:
    "marcelo9898vida", "nsnjt", "gabrielmarques2009", "renan201022",
    "r9kaa", "edgar_3502w", "soarex8804",
}

COMMAND_PATTERNS: list[re.Pattern] = [
    re.compile(r"^\s*[!/]\w"),
    re.compile(r"^\s*\.\w"),
    re.compile(r"^\s*\+\w"),
    re.compile(r"(?i)^\s*!+\w+"),
]

PROPAGANDA_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)(twitch\.tv/|youtube\.com/|discord\.gg/|kick\.com/|tiktok\.com/)"),
    re.compile(r"(?i)(follow\s+me|check\s+out\s+my|sub\s+to\s+me|my\s+channel|my\s+stream)"),
    re.compile(r"(?i)(is\s+raiding|has\s+raided|welcome\s+the\s+raid|just\s+raided)"),
    re.compile(r"[^a-zA-Z0-9\s]{6,}"),
    re.compile(r"(?i)(get\s+free\s+(subs|followers|viewers)|free\s+followers)"),
    re.compile(r"(?i)(i\s+make\s+\$[\d,]+|earn\s+money|click\s+here|buy\s+followers)"),
    # Any URL (catches sponsor links like alura.com.br, hotmart.com, etc.)
    re.compile(r"https?://\S+"),
    re.compile(r"\b\w+\.(com|com\.br|gg|tv|io|net|org|co)\b"),
]

# Broadcaster messages matching ANY of these = removed as stream noise / ad
BROADCASTER_REMOVE_PATTERNS: list[re.Pattern] = [
    # Sponsor / promo links
    re.compile(r"https?://\S+"),
    re.compile(r"\b\w+\.(com|com\.br|gg|tv|io|net|org|co)\b"),
    re.compile(r"(?i)(conheça|acesse|saiba mais|aproveite|desconto|cupom|oferta|parceiro|patrocin|inteligência artificial|\bIA\b)"),
    # Stream config/info posts  (sensitivity, DPI, resolution, settings)
    re.compile(r"(?i)(sensi|sensit|dpi|resolução|res(olution)?|crosshair|config|low\s*graphic|hz\b|fps\b|monitor)"),
    re.compile(r"(?i)(sens\s*:|\bdpi\b|\bres\b\s*:)"),
    # Pure stream mechanics: short tokens like "15s", "!next", timers
    re.compile(r"^\s*\d+s\s*$"),           # e.g. "15s"
    re.compile(r"^\s*\d+m\s*$"),           # e.g. "5m"
    re.compile(r"^\s*\d+:\d+\s*$"),        # e.g. "1:30"
]

# Broadcaster messages matching ANY of these = ALWAYS removed, even if keep patterns match
# These are automated/templated messages, not genuine chat
BROADCASTER_ALWAYS_REMOVE: list[re.Pattern] = [
    # Sub anniversary: "Obrigado @user por fazer parte da tribo por X meses!"
    re.compile(r"(?i)obrigado\s+@\w+\s+por\s+fazer\s+parte"),
    # English equivalent
    re.compile(r"(?i)thank\s+you\s+@\w+\s+for\s+being\s+a\s+sub"),
    # Generic: "@user ... por X meses" — sub milestone template
    re.compile(r"(?i)@\w+.{0,40}\bpor\s+\d+\s+mes(es)?\b"),
    re.compile(r"(?i)@\w+.{0,40}\bfor\s+\d+\s+months?\b"),
    # Sub welcome: "Agora você é um guerreiro ... @user!"
    re.compile(r"(?i)agora\s+você\s+é\s+um\s+guerreiro"),
    re.compile(r"(?i)(livre\s+dos\s+ads|gaupoints|emotes\s+sem\s+moderação)"),
    # Generic sub welcome templates (other streamers)
    re.compile(r"(?i)(bem[- ]vindo.{0,20}@\w+|welcome.{0,20}@\w+.{0,30}sub)"),
]

# Broadcaster messages matching ANY of these = KEEP (genuine human messages)
# Note: use strict word boundaries to avoid false positives like "discord.gg" matching "gg"
BROADCASTER_KEEP_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)(obrigad|valeu|vlw|thank|tmj|kkkk|haha|lol|XD|<3|❤|👏|🎉)"),
    re.compile(r"(?i)(?<![./\w])\bgg\b(?![./\w])"),  # "gg" standalone, not part of a URL
    re.compile(r"@\w+"),                    # mentions = talking to someone
]

BOT_USERNAME_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)bot$"),
    re.compile(r"(?i)^bot"),
    re.compile(r"(?i)_bot_"),
    re.compile(r"(?i)streamlabs"),
    re.compile(r"(?i)nightbot"),
]

# Combined pattern for vectorized bot detection
_BOT_PATTERN_RE = re.compile(r"(?i)(bot$|^bot|_bot_|streamlabs|nightbot)")

MESSAGE_CANDIDATES   = ["message", "Message", "body", "content", "text", "chat", "comment"]
USERNAME_CANDIDATES  = ["username", "user", "author", "commenter", "chatter", "Username", "User"]
TIMESTAMP_CANDIDATES = ["time", "timestamp", "created_at", "date", "datetime", "Time", "Timestamp"]
USERTYPE_CANDIDATES  = ["user_type", "user_badges", "badges", "type", "role"]

# User types that should be filtered out (broadcaster ads/propaganda)
FILTERED_USER_TYPES  = {"broadcaster"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for name in candidates:
        if name in df.columns:
            return name
    return None


def load_csv(path: str) -> pd.DataFrame:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, dtype=str)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode: {path}")


def _any_match(series: pd.Series, patterns: list[re.Pattern]) -> pd.Series:
    """Vectorized OR across a list of compiled regex patterns."""
    result = pd.Series(False, index=series.index)
    for pat in patterns:
        result |= series.str.contains(pat, na=False)
    return result


def _high_uppercase_ratio(msgs: pd.Series, min_letters: int = 8, threshold: float = 0.80) -> pd.Series:
    """True for messages where >= threshold of Unicode letters are uppercase."""
    def _check(m: str) -> bool:
        letters = [c for c in str(m) if c.isalpha()]
        return len(letters) >= min_letters and sum(c.isupper() for c in letters) / len(letters) >= threshold
    return msgs.apply(_check)


# ── Per-file filter ───────────────────────────────────────────────────────────

def filter_df(
    df: pd.DataFrame,
    bot_names: set[str],
    keep_commands: bool,
    keep_propaganda: bool,
    min_length: int = 0,
) -> tuple[pd.DataFrame, Counter]:
    """Return (clean_df, reason_counts) using vectorized pandas operations."""

    msg_col      = find_column(df, MESSAGE_CANDIDATES)
    user_col     = find_column(df, USERNAME_CANDIDATES)
    usertype_col = find_column(df, USERTYPE_CANDIDATES)

    if not msg_col:
        return df, Counter()

    msgs   = df[msg_col].fillna("").astype(str).str.strip()
    users  = df[user_col].fillna("").astype(str).str.strip().str.lower() if user_col else pd.Series("", index=df.index)
    utypes = df[usertype_col].fillna("").astype(str).str.strip().str.lower() if usertype_col else pd.Series("", index=df.index)

    removal = pd.Series(None, index=df.index, dtype=object)

    # 1. Broadcaster messages
    bcast = utypes.str.contains("broadcaster", na=False)
    if bcast.any():
        bcast_msgs  = msgs[bcast]
        always_rm   = _any_match(bcast_msgs, BROADCASTER_ALWAYS_REMOVE)
        keep_it     = (~always_rm) & _any_match(bcast_msgs, BROADCASTER_KEEP_PATTERNS)
        remove_it   = _any_match(bcast_msgs, BROADCASTER_REMOVE_PATTERNS)
        noise_local = always_rm | (~keep_it & remove_it)
        removal[bcast & noise_local.reindex(df.index, fill_value=False)] = "broadcaster_noise"

    unprocessed = removal.isna()

    # 2. Bot usernames
    if user_col:
        is_bot_mask = unprocessed & (
            users.isin(bot_names) | users.str.contains(_BOT_PATTERN_RE, na=False)
        )
        removal[is_bot_mask] = "bot"
        unprocessed = removal.isna()

    # 3. Chat commands (!command, /command, .command, +command)
    if not keep_commands:
        is_cmd = unprocessed & msgs.str.match(r"\s*[!/\.+]\w", na=False)
        removal[is_cmd] = "command"
        unprocessed = removal.isna()

    # 4. Spam / propaganda
    if not keep_propaganda:
        is_spam    = unprocessed & _any_match(msgs, PROPAGANDA_PATTERNS)
        high_upper = unprocessed & _high_uppercase_ratio(msgs)
        removal[is_spam | high_upper] = "propaganda"
        unprocessed = removal.isna()

    # 5. Minimum message length
    if min_length > 0:
        removal[unprocessed & (msgs.str.len() < min_length)] = "too_short"

    counts = Counter(removal.dropna())
    clean  = df[removal.isna()]
    return clean, counts


def remove_near_duplicates(df: pd.DataFrame, window_seconds: float) -> tuple[pd.DataFrame, int]:
    """Remove mensagens quase-duplicadas: mesmo canal, mesmo usuario, mesma
    mensagem, capturadas com poucos segundos de diferenca. Diferente do
    drop_duplicates exato (que exige timestamp identico), isso cobre o caso
    comum de o mesmo evento de chat ser capturado duas vezes pelo scraper
    com um timestamp ligeiramente diferente. Mantem a primeira ocorrencia."""
    msg_col  = find_column(df, MESSAGE_CANDIDATES)
    user_col = find_column(df, USERNAME_CANDIDATES)
    ts_col   = find_column(df, TIMESTAMP_CANDIDATES)

    if not (msg_col and user_col and ts_col) or "channel" not in df.columns:
        return df, 0

    ts = pd.to_datetime(df[ts_col], errors="coerce", utc=True)
    valid = ts.notna()
    if not valid.any():
        return df, 0

    tmp = pd.DataFrame({
        "_ts":   ts[valid],
        "_chan": df.loc[valid, "channel"],
        "_user": df.loc[valid, user_col],
        "_msg":  df.loc[valid, msg_col],
    })
    tmp.sort_values(["_chan", "_user", "_msg", "_ts"], inplace=True)
    delta = tmp.groupby(["_chan", "_user", "_msg"])["_ts"].diff().dt.total_seconds()
    drop_idx = tmp.index[delta.notna() & (delta <= window_seconds)]

    if len(drop_idx) == 0:
        return df, 0
    return df.drop(index=drop_idx), len(drop_idx)


# ── Main ──────────────────────────────────────────────────────────────────────

def run(folder: str, output: str, extra_bots: set[str], keep_commands: bool,
        keep_propaganda: bool, report: bool, min_length: int = 0,
        near_dup_window: float = 2.0) -> None:

    # Find all CSVs in folder, excluding the output file itself
    pattern = os.path.join(folder, "*.csv")
    all_files = sorted(glob.glob(pattern))
    files = [f for f in all_files if os.path.abspath(f) != os.path.abspath(output)]

    if not files:
        print(f"[ERR] No CSV files found in '{folder}'")
        sys.exit(1)

    bot_names = DEFAULT_BOT_NAMES | {b.lower() for b in extra_bots}

    print(f"\n[*] Found {len(files)} CSV file(s) in '{folder}'\n")

    clean_frames = []
    total_in = total_out = 0
    grand_counts: Counter = Counter()

    for path in files:
        fname = os.path.basename(path)
        try:
            df = load_csv(path)
        except Exception as e:
            print(f"  [!] {fname} -- {e}")
            continue

        clean, counts = filter_df(df, bot_names, keep_commands, keep_propaganda, min_length)
        removed = sum(counts.values())
        total_in  += len(df)
        total_out += len(clean)
        grand_counts += counts

        clean["_source_file"] = fname
        clean_frames.append(clean)

        status = f"{len(df):>6,} -> {len(clean):>6,}  (-{removed:,})"
        print(f"  [+] {fname:<40} {status}")

        if report and counts:
            for reason, n in counts.items():
                print(f"       |-- {reason}: {n}")

    if not clean_frames:
        print("[ERR] No data remained after filtering.")
        sys.exit(1)

    # ── Merge clean frames ────────────────────────────────────────────────────
    merged = pd.concat(clean_frames, ignore_index=True)

    # Deduplicate (excluding the helper column)
    subset = [c for c in merged.columns if c != "_source_file"]
    before_dedup = len(merged)
    merged.drop_duplicates(subset=subset, inplace=True)
    dupes = before_dedup - len(merged)

    merged, near_dupes = remove_near_duplicates(merged, near_dup_window)

    # Sort by timestamp if available
    ts_col = find_column(merged, TIMESTAMP_CANDIDATES)
    if ts_col:
        try:
            merged[ts_col] = pd.to_datetime(merged[ts_col], format="ISO8601")
            merged.sort_values(ts_col, inplace=True)
            merged[ts_col] = merged[ts_col].astype(str)
        except Exception:
            try:
                merged[ts_col] = pd.to_datetime(merged[ts_col])
                merged.sort_values(ts_col, inplace=True)
                merged[ts_col] = merged[ts_col].astype(str)
            except Exception:
                pass

    merged.to_csv(output, index=False, encoding="utf-8-sig")

    # ── Summary ───────────────────────────────────────────────────────────────
    pct = ((total_in - len(merged)) / total_in * 100) if total_in else 0.0
    print(f"\n{'-'*55}")
    print(f"  Files processed : {len(clean_frames)}")
    print(f"  Total rows in   : {total_in:>8,}")
    print(f"  Removed - ads   : {grand_counts.get('broadcaster_noise', 0):>8,}")
    print(f"  Removed - bots  : {grand_counts.get('bot', 0):>8,}")
    print(f"  Removed - cmds  : {grand_counts.get('command', 0):>8,}")
    print(f"  Removed - spam  : {grand_counts.get('propaganda', 0):>8,}")
    if min_length > 0:
        print(f"  Removed - short : {grand_counts.get('too_short', 0):>8,}  (< {min_length} chars)")
    print(f"  Duplicates      : {dupes:>8,}")
    print(f"  Near-duplicates : {near_dupes:>8,}  (<= {near_dup_window}s, mesmo usuario/mensagem)")
    print(f"  Final rows      : {len(merged):>8,}  ({100 - pct:.1f}% kept)")
    print(f"{'-'*55}")
    print(f"  [OK] Output -> {output}\n")


def main():
    parser = argparse.ArgumentParser(description="Filter all chat CSVs in a folder, then merge.")
    parser.add_argument("--folder",          default="./data/chat_logs",     help="Folder containing CSV files (default: ./data/chat_logs)")
    parser.add_argument("--output",          default="data/final_chat.csv",  help="Output filename (default: data/final_chat.csv)")
    parser.add_argument("--add-bots",        default="",                help="Comma-separated extra bot usernames")
    parser.add_argument("--keep-commands",   action="store_true",       help="Do not remove !command messages")
    parser.add_argument("--keep-propaganda", action="store_true",       help="Do not remove spam/promo messages")
    parser.add_argument("--report",          action="store_true",       help="Show per-file removal breakdown")
    parser.add_argument("--min-length",      type=int, default=0,       help="Drop messages shorter than N characters (default: disabled)")
    parser.add_argument("--near-dup-window", type=float, default=2.0,   help="Seconds within which same user+message is treated as a near-duplicate (default: 2.0)")
    args = parser.parse_args()

    extra_bots = {b.strip() for b in args.add_bots.split(",") if b.strip()}

    run(
        folder=args.folder,
        output=args.output,
        extra_bots=extra_bots,
        keep_commands=args.keep_commands,
        keep_propaganda=args.keep_propaganda,
        report=args.report,
        min_length=args.min_length,
        near_dup_window=args.near_dup_window,
    )


if __name__ == "__main__":
     main()
