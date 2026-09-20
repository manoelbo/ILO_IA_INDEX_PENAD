"""Single path context shared by every public replication component."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
ENVIRONMENT_KEYS = {
    "package": "REPLICATION_PACKAGE_ROOT",
    "data": "REPLICATION_DATA_DIR",
    "raw": "REPLICATION_RAW_DIR",
    "reference": "REPLICATION_REFERENCE_DIR",
    "reproduced": "REPLICATION_OUTPUT_DIR",
    "work": "REPLICATION_WORK_DIR",
}


def portable_path(path: Path, *, relative_to: Path = PACKAGE_ROOT) -> str:
    """Return a stable package-relative path and reject external inputs."""
    resolved_root = relative_to.expanduser().resolve()
    resolved_path = path.expanduser().resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError as error:
        raise ValueError(
            f"Path is outside the portable replication root: {path}"
        ) from error


@dataclass(frozen=True)
class ReplicationPaths:
    """Resolved package, input, output, reference, and workspace roots."""

    package: Path
    data: Path
    raw: Path
    reference: Path
    reproduced: Path
    work: Path

    @classmethod
    def defaults(cls) -> "ReplicationPaths":
        return cls(
            package=PACKAGE_ROOT,
            data=PACKAGE_ROOT / "data",
            raw=PACKAGE_ROOT / "data" / "vintage",
            reference=PACKAGE_ROOT / "results" / "reference",
            reproduced=PACKAGE_ROOT / "results" / "reproduced",
            work=PACKAGE_ROOT / ".replication-work",
        )

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
    ) -> "ReplicationPaths":
        values = os.environ if environment is None else environment
        defaults = cls.defaults()
        return cls(
            **{
                field: Path(values.get(variable, str(getattr(defaults, field))))
                for field, variable in ENVIRONMENT_KEYS.items()
            }
        ).resolved()

    def resolved(self) -> "ReplicationPaths":
        return ReplicationPaths(
            **{
                field: getattr(self, field).expanduser().resolve()
                for field in ENVIRONMENT_KEYS
            }
        )

    def environment(self) -> dict[str, str]:
        resolved = self.resolved()
        return {
            variable: str(getattr(resolved, field))
            for field, variable in ENVIRONMENT_KEYS.items()
        }
