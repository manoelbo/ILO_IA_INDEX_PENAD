from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from v2_pnadc.panels import (  # noqa: E402
    _promote_validated_parquet,
    build_cod3_panel,
    build_individual_quarter,
    quarter_number,
    validate_cod3_panel,
    validate_individual_chunk,
)
from v2_pnadc.stage0 import build_ilo_crosswalk  # noqa: E402


def raw_individual_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ano": [2023] * 5,
            "trimestre": [1] * 5,
            "sigla_uf": ["SP"] * 5,
            "sexo": ["1", "2", "1", "2", "1"],
            "idade": [30, 40, 50, 60, 35],
            "raca_cor": ["1", "2", "3", "4", "1"],
            "nivel_instrucao": ["5", "6", "7", "4", "5"],
            "cod_ocupacao": ["1111", "2222", "3333", "1119", "0000"],
            "grupamento_atividade": ["01001"] * 5,
            "posicao_ocupacao": ["01", "09", "03", "09", "01"],
            "rendimento_habitual": [100.0, 0.0, 300.0, 400.0, 500.0],
            "horas_habituais": [40.0] * 5,
            "peso": [10.0, 20.0, 30.0, 40.0, 50.0],
        }
    )


def ilo_crosswalk() -> pd.DataFrame:
    return build_ilo_crosswalk(
        pd.DataFrame(
            {
                "ISCO_08": [1111, 2222, 3333],
                "potential25": [
                    "Exposed: Gradient 1",
                    "Not Exposed",
                    "Minimal Exposure",
                ],
            }
        )
    )


def test_quarter_number_uses_the_preregistered_2012q1_origin() -> None:
    assert quarter_number(2012, 1) == 1
    assert quarter_number(2022, 4) == 44
    assert quarter_number(2023, 1) == 45
    assert quarter_number(2026, 1) == 57


def test_build_individual_quarter_keeps_only_exact_exposed_and_control() -> None:
    panel, diagnostics = build_individual_quarter(
        raw_individual_rows(),
        ilo_crosswalk(),
    )

    assert len(panel) == 2
    assert panel["cod3"].tolist() == ["111", "222"]
    assert panel["treated"].tolist() == [1, 0]
    assert panel["post"].tolist() == [1, 1]
    assert panel["post_treat"].tolist() == [1, 0]
    assert panel["formal"].tolist() == [1, 0]
    assert panel["informal"].tolist() == [0, 1]
    assert panel["conta_propria"].tolist() == [0, 1]
    assert panel.loc[0, "ln_renda"] == pytest.approx(np.log(100.0))
    assert pd.isna(panel.loc[1, "ln_renda"])
    assert not {"cod4", "cod_ocupacao"} & set(panel.columns)
    assert diagnostics["input_rows"] == 5
    assert diagnostics["panel_rows"] == 2
    assert diagnostics["excluded_minimal_exposure_rows"] == 1
    assert diagnostics["excluded_sem_classificacao_rows"] == 1


def test_transition_quarter_requires_explicit_pre_assignment() -> None:
    raw = raw_individual_rows().assign(ano=2022, trimestre=4)

    with pytest.raises(ValueError, match="must be excluded"):
        build_individual_quarter(raw, ilo_crosswalk())

    panel, _ = build_individual_quarter(
        raw,
        ilo_crosswalk(),
        include_transition_as_pre=True,
    )

    assert panel["periodo"].eq("2022Q4").all()
    assert panel["trimestre_num"].eq(44).all()
    assert panel["post"].eq(0).all()
    assert panel["post_treat"].eq(0).all()
    assert not {"cod4", "cod_ocupacao"} & set(panel.columns)

    treatment = pd.DataFrame(
        {
            "cod3": ["111", "222"],
            "treatment_status": ["treated", "control"],
            "treated_cod3": [1.0, 0.0],
        }
    )
    stock = build_cod3_panel(
        panel,
        treatment,
        include_transition_as_pre=True,
    )
    assert stock["trimestre_num"].eq(44).all()
    assert stock["post"].eq(0).all()


def test_individual_chunk_validation_rejects_cod4_and_complement_errors() -> None:
    panel, _ = build_individual_quarter(
        raw_individual_rows(),
        ilo_crosswalk(),
    )
    invalid = panel.assign(cod4="1111")

    with pytest.raises(ValueError, match="COD4"):
        validate_individual_chunk(invalid)

    invalid = panel.copy()
    invalid.loc[0, "informal"] = 1
    with pytest.raises(ValueError, match="exact complements"):
        validate_individual_chunk(invalid)


def test_build_cod3_panel_aggregates_weights_and_excludes_intermediate() -> None:
    individual = pd.DataFrame(
        {
            "ano": [2023, 2023, 2023, 2023],
            "trimestre": [1, 1, 1, 1],
            "periodo": ["2023Q1"] * 4,
            "trimestre_num": [45] * 4,
            "cod3": ["111", "111", "222", "333"],
            "peso": [10.0, 20.0, 30.0, 40.0],
            "formal": [1, 0, 1, 0],
            "informal": [0, 1, 0, 1],
        }
    )
    treatment = pd.DataFrame(
        {
            "cod3": ["111", "222", "333"],
            "treatment_status": ["treated", "control", "intermediate"],
            "treated_cod3": [1.0, 0.0, np.nan],
        }
    )

    panel = build_cod3_panel(individual, treatment)

    assert panel["cod3"].tolist() == ["111", "222"]
    treated = panel.set_index("cod3").loc["111"]
    assert treated["ocupados_total"] == pytest.approx(30.0)
    assert treated["ocupados_formais"] == pytest.approx(10.0)
    assert treated["ocupados_informais"] == pytest.approx(20.0)
    assert treated["treated"] == 1
    assert treated["post_treat"] == 1
    assert not {"cod4", "cod_ocupacao"} & set(panel.columns)


def test_cod3_panel_validation_rejects_duplicate_cells() -> None:
    individual = pd.DataFrame(
        {
            "ano": [2023, 2023],
            "trimestre": [1, 1],
            "periodo": ["2023Q1", "2023Q1"],
            "trimestre_num": [45, 45],
            "cod3": ["111", "222"],
            "peso": [10.0, 20.0],
            "formal": [1, 0],
            "informal": [0, 1],
        }
    )
    treatment = pd.DataFrame(
        {
            "cod3": ["111", "222"],
            "treatment_status": ["treated", "control"],
            "treated_cod3": [1.0, 0.0],
        }
    )
    panel = build_cod3_panel(individual, treatment)
    duplicated = pd.concat([panel, panel.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate"):
        validate_cod3_panel(duplicated)


def test_build_cod3_panel_rejects_missing_treatment_classification() -> None:
    individual = pd.DataFrame(
        {
            "ano": [2023, 2023],
            "trimestre": [1, 1],
            "periodo": ["2023Q1", "2023Q1"],
            "trimestre_num": [45, 45],
            "cod3": ["111", "222"],
            "peso": [10.0, 20.0],
            "formal": [1, 0],
            "informal": [0, 1],
        }
    )
    incomplete_treatment = pd.DataFrame(
        {
            "cod3": ["111"],
            "treatment_status": ["treated"],
            "treated_cod3": [1.0],
        }
    )

    with pytest.raises(ValueError, match="missing treatment"):
        build_cod3_panel(individual, incomplete_treatment)


def test_build_cod3_panel_rejects_inconsistent_treatment_encoding() -> None:
    individual = pd.DataFrame(
        {
            "ano": [2023],
            "trimestre": [1],
            "periodo": ["2023Q1"],
            "trimestre_num": [45],
            "cod3": ["111"],
            "peso": [10.0],
            "formal": [1],
            "informal": [0],
        }
    )
    inconsistent_treatment = pd.DataFrame(
        {
            "cod3": ["111"],
            "treatment_status": ["treated"],
            "treated_cod3": [0.0],
        }
    )

    with pytest.raises(ValueError, match="inconsistent"):
        build_cod3_panel(individual, inconsistent_treatment)


def test_parquet_promotion_rejects_cod4_before_replacing(
    tmp_path: Path,
) -> None:
    final_path = tmp_path / "panel.parquet"
    partial_path = tmp_path / "panel.parquet.partial"
    pd.DataFrame({"cod3": ["111"]}).to_parquet(final_path, index=False)
    original = final_path.read_bytes()
    pd.DataFrame(
        {"cod3": ["111"], "cod4": ["1111"]}
    ).to_parquet(partial_path, index=False)

    with pytest.raises(RuntimeError, match="COD4"):
        _promote_validated_parquet(
            partial_path,
            final_path,
            expected_rows=1,
        )

    assert final_path.read_bytes() == original
    assert not partial_path.exists()
