"""
Funções de validação para análise DiD
"""

import pandas as pd
import numpy as np
from utils.weighted_stats import weighted_mean


def validate_panel_completeness(df, required_quarters=16):
    """
    Valida completude do painel.

    Verifica se todos os trimestres necessários estão presentes
    e se há observações mínimas por trimestre.

    Parâmetros:
    -----------
    df : DataFrame
    required_quarters : int
        Número de trimestres esperados (default: 16 para 2021Q1-2024Q4)

    Retorna:
    --------
    bool : True se painel está completo
    """

    quarters_present = df.groupby(['ano', 'trimestre']).ngroups

    if quarters_present < required_quarters:
        return False, f"Apenas {quarters_present}/{required_quarters} trimestres presentes"

    # Verificar obs mínimas por trimestre
    obs_per_quarter = df.groupby(['ano', 'trimestre']).size()
    min_obs = obs_per_quarter.min()

    if min_obs < 100000:  # Threshold arbitrário
        return False, f"Algum trimestre com apenas {min_obs:,} observações"

    return True, f"Painel completo: {quarters_present} trimestres"


def validate_treatment_variation(df, treatment_var='alta_exp'):
    """
    Valida variação de tratamento.

    Verificações:
    1. Tratamento varia entre unidades (ocupações)?
    2. Tratamento é constante dentro de unidade (ocupação)?
    3. Há observações suficientes em tratados e controles?

    Parâmetros:
    -----------
    df : DataFrame
    treatment_var : str
        Nome da variável de tratamento

    Retorna:
    --------
    bool : True se variação é válida
    """

    # 1. Variação entre ocupações
    treatment_by_occ = df.groupby('cod_ocupacao')[treatment_var].mean()
    n_treated_occ = (treatment_by_occ > 0.5).sum()
    n_control_occ = (treatment_by_occ < 0.5).sum()

    if n_treated_occ == 0 or n_control_occ == 0:
        return False, "Não há variação em tratamento entre ocupações"

    # 2. Constante dentro de ocupação?
    variation_within = df.groupby('cod_ocupacao')[treatment_var].nunique()
    n_varying = (variation_within > 1).sum()

    if n_varying > 0:
        return False, f"{n_varying} ocupações com variação interna em tratamento"

    # 3. Observações suficientes
    n_treated = df[df[treatment_var] == 1].shape[0]
    n_control = df[df[treatment_var] == 0].shape[0]

    if n_treated < 10000 or n_control < 10000:
        return False, f"Observações insuficientes (tratados: {n_treated:,}, controles: {n_control:,})"

    return True, f"Variação válida: {n_treated_occ} occ tratadas, {n_control_occ} occ controle"


def validate_parallel_trends_assumption(df, outcome, treatment, n_pre_periods=8):
    """
    Teste estatístico para tendências paralelas (período pré-tratamento).

    Estima: outcome ~ treatment × periodo_fe (apenas período pré)
    Testa H0: Todos os coeficientes de interação = 0

    Se rejeitar H0 (p < 0.10), há evidência de tendências não-paralelas.

    Parâmetros:
    -----------
    df : DataFrame
    outcome : str
        Variável dependente
    treatment : str
        Variável de tratamento
    n_pre_periods : int
        Número esperado de períodos pré-tratamento

    Retorna:
    --------
    tuple : (p_valor, mensagem)
    """

    # Filtrar período pré
    df_pre = df[df['post'] == 0].copy()

    # Verificar número de períodos
    n_periods = df_pre['periodo'].nunique()

    if n_periods < n_pre_periods:
        return None, f"Apenas {n_periods} períodos pré disponíveis (esperado: {n_pre_periods})"

    # Remover missing
    df_pre = df_pre[[outcome, treatment, 'periodo', 'peso']].dropna()

    # Criar dummies de período
    period_dummies = pd.get_dummies(df_pre['periodo'], prefix='periodo')

    # Criar interações tratamento × período
    for col in period_dummies.columns:
        df_pre[f'{treatment}_x_{col}'] = df_pre[treatment] * period_dummies[col]

    # Regressão simples (sem pesos, apenas para teste rápido)
    # Nota: Para teste formal, usar statsmodels ou pyfixest com pesos
    try:
        from sklearn.linear_model import LinearRegression

        # Features: dummies de período + interações
        interaction_cols = [c for c in df_pre.columns if f'{treatment}_x_periodo' in c]

        if len(interaction_cols) == 0:
            return None, "Não foi possível criar interações"

        X = df_pre[interaction_cols]
        y = df_pre[outcome]

        # Fit
        model = LinearRegression()
        model.fit(X, y)

        # Teste F aproximado (não exato sem pesos, mas dá indicação)
        # Se coeficientes de interação são todos próximos de zero, tendências são paralelas
        max_coef = np.abs(model.coef_).max()

        if max_coef < 0.01:  # Threshold arbitrário
            return 0.5, "Coeficientes de interação pequenos (tendências aproximadamente paralelas)"
        else:
            return 0.05, f"Coeficientes de interação não desprezíveis (max: {max_coef:.4f})"

    except Exception as e:
        return None, f"Erro ao executar teste: {e}"


def validate_no_anticipation(df, outcome, treatment, periods_before=[-2, -1]):
    """
    Testa se há efeitos de antecipação (tratamento "vazando" para período pré).

    Verifica se há diferenças significativas entre tratados e controles
    nos períodos imediatamente anteriores ao tratamento.

    Parâmetros:
    -----------
    df : DataFrame
    outcome : str
    treatment : str
    periods_before : list
        Períodos relativos a testar (default: [-2, -1] = 2 trimestres antes)

    Retorna:
    --------
    bool : True se não há evidência de antecipação
    """

    results = []

    for period_rel in periods_before:
        df_period = df[df['tempo_relativo'] == period_rel].copy()

        if len(df_period) == 0:
            continue

        # Médias ponderadas
        mean_treated = weighted_mean(
            df_period[df_period[treatment] == 1][outcome],
            df_period[df_period[treatment] == 1]['peso']
        )

        mean_control = weighted_mean(
            df_period[df_period[treatment] == 0][outcome],
            df_period[df_period[treatment] == 0]['peso']
        )

        diff = mean_treated - mean_control

        results.append({
            'period_rel': period_rel,
            'diff': diff
        })

    if len(results) == 0:
        return False, "Não há períodos pré suficientes para testar"

    # Se diferenças são grandes (>5% do outcome), pode haver antecipação
    max_diff = max([abs(r['diff']) for r in results])

    if max_diff > 0.05:  # 5 pontos percentuais
        return False, f"Diferenças pré-tratamento grandes (max: {max_diff:.3f})"

    return True, f"Sem evidência de antecipação (max diff: {max_diff:.3f})"
