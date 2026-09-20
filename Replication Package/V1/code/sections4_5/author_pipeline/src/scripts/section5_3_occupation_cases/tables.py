"""Table construction and CSV/Markdown serialization for Section 5.3."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    AGE_LABELS,
    AGE_ORDER,
    CANARIES_BENCHMARK,
    CASE_ORDER,
    CASE_SHORT_LABELS,
)
from .transforms import EXPOSURE_ORDER


EXPOSURE_SHORT = {
    "Exposed: Gradient 3": "G3",
    "Exposed: Gradient 2": "G2",
    "Exposed: Gradient 1": "G1",
    "Minimal Exposure": "exposição mínima",
    "Not Exposed": "não exposto",
    "No score": "sem escore",
}
CONFIDENCE_PT = {
    "high": "Alta",
    "medium": "Moderada",
    "low": "Baixa",
}


def _format_pct_pt(value: float) -> str:
    if pd.isna(value):
        return "—"
    return f"{float(value):.1f}%".replace(".", ",")


def write_table_pair(frame: pd.DataFrame, table_dir: Path, stem: str) -> tuple[Path, Path]:
    """Write one source-of-truth frame to lossless CSV and readable Markdown."""
    table_dir.mkdir(parents=True, exist_ok=True)
    csv_path = table_dir / f"{stem}.csv"
    md_path = table_dir / f"{stem}.md"
    frame.to_csv(csv_path, index=False, float_format="%.10g")
    markdown_frame = frame.copy()
    numeric = markdown_frame.select_dtypes(include=[np.number]).columns
    markdown_frame[numeric] = markdown_frame[numeric].round(3)
    md_path.write_text(markdown_frame.to_markdown(index=False) + "\n", encoding="utf-8")
    return csv_path, md_path


def build_exposure_summary_table(
    exposure_summary: pd.DataFrame,
    dictionary: pd.DataFrame,
) -> pd.DataFrame:
    """Build the compact Portuguese table used in the dissertation body."""
    primary = dictionary[dictionary["primary_included"]].copy()
    sizes = primary.groupby("case_id", observed=True)["cbo_6d"].nunique()
    confidence = (
        primary.groupby("case_id", observed=True)["mapping_confidence"]
        .agg(lambda values: "/".join(dict.fromkeys(CONFIDENCE_PT.get(v, v) for v in values)))
    )
    exposure = exposure_summary.set_index("case_id")
    rows: list[dict[str, object]] = []
    for case_id in CASE_ORDER:
        row = exposure.loc[case_id]
        composition_parts = [
            f"{EXPOSURE_SHORT[category]} {_format_pct_pt(row.get(category, np.nan))}"
            for category in EXPOSURE_ORDER
            if pd.notna(row.get(category, np.nan)) and float(row.get(category, 0.0)) > 0.0001
        ]
        rows.append(
            {
                "Caso ocupacional": CASE_SHORT_LABELS[case_id],
                "CBOs (n)": int(sizes.loc[case_id]),
                "Confiança semântica": confidence.loc[case_id],
                "Benchmark em Canaries": CANARIES_BENCHMARK[case_id],
                "Composição OIT no Brasil": "; ".join(composition_parts),
                "Cobertura do escore OIT": _format_pct_pt(row["score_coverage_pct"]),
                "Admissões pré-tratamento": int(row["pre_admissions"]),
            }
        )
    return pd.DataFrame(rows)


def build_age_terminal_matrix(terminal: pd.DataFrame) -> pd.DataFrame:
    """Pivot the frozen terminal metric to a six-case by age appendix matrix."""
    data = terminal[
        terminal["variant_id"].eq("primary")
        & terminal["dimension"].eq("age")
    ].copy()
    rows: list[dict[str, object]] = []
    for case_id in CASE_ORDER:
        record: dict[str, object] = {
            "case_id": case_id,
            "case_label_pt": CASE_SHORT_LABELS[case_id],
        }
        case = data[data["case_id"].eq(case_id)].set_index(["outcome", "group_id"])
        for outcome in ["admissions", "real_admission_wage"]:
            prefix = "admissions" if outcome == "admissions" else "real_admission_wage"
            for group_id in AGE_ORDER:
                key = (outcome, group_id)
                token = group_id.removeprefix("age_")
                if key in case.index:
                    row = case.loc[key]
                    record[f"{prefix}_{token}_change_pct"] = row["terminal_change_pct"]
                    record[f"{prefix}_{token}_support_status"] = row["support_status"]
                else:
                    record[f"{prefix}_{token}_change_pct"] = np.nan
                    record[f"{prefix}_{token}_support_status"] = "missing"
        rows.append(record)
    return pd.DataFrame(rows)


def build_sensitivity_matrix(
    main_terminal: pd.DataFrame,
    alternative_terminal: pd.DataFrame,
    same_month_terminal: pd.DataFrame,
    raw_wage_terminal: pd.DataFrame,
    cell_winsor_terminal: pd.DataFrame,
) -> pd.DataFrame:
    """Join composition, normalization, and wage sensitivities in one audit matrix."""
    keys = ["case_id", "variant_id", "dimension", "group_id", "outcome"]
    main = main_terminal.copy().rename(
        columns={
            "terminal_change_pct": "main_terminal_change_pct",
            "support_status": "main_support_status",
            "baseline_value": "main_baseline_value",
            "baseline_support": "main_baseline_support",
        }
    )
    keep_main = keys + [
        "main_terminal_change_pct",
        "main_support_status",
        "main_baseline_value",
        "main_baseline_support",
        "terminal_months",
    ]
    alt = alternative_terminal[keys + ["terminal_change_pct", "support_status"]].rename(
        columns={
            "terminal_change_pct": "alternative_normalization_change_pct",
            "support_status": "alternative_support_status",
        }
    )
    same_month = same_month_terminal[
        keys + ["same_month_change_pct", "support_status", "matched_months"]
    ].rename(columns={"support_status": "same_month_support_status"})
    raw_wage = raw_wage_terminal[keys + ["terminal_change_pct", "support_status"]].rename(
        columns={
            "terminal_change_pct": "raw_wage_mean_change_pct",
            "support_status": "raw_wage_support_status",
        }
    )
    cell_winsor = cell_winsor_terminal[
        keys + ["terminal_change_pct", "support_status"]
    ].rename(
        columns={
            "terminal_change_pct": "cell_mean_winsorized_change_pct",
            "support_status": "cell_mean_winsorized_support_status",
        }
    )
    out = (
        main[keep_main]
        .merge(alt, on=keys, how="left", validate="one_to_one")
        .merge(same_month, on=keys, how="left", validate="one_to_one")
        .merge(raw_wage, on=keys, how="left", validate="one_to_one")
        .merge(cell_winsor, on=keys, how="left", validate="one_to_one")
    )
    primary_reference = out[out["variant_id"].eq("primary")][
        ["case_id", "dimension", "group_id", "outcome", "main_terminal_change_pct"]
    ].rename(columns={"main_terminal_change_pct": "primary_reference_change_pct"})
    out = out.merge(
        primary_reference,
        on=["case_id", "dimension", "group_id", "outcome"],
        how="left",
        validate="many_to_one",
    )
    out["composition_delta_pp"] = (
        out["main_terminal_change_pct"] - out["primary_reference_change_pct"]
    )
    out["normalization_delta_pp"] = (
        out["alternative_normalization_change_pct"] - out["main_terminal_change_pct"]
    )
    out["same_month_delta_pp"] = (
        out["same_month_change_pct"] - out["main_terminal_change_pct"]
    )
    out["raw_wage_delta_pp"] = np.where(
        out["outcome"].eq("real_admission_wage"),
        out["raw_wage_mean_change_pct"] - out["main_terminal_change_pct"],
        np.nan,
    )
    out["cell_mean_winsorization_delta_pp"] = np.where(
        out["outcome"].eq("real_admission_wage"),
        out["cell_mean_winsorized_change_pct"] - out["main_terminal_change_pct"],
        np.nan,
    )
    return out.sort_values(keys).reset_index(drop=True)


def annotate_dictionary_for_output(dictionary: pd.DataFrame) -> pd.DataFrame:
    """Add explicit case order and primary/sensitivity role to the frozen mapping."""
    out = dictionary.copy()
    out.insert(0, "case_order", out["case_id"].map({case: index + 1 for index, case in enumerate(CASE_ORDER)}))
    out["case_label_pt"] = out["case_id"].map(CASE_SHORT_LABELS)
    return out.sort_values(["case_order", "primary_included", "cbo_6d"], ascending=[True, False, True])
