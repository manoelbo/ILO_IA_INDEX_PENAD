"""
Script 02: Verificar dados CAGED (CHECKPOINT)
Entrada: data/raw/caged_{ano}.parquet
Saída:   (prints de verificação — nenhum arquivo)

Carrega ano a ano para evitar OOM.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import *


def main():
    print("=" * 60)
    print("CHECKPOINT — Microdados CAGED")
    print("=" * 60)

    # ── Verificar arquivos ──
    total_registros = 0
    registros_por_ano = {}

    for ano in range(ANO_INICIO, ANO_FIM + 1):
        p = DATA_RAW / f"caged_{ano}.parquet"
        if not p.exists():
            print(f"  ERRO: {p.name} não encontrado!")
            return
        size_mb = p.stat().st_size / 1e6
        df = pd.read_parquet(p)
        registros_por_ano[ano] = len(df)
        total_registros += len(df)
        print(f"  {ano}: {len(df):,} registros ({size_mb:.0f} MB)")

        # Liberar memória
        del df

    print(f"\n  Total: {total_registros:,} registros")

    # ── Verificação detalhada ano a ano ──
    print(f"\n--- Verificação detalhada ---")

    todas_colunas = None
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        df = pd.read_parquet(DATA_RAW / f"caged_{ano}.parquet")
        print(f"\n  [{ano}]")

        # Colunas
        if todas_colunas is None:
            todas_colunas = set(df.columns)
            print(f"    Colunas: {list(df.columns)}")
        else:
            if set(df.columns) != todas_colunas:
                print(f"    AVISO: Colunas diferentes! {set(df.columns) - todas_colunas}")

        # Meses cobertos
        meses = sorted(df['mes'].dropna().unique())
        print(f"    Meses: {len(meses)} — {list(meses)}")
        if len(meses) != 12:
            print(f"    WARNING: Esperado 12 meses, encontrado {len(meses)}")

        # Preenchimento
        for col in ['cbo_2002', 'saldo_movimentacao', 'salario_mensal', 'idade', 'sexo']:
            if col in df.columns:
                n_valid = df[col].notna().sum()
                pct = n_valid / len(df) * 100
                flag = "" if pct > 95 else " WARNING" if pct > 80 else " CRÍTICO"
                print(f"    {col}: {pct:.1f}%{flag}")

        # Saldo movimentação
        if 'saldo_movimentacao' in df.columns:
            saldo_vals = df['saldo_movimentacao'].value_counts()
            for val, count in saldo_vals.items():
                print(f"    saldo={val}: {count:,} ({count/len(df):.1%})")

        # CBO
        if 'cbo_2002' in df.columns:
            n_cbo = df['cbo_2002'].nunique()
            sample = df['cbo_2002'].dropna().astype(str).head(5).tolist()
            print(f"    CBOs únicos: {n_cbo:,}, amostra: {sample}")

        del df

    print(f"\n{'=' * 60}")
    print(f"CHECKPOINT CONCLUÍDO")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
