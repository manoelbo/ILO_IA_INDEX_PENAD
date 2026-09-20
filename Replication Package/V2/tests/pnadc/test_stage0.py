from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

import v2_pnadc.stage0 as stage0


sys.path.insert(0, str(Path(__file__).resolve().parent))

from v2_pnadc.stage0 import (  # noqa: E402
    P1_COLUMNS,
    SECTION3_EXPECTED_POPULATION,
    attach_crosswalk,
    build_extract_query,
    build_ilo_crosswalk,
    classify_support,
    classify_2020_break,
    derive_cod3_treatment,
    build_reference_population_query,
    expected_periods,
    formal_indicator,
    fetch_sidra_6463,
    normalize_ftp_extract,
    parse_sidra_6463,
    registered_manifest_is_complete,
    run_bq_csv,
    select_ftp_archive_name,
    section3_anchor,
    validate_quarter_extract,
    validate_registered_asset,
)


def valid_quarter_extract() -> pd.DataFrame:
    rows = []
    for state_index in range(27):
        for person_index in range(4_000):
            rows.append(
                {
                    "ano": 2012,
                    "trimestre": 1,
                    "sigla_uf": f"UF{state_index:02d}",
                    "sexo": "1",
                    "idade": 18 + person_index % 48,
                    "raca_cor": "1",
                    "nivel_instrucao": "5",
                    "cod_ocupacao": "1111",
                    "grupamento_atividade": "01001",
                    "posicao_ocupacao": "1",
                    "rendimento_habitual": 2_000.0,
                    "horas_habituais": 40.0,
                    "peso": 100.0,
                }
            )
    return pd.DataFrame(rows, columns=P1_COLUMNS)


def test_expected_periods_are_the_preregistered_57_quarters() -> None:
    periods = expected_periods()

    assert len(periods) == 57
    assert periods[0] == (2012, 1)
    assert periods[-1] == (2026, 1)


def test_complete_registered_manifest_skips_the_live_schema_probe() -> None:
    manifest = {
        "entries": [
            {"trimestre": f"{year}Q{quarter}"}
            for year, quarter in expected_periods()
        ],
        "expected_quarters": 57,
        "route": "mixed_bigquery_cli_ibge_ftp",
        "source": stage0.SOURCE_TABLE,
        "status": "complete",
    }

    assert registered_manifest_is_complete(manifest) is True
    manifest["entries"] = list(reversed(manifest["entries"]))
    with pytest.raises(ValueError, match="period grid"):
        registered_manifest_is_complete(manifest)


def test_bigquery_transport_uses_the_locked_python_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = pd.DataFrame({"ano": [2026], "trimestre": [1]})
    observed: dict[str, object] = {}

    class Rows:
        def to_dataframe(self, *, create_bqstorage_client: bool) -> pd.DataFrame:
            observed["storage"] = create_bqstorage_client
            return expected

    class Job:
        def result(self, *, max_results: int, timeout: int) -> Rows:
            observed["max_results"] = max_results
            observed["timeout"] = timeout
            return Rows()

    class Client:
        def query(self, query: str) -> Job:
            observed["query"] = query
            return Job()

    monkeypatch.setattr(stage0, "_bigquery_client", lambda: Client())

    result = run_bq_csv("SELECT 1", maximum_rows=5)

    pd.testing.assert_frame_equal(result, expected)
    assert observed == {
        "max_results": 5,
        "query": "SELECT 1",
        "storage": True,
        "timeout": stage0.BIGQUERY_TIMEOUT_SECONDS,
    }


def test_extract_query_uses_only_the_preregistered_columns_and_filters() -> None:
    query = build_extract_query(2025, 3)

    assert "ano = 2025" in query
    assert "trimestre = 3" in query
    assert "v4010 IS NOT NULL" in query
    assert "v2009 BETWEEN 18 AND 65" in query
    assert "vd4020" not in query
    assert "vd4035" not in query
    for column in P1_COLUMNS:
        assert column in query


def test_reference_population_query_matches_sidra_6463_universe() -> None:
    query = build_reference_population_query()

    assert "v2009 >= 14" in query
    assert "vd4002 = '1'" in query
    assert "v2009 BETWEEN 18 AND 65" in query
    assert "SUM(IF" in query
    assert "GROUP BY ano, trimestre" in query
    assert ")\n  AND v2009 BETWEEN 18 AND 65\nGROUP BY" not in query


def test_parse_sidra_6463_returns_one_row_per_quarter() -> None:
    payload = [
        {
            "V": "Valor",
            "D3C": "Trimestre (Código)",
            "D4C": "Condição (Código)",
        },
        {"V": "153031", "D3C": "201201", "D4C": "32385"},
        {"V": "87713", "D3C": "201201", "D4C": "32387"},
    ]

    result = parse_sidra_6463(payload)

    assert result.to_dict("records") == [
        {
            "ano": 2012,
            "trimestre": 1,
            "sidra_population_14plus": 153_031_000.0,
            "sidra_occupied_14plus": 87_713_000.0,
        }
    ]


def test_section3_anchor_applies_the_frozen_invalid_code_exclusions() -> None:
    frame = pd.DataFrame(
        {
            "ano": [2025, 2025, 2025],
            "trimestre": [3, 3, 3],
            "cod_ocupacao": ["1111", "0000", "9999"],
            "idade": [40, 40, 40],
            "peso": [10.25, 20.0, 30.0],
        }
    )

    result = section3_anchor(frame)

    assert result == {"rows": 1, "population": 10.25}


def test_section3_anchor_uses_the_literal_frozen_population_contract() -> None:
    frame = pd.DataFrame(
        {
            "ano": [2025],
            "trimestre": [3],
            "cod_ocupacao": ["1111"],
            "idade": [40],
            "peso": [97_783_776.18040435],
        }
    )

    result = section3_anchor(frame)

    assert SECTION3_EXPECTED_POPULATION == 97_783_776.1804
    assert result["population"] == SECTION3_EXPECTED_POPULATION
    assert abs(result["population"] - SECTION3_EXPECTED_POPULATION) <= 1e-6


def test_formal_indicator_normalizes_ftp_zero_padding() -> None:
    values = pd.Series(["01", "1", "03", "5", "09", None])

    assert formal_indicator(values).tolist() == [
        True,
        True,
        True,
        True,
        False,
        False,
    ]


def test_build_and_attach_crosswalk_assigns_gradient_only_to_exact_matches() -> None:
    ilo = pd.DataFrame(
        {
            "ISCO_08": [1111, 1111, 2222],
            "potential25": [
                "Exposed: Gradient 1",
                "Exposed: Gradient 1",
                "Not Exposed",
            ],
        }
    )
    people = pd.DataFrame(
        {
            "cod_ocupacao": ["1111", "1119", "8888", "0000"],
            "peso": [1.0, 2.0, 3.0, 4.0],
        }
    )

    result = attach_crosswalk(people, build_ilo_crosswalk(ilo))

    assert result["match_type"].tolist() == [
        "exact_4_digit",
        "fallback_3_digit",
        "unmatched",
    ]
    assert result["exposure_gradient"].tolist() == [
        "Exposed: Gradient 1",
        "Sem classificação",
        "Sem classificação",
    ]
    assert "0000" not in result["cod4"].tolist()


@pytest.mark.parametrize(
    ("treated", "control", "expected"),
    [
        (20, 50, "adequate"),
        (19, 50, "limited"),
        (10, 25, "limited"),
        (9, 25, "thin"),
        (20, 24, "thin"),
    ],
)
def test_classify_support_uses_the_frozen_cod3_thresholds(
    treated: int,
    control: int,
    expected: str,
) -> None:
    assert classify_support(treated, control) == expected


def test_derive_cod3_treatment_uses_preperiod_employment_weights() -> None:
    frame = pd.DataFrame(
        {
            "cod4": ["1111", "1112", "2221", "3331", "3332"],
            "exposure_gradient": [
                "Exposed: Gradient 1",
                "Not Exposed",
                "Not Exposed",
                "Exposed: Gradient 2",
                "Minimal Exposure",
            ],
            "peso": [50.0, 50.0, 100.0, 25.0, 75.0],
        }
    )

    result = derive_cod3_treatment(frame).set_index("cod3")

    assert result.loc["111", "exposed_employment_share"] == pytest.approx(0.5)
    assert result.loc["111", "treatment_status"] == "treated"
    assert result.loc["222", "treatment_status"] == "control"
    assert result.loc["333", "treatment_status"] == "intermediate"


@pytest.mark.parametrize(
    ("changes", "complete", "expected"),
    [
        ([0.25, -1.0], True, "non_differential"),
        ([0.25, -1.01], True, "differential"),
        ([0.25, float("nan")], True, "indeterminate"),
        ([0.25], False, "indeterminate"),
    ],
)
def test_classify_2020_break_uses_the_registered_one_point_rule(
    changes: list[float],
    complete: bool,
    expected: str,
) -> None:
    assert (
        classify_2020_break(pd.Series(changes), complete=complete)
        == expected
    )


def test_normalize_ftp_extract_maps_uf_and_applies_p1_source_filters() -> None:
    raw = pd.DataFrame(
        {
            "ano": ["2025", "2025", "2025"],
            "trimestre": ["4", "4", "4"],
            "uf_code": ["11", "11", "11"],
            "sexo": ["2", "1", "1"],
            "idade": ["65", "17", "40"],
            "raca_cor": ["4", "1", "2"],
            "nivel_instrucao": ["5", "2", "4"],
            "vd4002": ["1", "1", None],
            "cod_ocupacao": ["1111", "2222", None],
            "grupamento_atividade": ["01001", "02001", None],
            "posicao_ocupacao": ["1", "3", None],
            "rendimento_habitual": ["2000", "1000", None],
            "horas_habituais": ["40", "20", None],
            "peso": ["000349.37765480", "100.0", "50.0"],
        }
    )

    result = normalize_ftp_extract(raw, year=2025, quarter=4)

    assert len(result) == 1
    assert result.iloc[0]["sigla_uf"] == "RO"
    assert result.iloc[0]["cod_ocupacao"] == "1111"
    assert result.iloc[0]["peso"] == pytest.approx(349.3776548)


def test_select_ftp_archive_name_uses_the_published_revision_suffix() -> None:
    html = """
    <a href="PNADC_012024_20250815.zip">first quarter</a>
    <a href="PNADC_022024_20260324.zip">second quarter</a>
    """

    assert (
        select_ftp_archive_name(html, year=2024, quarter=2)
        == "PNADC_022024_20260324.zip"
    )


def test_registered_pnadc_asset_requires_exact_bytes_and_sha256(
    tmp_path: Path,
) -> None:
    source = tmp_path / "quarter.parquet"
    source.write_bytes(b"registered quarter")
    metadata = {
        "bytes": source.stat().st_size,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }

    validate_registered_asset(source, metadata, label="test quarter")
    source.write_bytes(b"changed quarter")

    with pytest.raises(ValueError, match="byte-size|SHA-256"):
        validate_registered_asset(source, metadata, label="test quarter")


def test_sidra_source_is_reused_without_network_when_registered(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "sidra_6463.json"
    records = [
        {"V": "Valor", "D3C": "Trimestre", "D4C": "Condição"},
        {"V": "100", "D3C": "202501", "D4C": "32385"},
    ]
    source.write_text(
        json.dumps(
            {
                "accessed_at": "2026-07-30T00:00:00+00:00",
                "records": records,
                "source": stage0.SIDRA_6463_URL,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(stage0, "SIDRA_VINTAGE_PATH", source)
    monkeypatch.setattr(
        stage0,
        "urlopen",
        lambda *_args, **_kwargs: pytest.fail("unexpected network call"),
    )

    payload, accessed_at = fetch_sidra_6463()

    assert payload == records
    assert accessed_at == "2026-07-30T00:00:00+00:00"


def test_validate_quarter_extract_accepts_the_frozen_contract() -> None:
    frame = valid_quarter_extract()

    metrics = validate_quarter_extract(frame, year=2012, quarter=1)

    assert metrics == {
        "year": 2012,
        "quarter": 1,
        "rows": 108_000,
        "states": 27,
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda frame: frame.iloc[:99_999], "fewer than 100,000"),
        (lambda frame: frame.loc[frame["sigla_uf"] != "UF26"], "expected 27 UFs"),
        (lambda frame: frame.assign(trimestre=2), "unexpected periods"),
    ],
)
def test_validate_quarter_extract_rejects_incomplete_vintages(
    mutation,
    message: str,
) -> None:
    frame = mutation(valid_quarter_extract())

    with pytest.raises(ValueError, match=message):
        validate_quarter_extract(frame, year=2012, quarter=1)
