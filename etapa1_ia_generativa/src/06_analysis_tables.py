"""
Script 06: Geração das 5 tabelas principais
Entrada: data/processed/pnad_ilo_merged.csv
Saída: outputs/tables/*.csv e *.tex
"""

import logging
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *
from src.utils.weighted_stats import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '06_tables.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_data():
    """Carrega base consolidada"""
    df = pd.read_csv(DATA_PROCESSED / "pnad_ilo_merged.csv")
    logger.info(f"Dados carregados: {len(df):,} observações")
    return df

def table1_exposicao_grupos(df):
    """TABELA 1: Exposição por Grande Grupo Ocupacional"""
    
    logger.info("\n=== TABELA 1: Exposição por Grande Grupo ===")
    
    results = []
    for grupo in df['grande_grupo'].dropna().unique():
        mask = df['grande_grupo'] == grupo
        subset = df[mask]
        
        results.append({
            'Grande Grupo': grupo,
            'Exposição Média': weighted_mean(subset['exposure_score'], subset['peso']),
            'Desvio-Padrão': weighted_std(subset['exposure_score'], subset['peso']),
            'Trabalhadores (milhões)': subset['peso'].sum() / 1e6,
            '% Força de Trabalho': subset['peso'].sum() / df['peso'].sum() * 100
        })
    
    tabela1 = pd.DataFrame(results)
    tabela1 = tabela1.sort_values('Exposição Média', ascending=False)
    tabela1 = tabela1.round(3)
    
    # Salvar CSV
    tabela1.to_csv(OUTPUTS_TABLES / "tabela1_exposicao_grupos.csv", index=False)
    
    # Salvar LaTeX
    latex = tabela1.to_latex(
        index=False,
        caption='Exposição à IA Generativa por Grande Grupo Ocupacional - Brasil 3º Tri 2025',
        label='tab:exposicao_grupos',
        column_format='lrrrr'
    )
    with open(OUTPUTS_TABLES / "tabela1_exposicao_grupos.tex", 'w') as f:
        f.write(latex)
    
    logger.info(tabela1.to_string())
    return tabela1

def table2_perfil_quintis(df):
    """TABELA 2: Perfil Socioeconômico por Quintil de Exposição"""
    
    logger.info("\n=== TABELA 2: Perfil por Quintil ===")
    
    results = []
    for quintil in ['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)']:
        if quintil not in df['quintil_exposure'].values:
            continue
        mask = df['quintil_exposure'] == quintil
        subset = df[mask]
        
        results.append({
            'Quintil': quintil,
            'Rendimento Médio (R$)': weighted_mean(subset['rendimento_habitual'], subset['peso']),
            '% Formal': weighted_mean(subset['formal'], subset['peso']) * 100,
            '% Mulheres': weighted_mean(subset['sexo_texto'] == 'Mulher', subset['peso']) * 100,
            '% Negros': weighted_mean(subset['raca_agregada'] == 'Negra', subset['peso']) * 100,
            'Idade Média': weighted_mean(subset['idade'], subset['peso']),
            'Pop. (milhões)': subset['peso'].sum() / 1e6
        })
    
    tabela2 = pd.DataFrame(results)
    tabela2 = tabela2.round(2)
    
    # Salvar
    tabela2.to_csv(OUTPUTS_TABLES / "tabela2_perfil_quintis.csv", index=False)
    
    latex = tabela2.to_latex(
        index=False,
        caption='Perfil Socioeconômico por Quintil de Exposição à IA - Brasil 3º Tri 2025',
        label='tab:perfil_quintis'
    )
    with open(OUTPUTS_TABLES / "tabela2_perfil_quintis.tex", 'w') as f:
        f.write(latex)
    
    logger.info(tabela2.to_string())
    return tabela2

def table3_regiao_setor(df):
    """TABELA 3: Exposição por Região e Setor (matriz)"""
    
    logger.info("\n=== TABELA 3: Região x Setor ===")
    
    # Calcular médias ponderadas por célula
    def calc_weighted_mean(group):
        return weighted_mean(group['exposure_score'], group['peso'])
    
    tabela3 = df.groupby(['regiao', 'setor_agregado']).apply(calc_weighted_mean).unstack(fill_value=np.nan)
    tabela3 = tabela3.round(3)
    
    # Adicionar médias marginais
    tabela3['Média Região'] = df.groupby('regiao').apply(calc_weighted_mean)
    
    setor_means = df.groupby('setor_agregado').apply(calc_weighted_mean)
    tabela3.loc['Média Setor'] = setor_means
    tabela3.loc['Média Setor', 'Média Região'] = weighted_mean(df['exposure_score'], df['peso'])
    
    # Salvar
    tabela3.to_csv(OUTPUTS_TABLES / "tabela3_regiao_setor.csv")
    
    latex = tabela3.to_latex(
        caption='Exposição Média à IA por Região e Setor - Brasil 3º Tri 2025',
        label='tab:regiao_setor'
    )
    with open(OUTPUTS_TABLES / "tabela3_regiao_setor.tex", 'w') as f:
        f.write(latex)
    
    logger.info(tabela3.to_string())
    return tabela3

def table4_desigualdade(df):
    """TABELA 4: Decomposição da Desigualdade de Exposição"""
    
    logger.info("\n=== TABELA 4: Desigualdade ===")
    
    mask = df['exposure_score'].notna()
    subset = df[mask]
    
    results = {
        'Métrica': [],
        'Valor': []
    }
    
    # Gini total
    gini = gini_coefficient(subset['exposure_score'], subset['peso'])
    results['Métrica'].append('Coeficiente de Gini')
    results['Valor'].append(gini)
    
    # Razão P90/P10
    p90 = weighted_quantile(subset['exposure_score'], subset['peso'], 0.90)
    p10 = weighted_quantile(subset['exposure_score'], subset['peso'], 0.10)
    results['Métrica'].append('Razão P90/P10')
    results['Valor'].append(p90 / p10 if p10 > 0 else np.nan)
    
    # Razão Q5/Q1
    q5_mean = weighted_mean(
        subset[subset['quintil_exposure'] == 'Q5 (Alta)']['exposure_score'],
        subset[subset['quintil_exposure'] == 'Q5 (Alta)']['peso']
    )
    q1_mean = weighted_mean(
        subset[subset['quintil_exposure'] == 'Q1 (Baixa)']['exposure_score'],
        subset[subset['quintil_exposure'] == 'Q1 (Baixa)']['peso']
    )
    results['Métrica'].append('Razão Média Q5/Q1')
    results['Valor'].append(q5_mean / q1_mean if q1_mean > 0 else np.nan)
    
    # % em alta exposição (Gradient 4)
    alta_exp = subset[subset['exposure_gradient'] == 'Gradient 4 (Alta)']['peso'].sum()
    results['Métrica'].append('% Alta Exposição (G4)')
    results['Valor'].append(alta_exp / subset['peso'].sum() * 100)
    
    tabela4 = pd.DataFrame(results)
    tabela4 = tabela4.round(4)
    
    # Salvar
    tabela4.to_csv(OUTPUTS_TABLES / "tabela4_desigualdade.csv", index=False)
    
    latex = tabela4.to_latex(
        index=False,
        caption='Métricas de Desigualdade na Exposição à IA - Brasil 3º Tri 2025',
        label='tab:desigualdade'
    )
    with open(OUTPUTS_TABLES / "tabela4_desigualdade.tex", 'w') as f:
        f.write(latex)
    
    logger.info(tabela4.to_string())
    return tabela4

def table5_comparacao(df):
    """TABELA 5: Comparação com Literatura"""
    
    logger.info("\n=== TABELA 5: Comparação ===")
    
    mask = df['exposure_score'].notna()
    media_br = weighted_mean(df[mask]['exposure_score'], df[mask]['peso'])
    
    # Alta exposição (score >= 0.45)
    alta_exp = df[df['exposure_score'] >= 0.45]['peso'].sum() / df[mask]['peso'].sum() * 100
    
    tabela5 = pd.DataFrame({
        'Estudo': [
            'Presente estudo (ILO 2025)',
            'Imaizumi et al. (LCA, 2024)*',
            'Gmyrek et al. (ILO, 2023)*',
            'Eloundou et al. (OpenAI, 2023)*'
        ],
        'Metodologia': [
            'ILO refined index 2025',
            'ILO 2023 + PNAD',
            'ILO 2023 global',
            'GPT exposure rubrics'
        ],
        'País/Região': [
            'Brasil',
            'Brasil',
            'Global',
            'EUA'
        ],
        'Exposição Média': [
            media_br,
            np.nan,  # Preencher manualmente após consultar literatura
            0.30,    # Valor aproximado ILO 2023
            np.nan   # Diferente metodologia
        ],
        '% Alta Exposição': [
            alta_exp,
            np.nan,
            np.nan,
            np.nan
        ]
    })
    
    tabela5.to_csv(OUTPUTS_TABLES / "tabela5_comparacao.csv", index=False)
    
    logger.info("* Valores a serem preenchidos após consulta à literatura")
    logger.info(tabela5.to_string())
    return tabela5

def generate_all_tables():
    """Gera todas as tabelas"""
    
    logger.info("=" * 60)
    logger.info("GERAÇÃO DE TABELAS - ETAPA 1")
    logger.info("=" * 60)
    
    df = load_data()
    
    t1 = table1_exposicao_grupos(df)
    t2 = table2_perfil_quintis(df)
    t3 = table3_regiao_setor(df)
    t4 = table4_desigualdade(df)
    t5 = table5_comparacao(df)
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ TABELAS GERADAS COM SUCESSO!")
    logger.info(f"Arquivos salvos em: {OUTPUTS_TABLES}")
    logger.info("=" * 60)
    
    return {'t1': t1, 't2': t2, 't3': t3, 't4': t4, 't5': t5}

if __name__ == "__main__":
    generate_all_tables()
