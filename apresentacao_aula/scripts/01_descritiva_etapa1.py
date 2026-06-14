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


INPUT = DATA_OUTPUT / "pnad_ilo_merged.csv"


def main() -> None:
    usecols = [
        "sigla_uf",
        "idade",
        "sexo_texto",
        "raca_agregada",
        "nivel_instrucao",
        "cod_ocupacao",
        "formal",
        "tem_renda",
        "rendimento_habitual",
        "rendimento_winsor",
        "horas_habituais",
        "peso",
        "exposure_score",
        "exposure_gradient",
        "match_level",
    ]
    df = pd.read_csv(INPUT, usecols=usecols)

    df["mulher"] = (df["sexo_texto"] == "Mulher").astype(float)
    df["branca"] = (df["raca_agregada"] == "Branca").astype(float)
    df["negra"] = (df["raca_agregada"] == "Negra").astype(float)
    df["alta_exposicao"] = df["exposure_gradient"].isin(
        ["Exposed: Gradient 3", "Exposed: Gradient 4"]
    ).astype(float)
    df["log_rendimento"] = np.log(df["rendimento_winsor"].where(df["rendimento_winsor"] > 0))

    peso = df["peso"]
    pop_total = peso.sum()
    score_classificado = df["exposure_score"].notna()
    match_4d = df["match_level"].eq("4-digit")

    rows = [
        ("Fonte", "PNADc 3T/2025 (IBGE) + ILO WP140"),
        ("Observações na amostra", fmt_int(len(df))),
        ("População representada", f"{fmt_decimal(pop_total / 1_000_000, 1)} milhões"),
        ("Unidades federativas", fmt_int(df["sigla_uf"].nunique())),
        ("Ocupações COD", fmt_int(df["cod_ocupacao"].nunique())),
        ("Cobertura de score", fmt_pct(peso[score_classificado].sum() / pop_total, 1)),
        ("Match a 4 dígitos", fmt_pct(peso[match_4d].sum() / pop_total, 1)),
        (
            "Alta exposição (G3-G4)",
            f"{fmt_decimal((peso * df['alta_exposicao']).sum() / 1_000_000, 1)} milhões",
        ),
    ]
    write_key_value_table(rows, "tab_amostra_etapa1")

    variables = [
        ("exposure_score", "Score de exposição ILO", "0-1"),
        ("alta_exposicao", "Alta exposição (G3-G4)", "%"),
        ("idade", "Idade", "anos"),
        ("nivel_instrucao", "Nível de instrução", "categoria"),
        ("rendimento_habitual", "Rendimento habitual", "R$"),
        ("log_rendimento", "Log rendimento habitual", "log R$"),
        ("horas_habituais", "Horas habituais", "horas/sem."),
        ("mulher", "Mulheres", "%"),
        ("branca", "Brancos", "%"),
        ("formal", "Trabalhadores formais", "%"),
    ]
    stats = descriptive_table(
        df,
        variables,
        weight="peso",
        percent_vars={"alta_exposicao", "mulher", "branca", "formal"},
    )
    save_table_outputs(format_descriptive_for_slides(stats, digits=2), "tab_descritiva_etapa1")


if __name__ == "__main__":
    main()

