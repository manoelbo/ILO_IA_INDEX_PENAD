"""
Etapa 1a - Preparação de Dados: PNAD + Índice de Exposição ILO

Equivalente Python do notebook etapa_1a_preparacao_dados_ilo_pnadc.ipynb.

Fluxo:
  1. Configuração do ambiente
  2. Download dos microdados PNAD (local cache ou BigQuery)
  3. Processar índice de exposição ILO (Gmyrek et al. 2025)
  4. Limpeza e variáveis derivadas
  5. Crosswalk COD → ISCO-08 (hierárquico 4→3→2→1 dígito)
  6. Merge final PNAD + ILO → data/output/pnad_ilo_merged.csv

Uso:
  python src/scripts/etapa_1a_preparacao_dados_ilo_pnadc.py
"""

import warnings
import re
import pandas as pd
import numpy as np
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Caminhos — relativos à raiz do projeto
# ---------------------------------------------------------------------------
ROOT           = Path(__file__).parent.parent.parent
DATA_INPUT     = ROOT / "data" / "input"
DATA_RAW       = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_OUTPUT    = ROOT / "data" / "output"

for d in [DATA_RAW, DATA_PROCESSED, DATA_OUTPUT]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Parâmetros PNAD / GCP
# ---------------------------------------------------------------------------
GCP_PROJECT_ID  = "mestrado-pnad-2026"
PNAD_ANO        = 2025
PNAD_TRIMESTRE  = 3
SALARIO_MINIMO  = 1518  # Valor vigente em Q3/2025 (R$)

# ---------------------------------------------------------------------------
# Arquivo ILO
# ---------------------------------------------------------------------------
ILO_FILE = DATA_INPUT / "Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx"

# ---------------------------------------------------------------------------
# Mapeamentos
# ---------------------------------------------------------------------------
REGIAO_MAP = {
    'RO': 'Norte', 'AC': 'Norte', 'AM': 'Norte', 'RR': 'Norte',
    'PA': 'Norte', 'AP': 'Norte', 'TO': 'Norte',
    'MA': 'Nordeste', 'PI': 'Nordeste', 'CE': 'Nordeste', 'RN': 'Nordeste',
    'PB': 'Nordeste', 'PE': 'Nordeste', 'AL': 'Nordeste', 'SE': 'Nordeste', 'BA': 'Nordeste',
    'MG': 'Sudeste', 'ES': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
    'PR': 'Sul', 'SC': 'Sul', 'RS': 'Sul',
    'MS': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'DF': 'Centro-Oeste',
}

GRANDES_GRUPOS = {
    '1': 'Dirigentes e gerentes',
    '2': 'Profissionais das ciências',
    '3': 'Técnicos nível médio',
    '4': 'Apoio administrativo',
    '5': 'Serviços e vendedores',
    '6': 'Agropecuária qualificada',
    '7': 'Indústria qualificada',
    '8': 'Operadores de máquinas',
    '9': 'Ocupações elementares',
}

RACA_AGREGADA_MAP = {
    '1': 'Branca',
    '2': 'Negra',   # Preta
    '4': 'Negra',   # Parda
    '3': 'Outras',  # Amarela
    '5': 'Outras',  # Indígena
    '9': 'Outras',  # Sem declaração
}

POSICAO_FORMAL = ['1', '3', '5']  # Empregado c/ carteira, Militar, Empregador

IDADE_BINS   = [0, 25, 35, 45, 55, 100]
IDADE_LABELS = ['18-24', '25-34', '35-44', '45-54', '55+']

CNAE_SETOR_MAP = {
    # A - Agropecuária
    '01': 'Agropecuária', '02': 'Agropecuária', '03': 'Agropecuária',
    # B - Indústria Extrativa
    '05': 'Ind. Extrativa', '06': 'Ind. Extrativa', '07': 'Ind. Extrativa',
    '08': 'Ind. Extrativa', '09': 'Ind. Extrativa',
    # C - Indústria de Transformação
    '10': 'Ind. Transformação', '11': 'Ind. Transformação', '12': 'Ind. Transformação',
    '13': 'Ind. Transformação', '14': 'Ind. Transformação', '15': 'Ind. Transformação',
    '16': 'Ind. Transformação', '17': 'Ind. Transformação', '18': 'Ind. Transformação',
    '19': 'Ind. Transformação', '20': 'Ind. Transformação', '21': 'Ind. Transformação',
    '22': 'Ind. Transformação', '23': 'Ind. Transformação', '24': 'Ind. Transformação',
    '25': 'Ind. Transformação', '26': 'Ind. Transformação', '27': 'Ind. Transformação',
    '28': 'Ind. Transformação', '29': 'Ind. Transformação', '30': 'Ind. Transformação',
    '31': 'Ind. Transformação', '32': 'Ind. Transformação', '33': 'Ind. Transformação',
    # D+E - Utilidades
    '35': 'Utilidades', '36': 'Utilidades', '37': 'Utilidades',
    '38': 'Utilidades', '39': 'Utilidades',
    # F - Construção
    '41': 'Construção', '42': 'Construção', '43': 'Construção',
    # G - Comércio
    '45': 'Comércio', '46': 'Comércio', '47': 'Comércio',
    # H - Transporte
    '49': 'Transporte', '50': 'Transporte', '51': 'Transporte',
    '52': 'Transporte', '53': 'Transporte',
    # I - Alojamento e Alimentação
    '55': 'Alojamento e Alimentação', '56': 'Alojamento e Alimentação',
    # J - Informação e Comunicação
    '58': 'Informação e Comunicação', '59': 'Informação e Comunicação',
    '60': 'Informação e Comunicação', '61': 'Informação e Comunicação',
    '62': 'Informação e Comunicação', '63': 'Informação e Comunicação',
    # K - Atividades Financeiras
    '64': 'Finanças e Seguros', '65': 'Finanças e Seguros', '66': 'Finanças e Seguros',
    # L - Atividades Imobiliárias
    '68': 'Atividades Imobiliárias',
    # M - Serviços Profissionais
    '69': 'Serviços Profissionais', '70': 'Serviços Profissionais',
    '71': 'Serviços Profissionais', '72': 'Serviços Profissionais',
    '73': 'Serviços Profissionais', '74': 'Serviços Profissionais',
    '75': 'Serviços Profissionais',
    # N - Serviços Administrativos
    '77': 'Serviços Administrativos', '78': 'Serviços Administrativos',
    '79': 'Serviços Administrativos', '80': 'Serviços Administrativos',
    '81': 'Serviços Administrativos', '82': 'Serviços Administrativos',
    # O - Administração Pública
    '84': 'Administração Pública',
    # P - Educação
    '85': 'Educação',
    # Q - Saúde
    '86': 'Saúde', '87': 'Saúde', '88': 'Saúde',
    # R - Artes e Cultura
    '90': 'Artes e Cultura', '91': 'Artes e Cultura',
    '92': 'Artes e Cultura', '93': 'Artes e Cultura',
    # S - Outros Serviços
    '94': 'Outros Serviços', '95': 'Outros Serviços', '96': 'Outros Serviços',
    # T - Serviços Domésticos
    '97': 'Serviços Domésticos',
}

SETORES_CRITICOS_IA = [
    'Informação e Comunicação',
    'Finanças e Seguros',
    'Serviços Profissionais',
]


# ---------------------------------------------------------------------------
# Funções utilitárias — estatísticas ponderadas
# ---------------------------------------------------------------------------
def weighted_mean(values, weights):
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    return np.average(values[mask], weights=weights[mask])


def weighted_std(values, weights):
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    avg = np.average(values[mask], weights=weights[mask])
    variance = np.average((values[mask] - avg) ** 2, weights=weights[mask])
    return np.sqrt(variance)


def weighted_quantile(values, weights, quantile):
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    sorted_idx = np.argsort(values[mask])
    sorted_values = values[mask].iloc[sorted_idx]
    sorted_weights = weights[mask].iloc[sorted_idx]
    cumsum = np.cumsum(sorted_weights)
    cutoff = quantile * cumsum.iloc[-1]
    return sorted_values.iloc[np.searchsorted(cumsum, cutoff)]


def weighted_qcut(values, weights, q, labels=None):
    mask = values.notna() & weights.notna()
    breakpoints = [values[mask].min() - 1e-10]
    for i in range(1, q):
        bp = weighted_quantile(values[mask], weights[mask], i / q)
        breakpoints.append(bp)
    breakpoints.append(values[mask].max() + 1e-10)
    breakpoints = sorted(set(breakpoints))
    if labels is not None and len(labels) != len(breakpoints) - 1:
        labels = None
    return pd.cut(values, bins=breakpoints, labels=labels, include_lowest=True)


# ---------------------------------------------------------------------------
# Etapas
# ---------------------------------------------------------------------------
def step_download_pnad():
    """Download ou carregamento local dos microdados PNAD."""
    global PNAD_ANO, PNAD_TRIMESTRE

    pnad_files = sorted(DATA_RAW.glob("pnad_*.parquet"))

    if pnad_files:
        pnad_path = pnad_files[-1]
        print(f"Arquivo PNAD encontrado localmente: {pnad_path.name}")
        df = pd.read_parquet(pnad_path)
        print(f"Carregado: {len(df):,} observações")

        match = re.search(r"pnad_(\d{4})q(\d)", pnad_path.name)
        if match:
            ano_arquivo, trim_arquivo = int(match.group(1)), int(match.group(2))
            if ano_arquivo != PNAD_ANO or trim_arquivo != PNAD_TRIMESTRE:
                print(f"  WARNING: Arquivo é {ano_arquivo} Q{trim_arquivo}, "
                      f"mas config diz {PNAD_ANO} Q{PNAD_TRIMESTRE}. Ajustando config.")
                PNAD_ANO = ano_arquivo
                PNAD_TRIMESTRE = trim_arquivo
        return df

    print("Nenhum arquivo PNAD local. Iniciando download do BigQuery...")
    import basedosdados as bd

    query_check = """
    SELECT DISTINCT ano, trimestre, COUNT(*) as n_obs
    FROM `basedosdados.br_ibge_pnadc.microdados`
    WHERE ano >= 2024
    GROUP BY ano, trimestre
    ORDER BY ano DESC, trimestre DESC
    LIMIT 5
    """
    df_check = bd.read_sql(query_check, billing_project_id=GCP_PROJECT_ID)
    print(f"Trimestres disponíveis:\n{df_check}")

    trimestre_existe = len(
        df_check[(df_check['ano'] == PNAD_ANO) & (df_check['trimestre'] == PNAD_TRIMESTRE)]
    ) > 0

    if trimestre_existe:
        ano_usar, trim_usar = PNAD_ANO, PNAD_TRIMESTRE
    else:
        ano_usar = int(df_check.iloc[0]['ano'])
        trim_usar = int(df_check.iloc[0]['trimestre'])
        print(f"AVISO: {PNAD_ANO} Q{PNAD_TRIMESTRE} indisponível. Usando {ano_usar} Q{trim_usar}")
        PNAD_ANO = ano_usar
        PNAD_TRIMESTRE = trim_usar

    query = f"""
    SELECT
        ano, trimestre, sigla_uf,
        v2007  AS sexo,
        v2009  AS idade,
        v2010  AS raca_cor,
        vd3004 AS nivel_instrucao,
        v4010  AS cod_ocupacao,
        v4013  AS grupamento_atividade,
        vd4009 AS posicao_ocupacao,
        vd4016 AS rendimento_habitual,
        vd4020 AS rendimento_efetivo,
        vd4031 AS horas_habituais,
        vd4035 AS horas_efetivas,
        v1028  AS peso
    FROM `basedosdados.br_ibge_pnadc.microdados`
    WHERE ano = {ano_usar}
      AND trimestre = {trim_usar}
      AND v4010 IS NOT NULL
    """
    print(f"Executando query para {ano_usar} Q{trim_usar} (pode demorar 2-5 min)...")
    df = bd.read_sql(query, billing_project_id=GCP_PROJECT_ID)

    ano_real = int(df['ano'].iloc[0])
    trim_real = int(df['trimestre'].iloc[0])
    output_path = DATA_RAW / f"pnad_{ano_real}q{trim_real}.parquet"
    df.to_parquet(output_path, index=False)
    print(f"Salvo em: {output_path}")
    return df


def step_process_ilo():
    """Processar índice de exposição ILO (Gmyrek et al. 2025)."""
    print(f"\nLendo arquivo ILO: {ILO_FILE}")
    df_ilo_raw = pd.read_excel(ILO_FILE)
    print(f"Linhas raw: {len(df_ilo_raw):,} | Colunas: {list(df_ilo_raw.columns)}")

    col_mapping = {
        'ISCO_08': 'isco_08',
        'Title': 'occupation_title',
        'mean_score_2025': 'exposure_score',
        'SD_2025': 'exposure_sd',
        'potential25': 'exposure_gradient',
    }
    df_ilo_renamed = df_ilo_raw.rename(
        columns={k: v for k, v in col_mapping.items() if k in df_ilo_raw.columns}
    )
    df_ilo = df_ilo_renamed.groupby('isco_08').agg({
        'occupation_title': 'first',
        'exposure_score': 'mean',
        'exposure_sd': 'mean',
        'exposure_gradient': 'first',
    }).reset_index()
    df_ilo['isco_08_str'] = df_ilo['isco_08'].astype(str).str.zfill(4)

    print(f"Ocupações únicas: {len(df_ilo):,}")
    print(f"Score médio: {df_ilo['exposure_score'].mean():.3f} "
          f"[{df_ilo['exposure_score'].min():.3f}, {df_ilo['exposure_score'].max():.3f}]")

    ilo_output = DATA_PROCESSED / "ilo_exposure_clean.csv"
    df_ilo.to_csv(ilo_output, index=False)
    print(f"Salvo em: {ilo_output}")
    return df_ilo


def step_clean_pnad(df_pnad_raw):
    """Limpeza e variáveis derivadas do PNAD."""
    df_pnad = df_pnad_raw.copy()
    n_inicial = len(df_pnad)
    print(f"\nObservações iniciais: {n_inicial:,}")

    df_pnad['cod_ocupacao'] = df_pnad['cod_ocupacao'].astype(str).str.zfill(4)
    for col in ['idade', 'rendimento_habitual', 'rendimento_efetivo',
                'horas_habituais', 'horas_efetivas', 'peso']:
        df_pnad[col] = pd.to_numeric(df_pnad[col], errors='coerce')

    df_pnad = df_pnad.dropna(subset=['cod_ocupacao', 'idade', 'peso'])
    df_pnad = df_pnad[(df_pnad['idade'] >= 18) & (df_pnad['idade'] <= 65)]
    df_pnad = df_pnad[~df_pnad['cod_ocupacao'].isin(['0000', '9999'])]
    print(f"Após filtros: {len(df_pnad):,} ({len(df_pnad)/n_inicial:.1%})")

    df_pnad['tem_renda'] = (
        df_pnad['rendimento_habitual'].notna() & (df_pnad['rendimento_habitual'] > 0)
    ).astype(int)
    df_pnad['formal'] = df_pnad['posicao_ocupacao'].astype(str).isin(POSICAO_FORMAL).astype(int)
    df_pnad['faixa_etaria'] = pd.cut(df_pnad['idade'], bins=IDADE_BINS, labels=IDADE_LABELS)
    df_pnad['regiao'] = df_pnad['sigla_uf'].map(REGIAO_MAP)
    df_pnad['raca_agregada'] = df_pnad['raca_cor'].astype(str).map(RACA_AGREGADA_MAP)
    df_pnad['grande_grupo'] = df_pnad['cod_ocupacao'].str[0].map(GRANDES_GRUPOS)
    df_pnad['sexo_texto'] = df_pnad['sexo'].map({1: 'Homem', 2: 'Mulher', '1': 'Homem', '2': 'Mulher'})

    mask_renda = df_pnad['tem_renda'] == 1
    p01 = weighted_quantile(df_pnad.loc[mask_renda, 'rendimento_habitual'],
                            df_pnad.loc[mask_renda, 'peso'], 0.01)
    p99 = weighted_quantile(df_pnad.loc[mask_renda, 'rendimento_habitual'],
                            df_pnad.loc[mask_renda, 'peso'], 0.99)
    df_pnad['rendimento_winsor'] = df_pnad['rendimento_habitual'].clip(lower=p01, upper=p99)
    print(f"Winsorização ponderada: P1=R${p01:,.0f}, P99=R${p99:,.0f}")

    df_pnad['faixa_renda_sm'] = pd.cut(
        df_pnad['rendimento_habitual'] / SALARIO_MINIMO,
        bins=[0, 1, 2, 3, 5, float('inf')],
        labels=['Até 1 SM', '1-2 SM', '2-3 SM', '3-5 SM', '5+ SM'],
        right=True, include_lowest=True,
    )
    print(f"Taxa de formalidade: {df_pnad['formal'].mean():.1%}")

    pnad_clean_path = DATA_PROCESSED / "pnad_clean.csv"
    df_pnad.to_csv(pnad_clean_path, index=False)
    print(f"Salvo em: {pnad_clean_path}")
    return df_pnad


def step_crosswalk(df_pnad, df_ilo):
    """Crosswalk hierárquico COD → ISCO-08 (4→3→2→1 dígito)."""
    df_ilo['isco_08_str'] = df_ilo['isco_08_str'].astype(str).str.zfill(4)
    df_pnad['cod_ocupacao'] = df_pnad['cod_ocupacao'].astype(str).str.zfill(4)

    ilo_4d = df_ilo.groupby('isco_08_str')['exposure_score'].mean().to_dict()
    ilo_3d = df_ilo.groupby(df_ilo['isco_08_str'].str[:3])['exposure_score'].mean().to_dict()
    ilo_2d = df_ilo.groupby(df_ilo['isco_08_str'].str[:2])['exposure_score'].mean().to_dict()
    ilo_1d = df_ilo.groupby(df_ilo['isco_08_str'].str[:1])['exposure_score'].mean().to_dict()
    ilo_gradient_4d = df_ilo.groupby('isco_08_str')['exposure_gradient'].first().to_dict()

    df = df_pnad.copy()
    df['exposure_score'] = np.nan
    df['exposure_gradient'] = None
    df['match_level'] = None

    mask_4d = df['cod_ocupacao'].isin(ilo_4d.keys())
    df.loc[mask_4d, 'exposure_score'] = df.loc[mask_4d, 'cod_ocupacao'].map(ilo_4d)
    df.loc[mask_4d, 'exposure_gradient'] = df.loc[mask_4d, 'cod_ocupacao'].map(ilo_gradient_4d)
    df.loc[mask_4d, 'match_level'] = '4-digit'
    print(f"\nMatch 4-digit: {mask_4d.sum():,} ({mask_4d.mean():.1%})")

    for n_digit, ilo_dict in [(3, ilo_3d), (2, ilo_2d), (1, ilo_1d)]:
        mask_missing = df['exposure_score'].isna()
        cod_nd = df.loc[mask_missing, 'cod_ocupacao'].str[:n_digit]
        mask_nd = cod_nd.isin(ilo_dict.keys())
        idx_nd = mask_missing[mask_missing].index[mask_nd.values]
        df.loc[idx_nd, 'exposure_score'] = cod_nd[mask_nd].map(ilo_dict).values
        df.loc[idx_nd, 'exposure_gradient'] = 'Sem classificação'
        df.loc[idx_nd, 'match_level'] = f'{n_digit}-digit'
        print(f"Match {n_digit}-digit: {len(idx_nd):,} ({len(idx_nd)/len(df):.1%})")

    n_sem = df['exposure_score'].isna().sum()
    df.loc[df['exposure_score'].isna(), 'exposure_gradient'] = 'Sem classificação'
    print(f"Sem match: {n_sem:,} ({n_sem/len(df):.1%})")
    return df


def step_merge_final(df_crosswalked):
    """Merge final, criação de quintis/decis e agregação setorial."""
    df = df_crosswalked.copy()

    mask_valid = df['exposure_score'].notna()
    df.loc[mask_valid, 'quintil_exposure'] = weighted_qcut(
        df.loc[mask_valid, 'exposure_score'],
        df.loc[mask_valid, 'peso'], q=5,
        labels=['Q1 (Baixa)', 'Q2', 'Q3', 'Q4', 'Q5 (Alta)'],
    )
    df.loc[mask_valid, 'decil_exposure'] = weighted_qcut(
        df.loc[mask_valid, 'exposure_score'],
        df.loc[mask_valid, 'peso'], q=10,
        labels=[f'D{i}' for i in range(1, 11)],
    )

    df['cnae_2d'] = df['grupamento_atividade'].astype(str).str[:2]
    df['setor_agregado'] = df['cnae_2d'].map(CNAE_SETOR_MAP).fillna('Outros Serviços')
    df['setor_critico_ia'] = df['setor_agregado'].isin(SETORES_CRITICOS_IA).astype(int)

    cols_output = [
        'ano', 'trimestre', 'sigla_uf', 'regiao',
        'sexo', 'sexo_texto', 'idade', 'faixa_etaria',
        'raca_cor', 'raca_agregada', 'nivel_instrucao',
        'cod_ocupacao', 'grande_grupo',
        'grupamento_atividade', 'setor_agregado', 'setor_critico_ia',
        'posicao_ocupacao', 'formal', 'tem_renda',
        'rendimento_habitual', 'rendimento_winsor', 'rendimento_efetivo',
        'horas_habituais', 'horas_efetivas', 'faixa_renda_sm', 'peso',
        'exposure_score', 'exposure_gradient', 'match_level',
        'quintil_exposure', 'decil_exposure',
    ]
    df = df[[c for c in cols_output if c in df.columns]]

    output_path = DATA_OUTPUT / "pnad_ilo_merged.csv"
    df.to_csv(output_path, index=False)

    print(f"\n{'='*60}")
    print("BASE FINAL CONSOLIDADA")
    print(f"{'='*60}")
    print(f"Observações:      {len(df):,}")
    print(f"Cobertura score:  {df['exposure_score'].notna().mean():.1%}")
    print(f"População total:  {df['peso'].sum()/1e6:.1f} milhões")
    print(f"Setores:          {df['setor_agregado'].nunique()} categorias")
    print(f"Salvo em:         {output_path}")
    print(f"Tamanho em disco: {output_path.stat().st_size/1e6:.1f} MB")
    return df


def main():
    print("=" * 60)
    print("ETAPA 1A — Preparação de Dados: PNAD + ILO")
    print("=" * 60)
    print(f"ROOT: {ROOT}")
    print(f"data/: {ROOT / 'data'}")

    print("\n[1/5] Download PNAD...")
    df_pnad_raw = step_download_pnad()

    print("\n[2/5] Processar índice ILO...")
    df_ilo = step_process_ilo()

    print("\n[3/5] Limpeza PNAD e variáveis derivadas...")
    df_pnad = step_clean_pnad(df_pnad_raw)

    print("\n[4/5] Crosswalk COD → ISCO-08...")
    df_crosswalked = step_crosswalk(df_pnad, df_ilo)

    print("\n[5/5] Merge final e exportação...")
    step_merge_final(df_crosswalked)

    print("\nEtapa 1a concluída.")


if __name__ == "__main__":
    main()
