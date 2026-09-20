"""Safe filesystem and hashing helpers for replication runs."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


RUN_MANIFEST = "run_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path, root: Path) -> str:
    """Return a stable relative path without leaking a local absolute prefix."""
    path = path.resolve()
    root = root.resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return f"<external>/{path.name}"


def prepare_output_directory(output_dir: Path, package_root: Path) -> None:
    """Create or safely reset an output produced by this package."""
    output_dir = output_dir.resolve()
    package_root = package_root.resolve()
    forbidden_exact = {
        Path("/").resolve(),
        Path.home().resolve(),
        package_root,
        (package_root / "results").resolve(),
    }
    immutable_roots = (
        (package_root / "code").resolve(),
        (package_root / "data").resolve(),
        (package_root / "results" / "reference").resolve(),
    )
    is_package_ancestor = package_root != output_dir and _is_within(
        package_root,
        output_dir,
    )
    is_immutable_descendant = any(
        _is_within(output_dir, root) for root in immutable_roots
    )
    if (
        output_dir in forbidden_exact
        or is_package_ancestor
        or is_immutable_descendant
    ):
        raise ValueError(f"Refusing broad or immutable output target: {output_dir}")

    if output_dir.exists() and any(output_dir.iterdir()):
        marker = output_dir / RUN_MANIFEST
        if not _is_valid_run_manifest(marker):
            raise ValueError(
                "Refusing to replace a non-empty directory without a valid "
                f"package run manifest: {output_dir}"
            )
        for child in output_dir.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)


def copy_file(source: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _is_valid_run_manifest(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return (
        payload.get("schema_version") == "dissertation_replication_v2"
        and payload.get("section") in {"3", "4-5"}
        and isinstance(payload.get("artifacts"), list)
    )
