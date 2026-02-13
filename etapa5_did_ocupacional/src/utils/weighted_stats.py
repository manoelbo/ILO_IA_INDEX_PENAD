"""
Funções utilitárias para estatísticas ponderadas
Copiado e estendido de etapa1_ia_generativa
"""

import numpy as np
import pandas as pd

def weighted_mean(values, weights):
    """Calcula média ponderada"""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    return np.average(values[mask], weights=weights[mask])

def weighted_std(values, weights):
    """Calcula desvio-padrão ponderado"""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan
    avg = np.average(values[mask], weights=weights[mask])
    variance = np.average((values[mask] - avg) ** 2, weights=weights[mask])
    return np.sqrt(variance)

def weighted_quantile(values, weights, quantile):
    """Calcula quantil ponderado"""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() == 0:
        return np.nan

    sorted_idx = np.argsort(values[mask])
    sorted_values = values[mask].iloc[sorted_idx]
    sorted_weights = weights[mask].iloc[sorted_idx]

    cumsum = np.cumsum(sorted_weights)
    cutoff = quantile * cumsum.iloc[-1]

    return sorted_values.iloc[np.searchsorted(cumsum, cutoff)]

def gini_coefficient(values, weights):
    """Calcula coeficiente de Gini ponderado"""
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() < 2:
        return np.nan

    x = np.array(values[mask])
    w = np.array(weights[mask])

    sorted_idx = np.argsort(x)
    sorted_x = x[sorted_idx]
    sorted_w = w[sorted_idx]

    cumsum_w = np.cumsum(sorted_w)
    cumsum_wx = np.cumsum(sorted_w * sorted_x)

    total_w = cumsum_w[-1]
    total_wx = cumsum_wx[-1]

    # Área sob curva de Lorenz
    B = np.sum(cumsum_wx[:-1] * sorted_w[1:]) / (total_w * total_wx)

    return 1 - 2 * B

def weighted_stats_summary(values, weights):
    """Retorna dicionário com estatísticas resumidas"""
    return {
        'mean': weighted_mean(values, weights),
        'std': weighted_std(values, weights),
        'p25': weighted_quantile(values, weights, 0.25),
        'p50': weighted_quantile(values, weights, 0.50),
        'p75': weighted_quantile(values, weights, 0.75),
        'n': (~pd.isna(values)).sum(),
        'population': weights[~pd.isna(values)].sum()
    }

def weighted_diff_normalized(values_t, weights_t, values_c, weights_c):
    """
    Calcula diferença normalizada (standardized difference) para balance table.

    Usado para avaliar desbalanceamento de covariáveis entre grupos de tratamento
    e controle. Regra de ouro: valores > 0.25 indicam desbalanceamento substancial.

    Parâmetros:
    -----------
    values_t : array-like
        Valores do grupo de tratamento
    weights_t : array-like
        Pesos do grupo de tratamento
    values_c : array-like
        Valores do grupo de controle
    weights_c : array-like
        Pesos do grupo de controle

    Retorna:
    --------
    float : Diferença normalizada
    """
    mean_t = weighted_mean(values_t, weights_t)
    mean_c = weighted_mean(values_c, weights_c)
    std_t = weighted_std(values_t, weights_t)
    std_c = weighted_std(values_c, weights_c)

    # Pooled standard deviation
    pooled_std = np.sqrt((std_t**2 + std_c**2) / 2)

    if pooled_std > 0:
        return (mean_t - mean_c) / pooled_std
    else:
        return np.nan

def weighted_se(values, weights):
    """
    Calcula erro padrão ponderado.

    Usado para construir intervalos de confiança em gráficos de tendências paralelas.
    """
    mask = ~(pd.isna(values) | pd.isna(weights))
    if mask.sum() < 2:
        return np.nan

    n_eff = (weights[mask].sum() ** 2) / (weights[mask] ** 2).sum()  # Effective sample size
    std = weighted_std(values, weights)

    return std / np.sqrt(n_eff)
