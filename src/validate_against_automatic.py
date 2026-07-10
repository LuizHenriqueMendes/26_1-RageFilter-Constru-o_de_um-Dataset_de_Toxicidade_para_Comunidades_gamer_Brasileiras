#!/usr/bin/env python3
"""
validate_against_automatic.py
──────────────────────────────
Consolida as planilhas dos 3 anotadores (data/validation_sample_anotador1.xlsx,
data/validation_sample_anotador2.xlsx, data/validation_sample_anotador3.xlsx) em
um voto majoritario por categoria, e compara esse voto com o rotulo automatico
(data/validation_key.csv) para estimar precisao, recall e F1 da rotulacao
automatica por lexico/regras.

Usage:
    python src/validate_against_automatic.py
"""

import pandas as pd

CATEGORIES = ["NT", "INS", "ASS", "DO", "AME", "OBS"]
ANNOTATOR_FILES = {
    "anotador_1": "data/validation_sample_anotador1.xlsx",
    "anotador_2": "data/validation_sample_anotador2.xlsx",
    "anotador_3": "data/validation_sample_anotador3.xlsx",
}


def load_annotator(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = df.set_index("id")
    out = pd.DataFrame(index=df.index)
    for cat in CATEGORIES:
        col = df[f"anotador_{cat}"]
        out[cat] = col.notna() & (col.astype(str).str.strip().str.lower().isin(["x", "1", "1.0"]))
    return out


def main():
    annotators = {name: load_annotator(path) for name, path in ANNOTATOR_FILES.items()}

    ids = next(iter(annotators.values())).index
    for name, df in annotators.items():
        if not df.index.equals(ids):
            raise ValueError(f"ids de {name} nao coincidem com os demais anotadores")

    # voto majoritario (>=2 de 3) por categoria
    majority = pd.DataFrame(index=ids)
    for cat in CATEGORIES:
        votes = sum(annotators[name][cat].astype(int) for name in annotators)
        majority[cat] = votes >= 2

    no_majority = majority[~majority.any(axis=1)]
    print(f"[INFO] {len(no_majority)} mensagens sem categoria majoritaria (nenhuma categoria com >=2/3 votos)")

    key = pd.read_csv("data/validation_key.csv", dtype=str, keep_default_na=False)
    key["id"] = key["id"].astype(int)
    key = key.set_index("id")
    key = key.loc[ids]
    automatic = pd.DataFrame(index=ids)
    for cat in CATEGORIES:
        automatic[cat] = key[f"label_{cat}"] == "True"

    print("\n=== Precisao / Recall / F1 do rotulo automatico vs. voto majoritario humano ===\n")
    rows = []
    for cat in CATEGORIES:
        human = majority[cat]
        auto = automatic[cat]
        tp = int((human & auto).sum())
        fp = int((~human & auto).sum())
        fn = int((human & ~auto).sum())
        tn = int((~human & ~auto).sum())
        precision = tp / (tp + fp) if (tp + fp) else float("nan")
        recall = tp / (tp + fn) if (tp + fn) else float("nan")
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else float("nan")
        support = int(human.sum())
        rows.append({
            "categoria": cat, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precisao": precision, "recall": recall, "f1": f1, "suporte_humano": support,
        })

    report = pd.DataFrame(rows)
    with pd.option_context("display.float_format", "{:.4f}".format):
        print(report.to_string(index=False))

    report.to_csv("data/validation_report.csv", index=False, encoding="utf-8-sig")
    print("\n[OK] relatorio salvo em data/validation_report.csv")

    overall_tp = report["tp"].sum()
    overall_fp = report["fp"].sum()
    overall_fn = report["fn"].sum()
    micro_p = overall_tp / (overall_tp + overall_fp) if (overall_tp + overall_fp) else float("nan")
    micro_r = overall_tp / (overall_tp + overall_fn) if (overall_tp + overall_fn) else float("nan")
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) else float("nan")
    print(f"\n[MICRO-AVG, exceto NT nao] precisao={micro_p:.4f} recall={micro_r:.4f} f1={micro_f1:.4f}")


if __name__ == "__main__":
    main()
