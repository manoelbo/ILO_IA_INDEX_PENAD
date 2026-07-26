from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PACKAGE_ROOT / "run_replication.py"


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_replication",
        RUNNER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load run_replication.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_reproduce_dag_reestimates_every_inferential_family() -> None:
    module = load_runner()

    dag = module.build_dag(
        section="4-5",
        mode="reproduce",
        raw_dir=PACKAGE_ROOT / "data" / "vintage",
    )
    command_text = "\n".join(" ".join(node.command) for node in dag)

    required_scripts = {
        "gate_v1_model.py",
        "specification_ladder.py",
        "secondary_flow_models.py",
        "event_study.py",
        "sector_models.py",
        "pretrends.py",
        "heterogeneity.py",
        "placebos.py",
        "separation_mechanisms.py",
        "stock_proxy.py",
        "hourly_wage.py",
        "employer_size.py",
        "exposure_sensitivity.py",
        "honest_did.R",
        "export_cross_replication.py",
        "cross_replication.R",
    }
    assert all(script in command_text for script in required_scripts)
    inferential = [node for node in dag if node.inferential]
    assert inferential
    assert all(
        node.disposition == module.REESTIMATED
        for node in inferential
    )


def test_full_dag_adds_data_construction_before_models() -> None:
    module = load_runner()

    dag = module.build_dag(
        section="all",
        mode="full",
        raw_dir=PACKAGE_ROOT / "data" / "vintage",
    )
    identifiers = [node.node_id for node in dag]

    assert identifiers.index("build_signed_movements") < identifiers.index(
        "national_specification_ladder"
    )
    assert "build_national_panel" in identifiers
    assert "build_sector_panel" in identifiers
    assert "validate_section3_reference" in identifiers


def test_dry_run_prints_dag_and_preflight_without_estimating() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER_PATH),
            "--section",
            "4-5",
            "--mode",
            "reproduce",
            "--dry-run",
        ],
        cwd=PACKAGE_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PREFLIGHT: PASS" in completed.stdout
    assert "DAG:" in completed.stdout
    assert "RE-ESTIMATED" in completed.stdout
    assert "FROZEN ESTIMATE VALIDATED" in completed.stdout
    assert "ARTIFACT RENDERED" in completed.stdout
