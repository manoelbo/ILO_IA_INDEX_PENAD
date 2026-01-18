"""
Teste: Validar download PNAD
Executar após: 01_download_pnad.py
"""

import pandas as pd
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import *

def test_download():
    """Testa se download foi bem sucedido"""
    
    file_path = DATA_RAW / f"pnad_{PNAD_ANO}q{PNAD_TRIMESTRE}.parquet"
    
    # Teste 1: Arquivo existe
    assert file_path.exists(), f"Arquivo não encontrado: {file_path}"
    print("✓ Arquivo existe")
    
    # Teste 2: Carregar e verificar tamanho
    df = pd.read_parquet(file_path)
    assert len(df) > 100000, f"Dados insuficientes: {len(df)} linhas"
    print(f"✓ {len(df):,} observações carregadas")
    
    # Teste 3: Colunas esperadas
    expected_cols = ['cod_ocupacao', 'peso', 'rendimento_habitual', 'idade', 'sigla_uf']
    for col in expected_cols:
        assert col in df.columns, f"Coluna ausente: {col}"
    print(f"✓ Colunas esperadas presentes")
    
    # Teste 4: Todas UFs presentes
    ufs = df['sigla_uf'].nunique()
    assert ufs == 27, f"UFs incompletas: {ufs}/27"
    print(f"✓ Todas 27 UFs presentes")
    
    # Teste 5: Peso válido
    assert df['peso'].sum() > 50e6, "Peso total muito baixo"
    print(f"✓ População: {df['peso'].sum()/1e6:.1f} milhões")
    
    print("\n🎉 TODOS OS TESTES PASSARAM - DOWNLOAD OK!")
    return True

if __name__ == "__main__":
    test_download()
