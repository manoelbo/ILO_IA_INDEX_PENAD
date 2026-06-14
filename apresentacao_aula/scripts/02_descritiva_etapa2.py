from __future__ import annotations

import numpy as np
import pandas as pd

from _common import (
    DATA_OUTPUT,
    descriptive_table,
    fmt_decimal,
    fmt_int,
    fmt_pct,
    format_descriptive_for_slides,
    save_table_outputs,
    write_key_value_table,
)


INPUT = DATA_OUTPUT / "painel_caged_did_ready.parquet"
BALANCE_THRESHOLD = 0.25


def normalized_difference(treated: pd.Series, control: pd.Series) -> float:
    pooled_std = np.sqrt((treated.var() + control.var()) / 2)
    return float((treated.mean() - control.mean()) / pooled_std) if pooled_std > 0 else np.nan


def fmt_millions(value: float) -> str:
    return f"{value / 1_000_000:.1f} milhões".replace(".", ",")


def make_balance_table(df: pd.DataFrame) -> pd.DataFrame:
    df_pre = df[df["post"] == 0].copy()
    ocup_pre = (
        df_pre.groupby("cbo_4d")
        .agg(
            alta_exp=("alta_exp", "first"),
            admissoes_media=("admissoes", "mean"),
            desligamentos_media=("desligamentos", "mean"),
            saldo_media=("saldo", "mean"),
            salario_media=("salario_medio_adm", "mean"),
            idade_media=("idade_media_adm", "mean"),
            pct_mulher=("pct_mulher_adm", "mean"),
            pct_superior=("pct_superior_adm", "mean"),
        )
        .reset_index()
    )

    covariates = [
        ("admissoes_media", "Admissões"),
        ("desligamentos_media", "Desligamentos"),
        ("saldo_media", "Saldo líquido"),
        ("salario_media", "Salário médio (R$)"),
        ("idade_media", "Idade média"),
        ("pct_mulher", "% mulheres"),
        ("pct_superior", "% superior"),
    ]
    rows: list[dict[str, object]] = []
    for var, label in covariates:
        treated = ocup_pre.loc[ocup_pre["alta_exp"] == 1, var].dropna()
        control = ocup_pre.loc[ocup_pre["alta_exp"] == 0, var].dropna()
        std_diff = normalized_difference(treated, control)
        scale = 100 if var.startswith("pct_") else 1
        rows.append(
            {
                "Variável": label,
                "Controle": control.mean() * scale,
                "Tratamento": treated.mean() * scale,
                "Dif. norm.": std_diff,
                "Balanceado": "Sim" if abs(std_diff) < BALANCE_THRESHOLD else "Não",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    columns = [
        "cbo_4d",
        "periodo",
        "post",
        "admissoes",
        "desligamentos",
        "saldo",
        "ln_admissoes",
        "ln_desligamentos",
        "salario_medio_adm",
        "salario_sm",
        "ln_salario_adm",
        "ln_salario_sm",
        "idade_media_adm",
        "pct_mulher_adm",
        "pct_superior_adm",
        "exposure_score_2d",
        "alta_exp",
    ]
    df = pd.read_parquet(INPUT, columns=columns)

    treated_occ = df.groupby("cbo_4d")["alta_exp"].first()
    total_movimentacoes = df["admissoes"].sum() + df["desligamentos"].sum()
    rows = [
        ("Fonte", "Novo CAGED + ILO WP140"),
        ("Janela analítica", f"{df['periodo'].min()} a {df['periodo'].max()}"),
        ("Movimentações CAGED agregadas", fmt_millions(total_movimentacoes)),
        ("Células ocupação-mês do painel", fmt_int(len(df))),
        ("Ocupações CBO 4d", fmt_int(df["cbo_4d"].nunique())),
        ("Períodos mensais", fmt_int(df["periodo"].nunique())),
        ("Ocupações tratadas", fmt_int(treated_occ.sum())),
        ("Participação tratada", fmt_pct(treated_occ.mean(), 1)),
        ("Evento", "Lançamento do ChatGPT (nov/2022)"),
    ]
    write_key_value_table(rows, "tab_amostra_etapa2")

    variables = [
        ("admissoes", "Admissões", "vagas/mês"),
        ("desligamentos", "Desligamentos", "vagas/mês"),
        ("saldo", "Saldo líquido", "vagas/mês"),
        ("salario_medio_adm", "Salário admissão", "R$"),
        ("salario_sm", "Salário admissão", "SM"),
        ("idade_media_adm", "Idade média", "anos"),
        ("pct_mulher_adm", "Mulheres nas admissões", "%"),
        ("pct_superior_adm", "Superior nas admissões", "%"),
        ("exposure_score_2d", "Score ILO", "0-1"),
    ]
    stats = descriptive_table(
        df,
        variables,
        percent_vars={"pct_mulher_adm", "pct_superior_adm"},
    )
    save_table_outputs(format_descriptive_for_slides(stats, digits=2), "tab_descritiva_etapa2")

    balance = make_balance_table(df)
    balance_slide = balance.copy()
    for col in ["Controle", "Tratamento", "Dif. norm."]:
        balance_slide[col] = balance_slide[col].map(lambda v: fmt_decimal(v, 2))
    save_table_outputs(balance_slide, "tab_balanco_etapa2")


if __name__ == "__main__":
    main()
