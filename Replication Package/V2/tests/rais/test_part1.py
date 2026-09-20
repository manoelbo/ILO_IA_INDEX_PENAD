from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from v2_rais.part1 import (
    V2_ROOT,
    aggregate_caged_flows,
    build_rotation_panel,
    build_support_table,
    classify_support,
    prepare_rais_panel,
)


def _classification() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cbo_4d": ["1111", "2222", "3333", "4444"],
            "cbo_ilo_gradient": [
                "Exposed: Gradient 1",
                "Not Exposed",
                "Minimal Exposure",
                "Exposed: Gradient 2",
            ],
        }
    )


def test_prepare_rais_panel_applies_the_derived_window_and_treatment_contract() -> None:
    rais = pd.DataFrame(
        {
            "ano": [2018, 2019, 2019, 2023, 2023],
            "cbo_4d": ["1111", "1111", "2222", "1111", "3333"],
            "vinculos_declarados": [12, 13, 20, 14, 9],
            "estoque_3112": [10, 11, 18, 12, 8],
            "tempo_emprego_medio": [20.0, 21.0, 30.0, 22.0, 15.0],
        }
    )

    panel, support = prepare_rais_panel(
        rais,
        _classification(),
        window_start=2019,
        window_end=2024,
    )

    assert panel[["cbo_4d", "ano"]].to_records(index=False).tolist() == [
        ("1111", 2019),
        ("1111", 2023),
        ("2222", 2019),
    ]
    assert panel["treated_main"].tolist() == [1.0, 1.0, 0.0]
    assert panel["post"].tolist() == [0, 1, 0]
    assert panel["post_treat"].tolist() == [0.0, 1.0, 0.0]
    assert panel["dummy_2020"].tolist() == [0, 0, 0]
    assert panel["ln_tempo_emprego_medio"].iloc[0] == pytest.approx(
        np.log(21.0)
    )
    assert support["contract_cbo"] == 3
    assert support["absent_contract_cbo"] == ["4444"]


def test_prepare_rais_panel_rejects_duplicate_cbo_year_keys() -> None:
    duplicate = pd.DataFrame(
        {
            "ano": [2019, 2019],
            "cbo_4d": ["1111", "1111"],
            "vinculos_declarados": [12, 12],
            "estoque_3112": [10, 10],
            "tempo_emprego_medio": [20.0, 20.0],
        }
    )

    with pytest.raises(RuntimeError, match="duplicate"):
        prepare_rais_panel(duplicate, _classification())


def test_build_rotation_panel_reports_missing_bases_and_never_imputes_zero_stock() -> None:
    monthly = pd.DataFrame(
        {
            "cbo_4d": ["1111", "1111", "2222", "2222", "4444"],
            "ano": [2021, 2021, 2021, 2022, 2021],
            "mes": [1, 2, 1, 1, 1],
            "admissoes": [2, 3, 5, 7, 11],
            "desligamentos": [1, 4, 2, 3, 5],
            "included_main": [True, True, True, True, True],
        }
    )
    rais_panel = pd.DataFrame(
        {
            "cbo_4d": ["1111", "2222", "2222", "3333"],
            "ano": [2021, 2021, 2022, 2021],
            "estoque_3112": [10, 0, 20, 30],
            "treated_main": [1.0, 0.0, 0.0, 1.0],
            "included_main": [True, True, True, True],
            "post": [0, 0, 0, 0],
            "post_treat": [0.0, 0.0, 0.0, 0.0],
            "dummy_2020": [0, 0, 0, 0],
        }
    )

    panel, support = build_rotation_panel(monthly, rais_panel)

    zero_stock = panel.loc[
        (panel["cbo_4d"] == "2222") & (panel["ano"] == 2021)
    ].iloc[0]
    assert pd.isna(zero_stock["taxa_rotatividade"])
    assert pd.isna(zero_stock["ln_taxa_rotatividade"])
    assert support["cells_missing_rais"] == 1
    assert support["cells_missing_caged"] == 1
    assert support["cells_zero_stock"] == 1
    assert support["zero_stock_cells_with_numeric_rate"] == 0


def test_aggregate_caged_flows_matches_the_real_monthly_v2_total_for_2022() -> None:
    monthly = pd.read_parquet(
        V2_ROOT / "data" / "derived" / "painel_nacional.parquet"
    )

    annual = aggregate_caged_flows(monthly)
    observed = annual.loc[
        annual["ano"].eq(2022), ["admissoes", "desligamentos"]
    ].sum()
    expected = monthly.loc[
        monthly["included_main"] & monthly["ano"].eq(2022),
        ["admissoes", "desligamentos"],
    ].sum()

    pd.testing.assert_series_equal(observed, expected)


@pytest.mark.parametrize(
    ("treated", "control", "expected"),
    [
        (20, 50, "adequate"),
        (10, 25, "limited"),
        (9, 80, "thin"),
        (30, 24, "thin"),
    ],
)
def test_classify_support_uses_the_frozen_thresholds(
    treated: int,
    control: int,
    expected: str,
) -> None:
    assert classify_support(treated, control) == expected


def test_build_support_table_counts_nonmissing_outcomes_by_group_and_year() -> None:
    annual = pd.DataFrame(
        {
            "cbo_4d": ["1111", "2222", "1111", "2222"],
            "ano": [2019, 2019, 2020, 2020],
            "treated_main": [1.0, 0.0, 1.0, 0.0],
            "estoque_3112": [10, 20, 11, 21],
            "ln_tempo_emprego_medio": [2.0, 3.0, np.nan, 3.1],
        }
    )
    rotation = pd.DataFrame(
        {
            "cbo_4d": ["1111", "2222"],
            "ano": [2021, 2021],
            "treated_main": [1.0, 0.0],
            "ln_taxa_rotatividade": [0.2, np.nan],
        }
    )

    support = build_support_table(annual, rotation)

    tempo_2020 = support.loc[
        support["outcome"].eq("ln_tempo_emprego_medio")
        & support["ano"].eq(2020)
    ].iloc[0]
    rotation_2021 = support.loc[
        support["outcome"].eq("ln_taxa_rotatividade")
        & support["ano"].eq(2021)
    ].iloc[0]
    assert tempo_2020["treated_cbo"] == 0
    assert tempo_2020["control_cbo"] == 1
    assert rotation_2021["treated_cbo"] == 1
    assert rotation_2021["control_cbo"] == 0
    assert set(support["support_status"]) == {"thin"}
