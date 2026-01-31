"""
Script 08: Tabela Detalhada de Exposicao a IA por Classificacao Ocupacional COD
Entrada: data/raw/Estrutura Ocupacao COD.xls, data/processed/pnad_ilo_merged.csv
Saida: outputs/tables/tabela_detalhada_cod.csv e .pdf
"""

import logging
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adicionar diretorio raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import DATA_RAW, DATA_PROCESSED, OUTPUTS_TABLES, OUTPUTS_LOGS, GRANDES_GRUPOS
from src.utils.weighted_stats import weighted_mean, weighted_std

# Para geracao de PDF
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '08_tabela_detalhada.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def read_cod_structure(path):
    """
    Le arquivo XLS com estrutura das ocupacoes COD e extrai hierarquia.
    Retorna dicionario com nomes para cada codigo em cada nivel.
    """
    logger.info(f"Lendo estrutura COD de: {path}")
    
    # Ler arquivo XLS (formato antigo .xls), pulando a primeira linha e usando a segunda como header
    try:
        df_cod = pd.read_excel(path, sheet_name='Estrutura COD', engine='xlrd', header=1)
    except Exception as e:
        logger.warning(f"Erro com xlrd, tentando openpyxl: {e}")
        df_cod = pd.read_excel(path, sheet_name='Estrutura COD', engine='openpyxl', header=1)
    
    # Renomear colunas para nomes padronizados
    df_cod.columns = ['Grande Grupo', 'Subgrupo principal', 'Subgrupo', 'Grupo de base', 'Denominacao']
    
    logger.info(f"Colunas encontradas: {df_cod.columns.tolist()}")
    logger.info(f"Linhas no arquivo: {len(df_cod)}")
    
    return df_cod


def process_cod_structure(df_cod):
    """
    Processa estrutura COD extraindo codigos e denominacoes.
    """
    cod_names = {1: {}, 2: {}, 3: {}, 4: {}}
    
    logger.info(f"Processando {len(df_cod)} linhas...")
    
    for idx, row in df_cod.iterrows():
        denominacao = row.get('Denominacao')
        if pd.isna(denominacao) or not str(denominacao).strip():
            continue
        denominacao = str(denominacao).strip()
        
        # Grande Grupo (1 digito)
        gg = row.get('Grande Grupo')
        if pd.notna(gg):
            try:
                val = str(int(gg))
                if len(val) == 1:
                    cod_names[1][val] = denominacao
            except (ValueError, TypeError):
                pass
        
        # Subgrupo Principal (2 digitos)
        sp = row.get('Subgrupo principal')
        if pd.notna(sp):
            try:
                val = str(int(sp)).zfill(2)
                if len(val) == 2:
                    cod_names[2][val] = denominacao
            except (ValueError, TypeError):
                pass
        
        # Subgrupo (3 digitos)
        sg = row.get('Subgrupo')
        if pd.notna(sg):
            try:
                val = str(int(sg)).zfill(3)
                if len(val) == 3:
                    cod_names[3][val] = denominacao
            except (ValueError, TypeError):
                pass
        
        # Grupo de Base (4 digitos)
        gb = row.get('Grupo de base')
        if pd.notna(gb):
            try:
                val = str(int(gb)).zfill(4)
                if len(val) == 4:
                    cod_names[4][val] = denominacao
            except (ValueError, TypeError):
                pass
    
    for nivel, nomes in cod_names.items():
        logger.info(f"Nivel {nivel}: {len(nomes)} codigos")
    
    return cod_names


def calculate_exposure_by_level(df, cod_names):
    """
    Calcula estatisticas de exposicao para cada codigo em cada nivel.
    """
    logger.info("\n=== CALCULANDO EXPOSICAO POR NIVEL ===")
    
    df['cod_ocupacao'] = df['cod_ocupacao'].astype(str).str.zfill(4)
    df['cod_1d'] = df['cod_ocupacao'].str[:1]
    df['cod_2d'] = df['cod_ocupacao'].str[:2]
    df['cod_3d'] = df['cod_ocupacao'].str[:3]
    df['cod_4d'] = df['cod_ocupacao']
    
    total_peso = df['peso'].sum()
    results = []
    
    for nivel in [1, 2, 3, 4]:
        col_cod = f'cod_{nivel}d'
        logger.info(f"Processando nivel {nivel}...")
        
        for codigo in sorted(df[col_cod].unique()):
            mask = df[col_cod] == codigo
            subset = df[mask]
            
            if len(subset) == 0:
                continue
            
            n_obs = len(subset)
            n_trabalhadores = subset['peso'].sum()
            pct_forca_trabalho = (n_trabalhadores / total_peso) * 100
            
            mask_valid = subset['exposure_score'].notna()
            if mask_valid.sum() > 0:
                exp_media = weighted_mean(
                    subset.loc[mask_valid, 'exposure_score'],
                    subset.loc[mask_valid, 'peso']
                )
                exp_std = weighted_std(
                    subset.loc[mask_valid, 'exposure_score'],
                    subset.loc[mask_valid, 'peso']
                )
            else:
                exp_media = np.nan
                exp_std = np.nan
            
            match_levels = subset['match_level'].value_counts()
            pct_4digit = (match_levels.get('4-digit', 0) / len(subset)) * 100
            
            denominacao = cod_names.get(nivel, {}).get(codigo, '')
            if not denominacao:
                if nivel == 1:
                    denominacao = GRANDES_GRUPOS.get(codigo, f'Grupo {codigo}')
                else:
                    denominacao = f'Codigo {codigo}'
            
            results.append({
                'codigo': codigo,
                'denominacao': denominacao,
                'nivel': nivel,
                'exposicao_media': exp_media,
                'exposicao_std': exp_std,
                'n_trabalhadores': n_trabalhadores,
                'pct_forca_trabalho': pct_forca_trabalho,
                'n_observacoes': n_obs,
                'pct_match_4digit': pct_4digit
            })
    
    df_results = pd.DataFrame(results)
    logger.info(f"Total de grupos: {len(df_results)}")
    return df_results


def add_methodological_notes(df_results, threshold_match=80):
    """
    Adiciona observacoes metodologicas.
    """
    logger.info("\n=== ADICIONANDO OBSERVACOES ===")
    
    obs_list = []
    for idx, row in df_results.iterrows():
        obs = []
        if row['pct_match_4digit'] < threshold_match:
            obs.append('*')
        if pd.isna(row['exposicao_media']):
            obs.append('t')
        if row['n_observacoes'] < 30:
            obs.append('d')
        obs_list.append(''.join(obs))
    
    df_results['observacoes'] = obs_list
    
    n_asterisco = sum(1 for o in obs_list if '*' in o)
    logger.info(f"Grupos com match indireto (*): {n_asterisco}")
    
    return df_results


def create_hierarchical_table(df_results):
    """
    Organiza resultados em formato hierarquico.
    """
    df_results = df_results.copy()
    df_results['sort_key'] = df_results['codigo'].str.ljust(4, '0')
    df_sorted = df_results.sort_values(['sort_key', 'nivel'])
    return df_sorted.drop(columns=['sort_key'])


def export_csv(df_results, output_path):
    """
    Exporta tabela em CSV.
    """
    logger.info(f"Exportando CSV: {output_path}")
    
    df_export = df_results[[
        'codigo', 'denominacao', 'nivel', 'exposicao_media', 'exposicao_std',
        'n_trabalhadores', 'pct_forca_trabalho', 'n_observacoes',
        'pct_match_4digit', 'observacoes'
    ]].copy()
    
    df_export['exposicao_media'] = df_export['exposicao_media'].round(3)
    df_export['exposicao_std'] = df_export['exposicao_std'].round(3)
    df_export['n_trabalhadores'] = df_export['n_trabalhadores'].round(0).astype('Int64')
    df_export['pct_forca_trabalho'] = df_export['pct_forca_trabalho'].round(2)
    df_export['pct_match_4digit'] = df_export['pct_match_4digit'].round(1)
    
    df_export.columns = [
        'Codigo', 'Denominacao', 'Nivel', 'Exposicao Media', 'Desvio Padrao',
        'N Trabalhadores', '% Forca Trabalho', 'N Observacoes',
        '% Match Direto', 'Obs'
    ]
    
    df_export.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"CSV salvo: {len(df_export)} linhas")
    return df_export


def get_exposure_color(value):
    """
    Retorna cor RGB baseada no valor de exposicao.
    """
    if pd.isna(value):
        return (0.9, 0.9, 0.9)
    if value < 0.20:
        return (0.2, 0.6, 0.2)
    elif value < 0.35:
        return (0.5, 0.8, 0.4)
    elif value < 0.45:
        return (1.0, 0.9, 0.3)
    elif value < 0.55:
        return (1.0, 0.6, 0.2)
    else:
        return (0.9, 0.3, 0.2)


def export_pdf_with_colors(df_results, output_path):
    """
    Gera PDF em paisagem com cores gradiente.
    """
    logger.info(f"Gerando PDF: {output_path}")
    
    fig_width = 16
    fig_height = 11
    rows_per_page = 35
    n_rows = len(df_results)
    n_pages = (n_rows // rows_per_page) + (1 if n_rows % rows_per_page > 0 else 0)
    
    logger.info(f"Gerando {n_pages} paginas para {n_rows} linhas")
    
    with PdfPages(output_path) as pdf:
        for page in range(n_pages):
            start_idx = page * rows_per_page
            end_idx = min((page + 1) * rows_per_page, n_rows)
            df_page = df_results.iloc[start_idx:end_idx]
            
            fig, ax = plt.subplots(figsize=(fig_width, fig_height))
            ax.axis('off')
            
            if page == 0:
                title = 'Tabela Detalhada de Exposicao a IA por Classificacao Ocupacional COD\nBrasil - PNAD Continua 2025'
            else:
                title = f'Tabela Detalhada de Exposicao a IA (continuacao - pagina {page + 1})'
            
            fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
            
            col_labels = ['Codigo', 'Denominacao', 'Nivel', 'Exp. Media',
                         'N Trab. (mil)', '% F.T.', 'Obs']
            
            table_data = []
            cell_colors = []
            
            for idx, row in df_page.iterrows():
                indent = '  ' * (row['nivel'] - 1)
                denom = indent + str(row['denominacao'])[:50]
                n_trab_mil = row['n_trabalhadores'] / 1000
                
                table_data.append([
                    row['codigo'],
                    denom,
                    str(row['nivel']),
                    f"{row['exposicao_media']:.3f}" if pd.notna(row['exposicao_media']) else '-',
                    f"{n_trab_mil:,.0f}",
                    f"{row['pct_forca_trabalho']:.2f}%",
                    row['observacoes']
                ])
                
                exp_color = get_exposure_color(row['exposicao_media'])
                row_colors = ['white', 'white', 'white', exp_color, 'white', 'white', 'white']
                cell_colors.append(row_colors)
            
            table = ax.table(
                cellText=table_data,
                colLabels=col_labels,
                cellColours=cell_colors,
                colColours=['#4472C4'] * len(col_labels),
                cellLoc='left',
                colLoc='center',
                loc='upper center',
                bbox=[0.02, 0.12, 0.96, 0.82]
            )
            
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            
            col_widths = [0.08, 0.45, 0.05, 0.10, 0.12, 0.10, 0.06]
            for i, width in enumerate(col_widths):
                for j in range(len(table_data) + 1):
                    table[(j, i)].set_width(width)
            
            for i in range(len(col_labels)):
                table[(0, i)].set_text_props(color='white', fontweight='bold')
                table[(0, i)].set_height(0.04)
            
            # Escala de cores - lado esquerdo inferior (em TODAS as paginas)
            legend_elements = [
                mpatches.Patch(facecolor=(0.2, 0.6, 0.2), label='Baixa (< 0.20)'),
                mpatches.Patch(facecolor=(0.5, 0.8, 0.4), label='Mod. Baixa (0.20-0.35)'),
                mpatches.Patch(facecolor=(1.0, 0.9, 0.3), label='Moderada (0.35-0.45)'),
                mpatches.Patch(facecolor=(1.0, 0.6, 0.2), label='Alta (0.45-0.55)'),
                mpatches.Patch(facecolor=(0.9, 0.3, 0.2), label='Muito Alta (> 0.55)'),
                mpatches.Patch(facecolor=(0.9, 0.9, 0.9), label='Sem dados'),
            ]
            legend = ax.legend(
                handles=legend_elements, 
                loc='lower left',
                ncol=3, 
                fontsize=7, 
                title='Escala de Exposicao',
                title_fontsize=8,
                bbox_to_anchor=(0.02, -0.02),
                frameon=True,
                fancybox=True,
                shadow=False
            )
            
            # Observacoes - lado direito inferior (em TODAS as paginas)
            notas = (
                "Observacoes:\n"
                "* Match indireto (exposicao por agregacao)\n"
                "t Sem dados de exposicao\n"
                "d Menos de 30 observacoes\n"
                f"Pagina {page + 1} de {n_pages}"
            )
            fig.text(0.98, 0.02, notas, fontsize=7, va='bottom', ha='right', 
                    style='italic', family='monospace',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # Fonte na parte central inferior
            fig.text(0.5, 0.01, 
                    'Fonte: PNAD Continua 2025 (IBGE) e ILO GenAI Exposure Index (Gmyrek et al., 2025)',
                    fontsize=7, va='bottom', ha='center', style='italic')
            
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight', dpi=150)
            plt.close(fig)
    
    logger.info(f"PDF salvo com {n_pages} paginas")


def run_tabela_detalhada():
    """Executa geracao completa da tabela detalhada."""
    
    logger.info("=" * 60)
    logger.info("TABELA DETALHADA DE EXPOSICAO POR COD")
    logger.info("=" * 60)
    
    # 1. Ler estrutura COD
    cod_file = DATA_RAW / "Estrutura Ocupacao COD.xls"
    if not cod_file.exists():
        cod_file = DATA_RAW / "Estrutura Ocupação COD.xls"
    
    df_cod = read_cod_structure(cod_file)
    cod_names = process_cod_structure(df_cod)
    
    total_nomes = sum(len(v) for v in cod_names.values())
    logger.info(f"Total de denominacoes: {total_nomes}")
    
    # 2. Carregar dados PNAD
    logger.info("\nCarregando dados PNAD...")
    df = pd.read_csv(DATA_PROCESSED / "pnad_ilo_merged.csv")
    logger.info(f"Dados carregados: {len(df):,} observacoes")
    
    # 3. Calcular exposicao por nivel
    df_results = calculate_exposure_by_level(df, cod_names)
    
    # 4. Adicionar observacoes metodologicas
    df_results = add_methodological_notes(df_results)
    
    # 5. Organizar hierarquicamente
    df_results = create_hierarchical_table(df_results)
    
    # 6. Exportar CSV
    csv_path = OUTPUTS_TABLES / "tabela_detalhada_cod.csv"
    export_csv(df_results, csv_path)
    
    # 7. Exportar PDF
    pdf_path = OUTPUTS_TABLES / "tabela_detalhada_cod.pdf"
    export_pdf_with_colors(df_results, pdf_path)
    
    logger.info("\n" + "=" * 60)
    logger.info("TABELA DETALHADA GERADA COM SUCESSO!")
    logger.info(f"CSV: {csv_path}")
    logger.info(f"PDF: {pdf_path}")
    logger.info("=" * 60)
    
    return df_results


if __name__ == "__main__":
    df_results = run_tabela_detalhada()
    print("\nTabela detalhada gerada com sucesso!")
