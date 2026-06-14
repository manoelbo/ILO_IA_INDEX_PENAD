"""
Tabela de exposicao a IA generativa por setor economico (PNADC 3T/2025 + OIT WP140).

CORRECAO IMPORTANTE (vs versao 1):
A coluna 'setor_agregado' da base 'pnad_ilo_merged.csv' tem bug de mapeamento.
A PNADC usa codigos CNAE-Domiciliar 2.0 (V4013) de 5 digitos onde a Secao A
(Agropecuaria, codigos 01xxx-03xxx) e a Secao B (Ind. Extrativa, 05xxx-09xxx)
tem zero a esquerda. Esses zeros foram perdidos quando o codigo foi salvo
como int em etapa_1a, fazendo '01101' (Cultivo de arroz) virar '1101' e ser
mapeado para 'Ind. Transformacao' (porque CNAE 2.0 codigo 11 = Bebidas).

Este script refaz 'setor_agregado' do zero usando o codigo completo (5 digitos
com zero-padding), com mapeamento por SECAO da CNAE-Domiciliar 2.0.

Impacto:
  - 'Agropecuaria' aparece com ~8M trabalhadores (antes ausente)
  - 'Ind. Extrativa' aparece com ~0.6M (antes ausente)
  - 'Ind. Transformacao' reduzida de 18.7M para ~14M (antes inflada pelo agro)

Para cada setor calcula:
  - Volume total (milhoes) e participacao no total Brasil
  - Volume + % em cada um dos 3 grupos (baixa / moderada / alta)
  - Volume + % de "expostos" (qualquer gradiente 1-4)
  - Score medio ponderado de exposicao (weighted mean por peso amostral)

Saidas:
  - outputs/tables/tab_setor_economico_exposicao.csv
  - outputs/tables/tab_setor_economico_exposicao.md

Uso:
  python src/scripts/export_tab_setor_economico_exposicao.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_INPUT = ROOT / "data" / "output" / "pnad_ilo_merged.csv"
DIR_TABLES = ROOT / "outputs" / "tables"

# Mapeamento por SECAO da CNAE-Domiciliar 2.0 (2 primeiros digitos do codigo
# de 5 digitos com zero-padding). Reproduz o CNAE_SETOR_MAP do etapa_1a, mas
# aplicado corretamente apos zero-padding.
CNAE_SECAO_TO_SETOR = {
    # Secao A - Agropecuaria
    "01": "Agropecuária", "02": "Agropecuária", "03": "Agropecuária",
    # Secao B - Industria Extrativa
    "05": "Ind. Extrativa", "06": "Ind. Extrativa", "07": "Ind. Extrativa",
    "08": "Ind. Extrativa", "09": "Ind. Extrativa",
    # Secao C - Industria de Transformacao
    **{f"{n:02d}": "Ind. Transformação" for n in range(10, 34)},
    # Secao D+E - Utilidades (eletricidade, agua, esgoto, residuos)
    **{f"{n:02d}": "Utilidades" for n in [35, 36, 37, 38, 39]},
    # Secao F - Construcao
    "41": "Construção", "42": "Construção", "43": "Construção",
    # Secao G - Comercio
    "45": "Comércio", "46": "Comércio", "47": "Comércio", "48": "Comércio",
    # Secao H - Transporte e armazenagem
    **{f"{n:02d}": "Transporte" for n in [49, 50, 51, 52, 53]},
    # Secao I - Alojamento e Alimentacao
    "55": "Alojamento e Alimentação", "56": "Alojamento e Alimentação",
    # Secao J - Informacao e Comunicacao
    **{f"{n:02d}": "Informação e Comunicação" for n in [58, 59, 60, 61, 62, 63]},
    # Secao K - Financas e Seguros
    "64": "Finanças e Seguros", "65": "Finanças e Seguros", "66": "Finanças e Seguros",
    # Secao L - Atividades Imobiliarias
    "68": "Atividades Imobiliárias",
    # Secao M - Atividades Profissionais, Cientificas e Tecnicas
    **{f"{n:02d}": "Serviços Profissionais" for n in [69, 70, 71, 72, 73, 74, 75]},
    # Secao N - Atividades Administrativas e Servicos Complementares
    **{f"{n:02d}": "Serviços Administrativos" for n in [77, 78, 79, 80, 81, 82]},
    # Secao O - Administracao Publica
    "84": "Administração Pública",
    # Secao P - Educacao
    "85": "Educação",
    # Secao Q - Saude e Servicos Sociais
    "86": "Saúde", "87": "Saúde", "88": "Saúde",
    # Secao R - Artes, Cultura, Esporte e Recreacao
    **{f"{n:02d}": "Artes e Cultura" for n in [90, 91, 92, 93]},
    # Secao S - Outras Atividades de Servicos
    **{f"{n:02d}": "Outros Serviços" for n in [94, 95, 96]},
    # Secao T - Servicos Domesticos
    "97": "Serviços Domésticos",
    # Secao U - Organismos Internacionais (raro)
    "99": "Outros Serviços",
}

GRADIENT_TO_GROUP = {
    "Not Exposed": "baixa",
    "Minimal Exposure": "baixa",
    "Exposed: Gradient 1": "moderada",
    "Exposed: Gradient 2": "moderada",
    "Exposed: Gradient 3": "alta",
    "Exposed: Gradient 4": "alta",
}

GRUPOS = ["baixa", "moderada", "alta"]
GRADIENTES_EXPOSTOS = {
    "Exposed: Gradient 1",
    "Exposed: Gradient 2",
    "Exposed: Gradient 3",
    "Exposed: Gradient 4",
}


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    w = weights.to_numpy(dtype=float)
    v = values.to_numpy(dtype=float)
    mask = ~np.isnan(v) & ~np.isnan(w) & (w > 0)
    if not mask.any():
        return float("nan")
    return float(np.average(v[mask], weights=w[mask]))


def load_and_aggregate() -> pd.DataFrame:
    df = pd.read_csv(DATA_INPUT)
    df = df[df["exposure_gradient"].ne("Sem classificação")].copy()
    df["grupo3"] = df["exposure_gradient"].map(GRADIENT_TO_GROUP)
    if df["grupo3"].isna().any():
        faltando = df.loc[df["grupo3"].isna(), "exposure_gradient"].unique().tolist()
        raise ValueError(f"Categorias nao mapeadas: {faltando}")

    # CORRECAO: refaz setor_agregado a partir do grupamento_atividade com
    # zero-padding correto (5 digitos), evitando o bug de mapeamento original.
    df["ga5"] = df["grupamento_atividade"].astype(int).astype(str).str.zfill(5)
    df["secao_cnae"] = df["ga5"].str[:2]
    df["setor_agregado_corrigido"] = df["secao_cnae"].map(CNAE_SECAO_TO_SETOR).fillna("Outros Serviços")

    total_brasil = float(df["peso"].sum())

    rows = []
    for setor, sub in df.groupby("setor_agregado_corrigido"):
        peso_total = float(sub["peso"].sum())
        row: dict[str, object] = {
            "setor": setor,
            "vol_total_milhoes": peso_total / 1e6,
            "pct_brasil": peso_total / total_brasil * 100,
        }

        for g in GRUPOS:
            peso_g = float(sub.loc[sub["grupo3"].eq(g), "peso"].sum())
            row[f"vol_{g}_milhoes"] = peso_g / 1e6
            row[f"pct_{g}"] = (peso_g / peso_total * 100) if peso_total > 0 else 0.0

        peso_exposto = float(sub.loc[sub["exposure_gradient"].isin(GRADIENTES_EXPOSTOS), "peso"].sum())
        row["vol_exposto_milhoes"] = peso_exposto / 1e6
        row["pct_exposto"] = (peso_exposto / peso_total * 100) if peso_total > 0 else 0.0

        row["exposicao_media_score"] = weighted_mean(sub["exposure_score"], sub["peso"])

        rows.append(row)

    out = pd.DataFrame(rows)
    out = out.sort_values("exposicao_media_score", ascending=False).reset_index(drop=True)

    soma_pct = out[[f"pct_{g}" for g in GRUPOS]].sum(axis=1)
    if not np.allclose(soma_pct, 100.0, atol=0.05):
        raise AssertionError(f"Somatorio das % por setor nao bate 100: min={soma_pct.min()}, max={soma_pct.max()}")

    return out


def export_csv(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cols_order = [
        "setor",
        "vol_total_milhoes", "pct_brasil",
        "exposicao_media_score",
        "vol_baixa_milhoes", "pct_baixa",
        "vol_moderada_milhoes", "pct_moderada",
        "vol_alta_milhoes", "pct_alta",
        "vol_exposto_milhoes", "pct_exposto",
    ]
    df_out = df[cols_order].copy()
    df_out.to_csv(output_path, index=False, float_format="%.4f", encoding="utf-8")


def export_markdown(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Exposicao a IA generativa por setor economico — PNADC 3T/2025",
        "",
        "Universo: ocupados classificaveis (~96M, excluindo 'Sem classificacao' do gradiente).",
        "",
        "Setores: 19 categorias derivadas das **Secoes A-T da CNAE-Domiciliar 2.0** (IBGE),",
        "agrupadas a partir da variavel V4013 da PNADC com zero-padding de 5 digitos.",
        "",
        "Grupos OIT: Baixa = Not Exposed + Minimal Exposure; Moderada = Gradients 1+2; Alta = Gradients 3+4.",
        "Expostos (qualquer) = Gradients 1+2+3+4.",
        "Ordenado por score medio de exposicao (ponderado pelo peso amostral) — decrescente.",
        "",
        "| Setor | Total (M) | % BR | Score medio | Baixa (M) | Baixa (%) | Moderada (M) | Moderada (%) | Alta (M) | Alta (%) | Expostos (M) | Expostos (%) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in df.iterrows():
        lines.append(
            "| {setor} | {vt:.2f} | {pbr:.1f} | {sc:.3f} "
            "| {vb:.2f} | {pb:.1f} | {vm:.2f} | {pm:.1f} | {va:.2f} | {pa:.1f} "
            "| {ve:.2f} | {pe:.1f} |".format(
                setor=row["setor"],
                vt=row["vol_total_milhoes"],
                pbr=row["pct_brasil"],
                sc=row["exposicao_media_score"],
                vb=row["vol_baixa_milhoes"], pb=row["pct_baixa"],
                vm=row["vol_moderada_milhoes"], pm=row["pct_moderada"],
                va=row["vol_alta_milhoes"], pa=row["pct_alta"],
                ve=row["vol_exposto_milhoes"], pe=row["pct_exposto"],
            )
        )

    lines += [
        "",
        "## Glossario das colunas",
        "",
        "- `Total (M)`: trabalhadores ocupados no setor, em milhoes.",
        "- `% BR`: participacao do setor no total de ocupados classificaveis do Brasil.",
        "- `Score medio`: media ponderada (pelo peso amostral) do score continuo de exposicao OIT (0 a 1).",
        "- `Baixa`: Not Exposed + Minimal Exposure (ocupacoes pouco/nada expostas).",
        "- `Moderada`: Gradients 1 + 2 (exposicao parcial; tarefas potencialmente complementadas pela IA).",
        "- `Alta`: Gradients 3 + 4 (exposicao alta e consistente; tarefas potencialmente automatizadas).",
        "- `Expostos`: soma de todos os trabalhadores em algum gradiente 1-4 (excluindo nao-expostos e exposicao minima).",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print(f"[1/2] Carregando e agregando dados de {DATA_INPUT.name}...")
    df = load_and_aggregate()
    print(f"    -> {len(df)} setores. Total: {df['vol_total_milhoes'].sum():.1f}M ocupados classificaveis.")

    print("[2/2] Exportando tabelas CSV e markdown...")
    out_csv = DIR_TABLES / "tab_setor_economico_exposicao.csv"
    out_md = DIR_TABLES / "tab_setor_economico_exposicao.md"
    export_csv(df, out_csv)
    export_markdown(df, out_md)
    print(f"    -> {out_csv.name}")
    print(f"    -> {out_md.name}")

    print("\nTop 5 setores por score medio de exposicao:")
    print(df.head(5)[["setor", "vol_total_milhoes", "exposicao_media_score", "pct_alta", "pct_exposto"]].to_string(index=False))

    print("\nBottom 3 setores por score medio de exposicao:")
    print(df.tail(3)[["setor", "vol_total_milhoes", "exposicao_media_score", "pct_alta", "pct_exposto"]].to_string(index=False))

    print("\nFeito.")


if __name__ == "__main__":
    main()
