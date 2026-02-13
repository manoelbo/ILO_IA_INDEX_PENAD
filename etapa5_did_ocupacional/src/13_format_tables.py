"""
Script 13: Format Tables for LaTeX

Generates publication-ready LaTeX tables from the DiD analysis results.

Inputs:
- outputs/tables/did_main_results.csv
- outputs/tables/heterogeneity_summary.csv
- outputs/tables/robustness_summary.csv
- outputs/tables/balance_table_pre.csv

Outputs:
- outputs/tables/table1_descriptives.tex
- outputs/tables/table2_main_did_results.tex
- outputs/tables/table3_heterogeneity.tex
- outputs/tables/table4_robustness.tex
- outputs/tables/appendix_all_tables.tex

Author: Claude Code
Date: 2026-02-08
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import (
    DATA_PROCESSED, OUTPUTS_TABLES, OUTPUTS_LOGS,
    OUTCOMES_VALID
)

# ============================================
# LOGGING SETUP
# ============================================

# Create log file
log_file = OUTPUTS_LOGS / '13_format_tables.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# UTILITY FUNCTIONS
# ============================================

def format_coef_se(coef, se, stars='', decimal_places=4):
    """
    Formats coefficient and standard error for LaTeX table.

    Parameters:
    -----------
    coef : float
        Coefficient value
    se : float
        Standard error
    stars : str
        Significance stars (*, **, ***)
    decimal_places : int
        Number of decimal places

    Returns:
    --------
    str: Formatted string like "0.0123*** \n (0.0045)"
    """
    if pd.isna(coef) or pd.isna(se):
        return "—"

    # Handle NaN/None stars
    if pd.isna(stars) or stars is None:
        stars = ''
    stars = str(stars).strip()

    # Format coefficient with stars
    coef_str = f"{coef:.{decimal_places}f}{stars}"

    # Format SE in parentheses
    se_str = f"({se:.{decimal_places}f})"

    return f"{coef_str} \\\\ {se_str}"


def escape_latex(text):
    """
    Escapes special LaTeX characters.

    Parameters:
    -----------
    text : str
        Text to escape

    Returns:
    --------
    str: Escaped text
    """
    if not isinstance(text, str):
        return str(text)

    # Define escape mappings
    escape_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
    }

    for char, escaped in escape_chars.items():
        text = text.replace(char, escaped)

    return text


def add_table_notes(notes_list, width='\\textwidth'):
    """
    Creates LaTeX table notes section.

    Parameters:
    -----------
    notes_list : list
        List of note strings
    width : str
        Width of the notes block

    Returns:
    --------
    str: LaTeX notes code
    """
    notes = "\\begin{tablenotes}\n"
    notes += "\\small\n"
    for note in notes_list:
        notes += f"\\item {note}\n"
    notes += "\\end{tablenotes}\n"

    return notes


def get_outcome_label(outcome):
    """
    Returns clean label for outcome variable.

    Parameters:
    -----------
    outcome : str
        Outcome variable name

    Returns:
    --------
    str: Clean label
    """
    labels = {
        'ln_renda': 'Log(Rendimento)',
        'horas_trabalhadas': 'Horas Trabalhadas',
        'ocupado': 'Ocupado',
        'formal': 'Formal',
        'informal': 'Informal'
    }
    return labels.get(outcome, outcome)


def get_group_label(group):
    """
    Returns clean label for demographic group.

    Parameters:
    -----------
    group : str
        Group variable name

    Returns:
    --------
    str: Clean label
    """
    labels = {
        'age': 'Idade (Jovem ≤30)',
        'gender': 'Gênero (Mulher)',
        'education': 'Educação (Superior)',
        'race': 'Raça (Negro/Pardo)'
    }
    return labels.get(group, group)


# ============================================
# TABLE 2: MAIN DID RESULTS
# ============================================

def create_table2_main_did(results_df, save_path):
    """
    Creates Table 2: Main DiD Results.

    Displays 4 model specifications × 2 outcomes in a clean panel format.

    Parameters:
    -----------
    results_df : DataFrame
        Main DiD results from script 09
    save_path : Path
        Where to save the .tex file

    Returns:
    --------
    str: LaTeX table code
    """
    logger.info("\nCreating Table 2: Main DiD Results...")

    # Filter to valid outcomes
    outcomes_to_use = [o for o in OUTCOMES_VALID if o in ['ln_renda', 'horas_trabalhadas']]
    df = results_df[results_df['outcome'].isin(outcomes_to_use)].copy()

    # Start LaTeX table
    latex = "\\begin{table}[htbp]\n"
    latex += "\\centering\n"
    latex += "\\caption{Efeitos DiD sobre Mercado de Trabalho: Resultados Principais}\n"
    latex += "\\label{tab:main_did_results}\n"
    latex += "\\begin{threeparttable}\n"
    latex += "\\begin{tabular}{l" + "c" * 4 + "}\n"
    latex += "\\toprule\n"

    # Create panels for each outcome
    for outcome in outcomes_to_use:
        df_outcome = df[df['outcome'] == outcome].copy()

        # Panel header
        outcome_label = get_outcome_label(outcome)
        latex += f"\\multicolumn{{5}}{{l}}{{\\textbf{{Painel {outcomes_to_use.index(outcome) + 1}: {outcome_label}}}}} \\\\\n"
        latex += "\\midrule\n"

        # Column headers
        latex += " & \\multicolumn{1}{c}{(1)} & \\multicolumn{1}{c}{(2)} & \\multicolumn{1}{c}{(3)} & \\multicolumn{1}{c}{(4)} \\\\\n"
        latex += " & Basic & FE & FE + Controls & Continuous \\\\\n"
        latex += "\\midrule\n"

        # DiD coefficient row
        latex += "Post $\\times$ Alta Exposição"

        for model_num, model_name in enumerate(['Model 1: Basic', 'Model 2: FE', 'Model 3: FE + Controls (MAIN)'], start=1):
            row = df_outcome[df_outcome['model'] == model_name]
            if not row.empty:
                coef = row['coef'].values[0]
                se = row['se'].values[0]
                stars = row['stars'].values[0]
                latex += f" & {format_coef_se(coef, se, stars, 4)}"
            else:
                latex += " & —"

        # Model 4 (Continuous)
        row = df_outcome[df_outcome['model'] == 'Model 4: Continuous']
        if not row.empty:
            latex += " & —"  # No coefficient for continuous in this row

        latex += " \\\\\n"

        # Continuous exposure row (only for Model 4)
        latex += "Post $\\times$ Exposição (contínua)"
        latex += " & — & — & —"

        row = df_outcome[df_outcome['model'] == 'Model 4: Continuous']
        if not row.empty:
            coef = row['coef'].values[0]
            se = row['se'].values[0]
            stars = row['stars'].values[0]
            latex += f" & {format_coef_se(coef, se, stars, 4)}"
        else:
            latex += " & —"

        latex += " \\\\\n"
        latex += "\\midrule\n"

        # Model specifications
        latex += "Controles individuais & Não & Não & Sim & Sim \\\\\n"
        latex += "EF Ocupação & Não & Sim & Sim & Sim \\\\\n"
        latex += "EF Período & Não & Sim & Sim & Sim \\\\\n"
        latex += "\\midrule\n"

        # Observations and R²
        for idx, model_name in enumerate(['Model 1: Basic', 'Model 2: FE', 'Model 3: FE + Controls (MAIN)', 'Model 4: Continuous']):
            row = df_outcome[df_outcome['model'] == model_name]
            if not row.empty and idx == 0:
                n_obs = int(row['n_obs'].values[0])
                latex += f"Observações & \\multicolumn{{4}}{{c}}{{{n_obs:,}}} \\\\\n"
                break

        # R² row
        latex += "$R^2$"
        for model_name in ['Model 1: Basic', 'Model 2: FE', 'Model 3: FE + Controls (MAIN)', 'Model 4: Continuous']:
            row = df_outcome[df_outcome['model'] == model_name]
            if not row.empty:
                r2 = row['r_squared'].values[0]
                if pd.notna(r2):
                    latex += f" & {r2:.4f}"
                else:
                    latex += " & —"
            else:
                latex += " & —"
        latex += " \\\\\n"

        # N clusters
        row = df_outcome[df_outcome['model'] == 'Model 2: FE']
        if not row.empty and pd.notna(row['n_clusters'].values[0]):
            n_clusters = int(row['n_clusters'].values[0])
            latex += f"N clusters (ocupações) & — & \\multicolumn{{3}}{{c}}{{{n_clusters}}} \\\\\n"

        # Add spacing between panels (except after last)
        if outcome != outcomes_to_use[-1]:
            latex += "\\midrule\n"
            latex += "[0.5em]\n"

    # Bottom rule
    latex += "\\bottomrule\n"
    latex += "\\end{tabular}\n"

    # Notes
    notes = [
        "Erros padrão clusterizados por ocupação em parênteses.",
        "* $p<0.10$, ** $p<0.05$, *** $p<0.01$.",
        "Alta exposição = ocupações no percentil 80+ do índice ILO de exposição à IA Generativa.",
        "Controles individuais: idade, idade$^2$, gênero, raça, educação.",
        "Modelo (3) é a especificação principal. Modelo (4) usa exposição contínua."
    ]

    latex += add_table_notes(notes)
    latex += "\\end{threeparttable}\n"
    latex += "\\end{table}\n"

    # Save to file
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(latex)

    logger.info(f"✓ Table 2 saved: {save_path.name}")

    return latex


# ============================================
# TABLE 1: DESCRIPTIVE STATISTICS
# ============================================

def create_table1_descriptives(balance_df, save_path):
    """
    Creates Table 1: Descriptive Statistics (Balance Table).

    Parameters:
    -----------
    balance_df : DataFrame
        Balance table from script 06 (Fase 3)
    save_path : Path
        Where to save the .tex file

    Returns:
    --------
    str: LaTeX table code
    """
    logger.info("\nCreating Table 1: Descriptive Statistics...")

    # Start LaTeX table
    latex = "\\begin{table}[htbp]\n"
    latex += "\\centering\n"
    latex += "\\caption{Estatísticas Descritivas por Grupo de Exposição (Período Pré-Tratamento)}\n"
    latex += "\\label{tab:descriptives}\n"
    latex += "\\begin{threeparttable}\n"
    latex += "\\begin{tabular}{l" + "c" * 3 + "}\n"
    latex += "\\toprule\n"

    # Headers
    latex += " & Baixa Exposição & Alta Exposição & Diferença \\\\\n"
    latex += "\\midrule\n"

    # Read CSV if it exists
    if balance_df is not None and not balance_df.empty:
        # Assuming balance_df has columns: Variable, Control, Treatment, Difference
        for _, row in balance_df.iterrows():
            var_name = escape_latex(str(row.get('Variable', row.get('variable', ''))))
            control = row.get('Control', row.get('control', '—'))
            treatment = row.get('Treatment', row.get('treatment', '—'))
            diff = row.get('Difference', row.get('difference', '—'))

            latex += f"{var_name} & {control} & {treatment} & {diff} \\\\\n"
    else:
        # Placeholder if balance table doesn't exist
        latex += "Idade (anos) & — & — & — \\\\\n"
        latex += "Mulher (\\%) & — & — & — \\\\\n"
        latex += "Negro/Pardo (\\%) & — & — & — \\\\\n"
        latex += "Superior completo (\\%) & — & — & — \\\\\n"
        latex += "Rendimento médio (R\\$) & — & — & — \\\\\n"
        latex += "Horas trabalhadas & — & — & — \\\\\n"

    latex += "\\bottomrule\n"
    latex += "\\end{tabular}\n"

    # Notes
    notes = [
        "Estatísticas calculadas para o período pré-tratamento (2021T1-2022T4).",
        "Baixa exposição = ocupações abaixo do percentil 80.",
        "Alta exposição = ocupações no percentil 80+ do índice ILO.",
        "Diferença = Alta Exposição - Baixa Exposição."
    ]

    latex += add_table_notes(notes)
    latex += "\\end{threeparttable}\n"
    latex += "\\end{table}\n"

    # Save to file
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(latex)

    logger.info(f"✓ Table 1 saved: {save_path.name}")

    return latex


# ============================================
# TABLE 3: HETEROGENEITY
# ============================================

def create_table3_heterogeneity(het_df, save_path):
    """
    Creates Table 3: Heterogeneity Analysis (Triple-DiD).

    Parameters:
    -----------
    het_df : DataFrame
        Heterogeneity summary from script 11
    save_path : Path
        Where to save the .tex file

    Returns:
    --------
    str: LaTeX table code
    """
    logger.info("\nCreating Table 3: Heterogeneity Analysis...")

    # Filter to valid outcomes
    outcomes_to_use = [o for o in OUTCOMES_VALID if o in ['ln_renda', 'horas_trabalhadas']]
    df = het_df[het_df['outcome'].isin(outcomes_to_use)].copy()

    # Start LaTeX table
    latex = "\\begin{table}[htbp]\n"
    latex += "\\centering\n"
    latex += "\\caption{Heterogeneidade dos Efeitos DiD por Grupos Demográficos}\n"
    latex += "\\label{tab:heterogeneity}\n"
    latex += "\\begin{threeparttable}\n"
    latex += "\\begin{tabular}{l" + "c" * 3 + "}\n"
    latex += "\\toprule\n"

    # Create panels for each outcome
    for outcome in outcomes_to_use:
        df_outcome = df[df['outcome'] == outcome].copy()

        # Panel header
        outcome_label = get_outcome_label(outcome)
        latex += f"\\multicolumn{{4}}{{l}}{{\\textbf{{Painel {outcomes_to_use.index(outcome) + 1}: {outcome_label}}}}} \\\\\n"
        latex += "\\midrule\n"

        # Column headers
        latex += "Grupo & Efeito Principal & Interação & Efeito Total \\\\\n"
        latex += "\\midrule\n"

        # Rows for each demographic group
        for _, row in df_outcome.iterrows():
            group = row['group']
            group_label = get_group_label(group)

            # Get coefficient and SE values (SE might be already formatted as string)
            main_coef = row['main_effect']
            main_se = str(row['main_se']).strip('()')  # Remove parentheses if present
            interaction_coef = row['interaction']
            interaction_se = str(row['interaction_se']).strip('()')
            total_coef = row['total_effect']
            total_se = str(row['total_se']).strip('()')

            # Check if values are numeric or already have stars
            def parse_value_with_stars(val_str):
                """Extract numeric value and stars from a string like '-0.7473***'"""
                val_str = str(val_str).strip()
                stars = ''
                # Extract stars from end
                while val_str and val_str[-1] == '*':
                    stars = val_str[-1] + stars
                    val_str = val_str[:-1]
                try:
                    val = float(val_str)
                except:
                    val = np.nan
                return val, stars

            # Parse main effect
            main_val, main_stars = parse_value_with_stars(main_coef)
            try:
                main_se_float = float(main_se)
            except:
                main_se_float = np.nan
            main_str = format_coef_se(main_val, main_se_float, main_stars, 4)

            # Parse interaction
            interaction_val, interaction_stars = parse_value_with_stars(interaction_coef)
            try:
                interaction_se_float = float(interaction_se)
            except:
                interaction_se_float = np.nan
            interaction_str = format_coef_se(interaction_val, interaction_se_float, interaction_stars, 4)

            # Parse total effect
            total_val, total_stars = parse_value_with_stars(total_coef)
            try:
                total_se_float = float(total_se)
            except:
                total_se_float = np.nan
            total_str = format_coef_se(total_val, total_se_float, total_stars, 4)

            latex += f"{group_label} & {main_str} & {interaction_str} & {total_str} \\\\\n"

        # Add spacing between panels (except after last)
        if outcome != outcomes_to_use[-1]:
            latex += "\\midrule\n"
            latex += "[0.5em]\n"

    # Bottom rule
    latex += "\\bottomrule\n"
    latex += "\\end{tabular}\n"

    # Notes
    notes = [
        "Erros padrão clusterizados por ocupação em parênteses.",
        "* $p<0.10$, ** $p<0.05$, *** $p<0.01$.",
        "Estimação via Triple-DiD: Post $\\times$ AltaExp $\\times$ Grupo.",
        "Efeito Principal = Post $\\times$ AltaExp (para grupo de referência).",
        "Interação = Efeito adicional para o grupo específico.",
        "Efeito Total = Principal + Interação (calculado via delta method)."
    ]

    latex += add_table_notes(notes)
    latex += "\\end{threeparttable}\n"
    latex += "\\end{table}\n"

    # Save to file
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(latex)

    logger.info(f"✓ Table 3 saved: {save_path.name}")

    return latex


# ============================================
# TABLE 4: ROBUSTNESS
# ============================================

def create_table4_robustness(rob_df, save_path):
    """
    Creates Table 4: Robustness Checks Summary.

    Parameters:
    -----------
    rob_df : DataFrame
        Robustness summary from script 12
    save_path : Path
        Where to save the .tex file

    Returns:
    --------
    str: LaTeX table code
    """
    logger.info("\nCreating Table 4: Robustness Checks...")

    # Filter to valid outcomes
    outcomes_to_use = [o for o in OUTCOMES_VALID if o in ['ln_renda', 'horas_trabalhadas']]
    df = rob_df[rob_df['outcome'].isin(outcomes_to_use)].copy()

    # Start LaTeX table
    latex = "\\begin{table}[htbp]\n"
    latex += "\\centering\n"
    latex += "\\caption{Testes de Robustez}\n"
    latex += "\\label{tab:robustness}\n"
    latex += "\\begin{threeparttable}\n"
    latex += "\\begin{tabular}{l" + "c" * 2 + "}\n"
    latex += "\\toprule\n"

    # Headers
    latex += "Especificação & Log(Rendimento) & Horas Trabalhadas \\\\\n"
    latex += "\\midrule\n"

    # Get unique specifications
    specs = df['specification'].unique()

    # Group specifications by test type
    spec_order = [
        'Top 10%',
        'Top 20% (MAIN)',
        'Top 25%',
        'Continuous',
        'Placebo (2021T4)',
        'Exclude IT',
        'Diff. Pre-Trends'
    ]

    # Test type sections
    test_sections = {
        'Alternative Cutoff': ['Top 10%', 'Top 20% (MAIN)', 'Top 25%', 'Continuous'],
        'Placebo': ['Placebo (2021T4)'],
        'Exclude IT': ['Exclude IT'],
        'Differential Trends': ['Diff. Pre-Trends']
    }

    for test_name, test_specs in test_sections.items():
        # Section header
        latex += f"\\multicolumn{{3}}{{l}}{{\\textit{{{test_name}}}}} \\\\\n"

        # Rows for this test
        for spec in test_specs:
            if spec not in specs:
                continue

            spec_label = spec.replace('(MAIN)', '\\textbf{(MAIN)}')
            latex += f"{spec_label}"

            # Columns for each outcome
            for outcome in outcomes_to_use:
                row = df[(df['outcome'] == outcome) & (df['specification'] == spec)]

                if not row.empty:
                    coef = row['coef'].values[0]
                    se = row['se'].values[0]
                    stars_val = row['stars'].values[0]

                    # Handle NaN stars
                    if pd.isna(stars_val):
                        stars_val = ''

                    formatted = format_coef_se(coef, se, stars_val, 4)
                    latex += f" & {formatted}"
                else:
                    latex += " & —"

            latex += " \\\\\n"

        latex += "\\midrule\n"

    # Remove last midrule
    latex = latex.rstrip("\\midrule\n")

    # Bottom rule
    latex += "\\bottomrule\n"
    latex += "\\end{tabular}\n"

    # Notes
    notes = [
        "Erros padrão clusterizados por ocupação em parênteses.",
        "* $p<0.10$, ** $p<0.05$, *** $p<0.01$.",
        "\\textbf{(MAIN)} indica a especificação principal (Top 20\\%).",
        "Placebo: teste com tratamento fictício em 2021T4 (pré-período).",
        "Exclude IT: exclui ocupações de Tecnologia da Informação (ISCO 25xx).",
        "Diff. Pre-Trends: teste de tendências diferenciais no pré-período."
    ]

    latex += add_table_notes(notes)
    latex += "\\end{threeparttable}\n"
    latex += "\\end{table}\n"

    # Save to file
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(latex)

    logger.info(f"✓ Table 4 saved: {save_path.name}")

    return latex


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """
    Main execution function.
    """
    logger.info("="*70)
    logger.info("SCRIPT 13: FORMAT TABLES FOR LATEX")
    logger.info("="*70)
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ============================================
    # LOAD DATA
    # ============================================

    logger.info("\nLoading results from previous scripts...")

    try:
        # Main DiD results (Script 09)
        main_results_path = OUTPUTS_TABLES / 'did_main_results.csv'
        main_results = pd.read_csv(main_results_path)
        logger.info(f"✓ Loaded: {main_results_path.name} ({len(main_results)} rows)")

        # Heterogeneity results (Script 11)
        het_summary_path = OUTPUTS_TABLES / 'heterogeneity_summary.csv'
        het_summary = pd.read_csv(het_summary_path)
        logger.info(f"✓ Loaded: {het_summary_path.name} ({len(het_summary)} rows)")

        # Robustness results (Script 12)
        rob_summary_path = OUTPUTS_TABLES / 'robustness_summary.csv'
        rob_summary = pd.read_csv(rob_summary_path)
        logger.info(f"✓ Loaded: {rob_summary_path.name} ({len(rob_summary)} rows)")

    except Exception as e:
        logger.error(f"✗ Failed to load input files: {e}")
        logger.error("  Make sure scripts 09-12 have been run successfully.")
        return

    # Try to load balance table (from Fase 3)
    try:
        balance_path = OUTPUTS_TABLES / 'balance_table_pre.csv'
        balance_df = pd.read_csv(balance_path)
        logger.info(f"✓ Loaded: {balance_path.name} ({len(balance_df)} rows)")
    except Exception as e:
        logger.warning(f"⚠️  Could not load balance table: {e}")
        logger.warning("  Table 1 will be generated with placeholders.")
        balance_df = None

    # ============================================
    # CREATE TABLES
    # ============================================

    logger.info("\n" + "="*70)
    logger.info("GENERATING LATEX TABLES")
    logger.info("="*70)

    tables_created = []

    # Table 1: Descriptive Statistics
    table1_path = OUTPUTS_TABLES / 'table1_descriptives.tex'
    try:
        create_table1_descriptives(balance_df, table1_path)
        tables_created.append(('Table 1', table1_path.name))
    except Exception as e:
        logger.error(f"✗ Failed to create Table 1: {e}")

    # Table 2: Main DiD Results
    table2_path = OUTPUTS_TABLES / 'table2_main_did_results.tex'
    try:
        create_table2_main_did(main_results, table2_path)
        tables_created.append(('Table 2', table2_path.name))
    except Exception as e:
        logger.error(f"✗ Failed to create Table 2: {e}")

    # Table 3: Heterogeneity
    table3_path = OUTPUTS_TABLES / 'table3_heterogeneity.tex'
    try:
        create_table3_heterogeneity(het_summary, table3_path)
        tables_created.append(('Table 3', table3_path.name))
    except Exception as e:
        logger.error(f"✗ Failed to create Table 3: {e}")

    # Table 4: Robustness
    table4_path = OUTPUTS_TABLES / 'table4_robustness.tex'
    try:
        create_table4_robustness(rob_summary, table4_path)
        tables_created.append(('Table 4', table4_path.name))
    except Exception as e:
        logger.error(f"✗ Failed to create Table 4: {e}")

    # ============================================
    # CREATE APPENDIX (ALL TABLES COMBINED)
    # ============================================

    logger.info("\nCreating appendix file with all tables...")

    appendix_path = OUTPUTS_TABLES / 'appendix_all_tables.tex'

    try:
        with open(appendix_path, 'w', encoding='utf-8') as f:
            f.write("% ======================================================================\n")
            f.write("% APPENDIX: ALL LATEX TABLES FOR DISSERTATION\n")
            f.write("% Generated by Script 13: Format Tables\n")
            f.write(f"% Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("% ======================================================================\n\n")

            # Add each table
            for table_name, table_file in [
                ('Table 1', 'table1_descriptives.tex'),
                ('Table 2', 'table2_main_did_results.tex'),
                ('Table 3', 'table3_heterogeneity.tex'),
                ('Table 4', 'table4_robustness.tex')
            ]:
                table_path = OUTPUTS_TABLES / table_file
                if table_path.exists():
                    f.write(f"\n% {table_name}: {table_file}\n")
                    f.write(f"% {'='*70}\n\n")
                    with open(table_path, 'r', encoding='utf-8') as tf:
                        f.write(tf.read())
                    f.write("\n\\clearpage\n\n")

        logger.info(f"✓ Appendix saved: {appendix_path.name}")
        tables_created.append(('Appendix', appendix_path.name))

    except Exception as e:
        logger.error(f"✗ Failed to create appendix: {e}")

    # ============================================
    # SUMMARY
    # ============================================

    logger.info("\n" + "="*70)
    logger.info("LATEX TABLE GENERATION COMPLETE")
    logger.info("="*70)

    logger.info(f"\nTables generated ({len(tables_created)}):")
    for table_name, table_file in tables_created:
        logger.info(f"  ✓ {table_name}: {table_file}")

    logger.info(f"\n📁 All tables saved to: {OUTPUTS_TABLES}")
    logger.info(f"📄 Log saved to: {log_file}")

    logger.info(f"\n✓ Script completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
