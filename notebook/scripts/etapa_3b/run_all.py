"""
Runner: Executa scripts da Etapa 3b em sequência.
Uso: python notebook/scripts/etapa_3b/run_all.py
Requer: painel_caged_municipio_anatel.parquet (Etapa 3a).
"""

import sys
import subprocess
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SCRIPTS = [
    ("01_load_and_prepare.py", "Carregar e preparar painel"),
    ("02_balance_conectividade.py", "Balanço por conectividade"),
    ("03_did_by_subgroup.py", "DiD por subgrupo"),
    ("04_triple_did_main.py", "Triple-DiD principal"),
    ("05_event_study_by_connect.py", "Event study por conectividade"),
    ("06_robustness.py", "Robustez"),
]


def main():
    print("=" * 60)
    print("ETAPA 3b — Pipeline Triple-DiD")
    print("=" * 60)
    t0 = time.time()
    for name, desc in SCRIPTS:
        path = SCRIPTS_DIR / name
        if not path.exists():
            print(f"  [SKIP] {name}")
            continue
        print(f"\n--- {name}: {desc} ---")
        r = subprocess.run([sys.executable, str(path)], cwd=str(SCRIPTS_DIR.parent.parent.parent))
        if r.returncode != 0:
            print(f"  ERRO: {name}")
            break
    print(f"\nTempo total: {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
