from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RAIS_CODE = PACKAGE_ROOT / "code" / "rais"
for module_path in (
    PACKAGE_ROOT / "code",
    RAIS_CODE,
    PACKAGE_ROOT / "code" / "common",
    PACKAGE_ROOT / "code" / "caged" / "models",
):
    if str(module_path) not in sys.path:
        sys.path.insert(0, str(module_path))


def _load_module():
    package_name = "v2_rais_offline"
    if package_name not in sys.modules:
        specification = importlib.util.spec_from_file_location(
            package_name,
            RAIS_CODE / "__init__.py",
            submodule_search_locations=[str(RAIS_CODE)],
        )
        if specification is None or specification.loader is None:
            raise RuntimeError("Unable to load the RAIS package")
        package = importlib.util.module_from_spec(specification)
        sys.modules[package_name] = package
        specification.loader.exec_module(package)
    return importlib.import_module(f"{package_name}.r10_sensitivities")


def test_replay_diagnostic_validates_frozen_input_without_network(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_module()
    diagnostic_path = tmp_path / "diagnostic.csv"
    manifest_path = tmp_path / "manifest.json"
    support_path = tmp_path / "support.json"
    diagnostic = pd.DataFrame(
        {
            "ano": list(range(2016, 2025)),
            "start_month_unresolved": [1] * 9,
            "inactive_end_month_unresolved": [0] * 9,
        }
    )
    diagnostic.to_csv(diagnostic_path, index=False)
    digest = hashlib.sha256(diagnostic_path.read_bytes()).hexdigest()
    manifest_path.write_text(
        json.dumps(
            {
                "sha256": digest,
                "linhas": 9,
                "consulta": module.DOMAIN_DIAGNOSTIC_QUERY,
                "treatment_coefficient_estimated": False,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOMAIN_DIAGNOSTIC_PATH", diagnostic_path)
    monkeypatch.setattr(
        module,
        "DOMAIN_DIAGNOSTIC_MANIFEST_PATH",
        manifest_path,
    )
    monkeypatch.setattr(module, "DOMAIN_DIAGNOSTIC_SUPPORT_PATH", support_path)
    monkeypatch.setattr(
        module,
        "_run_bq_csv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("offline replay attempted a network query")
        ),
    )

    result = module.run_replay_diagnostic()

    assert result["support"]["current_run_used_network"] is False
    assert result["support"]["diagnostic_sha256"] == digest
    assert json.loads(support_path.read_text(encoding="utf-8"))[
        "current_run_used_network"
    ] is False
