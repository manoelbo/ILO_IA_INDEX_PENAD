from __future__ import annotations

import json
import math
from pathlib import Path

import duckdb
import pyarrow.parquet as pq


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data" / "derived" / "pnadc"
CONTRACTS_DIR = DATA_DIR / "contracts"
RESULTS_DIR = (
    PACKAGE_ROOT / "results" / "reference" / "artifacts" / "pnadc" / "backing_data"
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_individual_panel_satisfies_p7_contract() -> None:
    path = DATA_DIR / "painel_pnadc_individual.parquet"
    support = read_json(
        CONTRACTS_DIR / "painel_pnadc_individual_support.json"
    )
    schema = set(pq.ParquetFile(path).schema_arrow.names)
    row = duckdb.execute(
        """
        SELECT
            count(*),
            count(DISTINCT periodo),
            count(DISTINCT cod3),
            sum((periodo = '2022Q4')::INT),
            sum((exposure_gradient IN (
                'Minimal Exposure',
                'Sem classificação'
            ))::INT),
            sum((formal + informal <> 1)::INT)
        FROM read_parquet(?)
        """,
        [str(path)],
    ).fetchone()

    assert row == (
        support["rows"],
        56,
        support["cod3"],
        0,
        0,
        0,
    )
    assert not {"cod4", "cod_ocupacao"} & schema
    assert support["treatment_coefficients_computed"] is False


def test_cod3_panel_satisfies_p8_contract() -> None:
    path = DATA_DIR / "painel_pnadc_cod3.parquet"
    support = read_json(CONTRACTS_DIR / "painel_pnadc_cod3_support.json")
    schema = set(pq.ParquetFile(path).schema_arrow.names)
    row = duckdb.execute(
        """
        SELECT
            count(*),
            count(DISTINCT periodo),
            count(DISTINCT cod3),
            count(*) - count(DISTINCT (
                cod3 || ':' || trimestre_num::VARCHAR
            )),
            sum((
                ocupados_total < 0
                OR ocupados_formais < 0
                OR ocupados_informais < 0
            )::INT),
            max(abs(
                ocupados_formais
                + ocupados_informais
                - ocupados_total
            ))
        FROM read_parquet(?)
        """,
        [str(path)],
    ).fetchone()

    assert row[:5] == (
        support["cells"],
        56,
        support["cod3"],
        0,
        0,
    )
    assert math.isclose(
        row[5],
        support["maximum_formal_informal_identity_difference"],
        rel_tol=0,
        abs_tol=1e-15,
    )
    assert not {"cod4", "cod_ocupacao"} & schema
    assert support["section3_anchor_rows"] == 207_901
    assert support["section3_anchor_population"] == 97_783_776.1804
    assert support["treatment_coefficients_computed"] is False


def test_frozen_construction_receipt_is_separate_from_public_results() -> None:
    part2 = (
        RESULTS_DIR / "pnadc_pretrends.csv",
        RESULTS_DIR / "pnadc_results.csv",
        RESULTS_DIR / "pnadc_sensitivities.csv",
    )
    status = read_json(CONTRACTS_DIR / "pnadc_part1_status.json")
    assert status["gate"] == "P-B1"
    assert status["gate_status"] == "open"
    assert status["part2_started"] is False
    assert status["treatment_coefficients_computed"] is False

    assert all(path.exists() for path in part2)
    assert (RESULTS_DIR / "pnadc_cross_replication_status.json").is_file()
