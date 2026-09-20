from __future__ import annotations

import importlib.util
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
ROOT_DOCUMENTS = {
    Path("README.md"),
    Path("DATA_AVAILABILITY.md"),
    Path("RESEARCH_DESIGN.md"),
}
REQUIRED_IGNORE_RULES = {
    ".DS_Store",
    ".pytest_cache/",
    ".venv/",
    "__pycache__/",
    "*.py[cod]",
}


def load_reference_module():
    path = PACKAGE_ROOT / "code" / "replication" / "reference_validation.py"
    spec = importlib.util.spec_from_file_location("reference_validation", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_tree_contains_no_development_material() -> None:
    assert not (PACKAGE_ROOT / "experiment").exists()
    for name in (
        "CHECKPOINTS.md",
        "COMPARACAO_V1_V2.md",
        "DECISIONS.md",
        "R/VERSIONS.md",
        "data/vintage/README.md",
    ):
        assert not (PACKAGE_ROOT / name).exists(), name


def test_release_distribution_excludes_local_environments_and_caches() -> None:
    rules = {
        line.strip()
        for line in (PACKAGE_ROOT / ".gitignore").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert REQUIRED_IGNORE_RULES <= rules


def test_release_markdown_matches_the_public_allowlist() -> None:
    module = load_reference_module()
    markdown = {
        path.relative_to(PACKAGE_ROOT)
        for path in PACKAGE_ROOT.rglob("*.md")
        if path.is_file()
    }
    assert ROOT_DOCUMENTS <= markdown
    for relative in markdown - ROOT_DOCUMENTS:
        prefix = Path("results/reference/artifacts")
        assert relative.is_relative_to(prefix), relative
        component_relative = relative.relative_to(prefix)
        assert module._public_markdown(component_relative), relative


def test_repository_data_mount_point_ignores_bundle_contents() -> None:
    mount_ignore = PACKAGE_ROOT / "data" / ".gitignore"
    rules = {
        line.strip()
        for line in mount_ignore.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert {"*", "!.gitignore"} <= rules


def test_citation_metadata_matches_the_publication_registry_size() -> None:
    citation = (PACKAGE_ROOT / "CITATION.cff").read_text(encoding="utf-8")

    assert "53 computational tables and figures" in citation
    assert "52 computational tables and figures" not in citation
