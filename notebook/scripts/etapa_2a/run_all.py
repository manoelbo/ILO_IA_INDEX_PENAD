"""
Runner: Executa todos os scripts da Etapa 2a em sequência.
Uso: python notebook/scripts/etapa_2a/run_all.py

Para pular o download (script 01), use --skip-download:
  python notebook/scripts/etapa_2a/run_all.py --skip-download
"""

import sys
import subprocess
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

SCRIPTS = [
    ("01_download_caged.py",     "Download CAGED"),
    ("02_verificar_caged.py",    "Checkpoint: Verificar CAGED"),
    ("03_agregar_painel.py",     "Agregar painel mensal"),
    ("04_verificar_painel.py",   "Checkpoint: Verificar painel"),
    ("05_crosswalk_cbo_isco.py", "Crosswalk CBO → ISCO-08"),
    ("06_verificar_crosswalk.py","Checkpoint: Verificar crosswalk"),
    ("07_definir_tratamento.py", "Definir tratamento"),
    ("08_verificar_tratamento.py","Checkpoint: Verificar tratamento"),
    ("09_enriquecer_e_salvar.py","Enriquecer e salvar final"),
]

def main():
    skip_download = "--skip-download" in sys.argv

    print("=" * 60)
    print("ETAPA 2a — Pipeline Completo")
    print("=" * 60)

    t_total = time.time()
    resultados = []

    for script_name, descricao in SCRIPTS:
        if skip_download and script_name == "01_download_caged.py":
            print(f"\n  [SKIP] {descricao} (--skip-download)")
            resultados.append((script_name, "SKIP", 0))
            continue

        script_path = SCRIPTS_DIR / script_name
        print(f"\n{'─' * 60}")
        print(f"  Executando: {script_name} ({descricao})")
        print(f"{'─' * 60}")

        t0 = time.time()
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(SCRIPTS_DIR.parent.parent.parent),  # repo root
        )
        elapsed = time.time() - t0

        status = "OK" if result.returncode == 0 else "ERRO"
        resultados.append((script_name, status, elapsed))
        print(f"\n  [{status}] {script_name} ({elapsed:.0f}s)")

        if result.returncode != 0:
            print(f"  ERRO: {script_name} falhou com código {result.returncode}")
            print(f"  Abortando pipeline.")
            break

    # Resumo
    elapsed_total = time.time() - t_total
    print(f"\n{'=' * 60}")
    print(f"RESUMO — Pipeline Etapa 2a")
    print(f"{'=' * 60}")
    for script_name, status, elapsed in resultados:
        print(f"  [{status:>4}] {script_name:<30} {elapsed:>6.0f}s")
    print(f"\n  Tempo total: {elapsed_total:.0f}s ({elapsed_total/60:.1f} min)")


if __name__ == "__main__":
    main()
