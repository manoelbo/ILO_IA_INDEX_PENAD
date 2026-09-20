"""Econometric estimators used by the final Section 4 package."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pyfixest as pf
from scipy.stats import chi2

from .config import BIN_MAX, BIN_MIN, CONTROL_COLUMNS, CONTROL_TERMS, REFERENCE_PERIOD
from .formatting import stars


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=r"(?s).*dropped due to multicollinearity.*", category=UserWarning)


def _clean_estimation_data(
    data: pd.DataFrame,
    outcome: str,
    term: str,
    cluster: str,
    weight: str | None = None,
    extra_required: list[str] | None = None,
    controls: list[str] | None = None,
) -> pd.DataFrame:
    control_columns = CONTROL_COLUMNS if controls is None else controls
    required = [outcome, term, cluster, "periodo", "cbo_4d", *control_columns]
    if extra_required:
        required.extend(extra_required)
    if weight:
        required.append(weight)
    d = data.dropna(subset=[col for col in required if col in data.columns]).copy()
    for col in [outcome, term, *control_columns, *(extra_required or [])]:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")
    if weight:
        d[weight] = pd.to_numeric(d[weight], errors="coerce")
        d = d[d[weight] > 0].copy()
    d = d.dropna(subset=[outcome, term, *control_columns])
    return d


def estimate_term(
    data: pd.DataFrame,
    outcome: str,
    term: str = "post_treat",
    cluster: str = "cbo_4d",
    weight: str | None = None,
    fe: str = "cbo_4d + periodo",
    extra_terms: list[str] | None = None,
    extra_required: list[str] | None = None,
    controls: list[str] | None = None,
) -> dict[str, object]:
    control_columns = CONTROL_COLUMNS if controls is None else controls
    d = _clean_estimation_data(data, outcome, term, cluster, weight, extra_required, control_columns)
    if d.empty or d["cbo_4d"].nunique() < 2 or d[term].nunique() < 2:
        return {
            "result_status": "failed_insufficient_sample",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": int(len(d)),
            "n_cbo": int(d["cbo_4d"].nunique()) if "cbo_4d" in d else 0,
            "n_clusters": int(d[cluster].nunique()) if cluster in d else 0,
            "error": "Empty sample, fewer than two CBOs, or no identifying variation.",
        }
    rhs_terms = [term, *(extra_terms or []), *control_columns]
    formula = f"{outcome} ~ {' + '.join(rhs_terms)} | {fe}"
    try:
        model = pf.feols(formula, data=d, vcov={"CRV1": cluster}, weights=weight)
        if term not in model.coef().index:
            raise RuntimeError(f"{term} was dropped or not estimated.")
        p_value = float(model.pvalue().loc[term])
        return {
            "result_status": "estimated",
            "coef": float(model.coef().loc[term]),
            "se": float(model.se().loc[term]),
            "p_value": p_value,
            "stars": stars(p_value),
            "n_obs": int(len(d)),
            "n_cbo": int(d["cbo_4d"].nunique()),
            "n_clusters": int(d[cluster].nunique()),
            "error": "",
            "formula": formula,
            "model_type": "ols",
        }
    except Exception as exc:  # noqa: BLE001 - recorded in audit table
        return {
            "result_status": "failed_estimation",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": int(len(d)),
            "n_cbo": int(d["cbo_4d"].nunique()),
            "n_clusters": int(d[cluster].nunique()) if cluster in d else 0,
            "error": str(exc),
            "formula": formula,
            "model_type": "ols",
        }


def estimate_poisson_term(
    data: pd.DataFrame,
    outcome: str,
    term: str = "post_treat",
    cluster: str = "cbo_4d",
    fe: str = "cbo_4d + periodo",
    extra_terms: list[str] | None = None,
    extra_required: list[str] | None = None,
    controls: list[str] | None = None,
) -> dict[str, object]:
    control_columns = CONTROL_COLUMNS if controls is None else controls
    d = _clean_estimation_data(data, outcome, term, cluster, None, extra_required, control_columns)
    if outcome in d.columns:
        d[outcome] = pd.to_numeric(d[outcome], errors="coerce")
        d = d[d[outcome].ge(0)].copy()
    if d.empty or d["cbo_4d"].nunique() < 2 or d[term].nunique() < 2:
        return {
            "result_status": "failed_insufficient_sample",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": int(len(d)),
            "n_cbo": int(d["cbo_4d"].nunique()) if "cbo_4d" in d else 0,
            "n_clusters": int(d[cluster].nunique()) if cluster in d else 0,
            "error": "Empty sample, fewer than two CBOs, or no identifying variation.",
            "model_type": "poisson",
        }
    rhs_terms = [term, *(extra_terms or []), *control_columns]
    formula = f"{outcome} ~ {' + '.join(rhs_terms)} | {fe}"
    try:
        model = pf.fepois(formula, data=d, vcov={"CRV1": cluster})
        if term not in model.coef().index:
            raise RuntimeError(f"{term} was dropped or not estimated.")
        p_value = float(model.pvalue().loc[term])
        return {
            "result_status": "estimated",
            "coef": float(model.coef().loc[term]),
            "se": float(model.se().loc[term]),
            "p_value": p_value,
            "stars": stars(p_value),
            "n_obs": int(len(d)),
            "n_cbo": int(d["cbo_4d"].nunique()),
            "n_clusters": int(d[cluster].nunique()),
            "error": "",
            "formula": formula,
            "model_type": "poisson",
        }
    except Exception as exc:  # noqa: BLE001 - recorded in audit table
        return {
            "result_status": "failed_estimation",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": int(len(d)),
            "n_cbo": int(d["cbo_4d"].nunique()),
            "n_clusters": int(d[cluster].nunique()) if cluster in d else 0,
            "error": str(exc),
            "formula": formula,
            "model_type": "poisson",
        }


def event_dummy_name(t: int) -> str:
    return f"did_tm{-t}" if t < 0 else f"did_t{t}"


def prepare_event_data(data: pd.DataFrame) -> tuple[pd.DataFrame, list[str], dict[int, str]]:
    out = data.copy()
    out["t_binned"] = pd.to_numeric(out["tempo_relativo_meses"], errors="raise").clip(BIN_MIN, BIN_MAX).astype(int)
    dummy_names: list[str] = []
    t_to_name: dict[int, str] = {}
    for t in range(BIN_MIN, BIN_MAX + 1):
        if t == REFERENCE_PERIOD:
            continue
        name = event_dummy_name(t)
        out[name] = ((out["t_binned"] == t) & (out["scenario_treat"] == 1)).astype(int)
        dummy_names.append(name)
        t_to_name[t] = name
    return out, dummy_names, t_to_name


def _wald_pretrend(model: object, pre_terms: list[str]) -> tuple[float, float, str]:
    if not pre_terms:
        return np.nan, np.nan, "not_available_no_pre_terms"
    coef_index = list(model.coef().index)
    try:
        r_matrix = np.zeros((len(pre_terms), len(coef_index)))
        for row_idx, term in enumerate(pre_terms):
            r_matrix[row_idx, coef_index.index(term)] = 1.0
        result = model.wald_test(R=r_matrix, q=np.zeros(len(pre_terms)), distribution="chi2")
        statistic = np.nan
        p_value = np.nan
        for key, value in result.items():
            text = str(key).lower()
            if "p" in text:
                p_value = float(value)
            if ("stat" in text or "wald" in text) and not pd.isna(value):
                statistic = float(value)
        if not pd.isna(p_value):
            return statistic, p_value, "wald_chi2"
    except Exception:
        pass
    tstats = model.tstat().reindex(pre_terms).dropna()
    if tstats.empty:
        return np.nan, np.nan, "not_available_no_tstats"
    statistic = float(np.square(tstats.astype(float)).sum())
    return statistic, float(chi2.sf(statistic, len(tstats))), "tstat_chi2_fallback"


def classify_pretrend(n_pre_p_lt_005: int, joint_p_value: float) -> str:
    if pd.isna(joint_p_value):
        return "warning"
    if joint_p_value < 0.05 or n_pre_p_lt_005 >= 2:
        return "fail"
    if n_pre_p_lt_005 == 0 and joint_p_value > 0.10:
        return "pass"
    return "warning"


def estimate_event_study(data: pd.DataFrame, outcomes: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    event_data, dummy_names, t_to_name = prepare_event_data(data)
    coef_rows: list[dict[str, object]] = []
    pretrend_rows: list[dict[str, object]] = []
    did_terms = " + ".join(dummy_names)
    for outcome, label in outcomes.items():
        d = event_data.dropna(subset=[outcome, *CONTROL_COLUMNS, "cbo_4d", "periodo"]).copy()
        for col in [outcome, *CONTROL_COLUMNS]:
            d[col] = pd.to_numeric(d[col], errors="coerce")
        d = d.dropna(subset=[outcome, *CONTROL_COLUMNS])
        formula = f"{outcome} ~ {did_terms} + {CONTROL_TERMS} | cbo_4d + periodo"
        model = pf.feols(formula, data=d, vcov={"CRV1": "cbo_4d"})
        coefs = model.coef()
        ses = model.se()
        pvalues = model.pvalue()
        coef_index = set(coefs.index)
        for t in range(BIN_MIN, BIN_MAX + 1):
            is_reference = t == REFERENCE_PERIOD
            if is_reference:
                row = {"coef": 0.0, "se": 0.0, "p_value": np.nan, "ci_low": 0.0, "ci_high": 0.0, "coefficient_status": "reference"}
            else:
                term = t_to_name[t]
                if term in coef_index:
                    coef = float(coefs.loc[term])
                    se = float(ses.loc[term])
                    p_value = float(pvalues.loc[term])
                    row = {
                        "coef": coef,
                        "se": se,
                        "p_value": p_value,
                        "ci_low": coef - 1.96 * se,
                        "ci_high": coef + 1.96 * se,
                        "coefficient_status": "estimated",
                    }
                else:
                    row = {"coef": np.nan, "se": np.nan, "p_value": np.nan, "ci_low": np.nan, "ci_high": np.nan, "coefficient_status": "omitted"}
            coef_rows.append(
                {
                    "outcome": outcome,
                    "outcome_label": label,
                    "t": t,
                    "is_reference": is_reference,
                    "is_pre": t < 0 and not is_reference,
                    "n_obs": int(len(d)),
                    "n_cbo": int(d["cbo_4d"].nunique()),
                    **row,
                }
            )
        pre_terms = [t_to_name[t] for t in range(BIN_MIN, BIN_MAX + 1) if t < 0 and t != REFERENCE_PERIOD and t_to_name[t] in coef_index]
        pre_pvalues = pd.Series(pvalues).reindex(pre_terms).astype(float)
        joint_statistic, joint_p_value, joint_method = _wald_pretrend(model, pre_terms)
        n_pre_p_lt_005 = int((pre_pvalues < 0.05).sum())
        pretrend_rows.append(
            {
                "outcome": outcome,
                "outcome_label": label,
                "n_obs": int(len(d)),
                "n_cbo": int(d["cbo_4d"].nunique()),
                "n_pre_coefficients": len(pre_terms),
                "n_pre_p_lt_005": n_pre_p_lt_005,
                "joint_statistic": joint_statistic,
                "joint_p_value": joint_p_value,
                "joint_test_method": joint_method,
                "pretrend_status": classify_pretrend(n_pre_p_lt_005, joint_p_value),
            }
        )
    return pd.DataFrame(coef_rows), pd.DataFrame(pretrend_rows)
