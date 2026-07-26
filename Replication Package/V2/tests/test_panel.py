from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "panel" / "build_panel.py"


def load_panel_module():
    spec = importlib.util.spec_from_file_location("build_panel", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load build_panel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_ipca_frame_rebases_monthly_variation() -> None:
    module = load_panel_module()
    payload = json.dumps(
        [
            {"data": "01/11/2024", "valor": "1.00"},
            {"data": "01/12/2024", "valor": "2.00"},
            {"data": "01/01/2025", "valor": "3.00"},
        ]
    ).encode()

    frame = module.build_ipca_frame(
        payload,
        expected_start="202411",
        expected_end="202501",
        base_period="202412",
    )

    assert frame["periodo_num"].tolist() == [202411, 202412, 202501]
    assert frame.loc[1, "indice"] == pytest.approx(100.0)
    assert frame.loc[0, "indice"] == pytest.approx(100 / 1.02)
    assert frame.loc[2, "indice"] == pytest.approx(103.0)


def test_national_panel_preserves_zero_flow_missingness(
    tmp_path: Path,
) -> None:
    module = load_panel_module()
    partition = tmp_path / "movements" / "competenciamov=202101"
    partition.mkdir(parents=True)
    movements = pd.DataFrame(
        [
            ["111105", 1, 1, 1000.0, 20, "3", "9", "2"],
            ["111105", 1, -1, 1000.0, 20, "3", "9", "2"],
            ["111105", -1, 1, 2000.0, 40, "1", "7", "1"],
            ["222205", 1, 1, 3000.0, 30, "3", "10", "3"],
            ["222205", -1, 1, 4000.0, 35, "1", "8", "1"],
            ["333305", 1, 1, 2500.0, 28, "1", "8", "1"],
            ["000000", 1, 1, 5000.0, 30, "1", "9", "1"],
            ["222205", 1, 1, 0.0, 30, "1", "9", "1"],
            ["222205", 1, 1, 5000.0, 10, "1", "9", "1"],
        ],
        columns=[
            "cbo2002ocupacao",
            "saldomovimentacao",
            "peso",
            "salario",
            "idade",
            "sexo",
            "graudeinstrucao",
            "racacor",
        ],
    )
    movements.to_parquet(partition / "part.parquet", index=False)
    ipca = pd.DataFrame(
        {
            "periodo_num": [202101],
            "indice": [80.0],
        }
    )
    classification = pd.DataFrame(
        {
            "cbo_4d": ["1111", "2222"],
            "cbo_ilo_gradient": [
                "Not Exposed",
                "Exposed: Gradient 2",
            ],
        }
    )

    panel, metrics = module.build_national_panel(
        tmp_path / "movements" / "competenciamov=*" / "part.parquet",
        ipca,
        classification,
        start_period=202101,
        end_period=202101,
        scratch_parent=tmp_path,
    )

    first = panel.set_index("cbo_4d").loc["1111"]
    assert first["admissoes"] == 0
    assert np.isnan(first["salario_medio_adm"])
    assert np.isnan(first["idade_media_adm"])
    assert first["desligamentos"] == 1
    assert first["salario_medio_desl"] == pytest.approx(2000.0)
    assert (
        panel.set_index("cbo_4d").loc["3333", "cbo_ilo_gradient"]
        == "No score"
    )
    assert metrics["invalid_rows_rejected"] == 3
    assert metrics["new_unclassified_cbo_families"] == ["3333"]
    module.validate_national_panel(panel)


def test_panel_validation_rejects_wage_in_zero_flow_cell() -> None:
    module = load_panel_module()
    invalid = pd.DataFrame(
        {
            "cbo_4d": ["1111"],
            "periodo_num": [202101],
            "admissoes": [0],
            "desligamentos": [1],
            "salario_medio_adm": [1104.7868],
            "salario_medio_desl": [2000.0],
            "idade_media_adm": [np.nan],
            "idade_media_desl": [40.0],
            "pct_mulher_adm": [np.nan],
            "pct_mulher_desl": [0.0],
            "pct_superior_adm": [np.nan],
            "pct_superior_desl": [0.0],
            "pct_negra_adm": [np.nan],
            "pct_negra_desl": [0.0],
        }
    )

    with pytest.raises(RuntimeError, match="zero-flow admission"):
        module.validate_national_panel(invalid)
