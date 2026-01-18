"""
Teste: Validar base final merged
Executar após: 05_merge_data.py
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *

def test_merged_data():
    """Testa integridade da base final"""
    
    file_path = DATA_PROCESSED / "pnad_ilo_merged.csv"
    
    # Teste 1: Arquivo existe
    assert file_path.exists(), f"Arquivo não encontrado: {file_path}"
    print("✓ Arquivo existe")
    
    df = pd.read_csv(file_path)
    
    # Teste 2: Colunas essenciais
    required = [
        'exposure_score', 'exposure_gradient', 'quintil_exposure',
        'grande_grupo', 'regiao', 'setor_agregado', 'peso',
        'rendimento_habitual', 'sexo_texto', 'raca_agregada', 'formal'
    ]
    for col in required:
        assert col in df.columns, f"Coluna ausente: {col}"
    print("✓ Colunas essenciais presentes")
    
    # Teste 3: Cobertura de exposure_score
    coverage = df['exposure_score'].notna().mean()
    assert coverage >= 0.85, f"Cobertura de score baixa: {coverage:.1%}"
    print(f"✓ Cobertura de scores: {coverage:.1%}")
    
    # Teste 4: Score no range válido [0, 1]
    scores = df['exposure_score'].dropna()
    assert scores.min() >= 0, f"Score mínimo inválido: {scores.min()}"
    assert scores.max() <= 1, f"Score máximo inválido: {scores.max()}"
    print(f"✓ Scores no range [0, 1]: [{scores.min():.3f}, {scores.max():.3f}]")
    
    # Teste 5: Gradientes atribuídos
    grad_coverage = df['exposure_gradient'].notna().mean()
    assert grad_coverage >= 0.85, f"Gradientes incompletos: {grad_coverage:.1%}"
    print(f"✓ Gradientes atribuídos: {grad_coverage:.1%}")
    
    # Teste 6: Quintis balanceados
    quintil_counts = df['quintil_exposure'].value_counts()
    if len(quintil_counts) > 0:
        min_pct = quintil_counts.min() / len(df) * 100
        max_pct = quintil_counts.max() / len(df) * 100
        assert max_pct - min_pct < 15, "Quintis muito desbalanceados"
        print(f"✓ Quintis balanceados ({min_pct:.1f}% - {max_pct:.1f}%)")
    
    # Teste 7: Peso total consistente
    pop = df['peso'].sum() / 1e6
    assert 50 < pop < 150, f"População fora do esperado: {pop:.1f}M"
    print(f"✓ População: {pop:.1f} milhões")
    
    print("\n🎉 TODOS OS TESTES PASSARAM - BASE FINAL OK!")
    return True

if __name__ == "__main__":
    test_merged_data()
