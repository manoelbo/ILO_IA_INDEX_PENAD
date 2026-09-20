"""Streaming CAGED input and CBO-level cell construction for Section 5.3."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from .config import END_PERIOD, START_PERIOD
from .transforms import assign_age_group, assign_demographic_group, normalize_codes


RAW_COLUMNS = [
    "ano",
    "mes",
    "cbo_2002",
    "saldo_movimentacao",
    "salario_mensal",
    "idade",
    "sexo",
    "raca_cor",
    "grau_instrucao",
]
RAW_BATCH_SIZE = 1_000_000


def _summarize_group(
    records: pd.DataFrame,
    *,
    dimension: str,
    group_id: pd.Series,
) -> pd.DataFrame:
    selected = records.assign(dimension=dimension, group_id=group_id)
    selected = selected[selected["group_id"].notna()].copy()
    if selected.empty:
        return pd.DataFrame(
            columns=[
                "cbo_6d",
                "dimension",
                "group_id",
                "period",
                "admissions",
                "wage_sum",
                "wage_count",
            ]
        )
    selected["valid_wage"] = selected["salario_mensal"].gt(0) & selected[
        "salario_mensal"
    ].notna()
    selected["wage_value"] = selected["salario_mensal"].where(
        selected["valid_wage"],
        0.0,
    )
    selected["wage_observation"] = selected["valid_wage"].astype(int)
    return (
        selected.groupby(
            ["cbo_6d", "dimension", "group_id", "period"],
            observed=True,
        )
        .agg(
            admissions=("saldo_movimentacao", "size"),
            wage_sum=("wage_value", "sum"),
            wage_count=("wage_observation", "sum"),
        )
        .reset_index()
    )


def aggregate_admission_records(records: pd.DataFrame) -> pd.DataFrame:
    """Aggregate one in-memory record batch into auditable CBO6 monthly cells."""
    missing = sorted(set(RAW_COLUMNS) - set(records.columns))
    if missing:
        raise RuntimeError(f"Raw CAGED records are missing columns: {missing}")
    data = records.copy()
    data = data[pd.to_numeric(data["saldo_movimentacao"], errors="coerce").eq(1)]
    if data.empty:
        return _summarize_group(
            data.assign(cbo_6d=pd.Series(dtype="string"), period=pd.Series(dtype="string")),
            dimension="overall",
            group_id=pd.Series(dtype="string"),
        )
    data["cbo_6d"] = normalize_codes(data["cbo_2002"]).str.zfill(6)
    data["period"] = (
        pd.to_numeric(data["ano"], errors="coerce").astype("Int64").astype(str)
        + "-"
        + pd.to_numeric(data["mes"], errors="coerce")
        .astype("Int64")
        .astype(str)
        .str.zfill(2)
    )
    data = data[data["period"].between(START_PERIOD, END_PERIOD)]
    data["salario_mensal"] = pd.to_numeric(
        data["salario_mensal"],
        errors="coerce",
    )
    dimensions = [
        ("overall", pd.Series("all", index=data.index, dtype="string")),
        ("age", assign_age_group(data["idade"])),
        ("sex", assign_demographic_group(data, "sex")),
        ("race_color", assign_demographic_group(data, "race_color")),
        ("education", assign_demographic_group(data, "education")),
    ]
    pieces = [
        _summarize_group(data, dimension=dimension, group_id=group)
        for dimension, group in dimensions
    ]
    return pd.concat(pieces, ignore_index=True)


def _filter_record_batch(
    batch: pa.RecordBatch,
    eligible_codes: pa.Array,
) -> pd.DataFrame:
    table = pa.Table.from_batches([batch])
    period_number = pc.add(pc.multiply(table["ano"], 100), table["mes"])
    mask = pc.and_kleene(
        pc.equal(table["saldo_movimentacao"], 1),
        pc.and_kleene(
            pc.is_in(table["cbo_2002"], value_set=eligible_codes),
            pc.and_kleene(
                pc.greater_equal(period_number, int(START_PERIOD.replace("-", ""))),
                pc.less_equal(period_number, int(END_PERIOD.replace("-", ""))),
            ),
        ),
    )
    filtered = table.filter(mask)
    return filtered.to_pandas() if filtered.num_rows else pd.DataFrame(columns=RAW_COLUMNS)


def scan_caged_cells(
    raw_paths: list[Path],
    eligible_codes: set[str],
    *,
    selected_records_path: Path | None = None,
    log=print,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Scan the raw CAGED files once and return consolidated cells plus scan audit."""
    if not raw_paths:
        raise FileNotFoundError("No raw CAGED parquet files were provided.")
    code_array = pa.array(sorted(eligible_codes), type=pa.string())
    pieces: list[pd.DataFrame] = []
    audit_rows: list[dict[str, object]] = []
    writer: pq.ParquetWriter | None = None
    if selected_records_path is not None:
        selected_records_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        for path in raw_paths:
            if not path.exists():
                raise FileNotFoundError(path)
            parquet = pq.ParquetFile(path)
            source_rows = int(parquet.metadata.num_rows)
            selected_rows = 0
            batches = 0
            log(f"Scanning {path.name} ({source_rows:,} rows)...")
            for batch in parquet.iter_batches(
                batch_size=RAW_BATCH_SIZE,
                columns=RAW_COLUMNS,
            ):
                batches += 1
                filtered = _filter_record_batch(batch, code_array)
                if filtered.empty:
                    continue
                selected_rows += len(filtered)
                pieces.append(aggregate_admission_records(filtered))
                if selected_records_path is not None:
                    table = pa.Table.from_pandas(
                        filtered[RAW_COLUMNS],
                        preserve_index=False,
                    )
                    if writer is None:
                        writer = pq.ParquetWriter(
                            selected_records_path,
                            table.schema,
                            compression="zstd",
                        )
                    writer.write_table(table)
            audit_rows.append(
                {
                    "source_file": str(path),
                    "source_rows": source_rows,
                    "selected_admissions": selected_rows,
                    "batches": batches,
                    "bytes": path.stat().st_size,
                }
            )
            log(f"Selected {selected_rows:,} admissions from {path.name}.")
    finally:
        if writer is not None:
            writer.close()
    if not pieces:
        raise RuntimeError("No admissions matched the frozen occupation dictionary.")
    keys = ["cbo_6d", "dimension", "group_id", "period"]
    cells = (
        pd.concat(pieces, ignore_index=True)
        .groupby(keys, observed=True)
        .agg(
            admissions=("admissions", "sum"),
            wage_sum=("wage_sum", "sum"),
            wage_count=("wage_count", "sum"),
        )
        .reset_index()
        .sort_values(keys)
        .reset_index(drop=True)
    )
    cells["admissions"] = cells["admissions"].astype(int)
    cells["wage_count"] = cells["wage_count"].astype(int)
    return cells, pd.DataFrame(audit_rows)


def compute_record_wage_winsor_bounds(
    selected_records_path: Path,
    *,
    lower_q: float = 0.01,
    upper_q: float = 0.99,
) -> pd.DataFrame:
    """Compute exact positive-wage P1/P99 bounds within CBO6 and calendar year."""
    if not 0 <= lower_q < upper_q <= 1:
        raise ValueError("Record-wage quantiles must satisfy 0 <= lower < upper <= 1.")
    if not selected_records_path.exists():
        raise FileNotFoundError(selected_records_path)
    values: dict[tuple[int, str], list[np.ndarray]] = {}
    parquet = pq.ParquetFile(selected_records_path)
    for batch in parquet.iter_batches(
        batch_size=RAW_BATCH_SIZE,
        columns=["ano", "cbo_2002", "salario_mensal"],
    ):
        frame = batch.to_pandas()
        frame["salario_mensal"] = pd.to_numeric(
            frame["salario_mensal"],
            errors="coerce",
        )
        frame = frame[frame["salario_mensal"].gt(0)].copy()
        frame["cbo_6d"] = normalize_codes(frame["cbo_2002"]).str.zfill(6)
        for (year, code), group in frame.groupby(["ano", "cbo_6d"], observed=True):
            values.setdefault((int(year), str(code)), []).append(
                group["salario_mensal"].to_numpy(dtype=float, copy=True)
            )
    rows: list[dict[str, object]] = []
    for (year, code), chunks in sorted(values.items()):
        wage = np.concatenate(chunks)
        lower, upper = np.quantile(wage, [lower_q, upper_q])
        rows.append(
            {
                "ano": year,
                "cbo_6d": code,
                "positive_wage_records": len(wage),
                "lower_quantile": lower_q,
                "upper_quantile": upper_q,
                "lower_bound": float(lower),
                "upper_bound": float(upper),
                "raw_min": float(wage.min()),
                "raw_max": float(wage.max()),
                "records_below_lower_bound": int((wage < lower).sum()),
                "records_above_upper_bound": int((wage > upper).sum()),
            }
        )
    if not rows:
        raise RuntimeError("No positive admission wages were available for winsorization.")
    return pd.DataFrame(rows)


def apply_record_wage_winsorization(
    records: pd.DataFrame,
    bounds: pd.DataFrame,
) -> pd.DataFrame:
    """Apply frozen CBO6-year wage bounds while retaining invalid wages as missing."""
    data = records.copy()
    data["cbo_6d"] = normalize_codes(data["cbo_2002"]).str.zfill(6)
    data = data.merge(
        bounds[["ano", "cbo_6d", "lower_bound", "upper_bound"]],
        on=["ano", "cbo_6d"],
        how="left",
        validate="many_to_one",
    )
    positive = pd.to_numeric(data["salario_mensal"], errors="coerce").gt(0)
    if data.loc[positive, ["lower_bound", "upper_bound"]].isna().any(axis=None):
        raise RuntimeError("Positive wages were found without CBO6-year winsorization bounds.")
    data.loc[positive, "salario_mensal"] = pd.to_numeric(
        data.loc[positive, "salario_mensal"],
        errors="coerce",
    ).clip(
        lower=data.loc[positive, "lower_bound"],
        upper=data.loc[positive, "upper_bound"],
        axis=0,
    )
    return data.drop(columns=["cbo_6d", "lower_bound", "upper_bound"])


def scan_winsorized_selected_cells(
    selected_records_path: Path,
    bounds: pd.DataFrame,
    *,
    log=print,
) -> pd.DataFrame:
    """Re-aggregate the once-filtered record cache using record-level robust wages."""
    parquet = pq.ParquetFile(selected_records_path)
    pieces: list[pd.DataFrame] = []
    for batch_number, batch in enumerate(
        parquet.iter_batches(batch_size=RAW_BATCH_SIZE, columns=RAW_COLUMNS),
        start=1,
    ):
        records = apply_record_wage_winsorization(batch.to_pandas(), bounds)
        pieces.append(aggregate_admission_records(records))
        if batch_number % 10 == 0:
            log(f"Processed {batch_number} selected-record batches for robust wages.")
    keys = ["cbo_6d", "dimension", "group_id", "period"]
    out = (
        pd.concat(pieces, ignore_index=True)
        .groupby(keys, observed=True)
        .agg(
            admissions=("admissions", "sum"),
            wage_sum=("wage_sum", "sum"),
            wage_count=("wage_count", "sum"),
        )
        .reset_index()
        .sort_values(keys)
        .reset_index(drop=True)
    )
    out["admissions"] = out["admissions"].astype(int)
    out["wage_count"] = out["wage_count"].astype(int)
    return out
