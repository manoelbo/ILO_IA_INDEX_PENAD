#!/usr/bin/env python3
"""Public V2 replication CLI with an explicit estimation DAG."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PACKAGE_ROOT = Path(__file__).resolve().parent
REPLICATION_CODE = PACKAGE_ROOT / "code" / "replication"
if str(REPLICATION_CODE) not in sys.path:
    sys.path.insert(0, str(REPLICATION_CODE))

from contracts import validate_reference


REESTIMATED = "RE-ESTIMATED"
FROZEN_VALIDATED = "FROZEN ESTIMATE VALIDATED"
RENDERED = "ARTIFACT RENDERED"
DATA_REBUILT = "DATA REBUILT"
DEFAULT_RAW_DIR = PACKAGE_ROOT / "data" / "vintage"
DEFAULT_OUTPUT_DIR = PACKAGE_ROOT / "results"


@dataclass(frozen=True)
class DagNode:
    node_id: str
    description: str
    command: tuple[str, ...]
    disposition: str
    outputs: tuple[str, ...] = ()
    inferential: bool = False


def _python(script: str, *arguments: str) -> tuple[str, ...]:
    return (
        sys.executable,
        str(PACKAGE_ROOT / script),
        *arguments,
    )


def _reference_node(section: str) -> DagNode:
    label = (
        "validate_section3_reference"
        if section in {"all", "3"}
        else "validate_reference_manifest"
    )
    return DagNode(
        node_id=label,
        description=(
            "Validate the signed frozen reference before any comparison"
        ),
        command=_python(
            "code/replication/contracts.py",
            "validate",
        ),
        disposition=FROZEN_VALIDATED,
    )


def _construction_nodes(raw_dir: Path) -> list[DagNode]:
    movements = (
        PACKAGE_ROOT
        / "data"
        / "interim"
        / "movimentacoes"
    )
    return [
        DagNode(
            "build_signed_movements",
            "Rebuild MOV + FOR - EXC partitions by fact month",
            _python(
                "code/ingest/build_movements.py",
                "--inventory",
                str(raw_dir / "ftp_inventory.csv"),
                "--vintage-dir",
                str(raw_dir),
                "--output-dir",
                str(movements),
            ),
            DATA_REBUILT,
            ("reconciliation/origem_por_competencia.csv",),
        ),
        DagNode(
            "classify_treatment",
            "Reproduce the frozen MTE-to-ILO treatment classification",
            _python("code/panel/crosswalk.py", "classify"),
            DATA_REBUILT,
            (
                "reconciliation/crosswalk_coverage.json",
                "reconciliation/treatment_classification_validation.json",
            ),
        ),
        DagNode(
            "build_treatment_variants",
            "Rebuild preregistered treatment variants",
            _python("code/panel/treatment_variants.py"),
            DATA_REBUILT,
            (
                "treatment/treatment_variant_comparison.csv",
                "treatment/treatment_variant_support.json",
            ),
        ),
        DagNode(
            "build_national_panel",
            "Rebuild the CBO4-by-month national panel",
            _python("code/panel/build_panel.py", "build"),
            DATA_REBUILT,
            ("reconciliation/painel_nacional_support.json",),
        ),
        DagNode(
            "build_sector_panel",
            "Rebuild the CBO4-by-CNAE-by-month panel",
            _python("code/panel/build_panel.py", "build-sector"),
            DATA_REBUILT,
            (
                "reconciliation/painel_cbo_cnae_support.json",
                "reconciliation/cnae_month_treatment_support.csv",
            ),
        ),
    ]


def _analysis_nodes() -> list[DagNode]:
    return [
        DagNode(
            "v1_gate_on_v2_panel",
            "Re-estimate the exact V1 model on the V2 panel",
            _python("code/models/gate_v1_model.py"),
            REESTIMATED,
            (
                "reconciliation/gate_modelo_antigo.csv",
                "reconciliation/GATE_MODELO_ANTIGO.md",
            ),
            True,
        ),
        DagNode(
            "national_specification_ladder",
            "Re-estimate PPML, real wage, net flow, and control ladder",
            _python("code/models/specification_ladder.py"),
            REESTIMATED,
            ("models/specification_ladder.csv",),
            True,
        ),
        DagNode(
            "balanced_event_studies",
            "Re-estimate the complete balanced event-study grid",
            _python("code/models/event_study.py"),
            REESTIMATED,
            (
                "models/event_study_coefficients.csv",
                "models/long_run_horizons.csv",
            ),
            True,
        ),
        DagNode(
            "sector_fixed_effects",
            "Re-estimate the sector fixed-effect and inference ladder",
            _python("code/models/sector_models.py"),
            REESTIMATED,
            (
                "models/sector_fixed_effect_ladder.csv",
                "models/sector_level1_vs_level2.csv",
            ),
            True,
        ),
        DagNode(
            "exact_pretrends",
            "Re-estimate exact-model pretrends and HonestDiD inputs",
            _python("code/models/pretrends.py"),
            REESTIMATED,
            (
                "diagnostics/pretrend_diagnostics.csv",
                "diagnostics/honest_did_event_coefficients.csv",
                "diagnostics/honest_did_event_vcov_long.csv",
            ),
            True,
        ),
        DagNode(
            "honest_did",
            "Re-estimate Rambachan-Roth sensitivity in R",
            (
                "Rscript",
                str(PACKAGE_ROOT / "R" / "honest_did.R"),
            ),
            REESTIMATED,
            (
                "diagnostics/honest_did_sensitivity.csv",
                "diagnostics/honest_did_summary.csv",
                "diagnostics/honest_did_asinh_saldo.png",
                "diagnostics/honest_did_ln_salario_real_adm.png",
            ),
            True,
        ),
        DagNode(
            "ddd_heterogeneity",
            "Rebuild and re-estimate the complete DDD family",
            _python("code/models/heterogeneity.py"),
            REESTIMATED,
            (
                "diagnostics/ddd_multiplicity_results.csv",
                "diagnostics/ddd_family_support.csv",
            ),
            True,
        ),
        DagNode(
            "placebo_falsifications",
            "Re-estimate temporal and 500-assignment group placebos",
            _python("code/models/placebos.py"),
            REESTIMATED,
            (
                "diagnostics/temporal_placebo_results.csv",
                "diagnostics/group_placebo_distribution.csv",
                "diagnostics/group_placebo_summary.csv",
            ),
            True,
        ),
        DagNode(
            "separation_mechanisms",
            "Rebuild and re-estimate separation mechanism families",
            _python("code/models/separation_mechanisms.py"),
            REESTIMATED,
            (
                "mechanisms/separation_static_results.csv",
                "mechanisms/separation_event_study.csv",
            ),
            True,
        ),
        DagNode(
            "cumulative_net_flow",
            "Rebuild and re-estimate the cumulative net-flow proxy",
            _python("code/models/stock_proxy.py"),
            REESTIMATED,
            ("mechanisms/stock_proxy_result.csv",),
            True,
        ),
        DagNode(
            "hourly_wage_and_schedules",
            "Rebuild and re-estimate wage and schedule margins",
            _python("code/models/hourly_wage.py"),
            REESTIMATED,
            ("mechanisms/hourly_wage_results.csv",),
            True,
        ),
        DagNode(
            "employer_size",
            "Rebuild and re-estimate employer-size heterogeneity",
            _python("code/models/employer_size.py"),
            REESTIMATED,
            (
                "mechanisms/employer_size_ddd_results.csv",
                "mechanisms/employer_registration_support.csv",
            ),
            True,
        ),
        DagNode(
            "exposure_measure_sensitivity",
            "Re-estimate 2023, model-consensus, and Anthropic measures",
            _python("code/models/exposure_sensitivity.py"),
            REESTIMATED,
            (
                "mechanisms/exposure_sensitivity_results.csv",
                "mechanisms/exposure_rank_correlations.csv",
            ),
            True,
        ),
    ]


def build_dag(
    *,
    section: str,
    mode: str,
    raw_dir: Path,
) -> list[DagNode]:
    if section not in {"all", "3", "4-5"}:
        raise ValueError(f"Unsupported section: {section}")
    if mode not in {"reproduce", "full"}:
        raise ValueError(f"Unsupported mode: {mode}")
    nodes = [_reference_node(section)]
    if section == "3":
        return nodes
    if mode == "full":
        nodes.extend(_construction_nodes(raw_dir))
    nodes.extend(_analysis_nodes())
    return nodes


def _required_reproduce_inputs() -> tuple[Path, ...]:
    return (
        PACKAGE_ROOT / "data" / "derived" / "painel_nacional.parquet",
        PACKAGE_ROOT / "data" / "derived" / "painel_cbo_cnae.parquet",
        PACKAGE_ROOT / "data" / "derived" / "treatment_variants.csv",
        PACKAGE_ROOT
        / "data"
        / "derived"
        / "painel_heterogeneity_ddd.parquet",
        PACKAGE_ROOT
        / "data"
        / "vintage"
        / "crosswalk"
        / "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx",
        PACKAGE_ROOT.parents[1]
        / "data"
        / "processed"
        / "anthropic_automation_augmentation_cbo.parquet",
    )


def preflight(
    *,
    section: str,
    mode: str,
    raw_dir: Path,
    dag: Sequence[DagNode],
) -> dict[str, object]:
    reference = validate_reference(
        PACKAGE_ROOT / "results" / "reference"
    )
    missing_scripts = [
        item
        for node in dag
        for item in node.command[1:2]
        if item.endswith((".py", ".R")) and not Path(item).is_file()
    ]
    if missing_scripts:
        raise FileNotFoundError(
            "DAG scripts are missing: " + ", ".join(missing_scripts)
        )
    missing_inputs: list[str] = []
    if section != "3" and mode == "reproduce":
        missing_inputs = [
            str(path)
            for path in _required_reproduce_inputs()
            if not path.is_file()
        ]
        partitions = len(
            list(
                (
                    PACKAGE_ROOT
                    / "data"
                    / "interim"
                    / "movimentacoes"
                ).glob("competenciamov=*/part.parquet")
            )
        )
        if partitions != 77:
            missing_inputs.append(
                f"expected 77 signed movement partitions, found {partitions}"
            )
    else:
        partitions = 77
    if section != "3" and mode == "full":
        archives = len(list(raw_dir.glob("CAGED*.7z")))
        if archives != 195:
            missing_inputs.append(
                f"expected 195 raw archives, found {archives} in {raw_dir}"
            )
        inventory = raw_dir / "ftp_inventory.csv"
        if not inventory.is_file():
            missing_inputs.append(str(inventory))
    else:
        archives = 195
    if section != "3" and shutil.which("Rscript") is None:
        missing_inputs.append("Rscript executable")
    if missing_inputs:
        raise FileNotFoundError(
            "Preflight inputs are missing:\n- "
            + "\n- ".join(missing_inputs)
        )
    return {
        "archives": archives,
        "dag_nodes": len(dag),
        "movement_partitions": partitions,
        "reference_artifacts": reference["artifacts"],
        "reference_signature_valid": reference[
            "manifest_signature_valid"
        ],
    }


def _print_dag(dag: Sequence[DagNode], skip_figures: bool) -> None:
    print("DAG:")
    for index, node in enumerate(dag, start=1):
        print(
            f"{index:02d}. [{node.disposition}] {node.node_id}: "
            f"{node.description}"
        )
        print("    COMMAND: " + " ".join(node.command))
        for output in node.outputs:
            if skip_figures and output.endswith(".png"):
                continue
            print(f"    [{RENDERED}] results/{output}")


def _execution_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for variable in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMBA_NUM_THREADS",
    ):
        environment.setdefault(variable, "1")
    environment.setdefault("PYTHONUNBUFFERED", "1")
    return environment


def run_dag(
    dag: Sequence[DagNode],
    *,
    skip_figures: bool,
) -> None:
    environment = _execution_environment()
    for index, node in enumerate(dag, start=1):
        print(
            f"[{node.disposition}] START {index}/{len(dag)} "
            f"{node.node_id}",
            flush=True,
        )
        completed = subprocess.run(
            node.command,
            cwd=PACKAGE_ROOT,
            env=environment,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"DAG node failed ({completed.returncode}): "
                f"{node.node_id}"
            )
        print(
            f"[{node.disposition}] DONE {node.node_id}",
            flush=True,
        )
        for output in node.outputs:
            if skip_figures and output.endswith(".png"):
                continue
            path = DEFAULT_OUTPUT_DIR / output
            if not path.is_file():
                raise FileNotFoundError(
                    f"Declared node output is missing: {path}"
                )
            print(f"[{RENDERED}] {path}", flush=True)


def render_output_bundle(
    output_dir: Path,
    *,
    skip_figures: bool,
) -> int:
    if output_dir.resolve() == DEFAULT_OUTPUT_DIR.resolve():
        return len(
            [
                path
                for path in DEFAULT_OUTPUT_DIR.rglob("*")
                if path.is_file()
                and "reference"
                not in path.relative_to(DEFAULT_OUTPUT_DIR).parts
                and not (skip_figures and path.suffix == ".png")
            ]
        )
    copied = 0
    for source in sorted(DEFAULT_OUTPUT_DIR.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(DEFAULT_OUTPUT_DIR)
        if "reference" in relative.parts:
            continue
        if skip_figures and source.suffix == ".png":
            continue
        destination = output_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(
            f"{destination.suffix}.tmp"
        )
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
        copied += 1
        print(f"[{RENDERED}] {destination}")
    return copied


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re-estimate the V2 dissertation replication package."
    )
    parser.add_argument(
        "--section",
        choices=("all", "3", "4-5"),
        default="all",
    )
    parser.add_argument(
        "--mode",
        choices=("reproduce", "full"),
        default="reproduce",
    )
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )
    parser.add_argument("--skip-figures", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.resolve()
    output_dir = args.output_dir.resolve()
    dag = build_dag(
        section=args.section,
        mode=args.mode,
        raw_dir=raw_dir,
    )
    summary = preflight(
        section=args.section,
        mode=args.mode,
        raw_dir=raw_dir,
        dag=dag,
    )
    print("PREFLIGHT: PASS " + json.dumps(summary, sort_keys=True))
    _print_dag(dag, args.skip_figures)
    if args.dry_run:
        print("DRY RUN: no estimation or rendering executed")
        return 0
    run_dag(dag, skip_figures=args.skip_figures)
    rendered = render_output_bundle(
        output_dir,
        skip_figures=args.skip_figures,
    )
    print(
        "REPLICATION: COMPLETE "
        + json.dumps(
            {
                "artifacts_rendered": rendered,
                "mode": args.mode,
                "output_dir": str(output_dir),
                "section": args.section,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
