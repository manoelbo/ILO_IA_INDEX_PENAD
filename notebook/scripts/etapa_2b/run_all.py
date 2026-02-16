"""
Runner: Executa todos os scripts da Etapa 2b em sequência.
Uso: python notebook/scripts/etapa_2b/run_all.py
CWD recomendado: notebook/ (ou raiz do repositório; os scripts usam paths absolutos).
"""

import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
NOTEBOOK_DIR = SCRIPTS_DIR.parent.parent

SCRIPTS = [
    ("01_load_and_prepare.py", "Carregar e preparar painel (winsorização)"),
    ("02_balance_table.py", "Tabela de balanço"),
    ("03_parallel_trends_visual.py", "Tendências paralelas (visual)"),
    ("04_did_main.py", "Estimação DiD principal"),
    ("05_checkpoint_did.py", "Checkpoint resultados DiD"),
    ("06_event_study.py", "Event study"),
    ("07_event_study_plots.py", "Gráficos event study"),
    ("08_parallel_trends_test.py", "Teste formal tendências paralelas"),
    ("09_heterogeneity.py", "Heterogeneidade (Triple-DiD)"),
    ("10_robustness.py", "Testes de robustez"),
    ("11_latex_tables.py", "Tabelas LaTeX"),
    ("12_synthesis.py", "Síntese e conclusões"),
]


def main():
    print("=" * 60)
    print("ETAPA 2b — Pipeline Completo (Análise DiD)")
    print("=" * 60)

    t_total = time.time()
    resultados = []

    for script_name, descricao in SCRIPTS:
        script_path = SCRIPTS_DIR / script_name
        print(f"\n{'─' * 60}")
        print(f"  Executando: {script_name} ({descricao})")
        print(f"{'─' * 60}")

        t0 = time.time()
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(NOTEBOOK_DIR),
        )
        elapsed = time.time() - t0

        status = "OK" if result.returncode == 0 else "ERRO"
        resultados.append((script_name, status, elapsed))
        print(f"\n  [{status}] {script_name} ({elapsed:.0f}s)")

        if result.returncode != 0:
            print(f"  ERRO: {script_name} falhou com código {result.returncode}")
            print("  Abortando pipeline.")
            break

    elapsed_total = time.time() - t_total
    print(f"\n{'=' * 60}")
    print("RESUMO — Pipeline Etapa 2b")
    print(f"{'=' * 60}")
    for script_name, status, elapsed in resultados:
        print(f"  [{status:>4}] {script_name:<30} {elapsed:>6.0f}s")
    print(f"\n  Tempo total: {elapsed_total:.0f}s ({elapsed_total/60:.1f} min)")


if __name__ == "__main__":
    main()
