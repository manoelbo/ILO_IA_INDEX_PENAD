from __future__ import annotations

import importlib.metadata
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


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
        target="caged",
        mode="reproduce",
        raw_dir=PACKAGE_ROOT / "data" / "vintage",
        data_dir=PACKAGE_ROOT / "data",
        output_dir=PACKAGE_ROOT / "results" / "reproduced",
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
        "backing.py",
        "diagnose_vintage.py",
        "reconcile_pdet.py",
        "complete_replication.R",
        "r_validation.py",
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
        target="all",
        mode="full",
        raw_dir=PACKAGE_ROOT / "data" / "vintage",
        data_dir=PACKAGE_ROOT / "data",
        output_dir=PACKAGE_ROOT / "results" / "reproduced",
    )
    identifiers = [node.node_id for node in dag]

    assert identifiers.index("build_signed_movements") < identifiers.index(
        "national_specification_ladder"
    )
    assert identifiers.index("download_official_caged") < identifiers.index(
        "verify_official_caged"
    ) < identifiers.index("build_signed_movements")
    assert identifiers.index("freeze_official_ipca") < identifiers.index(
        "build_national_panel"
    )
    assert identifiers.index("freeze_official_cnae") < identifiers.index(
        "build_sector_panel"
    )
    assert "build_national_panel" in identifiers
    assert "build_sector_panel" in identifiers
    assert "section3_reproduction" in identifiers


def test_caged_dag_orders_consumers_after_their_producers() -> None:
    module = load_runner()

    dag = module.build_dag(
        target="caged",
        mode="reproduce",
        raw_dir=PACKAGE_ROOT / "data" / "vintage",
        data_dir=PACKAGE_ROOT / "data",
        output_dir=PACKAGE_ROOT / "results" / "reproduced",
    )
    identifiers = [node.node_id for node in dag]

    assert identifiers.index("group_did_family_c") < identifiers.index(
        "audit_wage_composition"
    )
    assert identifiers.index("complete_r_replication") < identifiers.index(
        "compare_complete_r_replication"
    )
    assert identifiers.index("compare_complete_r_replication") < identifiers.index(
        "honest_did"
    )
    assert identifiers.index("canaries_wage_figure") < identifiers.index(
        "phase8b_rendering"
    )


def test_dag_dependency_validator_rejects_an_inverted_dependency() -> None:
    module = load_runner()
    def node(node_id: str) -> object:
        return module.DagNode(
            node_id,
            node_id,
            ("true",),
            module.REESTIMATED,
        )

    inverted = [
        node("ddd_pretrend_diagnostics"),
        node("ddd_alternative_partitions_pretrends"),
        node("national_specification_ladder"),
        node("hourly_wage_and_schedules"),
        node("audit_wage_composition"),
        node("group_did_family_c"),
    ]

    with pytest.raises(RuntimeError, match="must run after group_did_family_c"):
        module.validate_dag_dependencies(inverted)


def test_all_target_traverses_the_five_public_components() -> None:
    module = load_runner()

    dag = module.build_dag(
        target="all",
        mode="reproduce",
        raw_dir=PACKAGE_ROOT / "data" / "vintage",
        data_dir=PACKAGE_ROOT / "data",
        output_dir=PACKAGE_ROOT / "results" / "reproduced",
    )

    assert set(module.COMPONENTS) == {
        "section3",
        "caged",
        "rais",
        "pnadc",
        "spatial",
    }
    assert {node.component for node in dag} >= set(module.COMPONENTS)


def test_section3_target_has_a_real_producer() -> None:
    module = load_runner()

    dag = module.build_dag(
        target="section3",
        mode="reproduce",
        raw_dir=PACKAGE_ROOT / "data" / "vintage",
        data_dir=PACKAGE_ROOT / "data",
        output_dir=PACKAGE_ROOT / "results" / "reproduced",
    )

    assert [node.node_id for node in dag] == [
        "validate_reference_manifest",
        "section3_reproduction",
    ]
    producer = dag[-1]
    assert producer.component == "section3"
    assert "section3" in " ".join(producer.command)


def test_active_r_environment_matches_the_complete_lock() -> None:
    module = load_runner()

    status = module.validate_r_environment()

    assert status == {
        "locked_packages": 73,
        "r_version": "4.4.1",
        "status": "pass",
    }


def test_full_mode_python_dependencies_are_directly_locked() -> None:
    expected = {
        "basedosdados": "2.0.2",
        "google-cloud-bigquery": "3.40.0",
        "google-cloud-bigquery-storage": "2.36.0",
        "seaborn": "0.13.2",
        "urllib3": "2.7.0",
    }
    project = (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    for package, version in expected.items():
        assert f'"{package}=={version}"' in project
        assert importlib.metadata.version(package) == version


def test_public_cli_accepts_target_and_legacy_section_aliases() -> None:
    module = load_runner()

    direct = module.parse_args(["--target", "pnadc"])
    legacy = module.parse_args(["--section", "4-5"])

    assert module.resolve_target(direct.target, direct.section) == "pnadc"
    assert module.resolve_target(legacy.target, legacy.section) == "all_except_section3"
    with pytest.raises(ValueError, match="cannot be combined"):
        module.resolve_target("rais", "3")


def test_full_pnadc_preflight_requires_an_explicit_billing_project(
    tmp_path: Path,
) -> None:
    module = load_runner()

    with pytest.raises(
        ValueError,
        match="Full PNADc reconstruction requires --billing-project",
    ):
        module.preflight(
            target="pnadc",
            mode="full",
            raw_dir=tmp_path / "raw",
            data_dir=tmp_path / "data",
            dag=(),
            billing_project=None,
        )


def test_default_output_is_reproduced_and_reference_is_never_a_destination() -> None:
    module = load_runner()

    args = module.parse_args([])
    assert args.output_dir == PACKAGE_ROOT / "results" / "reproduced"

    forbidden = (
        PACKAGE_ROOT / "code",
        PACKAGE_ROOT / "data",
        PACKAGE_ROOT / "results" / "reference",
    )
    for destination in forbidden:
        with pytest.raises(ValueError, match="immutable package path"):
            module.validate_output_dir(destination)


@pytest.mark.parametrize(
    ("protected_kind", "relation"),
    (
        ("data", "equal"),
        ("data", "descendant"),
        ("data", "ancestor"),
        ("raw", "equal"),
        ("raw", "descendant"),
        ("raw", "ancestor"),
    ),
)
def test_output_cannot_overlap_external_inputs(
    tmp_path: Path,
    protected_kind: str,
    relation: str,
) -> None:
    module = load_runner()
    protected = tmp_path / protected_kind / "bundle"
    data_dir = protected if protected_kind == "data" else tmp_path / "data"
    raw_dir = protected if protected_kind == "raw" else tmp_path / "raw"
    if relation == "equal":
        destination = protected
    elif relation == "descendant":
        destination = protected / "reproduced"
    else:
        destination = protected.parent

    with pytest.raises(ValueError, match="overlaps the external"):
        module.validate_output_dir(
            destination,
            data_dir=data_dir,
            raw_dir=raw_dir,
        )


def test_output_overlap_check_resolves_symlink_aliases(tmp_path: Path) -> None:
    module = load_runner()
    data_dir = tmp_path / "bundle"
    data_dir.mkdir()
    alias = tmp_path / "bundle-alias"
    alias.symlink_to(data_dir, target_is_directory=True)

    with pytest.raises(ValueError, match="overlaps the external analytical data"):
        module.validate_output_dir(
            alias / "reproduced",
            data_dir=data_dir,
            raw_dir=tmp_path / "raw",
        )


def test_disjoint_output_sibling_is_allowed(tmp_path: Path) -> None:
    module = load_runner()
    destination = tmp_path / "outputs" / "reproduced"

    validated = module.validate_output_dir(
        destination,
        data_dir=tmp_path / "inputs" / "data",
        raw_dir=tmp_path / "inputs" / "raw",
    )

    assert validated == destination.resolve()


def test_main_rejects_input_overlap_before_any_execution_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_runner()
    data_dir = tmp_path / "bundle"
    raw_dir = tmp_path / "raw"
    data_dir.mkdir()
    raw_dir.mkdir()
    destination = data_dir / "reproduced"
    calls: list[str] = []

    def unexpected_call(name: str):
        def fail(*args, **kwargs):
            calls.append(name)
            raise AssertionError(f"{name} ran before output validation")

        return fail

    for name in (
        "build_dag",
        "preflight",
        "prepare_output_directory",
        "materialize_execution_root",
        "prepare_full_rebuild_runtime",
        "run_dag",
    ):
        monkeypatch.setattr(module, name, unexpected_call(name))

    with pytest.raises(ValueError, match="overlaps the external analytical data"):
        module.main(
            [
                "--target",
                "section3",
                "--mode",
                "reproduce",
                "--data-dir",
                str(data_dir),
                "--raw-dir",
                str(raw_dir),
                "--output-dir",
                str(destination),
            ]
        )

    assert calls == []
    assert not destination.exists()


def test_nonempty_output_requires_a_valid_package_manifest(tmp_path: Path) -> None:
    module = load_runner()
    destination = tmp_path / "results"
    destination.mkdir()
    (destination / "unrelated.txt").write_text("user data", encoding="utf-8")

    with pytest.raises(ValueError, match="valid package run manifest"):
        module.prepare_output_directory(destination)


def test_full_rebuild_clears_only_isolated_rebuildable_inputs(
    tmp_path: Path,
) -> None:
    module = load_runner()
    runtime = tmp_path / "runtime"
    movement = runtime / "data" / "interim" / "movimentacoes" / "part.parquet"
    building = (
        runtime / "data" / "interim" / "movimentacoes.building" / "part.parquet"
    )
    panel = runtime / "data" / "derived" / "painel_nacional.parquet"
    preserved = runtime / "data" / "derived" / "section3" / "analytic.parquet"
    ipca_source = (
        runtime
        / "data"
        / "vintage"
        / "ipca"
        / "sgs_433_202101_202605.json"
    )
    cnae_source = (
        runtime / "data" / "vintage" / "cnae" / "cnae2.0_subclasses.zip"
    )
    for path in (
        movement,
        building,
        panel,
        preserved,
        ipca_source,
        cnae_source,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"frozen")

    removed = module.prepare_full_rebuild_runtime(runtime)

    assert "data/interim/movimentacoes" in removed
    assert "data/interim/movimentacoes.building" in removed
    assert "data/derived/painel_nacional.parquet" in removed
    assert not movement.exists()
    assert not building.exists()
    assert not panel.exists()
    assert preserved.read_bytes() == b"frozen"
    assert ipca_source.read_bytes() == b"frozen"
    assert cnae_source.read_bytes() == b"frozen"


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


def test_numeric_claim_reconciliation_is_scoped_to_selected_components(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = load_runner()
    observed: list[tuple[str, ...]] = []

    def fake_run(command, **_kwargs):
        observed.append(tuple(command))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    module.reconcile_numeric_claims(
        tmp_path,
        components=("section3", "spatial"),
    )

    command = observed[0]
    assert command.count("--component") == 2
    assert "section3" in command
    assert "spatial" in command
    assert str(tmp_path / "validation" / "numeric_claims_reconciliation.csv") in command
