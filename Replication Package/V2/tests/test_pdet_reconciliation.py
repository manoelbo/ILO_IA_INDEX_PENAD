from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest
from openpyxl import Workbook


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "ingest" / "reconcile_pdet.py"


def load_pdet_module():
    spec = importlib.util.spec_from_file_location(
        "reconcile_pdet",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load reconcile_pdet.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_adjusted_workbook(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Tabela 5.1"
    sheet.append(["TABELA 5.1 - SÉRIE COM AJUSTES"])
    for _ in range(3):
        sheet.append([])
    sheet.append(
        [None, "Mês", "Estoque", "Admissões", "Desligamentos", "Saldos"]
    )
    sheet.append([None, "Janeiro/2021", 100, 10, 7, 3])
    sheet.append([None, "Fevereiro/2021", 104, 12, 8, 4])
    workbook.save(path)


def test_parse_adjusted_series_reads_fact_months(tmp_path: Path) -> None:
    module = load_pdet_module()
    workbook_path = tmp_path / "pdet.xlsx"
    write_adjusted_workbook(workbook_path)

    series = module.parse_adjusted_series(
        workbook_path,
        start_period=202101,
        end_period=202102,
    )

    assert series["competenciamov"].tolist() == [202101, 202102]
    assert series["pdet_admissoes"].tolist() == [10, 12]
    assert series["pdet_desligamentos"].tolist() == [7, 8]
    assert series["pdet_saldo"].tolist() == [3, 4]


def test_parse_adjusted_series_rejects_inconsistent_balance(
    tmp_path: Path,
) -> None:
    module = load_pdet_module()
    workbook_path = tmp_path / "pdet.xlsx"
    write_adjusted_workbook(workbook_path)
    workbook = module.load_workbook(workbook_path)
    workbook["Tabela 5.1"]["F6"] = 99
    workbook.save(workbook_path)

    with pytest.raises(RuntimeError, match="balance identity"):
        module.parse_adjusted_series(
            workbook_path,
            start_period=202101,
            end_period=202102,
        )


def test_reconciliation_reports_exact_and_shift_diagnostics() -> None:
    module = load_pdet_module()
    official = pd.DataFrame(
        {
            "competenciamov": [202101, 202102, 202103],
            "pdet_admissoes": [10, 20, 30],
            "pdet_desligamentos": [7, 11, 18],
            "pdet_saldo": [3, 9, 12],
        }
    )
    v2 = pd.DataFrame(
        {
            "competenciamov": [202101, 202102, 202103],
            "v2_admissoes": [10, 20, 30],
            "v2_desligamentos": [7, 11, 18],
            "v2_saldo": [3, 9, 12],
        }
    )

    comparison, metrics = module.reconcile_monthly(official, v2)

    assert metrics["months"] == 3
    assert metrics["months_with_any_difference"] == 0
    assert metrics["systematic_month_shift_detected"] is False
    assert comparison["diferenca_admissoes_abs"].sum() == 0
    assert comparison["diferenca_desligamentos_abs"].sum() == 0
    assert comparison["diferenca_saldo_abs"].sum() == 0
