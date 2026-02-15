"""
Script 05: Crosswalk CBO 2002 → ISCO-08 (dual: 2d principal + 4d robustez)
Entrada: data/processed/painel_caged_mensal.parquet, data/processed/ilo_exposure_clean.csv
Saída:   data/processed/painel_caged_crosswalk.parquet

═══════════════════════════════════════════════════════════════════════════
CONTEXTO METODOLÓGICO
═══════════════════════════════════════════════════════════════════════════
A CBO 2002 (Classificação Brasileira de Ocupações) foi construída com base
na ISCO-88 e na ISCO-08, compartilhando a mesma estrutura hierárquica:
  • 1 dígito (Grande Grupo)  — alinhamento perfeito com ISCO-08 Major Group
  • 2 dígitos (Subgrupo Principal) — bom alinhamento com ISCO-08 Sub-major Group
  • 3 dígitos (Subgrupo) — alinhamento parcial com ISCO-08 Minor Group
  • 4 dígitos (Família) — divergência significativa com ISCO-08 Unit Group

NOTA: A tabela Muendler (cbo-isco-conc.csv) mapeia CBO *1994* → ISCO-88,
NÃO a CBO 2002 usada no CAGED. Portanto, o match 4d via Muendler é limitado
e serve apenas como fonte auxiliar.

ESTRATÉGIA
═══════════════════════════════════════════════════════════════════════════
PARTE A (Principal — 2 dígitos):
  CBO 2d → ISCO-08 2d (direto) → fallback CBO 1d → ISCO-08 Major Group

PARTE B (Robustez — 4 dígitos, fallback hierárquico em 6 níveis):
  Nível 1: CBO 4d = ISCO-08 4d  (match direto, ~28%)
  Nível 2: CBO 4d = ISCO-88 4d → ISCO-08 4d via tabela de correspondência (~+9%)
  Nível 3: CBO 3d = ISCO-08 3d → média do Minor Group (~+15%)
  Nível 4: CBO 3d = ISCO-88 3d → ISCO-08 3d via correspondência (~+5%)
  Nível 5: CBO 2d = ISCO-08 2d → média do Sub-major Group (= spec principal)
  Nível 6: CBO 1d = ISCO-08 1d → média do Major Group (sempre funciona)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import *


def log(msg):
    print(msg, flush=True)


# ─────────────────────────────────────────────────────────────────────────
# Funções auxiliares
# ─────────────────────────────────────────────────────────────────────────

def carregar_ilo():
    """Carregar índice ILO processado na Etapa 1a."""
    if not ILO_FILE.exists():
        log(f"ERRO: {ILO_FILE} não encontrado! Execute a Etapa 1a primeiro.")
        sys.exit(1)

    df_ilo = pd.read_csv(ILO_FILE)
    df_ilo['isco_08_str'] = df_ilo['isco_08'].astype(str).str.zfill(4)
    log(f"Índice ILO carregado: {len(df_ilo)} ocupações ISCO-08")
    log(f"  Score range: [{df_ilo['exposure_score'].min():.3f}, {df_ilo['exposure_score'].max():.3f}]")
    return df_ilo


def carregar_correspondencia_isco():
    """
    Carregar tabela de correspondência ISCO-08 ↔ ISCO-88 (arquivo local).
    Retorna dict ISCO-88 4d → lista de ISCO-08 4d.
    """
    if not ISCO_08_88_FILE.exists():
        log(f"AVISO: {ISCO_08_88_FILE} não encontrado.")
        return {}, {}

    df = pd.read_excel(ISCO_08_88_FILE, sheet_name='ISCO-08 to 88')
    df['isco08_4d'] = df['ISCO-08 code'].astype(str).str.strip().str.zfill(4)
    df['isco88_4d'] = df['ISCO-88 code'].astype(str).str.strip().str.zfill(4)

    # ISCO-88 4d → lista de ISCO-08 4d (muitos-para-muitos)
    isco88_to_08 = df.groupby('isco88_4d')['isco08_4d'].apply(list).to_dict()

    # ISCO-88 3d → lista de ISCO-08 3d (agregação por 3 dígitos)
    df['isco88_3d'] = df['isco88_4d'].str[:3]
    df['isco08_3d'] = df['isco08_4d'].str[:3]
    isco88_3d_to_08_3d = df.groupby('isco88_3d')['isco08_3d'].apply(
        lambda x: list(set(x))
    ).to_dict()

    log(f"  Correspondência ISCO carregada: {len(df)} mapeamentos")
    log(f"    ISCO-88 4d → ISCO-08: {len(isco88_to_08)} códigos")
    log(f"    ISCO-88 3d → ISCO-08 3d: {len(isco88_3d_to_08_3d)} grupos")

    return isco88_to_08, isco88_3d_to_08_3d


def construir_dicts_ilo(df_ilo):
    """Construir dicionários de lookup ILO em múltiplos níveis."""
    codes = df_ilo['isco_08_str']
    scores = df_ilo['exposure_score']

    # 4d: score exato por unit group
    ilo_4d = df_ilo.groupby('isco_08_str')['exposure_score'].mean().to_dict()

    # 3d: média do minor group
    ilo_3d = df_ilo.assign(g=codes.str[:3]).groupby('g')['exposure_score'].mean().to_dict()

    # 2d: média do sub-major group
    ilo_2d = df_ilo.assign(g=codes.str[:2]).groupby('g')['exposure_score'].mean().to_dict()

    # 1d: média do major group
    ilo_1d = df_ilo.assign(g=codes.str[:1]).groupby('g')['exposure_score'].mean().to_dict()

    log(f"  Dicts ILO construídos: 4d={len(ilo_4d)}, 3d={len(ilo_3d)}, "
        f"2d={len(ilo_2d)}, 1d={len(ilo_1d)}")

    return ilo_4d, ilo_3d, ilo_2d, ilo_1d


# ─────────────────────────────────────────────────────────────────────────
# PARTE A: Crosswalk 2 dígitos (PRINCIPAL)
# ─────────────────────────────────────────────────────────────────────────

def crosswalk_2d(painel, df_ilo, ilo_2d, ilo_1d):
    """
    Match a 2 dígitos com fallback a 1 dígito.

    A CBO 2002 e a ISCO-08 compartilham os 9 major groups (1 dígito),
    mas NEM TODOS os sub-major groups (2 dígitos) coincidem.
    Ex: CBO 78 (produção industrial) não existe na ISCO-08.

    Estratégia: 2d direto → fallback 1d (média do major group).
    """
    log(f"\n{'=' * 60}")
    log(f"PARTE A: Crosswalk 2 dígitos (PRINCIPAL)")
    log(f"{'=' * 60}")

    # Match 2d direto
    painel['exposure_score_2d'] = painel['cbo_2d'].map(ilo_2d)
    painel['match_level_2d'] = np.where(painel['exposure_score_2d'].notna(), '2-digit', None)

    n_2d = painel['exposure_score_2d'].notna().sum()
    log(f"\n  Match 2d direto: {n_2d:,} / {len(painel):,} ({n_2d/len(painel):.1%})")

    # CBOs sem match 2d
    sem_match_2d = sorted(painel[painel['exposure_score_2d'].isna()]['cbo_2d'].unique())
    if sem_match_2d:
        log(f"  CBO 2d sem match ISCO-08 2d: {sem_match_2d}")

    # Fallback a 1d para linhas sem match 2d
    mask_na = painel['exposure_score_2d'].isna()
    if mask_na.any():
        cbo_1d = painel.loc[mask_na, 'cbo_4d'].str[:1]
        painel.loc[mask_na, 'exposure_score_2d'] = cbo_1d.map(ilo_1d).values
        painel.loc[mask_na, 'match_level_2d'] = '1-digit (fallback)'

        n_1d = painel.loc[mask_na, 'exposure_score_2d'].notna().sum()
        log(f"  Fallback 1d: {n_1d:,} linhas adicionais")

    # Reportar CBOs sem match em nenhum nível
    sem_match = painel[painel['exposure_score_2d'].isna()]['cbo_2d'].unique()
    if len(sem_match) > 0:
        log(f"  SEM MATCH (nenhum nível): {sorted(sem_match)}")

    coverage = painel['exposure_score_2d'].notna().mean()
    log(f"\n  COBERTURA FINAL 2d: {coverage:.1%}")

    # Distribuição por match level
    log(f"  Match levels:")
    for level, count in painel['match_level_2d'].value_counts().items():
        log(f"    {level}: {count:,} ({count/len(painel):.1%})")

    # Score principal = score 2d
    painel['exposure_score'] = painel['exposure_score_2d']

    # Top/Bottom
    log(f"\n  Top 5 CBO 2d mais expostos:")
    top = painel.groupby('cbo_2d')['exposure_score_2d'].first().nlargest(5)
    for cbo, score in top.items():
        nome = GRANDES_GRUPOS_CBO.get(cbo[0], '')
        log(f"    CBO {cbo}: {score:.3f}  ({nome})")

    log(f"\n  Bottom 5 CBO 2d menos expostos:")
    bot = painel.groupby('cbo_2d')['exposure_score_2d'].first().nsmallest(5)
    for cbo, score in bot.items():
        nome = GRANDES_GRUPOS_CBO.get(cbo[0], '')
        log(f"    CBO {cbo}: {score:.3f}  ({nome})")

    return painel


# ─────────────────────────────────────────────────────────────────────────
# PARTE B: Crosswalk 4 dígitos (ROBUSTEZ) — fallback hierárquico 6 níveis
# ─────────────────────────────────────────────────────────────────────────

def crosswalk_4d(painel, df_ilo, ilo_4d, ilo_3d, ilo_2d, ilo_1d,
                 isco88_to_08, isco88_3d_to_08_3d):
    """
    Robustez a 4 dígitos com fallback hierárquico em 6 níveis.

    Usa a estrutura compartilhada entre CBO 2002 e ISCO-08/ISCO-88,
    mais a tabela de correspondência oficial ISCO-08 ↔ ISCO-88.
    """
    log(f"\n{'=' * 60}")
    log(f"PARTE B: Crosswalk 4 dígitos (ROBUSTEZ)")
    log(f"{'=' * 60}")

    cbos_unicos = sorted(painel['cbo_4d'].unique())
    log(f"  CBOs 4d únicos no painel: {len(cbos_unicos)}")

    # --- Construir score 4d para cada CBO 4d ---
    cbo_score_4d = {}
    cbo_match_level = {}

    # Contadores por nível
    counts = {
        'N1_isco08_4d': 0,
        'N2_via_isco88_4d': 0,
        'N3_isco08_3d': 0,
        'N4_via_isco88_3d': 0,
        'N5_isco08_2d': 0,
        'N6_isco08_1d': 0,
        'sem_match': 0,
    }

    for cbo in cbos_unicos:
        score = None
        level = None

        # ── Nível 1: CBO 4d = ISCO-08 4d (match direto) ──
        if cbo in ilo_4d:
            score = ilo_4d[cbo]
            level = 'N1: ISCO-08 4d direto'
            counts['N1_isco08_4d'] += 1

        # ── Nível 2: CBO 4d = ISCO-88 4d → ISCO-08 via correspondência ──
        if score is None and cbo in isco88_to_08:
            isco08_candidates = isco88_to_08[cbo]
            # Média dos scores dos candidatos ISCO-08 presentes no ILO
            scores_cand = [ilo_4d[c] for c in isco08_candidates if c in ilo_4d]
            if scores_cand:
                score = np.mean(scores_cand)
                level = 'N2: via ISCO-88→08 4d'
                counts['N2_via_isco88_4d'] += 1

        # ── Nível 3: CBO 3d = ISCO-08 3d (média do Minor Group) ──
        if score is None:
            cbo_3d = cbo[:3]
            if cbo_3d in ilo_3d:
                score = ilo_3d[cbo_3d]
                level = 'N3: ISCO-08 3d'
                counts['N3_isco08_3d'] += 1

        # ── Nível 4: CBO 3d = ISCO-88 3d → ISCO-08 3d via correspondência ──
        if score is None:
            cbo_3d = cbo[:3]
            if cbo_3d in isco88_3d_to_08_3d:
                isco08_3d_candidates = isco88_3d_to_08_3d[cbo_3d]
                scores_cand = [ilo_3d[c] for c in isco08_3d_candidates if c in ilo_3d]
                if scores_cand:
                    score = np.mean(scores_cand)
                    level = 'N4: via ISCO-88→08 3d'
                    counts['N4_via_isco88_3d'] += 1

        # ── Nível 5: CBO 2d = ISCO-08 2d (média do Sub-major Group) ──
        if score is None:
            cbo_2d = cbo[:2]
            if cbo_2d in ilo_2d:
                score = ilo_2d[cbo_2d]
                level = 'N5: ISCO-08 2d'
                counts['N5_isco08_2d'] += 1

        # ── Nível 6: CBO 1d = ISCO-08 1d (média do Major Group) ──
        if score is None:
            cbo_1d = cbo[:1]
            if cbo_1d in ilo_1d:
                score = ilo_1d[cbo_1d]
                level = 'N6: ISCO-08 1d'
                counts['N6_isco08_1d'] += 1

        if score is not None:
            cbo_score_4d[cbo] = score
            cbo_match_level[cbo] = level
        else:
            counts['sem_match'] += 1
            cbo_match_level[cbo] = 'sem match'

    # ── Reportar resultados ──
    log(f"\n  Fallback hierárquico — distribuição por nível:")
    total = len(cbos_unicos)
    log(f"    {'Nível':<30} {'Ocup':>6} {'%':>8}")
    log(f"    {'-'*46}")
    log(f"    {'N1: ISCO-08 4d direto':<30} {counts['N1_isco08_4d']:>6} "
        f"{counts['N1_isco08_4d']/total:>8.1%}")
    log(f"    {'N2: via ISCO-88→08 4d':<30} {counts['N2_via_isco88_4d']:>6} "
        f"{counts['N2_via_isco88_4d']/total:>8.1%}")
    log(f"    {'N3: ISCO-08 3d':<30} {counts['N3_isco08_3d']:>6} "
        f"{counts['N3_isco08_3d']/total:>8.1%}")
    log(f"    {'N4: via ISCO-88→08 3d':<30} {counts['N4_via_isco88_3d']:>6} "
        f"{counts['N4_via_isco88_3d']/total:>8.1%}")
    log(f"    {'N5: ISCO-08 2d':<30} {counts['N5_isco08_2d']:>6} "
        f"{counts['N5_isco08_2d']/total:>8.1%}")
    log(f"    {'N6: ISCO-08 1d':<30} {counts['N6_isco08_1d']:>6} "
        f"{counts['N6_isco08_1d']/total:>8.1%}")
    log(f"    {'Sem match':<30} {counts['sem_match']:>6} "
        f"{counts['sem_match']/total:>8.1%}")
    log(f"    {'-'*46}")

    matched = sum(v for k, v in counts.items() if k != 'sem_match')
    log(f"    {'TOTAL COM SCORE':<30} {matched:>6} {matched/total:>8.1%}")

    # Granularidade: % com informação genuinamente 4d (N1 + N2)
    n_4d_genuine = counts['N1_isco08_4d'] + counts['N2_via_isco88_4d']
    log(f"\n  Informação genuinamente 4d: {n_4d_genuine}/{total} ({n_4d_genuine/total:.1%})")
    log(f"  Informação ≤3d (fallback): {matched - n_4d_genuine}/{total} "
        f"({(matched - n_4d_genuine)/total:.1%})")

    # Aplicar ao painel
    painel['exposure_score_4d'] = painel['cbo_4d'].map(cbo_score_4d)
    painel['match_level_4d'] = painel['cbo_4d'].map(cbo_match_level)

    coverage_4d = painel['exposure_score_4d'].notna().mean()
    log(f"\n  COBERTURA FINAL 4d (linhas no painel): {coverage_4d:.1%}")

    # Distribuição de match levels no painel (ponderado por linhas)
    log(f"\n  Match levels (ponderados por linhas no painel):")
    for level, count in painel['match_level_4d'].value_counts().items():
        log(f"    {level}: {count:,} ({count/len(painel):.1%})")

    # CBOs sem match
    sem = sorted(painel[painel['exposure_score_4d'].isna()]['cbo_4d'].unique())
    if sem:
        log(f"\n  CBOs sem match 4d ({len(sem)}): {sem[:20]}{'...' if len(sem) > 20 else ''}")

    return painel


# ─────────────────────────────────────────────────────────────────────────
# Diagnóstico: concordância 2d vs 4d
# ─────────────────────────────────────────────────────────────────────────

def diagnostico_concordancia(painel):
    """Comparar scores 2d e 4d para verificar consistência."""
    log(f"\n{'=' * 60}")
    log(f"DIAGNÓSTICO: Concordância 2d vs 4d")
    log(f"{'=' * 60}")

    mask = painel['exposure_score_2d'].notna() & painel['exposure_score_4d'].notna()
    df = painel.loc[mask, ['cbo_4d', 'exposure_score_2d', 'exposure_score_4d']].drop_duplicates(
        subset='cbo_4d'
    )

    if len(df) < 2:
        log("  Insuficiente para calcular correlação.")
        return

    corr = df['exposure_score_2d'].corr(df['exposure_score_4d'])
    log(f"  Ocupações com ambos os scores: {len(df)}")
    log(f"  Correlação Pearson (2d vs 4d): {corr:.4f}")

    diff = (df['exposure_score_4d'] - df['exposure_score_2d']).abs()
    log(f"  Diferença absoluta: média={diff.mean():.4f}, max={diff.max():.4f}")

    # Quantos mudam de ranking significativamente?
    # (score 4d difere >0.05 do score 2d)
    n_diff = (diff > 0.05).sum()
    log(f"  Ocupações com |diff| > 0.05: {n_diff} ({n_diff/len(df):.1%})")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("ETAPA 2a.4a — Crosswalk CBO 2002 → ISCO-08")
    log("=" * 60)

    # Carregar dados
    painel = pd.read_parquet(PAINEL_MENSAL_FILE)
    log(f"Painel carregado: {len(painel):,} linhas, {painel['cbo_4d'].nunique()} CBOs 4d")

    df_ilo = carregar_ilo()

    # Construir dicts de lookup em múltiplos níveis
    log(f"\nConstruindo dicionários de lookup ILO...")
    ilo_4d, ilo_3d, ilo_2d, ilo_1d = construir_dicts_ilo(df_ilo)

    # Carregar tabela de correspondência ISCO-08 ↔ ISCO-88
    log(f"\nCarregando correspondência ISCO-08 ↔ ISCO-88...")
    isco88_to_08, isco88_3d_to_08_3d = carregar_correspondencia_isco()

    # Parte A: 2 dígitos (principal) com fallback 1d
    painel = crosswalk_2d(painel, df_ilo, ilo_2d, ilo_1d)

    # Parte B: 4 dígitos (robustez) com fallback hierárquico
    painel = crosswalk_4d(painel, df_ilo, ilo_4d, ilo_3d, ilo_2d, ilo_1d,
                          isco88_to_08, isco88_3d_to_08_3d)

    # Diagnóstico de concordância
    diagnostico_concordancia(painel)

    # Salvar
    painel.to_parquet(PAINEL_CROSSWALK_FILE, index=False)
    size_mb = PAINEL_CROSSWALK_FILE.stat().st_size / 1e6
    log(f"\nSalvo: {PAINEL_CROSSWALK_FILE.name} ({size_mb:.1f} MB)")
    log(f"Colunas: {list(painel.columns)}")

    return painel


if __name__ == "__main__":
    painel = main()
