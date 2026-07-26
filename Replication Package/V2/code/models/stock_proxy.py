#!/usr/bin/env python3
"""Build and estimate the normalized cumulative net-flow proxy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from merge_audit import audited_merge
from estimators import fit_model


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NATIONAL_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet"
)
DEFAULT_PANEL = (
    PACKAGE_ROOT
    / "data"
    / "derived"
    / "painel_stock_proxy.parquet"
)
DEFAULT_RESULT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "stock_proxy_result.csv"
)
DEFAULT_SUPPORT = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "stock_proxy_support.csv"
)
DEFAULT_LARGE_CBO_SERIES = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "stock_proxy_large_cbo_series.csv"
)
DEFAULT_STATUS = (
    PACKAGE_ROOT
    / "results"
    / "mechanisms"
    / "stock_proxy_status.json"
)
DEFAULT_REPORT = (
    PACKAGE_ROOT / "results" / "mechanisms" / "STOCK_PROXY.md"
)
START_PERIOD = 202101
PRE_END_PERIOD = 202211
END_PERIOD = 202605
TREATMENT_PERIOD = 202212


def _period_numbers(start_period: int, end_period: int) -> list[int]:
    start = pd.Period(str(start_period), freq="M")
    end = pd.Period(str(end_period), freq="M")
    return [
        int(period.strftime("%Y%m"))
        for period in pd.period_range(start, end, freq="M")
    ]


def build_stock_proxy(
    national_panel: pd.DataFrame,
    *,
    start_period: int = START_PERIOD,
    end_period: int = END_PERIOD,
    pre_end_period: int = PRE_END_PERIOD,
) -> pd.DataFrame:
    required = {
        "cbo_4d",
        "periodo_num",
        "admissoes",
        "desligamentos",
        "included_main",
        "treated_main",
    }
    missing = sorted(required - set(national_panel.columns))
    if missing:
        raise ValueError(f"National panel is missing columns: {missing}")
    source = national_panel.loc[
        national_panel["included_main"].eq(True)
        & national_panel["periodo_num"].between(
            start_period,
            end_period,
        ),
        [
            "cbo_4d",
            "periodo_num",
            "admissoes",
            "desligamentos",
            "treated_main",
        ],
    ].copy()
    source["cbo_4d"] = source["cbo_4d"].astype(str).str.zfill(4)
    if source.duplicated(["cbo_4d", "periodo_num"]).any():
        raise ValueError("National panel contains duplicate CBO-month cells")
    treatment = (
        source[["cbo_4d", "treated_main"]]
        .drop_duplicates()
        .sort_values("cbo_4d")
    )
    if treatment["cbo_4d"].duplicated().any():
        raise ValueError("Treatment is not time invariant within CBO4")
    cbos = treatment["cbo_4d"].tolist()
    periods = _period_numbers(start_period, end_period)
    grid = pd.MultiIndex.from_product(
        [cbos, periods],
        names=["cbo_4d", "periodo_num"],
    ).to_frame(index=False)
    panel = audited_merge(
        grid,
        source.drop(columns="treated_main"),
        merge_id="stock_proxy_grid_to_flows",
        on=["cbo_4d", "periodo_num"],
        how="left",
        validate="one_to_one",
    )
    panel = audited_merge(
        panel,
        treatment,
        merge_id="stock_proxy_attach_treatment",
        on="cbo_4d",
        how="left",
        validate="many_to_one",
    )
    for column in ("admissoes", "desligamentos"):
        panel[column] = panel[column].fillna(0).astype("int64")
        if panel[column].lt(0).any():
            raise ValueError(f"Negative flow found in {column}")
    panel["saldo"] = panel["admissoes"] - panel["desligamentos"]
    panel["gross_flow"] = panel["admissoes"] + panel["desligamentos"]
    panel = panel.sort_values(["cbo_4d", "periodo_num"])
    panel["cumulative_net_flow"] = panel.groupby(
        "cbo_4d",
        sort=False,
    )["saldo"].cumsum()
    base = (
        panel.loc[panel["periodo_num"].eq(start_period)]
        .set_index("cbo_4d")["cumulative_net_flow"]
    )
    panel["base_cumulative_net_flow"] = panel["cbo_4d"].map(base)
    pre_gross = (
        panel.loc[panel["periodo_num"].le(pre_end_period)]
        .groupby("cbo_4d")["gross_flow"]
        .sum()
    )
    panel["pre_gross_flow"] = panel["cbo_4d"].map(pre_gross)
    panel["valid_pre_flow_scale"] = panel["pre_gross_flow"].gt(0)
    panel["cumulative_net_flow_change"] = (
        panel["cumulative_net_flow"]
        - panel["base_cumulative_net_flow"]
    )
    panel["stock_proxy_index"] = np.where(
        panel["valid_pre_flow_scale"],
        (
            100.0
            + 100.0
            * panel["cumulative_net_flow_change"]
            / panel["pre_gross_flow"]
        ),
        np.nan,
    )
    panel["post"] = (
        panel["periodo_num"].ge(TREATMENT_PERIOD).astype("int8")
    )
    panel["post_treat"] = (
        panel["post"] * panel["treated_main"]
    ).astype("int8")
    panel["periodo"] = pd.to_datetime(
        panel["periodo_num"].astype(str),
        format="%Y%m",
    ).dt.strftime("%Y-%m")
    base_index = panel.loc[
        panel["periodo_num"].eq(start_period),
        "stock_proxy_index",
    ]
    if not np.allclose(base_index.dropna(), 100.0):
        raise RuntimeError("Stock proxy is not normalized to 100 at base")
    return panel.reset_index(drop=True)


def build_support(panel: pd.DataFrame) -> pd.DataFrame:
    return (
        panel.groupby(
            ["cbo_4d", "treated_main"],
            as_index=False,
        )
        .agg(
            pre_gross_flow=("pre_gross_flow", "first"),
            base_net_flow=("saldo", "first"),
            final_cumulative_net_flow_change=(
                "cumulative_net_flow_change",
                "last",
            ),
            final_stock_proxy_index=("stock_proxy_index", "last"),
            valid_pre_flow_scale=("valid_pre_flow_scale", "first"),
            observed_months=("periodo_num", "size"),
        )
        .sort_values("pre_gross_flow", ascending=False)
        .reset_index(drop=True)
    )


def estimate_proxy(panel: pd.DataFrame) -> pd.DataFrame:
    result, _ = fit_model(
        panel,
        model_id="stock_proxy_index__principal",
        outcome="stock_proxy_index",
        treatment_term="post_treat",
        estimator="ols",
        fixed_effects=("cbo_4d", "periodo"),
        cluster_variables=("cbo_4d",),
        controls=(),
        principal=True,
    )
    result["bh_adjusted_p_value"] = result["p_value"]
    result["multiplicity_family_size"] = 1
    return pd.DataFrame([result])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_parquet(temporary, index=False)
    os.replace(temporary, path)


def write_report(
    result: pd.DataFrame,
    support: pd.DataFrame,
    path: Path,
) -> None:
    estimate = result.iloc[0]
    nonpositive_base = int(support["base_net_flow"].le(0).sum())
    invalid_scale = int(support["valid_pre_flow_scale"].eq(False).sum())
    lines = [
        "# Task 24 cumulative net-flow proxy",
        "",
        "## Measurement contract",
        "",
        (
            "This outcome is an occupation-size-normalized cumulative "
            "net-flow index, **not an employment-stock level**. It is set "
            "to 100 in January 2021 and scales subsequent cumulative net "
            "flow by each CBO's total gross flow during January "
            "2021-November 2022."
        ),
        "",
        (
            "It does not recover the unobserved initial employment stock "
            "and does not incorporate unregistered exits or any other "
            "employment transition outside Novo CAGED."
        ),
        "",
        (
            f"A literal January-balance ratio is rejected because "
            f"{nonpositive_base} of {len(support)} CBOs have a "
            "non-positive base net flow."
        ),
        "",
        (
            f"{invalid_scale} CBO lacks any pre-treatment gross flow and "
            "therefore remains in the series with a missing index but is "
            "excluded from estimation rather than assigned an artificial "
            "scale."
        ),
        "",
        "## Principal estimate",
        "",
        "| Coefficient | SE | p-value | BH-adjusted p | N | CBO clusters |",
        "|---:|---:|---:|---:|---:|---:|",
        (
            f"| {estimate.coefficient:.6f} | "
            f"{estimate.standard_error:.6f} | "
            f"{estimate.p_value:.6g} | "
            f"{estimate.bh_adjusted_p_value:.6g} | "
            f"{int(estimate.n_obs):,} | "
            f"{int(estimate.minimum_clusters)} |"
        ),
        "",
        (
            "The coefficient is measured in index points. Interpretation "
            "remains descriptive because the national exact-model "
            "pretrend diagnostics fail."
        ),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Task 24 cumulative net-flow proxy."
    )
    parser.add_argument(
        "--national-panel",
        type=Path,
        default=DEFAULT_NATIONAL_PANEL,
    )
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--support", type=Path, default=DEFAULT_SUPPORT)
    parser.add_argument(
        "--large-cbo-series",
        type=Path,
        default=DEFAULT_LARGE_CBO_SERIES,
    )
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    panel = build_stock_proxy(pd.read_parquet(args.national_panel))
    support = build_support(panel)
    result = estimate_proxy(panel)
    top_cbo = support.head(5)["cbo_4d"]
    large_series = panel.loc[
        panel["cbo_4d"].isin(top_cbo),
        [
            "cbo_4d",
            "periodo_num",
            "saldo",
            "cumulative_net_flow_change",
            "pre_gross_flow",
            "stock_proxy_index",
        ],
    ]
    _atomic_parquet(panel, args.panel)
    _atomic_csv(result, args.result)
    _atomic_csv(support, args.support)
    _atomic_csv(large_series, args.large_cbo_series)
    status = {
        "status": "completed",
        "balanced_grid": bool(
            len(panel) == panel["cbo_4d"].nunique() * len(
                _period_numbers(START_PERIOD, END_PERIOD)
            )
        ),
        "cbo_count": int(panel["cbo_4d"].nunique()),
        "month_count": int(panel["periodo_num"].nunique()),
        "panel_rows": int(len(panel)),
        "base_index_min": float(
            panel.loc[
                panel["periodo_num"].eq(START_PERIOD),
                "stock_proxy_index",
            ].min()
        ),
        "base_index_max": float(
            panel.loc[
                panel["periodo_num"].eq(START_PERIOD),
                "stock_proxy_index",
            ].max()
        ),
        "nonpositive_base_net_flow_cbo_count": int(
            support["base_net_flow"].le(0).sum()
        ),
        "invalid_pre_flow_scale_cbo_count": int(
            support["valid_pre_flow_scale"].eq(False).sum()
        ),
        "panel_sha256": _sha256(args.panel),
    }
    _atomic_json(status, args.status)
    write_report(result, support, args.report)
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
