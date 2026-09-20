from __future__ import annotations

import io
import hashlib
import sys
import zipfile
from pathlib import Path

import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PACKAGE_ROOT / "code" / "spatial"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import v2_spatial.vintage as spatial_vintage  # noqa: E402
from v2_spatial.late_declarations import (  # noqa: E402
    _aggregate_from_parquet,
    aggregate_late_declarations,
    validate_national_benchmarks,
)
from v2_spatial.vintage import (  # noqa: E402
    RangeZipReader,
    build_pre_treatment_connectivity,
    normalize_geographic_level,
    validate_csv_header,
    validate_existing_vintage,
)
from v2_spatial.panel import (  # noqa: E402
    assign_connectivity_split,
    filter_estimation_sample,
    map_caged_municipalities,
    prepare_treatment_classification,
)
from v2_spatial.diagnostics import (  # noqa: E402
    attribute_stage0_causes,
    build_pretrend_formula,
    evaluate_gate_a_g1,
    prepare_placebo_sample,
)


def test_aggregate_late_declarations_uses_signed_origin_weights() -> None:
    movements = pd.DataFrame(
        {
            "municipio": ["1100015"] * 5,
            "ano": [2021] * 5,
            "origem": ["MOV", "MOV", "FOR", "EXC", "MOV"],
            "peso": [1, 1, 1, -1, -1],
            "indicadordeforadoprazo": ["0", "0", "1", "1", "1"],
        }
    )

    result = aggregate_late_declarations(movements).iloc[0]

    assert result["mov_liquido"] == 1
    assert result["for_liquido"] == 1
    assert result["exc_liquido"] == -1
    assert result["total_liquido"] == 1
    assert result["share_for"] == pytest.approx(0.5)
    assert result["share_flag"] == pytest.approx(-1.0)


def test_validate_national_benchmarks_uses_percentage_point_tolerance() -> None:
    national = pd.DataFrame(
        {
            "ano": [2021, 2024],
            "share_for": [0.08619, 0.01291],
        }
    )

    audit = validate_national_benchmarks(
        national,
        tolerance_percentage_points=0.01,
    )

    assert audit["all_within_tolerance"] is True
    assert audit["years"]["2021"]["within_tolerance"] is True
    assert audit["years"]["2024"]["within_tolerance"] is True


def test_existing_spatial_vintage_is_hash_validated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = []
    for index, name in enumerate(spatial_vintage.SELECTED_MEMBERS):
        payload = f"registered-{index}\n".encode()
        (tmp_path / name).write_bytes(payload)
        records.append(
            {
                "member": name,
                "bytes_csv": len(payload),
                "sha256_csv": hashlib.sha256(payload).hexdigest(),
            }
        )
    manifest = {
        "source": {
            "url": spatial_vintage.URL,
            "content_length": spatial_vintage.EXPECTED_CONTENT_LENGTH,
            "last_modified": spatial_vintage.EXPECTED_LAST_MODIFIED,
        },
        "members": records,
    }
    monkeypatch.setattr(spatial_vintage, "VINTAGE_DIR", tmp_path)
    monkeypatch.setattr(
        spatial_vintage,
        "_freeze_ibge_reference",
        lambda: {"status": "pass"},
    )

    assert validate_existing_vintage(manifest) is manifest
    (tmp_path / spatial_vintage.SELECTED_MEMBERS[0]).write_text(
        "tampered\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="byte count|hash changed"):
        validate_existing_vintage(manifest)


def test_a2_parquet_path_applies_exact_v2_validity_filter(
    tmp_path: Path,
) -> None:
    partition = tmp_path / "competenciamov=202101"
    partition.mkdir()
    frame = pd.DataFrame(
        {
            "municipio": ["1100015", "1100015", "1100015"],
            "cbo2002ocupacao": ["123456", "000000", "123456"],
            "idade": [30, 30, 30],
            "salario": [2000.0, 2000.0, 0.0],
            "saldomovimentacao": [1, 1, 1],
            "peso": [1, 1, 1],
            "origem": ["FOR", "MOV", "MOV"],
            "indicadordeforadoprazo": ["1", "0", "0"],
            "competenciamov": [202101, 202101, 202101],
        }
    )
    frame.to_parquet(partition / "part.parquet", index=False)

    municipal, valid_records = _aggregate_from_parquet(
        tmp_path / "competenciamov=*" / "part.parquet"
    )

    assert valid_records == 1
    assert len(municipal) == 1
    assert municipal.iloc[0]["for_liquido"] == 1
    assert municipal.iloc[0]["share_for"] == 1


def _prefixed_zip() -> tuple[bytes, dict[str, bytes]]:
    members = {
        "Acessos_Banda_Larga_Fixa_2021.csv": b"header-2021\nrow\n",
        "Acessos_Banda_Larga_Fixa_2022.csv": b"header-2022\nrow\n",
        "Densidade_Banda_Larga_Fixa.csv": b"density\nrow\n",
        "Acessos_Banda_Larga_Fixa_Total.csv": b"total\nrow\n",
        "ignored.csv": b"ignored\n",
    }
    buffer = io.BytesIO()
    buffer.write(b"variable-prefix-to-prove-offsets-are-derived")
    with zipfile.ZipFile(buffer, mode="a", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    return buffer.getvalue(), members


def test_range_zip_reader_derives_offsets_and_extracts_selected_members() -> None:
    payload, members = _prefixed_zip()
    requests: list[tuple[int, int]] = []

    def fetch_range(start: int, end: int) -> bytes:
        requests.append((start, end))
        return payload[start : end + 1]

    reader = RangeZipReader(
        content_length=len(payload),
        fetch_range=fetch_range,
    )

    inventory = reader.inventory()
    names = {entry["member"] for entry in inventory}
    assert names == set(members)
    assert min(entry["offset_local"] for entry in inventory) > 0

    selected = reader.extract("Acessos_Banda_Larga_Fixa_2022.csv")
    assert selected.csv_bytes == members["Acessos_Banda_Larga_Fixa_2022.csv"]
    assert selected.compressed_bytes
    assert requests


def test_validate_csv_header_requires_exact_order() -> None:
    expected = ["Ano", "Mês", "Meio de Acesso", "Acessos"]
    validate_csv_header(
        b"\xef\xbb\xbfAno;M\xc3\xaas;Meio de Acesso;Acessos\n",
        expected,
    )

    with pytest.raises(RuntimeError, match="header mismatch"):
        validate_csv_header(
            b"Ano;M\xc3\xaas;Tecnologia;Acessos\n",
            expected,
        )


def test_pre_treatment_connectivity_uses_official_density_and_fiber_accesses() -> None:
    access_monthly = pd.DataFrame(
        {
            "ano": [2021, 2021],
            "mes": [1, 2],
            "id_municipio": ["1100015", "1100015"],
            "total_accesses": [100, 120],
            "fiber_accesses": [40, 60],
            "fiber_technology_accesses": [30, 50],
        }
    )
    density_monthly = pd.DataFrame(
        {
            "ano": [2021, 2021],
            "mes": [1, 2],
            "id_municipio": ["1100015", "1100015"],
            "densidade_oficial": [20.0, 22.0],
        }
    )
    ibge = pd.DataFrame(
        {
            "id_municipio": ["1100015"],
            "populacao": [550],
            "domicilios": [200],
        }
    )

    result, audit = build_pre_treatment_connectivity(
        access_monthly,
        density_monthly,
        ibge,
    )

    row = result.iloc[0]
    assert row["densidade_oficial"] == pytest.approx(21.0)
    assert row["penetracao_bl"] == pytest.approx(0.21)
    assert row["pct_fibra"] == pytest.approx(100 / 220)
    assert row["pct_fiber_technology_check"] == pytest.approx(80 / 220)
    assert row["densidade_censo_domicilios"] == pytest.approx(55.0)
    assert row["populacao_por_domicilio"] == pytest.approx(2.75)
    assert audit["pct_fibra_identically_zero"] is False


def test_density_level_normalization_accepts_source_without_accent() -> None:
    assert normalize_geographic_level("Municipio") == "municipio"
    assert normalize_geographic_level("Município") == "municipio"
    assert normalize_geographic_level("  MUNICÍPIO  ") == "municipio"


def test_assign_connectivity_split_uses_unique_surviving_municipalities() -> None:
    panel = pd.DataFrame(
        {
            "id_municipio": [
                "1100015",
                "1100015",
                "1100023",
                "1100023",
                "1100031",
            ],
            "penetracao_bl": [0.2, 0.2, 0.5, 0.5, 0.8],
        }
    )

    result, support = assign_connectivity_split(panel)

    assert support["threshold"] == pytest.approx(0.5)
    assert support["municipalities_total"] == 3
    assert support["municipalities_low"] == 2
    assert support["municipalities_high"] == 1
    assert support["low_share"] == pytest.approx(2 / 3)
    assert set(
        result.loc[result["high_connectivity"].eq(1), "id_municipio"]
    ) == {"1100031"}


def test_map_caged_municipalities_uses_ibge_prefix_without_padding() -> None:
    panel = pd.DataFrame(
        {
            "municipio_caged_6d": ["110001", "110002", "999999"],
            "value": [1, 2, 3],
        }
    )
    connectivity = pd.DataFrame(
        {
            "id_municipio": ["1100015", "1100023"],
            "penetracao_bl": [0.2, 0.4],
        }
    )

    mapped, support = map_caged_municipalities(panel, connectivity)

    assert mapped["id_municipio"].tolist() == ["1100015", "1100023"]
    assert support["input_rows"] == 3
    assert support["matched_rows"] == 2
    assert support["unmatched_caged_codes"] == ["999999"]


def test_prepare_treatment_classification_keeps_only_signed_groups() -> None:
    classification = pd.DataFrame(
        {
            "cbo_4d": ["1111", "2222", "3333", "4444"],
            "cbo_ilo_gradient": [
                "Exposed: Gradient 1",
                "Not Exposed",
                "Minimal Exposure",
                "No score",
            ],
        }
    )

    result, support = prepare_treatment_classification(classification)

    assert result["cbo_4d"].tolist() == ["1111", "2222"]
    assert result["treated"].tolist() == [1, 0]
    assert support["included_exposed_cbo"] == 1
    assert support["included_not_exposed_cbo"] == 1
    assert support["excluded_cbo"] == 2


def test_filter_estimation_sample_applies_population_and_pre_cell_support() -> None:
    panel = pd.DataFrame(
        {
            "cbo_4d": ["1111"] * 6,
            "id_municipio": [
                "1100015",
                "1100015",
                "1100023",
                "1100023",
                "1100031",
                "1100031",
            ],
            "periodo_num": [202101, 202301] * 3,
            "populacao": [60_000, 60_000, 40_000, 40_000, 70_000, 70_000],
            "n_movimentacoes": [5, 1, 8, 1, 4, 10],
        }
    )

    result, support = filter_estimation_sample(panel)

    assert set(result["id_municipio"]) == {"1100015"}
    assert result["pre_movements_cell"].eq(5).all()
    assert support["rows_after_population"] == 4
    assert support["rows_after_pre_cell"] == 2


def test_gate_a_g1_opens_only_when_all_three_contracts_pass() -> None:
    placebo = pd.DataFrame(
        {
            "outcome": [
                "ln_admissoes",
                "ln_desligamentos",
                "ln_salario_real_adm",
                "asinh_saldo",
            ],
            "p_value": [0.06, 0.50, 0.20, 0.10],
        }
    )
    pretrends = pd.DataFrame(
        {
            "outcome": placebo["outcome"],
            "pretrend_status": ["fail", "warning", "fail", "fail"],
        }
    )

    opened = evaluate_gate_a_g1(
        placebo,
        pretrends,
        low_connectivity_share=0.50,
    )
    assert opened["opens"] is True
    assert opened["failed_criteria"] == []

    placebo.loc[0, "p_value"] = 0.049
    closed = evaluate_gate_a_g1(
        placebo,
        pretrends,
        low_connectivity_share=0.50,
    )
    assert closed["opens"] is False
    assert "placebo_all_outcomes" in closed["failed_criteria"]


def test_prepare_placebo_sample_never_uses_true_post_period() -> None:
    panel = pd.DataFrame(
        {
            "periodo_num": [202111, 202112, 202211, 202212],
            "treated": [1, 1, 1, 1],
            "high_connectivity": [1, 1, 0, 1],
        }
    )

    sample = prepare_placebo_sample(
        panel,
        high_column="high_connectivity",
    )

    assert sample["periodo_num"].max() == 202211
    assert sample["placebo_post"].tolist() == [0, 1, 1]
    assert sample["placebo_triple"].tolist() == [0, 1, 0]
    assert "post" not in sample.columns


def test_pretrend_formula_has_triple_and_identifiable_lower_dynamic_term() -> None:
    formula = build_pretrend_formula(
        "ln_admissoes",
        triple_interaction="pretrend_treated_high",
        high_interaction="pretrend_high",
    )

    assert "i(event_time, pretrend_treated_high, ref=-1)" in formula
    assert "i(event_time, pretrend_high, ref=-1)" in formula
    assert "cbo_municipio + cbo_periodo + uf_periodo" in formula
    assert "stage0_triple" not in formula


def test_cause_attribution_is_mechanical_and_frozen() -> None:
    v1 = pd.DataFrame(
        {
            "outcome": ["ln_admissoes", "ln_desligamentos"],
            "p_value": [0.0, 0.0],
        }
    )
    corrected_old_cut = pd.DataFrame(
        {
            "outcome": ["ln_admissoes", "ln_desligamentos"],
            "p_value": [0.20, 0.01],
        }
    )
    corrected_new_cut = pd.DataFrame(
        {
            "outcome": ["ln_admissoes", "ln_desligamentos"],
            "p_value": [0.30, 0.20],
        }
    )
    old_pretrends = pd.DataFrame(
        {
            "outcome": ["ln_admissoes", "ln_desligamentos"],
            "pretrend_status": ["fail", "fail"],
        }
    )
    new_pretrends = pd.DataFrame(
        {
            "outcome": ["ln_admissoes", "ln_desligamentos"],
            "pretrend_status": ["fail", "warning"],
        }
    )

    attribution = attribute_stage0_causes(
        v1_placebo=v1,
        corrected_old_cut_placebo=corrected_old_cut,
        corrected_new_cut_placebo=corrected_new_cut,
        corrected_old_cut_pretrends=old_pretrends,
        corrected_new_cut_pretrends=new_pretrends,
    )

    assert attribution["vintage_contamination_supported"] is True
    assert attribution["broken_cut_supported"] is True
    assert attribution["conclusion"] == "both"
