"""Pipeline for the final Section 4/5 curation package."""

from __future__ import annotations

from .config import OUTPUT_ROOT
from .figures import build_all_figures
from .report import validate_package, write_audit, write_manifest, write_navigation
from .sources import load_sources
from .tables import build_all_tables


def log(message: str) -> None:
    print(f"[section4_5_final] {message}", flush=True)


def run() -> None:
    log("Loading final Section 4 source outputs...")
    sources = load_sources()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    log("Writing curated tables...")
    generated_tables = build_all_tables(sources)

    log("Writing publication-style figures...")
    build_all_figures(sources)

    log("Writing README, manifest, and audit files...")
    write_navigation()
    write_manifest(generated_tables)
    write_audit()

    log("Validating final package...")
    validate_package()
    log(f"Done. Final package written to {OUTPUT_ROOT}")

