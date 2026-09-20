"""Orchestrate standalone Section 3 reproduction."""

from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = PACKAGE_ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from common.artifacts import (
    compare_artifact_directories,
    write_artifact_navigation,
)
from common.files import copy_file, prepare_output_directory
from common.manifest import write_run_manifest
from common.paths import ReplicationPaths
from common.validation import (
    check_equal,
    write_validation_reports,
)
from section3.build_data import (
    build_section3_data,
    PNAD_MANIFEST_FILENAME,
    PNAD_FILENAME,
    validate_pnad_source,
    write_canonical_build_diagnostics,
)
from section3.data import load_ilo_metadata, read_data
from section3.figures import write_figures
from section3.r_validation import run_r_validation
from section3.tables import write_tables
from section3.validation import analytic_checks


@dataclass(frozen=True)
class RunSummary:
    output_dir: Path
    table_count: int
    figure_count: int
    validation_count: int
    failure_count: int


def stage_full_sources(
    *,
    raw_dir: Path,
    data_dir: Path,
    workspace: Path,
) -> Path:
    """Stage immutable source inputs without writing into either supplied root."""
    workspace.mkdir(parents=True, exist_ok=True)
    pnad_source = raw_dir / PNAD_FILENAME
    if pnad_source.is_file():
        validate_pnad_source(raw_dir)
        copy_file(pnad_source, workspace / pnad_source.name)
        copy_file(
            raw_dir / PNAD_MANIFEST_FILENAME,
            workspace / PNAD_MANIFEST_FILENAME,
        )
    ilo_name = "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"
    ilo_candidates = (
        raw_dir / ilo_name,
        raw_dir.parent / "crosswalk" / ilo_name,
        data_dir / "vintage" / "crosswalk" / ilo_name,
    )
    ilo_source = next((path for path in ilo_candidates if path.is_file()), None)
    if ilo_source is None:
        expected = ", ".join(str(path) for path in ilo_candidates)
        raise FileNotFoundError(
            f"Missing registered ILO workbook. Expected one of: {expected}"
        )
    copy_file(ilo_source, workspace / ilo_name)
    return workspace


def run(
    *,
    package_root: Path,
    data_dir: Path,
    reference_dir: Path,
    mode: str,
    raw_dir: Path,
    output_dir: Path,
    billing_project: str | None,
    skip_figures: bool,
) -> RunSummary:
    package_root = package_root.resolve()
    data_dir = data_dir.resolve()
    reference_dir = reference_dir.resolve()
    output_dir = output_dir.resolve()
    prepare_output_directory(output_dir, package_root)
    for directory in ("tables", "figures", "backing_data", "validation"):
        (output_dir / directory).mkdir(parents=True, exist_ok=True)

    full_workspace: tempfile.TemporaryDirectory[str] | None = None
    if mode == "full":
        full_workspace = tempfile.TemporaryDirectory(
            prefix="section3-full-",
            dir=output_dir.parent,
        )
        workspace = Path(full_workspace.name)
        staged_raw = stage_full_sources(
            raw_dir=raw_dir,
            data_dir=data_dir,
            workspace=workspace / "raw",
        )
        derived_dir = workspace / "derived"
        analytic_path, ilo_path, diagnostic_path = build_section3_data(
            raw_dir=staged_raw,
            derived_dir=derived_dir,
            billing_project=billing_project,
        )
        inputs = [analytic_path, ilo_path, diagnostic_path]
    elif mode == "reproduce":
        derived_dir = data_dir / "derived" / "section3"
        analytic_path = derived_dir / "pnad_ilo_merged.parquet"
        ilo_path = derived_dir / "ilo_exposure_clean.parquet"
        diagnostic_path = derived_dir / "data_build_diagnostics.csv"
        inputs = [analytic_path, ilo_path, diagnostic_path]
    else:
        raise ValueError(f"Unsupported Section 3 mode: {mode}")
    if not skip_figures:
        inputs.append(
            data_dir
            / "derived"
            / "section3"
            / "brazil_states_2020.gpkg"
        )

    frame = read_data(analytic_path)
    ilo_count, title_map = load_ilo_metadata(ilo_path)
    write_canonical_build_diagnostics(
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
    r_validation = run_r_validation(frame, output_dir)

    checks = analytic_checks(frame)
    checks.extend(
        [
            check_equal(
                "section3_table_count",
                len(table_files) // 2,
                4,
                "Published Section 3 tables.",
            ),
            check_equal(
                "section3_figure_count",
                len(figure_files),
                0 if skip_figures else 10,
                "Published Section 3 figures.",
            ),
            check_equal(
                "section3_complete_r_replication",
                r_validation["status"],
                "pass",
                "All registered Section 3 aggregates independently match R.",
            ),
        ]
    )
    nested_reference = reference_dir / "artifacts" / "section3"
    legacy_reference = reference_dir / "section3"
    artifact_reference = (
        nested_reference if nested_reference.is_dir() else legacy_reference
    )
    records, artifact_checks = compare_artifact_directories(
        section="3",
        reference_dir=artifact_reference,
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
    summary = RunSummary(
        output_dir=output_dir,
        table_count=len(table_files) // 2,
        figure_count=len(figure_files),
        validation_count=len(checks),
        failure_count=failure_count,
    )
    if full_workspace is not None:
        full_workspace.cleanup()
    return summary


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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("reproduce", "full"), required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--billing-project")
    parser.add_argument("--skip-figures", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    paths = ReplicationPaths.from_environment()
    run(
        package_root=PACKAGE_ROOT,
        data_dir=args.data_dir,
        reference_dir=paths.reference,
        mode=args.mode,
        raw_dir=args.raw_dir / "section3",
        output_dir=args.output_dir,
        billing_project=args.billing_project,
        skip_figures=args.skip_figures,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
