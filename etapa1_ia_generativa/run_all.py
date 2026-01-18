"""
Script Master: Executa todo o pipeline da Etapa 1
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_script(script_name, *args):
    """Executa um script e retorna status"""
    print(f"\n{'='*60}")
    print(f"EXECUTANDO: {script_name} {' '.join(args)}")
    print(f"{'='*60}\n")
    
    cmd = [sys.executable, f"src/{script_name}"] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ ERRO em {script_name}:")
        print(result.stderr)
        return False
    
    print(result.stdout)
    print(f"✓ {script_name} concluído com sucesso")
    return True

def run_test(test_name):
    """Executa um teste"""
    print(f"\n>>> Executando teste: {test_name}")
    result = subprocess.run(
        [sys.executable, f"tests/{test_name}"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    return result.returncode == 0

def main():
    """Pipeline completo"""
    
    start_time = datetime.now()
    print("=" * 60)
    print("ETAPA 1 - PIPELINE COMPLETO")
    print(f"Início: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Etapa 1: Download PNAD
    print("\n⚠️ ETAPA 1: Download PNAD")
    print("Certifique-se de ter:")
    print("1. BigQuery API ativada")
    print("2. Billing configurado")
    print("3. Autenticação feita (gcloud auth application-default login)")
    input("\nPressione ENTER para continuar com o download...")
    
    if not run_script("01_download_pnad.py", "--reauth"):
        return False
    run_test("test_01_download.py")
    
    # Etapa 2: Processar ILO
    if not run_script("02_process_ilo.py"):
        return False
    
    # Etapa 3: Limpar PNAD
    if not run_script("03_clean_pnad.py"):
        return False
    
    # Etapa 4: Crosswalk (validação manual recomendada)
    if not run_script("04_crosswalk.py"):
        return False
    
    print("\n" + "="*60)
    print("⚠️ ATENÇÃO: Revise o log do crosswalk antes de prosseguir")
    print("="*60)
    input("Pressione ENTER para continuar...")
    
    # Etapa 5: Merge
    if not run_script("05_merge_data.py"):
        return False
    run_test("test_05_merge.py")
    
    # Etapa 6: Gerar Tabelas
    if not run_script("06_analysis_tables.py"):
        return False
    
    # Etapa 7: Gerar Figuras
    if not run_script("07_analysis_figures.py"):
        return False
    
    # Finalização
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60
    
    print("\n" + "=" * 60)
    print("🎉 PIPELINE CONCLUÍDO COM SUCESSO!")
    print(f"Duração total: {duration:.1f} minutos")
    print(f"Fim: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print("\n📁 OUTPUTS GERADOS:")
    print("  - data/processed/pnad_ilo_merged.csv")
    print("  - outputs/tables/*.csv e *.tex")
    print("  - outputs/figures/*.png e *.pdf")
    print("  - outputs/logs/*.log")
    
    return True

if __name__ == "__main__":
    main()
