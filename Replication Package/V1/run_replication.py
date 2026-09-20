#!/usr/bin/env python3
"""Run the standalone dissertation replication package."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


PACKAGE_ROOT = Path(__file__).resolve().parent
CODE_ROOT = PACKAGE_ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))


from sections4_5.full_pipeline import (
    FULL_DAG,
    full_input_status,
    optional_cache_status,
)


SECTIONS45_DAG = tuple(stage.stage_id for stage in FULL_DAG)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reproduce the dissertation artifacts from frozen analytic inputs "
            "or rebuild them from external raw data."
        )
    )
    parser.add_argument(
        "--section",
        choices=("all", "3", "4-5"),
        default="all",
        help="Package section to run (default: all).",
    )
    parser.add_argument(
        "--mode",
        choices=("reproduce", "full"),
        default="reproduce",
        help="Use frozen inputs or rebuild derived data (default: reproduce).",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=PACKAGE_ROOT / "data" / "raw",
        help="Directory containing user-supplied raw data.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PACKAGE_ROOT / "results" / "reproduced",
        help="Destination for reproduced artifacts.",
    )
    parser.add_argument(
        "--billing-project",
        help="Google Cloud billing project used for PNAD or CAGED downloads.",
    )
    parser.add_argument(
        "--skip-figures",
        action="store_true",
        help="Generate and validate tables without materializing PNG figures.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected execution graph and required inputs without running it.",
    )
    return parser.parse_args(argv)


def print_dry_run(args: argparse.Namespace) -> None:
    print(f"mode={args.mode}")
    print(f"section={args.section}")
    if args.section in {"all", "3"}:
        print("section3: 01_data -> 02_tables -> 03_figures -> 04_validation")
        if args.mode == "full":
            section3_raw = args.raw_dir / "section3"
            print("section3_raw_inputs:")
            pnad = section3_raw / "pnad_2025q3.parquet"
            if pnad.is_file():
                pnad_status = "FOUND"
            elif args.billing_project:
                pnad_status = "BIGQUERY"
            else:
                pnad_status = "MISSING"
            print(f"  - {pnad_status}: {pnad.name}")
            ilo = (
                section3_raw
                / "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"
            )
            print(f"  - {'FOUND' if ilo.is_file() else 'MISSING'}: {ilo.name}")
    if args.section in {"all", "4-5"}:
        print("sections4_5:")
        for stage in FULL_DAG:
            print(f"  - {stage.stage_id}: {stage.description}")
        if args.mode == "full":
            print("sections4_5_raw_inputs:")
            for filename, exists in full_input_status(
                args.raw_dir / "sections4_5"
            ):
                downloadable = (
                    args.billing_project
                    and filename.startswith("caged_")
                    and filename.endswith(".parquet")
                )
                status = (
                    "FOUND"
                    if exists
                    else "BIGQUERY"
                    if downloadable
                    else "MISSING"
                )
                print(f"  - {status}: {filename}")
            print("sections4_5_optional_crosswalk_caches:")
            for filename, exists in optional_cache_status(
                args.raw_dir / "sections4_5"
            ):
                print(f"  - {'FOUND' if exists else 'REBUILD'}: {filename}")
    print(f"raw_dir={args.raw_dir.resolve()}")
    print(f"output_dir={args.output_dir.resolve()}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.dry_run:
        print_dry_run(args)
        return 0

    if args.section in {"all", "3"}:
        from section3.pipeline import run as run_section3

        run_section3(
            package_root=PACKAGE_ROOT,
            mode=args.mode,
            raw_dir=args.raw_dir / "section3",
            output_dir=args.output_dir / "section3",
            billing_project=args.billing_project,
            skip_figures=args.skip_figures,
        )

    if args.section in {"all", "4-5"}:
        from sections4_5.pipeline import run as run_sections45

        run_sections45(
            package_root=PACKAGE_ROOT,
            mode=args.mode,
            raw_dir=args.raw_dir / "sections4_5",
            output_dir=args.output_dir / "sections4_5",
            skip_figures=args.skip_figures,
            billing_project=args.billing_project,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
