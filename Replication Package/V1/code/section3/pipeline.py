"""Orchestrate standalone Section 3 reproduction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.artifacts import (
    compare_artifact_directories,
    write_artifact_navigation,
)
from common.files import copy_file, prepare_output_directory
from common.manifest import write_run_manifest
from common.validation import (
    check_equal,
    write_validation_reports,
)
from .build_data import build_section3_data
from .data import load_ilo_metadata, read_data
from .figures import write_figures
from .tables import write_tables
from .validation import analytic_checks


@dataclass(frozen=True)
class RunSummary:
    output_dir: Path
    table_count: int
    figure_count: int
    validation_count: int
    failure_count: int


def run(
    *,
    package_root: Path,
    mode: str,
    raw_dir: Path,
    output_dir: Path,
    billing_project: str | None,
    skip_figures: bool,
) -> RunSummary:
    package_root = package_root.resolve()
    output_dir = output_dir.resolve()
    prepare_output_directory(output_dir, package_root)
    for directory in ("tables", "figures", "backing_data", "validation"):
        (output_dir / directory).mkdir(parents=True, exist_ok=True)

    if mode == "full":
        derived_dir = package_root / "work" / "section3" / "derived"
        analytic_path, ilo_path, diagnostic_path = build_section3_data(
            raw_dir=raw_dir,
            derived_dir=derived_dir,
            billing_project=billing_project,
        )
        inputs = [analytic_path, ilo_path, diagnostic_path]
    elif mode == "reproduce":
        derived_dir = package_root / "data" / "derived" / "section3"
        analytic_path = derived_dir / "pnad_ilo_merged.parquet"
        ilo_path = derived_dir / "ilo_exposure_clean.parquet"
        diagnostic_path = derived_dir / "data_build_diagnostics.csv"
        inputs = [analytic_path, ilo_path, diagnostic_path]
    else:
        raise ValueError(f"Unsupported Section 3 mode: {mode}")
    if not skip_figures:
        inputs.append(
            package_root
            / "data"
            / "derived"
            / "section3"
            / "brazil_states_2020.gpkg"
        )

    frame = read_data(analytic_path)
    ilo_count, title_map = load_ilo_metadata(ilo_path)
    copy_file(
        diagnostic_path,
        output_dir / "backing_data" / "data_build_diagnostics.csv",
    )
    table_files = write_tables(
        frame,
        output_dir,
        ilo_count=ilo_count,
        title_map=title_map,
    )
    figure_files = [] if skip_figures else write_figures(frame, output_dir)

    checks = analytic_checks(frame)
    checks.extend(
        [
            check_equal(
                "section3_table_count",
                len(table_files) // 2,
                5,
                "Published Section 3 tables.",
            ),
            check_equal(
                "section3_figure_count",
                len(figure_files),
                0 if skip_figures else 10,
                "Published Section 3 figures.",
            ),
        ]
    )
    reference_dir = package_root / "results" / "reference" / "section3"
    records, artifact_checks = compare_artifact_directories(
        section="3",
        reference_dir=reference_dir,
        reproduced_dir=output_dir,
        producer="section3.tables; section3.figures",
        include_figures=not skip_figures,
        provenance=_artifact_provenance(),
    )
    checks.extend(artifact_checks)
    write_artifact_navigation(records, output_dir)
    write_validation_reports(
        checks,
        output_dir / "validation",
        title="Section 3 replication validation",
    )
    failure_count = sum(check.status == "FAIL" for check in checks)
    write_run_manifest(
        package_root=package_root,
        output_dir=output_dir,
        section="3",
        mode=mode,
        inputs=inputs,
        failure_count=failure_count,
    )
    if failure_count:
        raise RuntimeError(
            f"Section 3 replication failed {failure_count} validation check(s). "
            f"See {output_dir / 'validation/validation_checks.md'}."
        )
    return RunSummary(
        output_dir=output_dir,
        table_count=len(table_files) // 2,
        figure_count=len(figure_files),
        validation_count=len(checks),
        failure_count=failure_count,
    )


def _artifact_provenance() -> dict[str, tuple[str, str]]:
    analytic_input = "data/derived/section3/pnad_ilo_merged.parquet"
    producers = {
        "table_3_1_base_specs": "section3.tables.build_base_specs",
        "table_3_2_gradients": "section3.tables.build_gradients",
        "table_3_3_high_exposure_occupations": (
            "section3.tables.build_high_exposure_occupations"
        ),
        "table_3_4_sector_exposure": (
            "section3.tables.build_sector_exposure"
        ),
        "table_3_5_demographics_summary": (
            "section3.tables.build_demographics"
        ),
        "figure_3_1_histogram_kde": "section3.figures.plot_histogram_kde",
        "figure_3_2_gradient_population": (
            "section3.figures.plot_gradient_population"
        ),
        "figure_3_3_score_by_occupation_group": (
            "section3.figures.plot_score_by_occupation_group"
        ),
        "figure_3_4_state_high_exposure": (
            "section3.figures.plot_state_high"
        ),
        "figure_3_5_sex": "section3.figures.plot_demographic_dimension",
        "figure_3_6_race": "section3.figures.plot_demographic_dimension",
        "figure_3_7_age": "section3.figures.plot_demographic_dimension",
        "figure_3_8_education": (
            "section3.figures.plot_demographic_dimension"
        ),
        "figure_3_9_income": "section3.figures.plot_demographic_dimension",
        "figure_3_10_formality": (
            "section3.figures.plot_demographic_dimension"
        ),
    }
    return {
        artifact_id: (
            producer,
            (
                analytic_input
                if artifact_id != "figure_3_4_state_high_exposure"
                else analytic_input
                + "; data/derived/section3/brazil_states_2020.gpkg"
            ),
        )
        for artifact_id, producer in producers.items()
    } | {
        "backing_data/data_build_diagnostics.csv": (
            "section3.build_data.build_section3_data",
            "data/derived/section3/data_build_diagnostics.csv",
        )
    }
