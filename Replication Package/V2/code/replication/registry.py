"""Typed analysis and manuscript-publication registries for V2."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_REGISTRY = PACKAGE_ROOT / "config" / "analysis_registry.csv"
MANUSCRIPT_REGISTRY = PACKAGE_ROOT / "config" / "manuscript_artifacts.csv"
COMPONENTS = ("section3", "caged", "rais", "pnadc", "spatial")


@dataclass(frozen=True)
class AnalysisRecord:
    node_id: str
    component: str
    modes: frozenset[str]
    inferential: bool


@dataclass(frozen=True)
class ManuscriptArtifact:
    artifact_id: str
    caption: str
    component: str
    producer: str
    input_contract: str
    reference_path: str
    command: str


def analysis_records() -> tuple[AnalysisRecord, ...]:
    with ANALYSIS_REGISTRY.open(encoding="utf-8", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    records = tuple(
        AnalysisRecord(
            node_id=row["node_id"],
            component=row["component"],
            modes=frozenset(row["modes"].split("|")),
            inferential=row["inferential"].lower() == "true",
        )
        for row in rows
    )
    node_ids = [record.node_id for record in records]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("Analysis registry contains duplicate node IDs")
    return records


def manuscript_artifacts() -> tuple[ManuscriptArtifact, ...]:
    with MANUSCRIPT_REGISTRY.open(encoding="utf-8", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    records = tuple(ManuscriptArtifact(**row) for row in rows)
    artifact_ids = [record.artifact_id for record in records]
    if len(artifact_ids) != len(set(artifact_ids)):
        raise ValueError("Manuscript registry contains duplicate artifact IDs")
    return records


def _selected_components(target: str) -> frozenset[str]:
    if target == "all":
        return frozenset(COMPONENTS)
    if target == "all_except_section3":
        return frozenset(COMPONENTS[1:])
    if target in COMPONENTS:
        return frozenset((target,))
    raise ValueError(f"Unsupported target: {target}")


def expected_node_ids(*, target: str, mode: str) -> set[str]:
    if mode not in {"reproduce", "full"}:
        raise ValueError(f"Unsupported mode: {mode}")
    selected = _selected_components(target)
    return {
        record.node_id
        for record in analysis_records()
        if mode in record.modes
        and (record.component == "common" or record.component in selected)
    }


def validate_dag_nodes(
    node_ids: set[str],
    *,
    target: str,
    mode: str,
) -> None:
    expected = expected_node_ids(target=target, mode=mode)
    if node_ids == expected:
        return
    missing = sorted(expected - node_ids)
    extra = sorted(node_ids - expected)
    raise RuntimeError(
        "DAG does not match config/analysis_registry.csv; "
        f"missing={missing}, extra={extra}"
    )


def expected_publication_outputs(
    *,
    component: str,
    include_markdown_pairs: bool = False,
) -> set[str]:
    outputs: set[str] = set()
    prefix = f"{component}/"
    for record in manuscript_artifacts():
        if record.component != component:
            continue
        if not record.reference_path.startswith(prefix):
            raise ValueError(
                f"Artifact {record.artifact_id} is outside {component}: "
                f"{record.reference_path}"
            )
        relative = record.reference_path.removeprefix(prefix)
        outputs.add(relative)
        if include_markdown_pairs and relative.endswith(".csv"):
            outputs.add(relative.removesuffix(".csv") + ".md")
    return outputs


def validate_publications(
    output_root: Path,
    *,
    component: str,
    skip_figures: bool,
) -> None:
    expected = expected_publication_outputs(
        component=component,
        include_markdown_pairs=True,
    )
    if skip_figures:
        expected = {path for path in expected if not path.endswith(".png")}
    missing = sorted(
        path for path in expected if not (output_root / path).is_file()
    )
    if missing:
        raise RuntimeError(
            f"Missing registered {component} publications: {missing}"
        )
    actual = {
        path.relative_to(output_root).as_posix()
        for directory in ("tables", "figures")
        for path in (output_root / directory).rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".csv", ".md", ".png"}
        and not (skip_figures and path.suffix.lower() == ".png")
    }
    extra = sorted(actual - expected)
    if extra:
        raise RuntimeError(
            f"Unregistered public {component} publications: {extra}"
        )
