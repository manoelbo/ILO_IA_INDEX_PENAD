"""
Script de teste: Verificar disponibilidade de dados PNAD
"""

import basedosdados as bd
import sys
sys.path.append('..')
from config.settings import GCP_PROJECT_ID

print("Testando conexão BigQuery...")
print(f"Projeto: {GCP_PROJECT_ID}")

# Query para verificar anos/trimestres disponíveis
query_test = """
SELECT DISTINCT ano, trimestre, COUNT(*) as n_obs
FROM `basedosdados.br_ibge_pnad_continua.microdados`
WHERE ano >= 2023
GROUP BY ano, trimestre
ORDER BY ano DESC, trimestre DESC
LIMIT 10
"""

print("\nBuscando trimestres disponíveis...")
try:
    df = bd.read_sql(query_test, billing_project_id=GCP_PROJECT_ID)
    print("\nTrimestres disponíveis:")
    print(df)
    
    # Verificar se 2025 Q3 existe
    if len(df[(df['ano'] == 2025) & (df['trimestre'] == 3)]) > 0:
        print("\n✓ Dados de 2025 Q3 DISPONÍVEIS")
    else:
        print("\n⚠️ Dados de 2025 Q3 NÃO DISPONÍVEIS")
        print(f"Trimestre mais recente: {df.iloc[0]['ano']} Q{df.iloc[0]['trimestre']}")
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    print("\nVerifique se:")
    print("1. Você está autenticado: gcloud auth application-default login")
    print("2. O projeto está correto: dissertacao-ia-br")
    print("3. Billing está ativado no projeto")
