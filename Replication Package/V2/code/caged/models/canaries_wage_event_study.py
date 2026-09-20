#!/usr/bin/env python3
"""Event study do salário real de admissão na coorte Canaries de 22 a 25 anos.

Este contraste não entra em `group_event_studies.py` porque aquele módulo cobre
as partições PNAD/IBGE, e a coorte de 22 a 25 anos pertence às coortes Canaries.
Ele merece figura própria por ser o único contraste da dissertação cujo teste
conjunto de tendências paralelas não é rejeitado.

A especificação é idêntica à das demais figuras de grupo: MQO sobre o logaritmo,
efeitos fixos de CBO de quatro dígitos e de mês, erro-padrão agrupado por CBO,
janela de -23 a +41 e novembro de 2022 omitido como referência.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

MODELS_DIR = Path(__file__).resolve().parent
if str(MODELS_DIR) not in sys.path:
    sys.path.insert(0, str(MODELS_DIR))

from estimators import cluster_t_inference
from event_study import REFERENCE_EVENT_TIME
from group_event_studies import (
    CLUSTERS,
    FIXED_EFFECTS,
    PRE_WINDOW,
    WINDOW,
    complete_coefficient_grid,
    expected_estimated_event_times,
)
from pretrend_engine import (
    add_event_time,
    atomic_csv,
    atomic_json,
    event_parameter_frame,
    fit_event_model,
    restrict_event_window,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
FROZEN_PANEL = (
    PACKAGE_ROOT / "data" / "derived" / "painel_heterogeneity_ddd.parquet"
)
OUTPUT_DIR = PACKAGE_ROOT / "results" / "models"
COEFFICIENTS_PATH = OUTPUT_DIR / "canaries_22_25_wage_event_study.csv"
SUPPORT_PATH = OUTPUT_DIR / "canaries_22_25_wage_event_study_support.json"

DIMENSION = "age_canaries"
GROUP_ID = "age_22_25"
GROUP_LABEL = "Age 22-25"
OUTCOME = "ln_salario_real_adm"
ESTIMATOR = "ols"
MODEL_ID = f"group_event__canaries__{GROUP_ID}__{OUTCOME}"


def load_sample() -> pd.DataFrame:
    panel = pd.read_parquet(
        FROZEN_PANEL,
        columns=[
            "cbo_4d",
            "periodo_num",
            "periodo",
            "subgroup",
            "dimension",
            "group_id",
            "treatment",
            OUTCOME,
        ],
    )
    sample = panel.loc[
        panel["dimension"].eq(DIMENSION)
        & panel["group_id"].eq(GROUP_ID)
        & panel["subgroup"].eq("target")
    ].copy()
    if sample.empty:
        raise RuntimeError(
            f"Coorte {GROUP_ID} ausente da dimensão {DIMENSION}"
        )
    sample = add_event_time(sample)
    return restrict_event_window(sample, *WINDOW)


def estimate(sample: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    model, model_data, formula, cluster_counts = fit_event_model(
        sample,
        outcome=OUTCOME,
        estimator=ESTIMATOR,
        interaction="treatment",
        fixed_effects=FIXED_EFFECTS,
        cluster_variables=CLUSTERS,
        model_id=MODEL_ID,
    )
    minimum_clusters = int(min(cluster_counts.values()))
    parameters = event_parameter_frame(
        model,
        "treatment",
        expected_event_times=expected_estimated_event_times(),
    )
    coefficients = complete_coefficient_grid(
        parameters,
        minimum_clusters=minimum_clusters,
    )
    coefficients["model_id"] = MODEL_ID
    coefficients["dimension"] = "age_canaries"
    coefficients["group_id"] = GROUP_ID
    coefficients["group_label"] = GROUP_LABEL
    coefficients["outcome"] = OUTCOME
    coefficients["estimator"] = ESTIMATOR
    coefficients["reference_period"] = "2022-11"
    coefficients["is_causal_effect"] = False
    coefficients["formula"] = formula
    coefficients["n_obs"] = int(model._N)
    coefficients["minimum_clusters"] = minimum_clusters

    support = {
        "model_id": MODEL_ID,
        "dimension": DIMENSION,
        "group_id": GROUP_ID,
        "outcome": OUTCOME,
        "estimator": ESTIMATOR,
        "event_window": f"{WINDOW[0]}_to_{WINDOW[1]}",
        "reference_event_time": REFERENCE_EVENT_TIME,
        "reference_period": "2022-11",
        "pre_window": f"{PRE_WINDOW[0]}_to_{PRE_WINDOW[1]}",
        "pre_coefficient_mean": float(
            coefficients["pre_coefficient_mean"].iloc[0]
        ),
        "n_obs": int(model._N),
        "complete_case_input": int(len(model_data)),
        "minimum_clusters": minimum_clusters,
        "coefficient_rows": int(len(coefficients)),
        "is_causal_effect": False,
        "note": (
            "Único contraste da dissertação cujo teste conjunto de tendências "
            "paralelas não é rejeitado; é 1 entre 100 contrastes de "
            "diagnóstico, sem ajuste de multiplicidade sobre a família de "
            "pretrends."
        ),
    }
    return coefficients, support


def main() -> None:
    sample = load_sample()
    coefficients, support = estimate(sample)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    atomic_csv(coefficients, COEFFICIENTS_PATH)
    atomic_json(support, SUPPORT_PATH)
    print(
        f"[canaries-wage] linhas={len(coefficients)} "
        f"média pré={support['pre_coefficient_mean']:.4f} "
        f"clusters={support['minimum_clusters']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
