#!/usr/bin/env python3
"""Build the optional Section 5.2.5.b race/color table and dynamic figures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from section4_5_final.config import SOURCE_ROOT, TABLE_DIR  # noqa: E402
from section4_5_final.section5_2_combined_figures import (  # noqa: E402
    OUTPUT_ROOT as COMBINED_OUTPUT_ROOT,
    plot_combined_figure,
)
from section4_5_final.section5_2_dynamic_figures import (  # noqa: E402
    EVENT_TIMES,
    PATH_ROLES,
    build_micro_dimension_results,
    load_main_strict_panel,
)
from section4_5_final.section5_2_tables import (  # noqa: E402
    SECTION5_2_ADDITIONAL_SPECS,
    validate_section5_2_outputs,
    write_heterogeneity_table,
)
from section4_5_final.sources import load_sources  # noqa: E402
from section4_event_study.config import (  # noqa: E402
    NET_FLOW_OUTCOMES,
    REAL_HETEROGENEITY_OUTCOMES,
)
from section4_event_study.data import load_analysis_data  # noqa: E402
from section4_event_study.heterogeneity import (  # noqa: E402
    DIMENSIONS,
    aggregate_micro_group_pairs,
    estimate_heterogeneity,
)
from section4_event_study.treatment import apply_roles, assign_roles  # noqa: E402


DIMENSION = "race_color_b"
GROUPS = list(SECTION5_2_ADDITIONAL_SPECS[DIMENSION]["groups"])
FLOW_OUTCOMES = {
    "ln_admissoes": "Admissões (log)",
    "ln_desligamentos": "Desligamentos (log)",
}
DYNAMIC_OUTCOMES = ["ln_admissoes", "ln_salario_real_adm"]
SOURCE_TABLES = {
    "heterogeneity": SOURCE_ROOT / "final_event_study" / "tables" / "heterogeneity_triple_did_long.csv",
    "heterogeneity_real_wage": SOURCE_ROOT
    / "final_event_study"
    / "tables"
    / "heterogeneity_real_wage_triple_did_long.csv",
    "net_flow_heterogeneity": SOURCE_ROOT
    / "final_event_study"
    / "tables"
    / "net_flow_heterogeneity_long.csv",
}


def log(message: str) -> None:
    print(f"[section5_2_race_color_b] {message}", flush=True)


def _replace_dimension_rows(base: pd.DataFrame, replacement: pd.DataFrame) -> pd.DataFrame:
    kept = base[~base["dimension"].eq(DIMENSION)].copy()
    aligned = replacement.reindex(columns=base.columns)
    return pd.concat([kept, aligned], ignore_index=True)


def _augment_sources(
    sources: dict[str, pd.DataFrame],
    static_results: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    out = {key: value.copy() for key, value in sources.items()}
    for source_key, replacement in static_results.items():
        out[source_key] = _replace_dimension_rows(out[source_key], replacement)
    return out


def _persist_static_source_rows(static_results: dict[str, pd.DataFrame]) -> None:
    for source_key, replacement in static_results.items():
        path = SOURCE_TABLES[source_key]
        current = pd.read_csv(path)
        updated = _replace_dimension_rows(current, replacement)
        updated.to_csv(path, index=False)
        log(f"Updated reproducible source rows in {path}")


def _validate_dynamic_frames(
    coefficients: pd.DataFrame,
    pretrends: pd.DataFrame,
    paths: pd.DataFrame,
) -> None:
    expected_groups = [group_id for group_id, _label in GROUPS]
    expected_models = len(expected_groups) * len(DYNAMIC_OUTCOMES)
    if len(coefficients) != expected_models * len(EVENT_TIMES):
        raise RuntimeError("Alternative coefficient grid has an unexpected row count.")
    if len(pretrends) != expected_models:
        raise RuntimeError("Alternative pretrend grid has an unexpected row count.")
    if len(paths) != expected_models * len(PATH_ROLES) * len(EVENT_TIMES):
        raise RuntimeError("Alternative path grid has an unexpected row count.")
    for frame in [coefficients, pretrends, paths]:
        if set(frame["dimension"]) != {DIMENSION}:
            raise RuntimeError("Alternative dynamic results contain another dimension.")
        if set(frame["group_id"]) != set(expected_groups):
            raise RuntimeError("Alternative dynamic results contain unexpected groups.")
        if "race_unknown" in set(frame["group_id"]):
            raise RuntimeError("Unknown race/color must not be a substantive alternative group.")
    reference = coefficients[coefficients["t"].eq(-1)]
    if len(reference) != expected_models or not np.allclose(reference["coef"], 0.0):
        raise RuntimeError("Every alternative event study must have a zero t=-1 reference.")
    coefficient_pivot = coefficients.pivot(
        index=["outcome", "t"],
        columns="group_id",
        values="coef",
    )
    mirrored_sum = (
        coefficient_pivot["race_white"]
        + coefficient_pivot["race_black_combined"]
    )
    if not np.allclose(mirrored_sum, 0.0, atol=1e-10, equal_nan=True):
        raise RuntimeError(
            "Binary Branca–Negra dynamic DDD coefficients are not mirrored."
        )


def _validate_static_results(
    static_results: dict[str, pd.DataFrame],
) -> None:
    expected_groups = [group_id for group_id, _label in GROUPS]
    for source_key, frame in static_results.items():
        if set(frame["dimension"]) != {DIMENSION}:
            raise RuntimeError(f"{source_key} contains another dimension.")
        if frame["group_id"].drop_duplicates().tolist() != expected_groups:
            raise RuntimeError(f"{source_key} contains unexpected race/color groups.")
        pivot = frame.pivot(index="outcome", columns="group_id", values="coef")
        mirrored_sum = pivot["race_white"] + pivot["race_black_combined"]
        if not np.allclose(mirrored_sum, 0.0, atol=1e-10, equal_nan=True):
            raise RuntimeError(
                f"{source_key} binary Branca–Negra DDD coefficients are not mirrored."
            )


def build(dpi: int = 300) -> dict[str, Path]:
    log("Loading the full main-strict panel...")
    panel, classification = load_analysis_data()
    roles = assign_roles(classification, "main_strict")
    base = apply_roles(panel, roles)

    log("Reconstructing the binary Branca–Negra aggregates from CAGED microdata...")
    micro = aggregate_micro_group_pairs((DIMENSION,))
    dimension_spec = {DIMENSION: DIMENSIONS[DIMENSION]}
    static_results = {
        "heterogeneity": estimate_heterogeneity(
            base,
            FLOW_OUTCOMES,
            dimensions=dimension_spec,
            micro_pairs=micro,
        ),
        "heterogeneity_real_wage": estimate_heterogeneity(
            base,
            REAL_HETEROGENEITY_OUTCOMES,
            dimensions=dimension_spec,
            micro_pairs=micro,
        ),
        "net_flow_heterogeneity": estimate_heterogeneity(
            base,
            NET_FLOW_OUTCOMES,
            dimensions=dimension_spec,
            micro_pairs=micro,
        ),
    }
    _validate_static_results(static_results)

    log("Writing Table 5.2.5.b...")
    sources = _augment_sources(load_sources(), static_results)
    write_heterogeneity_table(sources, DIMENSION, TABLE_DIR)
    validate_section5_2_outputs(TABLE_DIR)

    log("Estimating the strict-window alternative event studies...")
    dynamic_base = load_main_strict_panel()
    coefficients, pretrends, paths = build_micro_dimension_results(
        dynamic_base,
        micro,
        dimension=DIMENSION,
        groups=GROUPS,
        outcomes=DYNAMIC_OUTCOMES,
    )
    _validate_dynamic_frames(coefficients, pretrends, paths)

    figure_dir = COMBINED_OUTPUT_ROOT / "figures"
    backing_dir = COMBINED_OUTPUT_ROOT / "tables"
    backing_dir.mkdir(parents=True, exist_ok=True)
    coefficients.to_csv(backing_dir / "race_color_b_event_study_coefficients_long.csv", index=False)
    pretrends.to_csv(backing_dir / "race_color_b_event_study_pretrends.csv", index=False)
    paths.to_csv(backing_dir / "race_color_b_normalized_paths_long.csv", index=False)

    outputs: dict[str, Path] = {
        "table_csv": TABLE_DIR / "table_5_2_5_b.csv",
        "table_md": TABLE_DIR / "table_5_2_5_b.md",
    }
    for outcome, file_stem in [
        ("ln_admissoes", "admissions"),
        ("ln_salario_real_adm", "real_admission_wage"),
    ]:
        output_path = figure_dir / f"figure_s5_2_race_color_b_{file_stem}_event_study_paths.png"
        plot_combined_figure(
            coefficients,
            pretrends,
            paths,
            dimension=DIMENSION,
            outcome=outcome,
            output_path=output_path,
            dpi=dpi,
        )
        outputs[f"figure_{file_stem}"] = output_path
        log(f"Wrote {output_path}")

    _persist_static_source_rows(static_results)
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build(dpi=args.dpi)
