"""Artifact inventory, comparison, and navigation."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageOps, ImageStat

from .files import sha256_file
from .validation import ValidationCheck


@dataclass(frozen=True)
class ArtifactRecord:
    section: str
    artifact_id: str
    artifact_type: str
    producer: str
    input_path: str
    reference_path: str
    reproduced_path: str
    status: str
    reference_sha256: str
    reproduced_sha256: str
    comparison: str


def compare_artifact_directories(
    *,
    section: str,
    reference_dir: Path,
    reproduced_dir: Path,
    producer: str,
    include_figures: bool,
    provenance: dict[str, tuple[str, str]] | None = None,
) -> tuple[list[ArtifactRecord], list[ValidationCheck]]:
    reference_files = [
        path
        for directory, suffixes in (
            ("tables", {".csv", ".md"}),
            ("figures", {".png"} if include_figures else set()),
            ("backing_data", {".csv"}),
        )
        for path in sorted((reference_dir / directory).rglob("*"))
        if path.is_file() and path.suffix.lower() in suffixes
    ]
    records: list[ArtifactRecord] = []
    checks: list[ValidationCheck] = []
    for reference in reference_files:
        relative = reference.relative_to(reference_dir)
        reproduced = reproduced_dir / relative
        artifact_id = (
            reference.stem
            if relative.parts[0] in {"tables", "figures"}
            else "__".join(relative.with_suffix("").parts)
        )
        artifact_producer, input_path = (provenance or {}).get(
            relative.as_posix(),
            (provenance or {}).get(
                artifact_id,
                (provenance or {}).get(
                    reference.stem,
                    (producer, ""),
                ),
            ),
        )
        exists = reproduced.exists()
        if not exists:
            matches = False
            comparison = "missing"
            reproduced_hash = ""
        elif reference.suffix.lower() == ".png":
            matches, comparison = compare_png(reference, reproduced)
            reproduced_hash = sha256_file(reproduced)
        elif relative.as_posix() == (
            "backing_data/core_model_reestimation.csv"
        ):
            matches, comparison = compare_core_reestimation(
                reference,
                reproduced,
            )
            reproduced_hash = sha256_file(reproduced)
        elif relative.as_posix() == (
            "backing_data/data_build_diagnostics.csv"
        ):
            matches, comparison = compare_build_diagnostics(
                reference,
                reproduced,
            )
            reproduced_hash = sha256_file(reproduced)
        else:
            matches = reference.read_bytes() == reproduced.read_bytes()
            comparison = "byte-identical" if matches else "text differs"
            reproduced_hash = sha256_file(reproduced)
        reference_hash = sha256_file(reference)
        records.append(
            ArtifactRecord(
                section=section,
                artifact_id=artifact_id,
                artifact_type=relative.parts[0].rstrip("s"),
                producer=artifact_producer,
                input_path=input_path,
                reference_path=relative.as_posix(),
                reproduced_path=relative.as_posix() if exists else "",
                status="PASS" if matches else "FAIL",
                reference_sha256=reference_hash,
                reproduced_sha256=reproduced_hash,
                comparison=comparison,
            )
        )
        checks.append(
            ValidationCheck(
                check_id=f"artifact_{relative.as_posix()}",
                status="PASS" if matches else "FAIL",
                observed=comparison,
                expected="matches reference",
                detail="Reference-to-reproduced artifact comparison.",
            )
        )
    return records, checks


def compare_png(reference: Path, reproduced: Path) -> tuple[bool, str]:
    with Image.open(reference) as reference_image, Image.open(
        reproduced
    ) as reproduced_image:
        reference_size = tuple(reference_image.size)
        reproduced_size = tuple(reproduced_image.size)
        small_reference = ImageOps.fit(
            reference_image.convert("L"),
            (64, 64),
            method=Image.Resampling.LANCZOS,
        )
        small_reproduced = ImageOps.fit(
            reproduced_image.convert("L"),
            (64, 64),
            method=Image.Resampling.LANCZOS,
        )
        rms = float(
            ImageStat.Stat(
                ImageChops.difference(small_reference, small_reproduced)
            ).rms[0]
        )
    matches = reference_size == reproduced_size and rms <= 5.0
    return (
        matches,
        f"dimensions={reproduced_size}; reference={reference_size}; RMS={rms:.6f}",
    )


def compare_core_reestimation(
    reference: Path,
    reproduced: Path,
) -> tuple[bool, str]:
    numeric_fields = {
        "coef",
        "se",
        "p_value",
        "n_obs",
        "n_cbo",
        "source_coef",
        "source_se",
        "source_p_value",
        "max_abs_difference",
    }
    with reference.open(encoding="utf-8", newline="") as handle:
        reference_rows = list(csv.DictReader(handle))
    with reproduced.open(encoding="utf-8", newline="") as handle:
        reproduced_rows = list(csv.DictReader(handle))
    if len(reference_rows) != len(reproduced_rows):
        return False, (
            f"row count differs: {len(reproduced_rows)} vs "
            f"{len(reference_rows)}"
        )
    max_difference = 0.0
    for expected, observed in zip(reference_rows, reproduced_rows):
        if set(expected) != set(observed):
            return False, "column structure differs"
        for field in expected:
            if field in numeric_fields:
                difference = abs(
                    float(expected[field]) - float(observed[field])
                )
                max_difference = max(max_difference, difference)
            elif expected[field] != observed[field]:
                return False, f"text differs in {field}"
    matches = max_difference <= 1e-12
    return matches, f"numeric max_abs_diff={max_difference:.3e}"


def compare_build_diagnostics(
    reference: Path,
    reproduced: Path,
    *,
    tolerance: float = 1e-6,
) -> tuple[bool, str]:
    """Compare build receipts by metric under the declared numeric tolerance."""

    def read_metrics(path: Path) -> dict[str, float]:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows or tuple(rows[0]) != ("metric", "value"):
            raise ValueError(f"Invalid build diagnostics schema: {path}")
        metrics = {row["metric"]: float(row["value"]) for row in rows}
        if len(metrics) != len(rows):
            raise ValueError(f"Duplicate build diagnostics metric: {path}")
        return metrics

    try:
        expected = read_metrics(reference)
        observed = read_metrics(reproduced)
    except (OSError, ValueError) as error:
        return False, str(error)
    if set(expected) != set(observed):
        return False, "metric set differs"
    differences = {
        metric: abs(observed[metric] - expected[metric])
        for metric in expected
    }
    maximum = max(differences.values(), default=0.0)
    return (
        maximum <= tolerance,
        f"metric max_abs_diff={maximum:.3e}; tolerance={tolerance:.1e}",
    )


def write_artifact_navigation(
    records: list[ArtifactRecord],
    output_dir: Path,
) -> tuple[Path, Path]:
    csv_path = output_dir / "artifact_manifest.csv"
    index_path = output_dir / "INDEX.md"
    fieldnames = [
        "section",
        "artifact_id",
        "artifact_type",
        "producer",
        "input_path",
        "reference_path",
        "reproduced_path",
        "status",
        "reference_sha256",
        "reproduced_sha256",
        "comparison",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)

    lines = [
        "# Reproduced artifact index",
        "",
        "[Artifact manifest](artifact_manifest.csv) · "
        "[Validation](validation/validation_checks.md) · "
        "[Run manifest](run_manifest.json)",
        "",
        "| Section | Artifact | Type | Status | File |",
        "|---|---|---|---:|---|",
    ]
    for record in records:
        link = (
            f"[{record.reproduced_path}]({record.reproduced_path})"
            if record.reproduced_path
            else "missing"
        )
        lines.append(
            f"| {record.section} | `{record.artifact_id}` | "
            f"{record.artifact_type} | {record.status} | {link} |"
        )
    lines.append("")
    index_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, index_path
