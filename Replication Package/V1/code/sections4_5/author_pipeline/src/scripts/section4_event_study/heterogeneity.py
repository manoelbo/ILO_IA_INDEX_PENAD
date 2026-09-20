"""Triple-difference heterogeneity estimators for the final Section 4 package."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyfixest as pf

from .config import CONTROL_COLUMNS, CONTROL_TERMS, DATA_RAW, MAIN_OUTCOMES, SALARIO_MINIMO, TREATMENT_PERIOD
from .data import add_real_wage_measures, load_ipca
from .formatting import stars

RAW_BATCH_SIZE = 500_000


DIMENSIONS = {
    "income": {
        "panel": "Painel A: Renda",
        "method": "pre_treatment_cbo_income",
        "income_scheme": "legacy",
        "groups": [
            ("low_income", "Baixa renda: até 2 salários mínimos"),
            ("middle_income", "Média renda: mais de 2 até 5 salários mínimos"),
            ("high_income", "Alta renda: mais de 5 salários mínimos"),
        ],
    },
    "income_pnad": {
        "panel": "Painel A.2: Renda — faixas PNAD/IBGE",
        "method": "pre_treatment_cbo_income",
        "income_scheme": "pnad",
        "groups": [
            ("income_up_to_1sm", "Até 1 salário mínimo"),
            ("income_1_2sm", "Mais de 1 até 2 salários mínimos"),
            ("income_2_3sm", "Mais de 2 até 3 salários mínimos"),
            ("income_3_5sm", "Mais de 3 até 5 salários mínimos"),
            ("income_5_plus_sm", "Mais de 5 salários mínimos"),
        ],
    },
    "age": {
        "panel": "Painel B: Idade",
        "method": "micro_group_pair",
        "groups": [
            ("age_14_24", "14-24"),
            ("age_25_34", "25-34"),
            ("age_35_59", "35-59"),
            ("age_60_plus", "60+"),
        ],
    },
    "age_pnad": {
        "panel": "Painel B.2: Idade — faixas PNAD/IBGE",
        "method": "micro_group_pair",
        "groups": [
            ("age_18_24", "18-24"),
            ("age_25_34", "25-34"),
            ("age_35_44", "35-44"),
            ("age_45_54", "45-54"),
            ("age_55_plus", "55+"),
        ],
    },
    "sex": {
        "panel": "Painel C: Sexo",
        "method": "micro_group_pair",
        "groups": [("men", "Homens"), ("women", "Mulheres")],
    },
    "education": {
        "panel": "Painel D: Escolaridade",
        "method": "micro_group_pair",
        "groups": [
            ("fundamental_or_less", "Fundamental ou menos"),
            ("high_school", "Médio"),
            ("higher_education", "Superior"),
        ],
    },
    "race_color": {
        "panel": "Painel E: Raça/cor",
        "method": "micro_group_pair",
        "groups": [
            ("race_white", "Branca"),
            ("race_black", "Preta"),
            ("race_pardo", "Parda"),
            ("race_yellow", "Amarela"),
            ("race_indigenous", "Indígena"),
            ("race_unknown", "Não informada/identificada"),
        ],
    },
    "race_color_b": {
        "panel": "Painel E.2: Raça/cor — Branca e Negra",
        "method": "micro_group_pair",
        "groups": [
            ("race_white", "Branca"),
            ("race_black_combined", "Negra (preta e parda)"),
        ],
    },
}

CANARIES_AGE_DIMENSIONS = {
    "canaries_age": {
        "panel": "Painel F: Idade estilo Canaries",
        "method": "micro_group_pair",
        "groups": [
            ("age_22_25", "22-25"),
            ("age_26_30", "26-30"),
            ("age_31_34", "31-34"),
            ("age_35_40", "35-40"),
            ("age_41_49", "41-49"),
            ("age_50_plus", "50+"),
        ],
    },
}

ALL_MICRO_DIMENSIONS = {**DIMENSIONS, **CANARIES_AGE_DIMENSIONS}

RACE_COLOR_CODE_TO_GROUP = {
    "1": "race_white",
    "2": "race_black",
    "3": "race_pardo",
    "4": "race_yellow",
    "5": "race_indigenous",
    "6": "race_unknown",
    "9": "race_unknown",
}

RACE_COLOR_B_CODE_TO_GROUP = {
    "1": "race_white",
    "2": "race_black_combined",
    "3": "race_black_combined",
}

MICRO_DIMENSION_SOURCE_COLUMNS = {
    "age": "idade",
    "age_pnad": "idade",
    "canaries_age": "idade",
    "sex": "sexo",
    "education": "grau_instrucao",
    "race_color": "raca_cor",
    "race_color_b": "raca_cor",
}


def normalize_codes(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)


def valid_cbo_4d(series: pd.Series) -> pd.Series:
    codes = normalize_codes(series).str[:4]
    return codes.where(codes.str.fullmatch(r"\d{4}", na=False))


def iter_raw_batches(columns: list[str]):
    for path in sorted(DATA_RAW.glob("caged_*.parquet")):
        print(f"  Reading heterogeneity microdata: {path.name}", flush=True)
        parquet_file = pq.ParquetFile(path)
        for batch in parquet_file.iter_batches(batch_size=RAW_BATCH_SIZE, columns=columns):
            yield path, batch.to_pandas()


def income_group_for_median(value: float, scheme: str = "legacy") -> str | None:
    """Classify a pre-treatment CBO median wage measured in minimum wages."""
    if scheme not in {"legacy", "pnad"}:
        raise ValueError(f"Unknown income grouping scheme: {scheme}")
    if value is None or pd.isna(value) or float(value) <= 0:
        return None
    wage = float(value)
    if scheme == "legacy":
        if wage <= 2:
            return "low_income"
        if wage <= 5:
            return "middle_income"
        return "high_income"
    if wage <= 1:
        return "income_up_to_1sm"
    if wage <= 2:
        return "income_1_2sm"
    if wage <= 3:
        return "income_2_3sm"
    if wage <= 5:
        return "income_3_5sm"
    return "income_5_plus_sm"


@lru_cache(maxsize=1)
def build_pre_treatment_income_medians() -> dict[str, float]:
    pieces = []
    columns = ["ano", "mes", "cbo_2002", "saldo_movimentacao", "salario_mensal"]
    for _path, df in iter_raw_batches(columns):
        df["ano"] = df["ano"].astype(int)
        df["mes"] = df["mes"].astype(int)
        df["periodo_num"] = df["ano"] * 100 + df["mes"]
        df = df[
            (df["periodo_num"] < TREATMENT_PERIOD)
            & (df["saldo_movimentacao"] == 1)
            & df["salario_mensal"].notna()
            & (df["salario_mensal"] > 0)
        ].copy()
        if df.empty:
            continue
        df["cbo_4d"] = valid_cbo_4d(df["cbo_2002"])
        df = df[df["cbo_4d"].notna()].copy()
        df["salario_sm"] = df["salario_mensal"] / df["ano"].map(SALARIO_MINIMO)
        pieces.append(df[["cbo_4d", "salario_sm"]])
    if not pieces:
        raise RuntimeError("Could not build pre-treatment income groups from raw CAGED.")
    wages = pd.concat(pieces, ignore_index=True)
    med = wages.groupby("cbo_4d", observed=True)["salario_sm"].median()
    return med.astype(float).to_dict()


@lru_cache(maxsize=2)
def build_pre_treatment_income_groups(scheme: str = "legacy") -> dict[str, str]:
    medians = build_pre_treatment_income_medians()
    return {
        cbo_4d: group
        for cbo_4d, value in medians.items()
        if (group := income_group_for_median(value, scheme=scheme)) is not None
    }


def build_pre_treatment_income_group_assignments() -> pd.DataFrame:
    """Return an auditable CBO-level crosswalk for both income grouping schemes."""
    medians = build_pre_treatment_income_medians()
    rows = [
        {
            "cbo_4d": str(cbo_4d).zfill(4),
            "median_pre_treatment_wage_sm": float(value),
            "income_group_legacy": income_group_for_median(value, scheme="legacy"),
            "income_group_pnad": income_group_for_median(value, scheme="pnad"),
        }
        for cbo_4d, value in sorted(medians.items())
    ]
    return pd.DataFrame(rows)


def group_series_for_dimension(df: pd.DataFrame, dimension: str) -> pd.Series:
    group = pd.Series(pd.NA, index=df.index, dtype="string")
    if dimension == "age":
        age = pd.to_numeric(df["idade"], errors="coerce")
        group.loc[(age >= 14) & (age <= 24)] = "age_14_24"
        group.loc[(age >= 25) & (age <= 34)] = "age_25_34"
        group.loc[(age >= 35) & (age <= 59)] = "age_35_59"
        group.loc[age >= 60] = "age_60_plus"
        return group
    if dimension == "age_pnad":
        age = pd.to_numeric(df["idade"], errors="coerce")
        group.loc[(age >= 18) & (age <= 24)] = "age_18_24"
        group.loc[(age >= 25) & (age <= 34)] = "age_25_34"
        group.loc[(age >= 35) & (age <= 44)] = "age_35_44"
        group.loc[(age >= 45) & (age <= 54)] = "age_45_54"
        group.loc[(age >= 55) & (age <= 65)] = "age_55_plus"
        return group
    if dimension == "canaries_age":
        age = pd.to_numeric(df["idade"], errors="coerce")
        group.loc[(age >= 22) & (age <= 25)] = "age_22_25"
        group.loc[(age >= 26) & (age <= 30)] = "age_26_30"
        group.loc[(age >= 31) & (age <= 34)] = "age_31_34"
        group.loc[(age >= 35) & (age <= 40)] = "age_35_40"
        group.loc[(age >= 41) & (age <= 49)] = "age_41_49"
        group.loc[age >= 50] = "age_50_plus"
        return group
    if dimension == "sex":
        sex = normalize_codes(df["sexo"])
        group.loc[sex == "1"] = "men"
        group.loc[sex == "3"] = "women"
        return group
    if dimension == "education":
        edu = normalize_codes(df["grau_instrucao"])
        group.loc[edu.isin(["1", "2", "3", "4", "5"])] = "fundamental_or_less"
        group.loc[edu.isin(["6", "7"])] = "high_school"
        group.loc[edu.isin(["8", "9", "10", "11", "80"])] = "higher_education"
        return group
    if dimension in {"race_color", "race_color_b"}:
        mapping = (
            RACE_COLOR_CODE_TO_GROUP
            if dimension == "race_color"
            else RACE_COLOR_B_CODE_TO_GROUP
        )
        mapped = normalize_codes(df["raca_cor"]).map(mapping)
        group.loc[mapped.notna()] = mapped.loc[mapped.notna()]
        return group
    raise ValueError(f"Unsupported micro heterogeneity dimension: {dimension}")


@lru_cache(maxsize=4)
def aggregate_micro_group_pairs(
    dimensions: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    available_dimensions = [
        name
        for name, spec in ALL_MICRO_DIMENSIONS.items()
        if spec["method"] == "micro_group_pair"
    ]
    if dimensions is None:
        micro_dimensions = available_dimensions
    else:
        micro_dimensions = list(dict.fromkeys(dimensions))
        unsupported = sorted(set(micro_dimensions) - set(available_dimensions))
        if unsupported:
            raise ValueError(f"Unsupported micro heterogeneity dimensions: {unsupported}")
        if not micro_dimensions:
            raise ValueError("At least one micro heterogeneity dimension is required.")

    raw_cols = [
        "ano",
        "mes",
        "cbo_2002",
        "saldo_movimentacao",
        "salario_mensal",
    ]
    raw_cols.extend(
        dict.fromkeys(
            MICRO_DIMENSION_SOURCE_COLUMNS[dimension]
            for dimension in micro_dimensions
        )
    )
    actual_pieces = []
    for _path, df in iter_raw_batches(raw_cols):
        cbo_4d = valid_cbo_4d(df["cbo_2002"])
        valid_cbo = cbo_4d.notna()
        if not bool(valid_cbo.any()):
            continue
        ano = pd.to_numeric(df["ano"], errors="coerce").astype("Int16")
        mes = pd.to_numeric(df["mes"], errors="coerce").astype("Int8")
        periodo = ano.astype(str) + "-" + mes.astype(str).str.zfill(2)
        periodo_num = ano.astype("Int32") * 100 + mes.astype("Int32")
        saldo = pd.to_numeric(df["saldo_movimentacao"], errors="coerce")
        is_adm = saldo.eq(1).astype("int8")
        is_des = saldo.eq(-1).astype("int8")
        wage = pd.to_numeric(df["salario_mensal"], errors="coerce")
        salario_adm = pd.Series(np.where(is_adm.eq(1) & wage.gt(0), wage, np.nan), index=df.index)
        for dimension in micro_dimensions:
            membership = group_series_for_dimension(df, dimension)
            valid = valid_cbo & membership.notna()
            if not bool(valid.any()):
                continue
            idx = valid[valid].index
            d = pd.DataFrame(
                {
                    "dimension": dimension,
                    "actual_group": membership.loc[idx].astype("category").to_numpy(),
                    "cbo_4d": cbo_4d.loc[idx].to_numpy(),
                    "ano": ano.loc[idx].astype("int16").to_numpy(),
                    "mes": mes.loc[idx].astype("int8").to_numpy(),
                    "periodo": periodo.loc[idx].to_numpy(),
                    "periodo_num": periodo_num.loc[idx].astype("int32").to_numpy(),
                    "is_adm": is_adm.loc[idx].to_numpy(),
                    "is_des": is_des.loc[idx].to_numpy(),
                    "salario_adm": salario_adm.loc[idx].to_numpy(),
                }
            )
            agg = (
                d.groupby(["dimension", "actual_group", "cbo_4d", "ano", "mes", "periodo", "periodo_num"], observed=True)
                .agg(
                    admissoes=("is_adm", "sum"),
                    desligamentos=("is_des", "sum"),
                    salario_sum=("salario_adm", "sum"),
                    salario_count=("salario_adm", "count"),
                )
                .reset_index()
            )
            actual_pieces.append(agg)
    if not actual_pieces:
        raise RuntimeError("Could not reconstruct heterogeneity pairs from raw CAGED.")
    actual = (
        pd.concat(actual_pieces, ignore_index=True)
        .groupby(["dimension", "actual_group", "cbo_4d", "ano", "mes", "periodo", "periodo_num"], observed=True)
        .agg(
            admissoes=("admissoes", "sum"),
            desligamentos=("desligamentos", "sum"),
            salario_sum=("salario_sum", "sum"),
            salario_count=("salario_count", "sum"),
        )
        .reset_index()
    )
    pair_pieces = []
    keys = ["dimension", "group_id", "subgroup", "cbo_4d", "ano", "mes", "periodo", "periodo_num"]
    for dimension in micro_dimensions:
        spec = ALL_MICRO_DIMENSIONS[dimension]
        dimension_actual = actual[actual["dimension"].eq(dimension)].copy()
        for group_id, _group_label in spec["groups"]:
            target = dimension_actual[dimension_actual["actual_group"].eq(group_id)].copy()
            target["group_id"] = group_id
            target["subgroup"] = "target"
            complement = (
                dimension_actual[~dimension_actual["actual_group"].eq(group_id)]
                .groupby(["dimension", "cbo_4d", "ano", "mes", "periodo", "periodo_num"], observed=True)
                .agg(
                    admissoes=("admissoes", "sum"),
                    desligamentos=("desligamentos", "sum"),
                    salario_sum=("salario_sum", "sum"),
                    salario_count=("salario_count", "sum"),
                )
                .reset_index()
            )
            complement["group_id"] = group_id
            complement["subgroup"] = "complement"
            pair_pieces.extend(
                [
                    target[keys + ["admissoes", "desligamentos", "salario_sum", "salario_count"]],
                    complement[keys + ["admissoes", "desligamentos", "salario_sum", "salario_count"]],
                ]
            )
    out = pd.concat(pair_pieces, ignore_index=True)
    out["saldo"] = pd.to_numeric(out["admissoes"], errors="coerce") - pd.to_numeric(out["desligamentos"], errors="coerce")
    pre = (
        out[out["periodo_num"] < TREATMENT_PERIOD]
        .groupby(["dimension", "group_id", "subgroup", "cbo_4d"], observed=True)["admissoes"]
        .mean()
        .rename("pre_adm_group")
        .reset_index()
    )
    out = out.merge(pre, on=["dimension", "group_id", "subgroup", "cbo_4d"], how="left")
    out["asinh_saldo"] = np.arcsinh(out["saldo"])
    out["saldo_per_pre_adm"] = np.where(out["pre_adm_group"].gt(0), out["saldo"] / out["pre_adm_group"], np.nan)
    flow = pd.to_numeric(out["admissoes"], errors="coerce") + pd.to_numeric(out["desligamentos"], errors="coerce")
    out["saldo_flow_rate"] = np.where(flow.gt(0), out["saldo"] / flow, np.nan)
    out["salario_adm"] = np.where(out["salario_count"] > 0, out["salario_sum"] / out["salario_count"], np.nan)
    out["ln_admissoes"] = np.log(out["admissoes"] + 1)
    out["ln_desligamentos"] = np.log(out["desligamentos"] + 1)
    out["ln_salario_adm"] = np.log(pd.to_numeric(out["salario_adm"], errors="coerce").clip(lower=1))
    out = add_real_wage_measures(out, load_ipca(), admission_col="salario_adm", dismissal_col=None)
    return out


def _add_triple_terms(data: pd.DataFrame, group_indicator: pd.Series) -> pd.DataFrame:
    out = data.copy()
    out["group_indicator"] = group_indicator.astype(int).to_numpy()
    out["post_treat"] = out["post"].astype(int) * out["scenario_treat"].astype(int)
    out["post_group"] = out["post"].astype(int) * out["group_indicator"]
    out["treat_group"] = out["scenario_treat"].astype(int) * out["group_indicator"]
    out["post_treat_group"] = out["post"].astype(int) * out["scenario_treat"].astype(int) * out["group_indicator"]
    if "trend" in out.columns:
        out["trend_treat"] = pd.to_numeric(out["trend"], errors="coerce") * out["scenario_treat"].astype(int)
        out["trend_group"] = pd.to_numeric(out["trend"], errors="coerce") * out["group_indicator"]
        out["trend_treat_group"] = pd.to_numeric(out["trend"], errors="coerce") * out["scenario_treat"].astype(int) * out["group_indicator"]
    return out


def _estimate_triple(data: pd.DataFrame, outcome: str, fe: str) -> dict[str, object]:
    required = [
        outcome,
        "post_treat_group",
        "post_treat",
        "post_group",
        "treat_group",
        "cbo_4d",
        "periodo",
        *CONTROL_COLUMNS,
    ]
    d = data.dropna(subset=[col for col in required if col in data.columns]).copy()
    for col in [outcome, "post_treat_group", "post_treat", "post_group", "treat_group", *CONTROL_COLUMNS]:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")
    d = d.dropna(subset=[outcome, "post_treat_group", *CONTROL_COLUMNS])
    if d.empty or d["cbo_4d"].nunique() < 2 or d["post_treat_group"].nunique() < 2:
        return {
            "result_status": "failed_insufficient_sample",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": int(len(d)),
            "n_cbo": int(d["cbo_4d"].nunique()) if "cbo_4d" in d else 0,
            "error": "Insufficient sample or no triple-interaction variation.",
            "wald_statistic": np.nan,
            "wald_test_method": "wald_test_R_beta_eq_q_chi2",
        }
    formula = f"{outcome} ~ post_treat_group + post_treat + post_group + treat_group + {CONTROL_TERMS} | {fe}"
    try:
        model = pf.feols(formula, data=d, vcov={"CRV1": "cbo_4d"})
        if "post_treat_group" not in model.coef().index:
            raise RuntimeError("post_treat_group was dropped or not estimated.")
        coefficient_names = list(model.coef().index)
        restriction = np.zeros((1, len(coefficient_names)))
        restriction[0, coefficient_names.index("post_treat_group")] = 1.0
        # Public linear-hypothesis API: https://pyfixest.org/reference/estimation.models.feols_.Feols.html#wald-test
        wald = model.wald_test(R=restriction, q=np.zeros(1), distribution="chi2")
        p_value = float(wald.loc["pvalue"])
        return {
            "result_status": "estimated",
            "coef": float(model.coef().loc["post_treat_group"]),
            "se": float(model.se().loc["post_treat_group"]),
            "p_value": p_value,
            "stars": stars(p_value),
            "n_obs": int(len(d)),
            "n_cbo": int(d["cbo_4d"].nunique()),
            "error": "",
            "model": formula,
            "wald_statistic": float(wald.loc["statistic"]),
            "wald_test_method": "wald_test_R_beta_eq_q_chi2",
        }
    except Exception as exc:  # noqa: BLE001 - keep failed rows auditable
        return {
            "result_status": "failed_estimation",
            "coef": np.nan,
            "se": np.nan,
            "p_value": np.nan,
            "stars": "",
            "n_obs": int(len(d)),
            "n_cbo": int(d["cbo_4d"].nunique()),
            "error": str(exc),
            "model": formula,
            "wald_statistic": np.nan,
            "wald_test_method": "wald_test_R_beta_eq_q_chi2",
        }


def _estimate_group_did(data: pd.DataFrame, outcome: str, fe: str) -> dict[str, object]:
    target = data[data["group_indicator"].eq(1)].copy()
    required = [outcome, "post_treat", "cbo_4d", "periodo", *CONTROL_COLUMNS]
    d = target.dropna(subset=[col for col in required if col in target.columns]).copy()
    for col in [outcome, "post_treat", *CONTROL_COLUMNS]:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")
    d = d.dropna(subset=[outcome, "post_treat", *CONTROL_COLUMNS])
    n_cbo = int(d["cbo_4d"].nunique()) if "cbo_4d" in d else 0
    if d.empty or n_cbo < 2 or d["post_treat"].nunique() < 2:
        return {
            "group_result_status": "failed_insufficient_sample",
            "group_coef": np.nan,
            "group_se": np.nan,
            "group_p_value": np.nan,
            "group_stars": "",
            "group_n_obs": int(len(d)),
            "group_n_cbo": n_cbo,
            "group_error": "Insufficient target-group sample or no post-treatment variation.",
            "group_model": "",
        }
    formula = f"{outcome} ~ post_treat + {CONTROL_TERMS} | {fe}"
    try:
        model = pf.feols(formula, data=d, vcov={"CRV1": "cbo_4d"})
        if "post_treat" not in model.coef().index:
            raise RuntimeError("post_treat was dropped or not estimated.")
        p_value = float(model.pvalue().loc["post_treat"])
        return {
            "group_result_status": "estimated",
            "group_coef": float(model.coef().loc["post_treat"]),
            "group_se": float(model.se().loc["post_treat"]),
            "group_p_value": p_value,
            "group_stars": stars(p_value),
            "group_n_obs": int(len(d)),
            "group_n_cbo": n_cbo,
            "group_error": "",
            "group_model": formula,
        }
    except Exception as exc:  # noqa: BLE001 - keep failed rows auditable
        return {
            "group_result_status": "failed_estimation",
            "group_coef": np.nan,
            "group_se": np.nan,
            "group_p_value": np.nan,
            "group_stars": "",
            "group_n_obs": int(len(d)),
            "group_n_cbo": n_cbo,
            "group_error": str(exc),
            "group_model": formula,
        }


def _pretrend_status(data: pd.DataFrame, outcome: str, fe: str) -> tuple[str, float, str]:
    if "trend_treat_group" not in data.columns:
        return "not_available", np.nan, "trend column missing"
    pre = data[data["post"].eq(0)].copy()
    required = [outcome, "trend_treat_group", "trend_treat", "trend_group", "treat_group", *CONTROL_COLUMNS]
    pre = pre.dropna(subset=[col for col in required if col in pre.columns]).copy()
    if pre.empty or pre["trend_treat_group"].nunique() < 2:
        return "not_available", np.nan, "insufficient pre-period variation"
    formula = f"{outcome} ~ trend_treat_group + trend_treat + trend_group + treat_group + {CONTROL_TERMS} | {fe}"
    try:
        model = pf.feols(formula, data=pre, vcov={"CRV1": "cbo_4d"})
        if "trend_treat_group" not in model.coef().index:
            return "not_available", np.nan, "trend_treat_group dropped"
        p_value = float(model.pvalue().loc["trend_treat_group"])
        if p_value > 0.10:
            return "pass", p_value, ""
        if p_value < 0.05:
            return "fail", p_value, ""
        return "warning", p_value, ""
    except Exception as exc:  # noqa: BLE001
        return "not_available", np.nan, str(exc)


def _group_pretrend_status(data: pd.DataFrame, outcome: str, fe: str) -> tuple[str, float, str]:
    if "trend_treat" not in data.columns:
        return "not_available", np.nan, "trend column missing"
    pre = data[data["post"].eq(0) & data["group_indicator"].eq(1)].copy()
    required = [outcome, "trend_treat", "cbo_4d", "periodo", *CONTROL_COLUMNS]
    pre = pre.dropna(subset=[col for col in required if col in pre.columns]).copy()
    if pre.empty or pre["cbo_4d"].nunique() < 2 or pre["trend_treat"].nunique() < 2:
        return "not_available", np.nan, "insufficient target-group pre-period variation"
    formula = f"{outcome} ~ trend_treat + {CONTROL_TERMS} | {fe}"
    try:
        model = pf.feols(formula, data=pre, vcov={"CRV1": "cbo_4d"})
        if "trend_treat" not in model.coef().index:
            return "not_available", np.nan, "trend_treat dropped"
        p_value = float(model.pvalue().loc["trend_treat"])
        if p_value > 0.10:
            return "pass", p_value, ""
        if p_value < 0.05:
            return "fail", p_value, ""
        return "warning", p_value, ""
    except Exception as exc:  # noqa: BLE001
        return "not_available", np.nan, str(exc)


def _power_status(data: pd.DataFrame) -> str:
    treated_target = data[(data["scenario_treat"].eq(1)) & (data["group_indicator"].eq(1))]["cbo_4d"].nunique()
    control_target = data[(data["scenario_treat"].eq(0)) & (data["group_indicator"].eq(1))]["cbo_4d"].nunique()
    if treated_target >= 20 and control_target >= 50:
        return "adequate"
    if treated_target >= 10 and control_target >= 25:
        return "limited"
    return "thin"


def _group_power(data: pd.DataFrame, outcome: str) -> tuple[str, int, int]:
    target = data[data["group_indicator"].eq(1) & data[outcome].notna()].copy()
    if {"admissoes", "desligamentos"}.issubset(target.columns):
        has_flow = pd.to_numeric(target["admissoes"], errors="coerce").fillna(0).gt(0) | pd.to_numeric(
            target["desligamentos"], errors="coerce"
        ).fillna(0).gt(0)
        supported_cbo = target.loc[has_flow, "cbo_4d"].unique()
        target = target[target["cbo_4d"].isin(supported_cbo)]
    treated = int(target[target["scenario_treat"].eq(1)]["cbo_4d"].nunique())
    control = int(target[target["scenario_treat"].eq(0)]["cbo_4d"].nunique())
    if treated >= 20 and control >= 50:
        return "adequate", treated, control
    if treated >= 10 and control >= 25:
        return "limited", treated, control
    return "thin", treated, control


def _base_controls(panel: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "cbo_4d",
        "ano",
        "mes",
        "periodo",
        "periodo_num",
        "post",
        "trend",
        *CONTROL_COLUMNS,
    ]
    return panel[cols].copy()


def estimate_heterogeneity(
    panel_with_roles: pd.DataFrame,
    outcomes: dict[str, str] | None = None,
    dimensions: dict[str, dict[str, object]] | None = None,
    micro_pairs: pd.DataFrame | None = None,
) -> pd.DataFrame:
    outcomes = outcomes or MAIN_OUTCOMES
    selected_dimensions = dimensions or DIMENSIONS
    controls = _base_controls(panel_with_roles)
    role_cols = panel_with_roles[["cbo_4d", "scenario_treat"]].drop_duplicates("cbo_4d")
    controls = controls.merge(role_cols, on="cbo_4d", how="inner")
    results: list[dict[str, object]] = []

    for dimension, spec in selected_dimensions.items():
        if spec["method"] != "pre_treatment_cbo_income":
            continue
        income_scheme = str(spec.get("income_scheme", "legacy"))
        income_groups = build_pre_treatment_income_groups(income_scheme)
        income_base = panel_with_roles.copy()
        income_base["income_group"] = income_base["cbo_4d"].map(income_groups)
        for group_id, group_label in spec["groups"]:
            data = _add_triple_terms(income_base, income_base["income_group"].eq(group_id))
            for outcome, outcome_label in outcomes.items():
                est = _estimate_triple(data, outcome, "cbo_4d + periodo")
                pre_status, pre_p, pre_error = _pretrend_status(data, outcome, "cbo_4d + periodo")
                group_est = _estimate_group_did(data, outcome, "cbo_4d + periodo")
                group_pre_status, group_pre_p, group_pre_error = _group_pretrend_status(
                    data, outcome, "cbo_4d + periodo"
                )
                group_power, group_treated_cbo, group_control_cbo = _group_power(data, outcome)
                results.append(
                    {
                        "dimension": dimension,
                        "panel": spec["panel"],
                        "group_id": group_id,
                        "group_label": group_label,
                        "comparison": "target_vs_complement",
                        "outcome": outcome,
                        "outcome_label": outcome_label,
                        "power_status": _power_status(data),
                        "pretrend_status": pre_status,
                        "pretrend_p_value": pre_p,
                        "pretrend_error": pre_error,
                        "group_pretrend_status": group_pre_status,
                        "group_pretrend_p_value": group_pre_p,
                        "group_pretrend_error": group_pre_error,
                        "group_power_status": group_power,
                        "group_treated_cbo": group_treated_cbo,
                        "group_control_cbo": group_control_cbo,
                        **est,
                        **group_est,
                    }
                )

    micro_dimensions = {
        dimension: spec
        for dimension, spec in selected_dimensions.items()
        if spec["method"] == "micro_group_pair"
    }
    if not micro_dimensions:
        return pd.DataFrame(results)

    micro = aggregate_micro_group_pairs() if micro_pairs is None else micro_pairs
    subgroup_frame = pd.DataFrame({"subgroup": ["target", "complement"]})
    micro_outcomes = [outcome for outcome in outcomes if outcome in micro.columns]
    for dimension, spec in micro_dimensions.items():
        for group_id, group_label in spec["groups"]:
            base = controls.assign(_cross_key=1).merge(subgroup_frame.assign(_cross_key=1), on="_cross_key").drop(columns="_cross_key")
            raw = micro[(micro["dimension"].eq(dimension)) & (micro["group_id"].eq(group_id))].copy()
            data = base.merge(
                raw[
                    [
                        "cbo_4d",
                        "ano",
                        "mes",
                        "subgroup",
                        "admissoes",
                        "desligamentos",
                        *micro_outcomes,
                    ]
                ],
                on=["cbo_4d", "ano", "mes", "subgroup"],
                how="left",
            )
            for col in ["admissoes", "desligamentos", "ln_admissoes", "ln_desligamentos"]:
                if col in data.columns:
                    data[col] = data[col].fillna(0)
            data = _add_triple_terms(data, data["subgroup"].eq("target"))
            for outcome, outcome_label in outcomes.items():
                est = _estimate_triple(data, outcome, "cbo_4d + periodo + subgroup")
                pre_status, pre_p, pre_error = _pretrend_status(data, outcome, "cbo_4d + periodo + subgroup")
                group_est = _estimate_group_did(data, outcome, "cbo_4d + periodo")
                group_pre_status, group_pre_p, group_pre_error = _group_pretrend_status(
                    data, outcome, "cbo_4d + periodo"
                )
                group_power, group_treated_cbo, group_control_cbo = _group_power(data, outcome)
                target_with_rows = data[
                    data["subgroup"].eq("target") & ((data["admissoes"] > 0) | (data["desligamentos"] > 0))
                ]
                results.append(
                    {
                        "dimension": dimension,
                        "panel": spec["panel"],
                        "group_id": group_id,
                        "group_label": group_label,
                        "comparison": "target_vs_complement",
                        "outcome": outcome,
                        "outcome_label": outcome_label,
                        "target_cbo_with_flows": int(target_with_rows["cbo_4d"].nunique()),
                        "power_status": _power_status(data),
                        "pretrend_status": pre_status,
                        "pretrend_p_value": pre_p,
                        "pretrend_error": pre_error,
                        "group_pretrend_status": group_pre_status,
                        "group_pretrend_p_value": group_pre_p,
                        "group_pretrend_error": group_pre_error,
                        "group_power_status": group_power,
                        "group_treated_cbo": group_treated_cbo,
                        "group_control_cbo": group_control_cbo,
                        **est,
                        **group_est,
                    }
                )
    return pd.DataFrame(results)
