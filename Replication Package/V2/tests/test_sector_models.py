from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "models" / "sector_models.py"


def load_sector_module():
    sys.path.insert(0, str(MODULE_PATH.parent))
    spec = importlib.util.spec_from_file_location(
        "sector_models",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load sector_models.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sector_contract_uses_section_fe_and_division_cluster() -> None:
    module = load_sector_module()
    contracts = {
        item["level_id"]: item for item in module.sector_model_contract()
    }

    assert contracts["level_2"]["fixed_effects"] == (
        "cbo_section",
        "section_period",
    )
    assert contracts["level_2"]["cluster_variables"] == ("cbo_4d",)
    assert contracts["level_2_two_way"]["cluster_variables"] == (
        "cbo_4d",
        "divisao",
    )
    assert contracts["level_3"]["fixed_effects"] == (
        "cbo_section",
        "section_period",
        "cbo2_period",
    )


def test_level_three_is_always_labeled_support_diagnostic() -> None:
    module = load_sector_module()
    level_three = {
        item["level_id"]: item
        for item in module.sector_model_contract()
    }["level_3"]

    assert level_three["role"] == "support_diagnostic"


def test_division_panel_build_uses_deterministic_duckdb(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = load_sector_module()
    destination = tmp_path / "division_panel.parquet"
    statements: list[str] = []

    class Result:
        def fetchone(self):
            return (1, 0, 1, 1, 1, 1)

    class Connection:
        def execute(self, query: str):
            normalized = " ".join(query.split())
            statements.append(normalized)
            if normalized.startswith("COPY"):
                temporary = destination.with_suffix(
                    f"{destination.suffix}.tmp"
                )
                temporary.write_bytes(b"deterministic-parquet")
            return Result()

        def close(self) -> None:
            return None

    monkeypatch.setattr(module.duckdb, "connect", lambda: Connection())

    metrics = module.build_division_panel(
        tmp_path / "subclass_panel.parquet",
        destination,
    )

    assert statements[0] == "SET threads = 1"
    copy_statement = next(
        statement
        for statement in statements
        if statement.startswith("COPY")
    )
    assert (
        "ORDER BY cbo_4d, secao, divisao, periodo_num"
        in copy_statement
    )
    assert metrics["division_panel_cells"] == 1
