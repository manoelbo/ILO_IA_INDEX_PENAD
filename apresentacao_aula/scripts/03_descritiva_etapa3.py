from __future__ import annotations

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


INPUT = DATA_OUTPUT / "painel_caged_municipio_anatel_v2.parquet"


def fmt_millions(value: float) -> str:
    return f"{value / 1_000_000:.1f} milhões".replace(".", ",")


def make_connectivity_split(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    variables = [
        ("admissoes", "Admissões"),
        ("salario_real_adm", "Salário real admissão"),
        ("idade_media_adm", "Idade média"),
        ("pct_mulher_adm", "% mulheres"),
        ("pct_superior_adm", "% superior"),
        ("exposure_score_2d", "Score ILO"),
        ("penetracao_bl", "Banda larga fixa"),
        ("pct_fibra_pre", "Fibra"),
    ]
    for var, label in variables:
        if var not in df.columns:
            continue
        low = df.loc[df["alta_conectividade"] == 0, var].dropna()
        high = df.loc[df["alta_conectividade"] == 1, var].dropna()
        scale = 100 if var.startswith("pct_") or var == "penetracao_bl" else 1
        rows.append(
            {
                "Variável": label,
                "Baixa conect.": low.mean() * scale,
                "Alta conect.": high.mean() * scale,
                "Diferença": (high.mean() - low.mean()) * scale,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    columns = [
        "cbo_4d",
        "id_municipio",
        "periodo",
        "sigla_uf",
        "post",
        "admissoes",
        "desligamentos",
        "saldo",
        "salario_real_adm",
        "ln_salario_real_adm",
        "idade_media_adm",
        "pct_mulher_adm",
        "pct_superior_adm",
        "pct_jovem_adm",
        "exposure_score_2d",
        "alta_exp",
        "penetracao_bl",
        "pct_fibra_pre",
        "alta_conectividade",
        "pib_per_capita",
        "populacao",
    ]
    df = pd.read_parquet(INPUT, columns=columns)
    total_movimentacoes = df["admissoes"].sum() + df["desligamentos"].sum()

    rows = [
        ("Fonte", "Novo CAGED + Anatel + IBGE + ILO WP140"),
        ("Unidade do painel", "Município × ocupação × mês"),
        ("Janela analítica", f"{df['periodo'].min()} a {df['periodo'].max()}"),
        ("Movimentações CAGED agregadas", fmt_millions(total_movimentacoes)),
        ("Células município-ocupação-mês", fmt_int(len(df))),
        ("Municípios", fmt_int(df["id_municipio"].nunique())),
        ("Ocupações CBO 4d", fmt_int(df["cbo_4d"].nunique())),
        ("UFs", fmt_int(df["sigla_uf"].nunique())),
        ("Alta conectividade", fmt_pct(df.groupby("id_municipio")["alta_conectividade"].first().mean(), 1)),
    ]
    write_key_value_table(rows, "tab_amostra_etapa3")

    variables = [
        ("admissoes", "Admissões", "vagas/mês"),
        ("desligamentos", "Desligamentos", "vagas/mês"),
        ("saldo", "Saldo líquido", "vagas/mês"),
        ("salario_real_adm", "Salário real admissão", "R$ dez/2024"),
        ("idade_media_adm", "Idade média", "anos"),
        ("pct_mulher_adm", "Mulheres nas admissões", "%"),
        ("pct_superior_adm", "Superior nas admissões", "%"),
        ("pct_jovem_adm", "Jovens nas admissões", "%"),
        ("exposure_score_2d", "Score ILO", "0-1"),
        ("penetracao_bl", "Penetração banda larga", "%"),
        ("pct_fibra_pre", "Fibra no pré", "%"),
        ("pib_per_capita", "PIB per capita", "R$"),
    ]
    stats = descriptive_table(
        df,
        variables,
        percent_vars={"pct_mulher_adm", "pct_superior_adm", "pct_jovem_adm", "penetracao_bl", "pct_fibra_pre"},
    )
    save_table_outputs(format_descriptive_for_slides(stats, digits=2), "tab_descritiva_etapa3")

    split = make_connectivity_split(df)
    split_slide = split.copy()
    for col in ["Baixa conect.", "Alta conect.", "Diferença"]:
        split_slide[col] = split_slide[col].map(lambda v: fmt_decimal(v, 2))
    save_table_outputs(split_slide, "tab_split_conectividade_etapa3")


if __name__ == "__main__":
    main()
