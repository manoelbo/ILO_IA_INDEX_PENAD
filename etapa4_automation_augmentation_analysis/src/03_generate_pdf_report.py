import logging
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches

# Adicionar diretório raiz ao path para importações
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from etapa4_automation_augmentation_analysis.config.settings import *
from etapa4_automation_augmentation_analysis.src.utils.weighted_stats import weighted_mean

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '03_generate_pdf.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_color_by_index(val):
    """Retorna cor baseada no Automation Index (Cai)."""
    if pd.isna(val):
        return (0.9, 0.9, 0.9)
    # Automação (Positivo) -> Vermelho
    # Aumentação (Negativo) -> Verde
    if val > 0.3:
        return (0.9, 0.3, 0.2) # Vermelho forte
    elif val > 0:
        return (1.0, 0.6, 0.2) # Laranja
    elif val > -0.3:
        return (0.5, 0.8, 0.4) # Verde claro
    else:
        return (0.2, 0.6, 0.2) # Verde forte

def run_pdf_report():
    """Gera relatório PDF detalhado por ocupação."""
    
    logger.info("Gerando Relatório PDF Detalhado...")

    # 1. Carregar Dados de Ocupações (gerados no Script 02)
    occ_csv = OUTPUTS_TABLES / "tabela_detalhada_ocupacoes_ia.csv"
    if not occ_csv.exists():
        logger.error(f"Tabela de ocupações não encontrada: {occ_csv}")
        return
    
    df_occ = pd.read_csv(occ_csv)
    
    # 2. Carregar Nomes da Estrutura COD
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("cod_detailed", 
                                                     ROOT_DIR / "etapa1_ia_generativa" / "src" / "08_tabela_detalhada_cod.py")
        cod_detailed = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cod_detailed)
        
        df_cod = cod_detailed.read_cod_structure(COD_STRUCTURE)
        cod_names = cod_detailed.process_cod_structure(df_cod)
        # Pegar apenas nível 4
        names_map = cod_names[4]
    except Exception as e:
        logger.warning(f"Erro ao carregar nomes do COD via importlib: {e}")
        names_map = {}

    # 3. Preparar Dados para o PDF
    df_occ['cod_ocupacao'] = df_occ['cod_ocupacao'].astype(str).str.zfill(4)
    df_occ['denominacao'] = df_occ['cod_ocupacao'].map(names_map).fillna("Ocupação " + df_occ['cod_ocupacao'])
    
    # Ordenar por Automation Index
    df_sorted = df_occ.sort_values('automation_index_cai', ascending=False)

    # 4. Gerar PDF
    output_pdf = OUTPUTS_REPORTS / "relatorio_detalhado_ia_brasil.pdf"
    
    fig_width = 16
    fig_height = 11
    rows_per_page = 35
    n_rows = len(df_sorted)
    n_pages = (n_rows // rows_per_page) + (1 if n_rows % rows_per_page > 0 else 0)
    
    logger.info(f"Gerando {n_pages} páginas para {n_rows} ocupações...")
    
    with PdfPages(output_pdf) as pdf:
        for page in range(n_pages):
            start_idx = page * rows_per_page
            end_idx = min((page + 1) * rows_per_page, n_rows)
            df_page = df_sorted.iloc[start_idx:end_idx]
            
            fig, ax = plt.subplots(figsize=(fig_width, fig_height))
            ax.axis('off')
            
            title = 'Impacto da IA Generativa (Anthropic V4) no Mercado de Trabalho Brasileiro\n'
            if page == 0:
                title += 'Tabela Detalhada: Automation vs Augmentation (PNAD 2025)'
            else:
                title += f'Continuação (página {page + 1})'
            
            fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
            
            col_labels = ['Código', 'Denominação', 'Auto Index', 'Auto %', 'Aug %', 'ILO Score', 'Rend. Médio', 'Obs']
            
            table_data = []
            cell_colors = []
            
            for idx, row in df_page.iterrows():
                table_data.append([
                    row['cod_ocupacao'],
                    str(row['denominacao'])[:50],
                    f"{row['automation_index_cai']:.2f}",
                    f"{row['automation_share_cai']:.1%}",
                    f"{row['augmentation_share_cai']:.1%}",
                    f"{row['exposure_score']:.2f}" if pd.notna(row['exposure_score']) else '-',
                    f"R$ {row['rendimento_todos']:,.0f}",
                    row['imputation_method'].split('_')[0] if pd.notna(row['imputation_method']) else '-'
                ])
                
                # Cor baseada no Automation Index
                color = get_color_by_index(row['automation_index_cai'])
                row_colors = ['white', 'white', color, 'white', 'white', 'white', 'white', 'white']
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
            
            # Legendas e Notas
            legend_elements = [
                mpatches.Patch(facecolor=(0.9, 0.3, 0.2), label='Alta Automação (> 0.3)'),
                mpatches.Patch(facecolor=(1.0, 0.6, 0.2), label='Mod. Automação (0 a 0.3)'),
                mpatches.Patch(facecolor=(0.5, 0.8, 0.4), label='Mod. Aprimoramento (-0.3 a 0)'),
                mpatches.Patch(facecolor=(0.2, 0.6, 0.2), label='Alto Aprimoramento (< -0.3)'),
            ]
            ax.legend(handles=legend_elements, loc='lower left', ncol=2, fontsize=8, title='Escala de Impacto IA')
            
            fig.text(0.5, 0.01, 'Fonte: Elaboração própria com dados Anthropic Index V4 (2026), ILO (2025) e PNAD Contínua (IBGE).', 
                    fontsize=7, va='bottom', ha='center', style='italic')
            
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight', dpi=150)
            plt.close(fig)
            
    logger.info(f"Relatório PDF salvo com sucesso em: {output_pdf}")

if __name__ == "__main__":
    run_pdf_report()
