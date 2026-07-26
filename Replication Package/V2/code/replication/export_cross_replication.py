#!/usr/bin/env python3
"""Export the exact principal sample for independent R replication."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PANEL = PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
DEFAULT_OUTPUT = (
    PACKAGE_ROOT
    / "data"
    / "derived"
    / "cross_replication_input.csv"
)
OUTCOMES = (
    "admissoes",
    "desligamentos",
    "n_movimentacoes",
    "ln_salario_real_adm",
    "asinh_saldo",
)


def build_cross_replication_input(panel: pd.DataFrame) -> pd.DataFrame:
    required = {
        "cbo_4d",
        "periodo",
        "periodo_num",
        "post",
        "treated_main",
        "included_main",
        *OUTCOMES,
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"National panel is missing columns: {missing}")
    sample = panel.loc[
        panel["included_main"].eq(True),
        [
            "cbo_4d",
            "periodo",
            "periodo_num",
            "post",
            "treated_main",
            *OUTCOMES,
        ],
    ].copy()
    sample["cbo_4d"] = sample["cbo_4d"].astype(str).str.zfill(4)
    sample["treatment"] = sample["treated_main"].astype(int)
    sample["post"] = sample["post"].astype(int)
    sample["post_treat"] = sample["post"] * sample["treatment"]
    sample = sample.drop(columns="treated_main").sort_values(
        ["cbo_4d", "periodo_num"]
    )
    if sample.duplicated(["cbo_4d", "periodo_num"]).any():
        raise RuntimeError("Cross-replication sample has duplicate cells")
    if len(sample) != 22_049 or sample["cbo_4d"].nunique() != 341:
        raise RuntimeError(
            "Cross-replication sample does not match the principal contract"
        )
    return sample.reset_index(drop=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the exact principal sample for R."
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sample = build_cross_replication_input(pd.read_parquet(args.panel))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(f"{args.output.suffix}.tmp")
    sample.to_csv(temporary, index=False)
    os.replace(temporary, args.output)
    print(
        json.dumps(
            {
                "cbo_clusters": int(sample["cbo_4d"].nunique()),
                "months": int(sample["periodo"].nunique()),
                "rows": int(len(sample)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
