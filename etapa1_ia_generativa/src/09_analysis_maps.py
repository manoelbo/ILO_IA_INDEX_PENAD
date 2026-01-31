"""
Script 09: Geração de mapas coropléticos de exposição à IA
Entrada: data/processed/pnad_ilo_merged.csv
Saída: outputs/figures/mapa_*.png e *.pdf
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.patheffects as pe
import geopandas as gpd
import geobr
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *
from src.utils.weighted_stats import weighted_mean

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(OUTPUTS_LOGS / '09_maps.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

plt.rcParams['figure.figsize'] = (12, 10)
plt.rcParams['font.size'] = 10

REGION_STATES = {
    'Norte': ['RO', 'AC', 'AM', 'RR', 'PA', 'AP', 'TO'],
    'Nordeste': ['MA', 'PI', 'CE', 'RN', 'PB', 'PE', 'AL', 'SE', 'BA'],
    'Sudeste': ['MG', 'ES', 'RJ', 'SP'],
    'Sul': ['PR', 'SC', 'RS'],
    'Centro-Oeste': ['MS', 'MT', 'GO', 'DF']
}

COLORMAPS = {
    'exposicao_media': 'YlOrRd',
    'not_exposed': 'Greens',
    'exposicao_baixa': 'Blues',
    'exposicao_media_grad': 'Oranges',
    'exposicao_alta': 'Reds'
}


def load_data():
    df = pd.read_csv(DATA_PROCESSED / "pnad_ilo_merged.csv")
    logger.info(f"Dados carregados: {len(df):,} obs")
    return df


def load_geodata():
    logger.info("Carregando shapefiles...")
    states = geobr.read_state(year=2020)
    states['abbrev_state'] = states['abbrev_state'].str.upper()
    return states


def create_regions_geodata(states_gdf):
    regions_list = []
    for region_name, state_codes in REGION_STATES.items():
        region_states = states_gdf[states_gdf['abbrev_state'].isin(state_codes)]
        if len(region_states) > 0:
            merged_geometry = region_states.geometry.union_all()
            regions_list.append({'name_region': region_name, 'geometry': merged_geometry})
    return gpd.GeoDataFrame(regions_list, crs=states_gdf.crs)


def aggregate_by_state(df):
    results = []
    for uf in df['sigla_uf'].unique():
        subset = df[df['sigla_uf'] == uf]
        total = subset['peso'].sum()
        exp = weighted_mean(subset['exposure_score'], subset['peso'])
        
        pct = {}
        for g in ['Not Exposed', 'Gradient 1-2', 'Gradient 3', 'Gradient 4 (Alta)']:
            p = subset[subset['exposure_gradient'] == g]['peso'].sum()
            pct[g] = (p / total * 100) if total > 0 else 0
        
        results.append({
            'sigla_uf': uf, 'regiao': subset['regiao'].iloc[0],
            'exposicao_media': exp, 'pct_not_exposed': pct['Not Exposed'],
            'pct_exposicao_baixa': pct['Gradient 1-2'],
            'pct_exposicao_media': pct['Gradient 3'],
            'pct_exposicao_alta': pct['Gradient 4 (Alta)']
        })
    return pd.DataFrame(results)


def aggregate_by_region(df):
    results = []
    for regiao in df['regiao'].unique():
        subset = df[df['regiao'] == regiao]
        total = subset['peso'].sum()
        exp = weighted_mean(subset['exposure_score'], subset['peso'])
        
        pct = {}
        for g in ['Not Exposed', 'Gradient 1-2', 'Gradient 3', 'Gradient 4 (Alta)']:
            p = subset[subset['exposure_gradient'] == g]['peso'].sum()
            pct[g] = (p / total * 100) if total > 0 else 0
        
        results.append({
            'regiao': regiao, 'exposicao_media': exp,
            'pct_not_exposed': pct['Not Exposed'],
            'pct_exposicao_baixa': pct['Gradient 1-2'],
            'pct_exposicao_media': pct['Gradient 3'],
            'pct_exposicao_alta': pct['Gradient 4 (Alta)']
        })
    return pd.DataFrame(results)


def create_map(gdf, metric, title, cmap, label_col, fmt='.1f', pct=True, fname=None):
    fig, ax = plt.subplots(1, 1, figsize=(14, 12))
    ax.set_axis_off()
    
    vmin, vmax = gdf[metric].min(), gdf[metric].max()
    gdf.plot(column=metric, cmap=cmap, linewidth=0.8, ax=ax,
             edgecolor='0.3', legend=False, vmin=vmin, vmax=vmax)
    
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.6, aspect=20, pad=0.02)
    cbar.set_label('% Força de Trabalho' if pct else 'Score', fontsize=12)
    
    for _, row in gdf.iterrows():
        c = row.geometry.centroid
        v = row[metric]
        vs = f"{v:{fmt}}%" if pct else f"{v:{fmt}}"
        nv = (v - vmin) / (vmax - vmin) if vmax > vmin else 0.5
        tc = 'white' if nv > 0.6 else 'black'
        ax.annotate(f"{row[label_col]}\n{vs}", xy=(c.x, c.y), ha='center', va='center',
                   fontsize=9, fontweight='bold', color=tc,
path_effects=[pe.withStroke(linewidth=2, 
                               foreground='white' if tc == 'black' else 'black')])
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    fig.text(0.5, 0.02, 'Fonte: PNAD 3T/2025 + ILO GenAI Scores', ha='center', fontsize=10, style='italic')
    plt.tight_layout()
    
    if fname:
        for ext in ['png', 'pdf']:
            fig.savefig(OUTPUTS_FIGURES / f'{fname}.{ext}', dpi=300, bbox_inches='tight', facecolor='white')
            logger.info(f"  Salvo: {fname}.{ext}")
    plt.close()


def generate_all_maps():
    logger.info("=" * 50)
    logger.info("GERAÇÃO DE MAPAS")
    logger.info("=" * 50)
    
    df = load_data()
    states = load_geodata()
    regions = create_regions_geodata(states)
    
    sd = aggregate_by_state(df)
    rd = aggregate_by_region(df)
    sd.to_csv(OUTPUTS_TABLES / "tabela_mapa_estados.csv", index=False)
    rd.to_csv(OUTPUTS_TABLES / "tabela_mapa_regioes.csv", index=False)
    
    sm = states.merge(sd, left_on='abbrev_state', right_on='sigla_uf')
    rm = regions.merge(rd, left_on='name_region', right_on='regiao')
    
    # C1: Exposição média
    logger.info("\n=== C1: Exposição Média ===")
    create_map(sm, 'exposicao_media', 'Exposição Média à IA por Estado\nBrasil 3T/2025',
               'YlOrRd', 'abbrev_state', '.3f', False, 'mapa_c1_exposicao_media_estado')
    create_map(rm, 'exposicao_media', 'Exposição Média à IA por Região\nBrasil 3T/2025',
               'YlOrRd', 'name_region', '.3f', False, 'mapa_c1_exposicao_media_regiao')
    
    # C2: Not Exposed
    logger.info("\n=== C2: Not Exposed ===")
    create_map(sm, 'pct_not_exposed', 'Força de Trabalho Não Exposta (%) por Estado\nBrasil 3T/2025',
               'Greens', 'abbrev_state', '.1f', True, 'mapa_c2_not_exposed_estado')
    create_map(rm, 'pct_not_exposed', 'Força de Trabalho Não Exposta (%) por Região\nBrasil 3T/2025',
               'Greens', 'name_region', '.1f', True, 'mapa_c2_not_exposed_regiao')
    
    # C3: Exposição Baixa
    logger.info("\n=== C3: Exposição Baixa ===")
    create_map(sm, 'pct_exposicao_baixa', 'Exposição Baixa à IA (%) por Estado\nGradient 1-2 - Brasil 3T/2025',
               'Blues', 'abbrev_state', '.1f', True, 'mapa_c3_exposicao_baixa_estado')
    create_map(rm, 'pct_exposicao_baixa', 'Exposição Baixa à IA (%) por Região\nGradient 1-2 - Brasil 3T/2025',
               'Blues', 'name_region', '.1f', True, 'mapa_c3_exposicao_baixa_regiao')
    
    # C4: Exposição Média
    logger.info("\n=== C4: Exposição Média (Grad 3) ===")
    create_map(sm, 'pct_exposicao_media', 'Exposição Média à IA (%) por Estado\nGradient 3 - Brasil 3T/2025',
               'Oranges', 'abbrev_state', '.1f', True, 'mapa_c4_exposicao_media_estado')
    create_map(rm, 'pct_exposicao_media', 'Exposição Média à IA (%) por Região\nGradient 3 - Brasil 3T/2025',
               'Oranges', 'name_region', '.1f', True, 'mapa_c4_exposicao_media_regiao')
    
    # C5: Exposição Alta
    logger.info("\n=== C5: Exposição Alta ===")
    create_map(sm, 'pct_exposicao_alta', 'Exposição Alta à IA (%) por Estado\nGradient 4 - Brasil 3T/2025',
               'Reds', 'abbrev_state', '.1f', True, 'mapa_c5_exposicao_alta_estado')
    create_map(rm, 'pct_exposicao_alta', 'Exposição Alta à IA (%) por Região\nGradient 4 - Brasil 3T/2025',
               'Reds', 'name_region', '.1f', True, 'mapa_c5_exposicao_alta_regiao')
    
    logger.info("\n" + "=" * 50)
    logger.info("MAPAS GERADOS!")
    logger.info("=" * 50)


if __name__ == "__main__":
    generate_all_maps()