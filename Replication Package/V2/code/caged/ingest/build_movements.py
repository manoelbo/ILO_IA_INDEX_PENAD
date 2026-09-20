#!/usr/bin/env python3
"""Build the signed MOV + FOR - EXC movement dataset by fact month."""

from __future__ import annotations

import argparse
import csv
import gc
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Sequence
from urllib.parse import urlparse

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from download import read_inventory
from parse import (
    BASE_COLUMNS,
    DECIMAL_COLUMNS,
    EXCLUSION_COLUMNS,
    INTEGER_COLUMNS,
    parse_archive,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INVENTORY = PACKAGE_ROOT / "data" / "vintage" / "ftp_inventory.csv"
DEFAULT_VINTAGE_DIR = PACKAGE_ROOT / "data" / "vintage"
DEFAULT_OUTPUT_DIR = (
    PACKAGE_ROOT / "data" / "interim" / "movimentacoes"
)
DEFAULT_RECONCILIATION = (
    PACKAGE_ROOT
    / "results"
    / "reconciliation"
    / "origem_por_competencia.csv"
)
OUTPUT_COLUMNS = (
    *(column for column in EXCLUSION_COLUMNS if column != "competenciamov"),
    "origem",
    "competencia_arquivo",
    "peso",
)
STRING_COLUMNS = (
    set(OUTPUT_COLUMNS)
    - set(DECIMAL_COLUMNS)
    - set(INTEGER_COLUMNS)
    - {"peso"}
)
ARROW_SCHEMA = pa.schema(
    [
        pa.field(
            column,
            pa.float64()
            if column in DECIMAL_COLUMNS
            else pa.int64()
            if column in INTEGER_COLUMNS
            else pa.int8()
            if column == "peso"
            else pa.string(),
        )
        for column in OUTPUT_COLUMNS
    ]
)
Parser = Callable[[Path], pd.DataFrame]


def prepare_archive_frame(
    frame: pd.DataFrame,
    archive_type: str,
    competencia_arquivo: str,
) -> pd.DataFrame:
    """Apply source metadata and enforce fact-time relationships."""
    if archive_type not in {"MOV", "FOR", "EXC"}:
        raise ValueError(f"Unexpected archive type: {archive_type}")
    if not frame["competenciamov"].str.fullmatch(r"\d{6}").all():
        raise ValueError("competenciamov must contain six-digit YYYYMM values")

    if archive_type == "MOV":
        invalid = frame["competenciamov"].ne(competencia_arquivo)
        if invalid.any():
            raise ValueError(
                f"MOV facts must equal file month {competencia_arquivo}; "
                f"found {int(invalid.sum())} violations"
            )
    elif archive_type == "FOR":
        invalid = frame["competenciamov"].ge(competencia_arquivo)
        if invalid.any():
            raise ValueError(
                f"FOR facts must be strictly earlier than file month "
                f"{competencia_arquivo}; found {int(invalid.sum())} violations"
            )
    else:
        invalid = frame["competenciamov"].gt(competencia_arquivo)
        if invalid.any():
            raise ValueError(
                f"EXC facts cannot be later than file month "
                f"{competencia_arquivo}; found {int(invalid.sum())} violations"
            )

    prepared = frame.copy()
    for column in set(EXCLUSION_COLUMNS) - set(prepared.columns):
        prepared[column] = pd.NA
    prepared["origem"] = archive_type
    prepared["competencia_arquivo"] = competencia_arquivo
    prepared["peso"] = -1 if archive_type == "EXC" else 1
    for column in STRING_COLUMNS:
        prepared[column] = prepared[column].astype("string")
    prepared["peso"] = prepared["peso"].astype("int8")
    return prepared[["competenciamov", *OUTPUT_COLUMNS]]


def _table_from_group(group: pd.DataFrame) -> pa.Table:
    return pa.Table.from_pandas(
        group[list(OUTPUT_COLUMNS)],
        schema=ARROW_SCHEMA,
        preserve_index=False,
        safe=True,
    )


def _write_reconciliation(
    counters: dict[str, Counter[str]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        "competenciamov",
        "linhas_mov",
        "linhas_for",
        "linhas_exc",
        "linhas_exc_mesmo_mes",
        "liquido",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        for competencia in sorted(counters):
            counts = counters[competencia]
            writer.writerow(
                {
                    "competenciamov": competencia,
                    "linhas_mov": counts["MOV"],
                    "linhas_for": counts["FOR"],
                    "linhas_exc": counts["EXC"],
                    "linhas_exc_mesmo_mes": counts["EXC_SAME_MONTH"],
                    "liquido": (
                        counts["MOV"] + counts["FOR"] - counts["EXC"]
                    ),
                }
            )


def _directory_size(path: Path) -> int:
    return sum(
        file_path.stat().st_size
        for file_path in path.rglob("*")
        if file_path.is_file()
    )


def build_movements(
    records: Sequence[dict[str, object]],
    vintage_dir: Path,
    output_dir: Path,
    reconciliation_path: Path,
    *,
    parser: Parser = parse_archive,
) -> dict[str, int]:
    """Build one atomic partitioned dataset from the frozen archives."""
    if output_dir.exists():
        raise FileExistsError(
            f"Output already exists; refusing to overwrite: {output_dir}"
        )
    building_dir = output_dir.with_name(f"{output_dir.name}.building")
    if building_dir.exists():
        raise FileExistsError(
            f"Previous incomplete build exists: {building_dir}"
        )
    building_dir.mkdir(parents=True)

    writers: dict[str, pq.ParquetWriter] = {}
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    total_exclusion_rows = 0
    negative_weight_rows = 0

    try:
        for index, record in enumerate(records, start=1):
            archive_type = str(record["tipo"])
            competencia_arquivo = str(record["competencia"])
            filename = Path(urlparse(str(record["url"])).path).name
            archive_path = vintage_dir / filename
            if not archive_path.is_file():
                raise FileNotFoundError(archive_path)
            print(
                f"[{index}/{len(records)}] parse {filename}",
                flush=True,
            )
            frame = parser(archive_path)
            prepared = prepare_archive_frame(
                frame,
                archive_type,
                competencia_arquivo,
            )
            if archive_type == "EXC":
                total_exclusion_rows += len(prepared)
                negative_weight_rows += int(prepared["peso"].eq(-1).sum())

            if archive_type == "MOV":
                archive_groups = (
                    (competencia_arquivo, prepared),
                )
            else:
                archive_groups = prepared.groupby(
                    "competenciamov",
                    sort=False,
                    observed=True,
                )
            for competencia, group in archive_groups:
                competencia_text = str(competencia)
                partition_dir = (
                    building_dir
                    / f"competenciamov={competencia_text}"
                )
                partition_dir.mkdir(parents=True, exist_ok=True)
                writer = writers.get(competencia_text)
                if writer is None:
                    writer = pq.ParquetWriter(
                        partition_dir / "part.parquet",
                        ARROW_SCHEMA,
                        compression="zstd",
                        compression_level=3,
                        use_dictionary=True,
                    )
                    writers[competencia_text] = writer
                writer.write_table(_table_from_group(group))
                counters[competencia_text][archive_type] += len(group)
                if (
                    archive_type == "EXC"
                    and competencia_text == competencia_arquivo
                ):
                    counters[competencia_text]["EXC_SAME_MONTH"] += len(group)

            del frame, prepared
            gc.collect()
    finally:
        for writer in writers.values():
            writer.close()

    if negative_weight_rows != total_exclusion_rows:
        raise RuntimeError(
            "Negative weights do not match processed EXC rows: "
            f"{negative_weight_rows} != {total_exclusion_rows}"
        )

    if len(records) == 195:
        required = pd.period_range("2021-01", "2026-05", freq="M").strftime(
            "%Y%m"
        )
        missing = sorted(set(required) - set(counters))
        if missing:
            raise RuntimeError(f"Missing fact-month partitions: {missing}")

    _write_reconciliation(counters, reconciliation_path)
    os.replace(building_dir, output_dir)
    metrics = {
        "archives_processed": len(records),
        "partitions_written": len(counters),
        "total_exclusion_rows": total_exclusion_rows,
        "negative_weight_rows": negative_weight_rows,
        "output_bytes": _directory_size(output_dir),
    }
    metrics_path = reconciliation_path.with_name(
        "build_movements_metrics.json"
    )
    metrics_path.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build signed MOV + FOR - EXC movement partitions."
    )
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--vintage-dir", type=Path, default=DEFAULT_VINTAGE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--reconciliation",
        type=Path,
        default=DEFAULT_RECONCILIATION,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics = build_movements(
        read_inventory(args.inventory),
        args.vintage_dir,
        args.output_dir,
        args.reconciliation,
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
