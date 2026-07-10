#!/usr/bin/env python3
"""
export_girias.py
─────────────────
Extrai, ocorrencia a ocorrencia, todos os tokens rotulados como GIRIA_GAMER
no dataset rotulado: o termo especifico, a mensagem onde apareceu, o stream
e a data.

Usage:
    python src/export_girias.py
    python src/export_girias.py --input data/final_chat_labeled.csv --output data/girias_ocorrencias.csv
"""

import argparse
import json

import pandas as pd
from collections import Counter

from export_toxic import is_laugh_word


def run(input_path: str, output_path: str) -> None:
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    df["data"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.date

    rows = []
    skipped_laugh = 0
    for message, stream, data, token_labels_json in zip(
        df["message"], df["channel"], df["data"], df["token_labels"]
    ):
        try:
            pairs = json.loads(token_labels_json)
        except (TypeError, ValueError):
            continue
        for token, label in pairs:
            if label == "GIRIA_GAMER":
                if is_laugh_word(token):
                    skipped_laugh += 1
                    continue
                rows.append((token, message, stream, data))

    out = pd.DataFrame(rows, columns=["termo", "mensagem", "stream", "data"])
    out.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[OK] {len(out):,} ocorrencias de giria exportadas -> {output_path}")
    print(f"     ({skipped_laugh:,} ocorrencias de risada (kkkk/haha/rs/etc.) excluidas)")
    print(f"\n  Top 10 girias mais usadas:")
    for termo, n in Counter(out["termo"].str.lower()).most_common(10):
        print(f"    {termo:<15} {n:,}")


def main():
    parser = argparse.ArgumentParser(description="Exporta ocorrencias de girias (token GIRIA_GAMER) rotuladas.")
    parser.add_argument("--input", default="data/final_chat_labeled.csv", help="CSV rotulado de entrada")
    parser.add_argument("--output", default="data/girias_ocorrencias.csv", help="CSV de saida com as ocorrencias")
    args = parser.parse_args()
    run(args.input, args.output)


if __name__ == "__main__":
    main()
