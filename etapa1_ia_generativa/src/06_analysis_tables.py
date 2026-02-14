"""
Script 06: Geração de tabelas descritivas
Entrada: data/output/pnad_ilo_merged.csv
Saída: outputs/tables/tabela{1..10}_*.csv + .tex
"""

import logging
import pandas as pd
import numpy as np
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *
from src.utils.weighted_stats import (
    weighted_mean, weighted_std, weighted_quantile, gini_coefficient
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '06_tables.log', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_data():
    path = DATA_OUTPUT / "pnad_ilo_merged.csv"
    logger.info(f"Carregando: {path}")
    df = pd.read_csv(path)
    logger.info(f"Observações: {len(df):,} | Colunas: {df.shape[1]}")
    return df


def save_table(df_table, name, caption=None):
    csv_path = OUTPUTS_TABLES / f"{name}.csv"
    tex_path = OUTPUTS_TABLES / f"{name}.tex"
    df_table.to_csv(csv_path, index=True)
    if caption:
        df_table.to_latex(tex_path, caption=caption, escape=False)
    else:
        df_table.to_latex(tex_path, escape=False)
    logger.info(f"  Salvo: {csv_path.name}, {tex_path.name}")


# =========================================================================
# Tabela 1 — Exposição por Grande Grupo Ocupacional
# =========================================================================
def table1_exposicao_grupos(df):
    logger.info("\n=== Tabela 1: Exposição por Grande Grupo ===")
    mask = df['exposure_score'].notna() & df['grande_grupo'].notna()
    dfs = df[mask]

    rows = []
    for grupo in sorted(dfs['grande_grupo'].unique()):
        sub = dfs[dfs['grande_grupo'] == grupo]
        rows.append({
            'Grande Grupo': grupo,
            'Exposição Média': weighted_mean(sub['exposure_score'], sub['peso']),
            'Desvio-Padrão': weighted_std(sub['exposure_score'], sub['peso']),
            'Trabalhadores (milhões)': sub['peso'].sum() / 1e6,
            '% Força de Trabalho': sub['peso'].sum() / dfs['peso'].sum() * 100,
        })

    result = pd.DataFrame(rows).sort_values('Exposição Média', ascending=False)
    result = result.set_index('Grande Grupo')
    result = result.round(3)

    for _, row in result.iterrows():
        logger.info(f"  {row.name}: {row['Exposição Média']:.3f} "
                     f"({row['Trabalhadores (milhões)']:.1f}M)")

    save_table(result, 'tabela1_exposicao_grupos',
               'Exposição à IA Generativa por Grande Grupo Ocupacional')
    return result


# =========================================================================
# Tabela 2 — Perfil Socioeconômico por Quintil de Exposição
# =========================================================================
def table2_perfil_quintis(df):
    logger.info("\n=== Tabela 2: Perfil por Quintil ===")
    mask = df['quintil_exposure'].notna()
    dfs = df[mask]

    rows = []
    for quintil in QUINTIL_ORDER:
        sub = dfs[dfs['quintil_exposure'] == quintil]
        if len(sub) == 0:
            continue
        sub_renda = sub[sub['tem_renda'] == 1]
        rows.append({
            'Quintil': quintil,
            'Rendimento Médio (R$)': weighted_mean(
                sub_renda['rendimento_habitual'], sub_renda['peso']
            ) if len(sub_renda) > 0 else np.nan,
            'Rendimento Mediano (R$)': weighted_quantile(
                sub_renda['rendimento_habitual'], sub_renda['peso'], 0.50
            ) if len(sub_renda) > 0 else np.nan,
            '% Formal': weighted_mean(sub['formal'], sub['peso']) * 100,
            '% Mulheres': weighted_mean(
                (sub['sexo_texto'] == 'Mulher').astype(int), sub['peso']
            ) * 100,
            '% Negros': weighted_mean(
                (sub['raca_agregada'] == 'Negra').astype(int), sub['peso']
            ) * 100,
            'Idade Média': weighted_mean(sub['idade'], sub['peso']),
            'Pop. (milhões)': sub['peso'].sum() / 1e6,
        })

    result = pd.DataFrame(rows).set_index('Quintil').round(1)

    for _, row in result.iterrows():
        logger.info(f"  {row.name}: R$ {row['Rendimento Médio (R$)']:,.0f} | "
                     f"Formal {row['% Formal']:.1f}%")

    save_table(result, 'tabela2_perfil_quintis',
               'Perfil Socioeconômico por Quintil de Exposição')
    return result


# =========================================================================
# Tabela 3 — Região × Setor
# =========================================================================
def table3_regiao_setor(df):
    logger.info("\n=== Tabela 3: Região x Setor ===")
    mask = df['exposure_score'].notna()
    dfs = df[mask]

    pivot = dfs.groupby(['regiao', 'setor_agregado']).apply(
        lambda x: weighted_mean(x['exposure_score'], x['peso'])
    ).unstack(fill_value=np.nan)

    # Adicionar marginais
    for regiao in pivot.index:
        sub = dfs[dfs['regiao'] == regiao]
        pivot.loc[regiao, 'Média Região'] = weighted_mean(
            sub['exposure_score'], sub['peso']
        )
    media_setor = {}
    for setor in [c for c in pivot.columns if c != 'Média Região']:
        sub = dfs[dfs['setor_agregado'] == setor]
        if len(sub) > 0:
            media_setor[setor] = weighted_mean(sub['exposure_score'], sub['peso'])
    media_setor['Média Região'] = weighted_mean(dfs['exposure_score'], dfs['peso'])
    pivot.loc['Média Setor'] = media_setor

    pivot = pivot.round(3)
    logger.info(f"  Dimensões: {pivot.shape[0]} x {pivot.shape[1]}")

    save_table(pivot, 'tabela3_regiao_setor',
               'Exposição Média por Região e Setor')
    return pivot


# =========================================================================
# Tabela 4 — Desigualdade na Exposição
# =========================================================================
def table4_desigualdade(df):
    logger.info("\n=== Tabela 4: Desigualdade ===")
    mask = df['exposure_score'].notna()
    dfs = df[mask]

    gini_exp = gini_coefficient(dfs['exposure_score'], dfs['peso'])

    p90 = weighted_quantile(dfs['exposure_score'], dfs['peso'], 0.90)
    p10 = weighted_quantile(dfs['exposure_score'], dfs['peso'], 0.10)
    ratio_p90_p10 = p90 / p10 if p10 > 0 else np.nan

    q5 = dfs[dfs['quintil_exposure'] == 'Q5 (Alta)']
    q1 = dfs[dfs['quintil_exposure'] == 'Q1 (Baixa)']
    mean_q5 = weighted_mean(q5['exposure_score'], q5['peso'])
    mean_q1 = weighted_mean(q1['exposure_score'], q1['peso'])
    ratio_q5_q1_exp = mean_q5 / mean_q1 if mean_q1 > 0 else np.nan

    n_alta = dfs[dfs['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
    pct_alta = n_alta / dfs['peso'].sum() * 100

    # Razão renda Q5/Q1
    mask_renda = dfs['tem_renda'] == 1
    q5r = dfs[(dfs['quintil_exposure'] == 'Q5 (Alta)') & mask_renda]
    q1r = dfs[(dfs['quintil_exposure'] == 'Q1 (Baixa)') & mask_renda]
    mean_renda_q5 = weighted_mean(q5r['rendimento_habitual'], q5r['peso'])
    mean_renda_q1 = weighted_mean(q1r['rendimento_habitual'], q1r['peso'])
    ratio_renda = mean_renda_q5 / mean_renda_q1 if mean_renda_q1 > 0 else np.nan

    # Gini da renda
    renda_sub = dfs[mask_renda]
    gini_renda = gini_coefficient(renda_sub['rendimento_habitual'], renda_sub['peso'])

    metrics = {
        'Gini Exposição': gini_exp,
        'Razão P90/P10 (Exposição)': ratio_p90_p10,
        'Razão Q5/Q1 (Exposição)': ratio_q5_q1_exp,
        '% Alta Exposição (G3+G4)': pct_alta,
        'Razão Renda Q5/Q1': ratio_renda,
        'Gini Renda': gini_renda,
    }

    result = pd.DataFrame([
        {'Métrica': k, 'Valor': v} for k, v in metrics.items()
    ]).set_index('Métrica').round(4)

    for m, v in metrics.items():
        logger.info(f"  {m}: {v:.4f}")

    save_table(result, 'tabela4_desigualdade',
               'Métricas de Desigualdade na Exposição à IA')
    return result


# =========================================================================
# Tabela 5 — Comparação com Literatura
# =========================================================================
def table5_comparacao(df):
    logger.info("\n=== Tabela 5: Comparação com Literatura ===")
    mask = df['exposure_score'].notna()
    dfs = df[mask]

    exp_media = weighted_mean(dfs['exposure_score'], dfs['peso'])
    pct_alta = dfs[dfs['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)][
        'peso'].sum() / dfs['peso'].sum() * 100

    rows = [
        {
            'Estudo': 'Presente (ILO 2025)',
            'Metodologia': 'ILO WP140 refined',
            'País/Região': 'Brasil',
            'Exposição Média': f'{exp_media:.3f}',
            '% Alta Exposição': f'{pct_alta:.1f}%',
        },
        {
            'Estudo': 'Gmyrek et al. (2024)',
            'Metodologia': 'ILO 2023 global',
            'País/Região': 'Global',
            'Exposição Média': '0.30',
            '% Alta Exposição': '--',
        },
        {
            'Estudo': 'Eloundou et al. (2023)',
            'Metodologia': 'GPT rubrics',
            'País/Região': 'EUA',
            'Exposição Média': '--',
            '% Alta Exposição': '19.0%',
        },
    ]

    result = pd.DataFrame(rows).set_index('Estudo')
    save_table(result, 'tabela5_comparacao',
               'Comparação com Estudos Internacionais')
    return result


# =========================================================================
# Tabela 6 — Exposição por Setor (NOVA)
# =========================================================================
def table6_exposicao_setores(df):
    logger.info("\n=== Tabela 6: Exposição por Setor ===")
    mask = df['exposure_score'].notna()
    dfs = df[mask]
    total_peso = dfs['peso'].sum()

    rows = []
    for setor in sorted(dfs['setor_agregado'].unique()):
        sub = dfs[dfs['setor_agregado'] == setor]
        n_alta = sub[sub['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
        is_critico = setor in SETORES_CRITICOS_IA
        rows.append({
            'Setor': setor,
            'Exposição Média': weighted_mean(sub['exposure_score'], sub['peso']),
            'Desvio-Padrão': weighted_std(sub['exposure_score'], sub['peso']),
            'Trabalhadores (milhões)': sub['peso'].sum() / 1e6,
            '% Força de Trabalho': sub['peso'].sum() / total_peso * 100,
            '% Alta Exposição': n_alta / sub['peso'].sum() * 100 if sub['peso'].sum() > 0 else 0,
            'Setor Crítico IA': 'Sim' if is_critico else '',
        })

    result = pd.DataFrame(rows).sort_values('Exposição Média', ascending=False)
    result = result.set_index('Setor').round(3)

    for _, row in result.iterrows():
        flag = " *" if row['Setor Crítico IA'] == 'Sim' else ""
        logger.info(f"  {row.name}: {row['Exposição Média']:.3f} "
                     f"({row['Trabalhadores (milhões)']:.1f}M){flag}")

    save_table(result, 'tabela6_exposicao_setores',
               'Exposição à IA Generativa por Setor Econômico')
    return result


# =========================================================================
# Tabela 7 — Exposição por Gênero e Raça (NOVA)
# =========================================================================
def table7_genero_raca(df):
    logger.info("\n=== Tabela 7: Exposição por Gênero e Raça ===")
    mask = df['exposure_score'].notna()
    dfs = df[mask]

    def stats_by_group(col):
        rows = []
        for val in sorted(dfs[col].dropna().unique()):
            sub = dfs[dfs[col] == val]
            n_alta = sub[sub['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
            rows.append({
                'Grupo': val,
                'Exposição Média': weighted_mean(sub['exposure_score'], sub['peso']),
                'Desvio-Padrão': weighted_std(sub['exposure_score'], sub['peso']),
                'Trabalhadores (milhões)': sub['peso'].sum() / 1e6,
                '% Alta Exposição': n_alta / sub['peso'].sum() * 100,
            })
        return rows

    rows_sexo = stats_by_group('sexo_texto')
    rows_raca = stats_by_group('raca_agregada')

    all_rows = []
    all_rows.append({'Grupo': '--- Por Sexo ---', 'Exposição Média': np.nan,
                     'Desvio-Padrão': np.nan, 'Trabalhadores (milhões)': np.nan,
                     '% Alta Exposição': np.nan})
    all_rows.extend(rows_sexo)
    all_rows.append({'Grupo': '--- Por Raça ---', 'Exposição Média': np.nan,
                     'Desvio-Padrão': np.nan, 'Trabalhadores (milhões)': np.nan,
                     '% Alta Exposição': np.nan})
    all_rows.extend(rows_raca)

    result = pd.DataFrame(all_rows).set_index('Grupo').round(3)

    for row in rows_sexo + rows_raca:
        logger.info(f"  {row['Grupo']}: {row['Exposição Média']:.3f} "
                     f"({row['Trabalhadores (milhões)']:.1f}M)")

    save_table(result, 'tabela7_genero_raca',
               'Exposição à IA Generativa por Gênero e Raça')
    return result


# =========================================================================
# Tabela 8 — Exposição Formal vs Informal (NOVA)
# =========================================================================
def table8_formalidade(df):
    logger.info("\n=== Tabela 8: Formal vs Informal ===")
    mask = df['exposure_score'].notna()
    dfs = df[mask]

    rows = []
    for val, label in [(1, 'Formal'), (0, 'Informal')]:
        sub = dfs[dfs['formal'] == val]
        sub_renda = sub[sub['tem_renda'] == 1]
        n_alta = sub[sub['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
        rows.append({
            'Tipo': label,
            'Exposição Média': weighted_mean(sub['exposure_score'], sub['peso']),
            'Desvio-Padrão': weighted_std(sub['exposure_score'], sub['peso']),
            'Trabalhadores (milhões)': sub['peso'].sum() / 1e6,
            '% Alta Exposição': n_alta / sub['peso'].sum() * 100,
            'Rendimento Médio (R$)': weighted_mean(
                sub_renda['rendimento_habitual'], sub_renda['peso']
            ) if len(sub_renda) > 0 else np.nan,
        })

    result = pd.DataFrame(rows).set_index('Tipo').round(3)

    for _, row in result.iterrows():
        logger.info(f"  {row.name}: Exp {row['Exposição Média']:.3f} | "
                     f"R$ {row['Rendimento Médio (R$)']:,.0f}")

    save_table(result, 'tabela8_formalidade',
               'Exposição à IA Generativa: Formal vs Informal')
    return result


# =========================================================================
# Tabela 9 — Exposição por Idade e Instrução (NOVA)
# =========================================================================
def table9_idade_instrucao(df):
    logger.info("\n=== Tabela 9: Idade e Instrução ===")
    mask = df['exposure_score'].notna()
    dfs = df[mask]

    def stats_by_col(col, label_map=None):
        rows = []
        for val in sorted(dfs[col].dropna().unique()):
            sub = dfs[dfs[col] == val]
            n_alta = sub[sub['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
            label = label_map[val] if label_map and val in label_map else str(val)
            rows.append({
                'Grupo': label,
                'Exposição Média': weighted_mean(sub['exposure_score'], sub['peso']),
                'Trabalhadores (milhões)': sub['peso'].sum() / 1e6,
                '% Alta Exposição': n_alta / sub['peso'].sum() * 100,
            })
        return rows

    rows_idade = stats_by_col('faixa_etaria')
    rows_instrucao = stats_by_col('nivel_instrucao', NIVEL_INSTRUCAO_MAP)

    all_rows = []
    all_rows.append({'Grupo': '--- Por Faixa Etária ---', 'Exposição Média': np.nan,
                     'Trabalhadores (milhões)': np.nan, '% Alta Exposição': np.nan})
    all_rows.extend(rows_idade)
    all_rows.append({'Grupo': '--- Por Nível de Instrução ---', 'Exposição Média': np.nan,
                     'Trabalhadores (milhões)': np.nan, '% Alta Exposição': np.nan})
    all_rows.extend(rows_instrucao)

    result = pd.DataFrame(all_rows).set_index('Grupo').round(3)

    for row in rows_idade + rows_instrucao:
        logger.info(f"  {row['Grupo']}: {row['Exposição Média']:.3f} "
                     f"({row['Trabalhadores (milhões)']:.1f}M)")

    save_table(result, 'tabela9_idade_instrucao',
               'Exposição à IA Generativa por Faixa Etária e Nível de Instrução')
    return result


# =========================================================================
# Tabela 10 — Exposição por Região (NOVA)
# =========================================================================
def table10_regiao(df):
    logger.info("\n=== Tabela 10: Exposição por Região ===")
    mask = df['exposure_score'].notna()
    dfs = df[mask]

    rows = []
    for regiao in ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']:
        sub = dfs[dfs['regiao'] == regiao]
        n_alta = sub[sub['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS)]['peso'].sum()
        n_nao_exp = sub[sub['exposure_gradient'] == 'Not Exposed']['peso'].sum()
        rows.append({
            'Região': regiao,
            'Exposição Média': weighted_mean(sub['exposure_score'], sub['peso']),
            'Desvio-Padrão': weighted_std(sub['exposure_score'], sub['peso']),
            'Trabalhadores (milhões)': sub['peso'].sum() / 1e6,
            '% Alta Exposição': n_alta / sub['peso'].sum() * 100,
            '% Não Exposto': n_nao_exp / sub['peso'].sum() * 100,
        })

    result = pd.DataFrame(rows).set_index('Região').round(3)

    for _, row in result.iterrows():
        logger.info(f"  {row.name}: {row['Exposição Média']:.3f} "
                     f"({row['Trabalhadores (milhões)']:.1f}M)")

    save_table(result, 'tabela10_regiao',
               'Exposição à IA Generativa por Região')
    return result


# =========================================================================
# Geração completa
# =========================================================================
def generate_all_tables():
    logger.info("=" * 60)
    logger.info("GERAÇÃO DE TABELAS DESCRITIVAS")
    logger.info("=" * 60)

    df = load_data()

    table1_exposicao_grupos(df)
    table2_perfil_quintis(df)
    table3_regiao_setor(df)
    table4_desigualdade(df)
    table5_comparacao(df)
    table6_exposicao_setores(df)
    table7_genero_raca(df)
    table8_formalidade(df)
    table9_idade_instrucao(df)
    table10_regiao(df)

    logger.info("\n" + "=" * 60)
    logger.info("TODAS AS TABELAS GERADAS COM SUCESSO")
    logger.info("=" * 60)


if __name__ == "__main__":
    generate_all_tables()
