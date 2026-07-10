#!/usr/bin/env python3
"""
export_toxic.py
────────────────
Extrai do dataset rotulado as mensagens toxicas e/ou nao-toxicas, com
mensagem, canal de origem, data e o(s) tipo(s) de toxicidade.

Usage:
    python src/export_toxic.py
    python src/export_toxic.py --mode non_toxic --output data/non_toxic_messages.csv
    python src/export_toxic.py --mode both
"""

import argparse
import re
import string

import pandas as pd

CATEGORIES = ["INS", "ASS", "DO", "AME", "OBS"]

_LAUGH_RS_RE = re.compile(r"^(rs)+$", re.IGNORECASE)
_LAUGH_HA_RE = re.compile(r"^(?:ha|he|hi|ho){2,}$", re.IGNORECASE)
_LAUGH_HUEHUE_RE = re.compile(r"^huehue+$", re.IGNORECASE)
_PUNCT_STRIP = string.punctuation + "~"


def is_laugh_word(word: str) -> bool:
    w = word.strip(_PUNCT_STRIP).lower()
    if not w:
        return True  # palavra vazia/so pontuacao nao desqualifica a mensagem
    if w == "lol" or _LAUGH_RS_RE.match(w) or _LAUGH_HA_RE.match(w) or _LAUGH_HUEHUE_RE.match(w):
        return True
    if set(w) <= {"k", "s"} and w.count("k") >= 2:
        return True
    return False


def is_pure_laughter(message: str) -> bool:
    """True se a mensagem for composta inteiramente por expressoes de risada
    (kkkk, ksks, haha, rs, huehue, lol, etc.), sem nenhum outro conteudo."""
    words = str(message).split()
    if not words:
        return False
    return all(is_laugh_word(w) for w in words) and any(
        w.strip(_PUNCT_STRIP) for w in words
    )


def _select(df: pd.DataFrame, mask: pd.Series, tipo_default: str | None) -> pd.DataFrame:
    subset = df.loc[mask].copy()

    if tipo_default is None:
        def tipos(row) -> str:
            return ", ".join(cat for cat in CATEGORIES if row[f"label_{cat}"] == "True")

        subset["tipo_toxicidade"] = subset.apply(tipos, axis=1)
    else:
        subset["tipo_toxicidade"] = tipo_default

    subset["data"] = pd.to_datetime(subset["timestamp"], errors="coerce").dt.date

    return subset[["message", "channel", "data", "tipo_toxicidade"]].rename(
        columns={"message": "mensagem", "channel": "stream"}
    )


def run(input_path: str, output_path: str, mode: str, non_toxic_output: str) -> None:
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)

    toxic_mask = pd.Series(False, index=df.index)
    for cat in CATEGORIES:
        toxic_mask |= df[f"label_{cat}"] == "True"

    if mode in ("toxic", "both"):
        out = _select(df, toxic_mask, tipo_default=None)
        out.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"[OK] {len(out):,} mensagens toxicas exportadas -> {output_path}")

    if mode in ("non_toxic", "both"):
        out = _select(df, ~toxic_mask, tipo_default="NT")
        before = len(out)
        out = out[~out["mensagem"].map(is_pure_laughter)]
        removed = before - len(out)
        out.to_csv(non_toxic_output, index=False, encoding="utf-8-sig")
        print(f"[OK] {len(out):,} mensagens nao-toxicas exportadas -> {non_toxic_output}")
        print(f"     ({removed:,} mensagens de risada pura removidas)")


def main():
    parser = argparse.ArgumentParser(description="Exporta mensagens toxicas e/ou nao-toxicas rotuladas.")
    parser.add_argument("--input", default="data/final_chat_labeled.csv", help="CSV rotulado de entrada")
    parser.add_argument("--output", default="data/toxic_messages.csv", help="CSV de saida com as mensagens toxicas")
    parser.add_argument(
        "--non-toxic-output", default="data/non_toxic_messages.csv", help="CSV de saida com as mensagens nao-toxicas"
    )
    parser.add_argument(
        "--mode", choices=["toxic", "non_toxic", "both"], default="toxic",
        help="O que exportar (default: toxic)",
    )
    args = parser.parse_args()
    run(args.input, args.output, args.mode, args.non_toxic_output)


if __name__ == "__main__":
    main()
