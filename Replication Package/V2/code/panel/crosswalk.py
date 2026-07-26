#!/usr/bin/env python3
"""Freeze and reproduce the official MTE-to-ILO occupation crosswalk."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_CROSSWALK_DIR = PACKAGE_ROOT / "data" / "vintage" / "crosswalk"
DEFAULT_MANIFEST = PACKAGE_ROOT / "data" / "vintage" / "manifest.json"
DEFAULT_CLASSIFICATION = (
    PACKAGE_ROOT / "data" / "derived" / "cbo_treatment_classification.csv"
)
DEFAULT_COVERAGE = (
    PACKAGE_ROOT / "results" / "reconciliation" / "crosswalk_coverage.json"
)
DEFAULT_REFERENCE = (
    REPOSITORY_ROOT
    / "outputs"
    / "treatment_scenario_grid"
    / "scenario_cbo_classification.csv"
)
DEFAULT_VALIDATION = (
    PACKAGE_ROOT
    / "results"
    / "reconciliation"
    / "treatment_classification_validation.json"
)

MTE_CACHE_FILENAME = "mte_cbo2002_cbo94_ciuo88_by_family.csv"
CBO_ISCO_FILENAME = "cbo-isco-conc.csv"
ISCO_CORRESPONDENCE_FILENAME = "Correspondência ISCO 08 a 88.xlsx"
ISCO_DEFINITIONS_FILENAME = "ISCO 08 Estruturas e Definições.xlsx"
ILO_FILENAME = "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"
REQUIRED_FILENAMES = (
    MTE_CACHE_FILENAME,
    CBO_ISCO_FILENAME,
    ISCO_CORRESPONDENCE_FILENAME,
    ISCO_DEFINITIONS_FILENAME,
    ILO_FILENAME,
)
EXPECTED_ILO_SHA256 = (
    "c1940b87e7293b1eb95b530b6d3da7cd806b61d217c4bff1e69372b2cff5c90a"
)
EXPECTED_COVERAGE = {
    "matched_official_mte": 436,
    "no_score": 193,
}
EXPECTED_CLASSIFICATION = {
    "Exposed: Gradient 4": 0,
    "Exposed: Gradient 3": 31,
    "Exposed: Gradient 2": 31,
    "Exposed: Gradient 1": 13,
    "Minimal Exposure": 95,
    "Not Exposed": 266,
    "No score": 193,
}

ILO_HIGH_EXPOSURE_BOUNDARY = 0.50
ILO_GRADIENT_4_MEAN_CUTOFF = 0.60
ILO_GRADIENT_3_MEAN_CUTOFF = 0.50
ILO_GRADIENT_2_MEAN_CUTOFF = 0.40
ILO_MINIMAL_EXPOSURE_BOUNDARY = 0.40


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_manifest(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Vintage manifest must be a JSON object")
    return payload


def _write_manifest(
    manifest: dict[str, dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def default_source_paths() -> dict[str, Path]:
    return {
        MTE_CACHE_FILENAME: (
            REPOSITORY_ROOT
            / "outputs"
            / "crosswalk_audit"
            / "source_dictionaries"
            / MTE_CACHE_FILENAME
        ),
        CBO_ISCO_FILENAME: (
            REPOSITORY_ROOT / "data" / "input" / CBO_ISCO_FILENAME
        ),
        ISCO_CORRESPONDENCE_FILENAME: (
            REPOSITORY_ROOT
            / "data"
            / "input"
            / ISCO_CORRESPONDENCE_FILENAME
        ),
        ISCO_DEFINITIONS_FILENAME: (
            REPOSITORY_ROOT
            / "data"
            / "input"
            / ISCO_DEFINITIONS_FILENAME
        ),
        ILO_FILENAME: REPOSITORY_ROOT / "data" / "input" / ILO_FILENAME,
    }


def source_reference(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def freeze_crosswalk_sources(
    sources: Mapping[str, Path],
    target_dir: Path,
    manifest_path: Path,
    *,
    expected_ilo_sha256: str = EXPECTED_ILO_SHA256,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict[str, Any]:
    """Copy the fixed crosswalk inputs and record immutable checksums."""
    missing_names = sorted(set(REQUIRED_FILENAMES) - set(sources))
    if missing_names:
        raise ValueError(f"Missing crosswalk source mappings: {missing_names}")
    missing_paths = [
        str(sources[filename])
        for filename in REQUIRED_FILENAMES
        if not Path(sources[filename]).is_file()
    ]
    if missing_paths:
        raise FileNotFoundError(
            "Missing crosswalk source files:\n" + "\n".join(missing_paths)
        )

    observed_ilo_sha256 = sha256_file(Path(sources[ILO_FILENAME]))
    if observed_ilo_sha256 != expected_ilo_sha256:
        raise RuntimeError(
            "ILO workbook SHA-256 mismatch: "
            f"expected {expected_ilo_sha256}, got {observed_ilo_sha256}"
        )

    frozen_at = utc_iso(now())
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest = _read_manifest(manifest_path)
    for filename in REQUIRED_FILENAMES:
        source = Path(sources[filename])
        target = target_dir / filename
        temporary = target.with_suffix(f"{target.suffix}.tmp")
        shutil.copy2(source, temporary)
        os.replace(temporary, target)
        observed_hash = sha256_file(target)
        source_hash = sha256_file(source)
        if observed_hash != source_hash:
            raise RuntimeError(f"Frozen copy hash mismatch for {filename}")
        manifest[f"crosswalk/{filename}"] = {
            "bytes": target.stat().st_size,
            "frozen_at": frozen_at,
            "sha256": observed_hash,
            "source_path": source_reference(source),
        }
    _write_manifest(manifest, manifest_path)
    return {
        "files_frozen": len(REQUIRED_FILENAMES),
        "ilo_sha256": observed_ilo_sha256,
        "frozen_at": frozen_at,
    }


def normalize_code(value: Any, width: int = 4) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(character for character in text if character.isdigit())
    return digits.zfill(width) if digits else ""


def unique_preserve(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def load_ilo_scores(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path)
    required = {
        "ISCO_08",
        "Title",
        "mean_score_2025",
        "SD_2025",
        "potential25",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"ILO workbook is missing columns: {missing}")
    raw["isco_08"] = raw["ISCO_08"].map(normalize_code)
    raw["exposure_score"] = pd.to_numeric(
        raw["mean_score_2025"], errors="coerce"
    )
    raw["exposure_sd"] = pd.to_numeric(raw["SD_2025"], errors="coerce")
    scores = (
        raw.groupby("isco_08", as_index=False)
        .agg(
            occupation_title=("Title", "first"),
            exposure_score=("exposure_score", "mean"),
            exposure_sd=("exposure_sd", "mean"),
            exposure_gradient=("potential25", "first"),
        )
        .sort_values("isco_08")
        .reset_index(drop=True)
    )
    if len(scores) != 427:
        raise RuntimeError(
            f"Expected 427 unique ILO occupations, found {len(scores)}"
        )
    return scores


def load_isco88_to_isco08(path: Path) -> dict[str, list[str]]:
    frame = pd.read_excel(path, sheet_name="ISCO-08 to 88")
    required = {"ISCO-08 code", "ISCO-88 code"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(
            f"ISCO correspondence is missing columns: {missing}"
        )
    frame["isco08"] = frame["ISCO-08 code"].map(normalize_code)
    frame["isco88"] = frame["ISCO-88 code"].map(normalize_code)
    frame = frame[(frame["isco08"] != "") & (frame["isco88"] != "")]
    return (
        frame.groupby("isco88", sort=True)["isco08"]
        .agg(lambda values: unique_preserve(list(values)))
        .to_dict()
    )


def pooled_equal_weight_sd(
    scores: list[float],
    standard_deviations: list[float],
) -> float:
    if not scores or len(scores) != len(standard_deviations):
        return math.nan
    mean_score = float(np.mean(scores))
    variances = [
        standard_deviation**2 + (score - mean_score) ** 2
        for score, standard_deviation in zip(
            scores, standard_deviations, strict=True
        )
    ]
    return float(np.sqrt(np.mean(variances)))


def classify_ilo_mean_sd(mean_score: float, sd_score: float) -> str:
    if pd.isna(mean_score) or pd.isna(sd_score):
        return "No score"
    if (
        mean_score >= ILO_GRADIENT_4_MEAN_CUTOFF
        and mean_score - sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY
    ):
        return "Exposed: Gradient 4"
    if (
        ILO_GRADIENT_3_MEAN_CUTOFF
        <= mean_score
        < ILO_GRADIENT_4_MEAN_CUTOFF
        and mean_score + sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY
    ):
        return "Exposed: Gradient 3"
    if (
        ILO_GRADIENT_2_MEAN_CUTOFF
        <= mean_score
        < ILO_GRADIENT_3_MEAN_CUTOFF
        and mean_score + sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY
    ):
        return "Exposed: Gradient 2"
    if (
        mean_score < ILO_GRADIENT_2_MEAN_CUTOFF
        and mean_score + sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY
    ):
        return "Exposed: Gradient 1"
    if (
        mean_score < ILO_HIGH_EXPOSURE_BOUNDARY
        and mean_score + sd_score > ILO_MINIMAL_EXPOSURE_BOUNDARY
    ):
        return "Minimal Exposure"
    return "Not Exposed"


def build_classification_from_frozen(crosswalk_dir: Path) -> pd.DataFrame:
    cache = pd.read_csv(
        crosswalk_dir / MTE_CACHE_FILENAME,
        dtype=str,
        keep_default_na=False,
    )
    if len(cache) != 1550 or cache["source_cbo_4d"].nunique() != 629:
        raise RuntimeError(
            "Frozen MTE cache must contain 1,550 rows and 629 CBO families"
        )
    scores = load_ilo_scores(crosswalk_dir / ILO_FILENAME)
    correspondence = load_isco88_to_isco08(
        crosswalk_dir / ISCO_CORRESPONDENCE_FILENAME
    )
    score_map = dict(zip(scores["isco_08"], scores["exposure_score"]))
    sd_map = dict(zip(scores["isco_08"], scores["exposure_sd"]))

    records: list[dict[str, Any]] = []
    for cbo_4d, group in cache.groupby("source_cbo_4d", sort=True):
        matched = group[
            group["status"].eq("matched") & group["ciuo88_code"].ne("")
        ]
        ciuo88_codes = unique_preserve(
            [normalize_code(value) for value in matched["ciuo88_code"]]
        )
        isco08_codes = unique_preserve(
            [
                isco08
                for ciuo88 in ciuo88_codes
                for isco08 in correspondence.get(ciuo88, [])
            ]
        )
        scored_codes = [
            code
            for code in isco08_codes
            if code in score_map
            and not pd.isna(score_map[code])
            and code in sd_map
            and not pd.isna(sd_map[code])
        ]
        target_scores = [float(score_map[code]) for code in scored_codes]
        target_sds = [float(sd_map[code]) for code in scored_codes]
        mean_score = (
            float(np.mean(target_scores)) if target_scores else math.nan
        )
        pooled_sd = pooled_equal_weight_sd(target_scores, target_sds)
        status = "matched_official_mte" if target_scores else "no_score"
        records.append(
            {
                "cbo_4d": normalize_code(cbo_4d),
                "mte_match_status": status,
                "ciuo88_codes": "; ".join(ciuo88_codes),
                "isco08_codes": "; ".join(isco08_codes),
                "scored_isco08_codes": "; ".join(scored_codes),
                "n_isco08_targets": len(isco08_codes),
                "n_scored_isco08_targets": len(scored_codes),
                "isco08_mean_score": mean_score,
                "isco08_pooled_sd": pooled_sd,
                "cbo_ilo_gradient": classify_ilo_mean_sd(
                    mean_score, pooled_sd
                ),
            }
        )

    classification = pd.DataFrame(records).sort_values("cbo_4d")
    coverage = classification["mte_match_status"].value_counts().to_dict()
    if coverage != EXPECTED_COVERAGE:
        raise RuntimeError(
            f"Crosswalk coverage mismatch: expected {EXPECTED_COVERAGE}, "
            f"got {coverage}"
        )
    return classification.reset_index(drop=True)


def classification_counts(frame: pd.DataFrame) -> dict[str, int]:
    observed = frame["cbo_ilo_gradient"].value_counts().to_dict()
    return {
        label: int(observed.get(label, 0))
        for label in EXPECTED_CLASSIFICATION
    }


def compare_with_reference(
    classification: pd.DataFrame,
    reference_path: Path,
) -> dict[str, int]:
    if not reference_path.is_file():
        raise FileNotFoundError(
            f"Treatment-classification reference not found: {reference_path}"
        )
    reference = pd.read_csv(
        reference_path,
        usecols=["cbo_4d", "cbo_ilo_gradient"],
        dtype={"cbo_4d": str, "cbo_ilo_gradient": str},
    )
    current = classification[
        ["cbo_4d", "cbo_ilo_gradient"]
    ].copy()
    current["cbo_4d"] = current["cbo_4d"].map(normalize_code)
    reference["cbo_4d"] = reference["cbo_4d"].map(normalize_code)
    comparison = current.merge(
        reference,
        on="cbo_4d",
        how="outer",
        suffixes=("_v2", "_reference"),
        indicator=True,
    )
    missing_from_v2 = int(comparison["_merge"].eq("right_only").sum())
    missing_from_reference = int(
        comparison["_merge"].eq("left_only").sum()
    )
    different = int(
        (
            comparison["_merge"].eq("both")
            & comparison["cbo_ilo_gradient_v2"].ne(
                comparison["cbo_ilo_gradient_reference"]
            )
        ).sum()
    )
    payload = {
        "v2_cbo_families": int(len(current)),
        "reference_cbo_families": int(len(reference)),
        "missing_from_v2": missing_from_v2,
        "missing_from_reference": missing_from_reference,
        "different_assignments": different,
    }
    if missing_from_v2 or missing_from_reference or different:
        raise RuntimeError(
            "Treatment classification differs from the V1 reference: "
            f"{different} assignments differ, "
            f"{missing_from_v2} CBOs missing from V2, "
            f"{missing_from_reference} CBOs missing from the reference"
        )
    return payload


def write_coverage_report(
    classification: pd.DataFrame,
    path: Path,
) -> dict[str, Any]:
    coverage = {
        key: int(value)
        for key, value in classification[
            "mte_match_status"
        ].value_counts().to_dict().items()
    }
    gradients = classification_counts(classification)
    payload = {
        "cbo_families": int(len(classification)),
        "coverage": coverage,
        "classification": gradients,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze and reproduce the V2 occupation crosswalk."
    )
    parser.add_argument(
        "command",
        choices=("freeze", "classify", "all"),
    )
    parser.add_argument(
        "--crosswalk-dir",
        type=Path,
        default=DEFAULT_CROSSWALK_DIR,
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
    )
    parser.add_argument(
        "--classification",
        type=Path,
        default=DEFAULT_CLASSIFICATION,
    )
    parser.add_argument(
        "--coverage",
        type=Path,
        default=DEFAULT_COVERAGE,
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=DEFAULT_REFERENCE,
    )
    parser.add_argument(
        "--validation",
        type=Path,
        default=DEFAULT_VALIDATION,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command in {"freeze", "all"}:
        summary = freeze_crosswalk_sources(
            default_source_paths(),
            args.crosswalk_dir,
            args.manifest,
        )
        print(json.dumps(summary, sort_keys=True))

    classification = build_classification_from_frozen(args.crosswalk_dir)
    coverage = write_coverage_report(classification, args.coverage)
    if args.command in {"classify", "all"}:
        observed = classification_counts(classification)
        if observed != EXPECTED_CLASSIFICATION:
            raise RuntimeError(
                "Treatment classification mismatch: "
                f"expected {EXPECTED_CLASSIFICATION}, got {observed}"
            )
        validation = compare_with_reference(
            classification, args.reference
        )
        args.classification.parent.mkdir(parents=True, exist_ok=True)
        classification.to_csv(args.classification, index=False)
        args.validation.parent.mkdir(parents=True, exist_ok=True)
        args.validation.write_text(
            json.dumps(validation, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(validation, sort_keys=True))
    print(json.dumps(coverage, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
