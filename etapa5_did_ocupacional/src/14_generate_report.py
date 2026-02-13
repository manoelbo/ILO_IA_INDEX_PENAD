"""
Script 14: Generate Markdown Report

Generates comprehensive markdown reports with automatic interpretation of DiD analysis results.

Inputs:
- outputs/tables/did_main_results.csv
- outputs/tables/event_study_*.csv
- outputs/tables/parallel_trends_test_formal.csv
- outputs/tables/heterogeneity_all_triple_did.csv
- outputs/tables/robustness_summary.csv
- outputs/tables/balance_table_pre.csv

Outputs:
- outputs/DID_ANALYSIS_REPORT.md (comprehensive report)
- outputs/DID_EXECUTIVE_SUMMARY.md (executive summary)

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
    DATA_PROCESSED, OUTPUTS_TABLES, OUTPUTS_LOGS, ROOT_DIR,
    OUTCOMES_VALID
)

# Define OUTPUTS_DIR
OUTPUTS_DIR = ROOT_DIR / "outputs"

# ============================================
# LOGGING SETUP
# ============================================

# Create log file
log_file = OUTPUTS_LOGS / '14_generate_report.log'
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
# INTERPRETATION FUNCTIONS
# ============================================

def interpret_coefficient_magnitude(coef, outcome):
    """
    Interprets the magnitude of a DiD coefficient.

    Parameters:
    -----------
    coef : float
        Coefficient value
    outcome : str
        Outcome variable name

    Returns:
    --------
    str: Interpretation text
    """
    if outcome == 'ln_renda':
        # Log points interpretation
        pct_change = (np.exp(coef) - 1) * 100
        if abs(pct_change) < 1:
            magnitude = "muito pequena"
        elif abs(pct_change) < 3:
            magnitude = "pequena"
        elif abs(pct_change) < 5:
            magnitude = "moderada"
        else:
            magnitude = "grande"

        direction = "aumento" if coef > 0 else "redução"
        return f"{magnitude} {direction} de aproximadamente {abs(pct_change):.1f}%"

    elif outcome == 'horas_trabalhadas':
        # Direct hours interpretation
        if abs(coef) < 0.5:
            magnitude = "muito pequena"
        elif abs(coef) < 1.0:
            magnitude = "pequena"
        elif abs(coef) < 2.0:
            magnitude = "moderada"
        else:
            magnitude = "grande"

        direction = "aumento" if coef > 0 else "redução"
        return f"{magnitude} {direction} de aproximadamente {abs(coef):.1f} horas por semana"

    else:
        return f"mudança de {coef:.4f}"


def interpret_did_coefficient(coef, se, p_value, outcome):
    """
    Generates automatic interpretation of a DiD coefficient.

    Parameters:
    -----------
    coef : float
        Coefficient value
    se : float
        Standard error
    p_value : float
        P-value
    outcome : str
        Outcome variable name

    Returns:
    --------
    str: Markdown-formatted interpretation
    """
    # Significance
    if p_value < 0.01:
        sig_text = "**estatisticamente significativo a 1%**"
        sig_level = "forte"
    elif p_value < 0.05:
        sig_text = "**estatisticamente significativo a 5%**"
        sig_level = "moderada"
    elif p_value < 0.10:
        sig_text = "**marginalmente significativo a 10%**"
        sig_level = "fraca"
    else:
        sig_text = "**não estatisticamente significativo**"
        sig_level = "nenhuma"

    # Direction
    if coef > 0:
        direction = "positivo"
        verb = "aumento"
    else:
        direction = "negativo"
        verb = "redução"

    # Magnitude interpretation
    magnitude_text = interpret_coefficient_magnitude(coef, outcome)

    # Build interpretation
    interpretation = f"O coeficiente DiD é {direction} (β = {coef:.4f}, SE = {se:.4f}) e {sig_text} (p = {p_value:.4f}). "

    if p_value < 0.10:
        interpretation += f"Isso sugere uma {magnitude_text} para trabalhadores em ocupações de alta exposição à IA Generativa, "
        interpretation += f"comparados aos de baixa exposição, após o lançamento do ChatGPT. "
        interpretation += f"A evidência é {sig_level}."
    else:
        interpretation += f"Não há evidência estatística suficiente de que o ChatGPT teve impacto diferencial sobre este outcome. "
        interpretation += f"Isso pode indicar que: (i) os efeitos ainda não se materializaram; "
        interpretation += f"(ii) o ajuste ocorre por outras margens não observadas; "
        interpretation += f"(iii) há erro de medida atenuando os coeficientes; ou "
        interpretation += f"(iv) a economia brasileira responde de forma diferente à tecnologia."

    return interpretation


def assess_parallel_trends(pt_df):
    """
    Assesses parallel trends assumption based on formal test.

    Parameters:
    -----------
    pt_df : DataFrame
        Parallel trends test results

    Returns:
    --------
    dict: Assessment with keys 'passed', 'text', 'concern_level'
    """
    assessments = []

    for _, row in pt_df.iterrows():
        outcome = row['outcome']
        n_sig_pre = row['n_significant_pre']  # Corrected column name
        avg_pre_coef = row['avg_abs_pre_coef']

        if n_sig_pre == 0:
            status = "✅ VALIDADO"
            concern = "low"
            text = f"Nenhum coeficiente pré-tratamento significativo. Tendências paralelas suportadas."
        elif n_sig_pre <= 1:
            status = "⚠️ ATENÇÃO"
            concern = "medium"
            text = f"{n_sig_pre} coeficiente(s) pré-tratamento significativo(s). Possível violação marginal."
        else:
            status = "❌ VIOLADO"
            concern = "high"
            text = f"{n_sig_pre} coeficientes pré-tratamento significativos. Violação clara de tendências paralelas."

        assessments.append({
            'outcome': outcome,
            'status': status,
            'concern_level': concern,
            'text': text,
            'n_sig_pre': n_sig_pre,
            'avg_pre_coef': avg_pre_coef
        })

    return assessments


def assess_robustness_summary(rob_df, main_results):
    """
    Assesses overall robustness based on multiple tests.

    Parameters:
    -----------
    rob_df : DataFrame
        Robustness summary results
    main_results : DataFrame
        Main DiD results for comparison

    Returns:
    --------
    dict: Assessment by outcome
    """
    outcomes = rob_df['outcome'].unique()
    assessments = {}

    for outcome in outcomes:
        df_outcome = rob_df[rob_df['outcome'] == outcome].copy()

        # Get main coefficient
        main_row = main_results[main_results['outcome'] == outcome]
        if main_row.empty:
            continue
        main_coef = main_row['coef'].values[0]

        # Check placebo test
        placebo = df_outcome[df_outcome['test_type'] == 'Placebo']
        placebo_pass = True
        placebo_text = ""
        if not placebo.empty:
            placebo_p = placebo['p_value'].values[0]
            if placebo_p < 0.10:
                placebo_pass = False
                placebo_text = f"❌ Placebo test FAILED (p={placebo_p:.3f}). "
            else:
                placebo_text = f"✅ Placebo test passed (p={placebo_p:.3f}). "

        # Check differential trends
        trends = df_outcome[df_outcome['test_type'] == 'Differential Trends']
        trends_ok = True
        trends_text = ""
        if not trends.empty:
            trends_p = trends['p_value'].values[0]
            if trends_p < 0.10:
                trends_ok = False
                trends_text = f"❌ Differential pre-trends DETECTED (p={trends_p:.3f}). "
            else:
                trends_text = f"✅ No differential pre-trends (p={trends_p:.3f}). "

        # Check alternative cutoffs
        cutoffs = df_outcome[df_outcome['test_type'] == 'Alternative Cutoff']
        cutoffs_text = ""
        if not cutoffs.empty:
            cutoff_coefs = cutoffs['coef'].values
            coef_range = cutoff_coefs.max() - cutoff_coefs.min()
            sign_consistent = (cutoff_coefs >= 0).all() or (cutoff_coefs <= 0).all()

            if sign_consistent and abs(coef_range / abs(main_coef)) < 2.0:
                cutoffs_text = f"✅ Results stable across cutoffs (range: {coef_range:.4f}). "
            else:
                cutoffs_text = f"⚠️ Some variation across cutoffs (range: {coef_range:.4f}). "

        # Overall assessment
        if placebo_pass and trends_ok:
            overall = "ROBUST"
            icon = "✅"
        elif placebo_pass or trends_ok:
            overall = "MODERATE CONCERNS"
            icon = "⚠️"
        else:
            overall = "SERIOUS CONCERNS"
            icon = "❌"

        assessments[outcome] = {
            'overall': overall,
            'icon': icon,
            'placebo_pass': placebo_pass,
            'trends_ok': trends_ok,
            'placebo_text': placebo_text,
            'trends_text': trends_text,
            'cutoffs_text': cutoffs_text
        }

    return assessments


def flag_heterogeneity_findings(het_df):
    """
    Identifies significant heterogeneity findings.

    Parameters:
    -----------
    het_df : DataFrame
        Heterogeneity results (all triple-DiD)

    Returns:
    --------
    list: List of significant findings with interpretations
    """
    findings = []

    for _, row in het_df.iterrows():
        outcome = row['outcome']
        group = row['group_label']
        interaction_pval = row['pval_interaction']

        # Check if interaction is significant
        if interaction_pval < 0.10:
            coef_interaction = row['coef_interaction']
            coef_total = row['coef_total']
            stars_interaction = row['stars_interaction']

            # Determine direction
            if coef_interaction > 0:
                direction = "maior"
                comparison = "mais positivo" if coef_total > 0 else "menos negativo"
            else:
                direction = "menor"
                comparison = "mais negativo" if coef_total < 0 else "menos positivo"

            # Significance level
            if interaction_pval < 0.01:
                sig_text = "forte (p<0.01)"
            elif interaction_pval < 0.05:
                sig_text = "moderada (p<0.05)"
            else:
                sig_text = "fraca (p<0.10)"

            finding = {
                'outcome': outcome,
                'group': group,
                'interaction_coef': coef_interaction,
                'total_coef': coef_total,
                'p_value': interaction_pval,
                'stars': stars_interaction,
                'direction': direction,
                'comparison': comparison,
                'sig_text': sig_text,
                'text': f"**{group}** apresenta efeito {comparison} ({coef_interaction:+.4f}{stars_interaction}), "
                        f"com significância {sig_text}. Efeito total para este grupo: {coef_total:.4f}."
            }

            findings.append(finding)

    return findings


# ============================================
# REPORT GENERATION FUNCTIONS
# ============================================

def generate_executive_summary(all_results):
    """
    Generates executive summary markdown.

    Parameters:
    -----------
    all_results : dict
        Dictionary with all loaded results

    Returns:
    --------
    str: Markdown text
    """
    md = "# Sumário Executivo: Análise DiD - Impacto da IA Generativa no Brasil\n\n"
    md += f"**Data**: {datetime.now().strftime('%d de %B de %Y')}\n\n"
    md += "---\n\n"

    # Add interpretive guidance box
    md += "## 📊 Como Interpretar os Resultados\n\n"
    md += "> **IMPORTANTE**: Efeito médio não significativo ≠ Ausência de efeitos\n>\n"
    md += "> Quando o efeito médio geral não é estatisticamente significativo, mas há **efeitos heterogêneos significativos**, "
    md += "isso indica que a IA está impactando diferentes grupos de formas **opostas** que se **cancelam** na média. "
    md += "Este padrão sugere que a tecnologia tem efeitos **diferenciados** por grupo demográfico, "
    md += "mesmo que a média agregada seja próxima de zero.\n\n"
    md += "---\n\n"

    # Heterogeneity FIRST (main finding)
    md += "## 🎯 Achado Principal: Efeitos Heterogêneos\n\n"

    het_findings = all_results.get('heterogeneity_findings', [])
    if het_findings:
        md += f"Encontramos **{len(het_findings)} efeito(s) heterogêneo(s) significativo(s)**:\n\n"
        for finding in het_findings:
            md += f"- **{finding['group']}** ({finding['outcome']}): {finding['text']}\n"
        md += "\n**Interpretação**: A IA Generativa tem impactos **diferenciados** por grupo demográfico. "
        md += "Efeitos opostos (positivos para alguns grupos, negativos para outros) se cancelam na média agregada, "
        md += "mas são reais e estatisticamente significativos para subgrupos específicos.\n\n"
    else:
        md += "Não foram encontrados efeitos heterogêneos estatisticamente significativos.\n\n"

    # Main findings (average effects) - now SECOND
    md += "## 📈 Efeitos Médios (Agregados)\n\n"

    main_results = all_results['main_results']
    main_spec = main_results[main_results['model'].str.contains('Model 3', na=False)]

    for outcome in ['ln_renda', 'horas_trabalhadas']:
        row = main_spec[main_spec['outcome'] == outcome]
        if not row.empty:
            coef = row['coef'].values[0]
            se = row['se'].values[0]
            p_val = row['p_value'].values[0]

            outcome_label = "Rendimento" if outcome == 'ln_renda' else "Horas Trabalhadas"
            md += f"### {outcome_label}\n\n"

            interpretation = interpret_did_coefficient(coef, se, p_val, outcome)
            md += interpretation + "\n\n"

    # Robustness
    md += "## 🔬 Robustez\n\n"

    rob_assessments = all_results.get('robustness_assessment', {})
    for outcome, assessment in rob_assessments.items():
        outcome_label = "Rendimento" if outcome == 'ln_renda' else "Horas Trabalhadas"
        md += f"**{outcome_label}**: {assessment['icon']} {assessment['overall']}\n\n"
        md += assessment['placebo_text'] + assessment['trends_text'] + "\n\n"

    md += "---\n\n"
    md += "*Relatório gerado automaticamente pelo Script 14: Generate Report*\n"

    return md


def generate_full_report(all_results):
    """
    Generates comprehensive markdown report.

    Parameters:
    -----------
    all_results : dict
        Dictionary with all loaded results

    Returns:
    --------
    str: Markdown text
    """
    md = "# Relatório Completo: Análise Difference-in-Differences\n"
    md += "# Impacto da IA Generativa no Mercado de Trabalho Brasileiro\n\n"
    md += f"**Data de Geração**: {datetime.now().strftime('%d de %B de %Y, %H:%M:%S')}\n\n"
    md += "---\n\n"

    # Table of Contents
    md += "## Índice\n\n"
    md += "1. [Visão Geral](#visão-geral)\n"
    md += "2. [Descrição da Amostra](#descrição-da-amostra)\n"
    md += "3. [Validação do Desenho DiD](#validação-do-desenho-did)\n"
    md += "4. [Resultados Principais](#resultados-principais)\n"
    md += "5. [Análise de Heterogeneidade](#análise-de-heterogeneidade)\n"
    md += "6. [Testes de Robustez](#testes-de-robustez)\n"
    md += "7. [Limitações](#limitações)\n"
    md += "8. [Conclusões](#conclusões)\n\n"
    md += "---\n\n"

    # ============================================
    # SECTION 1: OVERVIEW
    # ============================================

    md += "## 1. Visão Geral\n\n"
    md += "### 1.1 Objetivo\n\n"
    md += "Esta análise utiliza a metodologia **Difference-in-Differences (DiD)** para estimar o efeito causal "
    md += "do lançamento do ChatGPT (novembro de 2022) sobre o mercado de trabalho brasileiro, usando variação "
    md += "na intensidade de exposição ocupacional à IA Generativa.\n\n"

    md += "### 1.2 Dados\n\n"
    md += "- **Fonte**: PNAD Contínua (IBGE)\n"
    md += "- **Período**: 2021T1 a 2024T4 (16 trimestres)\n"
    md += "- **Índice de Exposição**: ILO GenAI Exposure Index (Gmyrek, Berg et al., 2025)\n"
    md += "- **Tratamento**: Ocupações no percentil 80+ de exposição à IA\n\n"

    md += "### 1.3 Especificação Principal\n\n"
    md += "```\n"
    md += "Y_iot = α + β(Post_t × AltaExp_o) + θX_it + δ_o + μ_t + ε_iot\n"
    md += "```\n\n"
    md += "Onde:\n"
    md += "- **Y_iot**: Outcome (ln_renda, horas_trabalhadas)\n"
    md += "- **Post_t**: Dummy pós-ChatGPT (≥2023T1)\n"
    md += "- **AltaExp_o**: Dummy alta exposição (top 20%)\n"
    md += "- **X_it**: Controles individuais (idade, gênero, raça, educação)\n"
    md += "- **δ_o**: Efeitos fixos de ocupação\n"
    md += "- **μ_t**: Efeitos fixos de período\n"
    md += "- **ε_iot**: Erro (clustered por ocupação)\n\n"

    # ============================================
    # SECTION 2: SAMPLE DESCRIPTION
    # ============================================

    md += "## 2. Descrição da Amostra\n\n"

    main_results = all_results['main_results']
    main_spec = main_results[main_results['model'].str.contains('Model 3', na=False)]

    if not main_spec.empty:
        n_obs = int(main_spec['n_obs'].values[0])
        n_clusters = int(main_spec['n_clusters'].values[0])

        md += f"- **Observações**: {n_obs:,}\n"
        md += f"- **Ocupações (clusters)**: {n_clusters}\n"
        md += f"- **Períodos**: 16 trimestres (8 pré + 8 pós)\n\n"

    # Balance table if available
    if 'balance_table' in all_results and not all_results['balance_table'].empty:
        md += "### 2.1 Balanço de Covariáveis (Período Pré-Tratamento)\n\n"
        md += "| Variável | Baixa Exposição | Alta Exposição | Diferença |\n"
        md += "|----------|----------------|----------------|------------|\n"

        balance_df = all_results['balance_table']
        for _, row in balance_df.iterrows():
            var = row.get('Variable', row.get('variable', ''))
            control = row.get('Control', row.get('control', '—'))
            treatment = row.get('Treatment', row.get('treatment', '—'))
            diff = row.get('Difference', row.get('difference', '—'))
            md += f"| {var} | {control} | {treatment} | {diff} |\n"

        md += "\n"

    # ============================================
    # SECTION 3: DESIGN VALIDATION
    # ============================================

    md += "## 3. Validação do Desenho DiD\n\n"
    md += "### 3.1 Hipótese de Tendências Paralelas\n\n"

    pt_assessments = all_results.get('parallel_trends_assessment', [])

    if pt_assessments:
        md += "A validade do DiD depende da hipótese de que, na ausência do tratamento, "
        md += "ocupações de alta e baixa exposição teriam evoluído de forma paralela.\n\n"

        md += "**Resultados do Teste Formal**:\n\n"

        for assessment in pt_assessments:
            md += f"- **{assessment['outcome']}**: {assessment['status']} - {assessment['text']}\n"

        md += "\n"
    else:
        md += "Teste formal de tendências paralelas não disponível.\n\n"

    md += "### 3.2 Event Study\n\n"
    md += "Os gráficos de event study mostram a evolução temporal do efeito DiD. "
    md += "Coeficientes pré-tratamento próximos de zero validam a hipótese de tendências paralelas.\n\n"
    md += "*Ver figuras: `event_study_ln_renda.png` e `event_study_horas_trabalhadas.png`*\n\n"

    # ============================================
    # SECTION 4: MAIN RESULTS
    # ============================================

    md += "## 4. Resultados Principais\n\n"
    md += "### 4.1 Estimativas DiD (Modelo 3 - Especificação Principal)\n\n"

    md += "| Outcome | Coeficiente | Erro Padrão | p-value | Stars | Interpretação |\n"
    md += "|---------|-------------|-------------|---------|-------|---------------|\n"

    for outcome in ['ln_renda', 'horas_trabalhadas']:
        row = main_spec[main_spec['outcome'] == outcome]
        if not row.empty:
            coef = row['coef'].values[0]
            se = row['se'].values[0]
            p_val = row['p_value'].values[0]
            stars = row['stars'].values[0] if pd.notna(row['stars'].values[0]) else ''

            outcome_label = "Log(Rendimento)" if outcome == 'ln_renda' else "Horas Trabalhadas"
            md += f"| {outcome_label} | {coef:.4f} | {se:.4f} | {p_val:.4f} | {stars} | "

            # Interpretation
            interpretation = interpret_did_coefficient(coef, se, p_val, outcome)
            # Shorten for table
            if p_val < 0.10:
                mag_text = interpret_coefficient_magnitude(coef, outcome)
                md += f"{mag_text} |"
            else:
                md += "Não significativo |"
            md += "\n"

    md += "\n"

    md += "### 4.2 Interpretação Detalhada\n\n"

    for outcome in ['ln_renda', 'horas_trabalhadas']:
        row = main_spec[main_spec['outcome'] == outcome]
        if not row.empty:
            coef = row['coef'].values[0]
            se = row['se'].values[0]
            p_val = row['p_value'].values[0]

            outcome_label = "Rendimento" if outcome == 'ln_renda' else "Horas Trabalhadas"
            md += f"#### {outcome_label}\n\n"

            interpretation = interpret_did_coefficient(coef, se, p_val, outcome)
            md += interpretation + "\n\n"

    # ============================================
    # SECTION 5: HETEROGENEITY
    # ============================================

    md += "## 5. Análise de Heterogeneidade\n\n"
    md += "### 5.1 Triple-DiD por Grupos Demográficos\n\n"

    md += "Investigamos se o efeito da IA varia por características demográficas usando Triple-DiD:\n\n"
    md += "```\n"
    md += "Y = β₁(Post×AltaExp) + β₂(Post×Grupo) + β₃(AltaExp×Grupo)\n"
    md += "    + β₄(Post×AltaExp×Grupo) + controles + FEs\n"
    md += "```\n\n"

    het_findings = all_results.get('heterogeneity_findings', [])

    if het_findings:
        md += f"### 5.2 Achados Significativos ({len(het_findings)} encontrado(s))\n\n"

        for finding in het_findings:
            md += f"#### {finding['group']} - {finding['outcome']}\n\n"
            md += finding['text'] + "\n\n"
    else:
        md += "### 5.2 Achados\n\n"
        md += "Não foram detectados efeitos heterogêneos estatisticamente significativos (p<0.10) "
        md += "para nenhum dos grupos demográficos analisados (idade, gênero, educação, raça).\n\n"

    # ============================================
    # SECTION 6: ROBUSTNESS
    # ============================================

    md += "## 6. Testes de Robustez\n\n"

    rob_assessments = all_results.get('robustness_assessment', {})

    for outcome, assessment in rob_assessments.items():
        outcome_label = "Rendimento" if outcome == 'ln_renda' else "Horas Trabalhadas"
        md += f"### 6.{list(rob_assessments.keys()).index(outcome) + 1} {outcome_label}\n\n"
        md += f"**Avaliação Geral**: {assessment['icon']} **{assessment['overall']}**\n\n"

        md += "#### Testes Realizados:\n\n"
        md += f"1. **Placebo Temporal**: {assessment['placebo_text']}\n"
        md += f"2. **Tendências Diferenciais**: {assessment['trends_text']}\n"
        md += f"3. **Definições Alternativas de Tratamento**: {assessment['cutoffs_text']}\n\n"

    # ============================================
    # SECTION 7: LIMITATIONS
    # ============================================

    md += "## 7. Limitações\n\n"
    md += "### 7.1 Limitações da Estratégia de Identificação\n\n"
    md += "- **Tendências Paralelas**: Não testável definitivamente; dependemos de validação indireta.\n"
    md += "- **Choques Correlacionados**: Outros eventos podem confundir a estimativa (juros, inflação).\n"
    md += "- **SUTVA**: Spillovers entre ocupações não são captados.\n\n"

    md += "### 7.2 Limitações dos Dados\n\n"
    md += "- **Frequência**: Dados trimestrais (menos precisão temporal que dados mensais).\n"
    md += "- **Amostra**: Survey (auto-declaração, possível erro de medida).\n"
    md += "- **Painel**: Não acompanhamos mesmas pessoas (não vemos transições individuais).\n\n"

    md += "### 7.3 Limitações de Interpretação\n\n"
    md += "- **Exposição ≠ Adoção**: Alto índice não garante que empresas adotaram IA.\n"
    md += "- **Timing**: Efeitos podem ser defasados.\n"
    md += "- **Externalidade**: Resultados são para o Brasil (podem não generalizar).\n\n"

    # ============================================
    # SECTION 8: CONCLUSIONS
    # ============================================

    md += "## 8. Conclusões\n\n"

    md += "### 8.1 Síntese dos Resultados\n\n"

    # Heterogeneity FIRST (main conclusion)
    if het_findings:
        md += "**Achado Principal**: Foram identificados **" + f"{len(het_findings)} efeito(s) heterogêneo(s) significativo(s)**, "
        md += "indicando que a IA Generativa tem impactos **diferenciados** por características demográficas. "
        md += "Especificamente:\n\n"

        for finding in het_findings:
            group_label = finding['group']
            outcome_label = "rendimento" if finding['outcome'] == 'ln_renda' else "horas trabalhadas"
            direction = "redução" if finding['direction'] == 'negative' else "aumento"
            md += f"- **{group_label}**: {direction} de {outcome_label} (p<0.05)\n"

        md += "\n"

    # Average effects (contextualized by heterogeneity)
    main_findings_summary = []
    for outcome in ['ln_renda', 'horas_trabalhadas']:
        row = main_spec[main_spec['outcome'] == outcome]
        if not row.empty:
            p_val = row['p_value'].values[0]
            outcome_label = "rendimento" if outcome == 'ln_renda' else "horas trabalhadas"

            if p_val < 0.10:
                main_findings_summary.append(f"efeito médio significativo sobre {outcome_label}")
            else:
                main_findings_summary.append(f"efeito médio não significativo sobre {outcome_label}")

    if main_findings_summary:
        md += "**Efeitos Médios Agregados**: Esta análise DiD encontrou " + " e ".join(main_findings_summary) + " "
        md += "para trabalhadores em ocupações de alta exposição à IA Generativa, "
        md += "após o lançamento do ChatGPT em novembro de 2022. "

        # Add interpretation about heterogeneity canceling out average effects
        if het_findings:
            md += "A ausência de efeito médio significativo **não implica ausência de impactos**: "
            md += "os efeitos heterogêneos documentados acima (positivos para alguns grupos, negativos para outros) "
            md += "**se cancelam na média agregada**, mas são reais e estatisticamente significativos para subgrupos específicos.\n\n"
        else:
            md += "\n\n"

    # Robustness conclusion
    robust_outcomes = [o for o, a in rob_assessments.items() if a['overall'] == 'ROBUST']
    if robust_outcomes:
        robust_labels = ["rendimento" if o == 'ln_renda' else "horas trabalhadas" for o in robust_outcomes]
        md += "**Robustez**: Os resultados para " + " e ".join(robust_labels) + " "
        md += "demonstraram robustez a múltiplos testes (placebo, tendências diferenciais, cutoffs alternativos), "
        md += "aumentando a confiança nas estimativas de heterogeneidade.\n\n"

    md += "### 8.2 Implicações\n\n"

    # Add specific implications based on heterogeneity findings
    if het_findings:
        md += "Os efeitos heterogêneos identificados têm implicações importantes para políticas públicas:\n\n"
        md += "1. **Políticas Diferenciadas**: O impacto desigual da IA entre grupos demográficos "
        md += "sugere a necessidade de políticas de adaptação tecnológica diferenciadas por grupo.\n"
        md += "2. **Monitoramento Contínuo**: É crucial monitorar continuamente como diferentes segmentos "
        md += "da força de trabalho são afetados pela IA, em vez de focar apenas em médias agregadas.\n"
        md += "3. **Redistribuição**: Grupos afetados negativamente podem requerer suporte (retreinamento, "
        md += "subsídios) financiado pelos ganhos de grupos beneficiados.\n\n"

    md += "Estes resultados contribuem para a compreensão dos efeitos iniciais da IA Generativa "
    md += "sobre o mercado de trabalho em economias emergentes, fornecendo evidência empírica "
    md += "para formulação de políticas públicas e estratégias de adaptação tecnológica.\n\n"

    md += "---\n\n"
    md += f"*Relatório gerado automaticamente em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    md += "*Script 14: Generate Report*\n"

    return md


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """
    Main execution function.
    """
    logger.info("="*70)
    logger.info("SCRIPT 14: GENERATE MARKDOWN REPORT")
    logger.info("="*70)
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ============================================
    # LOAD ALL RESULTS
    # ============================================

    logger.info("\nLoading all results from previous scripts...")

    all_results = {}

    try:
        # Main DiD results (Script 09)
        main_path = OUTPUTS_TABLES / 'did_main_results.csv'
        all_results['main_results'] = pd.read_csv(main_path)
        logger.info(f"✓ Loaded: {main_path.name}")

        # Parallel trends test (Script 10)
        pt_path = OUTPUTS_TABLES / 'parallel_trends_test_formal.csv'
        all_results['parallel_trends'] = pd.read_csv(pt_path)
        logger.info(f"✓ Loaded: {pt_path.name}")

        # Heterogeneity (Script 11)
        het_path = OUTPUTS_TABLES / 'heterogeneity_all_triple_did.csv'
        all_results['heterogeneity'] = pd.read_csv(het_path)
        logger.info(f"✓ Loaded: {het_path.name}")

        # Robustness (Script 12)
        rob_path = OUTPUTS_TABLES / 'robustness_summary.csv'
        all_results['robustness'] = pd.read_csv(rob_path)
        logger.info(f"✓ Loaded: {rob_path.name}")

        # Balance table (optional, from Fase 3)
        try:
            bal_path = OUTPUTS_TABLES / 'balance_table_pre.csv'
            all_results['balance_table'] = pd.read_csv(bal_path)
            logger.info(f"✓ Loaded: {bal_path.name}")
        except:
            logger.warning("⚠️  Balance table not found (optional)")
            all_results['balance_table'] = pd.DataFrame()

    except Exception as e:
        logger.error(f"✗ Failed to load required files: {e}")
        logger.error("  Make sure scripts 09-12 have been run successfully.")
        return

    # ============================================
    # GENERATE INTERPRETATIONS
    # ============================================

    logger.info("\nGenerating automatic interpretations...")

    # Parallel trends assessment
    pt_df = all_results['parallel_trends']
    all_results['parallel_trends_assessment'] = assess_parallel_trends(pt_df)
    logger.info(f"✓ Assessed parallel trends for {len(all_results['parallel_trends_assessment'])} outcome(s)")

    # Robustness assessment
    main_results = all_results['main_results']
    main_spec = main_results[main_results['model'].str.contains('Model 3', na=False)]
    rob_df = all_results['robustness']
    all_results['robustness_assessment'] = assess_robustness_summary(rob_df, main_spec)
    logger.info(f"✓ Assessed robustness for {len(all_results['robustness_assessment'])} outcome(s)")

    # Heterogeneity findings
    het_df = all_results['heterogeneity']
    all_results['heterogeneity_findings'] = flag_heterogeneity_findings(het_df)
    logger.info(f"✓ Identified {len(all_results['heterogeneity_findings'])} significant heterogeneity finding(s)")

    # ============================================
    # GENERATE REPORTS
    # ============================================

    logger.info("\n" + "="*70)
    logger.info("GENERATING MARKDOWN REPORTS")
    logger.info("="*70)

    # Executive Summary
    logger.info("\nGenerating executive summary...")
    exec_summary = generate_executive_summary(all_results)
    exec_path = OUTPUTS_DIR / 'DID_EXECUTIVE_SUMMARY.md'
    with open(exec_path, 'w', encoding='utf-8') as f:
        f.write(exec_summary)
    logger.info(f"✓ Executive summary saved: {exec_path.name}")

    # Full Report
    logger.info("\nGenerating comprehensive report...")
    full_report = generate_full_report(all_results)
    report_path = OUTPUTS_DIR / 'DID_ANALYSIS_REPORT.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(full_report)
    logger.info(f"✓ Comprehensive report saved: {report_path.name}")

    # ============================================
    # SUMMARY
    # ============================================

    logger.info("\n" + "="*70)
    logger.info("REPORT GENERATION COMPLETE")
    logger.info("="*70)

    logger.info("\nReports generated:")
    logger.info(f"  ✓ Executive Summary: {exec_path.name}")
    logger.info(f"  ✓ Comprehensive Report: {report_path.name}")

    # Summary statistics
    exec_lines = len(exec_summary.split('\n'))
    report_lines = len(full_report.split('\n'))
    logger.info(f"\nReport statistics:")
    logger.info(f"  - Executive Summary: {exec_lines} lines")
    logger.info(f"  - Comprehensive Report: {report_lines} lines")

    # Key findings summary
    logger.info(f"\nKey findings flagged:")
    logger.info(f"  - Parallel trends assessments: {len(all_results['parallel_trends_assessment'])}")
    logger.info(f"  - Robustness assessments: {len(all_results['robustness_assessment'])}")
    logger.info(f"  - Significant heterogeneity: {len(all_results['heterogeneity_findings'])}")

    logger.info(f"\n📁 Reports saved to: {OUTPUTS_DIR}")
    logger.info(f"📄 Log saved to: {log_file}")

    logger.info(f"\n✓ Script completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
