#!/usr/bin/env python3
"""Semantic contracts and signed manifests for V2 reference artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = PACKAGE_ROOT / "results"
DEFAULT_REFERENCE = DEFAULT_RESULTS / "reference"
CONTRACTS_FILENAME = "artifact_contracts.json"
MANIFEST_FILENAME = "manifest.json"
ARTIFACTS_DIRNAME = "artifacts"
FORMAT_VERSION = 1

CATEGORY_TOKENS = {
    "category",
    "classification",
    "dimension",
    "estimator",
    "family",
    "gradient",
    "group",
    "label",
    "measure",
    "method",
    "mode",
    "model",
    "origin",
    "outcome",
    "role",
    "sample",
    "section",
    "sex",
    "source",
    "status",
    "step",
    "term",
    "treatment",
    "type",
}


class SemanticContractError(RuntimeError):
    """Raised when an artifact violates its declared meaning."""


class ManifestValidationError(RuntimeError):
    """Raised when a signed reference freeze is inconsistent."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _payload_digest(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _atomic_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def source_id_for(artifact_path: str) -> str:
    path = artifact_path.lower()
    component = ""
    for component in ("section3", "caged", "rais", "pnadc", "spatial"):
        prefix = f"{component}/"
        if path.startswith(prefix):
            path = path[len(prefix) :]
            break
    else:
        component = "caged"
    if component == "caged" and path in {"index.md", "publication_index.csv"}:
        return "code.replication.reference_validation"
    if component == "caged" and path.startswith("validation/"):
        return "code.replication.claims"
    if component == "section3":
        if "r_" in path or "cross_language" in path:
            return "code.section3.r_validation"
        return "code.section3.pipeline"
    if component in {"rais", "pnadc", "spatial"}:
        if path.startswith("tables/") or path == "artifact_index.json":
            return "code.render.complementary"
        if path.startswith("validation/"):
            return "code.replication.component_pipeline"
        if component == "rais":
            if "rais_pretrend_r_" in path:
                return "code.rais.r_pretrend_replication"
            if "rais_cross_replication" in path:
                return "code.rais.r12_cross_replication"
            if "rais_static_results" in path:
                return "code.rais.r9_static"
            if "rais_pretrends" in path:
                return "code.rais.r8_pretrends"
            if "rais_sensitivities" in path:
                return "code.rais.r10_sensitivities"
            if "rais_support" in path:
                return "code.rais.part1"
        if component == "pnadc":
            if "pnadc_pretrend_cross_" in path:
                return "code.pnadc.pnadc_pretrend_cross_replication"
            if "pnadc_cross_replication" in path:
                return "code.pnadc.pnadc_cross_replication"
            if "pnadc_sensitivities" in path:
                return "code.pnadc.pnadc_sensitivities"
            if "pnadc_pretrends" in path:
                return "code.pnadc.pnadc_pretrends"
            if "pnadc_results" in path or "pnadc_support" in path:
                return "code.pnadc.pnadc_estimation"
        if component == "spatial":
            if "spatial_r_" in path:
                return "code.spatial.spatial_r_replication"
            if "family_f_declaration" in path or "anatel_a6_" in path:
                return "code.spatial.support"
            if "anatel_" in path or "spatial_pretrend_coefficients" in path:
                return "code.spatial.diagnostics"
        raise SemanticContractError(
            f"No {component} source declaration for artifact: {artifact_path}"
        )
    if path.startswith("tables/"):
        return "code.render.phase8b_tables"
    if path.startswith(
        "backing_data/figure_5_2_6_group_outcome_forest"
    ):
        return "code.render.phase8b_tables"
    if path.startswith("figures/figure_5_2_3_3_canaries"):
        return "code.render.canaries_wage_figure"
    if path.startswith("figures/"):
        return "code.render.phase8b_figures"
    if path.startswith("treatment/"):
        return "code.caged.panel.treatment_variants"
    if path.startswith("models/group_did"):
        return "code.caged.models.group_did_results"
    if path.startswith("models/group_event_stud"):
        return "code.caged.models.group_event_studies"
    if path.startswith("models/canaries"):
        return "code.caged.models.canaries_wage_event_study"
    if path.startswith("models/national_event_study_extended"):
        return "code.caged.models.national_event_study_extended"
    if path.startswith("models/long_run_horizon_estimates") or path.startswith(
        "models/long_run_horizon_reconciliation"
    ) or path.startswith("models/long_run_horizons_support") or path.endswith(
        "models/long_run_horizons.md"
    ):
        return "code.caged.models.long_run_horizons"
    if path.startswith("models/pretrend_control") or path.endswith(
        "models/pretrend_control_specification.md"
    ):
        return "code.caged.models.pretrend_control_spec"
    if path.startswith("models/event_study") or path.endswith(
        "models/long_run_horizons.csv"
    ):
        return "code.caged.models.event_study"
    if path.startswith("models/specification_ladder"):
        return "code.caged.models.specification_ladder"
    if path.startswith("models/secondary_log_flow") or path.endswith(
        "models/secondary_flow_estimators.md"
    ):
        return "code.caged.models.secondary_flow_models"
    if path.startswith("models/sector") or path.endswith(
        "models/01_sector_fixed_effect_support.csv"
    ):
        return "code.caged.models.sector_models"
    if path.startswith("diagnostics/pretrend_master") or path.endswith(
        "diagnostics/diagnostico_pretrends.md"
    ):
        return "code.caged.models.pretrend_report"
    if path.startswith(
        (
            "diagnostics/pretrend_sample_2022",
            "diagnostics/pretrend_power_check",
            "diagnostics/pretrend_ladder_variants",
            "diagnostics/pretrend_wage_balanced_coverage",
            "diagnostics/pretrend_national_variants_support",
            "diagnostics/pretrend_national_variants_coefficients",
        )
    ):
        return "code.caged.models.pretrend_national_variants"
    if path.startswith("diagnostics/pretrend_level2"):
        return "code.caged.models.pretrend_sector"
    if path.startswith("diagnostics/cbo_pre_period_slopes"):
        return "code.caged.models.pretrend_control_spec"
    if path.startswith("diagnostics/pretrend") or path.endswith(
        "diagnostics/pretrend_diagnostics.md"
    ):
        return "code.caged.models.pretrends"
    if path.startswith(
        (
            "diagnostics/honest_did_event_coefficients",
            "diagnostics/honest_did_event_vcov_long",
        )
    ):
        return "code.caged.models.pretrends"
    if path.startswith(
        (
            "diagnostics/honest_did_delta_comparison",
            "diagnostics/honest_did_sensitivity",
            "diagnostics/honest_did_summary",
        )
    ):
        return "R.honest_did_sd"
    if "honest_did" in path:
        return "R.honest_did"
    if path.startswith(
        (
            "diagnostics/ddd_pretrends",
            "diagnostics/ddd_alternative_partitions_pretrends",
        )
    ):
        return "code.caged.models.ddd_pretrends"
    if "ddd_" in path or path.endswith(
        "diagnostics/ddd_multiplicity_results.md"
    ):
        return "code.caged.models.heterogeneity"
    if "placebo" in path:
        return "code.caged.models.placebos"
    if path.startswith("mechanisms/separation"):
        return "code.caged.models.separation_mechanisms"
    if path.startswith("mechanisms/stock_proxy"):
        return "code.caged.models.stock_proxy"
    if path.startswith("mechanisms/hourly_wage"):
        return "code.caged.models.hourly_wage"
    if path.startswith("mechanisms/employer"):
        return "code.caged.models.employer_size"
    if path.startswith("mechanisms/exposure"):
        return "code.caged.models.exposure_sensitivity"
    if path.startswith("mechanisms/occupation_case_trajector") or path.startswith(
        "mechanisms/occupation_case_terminal"
    ) or path.endswith("mechanisms/occupation_case_trajectories.md"):
        return "code.caged.models.occupation_case_trajectories"
    if path.startswith("mechanisms/occupation_case") or path.endswith(
        (
            "mechanisms/occupation_case_monthly_coverage.md",
            "mechanisms/occupation_case_preperiod_diagnostics.md",
        )
    ):
        return "code.caged.panel.occupation_cases"
    if path.startswith("replication/complete_r/"):
        if path.endswith(
            (
                "python_r_model_comparison.csv",
                "python_r_pretrend_comparison.csv",
                "python_r_honest_did_coefficient_comparison.csv",
                "python_r_honest_did_vcov_comparison.csv",
                "comparison_status.json",
            )
        ):
            return "code.replication.r_validation"
        return "R.complete_replication"
    if path.startswith("audit/"):
        if path.startswith("audit/a"):
            return "code.caged.audit.wage_composition"
        if path.startswith("audit/b"):
            return "code.caged.audit.jackknife_occupations"
        if path.startswith(("audit/c", "audit/d")):
            return "code.caged.audit.exposure_and_control"
        if path.startswith("audit/e"):
            return "code.caged.audit.transfer_share"
    if path == "mechanisms/employer_size.md":
        return "code.caged.models.employer_size"
    if path == "mechanisms/hourly_wage.md":
        return "code.caged.models.hourly_wage"
    if path == "mechanisms/separation_mechanisms.md":
        return "code.caged.models.separation_mechanisms"
    if path == "mechanisms/stock_proxy.md":
        return "code.caged.models.stock_proxy"
    if path == "mechanisms/exposure_measure_sensitivity.md":
        return "code.caged.models.exposure_sensitivity"
    if path.startswith("reconciliation/pdet_"):
        return "code.caged.ingest.reconcile_pdet"
    if path.startswith("reconciliation/gate_modelo_antigo"):
        return "code.caged.models.gate_v1_model"
    if path.startswith("reconciliation/crosswalk_coverage") or path.startswith(
        "reconciliation/treatment_classification"
    ):
        return "code.caged.panel.crosswalk"
    if path.startswith("reconciliation/painel_") or path.startswith(
        "reconciliation/cnae_month"
    ):
        return "code.caged.panel.build_panel"
    if path.startswith("reconciliation/build_movements"):
        return "code.caged.ingest.build_movements"
    if path.startswith("reconciliation/"):
        return "code.caged.ingest.diagnose_vintage"
    raise SemanticContractError(
        f"No source declaration for artifact: {artifact_path}"
    )


def _is_category_column(column: str) -> bool:
    tokens = {
        token
        for token in column.lower().replace("-", "_").split("_")
        if token
    }
    return bool(tokens & CATEGORY_TOKENS)


def _unit_for(column: str) -> str:
    name = column.lower()
    if "p_value" in name or name in {"p", "pvalue"}:
        return "probability"
    if "share" in name or name.startswith("pct_"):
        return "proportion_or_percentage_as_declared_by_source"
    if "percent" in name or name.endswith("_pct"):
        return "percent"
    if any(
        token in name
        for token in (
            "count",
            "rows",
            "cells",
            "clusters",
            "months",
            "families",
            "observations",
            "n_obs",
        )
    ):
        return "count"
    if name in {
        "coefficient",
        "standard_error",
        "ci_low",
        "ci_high",
        "estimate",
    }:
        return "model_outcome_scale"
    return "declared_in_source"


def infer_csv_contract(
    frame: pd.DataFrame,
    *,
    artifact_path: str,
    source_id: str,
) -> dict[str, Any]:
    categorical_domains: dict[str, list[str]] = {}
    for column in frame.columns:
        if not _is_category_column(str(column)):
            continue
        values = sorted(
            {
                str(value)
                for value in frame[column].tolist()
                if str(value) != ""
            }
        )
        if len(values) <= 200:
            categorical_domains[str(column)] = values
    return {
        "artifact_path": artifact_path,
        "categorical_domains": categorical_domains,
        "columns": [str(column) for column in frame.columns],
        "json_top_level_keys": [],
        "media_type": "text/csv",
        "source_id": source_id,
        "units": {
            str(column): _unit_for(str(column))
            for column in frame.columns
        },
    }


def infer_artifact_contract(path: Path, artifact_path: str) -> dict[str, Any]:
    source_id = source_id_for(artifact_path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        return infer_csv_contract(
            frame,
            artifact_path=artifact_path,
            source_id=source_id,
        )
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        keys = sorted(payload) if isinstance(payload, dict) else []
        media_type = "application/json"
    elif suffix == ".md":
        keys = []
        media_type = "text/markdown"
    elif suffix == ".png":
        keys = []
        media_type = "image/png"
    else:
        raise SemanticContractError(
            f"Unsupported reference artifact type: {artifact_path}"
        )
    return {
        "artifact_path": artifact_path,
        "categorical_domains": {},
        "columns": [],
        "json_top_level_keys": keys,
        "media_type": media_type,
        "source_id": source_id,
        "units": {},
    }


def validate_artifact_semantics(
    path: Path,
    contract: dict[str, Any],
) -> None:
    if not contract.get("source_id"):
        raise SemanticContractError(
            f"Missing source_id for {contract.get('artifact_path')}"
        )
    if "categorical_domains" not in contract:
        raise SemanticContractError(
            f"Missing category declaration for {contract['artifact_path']}"
        )
    media_type = contract["media_type"]
    if media_type == "text/csv":
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        columns = [str(column) for column in frame.columns]
        if columns != contract["columns"]:
            raise SemanticContractError(
                f"Column contract failed for {contract['artifact_path']}: "
                f"expected {contract['columns']}, got {columns}"
            )
        for column, allowed in contract["categorical_domains"].items():
            observed = {
                str(value)
                for value in frame[column].tolist()
                if str(value) != ""
            }
            unexpected = sorted(observed - set(allowed))
            if unexpected:
                raise SemanticContractError(
                    f"Category contract failed for {column} in "
                    f"{contract['artifact_path']}: {unexpected}"
                )
    elif media_type == "application/json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        observed = sorted(payload) if isinstance(payload, dict) else []
        if observed != contract["json_top_level_keys"]:
            raise SemanticContractError(
                f"JSON-key contract failed for "
                f"{contract['artifact_path']}"
            )
    elif media_type == "image/png":
        if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise SemanticContractError(
                f"Invalid PNG signature: {contract['artifact_path']}"
            )
    elif media_type == "text/markdown":
        if not path.read_text(encoding="utf-8").strip():
            raise SemanticContractError(
                f"Empty Markdown artifact: {contract['artifact_path']}"
            )
    else:
        raise SemanticContractError(f"Unknown media type: {media_type}")


# Registered audit outputs back narrative values in the manuscript and are
# therefore part of the signed replication evidence.
EXCLUDED_FROM_REFERENCE: tuple[str, ...] = ()


def _result_artifacts(results_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in results_dir.rglob("*")
        if path.is_file()
        and DEFAULT_REFERENCE.name
        not in path.relative_to(results_dir).parts
        and not any(
            part in EXCLUDED_FROM_REFERENCE
            for part in path.relative_to(results_dir).parts
        )
        and not any(
            part.startswith(".")
            for part in path.relative_to(results_dir).parts
        )
    )


def freeze_reference(
    results_dir: Path = DEFAULT_RESULTS,
    reference_dir: Path = DEFAULT_REFERENCE,
) -> dict[str, Any]:
    artifacts = _result_artifacts(results_dir)
    if not artifacts:
        raise ManifestValidationError("No result artifacts to freeze")
    artifact_root = reference_dir / ARTIFACTS_DIRNAME
    artifact_root.mkdir(parents=True, exist_ok=True)
    contracts: dict[str, dict[str, Any]] = {}
    manifest_entries: list[dict[str, Any]] = []
    expected_paths: set[Path] = set()
    for source in artifacts:
        relative = source.relative_to(results_dir)
        artifact_path = relative.as_posix()
        destination = artifact_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(
            f"{destination.suffix}.tmp"
        )
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
        expected_paths.add(destination.resolve())
        contract = infer_artifact_contract(source, artifact_path)
        validate_artifact_semantics(destination, contract)
        contracts[artifact_path] = contract
        manifest_entries.append(
            {
                "bytes": destination.stat().st_size,
                "path": artifact_path,
                "sha256": sha256_file(destination),
            }
        )
    actual_paths = {
        path.resolve()
        for path in artifact_root.rglob("*")
        if path.is_file()
    }
    stale = sorted(str(path) for path in actual_paths - expected_paths)
    if stale:
        raise ManifestValidationError(
            "Reference directory contains stale artifacts: " + ", ".join(stale)
        )

    contracts_payload = {
        "artifacts": contracts,
        "format_version": FORMAT_VERSION,
    }
    contracts_path = reference_dir / CONTRACTS_FILENAME
    _atomic_json(contracts_payload, contracts_path)
    unsigned_manifest = {
        "artifacts": manifest_entries,
        "contracts_sha256": sha256_file(contracts_path),
        "format_version": FORMAT_VERSION,
        "signature_scope": (
            "canonical JSON of all manifest fields except signature"
        ),
    }
    manifest = {
        **unsigned_manifest,
        "signature": {
            "algorithm": "sha256",
            "digest": _payload_digest(unsigned_manifest),
        },
    }
    _atomic_json(manifest, reference_dir / MANIFEST_FILENAME)
    return validate_reference(reference_dir)


def validate_reference(
    reference_dir: Path = DEFAULT_REFERENCE,
) -> dict[str, Any]:
    manifest_path = reference_dir / MANIFEST_FILENAME
    contracts_path = reference_dir / CONTRACTS_FILENAME
    if not manifest_path.is_file() or not contracts_path.is_file():
        raise ManifestValidationError(
            "Reference manifest or semantic contracts are missing"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    signature = manifest.get("signature", {})
    unsigned = {
        key: value
        for key, value in manifest.items()
        if key != "signature"
    }
    if signature.get("algorithm") != "sha256" or signature.get(
        "digest"
    ) != _payload_digest(unsigned):
        raise ManifestValidationError(
            "Signed manifest digest does not validate"
        )
    if manifest.get("contracts_sha256") != sha256_file(contracts_path):
        raise ManifestValidationError(
            "Semantic-contract SHA-256 mismatch"
        )
    contracts_payload = json.loads(
        contracts_path.read_text(encoding="utf-8")
    )
    contracts = contracts_payload.get("artifacts", {})
    entries = manifest.get("artifacts", [])
    entry_paths = [entry["path"] for entry in entries]
    if len(entry_paths) != len(set(entry_paths)):
        raise ManifestValidationError("Duplicate artifact in manifest")
    if set(entry_paths) != set(contracts):
        raise ManifestValidationError(
            "Manifest and semantic-contract artifact sets differ"
        )
    artifact_root = reference_dir / ARTIFACTS_DIRNAME
    actual_paths = {
        path.relative_to(artifact_root).as_posix()
        for path in artifact_root.rglob("*")
        if path.is_file()
    }
    if actual_paths != set(entry_paths):
        raise ManifestValidationError(
            "Reference directory and manifest artifact sets differ"
        )
    for entry in entries:
        path = artifact_root / entry["path"]
        if path.stat().st_size != entry["bytes"]:
            raise ManifestValidationError(
                f"Byte-size mismatch for {entry['path']}"
            )
        if sha256_file(path) != entry["sha256"]:
            raise ManifestValidationError(
                f"SHA-256 mismatch for {entry['path']}"
            )
        try:
            validate_artifact_semantics(path, contracts[entry["path"]])
        except SemanticContractError as error:
            raise ManifestValidationError(str(error)) from error
    return {
        "artifacts": len(entries),
        "all_sources_declared": all(
            bool(contract.get("source_id"))
            for contract in contracts.values()
        ),
        "all_category_domains_declared": all(
            "categorical_domains" in contract
            for contract in contracts.values()
        ),
        "manifest_signature_valid": True,
        "semantic_contracts_valid": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze or validate V2 reference artifacts."
    )
    parser.add_argument(
        "action",
        choices=("freeze", "validate"),
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS,
    )
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=DEFAULT_REFERENCE,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.action == "freeze":
        summary = freeze_reference(
            args.results_dir,
            args.reference_dir,
        )
    else:
        summary = validate_reference(args.reference_dir)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
