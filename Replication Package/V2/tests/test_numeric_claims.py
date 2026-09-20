from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPLICATION_DIR = PACKAGE_ROOT / "code" / "replication"
if str(REPLICATION_DIR) not in sys.path:
    sys.path.insert(0, str(REPLICATION_DIR))

from claims import reconcile_claims


def test_claim_reconciliation_supports_filtered_csv_and_nested_json(
    tmp_path: Path,
) -> None:
    (tmp_path / "caged").mkdir()
    pd.DataFrame(
        {
            "outcome": ["admissions", "wage"],
            "coefficient": [-0.05, -0.04],
        }
    ).to_csv(tmp_path / "caged" / "models.csv", index=False)
    (tmp_path / "caged" / "status.json").write_text(
        json.dumps({"gate": {"opens": False}}),
        encoding="utf-8",
    )
    claims = pd.DataFrame(
        [
            {
                "claim_id": "c1",
                "manuscript_locator": "5.1",
                "description": "Wage coefficient",
                "component": "caged",
                "artifact_path": "models.csv",
                "field": "coefficient",
                "filter": '{"outcome":"wage"}',
                "aggregation": "scalar",
                "expected_value": "-0.04",
                "value_type": "number",
                "tolerance": "1e-12",
            },
            {
                "claim_id": "c2",
                "manuscript_locator": "B.4",
                "description": "Support gate",
                "component": "caged",
                "artifact_path": "status.json",
                "field": "gate.opens",
                "filter": "{}",
                "aggregation": "json_path",
                "expected_value": "false",
                "value_type": "boolean",
                "tolerance": "0",
            },
        ]
    )

    result = reconcile_claims(claims, output_root=tmp_path)

    assert result["status"].eq("pass").all()
    assert result["observed_value"].tolist() == ["-0.04", "false"]

    caged_only = reconcile_claims(
        claims.assign(component=["section3", "caged"]),
        output_root=tmp_path,
        components={"caged"},
    )
    assert caged_only["claim_id"].tolist() == ["c2"]


def test_claim_reconciliation_supports_numeric_filter_operators(
    tmp_path: Path,
) -> None:
    (tmp_path / "caged").mkdir()
    pd.DataFrame(
        {
            "outcome": ["wage", "wage", "wage", "admissions"],
            "coefficient": [-0.05, -0.02, 0.01, -0.10],
            "bh_significant": [True, True, True, True],
        }
    ).to_csv(tmp_path / "caged" / "models.csv", index=False)
    claims = pd.DataFrame(
        [
            {
                "claim_id": "negative_wage",
                "manuscript_locator": "5.2.6",
                "description": "Negative wage BH discoveries",
                "component": "caged",
                "artifact_path": "models.csv",
                "field": "coefficient",
                "filter": (
                    '{"outcome":"wage","bh_significant":true,'
                    '"coefficient__lt":0}'
                ),
                "aggregation": "count",
                "expected_value": "2",
                "value_type": "integer",
                "tolerance": "0",
            }
        ]
    )

    result = reconcile_claims(claims, output_root=tmp_path)

    assert result.loc[0, "status"] == "pass"
    assert result.loc[0, "observed_value"] == "2"


def test_frozen_claim_inventory_has_all_required_coordinates() -> None:
    claims = pd.read_csv(
        PACKAGE_ROOT / "config" / "numeric_claims.csv",
        dtype=str,
        keep_default_na=False,
    )

    required = {
        "claim_id",
        "manuscript_locator",
        "description",
        "component",
        "artifact_path",
        "field",
        "filter",
        "aggregation",
        "expected_value",
        "value_type",
        "tolerance",
    }
    assert set(claims.columns) == required
    assert len(claims) >= 50
    assert claims[list(required)].ne("").all().all()
    assert claims["claim_id"].is_unique
    assert set(claims["component"]) == {
        "section3",
        "caged",
        "rais",
        "pnadc",
        "spatial",
    }
    assert not claims["manuscript_locator"].str.startswith("Section 5.4").any()
    assert set(
        claims.loc[claims["component"].eq("rais"), "manuscript_locator"]
    ) == {"Appendix B.1", "Appendix D.1"}
    assert set(
        claims.loc[claims["component"].eq("pnadc"), "manuscript_locator"]
    ) == {"Appendix B.2", "Appendix D.2"}
