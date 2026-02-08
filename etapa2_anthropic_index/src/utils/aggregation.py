import numpy as np
import pandas as pd

def weighted_mean(values, weights):
    """Calcula a média ponderada de uma série de valores."""
    if len(values) == 0:
        return 0
    return np.average(values, weights=weights)

def calculate_indices(df_task):
    """
    Calcula os shares de automation e augmentation com base nos modos de colaboração.
    Espera um DataFrame onde as colunas são os modos (directive, learning, etc.)
    """
    # Garantir que todas as colunas necessárias existam
    required_modes = ["directive", "feedback loop", "learning", "task iteration", "validation"]
    for mode in required_modes:
        if mode not in df_task.columns:
            df_task[mode] = 0
            
    # Calcular Totais Categorizados (excluindo none/not_classified se houver)
    df_task['total_collab'] = df_task[required_modes].sum(axis=1)
    
    # Evitar divisão por zero
    mask = df_task['total_collab'] > 0
    
    df_task.loc[mask, 'automation_share'] = (df_task.loc[mask, "directive"] + df_task.loc[mask, "feedback loop"]) / df_task.loc[mask, 'total_collab']
    df_task.loc[mask, 'augmentation_share'] = (df_task.loc[mask, "learning"] + df_task.loc[mask, "task iteration"] + df_task.loc[mask, "validation"]) / df_task.loc[mask, 'total_collab']
    
    # Preencher NaNs (casos sem colab classificada)
    df_task['automation_share'] = df_task['automation_share'].fillna(0)
    df_task['augmentation_share'] = df_task['augmentation_share'].fillna(0)
    
    # Índice de Automação: (Share Auto - Share Aug)
    # Range: -1 (Total Augmentation) a +1 (Total Automation)
    df_task['automation_index'] = df_task['automation_share'] - df_task['augmentation_share']
    
    # Modo Dominante
    df_task['dominant_mode'] = np.where(df_task['automation_index'] > 0, "automation", "augmentation")
    df_task.loc[df_task['total_collab'] == 0, 'dominant_mode'] = "none"
    
    return df_task
