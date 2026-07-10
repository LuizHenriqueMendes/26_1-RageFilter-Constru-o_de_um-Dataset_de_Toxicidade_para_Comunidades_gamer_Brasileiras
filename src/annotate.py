#!/usr/bin/env python3
"""
annotate.py
───────────
Rotula final_chat.csv com a taxonomia de toxicidade do TCC (NT, INS, ASS, DO,
AME, OBS em nivel de sentenca; TOXICO, GIRIA_GAMER, NEUTRO em nivel de token),
usando o lexico em lexicon/lexicon.csv. Abordagem baseada em lexico/regras
(sem LLM, sem anotacao manual).

Usage:
    python src/annotate.py
    python src/annotate.py --input data/final_chat.csv --output data/final_chat_labeled.csv
    python src/annotate.py --lexicon lexicon/lexicon.csv
    python src/annotate.py --harassment-window 5min --harassment-min-repeats 3
    python src/annotate.py --report
"""

import argparse
import json
import re
import sys
import unicodedata
import warnings
from collections import Counter

import pandas as pd

# Os padroes de AME/DO usam grupos de captura para alternancia (ex.: (te\s+)?);
# usamos apenas presenca/ausencia de match via str.contains, nao os grupos.
warnings.filterwarnings("ignore", message=".*has match groups.*")


# ── Normalizacao e tokenizacao ────────────────────────────────────────────────

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if unicodedata.category(c) != "Mn")


LEET_MAP = {"4": "a", "3": "e", "1": "i", "0": "o", "5": "s", "7": "t", "8": "b"}
_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _fold_leet_word(word: str) -> str:
    """Converte digitos leetspeak (4,3,1,0,5,7,8) para a letra equivalente,
    mas so dentro de palavras com pelo menos 2 letras e algum digito leet —
    isso evita corromper placares e formatos de partida ("5x0", "1v1", "3v3"),
    que tem so uma letra isolada entre digitos, e nao caracterizam leetspeak."""
    letter_count = sum(1 for c in word if c.isalpha())
    has_leet_digit = any(c in LEET_MAP for c in word)
    if letter_count >= 2 and has_leet_digit:
        return "".join(LEET_MAP.get(c, c) for c in word)
    return word


def fold_leetspeak(s: str) -> str:
    return _WORD_RE.sub(lambda m: _fold_leet_word(m.group()), s)


def normalize_text(s: str) -> str:
    """Lowercase + remocao de acentos + folding de leetspeak, preservando o
    tamanho da string (1 char -> 1 char), para manter o alinhamento de
    offsets entre a mensagem original e a normalizada usado na rotulacao
    em nivel de token."""
    return fold_leetspeak(strip_accents(s).lower())


TOKEN_RE = re.compile(r"@\w+|\w+", re.UNICODE)

DIRECTION_MARKER_RE = re.compile(r"@\w+|\bvoce\b|\btu\b|\bvc\b")
MENTION_RE = re.compile(r"@(\w+)")


# ── Carregamento e compilacao do lexico ───────────────────────────────────────

def load_lexicon(path: str) -> dict:
    df = pd.read_csv(path)
    buckets: dict = {}
    for cat in df["category"].unique():
        sub = df[df["category"] == cat]
        buckets[cat] = {
            "word": sub.loc[sub["type"] == "word", "term"].str.lower().tolist(),
            "word_ambiguous": sub.loc[sub["type"] == "word_ambiguous", "term"].str.lower().tolist(),
            "phrase_pattern": sub.loc[sub["type"] == "phrase_pattern", "term"].tolist(),
        }
    return buckets


def compile_alternation(terms: list[str], anchored: bool = True, suffix_min_len: int = 4):
    """Compila lista de termos em uma unica alternancia regex.

    Termos com >= suffix_min_len caracteres aceitam sufixo (\\w*) para capturar
    flexoes simples (ex.: "idiota" -> "idiotas"). Termos mais curtos (ex.: "bot",
    "gg") usam casamento exato, pois um sufixo livre colidiria com palavras
    comuns nao relacionadas (ex.: "bot" + sufixo casaria "bota", "botao").

    anchored=True  -> busca dentro de uma string maior (mensagem completa)
    anchored=False -> padrao para usar com fullmatch em um token isolado
    """
    if not terms:
        return None
    long_terms = [t for t in terms if len(t) >= suffix_min_len]
    short_terms = [t for t in terms if len(t) < suffix_min_len]
    parts = []
    if long_terms:
        escaped = sorted((re.escape(t) for t in long_terms), key=len, reverse=True)
        parts.append("(?:" + "|".join(escaped) + r")\w*")
    if short_terms:
        escaped = sorted((re.escape(t) for t in short_terms), key=len, reverse=True)
        parts.append("(?:" + "|".join(escaped) + ")")
    combined = "(?:" + "|".join(parts) + ")"
    return re.compile(r"\b" + combined + r"\b") if anchored else re.compile(combined)


def compile_combined(patterns: list[str]):
    """Combina uma lista de padroes de frase (regex bruto) em um unico regex OR."""
    if not patterns:
        return None
    return re.compile("|".join(f"(?:{p})" for p in patterns))


class Lexicon:
    """Estruturas compiladas (busca em mensagem + fullmatch em token) por categoria."""

    def __init__(self, path: str):
        buckets = load_lexicon(path)

        def bucket(cat, key):
            return buckets.get(cat, {}).get(key, [])

        # GIRIA
        self.giria_word_terms = bucket("GIRIA", "word")
        self.giria_phrase_terms = bucket("GIRIA", "phrase_pattern")
        self.giria_word_search = compile_alternation(self.giria_word_terms, anchored=True)
        self.giria_word_full = compile_alternation(self.giria_word_terms, anchored=False)
        self.giria_phrase = compile_combined(self.giria_phrase_terms)
        self.giria_phrase_list = [re.compile(p) for p in self.giria_phrase_terms]

        # INS / DO / OBS (palavra direta + ambigua)
        self.word_search: dict = {}
        self.word_full: dict = {}
        self.amb_search: dict = {}
        self.amb_full: dict = {}
        self.term_lists: dict = {}
        for cat in ("INS", "DO", "OBS"):
            word_terms = bucket(cat, "word")
            amb_terms = bucket(cat, "word_ambiguous")
            self.word_search[cat] = compile_alternation(word_terms, anchored=True)
            self.word_full[cat] = compile_alternation(word_terms, anchored=False)
            self.amb_search[cat] = compile_alternation(amb_terms, anchored=True)
            self.amb_full[cat] = compile_alternation(amb_terms, anchored=False)
            self.term_lists[cat] = word_terms + amb_terms

        # DO tambem possui padroes de frase (ex.: xenofobia regional)
        self.do_phrase_terms = bucket("DO", "phrase_pattern")
        self.do_phrase = compile_combined(self.do_phrase_terms)
        self.do_phrase_list = [re.compile(p) for p in self.do_phrase_terms]

        # AME e exclusivamente padrao de frase
        self.ame_phrase_terms = bucket("AME", "phrase_pattern")
        self.ame_phrase = compile_combined(self.ame_phrase_terms)
        self.ame_phrase_list = [re.compile(p) for p in self.ame_phrase_terms]


def _contains(series: pd.Series, pattern) -> pd.Series:
    if pattern is None:
        return pd.Series(False, index=series.index)
    return series.str.contains(pattern, regex=True, na=False)


# ── Rotulacao em nivel de sentenca ────────────────────────────────────────────

def label_sentences(df: pd.DataFrame, lex: Lexicon, window: str, min_repeats: int) -> pd.DataFrame:
    norm_msg = df["message"].fillna("").map(normalize_text)
    has_direction = _contains(norm_msg, DIRECTION_MARKER_RE)

    # Menções (@usuario) sao mascaradas antes da busca por termos do lexico:
    # nomes de usuario/streamer frequentemente contem substrings que coincidem
    # com termos do lexico (ex.: "@PiranhaAgricola" contem "piranha"), o que
    # geraria falsos positivos nao relacionados ao conteudo da mensagem.
    search_msg = norm_msg.str.replace(MENTION_RE, " ", regex=True)

    label = {}
    for cat in ("INS", "DO", "OBS"):
        word_hit = _contains(search_msg, lex.word_search[cat])
        amb_hit = _contains(search_msg, lex.amb_search[cat]) & has_direction
        label[cat] = word_hit | amb_hit

    label["DO"] = label["DO"] | _contains(search_msg, lex.do_phrase)
    label["AME"] = _contains(search_msg, lex.ame_phrase)
    label["ASS"] = pd.Series(False, index=df.index)

    out = df.copy()
    out["_norm_message"] = norm_msg
    out["_has_direction"] = has_direction
    for cat in ("INS", "DO", "OBS", "AME", "ASS"):
        out[f"label_{cat}"] = label[cat]

    apply_harassment_heuristic(out, window, min_repeats)

    out["label_NT"] = ~(out["label_INS"] | out["label_ASS"] | out["label_DO"] | out["label_AME"] | out["label_OBS"])
    return out


def apply_harassment_heuristic(out: pd.DataFrame, window: str, min_repeats: int) -> None:
    """Marca label_ASS=True para mensagens dentro de uma rajada de ataques
    persistentes e direcionados (mesmo remetente, mesmo alvo mencionado,
    >= min_repeats mensagens dentro da janela temporal `window`).

    Apenas INS e DO entram na Condicao A: OBS e definida na taxonomia como
    "vulgar sem alvo especifico", logo, por definicao, nao caracteriza ataque
    direcionado mesmo quando a mensagem tambem contem uma mencao a alguem."""

    mention = out["message"].fillna("").map(lambda m: MENTION_RE.search(m))
    out["_target"] = mention.map(lambda m: m.group(1).lower() if m else None)

    candidate_mask = (
        (out["label_INS"] | out["label_DO"])
        & out["_has_direction"]
        & out["_target"].notna()
    )
    if not candidate_mask.any():
        out.drop(columns=["_target"], inplace=True)
        return

    candidates = out.loc[candidate_mask, ["channel", "username", "_target", "timestamp"]].copy()
    candidates["timestamp"] = pd.to_datetime(candidates["timestamp"], errors="coerce")
    candidates = candidates.dropna(subset=["timestamp"])

    ass_indices = []
    for _, group in candidates.groupby(["channel", "username", "_target"], sort=False):
        if len(group) < min_repeats:
            continue
        group = group.sort_values("timestamp")
        counts = (
            pd.Series(1, index=group["timestamp"])
            .rolling(window)
            .sum()
            .to_numpy()
        )
        positions = group.index.to_numpy()
        burst = counts >= min_repeats
        if not burst.any():
            continue
        marked = set()
        for i, is_burst in enumerate(burst):
            if is_burst:
                start = max(0, i - min_repeats + 1)
                marked.update(positions[start : i + 1])
        ass_indices.extend(marked)

    if ass_indices:
        out.loc[ass_indices, "label_ASS"] = True
    out.drop(columns=["_target"], inplace=True)


# ── Rotulacao em nivel de token ───────────────────────────────────────────────

def _spans_overlap(a_start: int, a_end: int, spans: list[tuple[int, int]]) -> bool:
    return any(a_start < e and a_end > s for s, e in spans)


def label_tokens_for_row(message: str, norm_message: str, has_direction: bool, lex: Lexicon) -> list:
    if not isinstance(message, str) or not message:
        return []

    phrase_spans: list[tuple[int, int]] = []
    for pat in lex.ame_phrase_list:
        phrase_spans.extend(m.span() for m in pat.finditer(norm_message))
    for pat in lex.do_phrase_list:
        phrase_spans.extend(m.span() for m in pat.finditer(norm_message))

    giria_phrase_spans: list[tuple[int, int]] = []
    for pat in lex.giria_phrase_list:
        giria_phrase_spans.extend(m.span() for m in pat.finditer(norm_message))

    result = []
    for m in TOKEN_RE.finditer(message):
        start, end = m.span()
        tok = m.group()
        norm_tok = norm_message[start:end] if end <= len(norm_message) else normalize_text(tok)

        is_toxic_word = any(
            lex.word_full[cat] is not None and lex.word_full[cat].fullmatch(norm_tok)
            for cat in ("INS", "DO", "OBS")
        )
        is_toxic_amb = has_direction and any(
            lex.amb_full[cat] is not None and lex.amb_full[cat].fullmatch(norm_tok)
            for cat in ("INS", "DO", "OBS")
        )

        if is_toxic_word or is_toxic_amb:
            label = "TOXICO"
        elif _spans_overlap(start, end, phrase_spans):
            label = "TOXICO"
        elif lex.giria_word_full is not None and lex.giria_word_full.fullmatch(norm_tok):
            label = "GIRIA_GAMER"
        elif _spans_overlap(start, end, giria_phrase_spans):
            label = "GIRIA_GAMER"
        else:
            label = "NEUTRO"

        result.append([tok, label])
    return result


def label_tokens(out: pd.DataFrame, lex: Lexicon) -> pd.Series:
    return out.apply(
        lambda row: json.dumps(
            label_tokens_for_row(row["message"], row["_norm_message"], row["_has_direction"], lex),
            ensure_ascii=False,
        ),
        axis=1,
    )


# ── Relatorio ──────────────────────────────────────────────────────────────────

def print_report(out: pd.DataFrame, lex: Lexicon, detailed: bool) -> None:
    total = len(out)
    print(f"\n{'-'*60}")
    print(f"  Total de mensagens: {total:,}")
    print(f"{'-'*60}")
    print("  Distribuicao por categoria (nivel de sentenca, multi-rotulo):")
    for cat in ("NT", "INS", "ASS", "DO", "AME", "OBS"):
        n = int(out[f"label_{cat}"].sum())
        pct = (n / total * 100) if total else 0.0
        print(f"    {cat:<5} {n:>8,}  ({pct:5.2f}%)")

    toxic_mask = out["label_INS"] | out["label_ASS"] | out["label_DO"] | out["label_AME"] | out["label_OBS"]
    n_toxic = int(toxic_mask.sum())
    print(f"\n  Mensagens toxicas (qualquer categoria != NT): {n_toxic:,} ({n_toxic/total*100:.2f}%)")

    multi = (
        out[["label_INS", "label_ASS", "label_DO", "label_AME", "label_OBS"]].astype(int).sum(axis=1) > 1
    )
    print(f"  Mensagens multi-rotulo (mais de uma categoria toxica): {int(multi.sum()):,}")

    token_counts = Counter()
    for tl in out["token_labels"]:
        try:
            pairs = json.loads(tl)
        except (TypeError, ValueError):
            continue
        for _, label in pairs:
            token_counts[label] += 1
    total_tokens = sum(token_counts.values())
    print(f"\n  Distribuicao de tokens (total: {total_tokens:,}):")
    for label in ("TOXICO", "GIRIA_GAMER", "NEUTRO"):
        n = token_counts.get(label, 0)
        pct = (n / total_tokens * 100) if total_tokens else 0.0
        print(f"    {label:<12} {n:>9,}  ({pct:5.2f}%)")

    if detailed:
        print(f"\n  Top termos acionados por categoria:")
        for cat in ("INS", "DO", "OBS"):
            term_counts = Counter()
            for term in lex.term_lists[cat]:
                pat = compile_alternation([term], anchored=True)
                term_counts[term] = int(out["_norm_message"].str.contains(pat, regex=True, na=False).sum())
            top = term_counts.most_common(8)
            print(f"    {cat}: " + ", ".join(f"{t}={n}" for t, n in top if n))
    print(f"{'-'*60}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def run(input_path: str, output_path: str, lexicon_path: str, window: str, min_repeats: int, report: bool) -> None:
    print(f"[*] Carregando lexico de '{lexicon_path}'...")
    lex = Lexicon(lexicon_path)

    print(f"[*] Carregando mensagens de '{input_path}'...")
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)

    print(f"[*] Rotulando {len(df):,} mensagens em nivel de sentenca...")
    out = label_sentences(df, lex, window, min_repeats)

    print(f"[*] Rotulando tokens (TOXICO / GIRIA_GAMER / NEUTRO)...")
    out["token_labels"] = label_tokens(out, lex)

    out.drop(columns=["_norm_message", "_has_direction"], errors="ignore").to_csv(
        output_path, index=False, encoding="utf-8-sig"
    )
    print(f"[OK] Saida -> {output_path}\n")

    print_report(out, lex, detailed=report)


def main():
    parser = argparse.ArgumentParser(description="Rotula final_chat.csv via lexico/regras (sentenca + token).")
    parser.add_argument("--input", default="data/final_chat.csv", help="CSV de entrada (default: data/final_chat.csv)")
    parser.add_argument("--output", default="data/final_chat_labeled.csv", help="CSV de saida rotulado")
    parser.add_argument("--lexicon", default="lexicon/lexicon.csv", help="Caminho do lexico CSV")
    parser.add_argument("--harassment-window", default="5min", help="Janela temporal para heuristica de ASS (default: 5min)")
    parser.add_argument("--harassment-min-repeats", type=int, default=3, help="Repeticoes minimas para ASS (default: 3)")
    parser.add_argument("--report", action="store_true", help="Mostra detalhamento de termos mais acionados por categoria")
    args = parser.parse_args()

    run(
        input_path=args.input,
        output_path=args.output,
        lexicon_path=args.lexicon,
        window=args.harassment_window,
        min_repeats=args.harassment_min_repeats,
        report=args.report,
    )


if __name__ == "__main__":
    main()
