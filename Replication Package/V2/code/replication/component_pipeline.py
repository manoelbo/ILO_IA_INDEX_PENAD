#!/usr/bin/env python3
"""Shared command-line contract for complementary evidence components."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = PACKAGE_ROOT / "code"
COMMON_ROOT = CODE_ROOT / "common"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from paths import ReplicationPaths

REFERENCE_ARTIFACTS = PACKAGE_ROOT / "results" / "reference" / "artifacts"

COMPONENT_SOURCES = {
    "rais": PACKAGE_ROOT / "code" / "rais",
    "pnadc": PACKAGE_ROOT / "code" / "pnadc",
    "spatial": PACKAGE_ROOT / "code" / "spatial",
}
COMPONENT_PACKAGES = {
    "rais": "v2_rais",
    "pnadc": "v2_pnadc",
    "spatial": "v2_spatial",
}
FULL_REQUIRED_CONTRACTS: dict[str, tuple[str, ...]] = {
    # P-B1 is the frozen authorization gate between panel construction and
    # estimation. Full mode reconstructs both panels, while the registered
    # gate remains an immutable analytical contract that downstream scripts
    # must validate against those reconstructed panels.
    "pnadc": ("pnadc_part1_status.json",),
}
SPATIAL_OFFICIAL_VINTAGE_FILES = (
    "Acessos_Banda_Larga_Fixa_2021.csv",
    "Acessos_Banda_Larga_Fixa_2022.csv",
    "Acessos_Banda_Larga_Fixa_Total.csv",
    "Densidade_Banda_Larga_Fixa.csv",
)

REPRODUCE_COMMANDS: dict[str, tuple[tuple[str, ...], ...]] = {
    "rais": (
        ("part1.py",),
        ("r8_pretrends.py",),
        ("r_pretrend_replication.py",),
        ("r9_static.py",),
        ("r10_sensitivities.py", "replay-diagnostic"),
        ("r10_sensitivities.py", "estimate"),
        ("r11_proxy_validation.py",),
        ("r12_cross_replication.py",),
    ),
    "pnadc": (
        ("pnadc_pretrends.py",),
        ("pnadc_pretrend_cross_replication.py",),
        ("pnadc_estimation.py",),
        ("pnadc_sensitivities.py",),
        ("pnadc_cross_replication.py",),
    ),
    "spatial": (
        ("diagnostics.py",),
        ("support.py",),
        ("spatial_r_replication.py",),
    ),
}

FULL_COMMANDS: dict[str, tuple[tuple[str, ...], ...]] = {
    "rais": (
        ("stage0.py", "probe"),
        ("stage0.py", "acquire"),
        ("stage0.py", "reconciliation-source"),
        ("stage0.py", "reconcile"),
        ("stage0.py", "esocial-break"),
        ("stage0.py", "gate"),
        *REPRODUCE_COMMANDS["rais"],
    ),
    "pnadc": (
        ("stage0.py", "acquire"),
        ("stage0.py", "reconcile"),
        ("stage0.py", "crosswalk"),
        ("stage0.py", "support"),
        ("stage0.py", "break-2020"),
        ("panels.py", "individual"),
        ("panels.py", "cod3"),
        *REPRODUCE_COMMANDS["pnadc"],
    ),
    "spatial": (
        ("late_declarations.py", "--acknowledge-incompatible-benchmark"),
        ("vintage.py",),
        ("panel.py",),
        *REPRODUCE_COMMANDS["spatial"],
    ),
}


def parse_args(
    component: str,
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Reproduce the registered {component} evidence."
    )
    parser.add_argument("--mode", choices=("reproduce", "full"), required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--billing-project")
    parser.add_argument("--skip-figures", action="store_true")
    return parser.parse_args(argv)


def _clone_or_copy(source: str, destination: str) -> str:
    completed = subprocess.run(
        ["/bin/cp", "-c", source, destination],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        shutil.copy2(source, destination)
    return destination


def _copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        copy_function=_clone_or_copy,
        ignore=shutil.ignore_patterns(
            ".DS_Store",
            ".pytest_cache",
            "__pycache__",
            "*.pyc",
            "*.7z",
            "test_*.py",
        ),
    )


def _copy_contents(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.iterdir()):
        target = destination / path.name
        if path.is_dir():
            shutil.copytree(
                path,
                target,
                dirs_exist_ok=True,
                copy_function=_clone_or_copy,
            )
        else:
            _clone_or_copy(str(path), str(target))


def _spatial_vintage_reuse_allowed(vintage: Path) -> bool:
    """Validate whether a separately supplied spatial raw snapshot is complete."""
    present = {
        name
        for name in SPATIAL_OFFICIAL_VINTAGE_FILES
        if (vintage / name).is_file()
    }
    has_manifest = (vintage / "manifest.json").is_file()
    if has_manifest and present != set(SPATIAL_OFFICIAL_VINTAGE_FILES):
        raise RuntimeError(
            "Spatial raw vintage manifest is incomplete; supply all four "
            "registered Anatel extracts or omit the manifest"
        )
    return bool(has_manifest)


def _stage_runtime(
    component: str,
    *,
    data_dir: Path,
    raw_dir: Path,
    mode: str,
    work_dir: Path,
) -> tuple[Path, Path, bool]:
    runtime_root = work_dir / "V2"
    front_root = runtime_root / "components" / component
    runtime_root.mkdir(parents=True)
    _copy_tree(PACKAGE_ROOT / "code", runtime_root / "code")
    _copy_tree(data_dir, runtime_root / "data")
    (runtime_root / "results").mkdir()
    if REFERENCE_ARTIFACTS.is_dir():
        caged_reference = REFERENCE_ARTIFACTS / "caged"
        _copy_contents(
            caged_reference if caged_reference.is_dir() else REFERENCE_ARTIFACTS,
            runtime_root / "results",
        )

    source = COMPONENT_SOURCES[component]
    component_package = COMPONENT_PACKAGES[component]
    _copy_tree(source, front_root / component_package)
    component_data = data_dir / "derived" / component
    if not component_data.is_dir():
        raise FileNotFoundError(
            f"Missing analytical bundle component: {component_data}"
        )
    _copy_tree(component_data, front_root / "data")
    (front_root / "results").mkdir()
    contracts = front_root / "data" / "contracts"
    if mode == "reproduce" and contracts.is_dir():
        _copy_contents(contracts, front_root / "results")
    elif mode == "full":
        for filename in FULL_REQUIRED_CONTRACTS.get(component, ()):
            source_contract = contracts / filename
            if not source_contract.is_file():
                raise FileNotFoundError(
                    f"Missing required full-mode contract: {source_contract}"
                )
            _clone_or_copy(
                str(source_contract),
                str(front_root / "results" / filename),
            )

    use_existing_spatial_vintage = False
    if mode == "full":
        raw_component = raw_dir / component
        if component == "spatial":
            vintage = front_root / "data" / "vintage"
            # The analytical bundle contains a frozen spatial snapshot for
            # offline reproduction. Full mode may reuse only a separately
            # supplied official-source snapshot; otherwise it downloads the
            # registered Anatel vintage again.
            for name in (*SPATIAL_OFFICIAL_VINTAGE_FILES, "manifest.json"):
                candidate = vintage / name
                if candidate.is_file():
                    candidate.unlink()
        if raw_component.is_dir():
            _copy_contents(raw_component, front_root / "data" / "vintage")
        if component == "spatial":
            vintage = front_root / "data" / "vintage"
            use_existing_spatial_vintage = _spatial_vintage_reuse_allowed(
                vintage
            )
    return runtime_root, front_root, use_existing_spatial_vintage


def _run_commands(
    component: str,
    *,
    mode: str,
    runtime_root: Path,
    front_root: Path,
    billing_project: str | None,
    use_existing_spatial_vintage: bool = False,
) -> None:
    environment = os.environ.copy()
    for variable in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMBA_NUM_THREADS",
    ):
        environment[variable] = "1"
    if billing_project:
        environment["REPLICATION_BILLING_PROJECT"] = billing_project
    environment.update(
        ReplicationPaths(
            package=runtime_root,
            data=runtime_root / "data",
            raw=front_root / "data" / "vintage",
            reference=runtime_root / "results" / "reference",
            reproduced=front_root / "results",
            work=runtime_root / ".replication-work",
        ).environment()
    )
    python_paths = [str(front_root), str(runtime_root / "code")]
    if environment.get("PYTHONPATH"):
        python_paths.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(python_paths)
    commands = REPRODUCE_COMMANDS if mode == "reproduce" else FULL_COMMANDS
    for command in commands[component]:
        component_package = COMPONENT_PACKAGES[component]
        script = front_root / component_package / command[0]
        if not script.is_file():
            raise FileNotFoundError(script)
        arguments = list(command[1:])
        if (
            component == "spatial"
            and mode == "full"
            and command[0] == "vintage.py"
            and use_existing_spatial_vintage
        ):
            arguments.append("--process-existing")
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                f"{component_package}.{script.stem}",
                *arguments,
            ],
            cwd=runtime_root,
            env=environment,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"{component} command failed ({completed.returncode}): "
                + " ".join(command)
            )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bundle_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(path.rglob("*")):
        if not file.is_file():
            continue
        relative = file.relative_to(path).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(_sha256(file).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cross_language_difference(
    status: dict[str, object],
    *keys: str,
) -> float:
    for key in keys:
        if key in status:
            return float(status[key])
    raise KeyError(f"Missing cross-language difference: {keys}")


def validate_component_results(
    component: str,
    results_dir: Path,
) -> dict[str, object]:
    """Validate the public scientific contract without experiment reports."""
    results_dir = results_dir.resolve()
    if component == "rais":
        estimates = pd.read_csv(results_dir / "rais_static_results.csv")
        pretrends = pd.read_csv(results_dir / "rais_pretrends.csv")
        cross = _read_json(results_dir / "rais_cross_replication_status.json")
        pretrend_cross = _read_json(results_dir / "rais_pretrend_r_status.json")
        valid_family = bool(
            len(estimates) == 3
            and estimates["family_id"].eq("D").all()
            and estimates["family_size"].astype(int).eq(3).all()
            and estimates["multiplicity_method"].eq(
                "Benjamini-Hochberg"
            ).all()
        )
        coefficient_difference = _cross_language_difference(
            cross,
            "max_coefficient_absolute_difference",
            "maximum_coefficient_absolute_difference",
        )
        standard_error_difference = _cross_language_difference(
            cross,
            "max_standard_error_absolute_difference",
            "maximum_standard_error_absolute_difference",
        )
        cross_pass = bool(
            cross.get("status") == "pass"
            and cross.get("same_n_and_clusters") is True
            and coefficient_difference <= 1e-6
            and standard_error_difference <= 1e-6
        )
        if (
            not valid_family
            or not cross_pass
            or len(pretrends) != 3
            or pretrend_cross.get("status") != "pass"
            or int(pretrend_cross.get("failed_models", -1)) != 0
        ):
            raise RuntimeError("RAIS public scientific contract failed")
        return {
            "causal_effect_claim_authorized": False,
            "component": "rais",
            "cross_language_max_coefficient_difference": coefficient_difference,
            "cross_language_max_standard_error_difference": standard_error_difference,
            "cross_language_status": "pass",
            "cross_language_pretrend_models": int(
                pretrend_cross["models"]
            ),
            "family": "D",
            "family_size": 3,
            "interpretation": "complementary_measurement_evidence",
            "pretrend_failures": int(
                pretrends["pretrend_status"].eq("fail").sum()
            ),
            "status": "pass_with_noncausal_limit",
        }

    if component == "pnadc":
        estimates = pd.read_csv(results_dir / "pnadc_results.csv")
        pretrends = pd.read_csv(results_dir / "pnadc_pretrends.csv")
        result_status_path = results_dir / "pnadc_results_status.json"
        if result_status_path.is_file():
            adjustment_once = bool(
                int(
                    _read_json(result_status_path).get(
                        "family_e_adjustment_calls", 0
                    )
                )
                == 1
            )
        else:
            adjustment_once = bool(
                estimates["multiplicity_method"]
                .eq("Benjamini-Hochberg")
                .all()
                and estimates["multiplicity_scope"].nunique() == 1
                and estimates["bh_adjusted_p_value"].notna().all()
            )
        cross = _read_json(results_dir / "pnadc_cross_replication_status.json")
        pretrend_cross = _read_json(
            results_dir / "pnadc_pretrend_cross_status.json"
        )
        valid_family = bool(
            len(estimates) == 6
            and estimates["family_id"].eq("E").all()
            and estimates["family_size"].astype(int).eq(6).all()
            and adjustment_once
        )
        coefficient_difference = _cross_language_difference(
            cross,
            "maximum_coefficient_absolute_difference",
            "max_coefficient_absolute_difference",
        )
        standard_error_difference = _cross_language_difference(
            cross,
            "maximum_standard_error_absolute_difference",
            "max_standard_error_absolute_difference",
        )
        cross_pass = bool(
            cross.get("status") == "pass"
            and cross.get("same_n_and_clusters") is True
            and coefficient_difference <= 1e-6
            and standard_error_difference <= 1e-6
        )
        all_pretrends_fail = bool(
            len(pretrends) == 12
            and pretrends["pretrend_status"].eq("fail").all()
        )
        if (
            not valid_family
            or not cross_pass
            or not all_pretrends_fail
            or pretrend_cross.get("status") != "pass"
            or int(pretrend_cross.get("failed_models", -1)) != 0
        ):
            raise RuntimeError("PNADc public scientific contract failed")
        return {
            "causal_effect_claim_authorized": False,
            "component": "pnadc",
            "cross_language_max_coefficient_difference": coefficient_difference,
            "cross_language_max_standard_error_difference": standard_error_difference,
            "cross_language_status": "pass",
            "cross_language_pretrend_models": int(
                pretrend_cross["models"]
            ),
            "family": "E",
            "family_size": 6,
            "interpretation": "complementary_composition_and_stock_evidence",
            "pretrend_failures": 12,
            "status": "pass_with_noncausal_limit",
        }

    if component == "spatial":
        placebo = pd.read_csv(results_dir / "anatel_placebo_dec2021.csv")
        family_path = results_dir / "anatel_family_f_declaration.csv"
        if not family_path.is_file():
            family_path = results_dir / "family_f_declaration.csv"
        family = pd.read_csv(family_path)
        gate = _read_json(results_dir / "anatel_a6_status.json")
        cross = _read_json(results_dir / "spatial_r_status.json")
        estimated = int(family["coefficient"].notna().sum())
        p_values = int(
            family[["p_value", "bh_adjusted_p_value"]].notna().sum().sum()
        )
        valid_stop = bool(
            len(family) == 12
            and family["family"].eq("F").all()
            and estimated == 0
            and p_values == 0
            and placebo["real_treatment_coefficient_estimated"].eq(False).all()
            and gate.get("real_treatment_coefficient_estimated") is False
            and gate.get("stopped_before_a7") is True
            and isinstance(gate.get("gate"), dict)
            and gate["gate"].get("opens") is False
            and cross.get("status") == "pass"
            and int(cross.get("failed_coefficient_rows", -1)) == 0
            and int(cross.get("failed_pretrend_models", -1)) == 0
            and int(cross.get("failed_support_proxies", -1)) == 0
            and cross.get("family_f_support_stop_replicated") is True
        )
        if not valid_stop:
            raise RuntimeError("Spatial support-stop contract failed")
        return {
            "causal_effect_claim_authorized": False,
            "component": "spatial",
            "declared_slots": 12,
            "estimated_coefficients": 0,
            "family": "F",
            "cross_language_status": "pass",
            "cross_language_max_coefficient_difference": float(
                cross["maximum_coefficient_absolute_difference"]
            ),
            "cross_language_max_standard_error_difference": float(
                cross["maximum_standard_error_absolute_difference"]
            ),
            "p_values_created": 0,
            "status": "stopped_at_support_gate",
            "support_gate_open": False,
        }

    raise ValueError(f"Unsupported complementary component: {component}")


def _write_component_validation(
    status: dict[str, object],
    output_dir: Path,
) -> None:
    destination = output_dir / "validation" / "component_status.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, destination)


def _write_manifest(
    component: str,
    *,
    mode: str,
    data_component: Path,
    output_dir: Path,
) -> None:
    artifacts = [
        {
            "bytes": path.stat().st_size,
            "path": path.relative_to(output_dir).as_posix(),
            "sha256": _sha256(path),
        }
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path.name != "run_manifest.json"
    ]
    payload = {
        "analytical_bundle_sha256": _bundle_digest(data_component),
        "artifacts": artifacts,
        "component": component,
        "failure_count": 0,
        "format_version": 1,
        "mode": mode,
        "package_id": "dissertation-replication-v2",
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main_for(component: str, argv: Sequence[str] | None = None) -> int:
    args = parse_args(component, argv)
    if component not in COMPONENT_SOURCES:
        raise ValueError(f"Unsupported component: {component}")
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Component output is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f"replication-{component}-",
        dir=output_dir.parent,
    ) as temporary_directory:
        runtime_root, front_root, use_existing_spatial_vintage = _stage_runtime(
            component,
            data_dir=args.data_dir.resolve(),
            raw_dir=args.raw_dir.resolve(),
            mode=args.mode,
            work_dir=Path(temporary_directory),
        )
        _run_commands(
            component,
            mode=args.mode,
            runtime_root=runtime_root,
            front_root=front_root,
            billing_project=args.billing_project,
            use_existing_spatial_vintage=use_existing_spatial_vintage,
        )
        if str(CODE_ROOT) not in sys.path:
            sys.path.insert(0, str(CODE_ROOT))
        from render.complementary import render_component

        render_component(
            component,
            results_dir=front_root / "results",
            output_dir=output_dir,
        )
        status = validate_component_results(component, front_root / "results")
        _write_component_validation(status, output_dir)
    _write_manifest(
        component,
        mode=args.mode,
        data_component=args.data_dir.resolve() / "derived" / component,
        output_dir=output_dir,
    )
    return 0
