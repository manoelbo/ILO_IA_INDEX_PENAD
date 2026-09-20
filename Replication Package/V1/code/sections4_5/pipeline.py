"""Standalone orchestration for dissertation Sections 4–5."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.artifacts import (
    compare_artifact_directories,
    write_artifact_navigation,
)
from common.files import copy_file, prepare_output_directory, sha256_file
from common.manifest import write_run_manifest
from common.validation import check_equal, write_validation_reports
from .analysis import (
    reestimate_core_models,
    validate_empirical_output_contracts,
)
from .contracts import BACKING_DATA_FILES, FIGURE_SPECS, TABLE_SPECS
from .panel import input_paths, validate_analytic_inputs
from .publication import render_figures, render_tables


@dataclass(frozen=True)
class RunSummary:
    output_dir: Path
    table_count: int
    figure_count: int
    backing_file_count: int
    validation_count: int
    failure_count: int


def run(
    *,
    package_root: Path,
    mode: str,
    raw_dir: Path,
    output_dir: Path,
    skip_figures: bool,
    billing_project: str | None = None,
) -> RunSummary:
    """Reproduce all public Sections 4–5 artifacts and numeric checks."""
    package_root = package_root.resolve()
    output_dir = output_dir.resolve()
    prepare_output_directory(output_dir, package_root)
    for directory in ("tables", "figures", "backing_data", "validation"):
        (output_dir / directory).mkdir(parents=True, exist_ok=True)

    if mode == "reproduce":
        data_root = package_root / "data" / "derived" / "sections4_5"
    elif mode == "full":
        from .full_pipeline import run_full_rebuild

        data_root = run_full_rebuild(
            package_root=package_root,
            raw_dir=raw_dir.resolve(),
            billing_project=billing_project,
        )
    else:
        raise ValueError(f"Unsupported Sections 4–5 mode: {mode}")

    inputs = _input_inventory(data_root)
    input_hashes = {path: sha256_file(path) for path in inputs}

    checks, _denominators = validate_analytic_inputs(data_root)
    checks.extend(validate_empirical_output_contracts(data_root))

    table_files = render_tables(
        data_root,
        output_dir / "tables",
    )
    figure_files = (
        []
        if skip_figures
        else render_figures(
            data_root,
            output_dir / "figures",
            (
                package_root
                / "code"
                / "sections4_5"
                / "author_pipeline"
                / "src"
                / "scripts"
            ),
        )
    )
    backing_files = _copy_backing_data(
        data_root / "backing_data",
        output_dir / "backing_data",
    )
    core_path = output_dir / "backing_data" / "core_model_reestimation.csv"
    _, core_checks = reestimate_core_models(
        data_root,
        core_path,
    )
    backing_files.append(core_path)
    checks.extend(core_checks)

    checks.extend(
        [
            check_equal(
                "sections4_5_table_count",
                len(table_files) // 2,
                23,
                "Published Sections 4–5 tables.",
            ),
            check_equal(
                "sections4_5_figure_count",
                len(figure_files),
                0 if skip_figures else 13,
                "Published Sections 4–5 figures.",
            ),
            check_equal(
                "sections4_5_backing_csv_count",
                len(backing_files),
                len(BACKING_DATA_FILES) + 1,
                "Full-precision backing files linked to artifacts or checks.",
            ),
            check_equal(
                "author_pipeline_source_count",
                len(
                    list(
                        (
                            package_root
                            / "code"
                            / "sections4_5"
                            / "author_pipeline"
                        ).rglob("*.py")
                    )
                ),
                48,
                "Packaged author scripts used by the documented full DAG.",
            ),
            check_equal(
                "derived_inputs_immutable",
                all(
                    sha256_file(path) == input_hashes[path]
                    for path in inputs
                ),
                True,
                "No stage may mutate frozen analytic or backing inputs.",
            ),
        ]
    )

    reference_dir = package_root / "results" / "reference" / "sections4_5"
    records, artifact_checks = compare_artifact_directories(
        section="4-5",
        reference_dir=reference_dir,
        reproduced_dir=output_dir,
        producer="sections4_5.pipeline",
        include_figures=not skip_figures,
        provenance=_artifact_provenance(),
    )
    checks.extend(artifact_checks)
    write_artifact_navigation(records, output_dir)
    write_validation_reports(
        checks,
        output_dir / "validation",
        title="Sections 4–5 replication validation",
    )
    failure_count = sum(check.status == "FAIL" for check in checks)
    write_run_manifest(
        package_root=package_root,
        output_dir=output_dir,
        section="4-5",
        mode=mode,
        inputs=inputs,
        failure_count=failure_count,
    )
    if failure_count:
        raise RuntimeError(
            "Sections 4–5 replication failed "
            f"{failure_count} validation check(s). See "
            f"{output_dir / 'validation/validation_checks.md'}."
        )
    return RunSummary(
        output_dir=output_dir,
        table_count=len(table_files) // 2,
        figure_count=len(figure_files),
        backing_file_count=len(backing_files),
        validation_count=len(checks),
        failure_count=failure_count,
    )


def _copy_backing_data(source_dir: Path, output_dir: Path) -> list[Path]:
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Missing backing-data directory: {source_dir}")
    written: list[Path] = []
    for relative_text in BACKING_DATA_FILES:
        relative = Path(relative_text)
        source = source_dir / relative
        if not source.is_file():
            raise FileNotFoundError(f"Missing backing-data input: {source}")
        written.append(copy_file(source, output_dir / relative))
    return written


def _input_inventory(
    data_root: Path,
) -> list[Path]:
    paths = list(input_paths(data_root).values())
    paths.extend(
        data_root / "backing_data" / relative
        for relative in BACKING_DATA_FILES
    )
    missing = [path for path in paths if not path.is_file()]
    if missing:
        rendered = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing replication input(s):\n{rendered}")
    return sorted(set(paths))


def _artifact_provenance() -> dict[str, tuple[str, str]]:
    curated_sources = {
        "table_4_2_1_panel_scope": "table_4_2a_panel_descriptive_summary.csv",
        "table_4_2_2_ilo_cbo_classification": "table_4_2b_ilo_cbo_classification.csv",
        "table_4_2_3_crosswalk_coverage": "table_4_2c_crosswalk_coverage.csv",
        "table_5_1_national_results": "table_5_2_1_national_main_results.csv",
        "table_5_2_1_sex": "table_5_2_2_heterogeneity_sex.csv",
        "table_5_2_2_race_color": "table_5_2_5_b.csv",
        "table_5_2_3_age_pnad": "table_5_2_4_b.csv",
        "table_5_2_4_education": "table_5_2_6_heterogeneity_education.csv",
        "table_5_2_5_income": "table_5_2_3_heterogeneity_income.csv",
        "table_5_3_1_occupation_cases": "table_5_3_1_occupation_case_exposure_summary.csv",
        "table_a_1_national_main_diagnostics": "table_5_2_1_national_main_results.csv",
        "table_a_1_national_net_flow_diagnostics": "table_5_2_1_national_main_results.csv",
        "table_a_2_sex_main_diagnostics": "table_5_2_2_heterogeneity_sex.csv",
        "table_a_2_sex_net_flow_diagnostics": "table_5_2_2_heterogeneity_sex.csv",
        "table_a_3_race_color_diagnostics": "table_5_2_5_b.csv",
        "table_a_4_age_pnad_main_diagnostics": "table_5_2_4_b.csv",
        "table_a_4_age_pnad_net_flow_diagnostics": "table_5_2_4_b.csv",
        "table_a_4_canaries_age_main_diagnostics": "table_5_2_4_heterogeneity_age_canaries.csv",
        "table_a_4_canaries_age_net_flow_diagnostics": "table_5_2_4_heterogeneity_age_canaries.csv",
        "table_a_5_education_diagnostics": "table_5_2_6_heterogeneity_education.csv",
        # The published appendix filenames retain their legacy "income"
        # label, but their frozen contents are education diagnostics.
        "table_a_6_income_main_diagnostics": "table_5_2_6_heterogeneity_education.csv",
        "table_a_6_income_net_flow_diagnostics": "table_5_2_6_heterogeneity_education.csv",
    }
    provenance: dict[str, tuple[str, str]] = {}
    for spec in TABLE_SPECS:
        input_path = (
            "code/sections4_5/publication.py"
            if spec.artifact_id == "table_4_2_outcomes"
            else "data/derived/sections4_5/backing_data/curated_tables/"
            f"{curated_sources[spec.artifact_id]}"
        )
        provenance[spec.artifact_id] = (spec.source_function, input_path)

    for spec in FIGURE_SPECS:
        if spec.artifact_id.startswith("figure_5_3_"):
            input_path = (
                "data/derived/sections4_5/backing_data/"
                "section5_3_occupation_cases/occupation_case_monthly_paths.csv"
            )
        elif "age_pnad" in spec.artifact_id:
            input_path = (
                "data/derived/sections4_5/backing_data/"
                "section5_2_age_pnad/event_study_coefficients_long.csv"
            )
        elif "race" in spec.artifact_id:
            input_path = (
                "data/derived/sections4_5/backing_data/"
                "section5_2_dynamic/race_color_b_event_study_coefficients_long.csv"
            )
        else:
            input_path = (
                "data/derived/sections4_5/backing_data/"
                "section5_2_dynamic/event_study_coefficients_long.csv"
            )
        provenance[Path(spec.canonical_name).stem] = (
            spec.source_function,
            input_path,
        )
    for relative in BACKING_DATA_FILES:
        provenance[f"backing_data/{relative}"] = (
            "sections4_5.full_pipeline",
            f"data/derived/sections4_5/backing_data/{relative}",
        )
    provenance["backing_data/core_model_reestimation.csv"] = (
        "sections4_5.analysis.reestimate_core_models",
        "data/derived/sections4_5/data/output/painel_2b_ready.parquet",
    )
    return provenance
