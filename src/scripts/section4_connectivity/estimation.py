"""Estimators for the Section 4 connectivity extension."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pyfixest as pf
from scipy.stats import chi2

from section4_event_study.formatting import stars

from .config import BIN_MAX, BIN_MIN, FE_SPECS, REFERENCE_PERIOD


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=r"(?s).*dropped due to multicollinearity.*", category=UserWarning)

FE_LIKE_COLUMNS = {"cbo_4d", "id_municipio", "periodo", "cbo_municipio", "cbo_periodo", "uf_periodo", "quad_subgroup_fe"}


def event_dummy_name(t: int) -> str:
    return f"ddd_tm{-t}" if t < 0 else f"ddd_t{t}"


def prepare_event_study_design(
    data: pd.DataFrame,
    bin_min: int = BIN_MIN,
    bin_max: int = BIN_MAX,
    high_connect_col: str = "high_connect",
) -> tuple[pd.DataFrame, list[str], dict[int, str], dict[str, float | int]]:
    out = data.copy()
    out["t_binned"] = pd.to_numeric(out["tempo_relativo_meses"], errors="coerce").clip(bin_min, bin_max).astype("Int64")
    dummy_names: list[str] = []
    t_to_name: dict[int, str] = {}
    for t in range(bin_min, bin_max + 1):
        if t == REFERENCE_PERIOD:
            continue
        name = event_dummy_name(t)
        out[name] = (
            out["t_binned"].eq(t)
            & pd.to_numeric(out["scenario_treat"], errors="coerce").eq(1)
            & pd.to_numeric(out[high_connect_col], errors="coerce").eq(1)
        ).astype(int)
        dummy_names.append(name)
        t_to_name[t] = name
    reference = {"t": REFERENCE_PERIOD, "coef": 0.0, "se": 0.0, "p_value": np.nan, "ci_low": 0.0, "ci_high": 0.0}
    return out, dummy_names, t_to_name, reference


def _cluster_vcov(cluster: str) -> dict[str, str]:
    return {"CRV1": cluster}


def _clean_data(
    data: pd.DataFrame,
    outcome: str,
    term: str,
    cluster: str,
    required: list[str] | None = None,
    weight: str | None = None,
) -> pd.DataFrame:
    cols = [outcome, term, cluster, "cbo_4d", "id_municipio", *(required or [])]
    if weight:
        cols.append(weight)
    available_cols = list(dict.fromkeys([col for col in cols if col in data.columns]))
    d = data[available_cols].dropna(subset=[outcome, term]).copy()
    for col in [outcome, term, *(required or [])]:
        if col in d.columns:
            if col not in FE_LIKE_COLUMNS:
                d[col] = pd.to_numeric(d[col], errors="coerce")
    if weight:
        d[weight] = pd.to_numeric(d[weight], errors="coerce")
        d = d[d[weight].gt(0)].copy()
    d = d.dropna(subset=[outcome, term])
    return d


def estimate_term(
    data: pd.DataFrame,
    outcome: str,
    term: str = "post_treat_connect",
    fe_spec: str = "strong",
    model_type: str = "ols",
    extra_terms: list[str] | None = None,
    extra_required: list[str] | None = None,
    cluster: str | None = None,
    weight: str | None = None,
) -> dict[str, object]:
    spec = FE_SPECS[fe_spec]
    fe = spec["fe"]
    cluster_var = cluster or str(spec["cluster"])
    extras = extra_terms if extra_terms is not None else list(spec["extra_terms"])
    required = [cluster_var, *fe.replace(" + ", "+").split("+"), *extras, *(extra_required or [])]
    d = _clean_data(data, outcome, term, cluster_var, required, weight)
    if d.empty or d[term].nunique() < 2:
        return {
            "result_status": "failed_insufficient_sample",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": int(len(d)),
            "n_cbo": int(d["cbo_4d"].nunique()) if "cbo_4d" in d else 0,
            "n_municipios": int(d["id_municipio"].nunique()) if "id_municipio" in d else 0,
            "n_clusters": int(d[cluster_var].nunique()) if cluster_var in d else 0,
            "error": "Empty sample or no identifying variation.",
            "formula": "",
            "model_type": model_type,
        }
    rhs = " + ".join([term, *extras])
    formula = f"{outcome} ~ {rhs} | {fe}"
    try:
        if model_type == "poisson":
            d = d[pd.to_numeric(d[outcome], errors="coerce").ge(0)].copy()
            model = pf.fepois(formula, data=d, vcov=_cluster_vcov(cluster_var))
        else:
            if weight:
                model = pf.feols(formula, data=d, vcov=_cluster_vcov(cluster_var), weights=weight)
            else:
                model = pf.feols(formula, data=d, vcov=_cluster_vcov(cluster_var))
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
            "n_municipios": int(d["id_municipio"].nunique()),
            "n_clusters": int(d[cluster_var].nunique()),
            "error": "",
            "formula": formula,
            "model_type": model_type,
        }
    except Exception as exc:  # noqa: BLE001 - recorded in audit tables
        return {
            "result_status": "failed_estimation",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": int(len(d)),
            "n_cbo": int(d["cbo_4d"].nunique()) if "cbo_4d" in d else 0,
            "n_municipios": int(d["id_municipio"].nunique()) if "id_municipio" in d else 0,
            "n_clusters": int(d[cluster_var].nunique()) if cluster_var in d else 0,
            "error": str(exc),
            "formula": formula,
            "model_type": model_type,
        }


def _wald_pretrend(model: object, pre_terms: list[str]) -> tuple[float, float, str]:
    if not pre_terms:
        return np.nan, np.nan, "not_available"
    coef_index = list(model.coef().index)
    try:
        r_matrix = np.zeros((len(pre_terms), len(coef_index)))
        for row_idx, term in enumerate(pre_terms):
            r_matrix[row_idx, coef_index.index(term)] = 1.0
        result = model.wald_test(R=r_matrix, q=np.zeros(len(pre_terms)), distribution="chi2")
        p_value = np.nan
        statistic = np.nan
        for key, value in result.items():
            key_text = str(key).lower()
            if "p" in key_text:
                p_value = float(value)
            if "stat" in key_text or "wald" in key_text:
                statistic = float(value)
        if not pd.isna(p_value):
            return statistic, p_value, "wald_chi2"
    except Exception:
        pass
    tstats = model.tstat().reindex(pre_terms).dropna()
    if tstats.empty:
        return np.nan, np.nan, "not_available"
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


def estimate_event_study(
    data: pd.DataFrame,
    outcomes: dict[str, str],
    fe_spec: str = "strong",
    high_connect_col: str = "high_connect",
    cluster: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    event_data, dummy_names, t_to_name, reference = prepare_event_study_design(data, high_connect_col=high_connect_col)
    spec = FE_SPECS[fe_spec]
    cluster_var = cluster or str(spec["cluster"])
    fe = spec["fe"]
    extra_terms = list(spec["extra_terms"])
    coef_rows: list[dict[str, object]] = []
    pretrend_rows: list[dict[str, object]] = []
    rhs = " + ".join([*dummy_names, *extra_terms])
    fe_cols = fe.replace(" + ", "+").split("+")
    for outcome, label in outcomes.items():
        required = [outcome, cluster_var, *fe_cols, *dummy_names, *extra_terms]
        d = event_data.dropna(subset=[col for col in required if col in event_data.columns]).copy()
        if d.empty:
            continue
        formula = f"{outcome} ~ {rhs} | {fe}"
        try:
            model = pf.feols(formula, data=d, vcov=_cluster_vcov(cluster_var))
        except Exception as exc:  # noqa: BLE001
            pretrend_rows.append(
                {
                    "outcome": outcome,
                    "outcome_label": label,
                    "coefs_pre": 0,
                    "sig_pre": 0,
                    "joint_p_value": np.nan,
                    "status": "failed",
                    "error": str(exc),
                }
            )
            continue
        coefs = model.coef()
        ses = model.se()
        pvalues = model.pvalue()
        for t in range(BIN_MIN, BIN_MAX + 1):
            if t == REFERENCE_PERIOD:
                row = dict(reference)
                row["coefficient_status"] = "reference"
            else:
                term = t_to_name[t]
                if term not in coefs.index:
                    row = {"t": t, "coef": np.nan, "se": np.nan, "p_value": np.nan, "ci_low": np.nan, "ci_high": np.nan}
                    row["coefficient_status"] = "dropped"
                else:
                    coef = float(coefs.loc[term])
                    se = float(ses.loc[term])
                    p_value = float(pvalues.loc[term])
                    row = {
                        "t": t,
                        "coef": coef,
                        "se": se,
                        "p_value": p_value,
                        "ci_low": coef - 1.96 * se,
                        "ci_high": coef + 1.96 * se,
                        "coefficient_status": "estimated",
                    }
            row.update({"outcome": outcome, "outcome_label": label, "fe_spec": fe_spec})
            coef_rows.append(row)
        pre_terms = [t_to_name[t] for t in range(BIN_MIN, 0) if t != REFERENCE_PERIOD and t_to_name.get(t) in coefs.index]
        pre_p = pvalues.reindex(pre_terms).dropna()
        statistic, joint_p, method = _wald_pretrend(model, pre_terms)
        sig_pre = int((pre_p < 0.05).sum())
        pretrend_rows.append(
            {
                "outcome": outcome,
                "outcome_label": label,
                "coefs_pre": int(len(pre_terms)),
                "sig_pre": sig_pre,
                "wald_stat": statistic,
                "joint_p_value": joint_p,
                "method": method,
                "status": classify_pretrend(sig_pre, joint_p),
                "error": "",
            }
        )
    return pd.DataFrame(coef_rows), pd.DataFrame(pretrend_rows)
