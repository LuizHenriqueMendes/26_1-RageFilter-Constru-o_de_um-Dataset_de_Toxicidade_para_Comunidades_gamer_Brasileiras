#!/usr/bin/env python3
"""
toxicity_by_stream.py
──────────────────────
Calcula a taxa de toxicidade por canal/stream a partir do dataset rotulado,
rankeando do mais ao menos toxico.

Usage:
    python src/toxicity_by_stream.py
    python src/toxicity_by_stream.py --min-messages 1000
    python src/toxicity_by_stream.py --output data/toxicity_by_stream.csv
"""

import argparse

import pandas as pd

CATEGORIES = ["INS", "ASS", "DO", "AME", "OBS"]


def run(input_path: str, output_path: str, min_messages: int) -> None:
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)

    for cat in CATEGORIES:
        df[f"_{cat}"] = (df[f"label_{cat}"] == "True").astype(int)

    df["_toxic"] = (df[[f"_{cat}" for cat in CATEGORIES]].sum(axis=1) > 0).astype(int)

    agg = {"_toxic": "sum", "message": "count"}
    agg.update({f"_{cat}": "sum" for cat in CATEGORIES})

    grouped = df.groupby("channel").agg(agg).rename(
        columns={"message": "total_mensagens", "_toxic": "mensagens_toxicas"}
    )
    grouped = grouped.rename(columns={f"_{cat}": f"{cat.lower()}_count" for cat in CATEGORIES})

    grouped["taxa_toxicidade_pct"] = (grouped["mensagens_toxicas"] / grouped["total_mensagens"] * 100).round(2)
    grouped["volume_suficiente"] = grouped["total_mensagens"] >= min_messages

    grouped = grouped.sort_values("taxa_toxicidade_pct", ascending=False).reset_index()
    grouped = grouped.rename(columns={"channel": "stream"})

    cols = ["stream", "total_mensagens", "mensagens_toxicas", "taxa_toxicidade_pct", "volume_suficiente"]
    cols += [f"{cat.lower()}_count" for cat in CATEGORIES]
    grouped = grouped[cols]

    grouped.to_csv(output_path, index=False, encoding="utf-8-sig")

    assert grouped["total_mensagens"].sum() == len(df)

    qualified = grouped[grouped["volume_suficiente"]]

    print(f"\n{'-'*70}")
    print(f"  Total de canais: {len(grouped)} ({len(qualified)} com >= {min_messages:,} mensagens)")
    print(f"  Total de mensagens: {len(df):,}")
    print(f"{'-'*70}")

    print(f"\n  Top 5 mais toxicos (>= {min_messages:,} mensagens):")
    for _, row in qualified.head(5).iterrows():
        print(f"    {row['stream']:<20} {row['taxa_toxicidade_pct']:>6.2f}%  ({row['mensagens_toxicas']:,}/{row['total_mensagens']:,})")

    print(f"\n  Top 5 menos toxicos (>= {min_messages:,} mensagens):")
    for _, row in qualified.tail(5).iloc[::-1].iterrows():
        print(f"    {row['stream']:<20} {row['taxa_toxicidade_pct']:>6.2f}%  ({row['mensagens_toxicas']:,}/{row['total_mensagens']:,})")

    print(f"\n  [OK] Tabela completa -> {output_path}")
    print(f"{'-'*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Ranking de taxa de toxicidade por canal/stream.")
    parser.add_argument("--input", default="data/final_chat_labeled.csv", help="CSV rotulado de entrada")
    parser.add_argument("--output", default="data/toxicity_by_stream.csv", help="CSV de saida com o ranking")
    parser.add_argument(
        "--min-messages", type=int, default=1000,
        help="Volume minimo de mensagens para um canal entrar no ranking exibido (default: 1000)",
    )
    args = parser.parse_args()
    run(args.input, args.output, args.min_messages)


if __name__ == "__main__":
    main()
