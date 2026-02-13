"""
Script 03: Criação de variáveis para análise DiD
=================================================

Cria TODAS as variáveis necessárias para Difference-in-Differences:
- Variáveis temporais (periodo, post, tempo_relativo)
- Variáveis de outcome (ocupado, formal, ln_renda)
- Variáveis demográficas (mulher, negro_pardo, jovem)
- Variáveis de educação (superior, medio)
- Variáveis regionais (regiao, grande_grupo)

Entrada: data/processed/pnad_panel_clean.parquet
Saída: data/processed/pnad_panel_variables.parquet
"""

import logging
import pandas as pd
import numpy as np
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '03_create_variables.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_temporal_variables(df):
    """
    Cria variáveis temporais para DiD.

    Variáveis criadas:
    - periodo: String "2021T1" para gráficos
    - periodo_num: Numérico 20211 para cálculos
    - tempo_relativo: Distância do período de referência (-7, -6, ..., 0, 1, 2, ...)
    - post: Dummy = 1 se período >= PERIODO_TRATAMENTO
    """

    logger.info("Criando variáveis temporais...")

    df = df.copy()

    # Período como string (para gráficos e legibilidade)
    df['periodo'] = df['ano'].astype(str) + 'T' + df['trimestre'].astype(str)

    # Período numérico (para ordenação e cálculos)
    df['periodo_num'] = df['ano'] * 10 + df['trimestre']

    # Tempo relativo ao período de referência (2022T4)
    # -7 = 2021T1, -6 = 2021T2, ..., 0 = 2022T4, 1 = 2023T1, ..., 8 = 2024T4
    df['tempo_relativo'] = df['periodo_num'] - PERIODO_REFERENCIA

    # Dummy pós-tratamento (ChatGPT lançado nov/2022, efeitos a partir de 2023T1)
    df['post'] = (df['periodo_num'] >= PERIODO_TRATAMENTO).astype(int)

    # Verificação
    n_pre = (df['post'] == 0).sum()
    n_post = (df['post'] == 1).sum()
    periodos_pre = df[df['post'] == 0]['periodo'].nunique()
    periodos_post = df[df['post'] == 1]['periodo'].nunique()

    logger.info(f"  Períodos pré-tratamento: {periodos_pre}")
    logger.info(f"  Períodos pós-tratamento: {periodos_post}")
    logger.info(f"  Obs pré: {n_pre:,} ({n_pre/len(df):.1%})")
    logger.info(f"  Obs pós: {n_post:,} ({n_post/len(df):.1%})")

    return df


def create_outcome_variables(df):
    """
    Cria variáveis de outcome (dependentes).

    Variáveis criadas:
    - ocupado: Binary de estar ocupado
    - formal: Binary de emprego formal
    - informal: Binary de emprego informal
    - ln_renda: Log do rendimento habitual
    - ln_horas: Log das horas trabalhadas (+ 1 para evitar log(0))
    """

    logger.info("Criando variáveis de outcome...")

    df = df.copy()

    # Ocupado (VD4002: 1 = ocupado, 2 = desocupado)
    df['ocupado'] = (df['condicao_ocupacao'] == '1').astype(int)

    # Formal (VD4009: 01-04 = formal, demais = informal)
    # 01 = Empregado com carteira
    # 02 = Militar
    # 03 = Estatutário
    # 04 = Empregador
    df['formal'] = df['tipo_vinculo'].isin(POSICAO_FORMAL).astype(int)

    # Informal (complemento)
    df['informal'] = 1 - df['formal']

    # Log do rendimento (apenas para quem tem rendimento positivo)
    df['ln_renda'] = np.where(
        df['rendimento_habitual'] > 0,
        np.log(df['rendimento_habitual']),
        np.nan
    )

    # Log das horas trabalhadas (+ 1 para evitar log(0))
    df['ln_horas'] = np.log(df['horas_trabalhadas'] + 1)

    # Estatísticas
    logger.info(f"  Taxa de ocupação: {df['ocupado'].mean():.1%}")
    logger.info(f"  Taxa de formalidade (entre ocupados): {df[df['ocupado']==1]['formal'].mean():.1%}")
    logger.info(f"  Renda média (ocupados, R$): {df[df['ocupado']==1]['rendimento_habitual'].mean():.0f}")
    logger.info(f"  Horas médias (ocupados): {df[df['ocupado']==1]['horas_trabalhadas'].mean():.1f}")

    return df


def create_demographic_variables(df):
    """
    Cria variáveis demográficas.

    Variáveis criadas:
    - mulher: Binary de sexo feminino
    - negro_pardo: Binary de raça negra ou parda
    - jovem: Binary de idade <= 30 anos
    - jovem_estrito: Binary de idade entre 22-25 (Brynjolfsson spec)
    - faixa_etaria: Categórica [18-25, 26-30, 31-40, 41-50, 51-65]
    """

    logger.info("Criando variáveis demográficas...")

    df = df.copy()

    # Sexo: mulher (V2007: 1=Masculino, 2=Feminino)
    df['mulher'] = (df['sexo'] == '2').astype(int)

    # Raça: negro ou pardo (V2010: 1=Branca, 2=Preta, 3=Amarela, 4=Parda, 5=Indígena)
    df['negro_pardo'] = df['raca'].isin(['2', '4']).astype(int)

    # Raça agregada (para análise)
    df['raca_agregada'] = df['raca'].map(RACA_AGREGADA_MAP)

    # Faixas etárias
    df['faixa_etaria'] = pd.cut(
        df['idade'],
        bins=IDADE_BINS,
        labels=IDADE_LABELS,
        include_lowest=True
    )

    # Jovem (para heterogeneidade - comparável com Brynjolfsson)
    df['jovem'] = (df['idade'] <= IDADE_JOVEM).astype(int)

    # Jovem estrito (22-25, exatamente como Brynjolfsson)
    df['jovem_estrito'] = (
        (df['idade'] >= IDADE_JOVEM_ESTRITO[0]) &
        (df['idade'] <= IDADE_JOVEM_ESTRITO[1])
    ).astype(int)

    # Estatísticas
    logger.info(f"  % Mulher: {df['mulher'].mean():.1%}")
    logger.info(f"  % Negro/Pardo: {df['negro_pardo'].mean():.1%}")
    logger.info(f"  % Jovem (≤30): {df['jovem'].mean():.1%}")
    logger.info(f"  Idade média: {df['idade'].mean():.1f} anos")

    return df


def create_education_variables(df):
    """
    Cria variáveis de educação.

    Variáveis criadas:
    - superior: Binary de ensino superior completo (anos_estudo >= 15)
    - medio: Binary de ensino médio completo (anos_estudo >= 11)
    - fundamental: Binary de ensino fundamental completo (anos_estudo >= 9)
    """

    logger.info("Criando variáveis de educação...")

    df = df.copy()

    # Superior completo (VD3004 >= 7 ou anos_estudo >= 15)
    df['superior'] = (df['anos_estudo'] >= 15).astype(int)

    # Médio completo
    df['medio'] = (df['anos_estudo'] >= 11).astype(int)

    # Fundamental completo
    df['fundamental'] = (df['anos_estudo'] >= 9).astype(int)

    # Estatísticas
    logger.info(f"  % Superior: {df['superior'].mean():.1%}")
    logger.info(f"  % Médio: {df['medio'].mean():.1%}")
    logger.info(f"  % Fundamental: {df['fundamental'].mean():.1%}")
    logger.info(f"  Anos de estudo médio: {df['anos_estudo'].mean():.1f}")

    return df


def create_regional_variables(df):
    """
    Cria variáveis regionais e ocupacionais.

    Variáveis criadas:
    - regiao: Região geográfica (Norte, Nordeste, Sudeste, Sul, Centro-Oeste)
    - grande_grupo: Grande grupo ocupacional (primeiro dígito do COD)
    """

    logger.info("Criando variáveis regionais...")

    df = df.copy()

    # Região
    df['regiao'] = df['sigla_uf'].map(REGIAO_MAP)

    # Grande grupo ocupacional (primeiro dígito do COD)
    df['grande_grupo_cod'] = df['cod_ocupacao'].str[0]
    df['grande_grupo'] = df['grande_grupo_cod'].map(GRANDES_GRUPOS)

    # Estatísticas
    logger.info("  Distribuição por região:")
    for regiao, count in df['regiao'].value_counts().items():
        pct = count / len(df) * 100
        logger.info(f"    {regiao}: {pct:.1f}%")

    return df


def create_variable_summary(df):
    """Cria sumário das variáveis criadas"""

    logger.info("")
    logger.info("="*70)
    logger.info("SUMÁRIO DAS VARIÁVEIS CRIADAS")
    logger.info("="*70)

    summary = []

    # Temporais
    summary.append({
        'Categoria': 'Temporal',
        'Variável': 'periodo',
        'Tipo': 'String',
        'Valores únicos': df['periodo'].nunique(),
        'Missing %': df['periodo'].isna().mean() * 100
    })
    summary.append({
        'Categoria': 'Temporal',
        'Variável': 'post',
        'Tipo': 'Binary',
        'Valores únicos': df['post'].nunique(),
        'Missing %': df['post'].isna().mean() * 100
    })

    # Outcomes
    for var in ['ocupado', 'formal', 'ln_renda', 'horas_trabalhadas']:
        summary.append({
            'Categoria': 'Outcome',
            'Variável': var,
            'Tipo': 'Numeric' if var.startswith('ln_') or var == 'horas_trabalhadas' else 'Binary',
            'Valores únicos': df[var].nunique(),
            'Missing %': df[var].isna().mean() * 100
        })

    # Demográficas
    for var in ['mulher', 'negro_pardo', 'jovem', 'faixa_etaria']:
        summary.append({
            'Categoria': 'Demográfica',
            'Variável': var,
            'Tipo': 'Binary' if var in ['mulher', 'negro_pardo', 'jovem'] else 'Categórica',
            'Valores únicos': df[var].nunique(),
            'Missing %': df[var].isna().mean() * 100
        })

    # Educação
    for var in ['superior', 'medio']:
        summary.append({
            'Categoria': 'Educação',
            'Variável': var,
            'Tipo': 'Binary',
            'Valores únicos': df[var].nunique(),
            'Missing %': df[var].isna().mean() * 100
        })

    # Regional
    for var in ['regiao', 'grande_grupo']:
        summary.append({
            'Categoria': 'Regional',
            'Variável': var,
            'Tipo': 'Categórica',
            'Valores únicos': df[var].nunique(),
            'Missing %': df[var].isna().mean() * 100
        })

    summary_df = pd.DataFrame(summary)
    logger.info("\n" + summary_df.to_string(index=False))

    # Salvar
    summary_path = OUTPUTS_TABLES / 'variable_summary.csv'
    summary_df.to_csv(summary_path, index=False)
    logger.info(f"\nSumário salvo em: {summary_path}")

    return summary_df


if __name__ == "__main__":

    # Carregar dados limpos
    logger.info("Carregando dados limpos...")
    df = pd.read_parquet(DATA_PROCESSED / "pnad_panel_clean.parquet")
    logger.info(f"Carregado: {len(df):,} observações\n")

    # Criar variáveis
    logger.info("="*70)
    logger.info("CRIAÇÃO DE VARIÁVEIS DID")
    logger.info("="*70)
    logger.info("")

    df = create_temporal_variables(df)
    logger.info("")
    df = create_outcome_variables(df)
    logger.info("")
    df = create_demographic_variables(df)
    logger.info("")
    df = create_education_variables(df)
    logger.info("")
    df = create_regional_variables(df)

    # Sumário
    create_variable_summary(df)

    # Salvar
    output_path = DATA_PROCESSED / "pnad_panel_variables.parquet"
    logger.info("")
    logger.info(f"Salvando em: {output_path}")
    df.to_parquet(output_path, index=False)

    logger.info("")
    logger.info("="*70)
    logger.info("CRIAÇÃO DE VARIÁVEIS CONCLUÍDA")
    logger.info("="*70)
    logger.info("Próximo passo: python src/04_merge_exposure.py")
