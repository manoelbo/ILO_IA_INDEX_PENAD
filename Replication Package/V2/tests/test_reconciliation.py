from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "ingest" / "reconcile_v1.py"


def load_reconciliation_module():
    spec = importlib.util.spec_from_file_location(
        "reconcile_v1",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load reconcile_v1.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reconciliation_decomposes_mov_revision_for_and_exc() -> None:
    module = load_reconciliation_module()
    v1 = pd.DataFrame(
        {
            "competenciamov": ["202101"],
            "v1_admissoes": [10],
            "v1_desligamentos": [8],
        }
    )
    v2 = pd.DataFrame(
        {
            "competenciamov": ["202101", "202101", "202101"],
            "origem": ["MOV", "FOR", "EXC"],
            "saldomovimentacao": [1, 1, 1],
            "linhas": [11, 2, 1],
        }
    )

    result = module.reconcile_monthly_totals(v1, v2)

    row = result.iloc[0]
    assert row["v2_admissoes"] == 12
    assert row["delta_admissoes_abs"] == 2
    assert row["delta_admissoes_pct"] == 20.0
    assert row["delta_admissoes_revisao_mov"] == 1
    assert row["delta_admissoes_for"] == 2
    assert row["delta_admissoes_exc"] == -1
    assert (
        row["delta_admissoes_revisao_mov"]
        + row["delta_admissoes_for"]
        + row["delta_admissoes_exc"]
        == row["delta_admissoes_abs"]
    )
    assert row["v2_desligamentos"] == 0
    assert row["delta_desligamentos_abs"] == -8
    assert row["delta_desligamentos_pct"] == -100.0


def test_reconciliation_preserves_signed_exclusion_components() -> None:
    module = load_reconciliation_module()
    v1 = pd.DataFrame(
        {
            "competenciamov": ["202102"],
            "v1_admissoes": [4],
            "v1_desligamentos": [6],
        }
    )
    v2 = pd.DataFrame(
        {
            "competenciamov": ["202102", "202102", "202102"],
            "origem": ["MOV", "FOR", "EXC"],
            "saldomovimentacao": [-1, -1, -1],
            "linhas": [6, 3, 2],
        }
    )

    result = module.reconcile_monthly_totals(v1, v2)

    row = result.iloc[0]
    assert row["v2_desligamentos"] == 7
    assert row["delta_desligamentos_abs"] == 1
    assert row["delta_desligamentos_revisao_mov"] == 0
    assert row["delta_desligamentos_for"] == 3
    assert row["delta_desligamentos_exc"] == -2


def test_report_exposes_the_annual_delta_decomposition(
    tmp_path: Path,
) -> None:
    module = load_reconciliation_module()
    v1 = pd.DataFrame(
        {
            "competenciamov": ["202101"],
            "v1_admissoes": [10],
            "v1_desligamentos": [8],
        }
    )
    v2 = pd.DataFrame(
        {
            "competenciamov": ["202101"] * 6,
            "origem": ["MOV", "FOR", "EXC"] * 2,
            "saldomovimentacao": [1, 1, 1, -1, -1, -1],
            "linhas": [10, 2, 1, 8, 3, 2],
        }
    )
    result = module.reconcile_monthly_totals(v1, v2)
    report_path = tmp_path / "RECONCILIACAO.md"

    module.write_report(result, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "MOV revision: 0" in report
    assert "FOR contribution: 5" in report
    assert "EXC contribution: -3" in report
