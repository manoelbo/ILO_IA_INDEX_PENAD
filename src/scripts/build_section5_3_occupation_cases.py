#!/usr/bin/env python3
"""Build the descriptive occupation-case package for dissertation Section 5.3."""

from __future__ import annotations

import argparse

from section5_3_occupation_cases.pipeline import run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reuse-cells",
        action="store_true",
        help="Reuse the verified CBO6 monthly-cell cache when source signatures match.",
    )
    parser.add_argument(
        "--skip-source-hashes",
        action="store_true",
        help="Skip expensive SHA-256 hashes for raw source files during development.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(
        reuse_cells=args.reuse_cells,
        include_source_hashes=not args.skip_source_hashes,
    )


if __name__ == "__main__":
    main()
