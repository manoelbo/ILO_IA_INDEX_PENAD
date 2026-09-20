from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "models" / "exposure_sensitivity.py"


def load_module():
    sys.path.insert(0, str(PACKAGE_ROOT / "code" / "caged" / "panel"))
    sys.path.insert(0, str(PACKAGE_ROOT / "code" / "caged" / "models"))
    spec = importlib.util.spec_from_file_location(
        "exposure_sensitivity",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load exposure_sensitivity.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_vintage_2023_mode_resolves_ties_conservatively() -> None:
    module = load_module()

    assert module.vintage_2023_mode(
        ["Automation Potential", "Not affected"]
    ) == "Not affected"
    assert module.vintage_2023_mode(
        ["Automation Potential", "Augmentation Potential"]
    ) == "Augmentation Potential"


def test_model_agreement_requires_the_complete_gradient_label() -> None:
    module = load_module()
    tasks = pd.DataFrame(
        {
            "ISCO_08": ["1111", "1111", "2222", "2222"],
            "Title": ["A", "A", "B", "B"],
            "predicted_score_2025_gpt4o": [0.55, 0.55, 0.20, 0.20],
            "predicted_score_2025_gemini": [0.55, 0.55, 0.60, 0.60],
            "mean_score_2023": [0.40, 0.40, 0.30, 0.30],
            "SD_2023": [0.10, 0.10, 0.10, 0.10],
            "potential23": [
                "Automation Potential",
                "Automation Potential",
                "Not affected",
                "Not affected",
            ],
            "mean_score_2025": [0.55, 0.55, 0.40, 0.40],
            "SD_2025": [0.05, 0.05, 0.10, 0.10],
        }
    )

    measures = module.build_isco_measures(tasks).set_index("isco08")

    assert bool(measures.loc["1111", "models_agree"])
    assert not bool(measures.loc["2222", "models_agree"])
    assert measures.loc["1111", "gpt4o_label"] == (
        measures.loc["1111", "gemini_label"]
    )


def test_anthropic_support_excludes_zero_without_source_evidence() -> None:
    module = load_module()
    frame = pd.DataFrame(
        {
            "cbo_4d": ["1111", "2222", "Grupo de base", "3333"],
            "anthropic_automation_index": [0.2, 0.0, 0.0, -0.3],
            "imputation_method": [
                "direct_match",
                "zero_imputation_no_data",
                "zero_imputation_no_data",
                "hierarchical_3d_mean",
            ],
        }
    )

    cleaned = module.clean_anthropic(frame)

    assert cleaned["cbo_4d"].tolist() == ["1111", "3333"]
    assert np.isclose(cleaned["anthropic_z"].mean(), 0.0)
    assert np.isclose(cleaned["anthropic_z"].std(ddof=0), 1.0)


def test_spearman_rank_correlation_is_exact_for_reverse_ranks() -> None:
    module = load_module()

    correlation = module.spearman_rank_correlation(
        pd.Series([1.0, 2.0, 3.0]),
        pd.Series([30.0, 20.0, 10.0]),
    )

    assert correlation == pytest.approx(-1.0)
