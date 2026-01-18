"""
Funções de validação para o pipeline
"""

import pandas as pd
import numpy as np


def validate_pnad_download(df):
    """Valida download da PNAD"""
    errors = []
    
    # Verificar colunas essenciais
    required_cols = ['cod_ocupacao', 'peso', 'rendimento_habitual', 'idade', 'sigla_uf']
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Coluna ausente: {col}")
    
    # Verificar UFs
    if 'sigla_uf' in df.columns:
        ufs = df['sigla_uf'].nunique()
        if ufs != 27:
            errors.append(f"UFs incompletas: {ufs}/27")
    
    # Verificar tamanho mínimo
    if len(df) < 100000:
        errors.append(f"Dados insuficientes: {len(df)} linhas")
    
    return len(errors) == 0, errors


def validate_ilo_scores(df):
    """Valida scores ILO processados"""
    errors = []
    
    # Verificar colunas
    required_cols = ['isco_08_str', 'exposure_score']
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Coluna ausente: {col}")
    
    # Verificar número de ocupações
    if len(df) < 400:
        errors.append(f"Poucas ocupações: {len(df)} (esperado ~427)")
    
    # Verificar range de scores
    if 'exposure_score' in df.columns:
        scores = df['exposure_score']
        if scores.min() < 0 or scores.max() > 1:
            errors.append(f"Scores fora do range [0,1]: [{scores.min()}, {scores.max()}]")
    
    return len(errors) == 0, errors


def validate_crosswalk_coverage(df, min_coverage=0.90):
    """Valida cobertura do crosswalk"""
    errors = []
    
    if 'exposure_score' not in df.columns:
        errors.append("Coluna 'exposure_score' ausente")
        return False, errors
    
    coverage = df['exposure_score'].notna().mean()
    
    if coverage < min_coverage:
        errors.append(f"Cobertura baixa: {coverage:.1%} (mínimo {min_coverage:.0%})")
    
    return len(errors) == 0, errors


def validate_sanity_checks(df):
    """Valida sanity checks por grande grupo"""
    from .weighted_stats import weighted_mean
    
    errors = []
    warnings = []
    
    if 'grande_grupo' not in df.columns or 'exposure_score' not in df.columns:
        errors.append("Colunas necessárias ausentes para sanity check")
        return False, errors, warnings
    
    # Calcular exposição por grupo
    exp_grupos = df.groupby('grande_grupo').apply(
        lambda x: weighted_mean(x['exposure_score'].dropna(), x.loc[x['exposure_score'].notna(), 'peso'])
    )
    
    # Verificações esperadas
    if 'Profissionais das ciências' in exp_grupos.index:
        if exp_grupos['Profissionais das ciências'] < 0.30:
            warnings.append(f"Profissionais com exposição baixa: {exp_grupos['Profissionais das ciências']:.3f}")
    
    if 'Ocupações elementares' in exp_grupos.index:
        if exp_grupos['Ocupações elementares'] > 0.20:
            warnings.append(f"Elementares com exposição alta: {exp_grupos['Ocupações elementares']:.3f}")
    
    return len(errors) == 0, errors, warnings
