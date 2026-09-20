from __future__ import annotations

import sys
import json
from pathlib import Path

import numpy as np
import pytest

import v2_rais.stage0 as stage0

sys.path.insert(0, str(Path(__file__).resolve().parent))

from v2_rais.stage0 import (
    REQUIRED_SCHEMA,
    _render_esocial_break_report,
    build_reconciliation_rows,
    classify_break_differential,
    choose_acquisition_route,
    derive_stage0_scorecard,
    fit_segmented_break,
    is_transition_gap_dominant,
    sha256_file,
    run_acquire,
    run_probe,
    run_reconciliation_source,
    validate_aggregate_rows,
    validate_active_domain,
    validate_schema,
    validate_year_coverage,
)


def _write_registered_extract(
    data_path: Path,
    manifest_path: Path,
    content: str,
    *,
    query: str,
) -> None:
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(content, encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "bytes": data_path.stat().st_size,
                "consulta": query,
                "linhas": len(content.strip().splitlines()) - 1,
                "sha256": sha256_file(data_path),
                "tabela": stage0.SOURCE_TABLE,
            }
        ),
        encoding="utf-8",
    )


def test_validate_schema_accepts_the_required_columns_and_types() -> None:
    observed = {
        "ano": "INT64",
        "cbo_2002": "STRING",
        "id_municipio": "STRING",
        "tempo_emprego": "FLOAT64",
        "vinculo_ativo_3112": "STRING",
    }

    validate_schema(observed)

    assert observed == REQUIRED_SCHEMA


def test_validate_schema_rejects_a_missing_required_column() -> None:
    observed = {
        "ano": "INT64",
        "cbo_2002": "STRING",
        "tempo_emprego": "FLOAT64",
        "vinculo_ativo_3112": "STRING",
    }

    with pytest.raises(ValueError, match="id_municipio"):
        validate_schema(observed)


def test_validate_year_coverage_requires_every_probe_year() -> None:
    complete = list(range(2015, 2026))

    assert validate_year_coverage(complete) == complete

    with pytest.raises(ValueError, match="2020"):
        validate_year_coverage([year for year in complete if year != 2020])


def test_choose_acquisition_route_uses_bigquery_when_2024_is_available() -> None:
    assert choose_acquisition_route(2025) == "basedosdados_bigquery"


def test_choose_acquisition_route_requires_fallback_below_2024() -> None:
    assert choose_acquisition_route(2023) == "mte_ftp_required"


def test_validate_active_domain_accepts_only_string_zero_one_in_every_year() -> None:
    rows = [
        {"ano": str(year), "valor": value, "vinculos": "1"}
        for year in range(2016, 2025)
        for value in ("0", "1")
    ]

    validate_active_domain(rows)


def test_validate_active_domain_rejects_an_unexpected_value() -> None:
    rows = [
        {"ano": str(year), "valor": value, "vinculos": "1"}
        for year in range(2016, 2025)
        for value in ("0", "1")
    ]
    rows.append({"ano": "2024", "valor": "true", "vinculos": "1"})

    with pytest.raises(ValueError, match="true"):
        validate_active_domain(rows)


def _valid_aggregate_rows() -> list[dict[str, str]]:
    return [
        {
            "ano": str(year),
            "cbo_4d": "2521",
            "vinculos_declarados": "10",
            "estoque_3112": "8",
            "tempo_emprego_medio": "42.5",
        }
        for year in range(2016, 2025)
    ]


def test_validate_aggregate_rows_accepts_a_unique_nine_year_panel() -> None:
    summary = validate_aggregate_rows(_valid_aggregate_rows())

    assert summary == {"rows": 9, "years": list(range(2016, 2025))}


def test_validate_aggregate_rows_rejects_duplicate_keys() -> None:
    rows = _valid_aggregate_rows()
    rows.append(dict(rows[0]))

    with pytest.raises(ValueError, match="Duplicate"):
        validate_aggregate_rows(rows)


def test_validate_aggregate_rows_rejects_invalid_cbo_and_stock_above_total() -> None:
    rows = _valid_aggregate_rows()
    rows[0]["cbo_4d"] = "0000"
    rows[1]["estoque_3112"] = "11"

    with pytest.raises(ValueError, match="Invalid CBO4"):
        validate_aggregate_rows(rows)


def test_run_acquire_reuses_a_valid_registered_extract_without_querying(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        "ano,cbo_4d,vinculos_declarados,estoque_3112,tempo_emprego_medio\n"
        + "".join(
            f"{year},2521,10,8,42.5\n" for year in range(2016, 2025)
        )
    )
    _write_registered_extract(
        tmp_path / "rais_cbo4_ano_2016_2024.csv",
        tmp_path / "manifest.json",
        content,
        query=stage0.AGGREGATE_QUERY,
    )
    monkeypatch.setattr(stage0, "VINTAGE_DIR", tmp_path)
    monkeypatch.setattr(
        stage0,
        "_run_bq_csv",
        lambda *_args, **_kwargs: pytest.fail("unexpected BigQuery call"),
    )

    manifest = run_acquire()

    assert manifest["sha256"] == sha256_file(
        tmp_path / "rais_cbo4_ano_2016_2024.csv"
    )


def test_run_probe_validates_a_registered_extract_without_live_queries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vintage = tmp_path / "vintage"
    content = (
        "ano,cbo_4d,vinculos_declarados,estoque_3112,tempo_emprego_medio\n"
        + "".join(
            f"{year},2521,10,8,42.5\n" for year in range(2016, 2025)
        )
    )
    _write_registered_extract(
        vintage / "rais_cbo4_ano_2016_2024.csv",
        vintage / "manifest.json",
        content,
        query=stage0.AGGREGATE_QUERY,
    )
    monkeypatch.setattr(stage0, "VINTAGE_DIR", vintage)
    monkeypatch.setattr(stage0, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(
        stage0,
        "_run_bq_csv",
        lambda *_args, **_kwargs: pytest.fail("unexpected BigQuery call"),
    )

    status = run_probe()

    assert status["status"] == "ok"
    assert status["max_year"] == 2024
    assert status["probe_executed"] is False


def test_run_reconciliation_source_reuses_a_valid_registered_extract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        "ano,ativos_total_fonte,ativos_sem_cbo,ativos_abandonados,"
        "ativos_abandonados_com_cbo\n"
        + "".join(f"{year},10,0,0,0\n" for year in range(2016, 2025))
    )
    _write_registered_extract(
        tmp_path / "rais_reconciliation_components_2016_2024.csv",
        tmp_path / "rais_reconciliation_components_manifest.json",
        content,
        query=stage0.RECONCILIATION_COMPONENTS_QUERY,
    )
    monkeypatch.setattr(stage0, "VINTAGE_DIR", tmp_path)
    monkeypatch.setattr(
        stage0,
        "_run_bq_csv",
        lambda *_args, **_kwargs: pytest.fail("unexpected BigQuery call"),
    )

    manifest = run_reconciliation_source()

    assert manifest["linhas"] == 9


def test_run_acquire_rejects_a_changed_registered_extract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        "ano,cbo_4d,vinculos_declarados,estoque_3112,tempo_emprego_medio\n"
        + "".join(
            f"{year},2521,10,8,42.5\n" for year in range(2016, 2025)
        )
    )
    data_path = tmp_path / "rais_cbo4_ano_2016_2024.csv"
    _write_registered_extract(
        data_path,
        tmp_path / "manifest.json",
        content,
        query=stage0.AGGREGATE_QUERY,
    )
    data_path.write_text(content.replace("42.5", "42.6"), encoding="utf-8")
    monkeypatch.setattr(stage0, "VINTAGE_DIR", tmp_path)

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        run_acquire()


def test_sha256_file_hashes_the_exact_frozen_bytes(tmp_path: Path) -> None:
    source = tmp_path / "vintage.csv"
    source.write_bytes(b"ano,cbo_4d\n2024,2521\n")

    assert (
        sha256_file(source)
        == "0f4b9c1239cf682db28394d1e23a26d21246b9e2f6fbe7629607380bf7eeafd5"
    )


def test_build_reconciliation_rows_explains_missing_cbo_and_abandoned_links() -> None:
    aggregate_rows = [
        {"ano": "2022", "estoque_3112": "90"},
        {"ano": "2023", "estoque_3112": "120"},
    ]
    components = [
        {
            "ano": "2022",
            "ativos_total_fonte": "100",
            "ativos_sem_cbo": "10",
            "ativos_abandonados": "0",
            "ativos_abandonados_com_cbo": "0",
        },
        {
            "ano": "2023",
            "ativos_total_fonte": "120",
            "ativos_sem_cbo": "0",
            "ativos_abandonados": "10",
            "ativos_abandonados_com_cbo": "10",
        },
    ]
    official = {2022: 100, 2023: 110}
    sources = {2022: "mte-2022", 2023: "mte-2023"}

    result = build_reconciliation_rows(
        aggregate_rows,
        components,
        official,
        sources,
    )

    assert result[0]["diferenca_absoluta"] == -10
    assert result[0]["explanation_code"] == "active_links_missing_cbo"
    assert result[1]["diferenca_absoluta"] == 10
    assert result[1]["explanation_code"] == "active_links_marked_abandoned"


def test_fit_segmented_break_recovers_level_and_trend_changes() -> None:
    years = np.arange(2016, 2025)
    time = years - 2016
    step = (years >= 2022).astype(float)
    post_transition_time = np.maximum(years - 2022, 0)
    log_stock = (
        10.0
        + 0.02 * time
        + 0.08 * step
        - 0.01 * post_transition_time
    )

    result = fit_segmented_break(
        years,
        np.exp(log_stock),
        transition_year=2022,
    )

    assert result["identified"] is True
    assert result["level_break"] == pytest.approx(0.08)
    assert result["trend_break"] == pytest.approx(-0.01)


def test_classify_break_differential_uses_the_frozen_one_pp_threshold() -> None:
    assert classify_break_differential(0.0101, 0.0) == "differential"
    assert classify_break_differential(0.01, -0.01) == "non_differential"
    assert classify_break_differential(float("nan"), 0.0) == "indeterminate"


def test_is_transition_gap_dominant_requires_the_largest_gap_above_one_pp() -> None:
    gaps = {2020: -2.0, 2021: 0.2, 2022: -3.0, 2023: -0.5}

    assert is_transition_gap_dominant(gaps, 2022)
    assert not is_transition_gap_dominant(gaps, 2021)


def test_esocial_break_report_states_log_point_threshold_units_correctly() -> None:
    annual_rows = [
        {
            "janela_inicio": 2016,
            "ano": 2016,
            "estoque_tratadas": 100,
            "estoque_controle": 200,
            "crescimento_tratadas": "",
            "crescimento_controle": "",
            "diferenca_crescimento_pp": "",
        },
        {
            "janela_inicio": 2016,
            "ano": 2022,
            "estoque_tratadas": 110,
            "estoque_controle": 220,
            "crescimento_tratadas": "0.05",
            "crescimento_controle": "0.08",
            "diferenca_crescimento_pp": "-3.0",
        },
    ]
    diagnostics = {
        2016: {
            "treated_level_break": 0.08,
            "control_level_break": 0.11,
            "level_difference": -0.03,
            "treated_trend_break": 0.02,
            "control_trend_break": 0.03,
            "trend_difference": -0.01,
            "classification": "differential",
        },
        2019: {
            "treated_level_break": 0.06,
            "control_level_break": 0.07,
            "level_difference": -0.01,
            "treated_trend_break": 0.01,
            "control_trend_break": 0.01,
            "trend_difference": 0.0,
            "classification": "non_differential",
        },
    }

    report = _render_esocial_break_report(
        annual_rows,
        diagnostics,
        dominant=True,
        derived_window_start=2019,
    )

    assert "0.01-log-point threshold" in report
    assert "one-log-point threshold" not in report


def test_derive_stage0_scorecard_opens_rais_after_both_gates_pass() -> None:
    row = derive_stage0_scorecard(
        acquisition_pass=True,
        reconciliation_pass=True,
        break_measured=True,
    )

    assert row["momento"] == "stage0"
    assert row["gate_aquisicao"] == "pass"
    assert row["gate_construcao"] == "pass"
    assert row["veredito"] == "corpo"
    assert "gate_aquisicao" in row["veredito_derivado_de"]
