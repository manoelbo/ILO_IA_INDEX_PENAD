"""End-to-end builder for the Section 5.3 occupation-case package."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import (
    AUDIT_DIR,
    CLASSIFICATION_PATH,
    DATA_RAW,
    DICTIONARY_PATH,
    FIGURE_DIR,
    INTERMEDIATE_DIR,
    IPCA_PATH,
    OFFICIAL_METADATA_PATH,
    OUTPUT_ROOT,
    SOURCE_MANIFEST_PATH,
    TABLE_DIR,
    load_occupation_dictionary,
)
from .data import (
    compute_record_wage_winsor_bounds,
    scan_caged_cells,
    scan_winsorized_selected_cells,
)
from .figures import (
    make_age_paths_free_scale_figure,
    make_age_paths_figure,
    make_age_paths_split_figure,
    make_age_terminal_heatmap,
    make_demographic_dumbbell,
    save_figure_bundle,
)
from .report import (
    build_result_selection_log,
    build_source_inventory,
    sha256_file,
    validate_technical_package,
    write_artifact_manifest,
    write_readme,
)
from .tables import (
    annotate_dictionary_for_output,
    build_age_terminal_matrix,
    build_exposure_summary_table,
    build_sensitivity_matrix,
    write_table_pair,
)
from .transforms import (
    aggregate_case_cells,
    build_case_composition_shift,
    build_demographic_difference_matrix,
    build_exposure_composition,
    build_exposure_detail,
    build_membership_table,
    build_preperiod_diagnostics,
    build_same_month_terminal_sensitivity,
    complete_case_panel,
    normalize_case_paths,
)


CELL_CACHE_PATH = INTERMEDIATE_DIR / "cbo6_monthly_cells.parquet"
ROBUST_CELL_CACHE_PATH = INTERMEDIATE_DIR / "cbo6_monthly_cells_record_wage_winsorized.parquet"
SELECTED_RECORD_CACHE_PATH = INTERMEDIATE_DIR / "selected_occupation_admissions.parquet"
RECORD_WAGE_BOUNDS_PATH = INTERMEDIATE_DIR / "record_wage_winsor_bounds.parquet"
CELL_CACHE_META_PATH = INTERMEDIATE_DIR / "cbo6_monthly_cells_metadata.json"


def log(message: str) -> None:
    print(f"[section5_3_occupation_cases] {message}", flush=True)


def _raw_paths() -> list[Path]:
    paths = [DATA_RAW / f"caged_{year}.parquet" for year in range(2021, 2026)]
    missing = [path for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing raw CAGED files: {missing}")
    return paths


def _source_signature(paths: list[Path]) -> list[dict[str, object]]:
    return [
        {
            "path": str(path),
            "bytes": path.stat().st_size,
            "modified_ns": path.stat().st_mtime_ns,
        }
        for path in paths
    ]


def _load_or_build_cells(
    dictionary: pd.DataFrame,
    membership: pd.DataFrame,
    raw_paths: list[Path],
    *,
    reuse_cells: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    eligible_codes = set(membership["cbo_6d"])
    expected_metadata = {
        "cache_schema_version": 3,
        "dictionary_sha256": sha256_file(DICTIONARY_PATH),
        "eligible_code_count": len(eligible_codes),
        "main_wage_method": "positive_record_p1_p99_within_cbo6_year",
        "raw_sources": _source_signature(raw_paths),
    }
    can_reuse = (
        reuse_cells
        and CELL_CACHE_PATH.exists()
        and ROBUST_CELL_CACHE_PATH.exists()
        and SELECTED_RECORD_CACHE_PATH.exists()
        and RECORD_WAGE_BOUNDS_PATH.exists()
        and CELL_CACHE_META_PATH.exists()
        and json.loads(CELL_CACHE_META_PATH.read_text(encoding="utf-8"))
        == expected_metadata
    )
    if can_reuse:
        log("Reusing verified CBO6 monthly-cell cache.")
        cells = pd.read_parquet(CELL_CACHE_PATH)
        audit_path = AUDIT_DIR / "raw_scan_audit.csv"
        if not audit_path.exists():
            raise RuntimeError("Verified cell cache exists but raw scan audit is missing.")
        robust_cells = pd.read_parquet(ROBUST_CELL_CACHE_PATH)
        bounds = pd.read_parquet(RECORD_WAGE_BOUNDS_PATH)
        return cells, robust_cells, bounds, pd.read_csv(audit_path)
    if reuse_cells:
        log("Cached cells are absent or stale; rebuilding from raw CAGED.")
    cells, scan_audit = scan_caged_cells(
        raw_paths,
        eligible_codes,
        selected_records_path=SELECTED_RECORD_CACHE_PATH,
        log=log,
    )
    log("Computing exact record-level P1/P99 wage bounds within CBO6 and year.")
    bounds = compute_record_wage_winsor_bounds(SELECTED_RECORD_CACHE_PATH)
    robust_cells = scan_winsorized_selected_cells(
        SELECTED_RECORD_CACHE_PATH,
        bounds,
        log=log,
    )
    comparison_keys = ["cbo_6d", "dimension", "group_id", "period"]
    comparison = cells.merge(
        robust_cells,
        on=comparison_keys,
        how="outer",
        suffixes=("_raw", "_robust"),
        validate="one_to_one",
    )
    if (
        comparison[["admissions_raw", "admissions_robust"]].isna().any(axis=None)
        or not comparison["admissions_raw"].eq(comparison["admissions_robust"]).all()
        or not comparison["wage_count_raw"].eq(comparison["wage_count_robust"]).all()
    ):
        raise RuntimeError("Record-level wage winsorization changed admission or wage counts.")
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    cells.to_parquet(CELL_CACHE_PATH, index=False)
    robust_cells.to_parquet(ROBUST_CELL_CACHE_PATH, index=False)
    bounds.to_parquet(RECORD_WAGE_BOUNDS_PATH, index=False)
    CELL_CACHE_META_PATH.write_text(
        json.dumps(expected_metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return cells, robust_cells, bounds, scan_audit


def _write_table_package(
    *,
    dictionary: pd.DataFrame,
    membership: pd.DataFrame,
    panel: pd.DataFrame,
    raw_wage_panel: pd.DataFrame,
    paths: pd.DataFrame,
    terminal: pd.DataFrame,
    diagnostics: pd.DataFrame,
    exposure_long: pd.DataFrame,
    exposure_summary: pd.DataFrame,
    exposure_detail: pd.DataFrame,
    sensitivities: pd.DataFrame,
    same_month_terminal: pd.DataFrame,
    composition_shift_detail: pd.DataFrame,
    composition_shift_summary: pd.DataFrame,
    demographic_matrix: pd.DataFrame,
    demographic_decisions: pd.DataFrame,
    record_wage_bounds: pd.DataFrame,
    cell_winsor_bounds: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    compact_exposure = build_exposure_summary_table(exposure_summary, dictionary)
    age_matrix = build_age_terminal_matrix(terminal)
    demographic_paths = paths[
        paths["variant_id"].eq("primary")
        & paths["dimension"].isin(["sex", "race_color", "education"])
    ].copy()
    result_log = build_result_selection_log(
        terminal,
        sensitivities,
        diagnostics,
        demographic_decisions,
    )
    detailed_exposure = exposure_detail.merge(
        dictionary[["case_id", "cbo_6d", "cbo_title", "mapping_confidence"]],
        on=["case_id", "cbo_6d"],
        how="left",
        validate="one_to_one",
    )
    tables = {
        "occupation_case_dictionary": annotate_dictionary_for_output(dictionary),
        "occupation_case_membership_variants": membership,
        "table_5_3_1_occupation_case_exposure_summary": compact_exposure,
        "occupation_case_monthly_panel": panel,
        "occupation_case_raw_monthly_panel": raw_wage_panel,
        "occupation_case_monthly_paths": paths,
        "occupation_case_terminal_summary": terminal,
        "occupation_case_age_terminal_matrix": age_matrix,
        "occupation_case_preperiod_diagnostics": diagnostics,
        "occupation_case_exposure_composition": exposure_long,
        "occupation_case_exposure_detail": detailed_exposure,
        "occupation_case_sensitivity_matrix": sensitivities,
        "occupation_case_same_month_sensitivity": same_month_terminal,
        "occupation_case_cbo_composition_shift_detail": composition_shift_detail,
        "occupation_case_cbo_composition_shift_summary": composition_shift_summary,
        "occupation_case_demographic_paths": demographic_paths,
        "occupation_case_demographic_terminal_matrix": demographic_matrix,
        "occupation_case_demographic_mention_decisions": demographic_decisions,
        "occupation_case_record_wage_winsor_bounds": record_wage_bounds,
        "occupation_case_wage_winsor_bounds": cell_winsor_bounds,
        "result_selection_log": result_log,
    }
    for stem, frame in tables.items():
        write_table_pair(frame, TABLE_DIR, stem)
    return tables


def _write_figures(
    paths: pd.DataFrame,
    terminal: pd.DataFrame,
    demographic_matrix: pd.DataFrame,
) -> None:
    save_figure_bundle(
        make_age_paths_figure(paths, "admissions"),
        FIGURE_DIR,
        "figure_5_3_1_occupation_cases_admissions_by_age",
    )
    save_figure_bundle(
        make_age_paths_figure(paths, "real_admission_wage"),
        FIGURE_DIR,
        "figure_5_3_2_occupation_cases_real_admission_wage_by_age",
    )
    alternative_specs = [
        (
            make_age_paths_free_scale_figure(paths, "admissions"),
            "figure_5_3_1a_occupation_cases_admissions_by_age",
        ),
        (
            make_age_paths_split_figure(paths, "admissions"),
            "figure_5_3_1b_occupation_cases_admissions_by_age",
        ),
        (
            make_age_terminal_heatmap(terminal, "admissions"),
            "figure_5_3_1c_occupation_cases_admissions_by_age",
        ),
        (
            make_age_paths_free_scale_figure(paths, "real_admission_wage"),
            "figure_5_3_2a_occupation_cases_real_admission_wage_by_age",
        ),
        (
            make_age_paths_split_figure(paths, "real_admission_wage"),
            "figure_5_3_2b_occupation_cases_real_admission_wage_by_age",
        ),
        (
            make_age_terminal_heatmap(terminal, "real_admission_wage"),
            "figure_5_3_2c_occupation_cases_real_admission_wage_by_age",
        ),
    ]
    for figure, stem in alternative_specs:
        save_figure_bundle(figure, FIGURE_DIR, stem)
    appendix_specs = [
        ("sex", "figure_b_1_occupation_cases_by_sex"),
        ("race_color", "figure_b_2_occupation_cases_by_race_color"),
        ("education", "figure_b_3_occupation_cases_by_education"),
    ]
    for dimension, stem in appendix_specs:
        save_figure_bundle(
            make_demographic_dumbbell(demographic_matrix, dimension),
            FIGURE_DIR,
            stem,
        )


def run(
    *,
    reuse_cells: bool = False,
    include_source_hashes: bool = True,
) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    log("Loading and validating the frozen semantic dictionary.")
    dictionary = load_occupation_dictionary()
    membership = build_membership_table(dictionary)
    raw_paths = _raw_paths()
    cells, robust_cells, record_wage_bounds, scan_audit = _load_or_build_cells(
        dictionary,
        membership,
        raw_paths,
        reuse_cells=reuse_cells,
    )
    scan_audit.to_csv(AUDIT_DIR / "raw_scan_audit.csv", index=False)
    (AUDIT_DIR / "raw_scan_audit.md").write_text(
        scan_audit.to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    log("Aggregating primary and pre-specified sensitivity cases.")
    ipca = pd.read_parquet(IPCA_PATH)
    classification = pd.read_csv(CLASSIFICATION_PATH, dtype={"cbo_4d": str})
    observed_panel, _unused_main_bounds = aggregate_case_cells(
        robust_cells,
        membership,
        ipca,
        winsorize_wages=False,
    )
    panel = complete_case_panel(observed_panel, membership, ipca)
    raw_wage_observed, _unused_raw_bounds = aggregate_case_cells(
        cells,
        membership,
        ipca,
        winsorize_wages=False,
    )
    raw_wage_panel = complete_case_panel(raw_wage_observed, membership, ipca)
    cell_winsor_observed, cell_winsor_bounds = aggregate_case_cells(
        cells,
        membership,
        ipca,
        winsorize_wages=True,
    )
    cell_winsor_panel = complete_case_panel(cell_winsor_observed, membership, ipca)

    log("Building normalized paths, terminal metrics, and descriptive diagnostics.")
    paths, terminal = normalize_case_paths(panel)
    _alternative_paths, alternative_terminal = normalize_case_paths(
        panel,
        baseline_window=("2022-01", "2022-10"),
    )
    _raw_wage_paths, raw_wage_terminal = normalize_case_paths(raw_wage_panel)
    _cell_winsor_paths, cell_winsor_terminal = normalize_case_paths(cell_winsor_panel)
    diagnostics = build_preperiod_diagnostics(panel)
    same_month_terminal = build_same_month_terminal_sensitivity(panel)
    exposure_long, exposure_summary = build_exposure_composition(
        cells,
        membership,
        classification,
    )
    exposure_detail = build_exposure_detail(cells, membership, classification)
    composition_shift_detail, composition_shift_summary = build_case_composition_shift(
        cells,
        membership,
    )
    sensitivities = build_sensitivity_matrix(
        terminal,
        alternative_terminal,
        same_month_terminal,
        raw_wage_terminal,
        cell_winsor_terminal,
    )
    demographic_matrix, demographic_decisions = build_demographic_difference_matrix(
        terminal,
        alternative_terminal,
        same_month_terminal,
    )

    log("Writing dissertation and appendix tables.")
    _write_table_package(
        dictionary=dictionary,
        membership=membership,
        panel=panel,
        raw_wage_panel=raw_wage_panel,
        paths=paths,
        terminal=terminal,
        diagnostics=diagnostics,
        exposure_long=exposure_long,
        exposure_summary=exposure_summary,
        exposure_detail=exposure_detail,
        sensitivities=sensitivities,
        same_month_terminal=same_month_terminal,
        composition_shift_detail=composition_shift_detail,
        composition_shift_summary=composition_shift_summary,
        demographic_matrix=demographic_matrix,
        demographic_decisions=demographic_decisions,
        record_wage_bounds=record_wage_bounds,
        cell_winsor_bounds=cell_winsor_bounds,
    )

    log(
        "Rendering the two official figures, six layout comparison exports, "
        "and three appendix figures."
    )
    _write_figures(paths, terminal, demographic_matrix)

    log("Writing source inventory and technical validation.")
    source_paths = raw_paths + [
        IPCA_PATH,
        CLASSIFICATION_PATH,
        DICTIONARY_PATH,
        OFFICIAL_METADATA_PATH,
        SOURCE_MANIFEST_PATH,
    ]
    inventory = build_source_inventory(
        source_paths,
        include_hashes=include_source_hashes,
    )
    inventory.to_csv(AUDIT_DIR / "source_inventory.csv", index=False)
    (AUDIT_DIR / "source_inventory.md").write_text(
        inventory.to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    write_readme()
    validate_technical_package(
        dictionary=dictionary,
        paths=paths,
        terminal=terminal,
        exposure_long=exposure_long,
    )
    write_artifact_manifest()
    log(f"Done. Package written to {OUTPUT_ROOT}.")
