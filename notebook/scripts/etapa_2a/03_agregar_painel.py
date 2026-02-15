"""
Script 03: Agregar microdados CAGED em painel mensal por ocupação
Entrada: data/raw/caged_{ano}.parquet
Saída:   data/processed/painel_caged_mensal.parquet

Processa ano a ano para evitar OOM, agrega por CBO 4 dígitos × mês.
OTIMIZADO: evita lambdas no groupby (que são ~100x mais lentos).
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import *


def log(msg):
    """Print com flush imediato para feedback em tempo real."""
    print(msg, flush=True)


def processar_ano(ano):
    """Carrega um ano e retorna painéis de admissões e desligamentos."""
    t0 = time.time()
    df = pd.read_parquet(DATA_RAW / f"caged_{ano}.parquet")
    log(f"  [{ano}] Carregado: {len(df):,} registros ({time.time()-t0:.0f}s)")

    # ── CBO 4 dígitos ──
    df['cbo_2002'] = df['cbo_2002'].astype(str).str.strip()
    df['cbo_4d'] = df['cbo_2002'].str[:4]

    # Remover CBO inválidos
    cbo_invalidos = ['0000', 'nan', '', 'None']
    n_antes = len(df)
    df = df[~df['cbo_4d'].isin(cbo_invalidos)]
    df = df[df['cbo_4d'].str.len() == 4]
    df = df[df['cbo_4d'].str.isdigit()]
    n_depois = len(df)
    log(f"  [{ano}] CBOs válidos: {n_depois:,} / {n_antes:,} ({n_depois/n_antes:.1%})")

    # ── PRÉ-COMPUTAR flags booleanas (VETORIZADO — muito mais rápido que lambda) ──
    df['is_mulher'] = (df['sexo'].astype(str) == '2').astype(float)
    df['is_superior'] = df['grau_instrucao'].astype(str).isin(
        ['9', '10', '11', '12', '13']).astype(float)

    # ── Separar admissões e desligamentos ──
    df_adm = df[df['saldo_movimentacao'] == 1]
    df_des = df[df['saldo_movimentacao'] == -1]
    log(f"  [{ano}] Admissões: {len(df_adm):,} | Desligamentos: {len(df_des):,}")

    # ── Agregar admissões ──
    # NOTA: 'median' removida do agg para performance (~10x mais rápido).
    # Calculada separadamente depois via quantile.
    t1 = time.time()
    painel_adm = df_adm.groupby(['cbo_4d', 'ano', 'mes']).agg(
        admissoes=('saldo_movimentacao', 'count'),
        salario_medio_adm=('salario_mensal', 'mean'),
        idade_media_adm=('idade', 'mean'),
        pct_mulher_adm=('is_mulher', 'mean'),
        pct_superior_adm=('is_superior', 'mean'),
    ).reset_index()
    log(f"  [{ano}] Admissões agregadas: {len(painel_adm):,} ({time.time()-t1:.0f}s)")

    # Mediana salarial (separada — mais rápida que dentro do agg)
    t1 = time.time()
    mediana = df_adm.groupby(['cbo_4d', 'ano', 'mes'])['salario_mensal'].median().reset_index()
    mediana.columns = ['cbo_4d', 'ano', 'mes', 'salario_mediano_adm']
    painel_adm = painel_adm.merge(mediana, on=['cbo_4d', 'ano', 'mes'], how='left')
    log(f"  [{ano}] Mediana salarial: ({time.time()-t1:.0f}s)")

    # ── Agregar desligamentos ──
    t1 = time.time()
    painel_des = df_des.groupby(['cbo_4d', 'ano', 'mes']).agg(
        desligamentos=('saldo_movimentacao', 'count'),
        salario_medio_desl=('salario_mensal', 'mean'),
    ).reset_index()
    log(f"  [{ano}] Desligamentos agregados: {len(painel_des):,} ({time.time()-t1:.0f}s)")

    elapsed = time.time() - t0
    log(f"  [{ano}] Total: {elapsed:.0f}s")

    # Liberar memória
    del df, df_adm, df_des

    return painel_adm, painel_des


def main():
    print("=" * 60)
    print("ETAPA 2a.3a — Agregação: Microdados → Painel Mensal")
    print("=" * 60)

    t_total = time.time()

    # ── Processar ano a ano ──
    paineis_adm = []
    paineis_des = []

    for ano in range(ANO_INICIO, ANO_FIM + 1):
        p_adm, p_des = processar_ano(ano)
        paineis_adm.append(p_adm)
        paineis_des.append(p_des)

    # ── Concatenar os painéis anuais (pequenos, ~7k linhas cada) ──
    painel_adm = pd.concat(paineis_adm, ignore_index=True)
    painel_des = pd.concat(paineis_des, ignore_index=True)
    print(f"\nPainel admissões (total): {len(painel_adm):,}")
    print(f"Painel desligamentos (total): {len(painel_des):,}")

    # ── Merge admissões + desligamentos ──
    painel = painel_adm.merge(
        painel_des,
        on=['cbo_4d', 'ano', 'mes'],
        how='outer'
    ).fillna(0)

    # ── Variáveis derivadas ──
    painel['saldo'] = painel['admissoes'] - painel['desligamentos']
    painel['n_movimentacoes'] = painel['admissoes'] + painel['desligamentos']

    # Temporal
    painel['periodo'] = (painel['ano'].astype(int).astype(str) + '-' +
                         painel['mes'].astype(int).astype(str).str.zfill(2))
    painel['periodo_num'] = painel['ano'].astype(int) * 100 + painel['mes'].astype(int)
    painel['post'] = (painel['periodo_num'] >= ANO_TRATAMENTO * 100 + MES_TRATAMENTO).astype(int)

    # Log-transformações
    painel['ln_admissoes'] = np.log(painel['admissoes'] + 1)
    painel['ln_desligamentos'] = np.log(painel['desligamentos'] + 1)
    painel['ln_salario_adm'] = np.log(painel['salario_medio_adm'].clip(lower=1))

    # CBO 2 dígitos
    painel['cbo_2d'] = painel['cbo_4d'].str[:2]

    # ── Salvar ──
    painel.to_parquet(PAINEL_MENSAL_FILE, index=False)
    size_mb = PAINEL_MENSAL_FILE.stat().st_size / 1e6

    elapsed_total = time.time() - t_total

    # ── Resumo ──
    print(f"\n{'=' * 60}")
    print(f"PAINEL MENSAL CONSTRUÍDO")
    print(f"{'=' * 60}")
    print(f"  Linhas: {len(painel):,} (ocupação × mês)")
    print(f"  Ocupações CBO 4d: {painel['cbo_4d'].nunique()}")
    print(f"  Períodos: {painel['periodo'].nunique()} meses")
    print(f"  Períodos pré:  {painel[painel['post']==0]['periodo'].nunique()}")
    print(f"  Períodos pós:  {painel[painel['post']==1]['periodo'].nunique()}")
    print(f"  Colunas: {list(painel.columns)}")
    print(f"  Salvo: {PAINEL_MENSAL_FILE.name} ({size_mb:.1f} MB)")
    print(f"  Tempo total: {elapsed_total:.0f}s ({elapsed_total/60:.1f} min)")

    return painel


if __name__ == "__main__":
    painel = main()
