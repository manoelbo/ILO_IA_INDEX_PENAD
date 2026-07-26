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
    if path.startswith("treatment/"):
        return "code.panel.treatment_variants"
    if path.startswith("models/event_study") or path.endswith(
        "models/long_run_horizons.csv"
    ):
        return "code.models.event_study"
    if path.startswith("models/specification_ladder"):
        return "code.models.specification_ladder"
    if path.startswith("models/secondary_log_flow") or path.endswith(
        "models/secondary_flow_estimators.md"
    ):
        return "code.models.secondary_flow_models"
    if path.startswith("models/sector") or path.endswith(
        "models/01_sector_fixed_effect_support.csv"
    ):
        return "code.models.sector_models"
    if path.startswith("diagnostics/pretrend") or path.endswith(
        "diagnostics/pretrend_diagnostics.md"
    ):
        return "code.models.pretrends"
    if "honest_did" in path:
        return "R.honest_did"
    if "ddd_" in path or path.endswith(
        "diagnostics/ddd_multiplicity_results.md"
    ):
        return "code.models.heterogeneity"
    if "placebo" in path:
        return "code.models.placebos"
    if path.startswith("mechanisms/separation"):
        return "code.models.separation_mechanisms"
    if path.startswith("mechanisms/stock_proxy"):
        return "code.models.stock_proxy"
    if path.startswith("mechanisms/hourly_wage"):
        return "code.models.hourly_wage"
    if path.startswith("mechanisms/employer"):
        return "code.models.employer_size"
    if path.startswith("mechanisms/exposure"):
        return "code.models.exposure_sensitivity"
    if path.startswith("replication/cross_replication"):
        return "R.cross_replication"
    if path == "mechanisms/employer_size.md":
        return "code.models.employer_size"
    if path == "mechanisms/hourly_wage.md":
        return "code.models.hourly_wage"
    if path == "mechanisms/separation_mechanisms.md":
        return "code.models.separation_mechanisms"
    if path == "mechanisms/stock_proxy.md":
        return "code.models.stock_proxy"
    if path == "mechanisms/exposure_measure_sensitivity.md":
        return "code.models.exposure_sensitivity"
    if path.startswith("reconciliation/pdet_"):
        return "code.ingest.reconcile_pdet"
    if path.startswith("reconciliation/v1_vs_v2") or path.endswith(
        "reconciliation/reconciliacao.md"
    ):
        return "code.ingest.reconcile_v1"
    if path.startswith("reconciliation/gate_modelo_antigo"):
        return "code.models.gate_v1_model"
    if path.startswith("reconciliation/crosswalk_coverage") or path.startswith(
        "reconciliation/treatment_classification"
    ):
        return "code.panel.crosswalk"
    if path.startswith("reconciliation/painel_") or path.startswith(
        "reconciliation/cnae_month"
    ):
        return "code.panel.build_panel"
    if path.startswith("reconciliation/build_movements"):
        return "code.ingest.build_movements"
    if path.startswith("reconciliation/"):
        return "code.ingest.diagnose_vintage"
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


def _result_artifacts(results_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in results_dir.rglob("*")
        if path.is_file()
        and DEFAULT_REFERENCE.name not in path.relative_to(
            results_dir
        ).parts
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
