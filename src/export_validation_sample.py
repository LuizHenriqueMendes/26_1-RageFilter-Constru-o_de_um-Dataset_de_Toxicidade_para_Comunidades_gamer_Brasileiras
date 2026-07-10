#!/usr/bin/env python3
"""
export_validation_sample.py
─────────────────────────────
Gera uma amostra estratificada do dataset rotulado para validacao humana da
rotulacao automatica (anotacao as ciegas, sem usuario/display_name e sem o
rotulo automatico visivel).

Produz dois arquivos:
  - validation_sample.csv: planilha para o(s) anotador(es) preencherem, com
    apenas id + mensagem + colunas vazias (uma por categoria) para marcar.
  - validation_key.csv: gabarito com o rotulo automatico de cada mensagem,
    NAO deve ser mostrado ao anotador. Usado depois para calcular
    precisao/recall/F1 e concordancia entre o automatico e o humano.

As linhas sao embaralhadas e recebem um "id" sequencial novo, de forma que a
ordem nao revele de qual categoria a mensagem foi originalmente sorteada.

Usage:
    python src/export_validation_sample.py
    python src/export_validation_sample.py --sample-size 80 --seed 7
"""

import argparse

import pandas as pd

ALL_CATEGORIES = ["NT", "INS", "ASS", "DO", "AME", "OBS"]


def sample_category(df: pd.DataFrame, category: str, n: int, used: set, seed: int) -> pd.DataFrame:
    mask = (df[f"label_{category}"] == "True") & (~df.index.isin(used))
    pool = df.loc[mask]
    n = min(n, len(pool))
    sampled = pool.sample(n=n, random_state=seed)
    sampled = sampled.copy()
    sampled["sampled_for"] = category
    return sampled


def run(input_path: str, sample_output: str, key_output: str, sample_size: int, ass_size: int | None, seed: int) -> None:
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)

    sizes = {cat: sample_size for cat in ALL_CATEGORIES}
    sizes["ASS"] = ass_size if ass_size is not None else len(df[df["label_ASS"] == "True"])

    used: set = set()
    parts = []
    for cat in ALL_CATEGORIES:
        sampled = sample_category(df, cat, sizes[cat], used, seed)
        used.update(sampled.index)
        parts.append(sampled)
        print(f"[OK] {cat}: {len(sampled)} mensagens amostradas (pedidas: {sizes[cat]})")

    combined = pd.concat(parts)
    combined = combined.sample(frac=1, random_state=seed).reset_index().rename(columns={"index": "original_index"})
    combined.insert(0, "id", range(1, len(combined) + 1))

    annotation_sheet = combined[["id", "message"]].copy()
    for cat in ALL_CATEGORIES:
        annotation_sheet[f"anotador_{cat}"] = ""
    annotation_sheet.to_csv(sample_output, index=False, encoding="utf-8-sig")
    print(f"[OK] {len(annotation_sheet)} mensagens -> {sample_output} (enviar ao(s) anotador(es))")

    key_columns = ["id", "original_index", "sampled_for"] + [f"label_{cat}" for cat in ALL_CATEGORIES]
    key_sheet = combined[key_columns]
    key_sheet.to_csv(key_output, index=False, encoding="utf-8-sig")
    print(f"[OK] gabarito -> {key_output} (NAO enviar ao(s) anotador(es))")


def main():
    parser = argparse.ArgumentParser(description="Gera amostra estratificada para validacao humana da rotulacao automatica.")
    parser.add_argument("--input", default="data/final_chat_labeled.csv", help="CSV rotulado de entrada")
    parser.add_argument("--sample-output", default="data/validation_sample.csv", help="CSV de saida para o(s) anotador(es)")
    parser.add_argument("--key-output", default="data/validation_key.csv", help="CSV de saida com o gabarito (rotulo automatico)")
    parser.add_argument("--sample-size", type=int, default=60, help="Tamanho da amostra por categoria (exceto ASS)")
    parser.add_argument("--ass-size", type=int, default=None, help="Tamanho da amostra para ASS (default: todas as disponiveis)")
    parser.add_argument("--seed", type=int, default=42, help="Seed para reprodutibilidade da amostragem")
    args = parser.parse_args()
    run(args.input, args.sample_output, args.key_output, args.sample_size, args.ass_size, args.seed)


if __name__ == "__main__":
    main()
