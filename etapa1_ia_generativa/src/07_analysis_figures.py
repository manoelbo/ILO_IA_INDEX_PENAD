"""
Script 07: Geração das 8 figuras de análise
Entrada: data/output/pnad_ilo_merged.csv
Saída: outputs/figures/*.png e *.pdf
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import linregress
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
        logging.FileHandler(OUTPUTS_LOGS / '07_figures.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurações globais de estilo
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
sns.set_style("whitegrid")


def load_data():
    """Carrega base consolidada"""
    df = pd.read_csv(DATA_OUTPUT / "pnad_ilo_merged.csv")
    logger.info(f"Dados carregados: {len(df):,} observações")
    return df


# ---------------------------------------------------------------------------
# Figuras 1-4: Atualizadas
# ---------------------------------------------------------------------------

def figure1_distribuicao(df):
    """FIGURA 1: Distribuição da Exposição (histograma + gradientes ILO)"""

    logger.info("\n=== FIGURA 1: Distribuição da Exposição ===")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    mask = df['exposure_score'].notna()
    subset = df[mask]

    # Painel A: Histograma ponderado
    ax1.hist(
        subset['exposure_score'],
        weights=subset['peso'] / 1e6,
        bins=50,
        edgecolor='black',
        alpha=0.7,
        color='steelblue'
    )

    media = weighted_mean(subset['exposure_score'], subset['peso'])
    ax1.axvline(media, color='red', linestyle='--', linewidth=2,
                label=f'Média: {media:.3f}')

    ax1.set_xlabel('Score de Exposição à IA Generativa')
    ax1.set_ylabel('Trabalhadores (milhões)')
    ax1.set_title('(A) Distribuição Contínua da Exposição')
    ax1.legend()

    # Painel B: Barras por gradiente (6 gradientes oficiais, excluir "Sem classificação")
    gradient_display = [g for g in GRADIENT_ORDER if g != 'Sem classificação']
    gradient_counts = subset.groupby('exposure_gradient')['peso'].sum() / 1e6
    gradient_counts = gradient_counts.reindex(
        [g for g in gradient_display if g in gradient_counts.index]
    )

    colors = [GRADIENT_COLORS[g] for g in gradient_counts.index]
    bars = ax2.barh(range(len(gradient_counts)), gradient_counts.values,
                    color=colors, edgecolor='black')
    ax2.set_yticks(range(len(gradient_counts)))
    ax2.set_yticklabels([GRADIENT_LABELS_PT.get(g, g) for g in gradient_counts.index])
    ax2.set_xlabel('Trabalhadores (milhões)')
    ax2.set_title('(B) Distribuição por Gradiente ILO')

    for i, v in enumerate(gradient_counts.values):
        ax2.text(v + 0.3, i, f'{v:.1f}M', va='center')

    plt.suptitle(
        'Distribuição da Exposição à IA Generativa na Força de Trabalho Brasileira\n'
        f'{PNAD_ANO} Q{PNAD_TRIMESTRE}',
        fontsize=14, y=1.02
    )
    plt.tight_layout()

    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig1_distribuicao_exposicao.{ext}',
                    dpi=300, bbox_inches='tight')

    logger.info("Figura 1 salva")
    plt.close()


def figure2_heatmap(df):
    """FIGURA 2: Heatmap Região x Setor (17 setores x 5 regiões)"""

    logger.info("\n=== FIGURA 2: Heatmap Região x Setor ===")

    mask = df['exposure_score'].notna() & df['setor_agregado'].notna()
    subset = df[mask]

    def calc_weighted_mean(group):
        return weighted_mean(group['exposure_score'], group['peso'])

    pivot = subset.groupby(['setor_agregado', 'regiao']).apply(calc_weighted_mean).unstack()

    # Ordenar setores por exposição média decrescente
    pivot['_mean'] = pivot.mean(axis=1)
    pivot = pivot.sort_values('_mean', ascending=True).drop(columns='_mean')

    # Ordenar regiões
    regiao_order = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
    pivot = pivot[[r for r in regiao_order if r in pivot.columns]]

    fig, ax = plt.subplots(figsize=(10, 14))

    sns.heatmap(
        pivot,
        annot=True,
        fmt='.3f',
        cmap='YlOrRd',
        cbar_kws={'label': 'Score de Exposição'},
        ax=ax,
        linewidths=0.5,
        annot_kws={'size': 9}
    )

    ax.set_title(
        f'Exposição à IA Generativa por Setor e Região\nBrasil - {PNAD_ANO} Q{PNAD_TRIMESTRE}',
        fontsize=14
    )
    ax.set_xlabel('Região')
    ax.set_ylabel('Setor de Atividade')

    plt.tight_layout()

    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig2_heatmap_regiao_setor.{ext}',
                    dpi=300, bbox_inches='tight')

    logger.info("Figura 2 salva")
    plt.close()


def figure3_renda(df):
    """FIGURA 3: Perfil Salarial por Decil de Exposição"""

    logger.info("\n=== FIGURA 3: Renda por Exposição ===")

    # Filtrar: apenas quem tem renda E decil definido
    mask = (df['tem_renda'] == 1) & df['decil_exposure'].notna()
    subset = df[mask]

    renda_decil = subset.groupby('decil_exposure').apply(
        lambda x: weighted_mean(x['rendimento_habitual'], x['peso'])
    )

    # Garantir ordem D1..D10
    renda_decil = renda_decil.reindex([d for d in DECIL_ORDER if d in renda_decil.index])

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(range(len(renda_decil)), renda_decil.values,
                  color='teal', edgecolor='black', alpha=0.8)

    ax.set_xticks(range(len(renda_decil)))
    ax.set_xticklabels(renda_decil.index, rotation=0)
    ax.set_xlabel('Decil de Exposição à IA')
    ax.set_ylabel('Rendimento Médio Mensal (R$)')
    ax.set_title(
        f'Rendimento Médio por Decil de Exposição à IA Generativa\n'
        f'Brasil - {PNAD_ANO} Q{PNAD_TRIMESTRE} (apenas com renda declarada)'
    )

    # Linha de tendência
    x_numeric = np.arange(1, len(renda_decil) + 1)
    slope, intercept, r_value, p_value, std_err = linregress(x_numeric, renda_decil.values)
    trend_line = slope * x_numeric + intercept
    ax.plot(range(len(renda_decil)), trend_line, 'r--', linewidth=2,
            label=f'Tendência (R² = {r_value**2:.3f})')

    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))

    plt.tight_layout()

    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig3_renda_exposicao.{ext}',
                    dpi=300, bbox_inches='tight')

    logger.info(f"Figura 3 salva (R² = {r_value**2:.3f})")
    plt.close()


def figure4_decomposicao(df):
    """FIGURA 4: Decomposição Demográfica por Gradiente (4 painéis)"""

    logger.info("\n=== FIGURA 4: Decomposição Demográfica ===")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Usar 6 gradientes oficiais (sem "Sem classificação")
    gradient_display = [g for g in GRADIENT_ORDER if g != 'Sem classificação']
    mask = df['exposure_gradient'].isin(gradient_display)
    subset = df[mask]

    # Labels PT para eixo Y
    def _reindex(frame):
        return frame.reindex([g for g in gradient_display if g in frame.index])

    def _rename_y(ax_):
        labels = ax_.get_yticklabels()
        ax_.set_yticklabels([GRADIENT_LABELS_PT.get(l.get_text(), l.get_text()) for l in labels])

    # Painel A: Por gênero
    gender_comp = subset.groupby(['exposure_gradient', 'sexo_texto'])['peso'].sum().unstack(fill_value=0)
    gender_comp = _reindex(gender_comp)
    gender_pct = gender_comp.div(gender_comp.sum(axis=1), axis=0)

    gender_pct.plot(kind='barh', stacked=True, ax=axes[0, 0],
                    color=['lightblue', 'lightpink'], edgecolor='black')
    axes[0, 0].set_title('(A) Composição por Gênero')
    axes[0, 0].set_xlabel('Proporção')
    axes[0, 0].legend(title='Sexo')
    _rename_y(axes[0, 0])

    # Painel B: Por raça
    race_comp = subset.groupby(['exposure_gradient', 'raca_agregada'])['peso'].sum().unstack(fill_value=0)
    race_comp = _reindex(race_comp)
    race_pct = race_comp.div(race_comp.sum(axis=1), axis=0)

    race_pct.plot(kind='barh', stacked=True, ax=axes[0, 1],
                  color=['#d4a574', '#8b6914', '#a9a9a9'], edgecolor='black')
    axes[0, 1].set_title('(B) Composição por Raça')
    axes[0, 1].set_xlabel('Proporção')
    axes[0, 1].legend(title='Raça')
    _rename_y(axes[0, 1])

    # Painel C: Por formalidade
    formal_comp = subset.groupby(['exposure_gradient', 'formal'])['peso'].sum().unstack(fill_value=0)
    formal_comp = _reindex(formal_comp)
    formal_comp.columns = ['Informal', 'Formal']
    formal_pct = formal_comp.div(formal_comp.sum(axis=1), axis=0)

    formal_pct.plot(kind='barh', stacked=True, ax=axes[1, 0],
                    color=['lightcoral', 'lightgreen'], edgecolor='black')
    axes[1, 0].set_title('(C) Composição por Formalidade')
    axes[1, 0].set_xlabel('Proporção')
    axes[1, 0].legend(title='Vínculo')
    _rename_y(axes[1, 0])

    # Painel D: Por faixa etária
    age_comp = subset.groupby(['exposure_gradient', 'faixa_etaria'])['peso'].sum().unstack(fill_value=0)
    age_comp = _reindex(age_comp)
    age_pct = age_comp.div(age_comp.sum(axis=1), axis=0)

    cmap = plt.cm.viridis(np.linspace(0.2, 0.8, len(age_pct.columns)))
    age_pct.plot(kind='barh', stacked=True, ax=axes[1, 1],
                 color=cmap, edgecolor='black')
    axes[1, 1].set_title('(D) Composição por Faixa Etária')
    axes[1, 1].set_xlabel('Proporção')
    axes[1, 1].legend(title='Idade', bbox_to_anchor=(1.05, 1))
    _rename_y(axes[1, 1])

    plt.suptitle(
        f'Composição Demográfica por Gradiente de Exposição à IA\n'
        f'Brasil - {PNAD_ANO} Q{PNAD_TRIMESTRE}',
        fontsize=14, y=1.02
    )
    plt.tight_layout()

    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig4_decomposicao_demografica.{ext}',
                    dpi=300, bbox_inches='tight')

    logger.info("Figura 4 salva")
    plt.close()


# ---------------------------------------------------------------------------
# Figuras 5-8: Novas
# ---------------------------------------------------------------------------

def figure5_setores(df):
    """FIGURA 5: Exposição por Setor (barras horizontais, highlight setores críticos)"""

    logger.info("\n=== FIGURA 5: Exposição por Setor ===")

    mask = df['exposure_score'].notna() & df['setor_agregado'].notna()
    subset = df[mask]

    setor_stats = subset.groupby('setor_agregado').apply(
        lambda x: pd.Series({
            'exposure_mean': weighted_mean(x['exposure_score'], x['peso']),
            'pop_milhoes': x['peso'].sum() / 1e6,
        })
    ).sort_values('exposure_mean')

    fig, ax = plt.subplots(figsize=(10, 10))

    # Cores: highlight para setores críticos IA
    colors = [
        '#d62728' if s in SETORES_CRITICOS_IA else 'steelblue'
        for s in setor_stats.index
    ]

    bars = ax.barh(range(len(setor_stats)), setor_stats['exposure_mean'],
                   color=colors, edgecolor='black', alpha=0.85)

    ax.set_yticks(range(len(setor_stats)))
    ax.set_yticklabels(setor_stats.index)
    ax.set_xlabel('Score Médio de Exposição')
    ax.set_title(
        f'Exposição à IA Generativa por Setor de Atividade\n'
        f'Brasil - {PNAD_ANO} Q{PNAD_TRIMESTRE}'
    )

    # Valores ao lado das barras
    for i, (exp, pop) in enumerate(zip(setor_stats['exposure_mean'], setor_stats['pop_milhoes'])):
        ax.text(exp + 0.005, i, f'{exp:.3f} ({pop:.1f}M)', va='center', fontsize=9)

    # Legenda manual
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#d62728', edgecolor='black', label='Setor Crítico IA'),
        Patch(facecolor='steelblue', edgecolor='black', label='Demais Setores'),
    ]
    ax.legend(handles=legend_elements, loc='lower right')

    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()

    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig5_exposicao_setores.{ext}',
                    dpi=300, bbox_inches='tight')

    logger.info("Figura 5 salva")
    plt.close()


def figure6_genero_raca(df):
    """FIGURA 6: Exposição por Gênero e Raça dentro de cada Quintil"""

    logger.info("\n=== FIGURA 6: Gênero e Raça por Quintil ===")

    mask = df['exposure_score'].notna() & df['quintil_exposure'].notna()
    subset = df[mask]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Painel A: Por sexo dentro de cada quintil
    sexo_quintil = subset.groupby(['quintil_exposure', 'sexo_texto']).apply(
        lambda x: weighted_mean(x['exposure_score'], x['peso'])
    ).unstack()
    sexo_quintil = sexo_quintil.reindex([q for q in QUINTIL_ORDER if q in sexo_quintil.index])

    sexo_quintil.plot(kind='bar', ax=ax1, color=['lightblue', 'lightpink'],
                      edgecolor='black', width=0.7)
    ax1.set_title('(A) Exposição Média por Sexo e Quintil')
    ax1.set_xlabel('Quintil de Exposição')
    ax1.set_ylabel('Score Médio de Exposição')
    ax1.legend(title='Sexo')
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=0)

    # Painel B: Por raça dentro de cada quintil
    raca_quintil = subset.groupby(['quintil_exposure', 'raca_agregada']).apply(
        lambda x: weighted_mean(x['exposure_score'], x['peso'])
    ).unstack()
    raca_quintil = raca_quintil.reindex([q for q in QUINTIL_ORDER if q in raca_quintil.index])

    raca_quintil.plot(kind='bar', ax=ax2, color=['#d4a574', '#8b6914', '#a9a9a9'],
                      edgecolor='black', width=0.7)
    ax2.set_title('(B) Exposição Média por Raça e Quintil')
    ax2.set_xlabel('Quintil de Exposição')
    ax2.set_ylabel('Score Médio de Exposição')
    ax2.legend(title='Raça')
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=0)

    plt.suptitle(
        f'Desigualdade na Exposição à IA por Gênero e Raça\n'
        f'Brasil - {PNAD_ANO} Q{PNAD_TRIMESTRE}',
        fontsize=14, y=1.02
    )
    plt.tight_layout()

    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig6_genero_raca_quintil.{ext}',
                    dpi=300, bbox_inches='tight')

    logger.info("Figura 6 salva")
    plt.close()


def figure7_idade_instrucao(df):
    """FIGURA 7: Exposição por Faixa Etária e Nível de Instrução"""

    logger.info("\n=== FIGURA 7: Idade e Instrução ===")

    mask = df['exposure_score'].notna()
    subset = df[mask]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Painel A: Por faixa etária
    idade_stats = subset.groupby('faixa_etaria').apply(
        lambda x: weighted_mean(x['exposure_score'], x['peso'])
    )
    # Garantir ordem
    idade_stats = idade_stats.reindex([l for l in IDADE_LABELS if l in idade_stats.index])

    ax1.bar(range(len(idade_stats)), idade_stats.values,
            color='teal', edgecolor='black', alpha=0.8)
    ax1.set_xticks(range(len(idade_stats)))
    ax1.set_xticklabels(idade_stats.index)
    ax1.set_xlabel('Faixa Etária')
    ax1.set_ylabel('Score Médio de Exposição')
    ax1.set_title('(A) Exposição por Faixa Etária')

    for i, v in enumerate(idade_stats.values):
        ax1.text(i, v + 0.003, f'{v:.3f}', ha='center', fontsize=9)

    # Painel B: Por nível de instrução
    subset_instr = subset[subset['nivel_instrucao'].notna()].copy()
    subset_instr['nivel_instrucao_label'] = subset_instr['nivel_instrucao'].astype(int).map(NIVEL_INSTRUCAO_MAP)

    instrucao_stats = subset_instr.groupby('nivel_instrucao_label').apply(
        lambda x: weighted_mean(x['exposure_score'], x['peso'])
    )

    # Ordenar por nível (usar ordem do mapa)
    instrucao_order = [NIVEL_INSTRUCAO_MAP[k] for k in sorted(NIVEL_INSTRUCAO_MAP.keys())]
    instrucao_stats = instrucao_stats.reindex([i for i in instrucao_order if i in instrucao_stats.index])

    ax2.barh(range(len(instrucao_stats)), instrucao_stats.values,
             color='darkorange', edgecolor='black', alpha=0.8)
    ax2.set_yticks(range(len(instrucao_stats)))
    ax2.set_yticklabels(instrucao_stats.index)
    ax2.set_xlabel('Score Médio de Exposição')
    ax2.set_title('(B) Exposição por Nível de Instrução')

    for i, v in enumerate(instrucao_stats.values):
        ax2.text(v + 0.003, i, f'{v:.3f}', va='center', fontsize=9)

    plt.suptitle(
        f'Exposição à IA Generativa por Idade e Escolaridade\n'
        f'Brasil - {PNAD_ANO} Q{PNAD_TRIMESTRE}',
        fontsize=14, y=1.02
    )
    plt.tight_layout()

    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig7_idade_instrucao.{ext}',
                    dpi=300, bbox_inches='tight')

    logger.info("Figura 7 salva")
    plt.close()


def figure8_formalidade_renda(df):
    """FIGURA 8: Formalidade e Renda (2 painéis)"""

    logger.info("\n=== FIGURA 8: Formalidade e Renda ===")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    mask = df['exposure_score'].notna()
    subset = df[mask]

    # Painel A: Exposição média formal vs informal
    formal_stats = subset.groupby('formal').apply(
        lambda x: pd.Series({
            'exposure_mean': weighted_mean(x['exposure_score'], x['peso']),
            'pop_milhoes': x['peso'].sum() / 1e6,
        })
    )
    formal_labels = ['Informal', 'Formal']

    bars = ax1.bar(formal_labels, formal_stats['exposure_mean'],
                   color=['lightcoral', 'lightgreen'], edgecolor='black', width=0.5)

    for i, (exp, pop) in enumerate(zip(formal_stats['exposure_mean'], formal_stats['pop_milhoes'])):
        ax1.text(i, exp + 0.005, f'{exp:.3f}\n({pop:.1f}M)', ha='center', fontsize=10)

    ax1.set_ylabel('Score Médio de Exposição')
    ax1.set_title('(A) Exposição: Formal vs Informal')
    ax1.grid(axis='y', alpha=0.3)

    # Painel B: Rendimento médio por quintil, split formal/informal
    mask_renda = (df['tem_renda'] == 1) & df['quintil_exposure'].notna()
    subset_renda = df[mask_renda]

    renda_formal = subset_renda.groupby(['quintil_exposure', 'formal']).apply(
        lambda x: weighted_mean(x['rendimento_habitual'], x['peso'])
    ).unstack()
    renda_formal = renda_formal.reindex([q for q in QUINTIL_ORDER if q in renda_formal.index])
    renda_formal.columns = ['Informal', 'Formal']

    renda_formal.plot(kind='bar', ax=ax2, color=['lightcoral', 'lightgreen'],
                      edgecolor='black', width=0.7)
    ax2.set_title('(B) Rendimento por Quintil e Formalidade')
    ax2.set_xlabel('Quintil de Exposição')
    ax2.set_ylabel('Rendimento Médio (R$)')
    ax2.legend(title='Vínculo')
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=0)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))

    plt.suptitle(
        f'Formalidade e Rendimento por Exposição à IA\n'
        f'Brasil - {PNAD_ANO} Q{PNAD_TRIMESTRE}',
        fontsize=14, y=1.02
    )
    plt.tight_layout()

    for ext in ['png', 'pdf']:
        fig.savefig(OUTPUTS_FIGURES / f'fig8_formalidade_renda.{ext}',
                    dpi=300, bbox_inches='tight')

    logger.info("Figura 8 salva")
    plt.close()


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

def generate_all_figures():
    """Gera todas as figuras"""

    logger.info("=" * 60)
    logger.info("GERAÇÃO DE FIGURAS - ETAPA 1")
    logger.info("=" * 60)

    df = load_data()

    figure1_distribuicao(df)
    figure2_heatmap(df)
    figure3_renda(df)
    figure4_decomposicao(df)
    figure5_setores(df)
    figure6_genero_raca(df)
    figure7_idade_instrucao(df)
    figure8_formalidade_renda(df)

    logger.info("\n" + "=" * 60)
    logger.info("TODAS AS 8 FIGURAS GERADAS COM SUCESSO")
    logger.info(f"Arquivos salvos em: {OUTPUTS_FIGURES}")
    logger.info("=" * 60)


if __name__ == "__main__":
    generate_all_figures()
