from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PACKAGE_ROOT / "code" / "spatial"
FRONT_DIR = PACKAGE_ROOT / "data" / "derived" / "spatial"
RESULTS_DIR = (
    PACKAGE_ROOT / "results" / "reference" / "artifacts" / "spatial" / "backing_data"
)
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from v2_spatial.support import (  # noqa: E402
    PNAD_EXPECTED_SHA256,
    assign_municipality_median_split,
    build_digital_admission_share,
    classify_balance,
    classify_cluster_support,
    classify_coexistence,
    classify_exposed_low,
    classify_residual_variation,
    correlation_label,
    effective_cluster_count,
    evaluate_support_gate,
    family_f_declaration,
    iterative_singleton_keep,
    parse_pnad_sidra,
    residualize_fixed_effects,
)


def test_frozen_pnad_input_matches_hash_and_exact_construct() -> None:
    path = (
        FRONT_DIR
        / "vintage"
        / "pnad_continua_tic_2021_sidra_table_7334.json"
    )
    payload = path.read_bytes()

    assert hashlib.sha256(payload).hexdigest() == PNAD_EXPECTED_SHA256
    parsed = parse_pnad_sidra(json.loads(payload))

    assert len(parsed) == 27
    assert parsed["uf_code"].nunique() == 27
    assert parsed["internet_use_pct"].between(0, 100).all()
    assert parsed["year"].eq(2021).all()
    assert parsed["age_group"].eq("Total").all()


def test_parse_pnad_sidra_rejects_wrong_variable() -> None:
    payload = [
        {
            "NC": "Nível Territorial (Código)",
            "V": "Valor",
            "D1C": "Unidade da Federação (Código)",
            "D1N": "Unidade da Federação",
            "D2C": "Variável (Código)",
            "D2N": "Variável",
            "D3C": "Ano (Código)",
            "D3N": "Ano",
            "D4C": "Grupo de idade (Código)",
            "D4N": "Grupo de idade",
        },
        {
            "NC": "3",
            "V": "85.0",
            "D1C": "11",
            "D1N": "Rondônia",
            "D2C": "99999",
            "D2N": "Wrong variable",
            "D3C": "2021",
            "D3N": "2021",
            "D4C": "95253",
            "D4N": "Total",
        },
    ]

    with pytest.raises(RuntimeError, match="variable"):
        parse_pnad_sidra(payload, require_27_ufs=False)


def test_proxy2_uses_signed_preperiod_admissions_in_cnae_58_to_63() -> None:
    records = pd.DataFrame(
        {
            "id_municipio": ["1", "1", "1", "1", "2"],
            "periodo_num": [202101, 202102, 202103, 202212, 202101],
            "saldomovimentacao": [1, 1, -1, 1, 1],
            "peso": [1, -1, 1, 1, 2],
            "cnae_division": ["62", "62", "62", "62", "10"],
        }
    )

    result = build_digital_admission_share(records)

    municipality_1 = result.set_index("id_municipio").loc["1"]
    municipality_2 = result.set_index("id_municipio").loc["2"]
    assert municipality_1["signed_admissions"] == 0
    assert municipality_1["signed_digital_admissions"] == 0
    assert np.isnan(municipality_1["digital_admission_share"])
    assert municipality_2["signed_admissions"] == 2
    assert municipality_2["signed_digital_admissions"] == 0
    assert municipality_2["digital_admission_share"] == 0


def test_municipality_median_split_is_weighted_by_sample_municipalities() -> None:
    municipalities = pd.DataFrame(
        {
            "id_municipio": ["a", "b", "c", "d", "e"],
            "value": [10.0, 10.0, 10.0, 20.0, 30.0],
            "uf_code": ["11", "11", "11", "12", "13"],
        }
    )

    split, support = assign_municipality_median_split(
        municipalities,
        value_column="value",
        high_column="high",
    )

    assert support["threshold"] == 10.0
    assert split.set_index("id_municipio")["high"].to_dict() == {
        "a": 0,
        "b": 0,
        "c": 0,
        "d": 1,
        "e": 1,
    }


def test_multiway_residualization_is_orthogonal_to_each_fixed_effect() -> None:
    frame = pd.DataFrame(
        {
            "fe_a": ["a", "a", "a", "a", "b", "b", "b", "b"],
            "fe_b": ["x", "x", "y", "y", "x", "x", "y", "y"],
            "fe_c": ["p", "q", "p", "q", "p", "q", "p", "q"],
        }
    )
    values = np.array([0.0, 2.0, 1.0, 3.0, 4.0, 6.0, 5.0, 8.0])

    residual, diagnostics = residualize_fixed_effects(
        values,
        frame,
        ["fe_a", "fe_b", "fe_c"],
    )

    assert diagnostics["converged"] is True
    for column in ["fe_a", "fe_b", "fe_c"]:
        grouped = pd.Series(residual).groupby(frame[column]).mean()
        assert np.abs(grouped.to_numpy()).max() < 1e-10


def test_iterative_singleton_removal_handles_cascades() -> None:
    frame = pd.DataFrame(
        {
            "fe_a": ["a", "a", "b"],
            "fe_b": ["x", "y", "y"],
        }
    )

    keep, diagnostics = iterative_singleton_keep(frame, ["fe_a", "fe_b"])

    assert keep.tolist() == [False, False, False]
    assert diagnostics["removed_rows"] == 3
    assert diagnostics["rounds"] >= 2


def test_effective_cluster_count_uses_squared_residual_mass() -> None:
    residual = np.array([1.0, 1.0, 1.0, 1.0])
    clusters = pd.Series(["a", "a", "b", "c"])

    result = effective_cluster_count(residual, clusters)

    assert result == pytest.approx(1 / (0.5**2 + 0.25**2 + 0.25**2))


@pytest.mark.parametrize(
    ("retained", "residual_sd", "expected"),
    [(0.10, 0.1, "adequate"), (0.01, 0.1, "limited"), (0.009, 0.1, "thin")],
)
def test_residual_support_thresholds(
    retained: float,
    residual_sd: float,
    expected: str,
) -> None:
    assert (
        classify_residual_variation(retained, residual_sd) == expected
    )


def test_support_classifiers_follow_declared_thresholds() -> None:
    assert classify_coexistence(0.80, 0.80) == "adequate"
    assert classify_coexistence(0.50, 0.50) == "limited"
    assert classify_coexistence(0.49, 0.90) == "thin"
    assert classify_exposed_low(20, 50, 20, 50) == "adequate"
    assert classify_exposed_low(10, 25, 10, 25) == "limited"
    assert classify_exposed_low(9, 100, 20, 100) == "thin"
    assert classify_cluster_support(50, 20) == "adequate"
    assert classify_cluster_support(25, 10) == "limited"
    assert classify_cluster_support(24.9, 27) == "thin"
    assert classify_balance(0.05, 0.80) == "adequate"
    assert classify_balance(0.10, 0.50) == "limited"
    assert classify_balance(0.101, 0.90) == "thin"
    assert correlation_label(0.95) == "near_collinear"
    assert correlation_label(-0.10) == "near_orthogonal"
    assert correlation_label(0.50) == "intermediate"


def test_family_f_is_declared_without_results() -> None:
    family = family_f_declaration()

    assert len(family) == 12
    assert set(family["outcome"]) == {
        "ln_admissoes",
        "ln_desligamentos",
        "ln_salario_real_adm",
        "asinh_saldo",
    }
    assert family["proxy"].nunique() == 3
    assert family["p_value"].isna().all()
    assert family["coefficient"].isna().all()


def test_support_gate_opens_only_when_all_required_items_pass() -> None:
    passing = {
        "pnad_frozen": True,
        "residual_statuses": ["adequate", "limited", "adequate"],
        "cluster_statuses": ["adequate", "limited", "adequate"],
        "coexistence_status": "limited",
        "cell_statuses": ["adequate", "limited", "adequate"],
        "all_cells_nonempty": True,
        "pnad_distinct_status": "adequate",
        "balance_status": "adequate",
        "family_slots": 12,
        "family_p_values_present": 0,
        "family_coefficients_present": 0,
    }

    opened = evaluate_support_gate(passing)
    assert opened["opens"] is True

    failing = dict(passing)
    failing["cluster_statuses"] = ["adequate", "thin", "adequate"]
    closed = evaluate_support_gate(failing)
    assert closed["opens"] is False
    assert "cluster_support" in closed["failed_criteria"]


def test_generated_a6_artifacts_close_only_on_cluster_support() -> None:
    results = RESULTS_DIR
    status = json.loads(
        (results / "anatel_a6_status.json").read_text(encoding="utf-8")
    )
    residual = pd.read_csv(results / "anatel_a6_residual_variation.csv")
    clusters = pd.read_csv(results / "anatel_a6_cluster_structure.csv")
    family = pd.read_csv(results / "family_f_declaration.csv")

    assert status["gate"]["opens"] is False
    assert status["gate"]["failed_criteria"] == ["cluster_support"]
    assert status["a7_executed"] is False
    assert status["outcome_model_estimated"] is False
    assert status["real_treatment_coefficient_estimated"] is False
    assert residual["outcome_model_estimated"].eq(False).all()
    assert residual["treatment_coefficient_estimated"].eq(False).all()
    assert residual["classification"].eq("adequate").all()

    proxy2 = clusters.set_index("proxy").loc[
        "digital_intensive_admission_share"
    ]
    assert proxy2["effective_uf_clusters"] < 10
    assert proxy2["classification"] == "thin"
    assert len(family) == 12
    assert family["coefficient"].isna().all()
    assert family["p_value"].isna().all()
    assert family["bh_adjusted_p_value"].isna().all()
