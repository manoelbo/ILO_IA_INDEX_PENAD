#!/usr/bin/env python3
"""Publish Anatel A6 support diagnostics without estimating outcome models."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import duckdb
import numpy as np
import pandas as pd


V2_ROOT = Path(
    os.environ.get(
        "REPLICATION_PACKAGE_ROOT",
        Path(__file__).resolve().parents[2],
    )
).resolve()
FRONT_DIR = Path(__file__).resolve().parents[1]
COMMON_DIR = V2_ROOT / "code" / "common"
PANEL_CODE_DIR = V2_ROOT / "code" / "caged" / "panel"
for package_path in (COMMON_DIR, PANEL_CODE_DIR):
    if str(package_path) not in sys.path:
        sys.path.insert(0, str(package_path))

from build_panel import _configure_connection  # noqa: E402
from merge_audit import audited_merge  # noqa: E402
from paths import portable_path  # noqa: E402

PNAD_PATH = (
    FRONT_DIR
    / "data"
    / "vintage"
    / "pnad_continua_tic_2021_sidra_table_7334.json"
)
PNAD_EXPECTED_SHA256 = (
    "845e9a5a28a3e4f2343f035f67a9a7daa7de01ac037dfb0679ba3565b24e390a"
)
PNAD_VARIABLE_CODE = "10659"
PNAD_YEAR = "2021"
PNAD_AGE_GROUP_CODE = "95253"

PRE_START = 202101
PRE_END = 202211
TREATMENT_PERIOD = 202212
DIGITAL_CNAE_DIVISIONS = frozenset(
    {"58", "59", "60", "61", "62", "63"}
)
MOVEMENTS_GLOB = (
    V2_ROOT
    / "data"
    / "interim"
    / "movimentacoes"
    / "competenciamov=*"
    / "part.parquet"
)
PANEL_PATH = FRONT_DIR / "data" / "painel_anatel.parquet"
PROXY_ASSIGNMENTS_PATH = (
    FRONT_DIR / "data" / "anatel_a6_proxy_assignments.csv"
)
PROXY2_PATH = (
    FRONT_DIR / "data" / "anatel_proxy2_digital_admission_share.csv"
)
PROXY3_PATH = FRONT_DIR / "data" / "anatel_proxy3_pnad_tic_2021.csv"

RESIDUAL_PATH = (
    FRONT_DIR / "results" / "anatel_a6_residual_variation.csv"
)
COEXISTENCE_PATH = FRONT_DIR / "results" / "anatel_a6_coexistence.csv"
FE_SUPPORT_PATH = FRONT_DIR / "results" / "anatel_fe_support.csv"
CELL_SUPPORT_PATH = FRONT_DIR / "results" / "anatel_a6_cell_support.csv"
CLUSTER_PATH = FRONT_DIR / "results" / "anatel_a6_cluster_structure.csv"
CORRELATION_PATH = (
    FRONT_DIR / "results" / "anatel_a6_proxy_correlation.csv"
)
CORRELATION_PAIRS_PATH = (
    FRONT_DIR / "results" / "anatel_a6_proxy_correlation_pairs.csv"
)
DISTRIBUTION_PATH = (
    FRONT_DIR / "results" / "anatel_a6_proxy_distribution.csv"
)
ABSORPTION_PATH = (
    FRONT_DIR / "results" / "anatel_a6_absorption_balance.csv"
)
FAMILY_PATH = FRONT_DIR / "results" / "anatel_family_f_declaration.csv"
STATUS_PATH = FRONT_DIR / "results" / "anatel_a6_status.json"
REPORT_PATH = FRONT_DIR / "results" / "ANATEL_A6_SUPPORT.md"

OUTCOMES = (
    "ln_admissoes",
    "ln_desligamentos",
    "ln_salario_real_adm",
    "asinh_saldo",
)
PROXIES = (
    "fixed_broadband_penetration",
    "digital_intensive_admission_share",
    "pnad_internet_use_2021",
)

STATUS_ORDER = {"thin": 0, "limited": 1, "adequate": 2}


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def parse_pnad_sidra(
    payload: list[dict[str, Any]],
    *,
    require_27_ufs: bool = True,
) -> pd.DataFrame:
    """Validate and normalize the frozen SIDRA table 7334 response."""
    if len(payload) < 2:
        raise RuntimeError("PNAD SIDRA payload has no observations")
    rows = pd.DataFrame(payload[1:])
    required = {
        "NC",
        "V",
        "D1C",
        "D1N",
        "D2C",
        "D2N",
        "D3C",
        "D3N",
        "D4C",
        "D4N",
    }
    missing = sorted(required - set(rows.columns))
    if missing:
        raise RuntimeError(f"PNAD SIDRA payload is missing columns: {missing}")
    if not rows["NC"].astype(str).eq("3").all():
        raise RuntimeError("PNAD SIDRA geography is not Federative Unit")
    if not rows["D2C"].astype(str).eq(PNAD_VARIABLE_CODE).all():
        raise RuntimeError("PNAD SIDRA variable does not match 10659")
    if not rows["D3C"].astype(str).eq(PNAD_YEAR).all():
        raise RuntimeError("PNAD SIDRA year does not match 2021")
    if not rows["D4C"].astype(str).eq(PNAD_AGE_GROUP_CODE).all():
        raise RuntimeError("PNAD SIDRA age group is not the total population")
    result = pd.DataFrame(
        {
            "uf_code": rows["D1C"].astype(str).str.zfill(2),
            "uf_name": rows["D1N"].astype(str),
            "internet_use_pct": pd.to_numeric(rows["V"], errors="raise"),
            "year": pd.to_numeric(rows["D3C"], errors="raise").astype(int),
            "age_group": rows["D4N"].astype(str),
            "sidra_variable_code": rows["D2C"].astype(str),
        }
    ).sort_values("uf_code", ignore_index=True)
    if result["uf_code"].duplicated().any():
        raise RuntimeError("PNAD SIDRA has duplicate Federative Units")
    if require_27_ufs and len(result) != 27:
        raise RuntimeError(
            f"PNAD SIDRA must contain 27 Federative Units, observed {len(result)}"
        )
    if not result["internet_use_pct"].between(0, 100).all():
        raise RuntimeError("PNAD SIDRA percentages are outside [0, 100]")
    return result


def build_digital_admission_share(records: pd.DataFrame) -> pd.DataFrame:
    """Compute the signed pre-period admission share in CNAE divisions 58–63."""
    required = {
        "id_municipio",
        "periodo_num",
        "saldomovimentacao",
        "peso",
        "cnae_division",
    }
    missing = sorted(required - set(records.columns))
    if missing:
        raise ValueError(f"Proxy 2 records are missing columns: {missing}")
    source = records.copy()
    source["id_municipio"] = source["id_municipio"].astype(str)
    municipalities = pd.Index(
        source["id_municipio"].drop_duplicates(),
        name="id_municipio",
    )
    period = pd.to_numeric(source["periodo_num"], errors="raise")
    movement = pd.to_numeric(
        source["saldomovimentacao"], errors="raise"
    )
    source = source.loc[
        period.between(PRE_START, PRE_END) & movement.eq(1)
    ].copy()
    source["peso"] = pd.to_numeric(source["peso"], errors="raise")
    source["cnae_division"] = (
        source["cnae_division"].astype(str).str.strip().str.zfill(2)
    )
    source["signed_digital_admission"] = source["peso"].where(
        source["cnae_division"].isin(DIGITAL_CNAE_DIVISIONS),
        0,
    )
    grouped = source.groupby("id_municipio", observed=True).agg(
        signed_admissions=("peso", "sum"),
        signed_digital_admissions=("signed_digital_admission", "sum"),
    )
    grouped = grouped.reindex(municipalities, fill_value=0).reset_index()
    denominator = grouped["signed_admissions"].where(
        grouped["signed_admissions"].gt(0)
    )
    grouped["digital_admission_share"] = (
        grouped["signed_digital_admissions"] / denominator
    )
    return grouped


def assign_municipality_median_split(
    municipalities: pd.DataFrame,
    *,
    value_column: str,
    high_column: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Split unique sample municipalities above their municipality median."""
    required = {"id_municipio", value_column}
    missing = sorted(required - set(municipalities.columns))
    if missing:
        raise ValueError(f"Median split is missing columns: {missing}")
    result = municipalities.copy()
    if result["id_municipio"].duplicated().any():
        raise RuntimeError("Median split requires unique municipalities")
    values = pd.to_numeric(result[value_column], errors="raise")
    if values.isna().any():
        raise RuntimeError("Median split contains a missing value")
    threshold = float(values.median())
    result[high_column] = values.gt(threshold).astype("int8")
    total = int(len(result))
    high = int(result[high_column].sum())
    return result, {
        "threshold": threshold,
        "municipalities": total,
        "high_municipalities": high,
        "low_municipalities": total - high,
        "high_share": high / total,
        "low_share": (total - high) / total,
        "ties_assigned_low": int(values.eq(threshold).sum()),
    }


def _factorize_fixed_effects(
    frame: pd.DataFrame,
    fixed_effects: Iterable[str],
) -> list[tuple[np.ndarray, int]]:
    factors: list[tuple[np.ndarray, int]] = []
    for column in fixed_effects:
        if column not in frame.columns:
            raise ValueError(f"Missing fixed effect: {column}")
        codes, levels = pd.factorize(frame[column], sort=False)
        if np.any(codes < 0):
            raise RuntimeError(f"Fixed effect {column} contains missing values")
        factors.append((codes.astype(np.int64), len(levels)))
    return factors


def residualize_fixed_effects(
    values: np.ndarray | pd.Series,
    frame: pd.DataFrame,
    fixed_effects: Iterable[str],
    *,
    tolerance: float = 1e-12,
    max_iterations: int = 10_000,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Residualize a vector by alternating projections over categorical FEs."""
    residual = np.asarray(values, dtype=float).copy()
    if residual.ndim != 1 or len(residual) != len(frame):
        raise ValueError("Residualization values must align one-to-one with rows")
    if not np.isfinite(residual).all():
        raise RuntimeError("Residualization values must be finite")
    factors = _factorize_fixed_effects(frame, fixed_effects)
    return _residualize_factor_codes(
        residual,
        factors,
        tolerance=tolerance,
        max_iterations=max_iterations,
    )


def _residualize_factor_codes(
    values: np.ndarray | pd.Series,
    factors: list[tuple[np.ndarray, int]],
    *,
    tolerance: float = 1e-12,
    max_iterations: int = 10_000,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Residualize using validated, precomputed categorical FE codes."""
    residual = np.asarray(values, dtype=float).copy()
    converged = False
    maximum_adjustment = float("inf")
    iterations = 0
    for iterations in range(1, max_iterations + 1):
        maximum_adjustment = 0.0
        for codes, level_count in factors:
            counts = np.bincount(codes, minlength=level_count)
            sums = np.bincount(
                codes,
                weights=residual,
                minlength=level_count,
            )
            means = sums / counts
            maximum_adjustment = max(
                maximum_adjustment,
                float(np.max(np.abs(means))),
            )
            residual -= means[codes]
        if maximum_adjustment <= tolerance:
            converged = True
            break
    return residual, {
        "converged": converged,
        "iterations": iterations,
        "maximum_abs_adjustment": maximum_adjustment,
        "tolerance": tolerance,
    }


def iterative_singleton_keep(
    frame: pd.DataFrame,
    fixed_effects: Iterable[str],
) -> tuple[np.ndarray, dict[str, Any]]:
    """Return rows surviving iterative singleton removal across fixed effects."""
    factors = _factorize_fixed_effects(frame, fixed_effects)
    keep = np.ones(len(frame), dtype=bool)
    rounds = 0
    removed_by_round: list[int] = []
    while keep.any():
        singleton = np.zeros(len(frame), dtype=bool)
        for codes, level_count in factors:
            counts = np.bincount(
                codes[keep],
                minlength=level_count,
            )
            singleton |= keep & (counts[codes] == 1)
        removed = int(singleton.sum())
        if removed == 0:
            break
        keep[singleton] = False
        rounds += 1
        removed_by_round.append(removed)
    return keep, {
        "input_rows": int(len(frame)),
        "surviving_rows": int(keep.sum()),
        "removed_rows": int((~keep).sum()),
        "removed_share": float((~keep).mean()) if len(frame) else 0.0,
        "rounds": rounds,
        "removed_by_round": removed_by_round,
    }


def effective_cluster_count(
    residual: np.ndarray | pd.Series,
    clusters: pd.Series,
) -> float:
    """Compute inverse-Herfindahl effective clusters from residualized mass."""
    values = np.asarray(residual, dtype=float)
    if len(values) != len(clusters):
        raise ValueError("Residuals and clusters must have equal length")
    mass = pd.Series(values**2).groupby(
        clusters.reset_index(drop=True),
        observed=True,
    ).sum()
    total = float(mass.sum())
    if total <= 0:
        return 0.0
    shares = mass.to_numpy(dtype=float) / total
    return float(1.0 / np.sum(shares**2))


def classify_residual_variation(
    retained_variance_share: float,
    residual_standard_deviation: float,
) -> str:
    if residual_standard_deviation <= 1e-8:
        return "thin"
    if retained_variance_share >= 0.10:
        return "adequate"
    if retained_variance_share >= 0.01:
        return "limited"
    return "thin"


def classify_coexistence(pre_share: float, post_share: float) -> str:
    minimum = min(pre_share, post_share)
    if minimum >= 0.80:
        return "adequate"
    if minimum >= 0.50:
        return "limited"
    return "thin"


def classify_exposed_low(
    pre_cbo: int,
    pre_municipalities: int,
    post_cbo: int,
    post_municipalities: int,
) -> str:
    if (
        min(pre_cbo, post_cbo) >= 20
        and min(pre_municipalities, post_municipalities) >= 50
    ):
        return "adequate"
    if (
        min(pre_cbo, post_cbo) >= 10
        and min(pre_municipalities, post_municipalities) >= 25
    ):
        return "limited"
    return "thin"


def classify_cluster_support(
    effective_municipalities: float,
    effective_federative_units: float,
) -> str:
    municipality_status = (
        "adequate"
        if effective_municipalities >= 50
        else "limited"
        if effective_municipalities >= 25
        else "thin"
    )
    uf_status = (
        "adequate"
        if effective_federative_units >= 20
        else "limited"
        if effective_federative_units >= 10
        else "thin"
    )
    return min(
        (municipality_status, uf_status),
        key=STATUS_ORDER.__getitem__,
    )


def classify_balance(
    singleton_removed_share: float,
    cells_with_pre_and_post_share: float,
) -> str:
    if (
        singleton_removed_share <= 0.05
        and cells_with_pre_and_post_share >= 0.80
    ):
        return "adequate"
    if (
        singleton_removed_share <= 0.10
        and cells_with_pre_and_post_share >= 0.50
    ):
        return "limited"
    return "thin"


def correlation_label(correlation: float) -> str:
    absolute = abs(correlation)
    if absolute >= 0.95:
        return "near_collinear"
    if absolute <= 0.10:
        return "near_orthogonal"
    return "intermediate"


def family_f_declaration() -> pd.DataFrame:
    """Return the 12 fixed slots without coefficients or p-values."""
    return pd.DataFrame(
        [
            {
                "family": "F",
                "family_size": 12,
                "outcome": outcome,
                "proxy": proxy,
                "coefficient": np.nan,
                "p_value": np.nan,
                "bh_adjusted_p_value": np.nan,
                "status": "declared_not_estimated",
            }
            for outcome in OUTCOMES
            for proxy in PROXIES
        ]
    )


def evaluate_support_gate(metrics: dict[str, Any]) -> dict[str, Any]:
    """Apply the post-A-G1 protocol-amendment support gate."""
    failed: list[str] = []
    if not metrics["pnad_frozen"]:
        failed.append("pnad_frozen")
    if any(status == "thin" for status in metrics["residual_statuses"]):
        failed.append("residual_variation")
    if any(status == "thin" for status in metrics["cluster_statuses"]):
        failed.append("cluster_support")
    if metrics["coexistence_status"] == "thin":
        failed.append("coexistence")
    if (
        any(status == "thin" for status in metrics["cell_statuses"])
        or not metrics["all_cells_nonempty"]
    ):
        failed.append("exposed_low_cell")
    if metrics["pnad_distinct_status"] == "thin":
        failed.append("pnad_distinct_uf_support")
    if metrics["balance_status"] == "thin":
        failed.append("singleton_panel_balance")
    if (
        metrics["family_slots"] != 12
        or metrics["family_p_values_present"] != 0
        or metrics["family_coefficients_present"] != 0
    ):
        failed.append("family_f_declaration")
    return {
        "gate": "A6-support",
        "opens": not failed,
        "failed_criteria": failed,
        "decision": (
            "return_to_author_before_A7"
            if not failed
            else "stop_front_at_A6_no_family_F_estimation"
        ),
    }


def _read_frozen_pnad() -> pd.DataFrame:
    return parse_pnad_sidra(json.loads(PNAD_PATH.read_text(encoding="utf-8")))


def verify_frozen_pnad() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Verify the frozen PNAD bytes before parsing or assigning the proxy."""
    payload = PNAD_PATH.read_bytes()
    observed_hash = hashlib.sha256(payload).hexdigest()
    if observed_hash != PNAD_EXPECTED_SHA256:
        raise RuntimeError(
            "Frozen PNAD SHA-256 mismatch: "
            f"expected {PNAD_EXPECTED_SHA256}, observed {observed_hash}"
        )
    parsed = parse_pnad_sidra(json.loads(payload))
    return parsed, {
        "path": portable_path(PNAD_PATH, relative_to=FRONT_DIR),
        "bytes": len(payload),
        "expected_sha256": PNAD_EXPECTED_SHA256,
        "observed_sha256": observed_hash,
        "sha256_verified": True,
        "sidra_table": 7334,
        "sidra_variable": int(PNAD_VARIABLE_CODE),
        "federative_units": int(len(parsed)),
        "reference": "fourth_quarter_2021",
        "strictly_pre_event": True,
    }


def compute_proxy2_from_signed_partitions(
    sample_municipalities: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate proxy 2 from signed V2 admissions for sample municipalities."""
    required = {"id_municipio", "municipio_caged_6d"}
    missing = sorted(required - set(sample_municipalities.columns))
    if missing:
        raise ValueError(f"Sample municipality map is missing: {missing}")
    municipality_map = sample_municipalities[
        ["id_municipio", "municipio_caged_6d"]
    ].copy()
    if municipality_map.duplicated("id_municipio").any():
        raise RuntimeError("Sample has duplicate seven-digit municipality IDs")
    if municipality_map.duplicated("municipio_caged_6d").any():
        raise RuntimeError("Sample has duplicate six-digit municipality IDs")
    municipality_map["id_municipio"] = (
        municipality_map["id_municipio"].astype(str).str.zfill(7)
    )
    municipality_map["municipio_caged_6d"] = (
        municipality_map["municipio_caged_6d"].astype(str).str.zfill(6)
    )
    with tempfile.TemporaryDirectory(
        prefix="a6-proxy2-duckdb-",
        dir=FRONT_DIR / "data",
    ) as temporary_name:
        connection = duckdb.connect()
        try:
            _configure_connection(connection, Path(temporary_name))
            connection.register(
                "sample_municipality_input",
                municipality_map[["municipio_caged_6d"]],
            )
            source = _sql_literal(MOVEMENTS_GLOB)
            divisions = ", ".join(
                _sql_literal(value)
                for value in sorted(DIGITAL_CNAE_DIVISIONS)
            )
            aggregate = connection.execute(
                f"""
                WITH valid_admissions AS (
                    SELECT
                        trim(CAST(municipio AS VARCHAR))
                            AS municipio_caged_6d,
                        substring(
                            trim(CAST(subclasse AS VARCHAR)), 1, 2
                        ) AS cnae_division,
                        CAST(peso AS BIGINT) AS peso
                    FROM read_parquet(
                        {source},
                        hive_partitioning = true,
                        union_by_name = true
                    )
                    WHERE CAST(competenciamov AS INTEGER)
                          BETWEEN {PRE_START} AND {PRE_END}
                      AND regexp_full_match(
                          CAST(cbo2002ocupacao AS VARCHAR),
                          '[0-9]{{4,6}}'
                      )
                      AND substring(
                          CAST(cbo2002ocupacao AS VARCHAR), 1, 4
                      ) <> '0000'
                      AND CAST(idade AS INTEGER) BETWEEN 14 AND 90
                      AND CAST(salario AS DOUBLE) > 0
                      AND CAST(salario AS DOUBLE) < 1000000
                      AND CAST(saldomovimentacao AS INTEGER) = 1
                      AND CAST(peso AS INTEGER) IN (-1, 1)
                      AND trim(CAST(municipio AS VARCHAR)) IN (
                          SELECT municipio_caged_6d
                          FROM sample_municipality_input
                      )
                )
                SELECT
                    municipio_caged_6d,
                    CAST(sum(peso) AS BIGINT) AS signed_admissions,
                    CAST(sum(
                        CASE
                            WHEN cnae_division IN ({divisions}) THEN peso
                            ELSE 0
                        END
                    ) AS BIGINT) AS signed_digital_admissions
                FROM valid_admissions
                GROUP BY municipio_caged_6d
                ORDER BY municipio_caged_6d
                """
            ).df()
        finally:
            connection.close()
    proxy = audited_merge(
        municipality_map,
        aggregate,
        merge_id="a6_proxy2_signed_admission_share",
        validate="one_to_one",
        on="municipio_caged_6d",
        how="left",
    )
    if proxy[["signed_admissions", "signed_digital_admissions"]].isna().any().any():
        missing_ids = proxy.loc[
            proxy["signed_admissions"].isna(), "id_municipio"
        ].tolist()
        raise RuntimeError(
            "Proxy 2 lacks signed admissions for sample municipalities: "
            f"{missing_ids[:10]}"
        )
    if proxy["signed_admissions"].le(0).any():
        invalid_ids = proxy.loc[
            proxy["signed_admissions"].le(0), "id_municipio"
        ].tolist()
        raise RuntimeError(
            "Proxy 2 has non-positive signed admission denominators: "
            f"{invalid_ids[:10]}"
        )
    if (
        proxy["signed_digital_admissions"].lt(0).any()
        or proxy["signed_digital_admissions"]
        .gt(proxy["signed_admissions"])
        .any()
    ):
        raise RuntimeError("Proxy 2 signed numerator is outside its denominator")
    proxy["digital_admission_share"] = (
        proxy["signed_digital_admissions"] / proxy["signed_admissions"]
    )
    return proxy


def build_proxy_assignments(
    panel_municipalities: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """Construct all three continuous proxies and within-sample splits."""
    required = {
        "id_municipio",
        "municipio_caged_6d",
        "uf_code",
        "penetracao_bl",
        "high_connectivity",
    }
    missing = sorted(required - set(panel_municipalities.columns))
    if missing:
        raise ValueError(f"Panel municipality table is missing: {missing}")
    base = panel_municipalities[list(required)].copy()
    if base.duplicated("id_municipio").any():
        raise RuntimeError("Panel municipality table is not unique")
    if len(base) != 657:
        raise RuntimeError(
            f"A6 requires 657 sample municipalities, observed {len(base)}"
        )
    base["id_municipio"] = base["id_municipio"].astype(str).str.zfill(7)
    base["municipio_caged_6d"] = (
        base["municipio_caged_6d"].astype(str).str.zfill(6)
    )
    base["uf_code"] = base["uf_code"].astype(str).str.zfill(2)

    proxy2 = compute_proxy2_from_signed_partitions(base)
    proxy2_split, proxy2_cut = assign_municipality_median_split(
        proxy2,
        value_column="digital_admission_share",
        high_column="high_digital_admission_share",
    )
    pnad, pnad_support = verify_frozen_pnad()
    proxy3 = audited_merge(
        base[["id_municipio", "uf_code"]],
        pnad,
        merge_id="a6_proxy3_pnad_by_uf",
        validate="many_to_one",
        on="uf_code",
        how="left",
    )
    if proxy3["internet_use_pct"].isna().any():
        raise RuntimeError("Proxy 3 PNAD merge produced missing values")
    proxy3_split, proxy3_cut = assign_municipality_median_split(
        proxy3,
        value_column="internet_use_pct",
        high_column="high_pnad_internet_use",
    )
    assignments = audited_merge(
        base,
        proxy2_split[
            [
                "id_municipio",
                "signed_admissions",
                "signed_digital_admissions",
                "digital_admission_share",
                "high_digital_admission_share",
            ]
        ],
        merge_id="a6_attach_proxy2",
        validate="one_to_one",
        on="id_municipio",
        how="left",
    )
    assignments = audited_merge(
        assignments,
        proxy3_split[
            ["id_municipio", "internet_use_pct", "high_pnad_internet_use"]
        ],
        merge_id="a6_attach_proxy3",
        validate="one_to_one",
        on="id_municipio",
        how="left",
    )
    support = {
        "proxy1_cut": {
            "threshold": float(
                assignments.loc[
                    assignments["high_connectivity"].eq(0),
                    "penetracao_bl",
                ].max()
            ),
            "high_municipalities": int(
                assignments["high_connectivity"].sum()
            ),
            "low_municipalities": int(
                assignments["high_connectivity"].eq(0).sum()
            ),
        },
        "proxy2_cut": proxy2_cut,
        "proxy3_cut": proxy3_cut,
        "pnad": pnad_support,
        "proxy2_reference": {
            "period_start": PRE_START,
            "period_end": PRE_END,
            "digital_cnae_divisions": sorted(DIGITAL_CNAE_DIVISIONS),
            "numerator": (
                "sum(peso) for valid admissions in CNAE divisions 58-63"
            ),
            "denominator": "sum(peso) for all valid admissions",
            "employment_stock_claim": False,
        },
    }
    return assignments, support, proxy2_split, proxy3_split


def proxy_specifications() -> tuple[dict[str, str], ...]:
    return (
        {
            "proxy": "fixed_broadband_penetration",
            "continuous": "penetracao_bl",
            "high": "high_connectivity",
            "geographic_variation": "municipality_within_uf",
        },
        {
            "proxy": "digital_intensive_admission_share",
            "continuous": "digital_admission_share",
            "high": "high_digital_admission_share",
            "geographic_variation": "municipality_within_uf",
        },
        {
            "proxy": "pnad_internet_use_2021",
            "continuous": "internet_use_pct",
            "high": "high_pnad_internet_use",
            "geographic_variation": "federative_unit_between_uf",
        },
    )


def prepare_a6_panel(
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    """Read only support columns and attach the three frozen proxy splits."""
    columns = [
        "cbo_4d",
        "municipio_caged_6d",
        "id_municipio",
        "periodo_num",
        "periodo",
        "treated",
        "post",
        "uf_code",
        "cbo_municipio",
        "cbo_periodo",
        "uf_periodo",
        "penetracao_bl",
        "high_connectivity",
    ]
    panel = pd.read_parquet(PANEL_PATH, columns=columns)
    proxy_columns = [
        "id_municipio",
        "digital_admission_share",
        "high_digital_admission_share",
        "internet_use_pct",
        "high_pnad_internet_use",
    ]
    panel = audited_merge(
        panel,
        assignments[proxy_columns],
        merge_id="a6_attach_all_proxy_splits",
        validate="many_to_one",
        on="id_municipio",
        how="left",
    )
    if panel[proxy_columns[1:]].isna().any().any():
        raise RuntimeError("A6 proxy assignment merge produced missing values")
    if len(panel) != 4_343_581:
        raise RuntimeError(
            f"A6 requires 4,343,581 panel rows, observed {len(panel)}"
        )
    if panel["id_municipio"].nunique() != 657:
        raise RuntimeError("A6 panel does not contain 657 municipalities")
    if panel.duplicated(
        ["cbo_4d", "id_municipio", "periodo_num"]
    ).any():
        raise RuntimeError("A6 panel has duplicate observed cells")
    return panel


def coexistence_diagnostics(
    panel: pd.DataFrame,
) -> tuple[pd.DataFrame, str]:
    """Count municipality-months with both exposed and control occupations."""
    municipality_month = (
        panel.groupby(
            ["id_municipio", "periodo_num", "post"],
            observed=True,
        )["treated"]
        .agg(["min", "max"])
        .reset_index()
    )
    municipality_month["coexists"] = (
        municipality_month["min"].eq(0)
        & municipality_month["max"].eq(1)
    )
    rows: list[dict[str, Any]] = []
    for period, subset in (
        ("pre", municipality_month.loc[municipality_month["post"].eq(0)]),
        ("post", municipality_month.loc[municipality_month["post"].eq(1)]),
        ("overall", municipality_month),
    ):
        total = int(len(subset))
        coexisting = int(subset["coexists"].sum())
        rows.append(
            {
                "period": period,
                "observed_municipality_months": total,
                "coexisting_municipality_months": coexisting,
                "coexistence_share": coexisting / total,
            }
        )
    output = pd.DataFrame(rows)
    shares = output.set_index("period")["coexistence_share"]
    status = classify_coexistence(
        float(shares["pre"]),
        float(shares["post"]),
    )
    output["gate_status"] = status
    return output, status


def fe_ladder_support(panel: pd.DataFrame) -> pd.DataFrame:
    """Publish coexistence support for all three declared FE arrangements."""
    arrangements = (
        (
            "legacy_cbo4_plus_uf_period",
            "cbo_4d + uf_periodo",
            ["uf_code", "periodo_num", "post"],
            "uf_period",
        ),
        (
            "cbo_municipality_plus_period",
            "cbo_municipio + periodo",
            ["id_municipio", "periodo_num", "post"],
            "municipality_period",
        ),
        (
            "principal",
            "cbo_municipio + cbo_periodo + uf_periodo",
            ["id_municipio", "periodo_num", "post"],
            "municipality_period",
        ),
    )
    rows: list[dict[str, Any]] = []
    for arrangement, fixed_effects, group_columns, comparison_cell in arrangements:
        cells = (
            panel.groupby(group_columns, observed=True)["treated"]
            .agg(["min", "max"])
            .reset_index()
        )
        cells["coexists"] = cells["min"].eq(0) & cells["max"].eq(1)
        for period, subset in (
            ("pre", cells.loc[cells["post"].eq(0)]),
            ("post", cells.loc[cells["post"].eq(1)]),
            ("overall", cells),
        ):
            total = int(len(subset))
            coexisting = int(subset["coexists"].sum())
            rows.append(
                {
                    "arrangement": arrangement,
                    "fixed_effects": fixed_effects,
                    "role": (
                        "principal"
                        if arrangement == "principal"
                        else "diagnostic"
                    ),
                    "comparison_cell": comparison_cell,
                    "period": period,
                    "observed_cells": total,
                    "cells_with_exposed_and_control": coexisting,
                    "coexistence_share": coexisting / total,
                    "outcome_coefficient_estimated": False,
                }
            )
    return pd.DataFrame(rows)


def cell_support_diagnostics(
    panel: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, str], bool]:
    """Report all exposed/control × low/high cells before and after treatment."""
    rows: list[pd.DataFrame] = []
    statuses: dict[str, str] = {}
    all_nonempty = True
    for specification in proxy_specifications():
        proxy = specification["proxy"]
        high = specification["high"]
        grouped = (
            panel.groupby(["post", "treated", high], observed=True)
            .agg(
                panel_rows=("cbo_4d", "size"),
                municipalities=("id_municipio", "nunique"),
                cbo4=("cbo_4d", "nunique"),
            )
            .reset_index()
            .rename(columns={high: "high_proxy"})
        )
        expected = pd.MultiIndex.from_product(
            [[0, 1], [0, 1], [0, 1]],
            names=["post", "treated", "high_proxy"],
        ).to_frame(index=False)
        grouped = audited_merge(
            expected,
            grouped,
            merge_id=f"spatial_support_grid_{proxy}",
            on=["post", "treated", "high_proxy"],
            how="left",
            validate="one_to_one",
        )
        grouped[["panel_rows", "municipalities", "cbo4"]] = grouped[
            ["panel_rows", "municipalities", "cbo4"]
        ].fillna(0).astype(int)
        grouped["proxy"] = proxy
        grouped["period"] = np.where(grouped["post"].eq(0), "pre", "post")
        grouped["exposure_group"] = np.where(
            grouped["treated"].eq(1), "exposed", "not_exposed"
        )
        grouped["connectivity_group"] = np.where(
            grouped["high_proxy"].eq(1), "high", "low"
        )
        exposed_low = grouped.loc[
            grouped["treated"].eq(1) & grouped["high_proxy"].eq(0)
        ].set_index("period")
        status = classify_exposed_low(
            int(exposed_low.loc["pre", "cbo4"]),
            int(exposed_low.loc["pre", "municipalities"]),
            int(exposed_low.loc["post", "cbo4"]),
            int(exposed_low.loc["post", "municipalities"]),
        )
        statuses[proxy] = status
        grouped["exposed_low_gate_status"] = status
        all_nonempty = all_nonempty and bool(grouped["panel_rows"].gt(0).all())
        rows.append(grouped)
    return pd.concat(rows, ignore_index=True), statuses, all_nonempty


def proxy_correlation_diagnostics(
    assignments: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    columns = {
        specification["proxy"]: specification["continuous"]
        for specification in proxy_specifications()
    }
    values = assignments[list(columns.values())].rename(
        columns={value: key for key, value in columns.items()}
    )
    matrix = values.corr(method="pearson")
    matrix.insert(0, "proxy", matrix.index)
    matrix = matrix.reset_index(drop=True)
    pairs: list[dict[str, Any]] = []
    names = list(columns)
    for left_index, left in enumerate(names):
        for right in names[left_index + 1 :]:
            correlation = float(
                values[left].corr(values[right], method="pearson")
            )
            pairs.append(
                {
                    "proxy_left": left,
                    "proxy_right": right,
                    "correlation": correlation,
                    "classification": correlation_label(correlation),
                    "gate_role": "diagnostic_only",
                }
            )
    return matrix, pd.DataFrame(pairs)


def proxy_distribution_diagnostics(
    assignments: pd.DataFrame,
) -> tuple[pd.DataFrame, str]:
    """Summarize proxy scale and between/within-UF variance."""
    rows: list[dict[str, Any]] = []
    pnad_distinct_status = "thin"
    for specification in proxy_specifications():
        proxy = specification["proxy"]
        continuous = specification["continuous"]
        high = specification["high"]
        values = pd.to_numeric(assignments[continuous], errors="raise")
        overall_mean = float(values.mean())
        uf_means = values.groupby(assignments["uf_code"], observed=True).transform(
            "mean"
        )
        total_variance = float(np.mean((values - overall_mean) ** 2))
        between_variance = float(
            np.mean((uf_means.to_numpy() - overall_mean) ** 2)
        )
        within_variance = float(
            np.mean((values.to_numpy() - uf_means.to_numpy()) ** 2)
        )
        quantiles = values.quantile([0.25, 0.50, 0.75])
        threshold = float(values.median())
        uf_values = (
            assignments.groupby("uf_code", observed=True)[continuous]
            .mean()
            .reset_index()
            .sort_values("uf_code")
        )
        if (
            proxy == "pnad_internet_use_2021"
            and assignments.groupby("uf_code", observed=True)[continuous]
            .nunique()
            .max()
            != 1
        ):
            raise RuntimeError("PNAD proxy must be constant within each UF")
        row = {
            "proxy": proxy,
            "geographic_variation": specification["geographic_variation"],
            "municipalities": int(len(values)),
            "mean": overall_mean,
            "standard_deviation": float(values.std(ddof=1)),
            "minimum": float(values.min()),
            "q25": float(quantiles.loc[0.25]),
            "median": float(quantiles.loc[0.50]),
            "q75": float(quantiles.loc[0.75]),
            "maximum": float(values.max()),
            "range": float(values.max() - values.min()),
            "distinct_values_municipal": int(values.nunique()),
            "high_split_distinct_values": int(
                assignments[high].nunique()
            ),
            "threshold": threshold,
            "high_municipalities": int(assignments[high].sum()),
            "low_municipalities": int(assignments[high].eq(0).sum()),
            "ties_assigned_low": int(values.eq(threshold).sum()),
            "total_variance": total_variance,
            "between_uf_variance": between_variance,
            "within_uf_variance": within_variance,
            "between_uf_variance_share": (
                between_variance / total_variance
                if total_variance > 0
                else np.nan
            ),
            "within_uf_variance_share": (
                within_variance / total_variance
                if total_variance > 0
                else np.nan
            ),
            "unweighted_uf_count": int(len(uf_values)),
            "unweighted_uf_distinct_values": int(
                uf_values[continuous].nunique()
            ),
            "unweighted_uf_standard_deviation": float(
                uf_values[continuous].std(ddof=1)
            ),
            "unweighted_uf_range": float(
                uf_values[continuous].max()
                - uf_values[continuous].min()
            ),
        }
        if proxy == "pnad_internet_use_2021":
            distinct = row["unweighted_uf_distinct_values"]
            nonzero_scale = (
                row["unweighted_uf_standard_deviation"] > 0
                and row["unweighted_uf_range"] > 0
            )
            pnad_distinct_status = (
                "adequate"
                if distinct >= 20 and nonzero_scale
                else "limited"
                if distinct >= 10 and nonzero_scale
                else "thin"
            )
        row["pnad_distinct_uf_status"] = (
            pnad_distinct_status
            if proxy == "pnad_internet_use_2021"
            else "not_applicable"
        )
        rows.append(row)
    return pd.DataFrame(rows), pnad_distinct_status


def _maximum_fixed_effect_mean(
    residual: np.ndarray,
    factors: list[tuple[np.ndarray, int]],
) -> float:
    maximum = 0.0
    for codes, level_count in factors:
        counts = np.bincount(codes, minlength=level_count)
        sums = np.bincount(
            codes,
            weights=residual,
            minlength=level_count,
        )
        maximum = max(maximum, float(np.max(np.abs(sums / counts))))
    return maximum


def residual_cluster_absorption_diagnostics(
    panel: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    list[str],
    list[str],
    str,
    dict[str, Any],
]:
    """Residualize each key regressor and report clusters and absorption."""
    fixed_effects = ["cbo_municipio", "cbo_periodo", "uf_periodo"]
    keep, singleton = iterative_singleton_keep(panel, fixed_effects)
    surviving = panel.loc[keep].reset_index(drop=True)
    factors = _factorize_fixed_effects(surviving, fixed_effects)

    cell_balance = (
        surviving.groupby("cbo_municipio", observed=True)
        .agg(
            observed_months=("periodo_num", "nunique"),
            post_minimum=("post", "min"),
            post_maximum=("post", "max"),
        )
        .reset_index()
    )
    cell_balance["has_pre_and_post"] = (
        cell_balance["post_minimum"].eq(0)
        & cell_balance["post_maximum"].eq(1)
    )
    both_share = float(cell_balance["has_pre_and_post"].mean())
    balance_status = classify_balance(
        singleton["removed_share"],
        both_share,
    )
    month_quantiles = cell_balance["observed_months"].quantile(
        [0.25, 0.50, 0.75]
    )
    balance_common = {
        **singleton,
        "surviving_cbo_municipality_cells": int(len(cell_balance)),
        "cells_with_pre_and_post": int(
            cell_balance["has_pre_and_post"].sum()
        ),
        "cells_with_pre_and_post_share": both_share,
        "pre_only_cells": int(
            (
                cell_balance["post_minimum"].eq(0)
                & cell_balance["post_maximum"].eq(0)
            ).sum()
        ),
        "post_only_cells": int(
            (
                cell_balance["post_minimum"].eq(1)
                & cell_balance["post_maximum"].eq(1)
            ).sum()
        ),
        "observed_months_minimum": int(
            cell_balance["observed_months"].min()
        ),
        "observed_months_q25": float(month_quantiles.loc[0.25]),
        "observed_months_median": float(month_quantiles.loc[0.50]),
        "observed_months_q75": float(month_quantiles.loc[0.75]),
        "observed_months_maximum": int(
            cell_balance["observed_months"].max()
        ),
        "balance_status": balance_status,
    }

    residual_rows: list[dict[str, Any]] = []
    cluster_rows: list[dict[str, Any]] = []
    absorption_rows: list[dict[str, Any]] = []
    residual_statuses: list[str] = []
    cluster_statuses: list[str] = []
    for specification in proxy_specifications():
        proxy = specification["proxy"]
        high = specification["high"]
        key = (
            surviving["post"].to_numpy(dtype=float)
            * surviving["treated"].to_numpy(dtype=float)
            * surviving[high].to_numpy(dtype=float)
        )
        raw_mean = float(np.mean(key))
        raw_sst = float(np.sum((key - raw_mean) ** 2))
        if raw_sst <= 0:
            raise RuntimeError(f"{proxy} key regressor has zero raw variance")
        residual, demeaning = _residualize_factor_codes(
            key,
            factors,
            tolerance=1e-12,
            max_iterations=10_000,
        )
        if not demeaning["converged"]:
            raise RuntimeError(f"{proxy} fixed-effect residualization failed")
        residual_sse = float(np.sum(residual**2))
        retained = residual_sse / raw_sst
        raw_sd = float(np.std(key, ddof=0))
        residual_sd = float(np.std(residual, ddof=0))
        r_squared = 1.0 - retained
        residual_status = classify_residual_variation(
            retained,
            residual_sd,
        )
        residual_statuses.append(residual_status)
        maximum_fe_mean = _maximum_fixed_effect_mean(residual, factors)
        residual_rows.append(
            {
                "proxy": proxy,
                "fixed_effects": (
                    "cbo_municipio + cbo_periodo + uf_periodo"
                ),
                "panel_rows_input": int(len(panel)),
                "panel_rows_after_singletons": int(len(surviving)),
                "raw_standard_deviation": raw_sd,
                "residual_standard_deviation": residual_sd,
                "r_squared_fixed_effects": r_squared,
                "retained_variance_share": retained,
                "demeaning_iterations": demeaning["iterations"],
                "demeaning_tolerance": demeaning["tolerance"],
                "maximum_abs_fe_group_mean": maximum_fe_mean,
                "classification": residual_status,
                "outcome_model_estimated": False,
                "treatment_coefficient_estimated": False,
            }
        )

        effective_municipalities = effective_cluster_count(
            residual,
            surviving["id_municipio"],
        )
        effective_ufs = effective_cluster_count(
            residual,
            surviving["uf_code"],
        )
        cluster_status = classify_cluster_support(
            effective_municipalities,
            effective_ufs,
        )
        cluster_statuses.append(cluster_status)
        uf_mass = pd.Series(residual**2).groupby(
            surviving["uf_code"].reset_index(drop=True),
            observed=True,
        ).sum()
        uf_leverage = uf_mass / uf_mass.sum()
        largest_uf = str(uf_leverage.idxmax())
        cluster_rows.append(
            {
                "proxy": proxy,
                "municipality_clusters_nominal": int(
                    surviving["id_municipio"].nunique()
                ),
                "uf_clusters_nominal": int(
                    surviving["uf_code"].nunique()
                ),
                "continuous_proxy_distinct_values": int(
                    surviving[specification["continuous"]].nunique()
                ),
                "split_proxy_distinct_values": int(
                    surviving[high].nunique()
                ),
                "effective_municipality_clusters": (
                    effective_municipalities
                ),
                "effective_uf_clusters": effective_ufs,
                "largest_uf_leverage_code": largest_uf,
                "largest_uf_leverage_share": float(
                    uf_leverage.loc[largest_uf]
                ),
                "classification": cluster_status,
            }
        )

        absorbed = np.abs(residual) <= 1e-12
        cell_absorption = (
            pd.DataFrame(
                {
                    "cbo_municipio": surviving[
                        "cbo_municipio"
                    ].to_numpy(),
                    "abs_residual": np.abs(residual),
                }
            )
            .groupby("cbo_municipio", observed=True)["abs_residual"]
            .max()
            .le(1e-12)
        )
        absorption_rows.append(
            {
                "proxy": proxy,
                **balance_common,
                "absorbed_rows": int(absorbed.sum()),
                "absorbed_rows_share": float(absorbed.mean()),
                "fully_absorbed_cbo_municipality_cells": int(
                    cell_absorption.sum()
                ),
                "fully_absorbed_cbo_municipality_cells_share": float(
                    cell_absorption.mean()
                ),
            }
        )
        del residual
    return (
        pd.DataFrame(residual_rows),
        pd.DataFrame(cluster_rows),
        residual_statuses,
        cluster_statuses,
        balance_status,
        {
            "rows": absorption_rows,
            "common": balance_common,
        },
    )


def _format_markdown_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        if abs(float(value)) < 1e-4 and float(value) != 0:
            return f"{float(value):.6e}"
        return f"{float(value):.6f}"
    if isinstance(value, (bool, np.bool_)):
        return str(bool(value)).lower()
    return str(value)


def _markdown_table(
    frame: pd.DataFrame,
    columns: list[str] | None = None,
) -> str:
    selected = frame[columns] if columns is not None else frame
    header = "| " + " | ".join(selected.columns) + " |"
    separator = "| " + " | ".join("---" for _ in selected.columns) + " |"
    rows = [
        "| "
        + " | ".join(_format_markdown_value(value) for value in row)
        + " |"
        for row in selected.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *rows])


def build_a6_report(
    *,
    residual: pd.DataFrame,
    coexistence: pd.DataFrame,
    cell_support: pd.DataFrame,
    cluster: pd.DataFrame,
    correlation: pd.DataFrame,
    distribution: pd.DataFrame,
    absorption: pd.DataFrame,
    family: pd.DataFrame,
    gate: dict[str, Any],
    proxy_support: dict[str, Any],
) -> str:
    """Render the eight required diagnostics without effect interpretation."""
    gate_word = "OPEN" if gate["opens"] else "CLOSED"
    decision = gate["decision"]
    residual_view = residual.rename(
        columns={
            "r_squared_fixed_effects": "R2_FE",
            "raw_standard_deviation": "raw_sd",
            "residual_standard_deviation": "residual_sd",
            "retained_variance_share": "retained_share",
        }
    )
    cell_view = cell_support[
        [
            "proxy",
            "period",
            "exposure_group",
            "connectivity_group",
            "panel_rows",
            "municipalities",
            "cbo4",
            "exposed_low_gate_status",
        ]
    ]
    lines = [
        "# Anatel A6 — support diagnostics",
        "",
        "This report was produced before any Family F outcome coefficient or "
        "p-value. No outcome model and no real treatment coefficient were "
        "estimated.",
        "",
        "## 1. Residual identifying variation",
        "",
        "Threshold: `adequate` if residual SD > 1e-8 and retained variance "
        "≥ 10%; `limited` if residual SD > 1e-8 and retained variance ≥ 1%; "
        "`thin` otherwise.",
        "",
        _markdown_table(
            residual_view,
            [
                "proxy",
                "R2_FE",
                "raw_sd",
                "residual_sd",
                "retained_share",
                "demeaning_iterations",
                "classification",
            ],
        ),
        "",
        "## 2. Exposed/control coexistence",
        "",
        "Threshold: `adequate` if the share is ≥ 80% in both pre and post; "
        "`limited` if ≥ 50% in both; `thin` otherwise.",
        "",
        _markdown_table(coexistence),
        "",
        "## 3. Exposed/control × low/high support",
        "",
        "Threshold for the exposed × low cell in both pre and post: "
        "`adequate` at ≥ 20 CBO4 and ≥ 50 municipalities; `limited` at "
        "≥ 10 CBO4 and ≥ 25 municipalities; `thin` otherwise. Every 2×2 "
        "cell must be nonempty.",
        "",
        _markdown_table(cell_view),
        "",
        "## 4. Cluster structure",
        "",
        "Effective clusters use inverse Herfindahl shares of squared "
        "residualized-regressor mass. Municipality thresholds are 50/25; "
        "UF thresholds are 20/10 for `adequate`/`limited`; the weaker level "
        "classifies the proxy.",
        "",
        _markdown_table(cluster),
        "",
        "## 5. Proxy correlation matrix",
        "",
        "Absolute correlation ≥ 0.95 is `near_collinear`; ≤ 0.10 is "
        "`near_orthogonal`; this diagnostic does not determine the gate.",
        "",
        _markdown_table(correlation),
        "",
        "## 6. Proxy distributions and variance decomposition",
        "",
        "Proxy 3 requires at least 20 distinct UF values for `adequate`, "
        "10 for `limited`, and a nonzero UF range and standard deviation.",
        "",
        _markdown_table(distribution),
        "",
        "## 7. Singletons, absorption, and panel balance",
        "",
        "Threshold: `adequate` with ≤ 5% singleton removal and ≥ 80% of "
        "surviving cells observed pre and post; `limited` with ≤ 10% and "
        "≥ 50%; `thin` otherwise. A row is numerically absorbed when "
        "|residual| ≤ 1e-12.",
        "",
        _markdown_table(
            absorption,
            [
                "proxy",
                "input_rows",
                "surviving_rows",
                "removed_rows",
                "removed_share",
                "absorbed_rows",
                "absorbed_rows_share",
                "fully_absorbed_cbo_municipality_cells",
                "cells_with_pre_and_post",
                "cells_with_pre_and_post_share",
                "balance_status",
            ],
        ),
        "",
        "## 8. Family F declaration",
        "",
        f"- Declared slots: {len(family)}.",
        "- Fixed size: 12 = four outcomes × three proxies.",
        f"- Nonmissing coefficients: {int(family['coefficient'].notna().sum())}.",
        f"- Nonmissing p-values: {int(family['p_value'].notna().sum())}.",
        "- BH contract: one adjustment with `family_size=12`, only if A7 is "
        "later authorized.",
        "",
        "## Frozen proxy construction checks",
        "",
        f"- PNAD SHA-256 verified: "
        f"`{proxy_support['pnad']['observed_sha256']}`.",
        f"- Proxy 2 median: "
        f"{proxy_support['proxy2_cut']['threshold']:.9f}.",
        f"- Proxy 3 municipality-weighted median: "
        f"{proxy_support['proxy3_cut']['threshold']:.6f}.",
        "",
        "## Mechanical support gate",
        "",
        "Protocol provenance: this gate was not preregistered and was not a "
        "kill switch in the frozen A6 plan. It is a post-A-G1 protocol "
        "amendment declared before any A6 value was observed.",
        "",
        f"**A6 support gate: {gate_word}.**",
        "",
        f"- Failed criteria: "
        f"{', '.join(gate['failed_criteria']) if gate['failed_criteria'] else 'none'}.",
        f"- Derived decision: `{decision}`.",
        "- Execution stops here before A7.",
        "- Destination remains the appendix or Section 6.4 research agenda; "
        "never Section 5.",
    ]
    return "\n".join(lines)


def execute_a6() -> dict[str, Any]:
    """Run all A6 diagnostics, write artifacts, apply the gate, and stop."""
    municipality_columns = [
        "id_municipio",
        "municipio_caged_6d",
        "uf_code",
        "penetracao_bl",
        "high_connectivity",
    ]
    panel_municipalities = (
        pd.read_parquet(PANEL_PATH, columns=municipality_columns)
        .drop_duplicates()
        .sort_values("id_municipio")
        .reset_index(drop=True)
    )
    assignments, proxy_support, proxy2, proxy3 = build_proxy_assignments(
        panel_municipalities
    )
    panel = prepare_a6_panel(assignments)

    coexistence, coexistence_status = coexistence_diagnostics(panel)
    ladder = fe_ladder_support(panel)
    cell_support, cell_status_map, all_cells_nonempty = (
        cell_support_diagnostics(panel)
    )
    correlation, correlation_pairs = proxy_correlation_diagnostics(
        assignments
    )
    distribution, pnad_distinct_status = (
        proxy_distribution_diagnostics(assignments)
    )
    (
        residual,
        cluster,
        residual_statuses,
        cluster_statuses,
        balance_status,
        absorption_payload,
    ) = residual_cluster_absorption_diagnostics(panel)
    absorption = pd.DataFrame(absorption_payload["rows"])
    family = family_f_declaration()

    gate_metrics = {
        "pnad_frozen": bool(proxy_support["pnad"]["sha256_verified"]),
        "residual_statuses": residual_statuses,
        "cluster_statuses": cluster_statuses,
        "coexistence_status": coexistence_status,
        "cell_statuses": [
            cell_status_map[specification["proxy"]]
            for specification in proxy_specifications()
        ],
        "all_cells_nonempty": all_cells_nonempty,
        "pnad_distinct_status": pnad_distinct_status,
        "balance_status": balance_status,
        "family_slots": int(len(family)),
        "family_p_values_present": int(family["p_value"].notna().sum()),
        "family_coefficients_present": int(
            family["coefficient"].notna().sum()
        ),
    }
    gate = evaluate_support_gate(gate_metrics)
    status = {
        "status": (
            "support_gate_open"
            if gate["opens"]
            else "not_executed_support_failed"
        ),
        "stage": "A6",
        "gate": gate,
        "gate_provenance": {
            "preregistered": False,
            "frozen_plan_a6_kill_switch": False,
            "classification": (
                "post_a_g1_protocol_amendment_declared_before_a6_observation"
            ),
            "declaration_before_observation_preserved": True,
        },
        "gate_metrics": gate_metrics,
        "a1_resolved": True,
        "proxy2_definition": proxy_support["proxy2_reference"],
        "proxy_cuts": {
            "proxy1": proxy_support["proxy1_cut"],
            "proxy2": proxy_support["proxy2_cut"],
            "proxy3": proxy_support["proxy3_cut"],
        },
        "pnad_vintage": proxy_support["pnad"],
        "family_f_declared_slots": int(len(family)),
        "family_f_instantiated": False,
        "family_f_p_values_present": 0,
        "family_f_coefficients_present": 0,
        "outcome_model_estimated": False,
        "real_treatment_coefficient_estimated": False,
        "a7_executed": False,
        "stopped_before_a7": True,
        "destination": "appendix_or_section_6_4_agenda_never_section_5",
    }

    _atomic_csv(proxy2, PROXY2_PATH)
    _atomic_csv(proxy3, PROXY3_PATH)
    _atomic_csv(assignments, PROXY_ASSIGNMENTS_PATH)
    _atomic_csv(residual, RESIDUAL_PATH)
    _atomic_csv(coexistence, COEXISTENCE_PATH)
    _atomic_csv(ladder, FE_SUPPORT_PATH)
    _atomic_csv(cell_support, CELL_SUPPORT_PATH)
    _atomic_csv(cluster, CLUSTER_PATH)
    _atomic_csv(correlation, CORRELATION_PATH)
    _atomic_csv(correlation_pairs, CORRELATION_PAIRS_PATH)
    _atomic_csv(distribution, DISTRIBUTION_PATH)
    _atomic_csv(absorption, ABSORPTION_PATH)
    _atomic_csv(family, FAMILY_PATH)
    _atomic_json(status, STATUS_PATH)
    _atomic_text(
        build_a6_report(
            residual=residual,
            coexistence=coexistence,
            cell_support=cell_support,
            cluster=cluster,
            correlation=correlation,
            distribution=distribution,
            absorption=absorption,
            family=family,
            gate=gate,
            proxy_support=proxy_support,
        ),
        REPORT_PATH,
    )
    return status


def main() -> None:
    status = execute_a6()
    print(json.dumps(status, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
