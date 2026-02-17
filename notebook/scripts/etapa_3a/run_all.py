"""
Runner: Executa todos os scripts da Etapa 3a em sequência.
Uso: python notebook/scripts/etapa_3a/run_all.py

Para pular download Anatel/IBGE (usar cache): --skip-download
Para pular agregação CAGED (usar painel_caged_municipio.parquet existente): --skip-aggregate
"""

import sys
import subprocess
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# Ordem: Anatel, IBGE, Conectividade, Agregar CAGED municipal, Merge final
SCRIPTS = [
    ("01_anatel.py", "Anatel banda larga (pré-tratamento)"),
    ("02_ibge.py", "IBGE domicílios/PIB/população"),
    ("03_conectividade.py", "Índice conectividade municipal"),
    ("03_aggregate_caged_mun.py", "Agregar CAGED por ocupação × município × período"),
    ("04_merge_panel.py", "Merge painel final (exposure + conectividade + IPCA)"),
]


def main():
    skip_download = "--skip-download" in sys.argv
    skip_aggregate = "--skip-aggregate" in sys.argv

    print("=" * 60)
    print("ETAPA 3a — Pipeline Preparação Painel Município × Conectividade")
    print("=" * 60)

    t_total = time.time()
    resultados = []

    for script_name, descricao in SCRIPTS:
        if skip_download and script_name in ("01_anatel.py", "02_ibge.py"):
            print(f"\n  [SKIP] {script_name} ({descricao}) — --skip-download")
            resultados.append((script_name, "SKIP", 0))
            continue
        if skip_aggregate and script_name == "03_aggregate_caged_mun.py":
            print(f"\n  [SKIP] {script_name} ({descricao}) — --skip-aggregate")
            resultados.append((script_name, "SKIP", 0))
            continue

        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            print(f"\n  [SKIP] {script_name} — arquivo não encontrado")
            resultados.append((script_name, "SKIP", 0))
            continue

        print(f"\n{'─' * 60}")
        print(f"  Executando: {script_name} — {descricao}")
        print(f"{'─' * 60}")

        t0 = time.time()
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(SCRIPTS_DIR.parent.parent.parent),
        )
        elapsed = time.time() - t0
        status = "OK" if result.returncode == 0 else "ERRO"
        resultados.append((script_name, status, elapsed))
        print(f"\n  [{status}] {script_name} ({elapsed:.0f}s)")

        if result.returncode != 0:
            print(f"  Abortando pipeline.")
            break

    elapsed_total = time.time() - t_total
    print(f"\n{'=' * 60}")
    print("RESUMO — Etapa 3a")
    print("=" * 60)
    for script_name, status, elapsed in resultados:
        print(f"  [{status:>4}] {script_name:<35} {elapsed:>6.0f}s")
    print(f"\n  Tempo total: {elapsed_total:.0f}s ({elapsed_total/60:.1f} min)")


if __name__ == "__main__":
    main()
