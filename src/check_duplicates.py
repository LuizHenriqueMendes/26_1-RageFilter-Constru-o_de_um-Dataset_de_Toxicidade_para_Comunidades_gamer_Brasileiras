#!/usr/bin/env python3
"""
check_duplicates.py
─────────────────────
Audita duplicatas nos datasets finais exportados (toxic_messages.csv,
non_toxic_messages.csv, girias_ocorrencias.csv) e na fonte rotulada
(final_chat_labeled.csv).

Dois fenomenos sao distintos e reportados separadamente:

1. Duplicata exata nos CSVs exportados (linhas identicas em todas as
   colunas). Como esses exports nao tem username nem horario exato (so a
   data), MUITAS dessas "duplicatas" sao na verdade usuarios diferentes
   mandando a mesma frase curta no mesmo canal no mesmo dia -- nao e bug,
   e perda de granularidade do export.

2. Quase-duplicata na fonte (final_chat_labeled.csv): mesmo canal, mesmo
   usuario, mesma mensagem, com poucos segundos de diferenca. Isso e mais
   provavel de ser duplicacao tecnica real (evento de chat capturado duas
   vezes pelo scraper), e nao repeticao genuina do usuario.

Usage:
    python src/check_duplicates.py
    python src/check_duplicates.py --source-window 2.0
"""

import argparse

import pandas as pd

EXPORT_FILES = ["data/toxic_messages.csv", "data/non_toxic_messages.csv", "data/girias_ocorrencias.csv"]


def audit_export_file(path: str) -> None:
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except FileNotFoundError:
        print(f"  [!] {path} nao encontrado, pulando.")
        return

    dup_mask = df.duplicated(keep=False)
    n_dup_rows = int(dup_mask.sum())
    n_dup_groups = int(df[dup_mask].drop_duplicates().shape[0])

    print(f"\n  {path}")
    print(f"    linhas totais: {len(df):,}")
    print(f"    linhas envolvidas em duplicata exata: {n_dup_rows:,} ({n_dup_rows/len(df)*100:.1f}%)")
    print(f"    grupos de valores repetidos: {n_dup_groups:,}")

    if n_dup_rows:
        top = (
            df[dup_mask]
            .value_counts()
            .head(3)
        )
        print(f"    exemplos mais repetidos:")
        for values, count in top.items():
            row = dict(zip(df.columns, values))
            preview = {k: v for k, v in row.items() if k in ("mensagem", "termo", "stream")}
            print(f"      {count:>4}x  {preview}")


def audit_source_near_duplicates(path: str, window_seconds: float) -> None:
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except FileNotFoundError:
        print(f"  [!] {path} nao encontrado, pulando.")
        return

    df["_ts"] = pd.to_datetime(df["timestamp"], errors="coerce")
    dup_mask = df.duplicated(subset=["channel", "username", "message"], keep=False)
    candidates = df[dup_mask].sort_values(["channel", "username", "message", "_ts"]).copy()

    if candidates.empty:
        print(f"\n  {path}: nenhuma mensagem repetida pelo mesmo usuario.")
        return

    candidates["_delta"] = (
        candidates.groupby(["channel", "username", "message"])["_ts"].diff().dt.total_seconds()
    )
    near = candidates[candidates["_delta"].notna() & (candidates["_delta"] <= window_seconds)]

    print(f"\n  {path}")
    print(f"    mensagens repetidas pelo mesmo usuario (qualquer intervalo): {len(candidates):,}")
    print(f"    dessas, com <= {window_seconds}s de diferenca (provavel duplicata tecnica): {len(near):,}")

    if not near.empty:
        print(f"    exemplos:")
        for _, row in near.head(5).iterrows():
            print(f"      [{row['_delta']:.2f}s] {row['channel']}/{row['username']}: {row['message']!r}")


def run(source_path: str, window_seconds: float) -> None:
    print(f"{'='*70}")
    print("  1) Duplicatas exatas nos CSVs exportados")
    print(f"{'='*70}")
    for path in EXPORT_FILES:
        audit_export_file(path)

    print(f"\n{'='*70}")
    print("  2) Quase-duplicatas na fonte (mesmo usuario/mensagem, poucos segundos)")
    print(f"{'='*70}")
    audit_source_near_duplicates(source_path, window_seconds)
    print()


def main():
    parser = argparse.ArgumentParser(description="Audita duplicatas nos datasets exportados e na fonte.")
    parser.add_argument("--source", default="data/final_chat_labeled.csv", help="CSV fonte rotulado")
    parser.add_argument(
        "--source-window", type=float, default=2.0,
        help="Janela em segundos para considerar quase-duplicata na fonte (default: 2.0)",
    )
    args = parser.parse_args()
    run(args.source, args.source_window)


if __name__ == "__main__":
    main()
