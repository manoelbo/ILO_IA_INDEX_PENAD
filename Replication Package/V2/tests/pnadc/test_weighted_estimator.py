from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


CODE_DIR = Path(__file__).resolve().parent
V2_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE_DIR))
sys.path.insert(0, str(V2_ROOT / "code" / "caged" / "models"))

from estimators import fit_model  # noqa: E402
from v2_pnadc.weighted_estimator import fit_weighted_model  # noqa: E402


def equivalence_frame() -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    rng = np.random.default_rng(20260730)
    for cluster in range(12):
        treated = int(cluster < 6)
        for quarter in range(8):
            post = int(quarter >= 4)
            for person in range(4):
                rows.append(
                    {
                        "cod3": f"{cluster:03d}",
                        "quarter": f"Q{quarter}",
                        "post_treat": treated * post,
                        "outcome": (
                            0.4 * cluster
                            + 0.2 * quarter
                            + 0.75 * treated * post
                            + rng.normal(scale=0.2)
                        ),
                        "unit_weight": 1.0,
                        "pct_mulher_adm": person / 10,
                    }
                )
    return pd.DataFrame(rows)


def test_unit_weights_match_shared_fit_model_to_1e_10() -> None:
    data = equivalence_frame()
    specification = {
        "model_id": "unit_weight_equivalence",
        "outcome": "outcome",
        "treatment_term": "post_treat",
        "estimator": "ols",
        "fixed_effects": ("cod3", "quarter"),
        "cluster_variables": ("cod3",),
        "controls": (),
        "principal": True,
    }

    shared, _ = fit_model(data, **specification)
    weighted, _ = fit_weighted_model(
        data,
        **specification,
        weight_column="unit_weight",
    )

    assert set(weighted) == {
        *shared.keys(),
        "weight_column",
        "sum_of_weights",
    }
    assert len(weighted) == 27
    assert abs(weighted["coefficient"] - shared["coefficient"]) <= 1e-10
    assert abs(weighted["standard_error"] - shared["standard_error"]) <= 1e-10
    assert weighted["weight_column"] == "unit_weight"
    assert weighted["sum_of_weights"] == pytest.approx(weighted["n_obs"])


def test_principal_weighted_model_calls_shared_control_guard() -> None:
    data = equivalence_frame()

    with pytest.raises(ValueError, match="contemporary composition"):
        fit_weighted_model(
            data,
            model_id="forbidden_control",
            outcome="outcome",
            treatment_term="post_treat",
            estimator="ols",
            fixed_effects=("cod3", "quarter"),
            cluster_variables=("cod3",),
            controls=("pct_mulher_adm",),
            principal=True,
            weight_column="unit_weight",
        )


def test_weighted_ppml_is_rejected_by_the_installed_backend() -> None:
    data = equivalence_frame()

    with pytest.raises(ValueError, match="Weighted PPML is not supported"):
        fit_weighted_model(
            data,
            model_id="unsupported_weighted_ppml",
            outcome="outcome",
            treatment_term="post_treat",
            estimator="ppml",
            fixed_effects=("cod3", "quarter"),
            cluster_variables=("cod3",),
            weight_column="unit_weight",
        )
