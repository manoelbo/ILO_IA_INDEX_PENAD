"""
Funções auxiliares para agregação de scores
"""
import pandas as pd
import numpy as np


def normalize_task_name(task: str) -> str:
    """Normaliza nome da tarefa para matching."""
    if pd.isna(task):
        return ""
    return task.lower().strip()


def extract_soc_6digit(onet_code: str) -> str:
    """
    Extrai código SOC 6 dígitos do código O*NET-SOC.
    
    Exemplo: '11-1011.00' -> '11-1011'
             '15-1252.00' -> '15-1252'
    """
    if pd.isna(onet_code):
        return None
    # Remove o sufixo .XX
    return onet_code.split('.')[0]


def calculate_automation_score(row: pd.Series, 
                               automation_cols: list,
                               augmentation_cols: list) -> dict:
    """
    Calcula scores de automação e aumentação para uma linha.
    
    Retorna dict com automation_score, augmentation_score, filtered_ratio
    """
    automation = sum(row.get(col, 0) or 0 for col in automation_cols)
    augmentation = sum(row.get(col, 0) or 0 for col in augmentation_cols)
    filtered = row.get('filtered', 0) or 0
    
    # Total para normalização (deve ser ~1.0)
    total = automation + augmentation + filtered
    
    if total > 0:
        return {
            'automation_raw': automation,
            'augmentation_raw': augmentation,
            'filtered_ratio': filtered,
            'automation_score': automation / (automation + augmentation) if (automation + augmentation) > 0 else 0.5,
            'augmentation_score': augmentation / (automation + augmentation) if (automation + augmentation) > 0 else 0.5
        }
    return {
        'automation_raw': 0,
        'augmentation_raw': 0,
        'filtered_ratio': 1.0,
        'automation_score': np.nan,
        'augmentation_score': np.nan
    }


def aggregate_to_occupation(df: pd.DataFrame, 
                            group_col: str = 'soc_code') -> pd.DataFrame:
    """
    Agrega scores de tarefas para nível de ocupação.
    
    Usa média simples dos scores de cada tarefa.
    """
    agg_funcs = {
        'soc_title': 'first',
        'automation_score': 'mean',
        'augmentation_score': 'mean',
        'automation_raw': 'mean',
        'augmentation_raw': 'mean',
        'filtered_ratio': 'mean',
        'task_name': 'count'  # conta tarefas matched
    }
    
    result = df.groupby(group_col).agg(agg_funcs).reset_index()
    result = result.rename(columns={'task_name': 'n_tasks_matched'})
    
    return result
