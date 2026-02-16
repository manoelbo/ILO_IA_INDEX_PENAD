# ETAPA 2b — Análise Difference-in-Differences: IA Generativa e Emprego Formal no Brasil

## Planejamento Detalhado do Notebook

**Dissertação:** Inteligência Artificial Generativa e o Mercado de Trabalho Brasileiro: Uma Análise de Exposição Ocupacional e seus Efeitos Distributivos.

**Aluno:** Manoel Brasil Orlandi

**Objetivo deste notebook:** Estimar o efeito causal do lançamento da IA generativa (ChatGPT, novembro/2022) sobre o mercado de trabalho formal brasileiro, usando variação na exposição ocupacional à IA como fonte de identificação. Implementa um design Difference-in-Differences (DiD) com dados do CAGED (2021–2025) e o índice de exposição da OIT.

**Estratégia de crosswalk:** Análise principal a **2 dígitos** ISCO-08 (match por Sub-major Group com fallback hierárquico a Major Group), com robustez a **4 dígitos** via correspondência ISCO-88↔ISCO-08 + fallback hierárquico em 6 níveis. Ver `abordagens_crosswalk.md` para justificativa completa.

**Dados do Notebook 2a (valores reais):** 629 ocupações CBO 4d × 54 meses (Jan/2021–Jun/2025) = 32.988 observações. Cobertura crosswalk: 100% (2d e 4d). Correlação 2d vs 4d: 0,9150. Concordância binária: 93,1%. Tratamento 2d: 20,3% (128 CBOs), 4d: 21,3% (134 CBOs).

**Pergunta de pesquisa:** Após o lançamento do ChatGPT, ocupações mais expostas à IA generativa tiveram mudanças diferenciais em contratações, demissões ou salários de admissão, em comparação com ocupações menos expostas?

**Input:** `data/output/painel_caged_did_ready.parquet` (produzido no Notebook 2a)

---

## Referências Metodológicas

- Hui, X., Reshef, O. & Zhou, L. (2024). *The Short-Term Effects of Generative AI on Employment*. Organization Science, 35(6).
- Cunningham, S. (2021). *Causal Inference: The Mixtape*. Yale University Press. Cap. 9 (Difference-in-Differences).
- Callaway, B. & Sant'Anna, P. (2021). *DiD with multiple time periods*. Journal of Econometrics, 225(2), 200–230.
- Sun, L. & Abraham, S. (2021). *Estimating dynamic treatment effects in event studies*. Journal of Econometrics, 225(2), 175–199.
- de Chaisemartin, C. & D'Haultfœuille, X. (2020). *Two-Way Fixed Effects Estimators with Heterogeneous Treatment Effects*. AER, 110(9).
- Goodman-Bacon, A. (2021). *Difference-in-differences with variation in treatment timing*. Journal of Econometrics, 225(2).
- Gmyrek, P., Berg, J. & Cappelli, D. (2025). ILO Working Paper 140.

---

## Estratégia de Identificação

### Design

| Elemento | Definição |
|----------|-----------|
| **Unidade de análise** | Ocupação CBO × mês (2 dígitos na espec. principal; 4 dígitos na robustez) |
| **Tratamento** | Ocupações com alta exposição à IA (top 20% do índice ILO via `exposure_score_2d`) |
| **Controle** | Ocupações com baixa exposição (bottom 80%) |
| **Evento** | Lançamento do ChatGPT (30/nov/2022) |
| **Pré-tratamento** | Jan/2021 — Nov/2022 (23 meses) |
| **Pós-tratamento** | Dez/2022 — Jun/2025 (31 meses) |
| **Outcomes** | Admissões, desligamentos, saldo, salário médio de admissão |
| **Efeitos fixos** | Ocupação (CBO 4d) + período (ano-mês) |
| **Erros padrão** | Clusterizados por ocupação (CBO 4d) |

### Hipótese de identificação

A hipótese central é que, **na ausência do lançamento do ChatGPT**, ocupações de alta e baixa exposição teriam seguido tendências paralelas em suas métricas de emprego formal. Testamos essa hipótese com:

1. Inspeção visual de tendências pré-tratamento
2. Teste formal de coeficientes pré-tratamento no event study
3. Testes placebo (tratamento fictício antes do evento real)

### Por que TWFE é válido aqui

O design tem **tratamento sharp** (todos tratados no mesmo momento — Nov/2022), sem adoção escalonada. Nesse caso, os problemas de heterogeneidade identificados por Goodman-Bacon (2021) e de Chaisemartin & D'Haultfœuille (2020) **não se aplicam**, e o TWFE produz estimativas consistentes do ATT médio. Usamos Callaway-Sant'Anna apenas como robustez.

> **Referência Mixtape, Cap. 9:** "When treatment timing is the same for all treated units, TWFE reduces to the simple 2×2 DiD and produces unbiased estimates of the average treatment effect on the treated."

---

## Outcomes

| Outcome | Variável | Transformação | Interpretação |
|---------|----------|---------------|---------------|
| Contratações | `admissoes` | `ln_admissoes = log(admissoes + 1)` | Fluxo de novas contratações |
| Demissões | `desligamentos` | `ln_desligamentos = log(desligamentos + 1)` | Fluxo de demissões |
| Saldo líquido | `saldo` | Em nível (pode ser negativo) | Criação líquida de empregos |
| Salário de admissão | `salario_medio_adm` | `ln_salario_adm = log(salario_medio_adm)` | Poder de barganha / demanda |
| Salário normalizado | `salario_sm` | `ln_salario_sm = log(salario_sm)` | Controlando inflação |

> **Nota — Tratamento de outliers salariais:** O Notebook 2a identificou um outlier em Jun/2025 (salário médio agregado ~R$11.519 vs ~R$4.000 nos meses anteriores), causado por poucas células com salários extremos (0,01% das admissões). Para evitar distorção nos modelos com salário como controle, aplicar **winsorização nos percentis 1% e 99%** de `salario_medio_adm` antes da estimação. Isso preserva todas as observações sem gerar viés de seleção. A winsorização deve ser feita neste notebook (2b), mantendo o dataset de preparação (2a) intacto.

---

## Estrutura do Notebook

---

### 1. Configuração do ambiente

**Markdown:** Importar bibliotecas, carregar dados, definir parâmetros de estimação.

```python
# Etapa 2b.1 — Configuração do ambiente

import warnings
import pandas as pd
import numpy as np
import pyfixest as pf
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
DATA_OUTPUT    = Path("data/output")
OUTPUTS_TABLES = Path("outputs/tables")
OUTPUTS_FIGURES = Path("outputs/figures")
OUTPUTS_LOGS   = Path("outputs/logs")

for d in [OUTPUTS_TABLES, OUTPUTS_FIGURES, OUTPUTS_LOGS]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Parâmetros de estimação
# ---------------------------------------------------------------------------
TREATMENT_VAR    = 'alta_exp'          # Especificação principal (top 20%, 2d)
TREATMENT_VAR_4D = 'alta_exp_4d'       # Robustez (top 20%, 4d)
CLUSTER_VAR      = 'cbo_4d'            # Cluster de erros padrão
VCOV_SPEC        = {'CRV1': 'cbo_4d'}  # Cluster-robust (CRV1)
REFERENCE_PERIOD = -1                  # Mês t=-1 como referência no event study
ALPHA            = 0.05                # Nível de significância

# Scores contínuos para tratamento contínuo
EXPOSURE_SCORE_MAIN = 'exposure_score_2d'  # Principal (Sub-major Group + fallback 1d)
EXPOSURE_SCORE_4D   = 'exposure_score_4d'  # Robustez (fallback hierárquico 6 níveis via ISCO-88↔08)

# Outcomes principais
OUTCOMES = {
    'ln_admissoes':       'Log(Admissões)',
    'ln_desligamentos':   'Log(Desligamentos)',
    'saldo':              'Saldo Líquido',
    'ln_salario_adm':     'Log(Salário Admissão)',
}

# Outcomes secundários
OUTCOMES_SECONDARY = {
    'ln_salario_sm':      'Log(Salário em SM)',
}

# ---------------------------------------------------------------------------
# Estilo de gráficos
# ---------------------------------------------------------------------------
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("Set2")
plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'figure.titlesize': 14,
    'font.family': 'serif',
    'figure.dpi': 150,
})

COLORS = {
    'pre': '#1f77b4',    # Azul (pré-tratamento)
    'post': '#d62728',   # Vermelho (pós-tratamento)
    'ci': '#cccccc',     # Cinza (IC)
    'treated': '#ff7f0e', # Laranja (tratamento)
    'control': '#2ca02c', # Verde (controle)
}

print("Configuração carregada.")
```

---

### 2. Carregar e explorar dados

**Markdown:** Carregar o painel produzido no Notebook 2a e fazer verificações iniciais.

```python
# Etapa 2b.2 — Carregar e explorar dados

# ---------------------------------------------------------------------------
# Carregar painel
# ---------------------------------------------------------------------------
painel_path = DATA_OUTPUT / "painel_caged_did_ready.parquet"
df = pd.read_parquet(painel_path)

print(f"Painel carregado: {len(df):,} observações")
print(f"Ocupações: {df['cbo_4d'].nunique()}")
print(f"Períodos: {df['periodo'].nunique()} meses")
print(f"Período: {df['periodo'].min()} a {df['periodo'].max()}")
print(f"\nTratamento ({TREATMENT_VAR}):")
print(f"  Alta exposição: {df[TREATMENT_VAR].mean():.1%}")
print(f"  Pré: {df[df['post']==0].shape[0]:,} obs")
print(f"  Pós: {df[df['post']==1].shape[0]:,} obs")

# ---------------------------------------------------------------------------
# Winsorização de salários (outliers — ver nota no Notebook 2a)
# ---------------------------------------------------------------------------
from scipy.stats import mstats

for col_sal in ['salario_medio_adm', 'salario_sm']:
    if col_sal in df.columns:
        p1 = df[col_sal].quantile(0.01)
        p99 = df[col_sal].quantile(0.99)
        n_clip = ((df[col_sal] < p1) | (df[col_sal] > p99)).sum()
        df[col_sal] = df[col_sal].clip(lower=p1, upper=p99)
        print(f"\nWinsorização {col_sal}: [{p1:.2f}, {p99:.2f}], {n_clip} obs clipped ({100*n_clip/len(df):.1f}%)")

# Recalcular logs após winsorização
df['ln_salario_adm'] = np.log(df['salario_medio_adm'])
df['ln_salario_sm'] = np.log(df['salario_sm'])

print("Logs salariais recalculados após winsorização.")

# ---------------------------------------------------------------------------
# Estatísticas descritivas dos outcomes
# ---------------------------------------------------------------------------
print("\nEstatísticas descritivas dos outcomes:")
for var, label in {**OUTCOMES, **OUTCOMES_SECONDARY}.items():
    if var in df.columns:
        print(f"\n  {label} ({var}):")
        print(f"    N: {df[var].notna().sum():,}")
        print(f"    Média: {df[var].mean():.3f}")
        print(f"    Std: {df[var].std():.3f}")
        print(f"    Min: {df[var].min():.3f}, Max: {df[var].max():.3f}")
```

---

### 3. Tabela de balanço (balance table)

**Markdown:**

Comparar características de ocupações tratadas vs. controle no período pré-tratamento. Critério de balanço: |diferença normalizada| < 0,25.

> **Ref. Mixtape, Cap. 9:** "A balance table compares the pre-treatment characteristics of the treatment and control groups. If these groups differ substantially, the parallel trends assumption may be less credible."

```python
# Etapa 2b.3 — Tabela de balanço

# ---------------------------------------------------------------------------
# Filtrar período pré-tratamento
# ---------------------------------------------------------------------------
df_pre = df[df['post'] == 0].copy()

# Agregar por ocupação (médias no pré)
ocup_pre = df_pre.groupby('cbo_4d').agg(
    exposure_score=('exposure_score_2d', 'first'),
    alta_exp=('alta_exp', 'first'),
    admissoes_media=('admissoes', 'mean'),
    desligamentos_media=('desligamentos', 'mean'),
    saldo_media=('saldo', 'mean'),
    salario_media=('salario_medio_adm', 'mean'),
    idade_media=('idade_media_adm', 'mean'),
    pct_mulher=('pct_mulher_adm', 'mean'),
    pct_superior=('pct_superior_adm', 'mean'),
    n_meses=('periodo', 'nunique'),
).reset_index()

# ---------------------------------------------------------------------------
# Calcular estatísticas de balanço
# ---------------------------------------------------------------------------
BALANCE_THRESHOLD = 0.25

covariates = {
    'admissoes_media': 'Admissões (média mensal)',
    'desligamentos_media': 'Desligamentos (média mensal)',
    'saldo_media': 'Saldo (média mensal)',
    'salario_media': 'Salário médio (R$)',
    'idade_media': 'Idade média',
    'pct_mulher': '% Mulheres',
    'pct_superior': '% Superior completo',
    'n_meses': 'Meses com dados',
}

results_balance = []
for var, label in covariates.items():
    treated = ocup_pre[ocup_pre['alta_exp'] == 1][var].dropna()
    control = ocup_pre[ocup_pre['alta_exp'] == 0][var].dropna()

    mean_t = treated.mean()
    mean_c = control.mean()
    diff = mean_t - mean_c

    # Diferença normalizada
    pooled_std = np.sqrt((treated.var() + control.var()) / 2)
    std_diff = diff / pooled_std if pooled_std > 0 else np.nan

    results_balance.append({
        'Variável': label,
        'Controle': mean_c,
        'Tratamento': mean_t,
        'Diferença': diff,
        'Diff. Normalizada': std_diff,
        'Balanceado': '✓' if abs(std_diff) < BALANCE_THRESHOLD else '⚠️'
    })

df_balance = pd.DataFrame(results_balance)
print("\nTabela de Balanço (Pré-Tratamento):")
print(df_balance.to_string(index=False))

# Salvar
df_balance.to_csv(OUTPUTS_TABLES / 'balance_table_pre.csv', index=False)
```

---

### 4. Tendências paralelas (inspeção visual)

**Markdown:**

Gráficos de evolução temporal das métricas de emprego para tratamento vs. controle. A hipótese de tendências paralelas exige que ambos os grupos sigam trajetórias semelhantes antes do evento (Nov/2022).

```python
# Etapa 2b.4 — Tendências paralelas (inspeção visual)

# ---------------------------------------------------------------------------
# Agregar séries temporais por grupo de tratamento
# ---------------------------------------------------------------------------
ts_grupo = df.groupby(['periodo_num', 'alta_exp']).agg(
    admissoes_total=('admissoes', 'sum'),
    desligamentos_total=('desligamentos', 'sum'),
    saldo_total=('saldo', 'sum'),
    salario_medio=('salario_medio_adm', 'mean'),
    n_ocupacoes=('cbo_4d', 'nunique'),
).reset_index()

# Normalizar por número de ocupações (média por ocupação)
for col in ['admissoes_total', 'desligamentos_total', 'saldo_total']:
    ts_grupo[f'{col}_per_ocup'] = ts_grupo[col] / ts_grupo['n_ocupacoes']

# Label de grupo
ts_grupo['grupo'] = ts_grupo['alta_exp'].map({0: 'Controle (Baixa Exp.)', 1: 'Tratamento (Alta Exp.)'})

# ---------------------------------------------------------------------------
# Gráficos de tendências paralelas
# ---------------------------------------------------------------------------
outcomes_plot = {
    'admissoes_total_per_ocup': 'Admissões médias por ocupação',
    'desligamentos_total_per_ocup': 'Desligamentos médios por ocupação',
    'saldo_total_per_ocup': 'Saldo médio por ocupação',
    'salario_medio': 'Salário médio de admissão (R$)',
}

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

evento_periodo = ANO_TRATAMENTO * 100 + MES_TRATAMENTO  # 202212

for i, (var, title) in enumerate(outcomes_plot.items()):
    ax = axes[i]
    for grupo in ['Controle (Baixa Exp.)', 'Tratamento (Alta Exp.)']:
        data = ts_grupo[ts_grupo['grupo'] == grupo]
        color = COLORS['control'] if 'Controle' in grupo else COLORS['treated']
        ax.plot(data['periodo_num'], data[var], label=grupo, color=color, linewidth=1.5)

    # Linha vertical no evento
    ax.axvline(x=evento_periodo, color='gray', linestyle='--', alpha=0.7, label='ChatGPT (Nov/2022)')

    ax.set_title(title)
    ax.set_xlabel('Período')
    ax.legend(fontsize=8)
    ax.tick_params(axis='x', rotation=45)

plt.suptitle('Tendências Paralelas: Tratamento vs. Controle', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUTS_FIGURES / 'parallel_trends_all_outcomes.png', dpi=150, bbox_inches='tight')
plt.show()

print("Gráficos salvos em outputs/figures/parallel_trends_all_outcomes.png")
```

---

### 5a. Estimação DiD principal

**Markdown:**

Estimação dos modelos DiD com complexidade crescente, seguindo a mesma progressão da Etapa 5 antiga (que usava PNAD):

| Modelo | Especificação | Descrição |
|--------|---------------|-----------|
| Model 1 | `y ~ post × alta_exp` | DiD básico (sem FE) |
| Model 2 | `y ~ post × alta_exp | cbo_4d + periodo` | Com efeitos fixos |
| Model 3 | `y ~ post × alta_exp + controles | cbo_4d + periodo` | **PRINCIPAL**: FE + controles (2d) |
| Model 4 | `y ~ post × exposure_score_2d + controles | cbo_4d + periodo` | Tratamento contínuo (2d) |
| Model 5 | `y ~ post × alta_exp_4d + controles | cbo_4d + periodo` | **ROBUSTEZ**: FE + controles (4d) |
| Model 6 | `y ~ post × exposure_score_4d + controles | cbo_4d + periodo` | Tratamento contínuo (4d) |

> **Nota — Estratégia dual de crosswalk:** Models 1–4 usam o score a 2 dígitos (match perfeito CBO↔ISCO-08). Models 5–6 replicam com o score a 4 dígitos (via CBO→ISCO-88→ISCO-08). Se os resultados forem consistentes entre as duas especificações, isso reforça a robustez. Ver `abordagens_crosswalk.md`.

> **Nota — Controles ao nível de ocupação:** Como o painel é ao nível ocupação × mês, os controles individuais usados na Etapa antiga (idade, sexo, raça) estão disponíveis como **médias das admissões** (ex: `idade_media_adm`, `pct_mulher_adm`). Esses controles capturam mudanças na composição demográfica dos contratados.

> **Nota — Efeitos fixos:** Os FE de ocupação (`cbo_4d`) absorvem diferenças permanentes entre ocupações. Os FE de período (`periodo`) absorvem choques macroeconômicos comuns a todas as ocupações (ex: variações sazonais, reformas trabalhistas).

```python
# Etapa 2b.5a — Estimação DiD principal

# ---------------------------------------------------------------------------
# Preparar dados para estimação
# ---------------------------------------------------------------------------
df_reg = df.copy()

# Garantir tipos numéricos
for col in ['admissoes', 'desligamentos', 'saldo', 'ln_admissoes',
            'ln_desligamentos', 'ln_salario_adm', 'salario_medio_adm',
            'idade_media_adm', 'pct_mulher_adm', 'pct_superior_adm',
            'post', 'alta_exp', 'exposure_score_2d', 'exposure_score_4d']:
    if col in df_reg.columns:
        df_reg[col] = pd.to_numeric(df_reg[col], errors='coerce')

# Criar interações DiD (se não existirem)
df_reg['post_alta'] = df_reg['post'] * df_reg['alta_exp']
df_reg['post_exposure_2d'] = df_reg['post'] * df_reg['exposure_score_2d']

# Robustez: 4 dígitos
df_reg['post_alta_4d'] = df_reg['post'] * df_reg['alta_exp_4d']
df_reg['post_exposure_4d'] = df_reg['post'] * df_reg['exposure_score_4d']

# Verificar variância dos outcomes
print("Variância dos outcomes:")
for var in OUTCOMES.keys():
    if var in df_reg.columns:
        v = df_reg[var].var()
        print(f"  {var}: {v:.4f} {'(OK)' if v > 0.001 else '(WARNING: variância muito baixa)'}")

# ---------------------------------------------------------------------------
# Função de estimação
# ---------------------------------------------------------------------------
def estimate_did(df, outcome, formula, label, vcov_spec=VCOV_SPEC):
    """Estima um modelo DiD e retorna resultados formatados."""
    try:
        model = pf.feols(formula, data=df, vcov=vcov_spec)
        # Extrair coeficiente da interação DiD
        coef_names = model.coefnames()
        # Buscar o coeficiente de interesse
        did_coef_name = [c for c in coef_names if 'post' in c.lower() and ('alta' in c.lower() or 'exposure' in c.lower())]
        if not did_coef_name:
            did_coef_name = [coef_names[0]]  # fallback

        coef = model.coef()[did_coef_name[0]]
        se = model.se()[did_coef_name[0]]
        pval = model.pvalue()[did_coef_name[0]]
        n_obs = model.nobs()
        n_clusters = model._N_clusters if hasattr(model, '_N_clusters') else None

        stars = '***' if pval < 0.01 else '**' if pval < 0.05 else '*' if pval < 0.10 else ''

        return {
            'model': label,
            'outcome': outcome,
            'coef': coef,
            'se': se,
            'p_value': pval,
            'stars': stars,
            'n_obs': n_obs,
            'n_clusters': n_clusters,
        }
    except Exception as e:
        print(f"  ERRO em {label}/{outcome}: {e}")
        return None

# ---------------------------------------------------------------------------
# Estimar 4 especificações para cada outcome
# ---------------------------------------------------------------------------
all_results = []

for outcome, label in OUTCOMES.items():
    if outcome not in df_reg.columns:
        print(f"SKIP: {outcome} não encontrado")
        continue

    print(f"\n{'='*40}")
    print(f"Outcome: {label} ({outcome})")
    print(f"{'='*40}")

    # Filtrar NaN no outcome
    df_out = df_reg[df_reg[outcome].notna()].copy()

    # Model 1: Basic DiD
    r1 = estimate_did(df_out, outcome,
        f"{outcome} ~ post_alta + post + alta_exp",
        "Model 1: Basic")

    # Model 2: FE
    r2 = estimate_did(df_out, outcome,
        f"{outcome} ~ post_alta | cbo_4d + periodo",
        "Model 2: FE")

    # Model 3: FE + Controls (PRINCIPAL)
    r3 = estimate_did(df_out, outcome,
        f"{outcome} ~ post_alta + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo",
        "Model 3: FE + Controls (MAIN)")

    # Model 4: Continuous treatment (2d)
    r4 = estimate_did(df_out, outcome,
        f"{outcome} ~ post_exposure_2d + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo",
        "Model 4: Continuous (2d)")

    # Model 5: FE + Controls (4d robustez)
    df_out_4d = df_out[df_out['exposure_score_4d'].notna()].copy()
    r5 = estimate_did(df_out_4d, outcome,
        f"{outcome} ~ post_alta_4d + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo",
        "Model 5: FE + Controls (4d)")

    # Model 6: Continuous treatment (4d)
    r6 = estimate_did(df_out_4d, outcome,
        f"{outcome} ~ post_exposure_4d + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo",
        "Model 6: Continuous (4d)")

    for r in [r1, r2, r3, r4, r5, r6]:
        if r:
            all_results.append(r)
            print(f"  {r['model']}: β={r['coef']:.4f}{r['stars']} (SE={r['se']:.4f}, p={r['p_value']:.3f}, N={r['n_obs']:,})")

# ---------------------------------------------------------------------------
# Consolidar resultados
# ---------------------------------------------------------------------------
df_results = pd.DataFrame(all_results)
df_results.to_csv(OUTPUTS_TABLES / 'did_main_results.csv', index=False)

print(f"\nResultados salvos em: {OUTPUTS_TABLES / 'did_main_results.csv'}")
```

---

### 5b. Verificar resultados DiD (CHECKPOINT)

```python
# Etapa 2b.5b — CHECKPOINT: Resultados DiD

print("=" * 60)
print("CHECKPOINT — Resultados DiD Principais")
print("=" * 60)

# Tabela formatada — PRINCIPAL (2d)
print("\nResultados Model 3 (FE + Controls, 2d — PRINCIPAL):")
main_results = df_results[df_results['model'] == 'Model 3: FE + Controls (MAIN)']
for _, row in main_results.iterrows():
    sig = "SIG" if row['p_value'] < ALPHA else "n.s."
    print(f"  {OUTCOMES.get(row['outcome'], row['outcome'])}: "
          f"β = {row['coef']:.4f}{row['stars']} "
          f"(SE = {row['se']:.4f}, p = {row['p_value']:.3f}) [{sig}]")

# Comparação — ROBUSTEZ (4d)
print("\nResultados Model 5 (FE + Controls, 4d — ROBUSTEZ):")
rob_4d = df_results[df_results['model'] == 'Model 5: FE + Controls (4d)']
for _, row in rob_4d.iterrows():
    sig = "SIG" if row['p_value'] < ALPHA else "n.s."
    print(f"  {OUTCOMES.get(row['outcome'], row['outcome'])}: "
          f"β = {row['coef']:.4f}{row['stars']} "
          f"(SE = {row['se']:.4f}, p = {row['p_value']:.3f}) [{sig}]")

# Consistência 2d vs 4d
print("\n--- Consistência 2d vs 4d ---")
for outcome in OUTCOMES.keys():
    r_2d = main_results[main_results['outcome'] == outcome]
    r_4d = rob_4d[rob_4d['outcome'] == outcome]
    if len(r_2d) > 0 and len(r_4d) > 0:
        same_sign = (r_2d.iloc[0]['coef'] * r_4d.iloc[0]['coef']) > 0
        print(f"  {outcome}: {'✓ mesma direção' if same_sign else '⚠ direções opostas'} "
              f"(2d: {r_2d.iloc[0]['coef']:.4f}, 4d: {r_4d.iloc[0]['coef']:.4f})")

# Comparar com abordagem antiga (PNAD)
print("\n--- Comparação com Etapa antiga (PNAD, ref.) ---")
print("  PNAD Model 3: ln_renda β = -0.003 (n.s.), horas β = -0.136 (n.s.)")
print("  CAGED Model 3: ver resultados acima")
print("  Nota: outcomes diferentes — CAGED mede fluxos (admissões/demissões),")
print("  PNAD media estoques (renda/horas de todos os ocupados).")
```

---

### 6. Event study

**Markdown:**

Estimação do event study com dummies de interação período × tratamento. O período de referência é t = −1 (mês antes do lançamento do ChatGPT, ou seja, Nov/2022).

#### Especificação

$$y_{it} = \alpha_i + \gamma_t + \sum_{k \neq -1} \beta_k \cdot \mathbb{1}[t = k] \cdot \text{AltaExp}_i + X_{it}'\delta + \varepsilon_{it}$$

Onde $k$ é o tempo relativo ao tratamento em meses, $\alpha_i$ são efeitos fixos de ocupação, $\gamma_t$ são efeitos fixos de período, e $X_{it}$ são controles.

> **Nota — Binning dos extremos:** Com 54 meses e muitas dummies, os extremos podem ser imprecisos. Agrupar os primeiros/últimos meses (ex: k ≤ −12 e k ≥ 24) em bins melhora a precisão. Com a janela Jan/2021–Jun/2025, temos 23 meses pré (t=-23 a t=-1) e 31 meses pós (t=0 a t=30).

```python
# Etapa 2b.6 — Event Study

# ---------------------------------------------------------------------------
# PASSO 1: Criar dummies de evento
# ---------------------------------------------------------------------------
df_es = df_reg.copy()

# Referência: t = -1 (mês antes do ChatGPT)
ref_t = -1
periodos_relativos = sorted(df_es['tempo_relativo_meses'].unique())
print(f"Períodos relativos: {periodos_relativos[0]} a {periodos_relativos[-1]}")
print(f"Referência: t = {ref_t}")

# Binning dos extremos (recomendado)
# Com janela Jan/2021–Jun/2025: 23 meses pré (t=-23 a t=-1), 31 meses pós (t=0 a t=30)
BIN_MIN = -12  # Agrupar t <= -12 (primeiros 11 meses do pré)
BIN_MAX = 24   # Agrupar t >= 24 (últimos 6 meses do pós: t=24 a t=30)

df_es['t_binned'] = df_es['tempo_relativo_meses'].clip(lower=BIN_MIN, upper=BIN_MAX)

# Criar dummies de interação período × tratamento
did_vars = []
for t in sorted(df_es['t_binned'].unique()):
    if t == ref_t:
        continue  # Omitir referência
    dummy_name = f'did_t{t}'
    df_es[dummy_name] = ((df_es['t_binned'] == t) & (df_es['alta_exp'] == 1)).astype(int)
    did_vars.append(dummy_name)

print(f"\nDummies de evento: {len(did_vars)} (excluindo referência t={ref_t})")

# ---------------------------------------------------------------------------
# PASSO 2: Estimar event study para cada outcome
# ---------------------------------------------------------------------------
event_study_results = {}

for outcome, label in OUTCOMES.items():
    if outcome not in df_es.columns:
        continue

    df_out = df_es[df_es[outcome].notna()].copy()

    # Fórmula
    did_terms = ' + '.join(did_vars)
    formula = f"{outcome} ~ {did_terms} + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"

    try:
        model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)

        # Extrair coeficientes
        coefs = []
        for t in sorted(df_es['t_binned'].unique()):
            if t == ref_t:
                coefs.append({'t': t, 'coef': 0, 'se': 0, 'p_value': np.nan,
                              'is_reference': True, 'is_pre': t < 0})
            else:
                dname = f'did_t{t}'
                if dname in model.coefnames():
                    idx = list(model.coefnames()).index(dname)
                    coefs.append({
                        't': t,
                        'coef': model.coef()[dname],
                        'se': model.se()[dname],
                        'p_value': model.pvalue()[dname],
                        'is_reference': False,
                        'is_pre': t < 0,
                    })

        df_coefs = pd.DataFrame(coefs)
        df_coefs['ci_low'] = df_coefs['coef'] - 1.96 * df_coefs['se']
        df_coefs['ci_high'] = df_coefs['coef'] + 1.96 * df_coefs['se']

        event_study_results[outcome] = df_coefs
        df_coefs.to_csv(OUTPUTS_TABLES / f'event_study_{outcome}.csv', index=False)

        print(f"\n{label}:")
        print(f"  Coeficientes pré significativos (p<0.05): "
              f"{(df_coefs[(df_coefs['is_pre']) & (df_coefs['p_value'] < 0.05)]).shape[0]}")
        print(f"  Coeficientes pós significativos (p<0.05): "
              f"{(df_coefs[(~df_coefs['is_pre']) & (~df_coefs['is_reference']) & (df_coefs['p_value'] < 0.05)]).shape[0]}")

    except Exception as e:
        print(f"  ERRO em {outcome}: {e}")
```

```python
# Etapa 2b.6 (cont.) — Gráficos do Event Study

# ---------------------------------------------------------------------------
# PASSO 3: Gráficos de event study
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for i, (outcome, label) in enumerate(OUTCOMES.items()):
    if outcome not in event_study_results:
        continue

    ax = axes[i]
    df_coefs = event_study_results[outcome]

    # Separar pré e pós
    pre = df_coefs[df_coefs['is_pre'] & ~df_coefs['is_reference']]
    post = df_coefs[~df_coefs['is_pre'] & ~df_coefs['is_reference']]
    ref = df_coefs[df_coefs['is_reference']]

    # Plotar IC
    ax.fill_between(df_coefs['t'], df_coefs['ci_low'], df_coefs['ci_high'],
                     alpha=0.15, color='gray')

    # Plotar coeficientes
    ax.scatter(pre['t'], pre['coef'], color=COLORS['pre'], s=30, zorder=5, label='Pré-tratamento')
    ax.scatter(post['t'], post['coef'], color=COLORS['post'], s=30, zorder=5, label='Pós-tratamento')
    ax.scatter(ref['t'], ref['coef'], color='black', s=60, marker='D', zorder=6, label='Referência')

    # Conectar pontos
    ax.plot(df_coefs['t'], df_coefs['coef'], color='gray', linewidth=0.8, alpha=0.5)

    # Linha zero e evento
    ax.axhline(y=0, color='black', linewidth=0.5)
    ax.axvline(x=0, color='gray', linestyle='--', alpha=0.7)

    ax.set_title(label)
    ax.set_xlabel('Meses relativos ao ChatGPT')
    ax.set_ylabel('Coeficiente DiD')
    ax.legend(fontsize=7)

plt.suptitle('Event Study: Efeito da IA Generativa sobre Emprego Formal',
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUTS_FIGURES / 'event_study_all_outcomes.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

### 6b. Teste formal de tendências paralelas

**Markdown:**

Teste estatístico: H₀ = todos os coeficientes pré-tratamento são conjuntamente zero.

```python
# Etapa 2b.6b — Teste formal de tendências paralelas

print("=" * 60)
print("TESTE FORMAL DE TENDÊNCIAS PARALELAS")
print("=" * 60)

results_pt = []

for outcome, label in OUTCOMES.items():
    if outcome not in event_study_results:
        continue

    df_coefs = event_study_results[outcome]
    pre_coefs = df_coefs[df_coefs['is_pre'] & ~df_coefs['is_reference']]

    # Teste: algum coeficiente pré é individualmente significativo?
    n_sig = (pre_coefs['p_value'] < 0.05).sum()
    max_abs_coef = pre_coefs['coef'].abs().max()
    max_abs_t = (pre_coefs['coef'] / pre_coefs['se']).abs().max()

    # Teste conjunto (F-test aproximado)
    # H0: todos os betas_pre = 0
    pre_t_stats = (pre_coefs['coef'] / pre_coefs['se']).values
    n_pre = len(pre_t_stats)
    f_stat = np.mean(pre_t_stats**2)  # Approximação
    p_joint = 1 - stats.chi2.cdf(f_stat * n_pre, df=n_pre)

    status = 'PARALELAS' if n_sig == 0 and p_joint > 0.10 else 'PREOCUPAÇÃO'

    results_pt.append({
        'Outcome': label,
        'N coefs pré': n_pre,
        'Sig. individuais (p<0.05)': n_sig,
        'Max |t-stat|': f'{max_abs_t:.2f}',
        'p-valor conjunto': f'{p_joint:.3f}',
        'Status': status,
    })

    print(f"\n{label}:")
    print(f"  Coefs pré: {n_pre}")
    print(f"  Significativos (p<0.05): {n_sig}")
    print(f"  Max |coef|: {max_abs_coef:.4f}")
    print(f"  Teste conjunto p-valor: {p_joint:.3f}")
    print(f"  → {status}")

df_pt = pd.DataFrame(results_pt)
df_pt.to_csv(OUTPUTS_TABLES / 'parallel_trends_test.csv', index=False)
```

---

### 7. Análise de heterogeneidade (Triple-DiD)

**Markdown:**

Testar se o efeito da IA generativa é heterogêneo por dimensão das admissões. Inspirado nos achados da Etapa antiga: jovens e trabalhadores com ensino superior tiveram efeitos diferenciados em horas trabalhadas.

#### Dimensões de heterogeneidade

| Dimensão | Variável | Definição |
|----------|----------|-----------|
| Composição etária | `jovem_adm` | 1 se `idade_media_adm ≤ 30` |
| Composição de gênero | `feminino_adm` | 1 se `pct_mulher_adm > mediana` |
| Composição educacional | `alta_educ_adm` | 1 se `pct_superior_adm > mediana` |
| Setor | `grande_grupo_cbo` | Por grande grupo ocupacional |

#### Especificação Triple-DiD

$$y_{it} = \alpha_i + \gamma_t + \beta_1 (Post_t \times AltaExp_i) + \beta_2 (Post_t \times AltaExp_i \times Grupo_i) + \text{controles} + \varepsilon_{it}$$

O coeficiente $\beta_2$ captura o **efeito diferencial** para o subgrupo.

```python
# Etapa 2b.7 — Análise de heterogeneidade (Triple-DiD)

# ---------------------------------------------------------------------------
# PASSO 1: Criar variáveis de heterogeneidade
# ---------------------------------------------------------------------------
df_het = df_reg.copy()

# Definir medianas no pré-tratamento para cortes
pre_mask = df_het['post'] == 0
mediana_idade = df_het.loc[pre_mask, 'idade_media_adm'].median()
mediana_mulher = df_het.loc[pre_mask, 'pct_mulher_adm'].median()
mediana_educ = df_het.loc[pre_mask, 'pct_superior_adm'].median()

df_het['jovem_adm'] = (df_het['idade_media_adm'] <= 30).astype(int)
df_het['feminino_adm'] = (df_het['pct_mulher_adm'] > mediana_mulher).astype(int)
df_het['alta_educ_adm'] = (df_het['pct_superior_adm'] > mediana_educ).astype(int)

print(f"Medianas pré-tratamento:")
print(f"  Idade: {mediana_idade:.1f}")
print(f"  % Mulher: {mediana_mulher:.3f}")
print(f"  % Superior: {mediana_educ:.3f}")

# ---------------------------------------------------------------------------
# PASSO 2: Triple-DiD para cada dimensão × outcome
# ---------------------------------------------------------------------------
HETEROGENEITY_GROUPS = {
    'jovem_adm': 'Idade (jovem ≤ 30)',
    'feminino_adm': 'Gênero (feminino)',
    'alta_educ_adm': 'Educação (superior)',
}

results_het = []

for group_var, group_label in HETEROGENEITY_GROUPS.items():
    # Criar interações
    df_het['post_alta'] = df_het['post'] * df_het['alta_exp']
    df_het['post_group'] = df_het['post'] * df_het[group_var]
    df_het['alta_group'] = df_het['alta_exp'] * df_het[group_var]
    df_het['post_alta_group'] = df_het['post'] * df_het['alta_exp'] * df_het[group_var]

    for outcome, outcome_label in OUTCOMES.items():
        if outcome not in df_het.columns:
            continue

        df_out = df_het[df_het[outcome].notna()].copy()

        formula = (f"{outcome} ~ post_alta_group + post_alta + post_group + alta_group "
                   f"+ idade_media_adm + pct_mulher_adm + pct_superior_adm "
                   f"| cbo_4d + periodo")

        try:
            model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)

            # Extrair coeficientes
            main_coef = model.coef()['post_alta']
            main_se = model.se()['post_alta']
            inter_coef = model.coef()['post_alta_group']
            inter_se = model.se()['post_alta_group']
            inter_pval = model.pvalue()['post_alta_group']

            # Efeito total para o subgrupo = main + interaction
            total_effect = main_coef + inter_coef
            total_se = np.sqrt(main_se**2 + inter_se**2)  # Aproximação

            stars = '***' if inter_pval < 0.01 else '**' if inter_pval < 0.05 else '*' if inter_pval < 0.10 else ''

            results_het.append({
                'outcome': outcome,
                'outcome_label': outcome_label,
                'group': group_label,
                'main_effect': main_coef,
                'interaction': inter_coef,
                'interaction_se': inter_se,
                'interaction_pval': inter_pval,
                'interaction_stars': stars,
                'total_effect': total_effect,
                'total_se': total_se,
            })

            if inter_pval < 0.10:
                print(f"  ** {outcome_label} × {group_label}: "
                      f"interação = {inter_coef:.4f}{stars} (p={inter_pval:.3f})")

        except Exception as e:
            print(f"  ERRO: {outcome} × {group_var}: {e}")

df_het_results = pd.DataFrame(results_het)
df_het_results.to_csv(OUTPUTS_TABLES / 'heterogeneity_triple_did.csv', index=False)

# Resumo
print("\n\nRESUMO DA HETEROGENEIDADE:")
sig_results = df_het_results[df_het_results['interaction_pval'] < 0.10]
if len(sig_results) > 0:
    print(f"Efeitos heterogêneos significativos (p<0.10): {len(sig_results)}")
    for _, row in sig_results.iterrows():
        print(f"  {row['outcome_label']} × {row['group']}: "
              f"β_inter = {row['interaction']:.4f}{row['interaction_stars']}")
else:
    print("Nenhum efeito heterogêneo significativo detectado.")
```

---

### 8. Testes de robustez

**Markdown:**

Cinco testes de robustez para avaliar a validade dos resultados:

| Teste | Descrição | Resultado esperado (se válido) |
|-------|-----------|-------------------------------|
| **Cutoffs alternativos** | Top 10%, 25%, mediana, contínuo | Coeficientes na mesma direção |
| **Placebo temporal** | Evento fictício em Jun/2021 | Coeficiente não significativo |
| **Exclusão de TI** | Remover ocupações de TI (CBO 2xxx) | Resultado estável |
| **Tendências diferenciais** | Trend × tratamento no pré | Coeficiente não significativo |
| **Crosswalk 2d vs 4d** | Comparar resultados com score 4d | Mesma direção e magnitude similar |

```python
# Etapa 2b.8 — Testes de robustez

results_robust = []

# ---------------------------------------------------------------------------
# TESTE 1: Cutoffs alternativos de tratamento
# ---------------------------------------------------------------------------
print("TESTE 1: Cutoffs alternativos")
cutoff_vars = {
    'alta_exp': 'Top 20% (MAIN)',
    'alta_exp_10': 'Top 10%',
    'alta_exp_25': 'Top 25%',
    'alta_exp_mediana': 'Mediana',
}

for treat_var, treat_label in cutoff_vars.items():
    if treat_var not in df_reg.columns:
        continue

    df_reg[f'post_{treat_var}'] = df_reg['post'] * df_reg[treat_var]

    for outcome, out_label in OUTCOMES.items():
        if outcome not in df_reg.columns:
            continue

        df_out = df_reg[df_reg[outcome].notna()].copy()
        formula = f"{outcome} ~ post_{treat_var} + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"

        try:
            model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
            coef = model.coef()[f'post_{treat_var}']
            se = model.se()[f'post_{treat_var}']
            pval = model.pvalue()[f'post_{treat_var}']
            stars = '***' if pval < 0.01 else '**' if pval < 0.05 else '*' if pval < 0.10 else ''

            results_robust.append({
                'outcome': outcome,
                'test_type': 'Alternative Cutoff',
                'specification': treat_label,
                'coef': coef, 'se': se, 'p_value': pval, 'stars': stars,
            })
        except Exception as e:
            print(f"  Erro: {outcome}/{treat_label}: {e}")

# ---------------------------------------------------------------------------
# TESTE 2: Placebo temporal
# ---------------------------------------------------------------------------
print("\nTESTE 2: Placebo temporal (evento fictício Dez/2021)")
PLACEBO_ANO = 2021
PLACEBO_MES = 12  # ~metade do período pré (Jan/2021 a Nov/2022)

df_placebo = df_reg[df_reg['post'] == 0].copy()  # Apenas pré-tratamento real
placebo_ref = PLACEBO_ANO * 100 + PLACEBO_MES
df_placebo['post_placebo'] = (df_placebo['periodo_num'] >= placebo_ref).astype(int)
df_placebo['did_placebo'] = df_placebo['post_placebo'] * df_placebo['alta_exp']

for outcome, out_label in OUTCOMES.items():
    if outcome not in df_placebo.columns:
        continue

    df_out = df_placebo[df_placebo[outcome].notna()].copy()
    formula = f"{outcome} ~ did_placebo + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"

    try:
        model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
        coef = model.coef()['did_placebo']
        se = model.se()['did_placebo']
        pval = model.pvalue()['did_placebo']
        stars = '***' if pval < 0.01 else '**' if pval < 0.05 else '*' if pval < 0.10 else ''

        results_robust.append({
            'outcome': outcome, 'test_type': 'Placebo',
            'specification': f'Placebo ({PLACEBO_MES}/{PLACEBO_ANO})',
            'coef': coef, 'se': se, 'p_value': pval, 'stars': stars,
        })

        status = "PASS" if pval > 0.10 else "FAIL"
        print(f"  {out_label}: β={coef:.4f}{stars} (p={pval:.3f}) → {status}")
    except Exception as e:
        print(f"  Erro: {outcome}: {e}")

# ---------------------------------------------------------------------------
# TESTE 3: Exclusão de ocupações de TI
# ---------------------------------------------------------------------------
print("\nTESTE 3: Exclusão de ocupações de TI")
# CBO grupo 2 (profissionais) inclui TI; grupo 1 (dirigentes) pode incluir gestores de TI
# Mais preciso: excluir CBOs que começam com '21' (profissionais de ciência/TI)
df_no_it = df_reg[~df_reg['cbo_4d'].str.startswith('21')].copy()
print(f"  Registros sem TI: {len(df_no_it):,} (removidos: {len(df_reg)-len(df_no_it):,})")

for outcome, out_label in OUTCOMES.items():
    if outcome not in df_no_it.columns:
        continue

    df_out = df_no_it[df_no_it[outcome].notna()].copy()
    formula = f"{outcome} ~ post_alta + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"

    try:
        model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
        coef = model.coef()['post_alta']
        se = model.se()['post_alta']
        pval = model.pvalue()['post_alta']
        stars = '***' if pval < 0.01 else '**' if pval < 0.05 else '*' if pval < 0.10 else ''

        results_robust.append({
            'outcome': outcome, 'test_type': 'Excl. TI',
            'specification': 'Sem ocupações TI',
            'coef': coef, 'se': se, 'p_value': pval, 'stars': stars,
        })
    except Exception as e:
        print(f"  Erro: {outcome}: {e}")

# ---------------------------------------------------------------------------
# TESTE 4: Tendências diferenciais pré-tratamento
# ---------------------------------------------------------------------------
print("\nTESTE 4: Tendências diferenciais pré-tratamento")
df_pre_trend = df_reg[df_reg['post'] == 0].copy()
df_pre_trend['trend_alta'] = df_pre_trend['trend'] * df_pre_trend['alta_exp']

for outcome, out_label in OUTCOMES.items():
    if outcome not in df_pre_trend.columns:
        continue

    df_out = df_pre_trend[df_pre_trend[outcome].notna()].copy()
    formula = f"{outcome} ~ trend_alta + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"

    try:
        model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
        coef = model.coef()['trend_alta']
        se = model.se()['trend_alta']
        pval = model.pvalue()['trend_alta']
        stars = '***' if pval < 0.01 else '**' if pval < 0.05 else '*' if pval < 0.10 else ''

        results_robust.append({
            'outcome': outcome, 'test_type': 'Differential Trends',
            'specification': 'Trend × Tratamento (pré)',
            'coef': coef, 'se': se, 'p_value': pval, 'stars': stars,
        })

        status = "OK" if pval > 0.10 else "PREOCUPAÇÃO"
        print(f"  {out_label}: β_trend={coef:.6f}{stars} (p={pval:.3f}) → {status}")
    except Exception as e:
        print(f"  Erro: {outcome}: {e}")

# ---------------------------------------------------------------------------
# TESTE 5: Crosswalk 2d vs 4d (consistência entre especificações)
# ---------------------------------------------------------------------------
print("\nTESTE 5: Crosswalk 2d vs 4d")
df_4d = df_reg[df_reg['exposure_score_4d'].notna()].copy()

for outcome, out_label in OUTCOMES.items():
    if outcome not in df_4d.columns:
        continue

    df_out = df_4d[df_4d[outcome].notna()].copy()
    formula = f"{outcome} ~ post_alta_4d + idade_media_adm + pct_mulher_adm + pct_superior_adm | cbo_4d + periodo"

    try:
        model = pf.feols(formula, data=df_out, vcov=VCOV_SPEC)
        coef = model.coef()['post_alta_4d']
        se = model.se()['post_alta_4d']
        pval = model.pvalue()['post_alta_4d']
        stars = '***' if pval < 0.01 else '**' if pval < 0.05 else '*' if pval < 0.10 else ''

        results_robust.append({
            'outcome': outcome, 'test_type': 'Crosswalk 4d',
            'specification': 'Score 4d (fallback hierárquico 6 níveis)',
            'coef': coef, 'se': se, 'p_value': pval, 'stars': stars,
        })

        # Comparar com resultado 2d
        r_2d = df_results[(df_results['model'] == 'Model 3: FE + Controls (MAIN)') &
                          (df_results['outcome'] == outcome)]
        if len(r_2d) > 0:
            same_sign = (coef * r_2d.iloc[0]['coef']) > 0
            status = "CONSISTENTE" if same_sign else "DIVERGE"
            print(f"  {out_label}: 4d β={coef:.4f}{stars} vs 2d β={r_2d.iloc[0]['coef']:.4f} → {status}")
    except Exception as e:
        print(f"  Erro: {outcome}: {e}")

# ---------------------------------------------------------------------------
# Consolidar e salvar
# ---------------------------------------------------------------------------
df_robust = pd.DataFrame(results_robust)
df_robust.to_csv(OUTPUTS_TABLES / 'robustness_results.csv', index=False)

print(f"\nResultados de robustez salvos: {OUTPUTS_TABLES / 'robustness_results.csv'}")
```

---

### 9. Tabelas LaTeX

**Markdown:**

Formatar os resultados principais em tabelas LaTeX para inclusão na dissertação.

```python
# Etapa 2b.9 — Tabelas LaTeX

# ---------------------------------------------------------------------------
# Função auxiliar de formatação
# ---------------------------------------------------------------------------
def format_coef_se(coef, se, stars='', decimal_places=4):
    """Formata coeficiente e SE para LaTeX."""
    if pd.isna(coef) or pd.isna(se):
        return "—"
    coef_str = f"{coef:.{decimal_places}f}{stars}"
    se_str = f"({se:.{decimal_places}f})"
    return f"{coef_str} \\\\ {se_str}"

# ---------------------------------------------------------------------------
# Tabela 1: Resultados DiD principais
# ---------------------------------------------------------------------------
print("Gerando tabelas LaTeX...")

# Tabela principal (Model 3 para todos os outcomes)
main = df_results[df_results['model'] == 'Model 3: FE + Controls (MAIN)']

latex_main = []
latex_main.append(r"\begin{table}[htbp]")
latex_main.append(r"\centering")
latex_main.append(r"\caption{Efeitos DiD sobre Emprego Formal: Resultados Principais}")
latex_main.append(r"\label{tab:did_main}")
latex_main.append(r"\begin{tabular}{lcccc}")
latex_main.append(r"\toprule")
latex_main.append(r" & (1) Log(Adm.) & (2) Log(Desl.) & (3) Saldo & (4) Log(Salário) \\")
latex_main.append(r"\midrule")

# Coeficientes
coef_line = r"Post $\times$ Alta Exp."
se_line = ""
for outcome in ['ln_admissoes', 'ln_desligamentos', 'saldo', 'ln_salario_adm']:
    row = main[main['outcome'] == outcome]
    if len(row) > 0:
        r = row.iloc[0]
        coef_line += f" & {r['coef']:.4f}{r['stars']}"
        se_line += f" & ({r['se']:.4f})"
    else:
        coef_line += " & —"
        se_line += " & —"

latex_main.append(coef_line + r" \\")
latex_main.append(se_line + r" \\")
latex_main.append(r"\midrule")

# N e clusters
n_line = "N"
cl_line = "Clusters"
for outcome in ['ln_admissoes', 'ln_desligamentos', 'saldo', 'ln_salario_adm']:
    row = main[main['outcome'] == outcome]
    if len(row) > 0:
        r = row.iloc[0]
        n_line += f" & {int(r['n_obs']):,}"
        cl_line += f" & {int(r['n_clusters']) if r['n_clusters'] else '—'}"
    else:
        n_line += " & —"
        cl_line += " & —"

latex_main.append(n_line + r" \\")
latex_main.append(cl_line + r" \\")
latex_main.append(r"FE Ocupação & \checkmark & \checkmark & \checkmark & \checkmark \\")
latex_main.append(r"FE Período & \checkmark & \checkmark & \checkmark & \checkmark \\")
latex_main.append(r"Controles & \checkmark & \checkmark & \checkmark & \checkmark \\")
latex_main.append(r"\bottomrule")
latex_main.append(r"\end{tabular}")
latex_main.append(r"\begin{tablenotes}\small")
latex_main.append(r"\item Erros padrão clusterizados por ocupação (CBO 4d). * $p<0.10$, ** $p<0.05$, *** $p<0.01$.")
latex_main.append(r"\item Controles: idade média, \% mulheres e \% superior completo nas admissões.")
latex_main.append(r"\item Tratamento: top 20\% de exposição à IA (índice ILO, 2 dígitos ISCO-08). Período: Jan/2021–Jun/2025 (54 meses). Salários winsorizados P1/P99.")
latex_main.append(r"\end{tablenotes}")
latex_main.append(r"\end{table}")

latex_text = '\n'.join(latex_main)

# Salvar
with open(OUTPUTS_TABLES / 'table_did_main.tex', 'w') as f:
    f.write(latex_text)

print(f"Tabela LaTeX salva: {OUTPUTS_TABLES / 'table_did_main.tex'}")
print("\nPreview:")
print(latex_text)
```

---

### 10. Síntese e conclusões

**Markdown:**

Resumo dos principais achados, comparação com a literatura e limitações.

```python
# Etapa 2b.10 — Síntese e conclusões

print("=" * 70)
print("SÍNTESE DOS PRINCIPAIS ACHADOS — ETAPA 2b")
print("=" * 70)

# ---------------------------------------------------------------------------
# 1. Resultados principais (Model 3)
# ---------------------------------------------------------------------------
print("\n1. RESULTADOS DiD PRINCIPAIS (Model 3: FE + Controls)")
print("-" * 50)
main = df_results[df_results['model'] == 'Model 3: FE + Controls (MAIN)']
for _, row in main.iterrows():
    label = OUTCOMES.get(row['outcome'], row['outcome'])
    sig = "SIGNIFICATIVO" if row['p_value'] < 0.05 else "não significativo"
    print(f"  {label}: β = {row['coef']:.4f}{row['stars']} (SE = {row['se']:.4f}, p = {row['p_value']:.3f}) — {sig}")

# ---------------------------------------------------------------------------
# 2. Event study
# ---------------------------------------------------------------------------
print("\n2. EVENT STUDY")
print("-" * 50)
for outcome, label in OUTCOMES.items():
    if outcome in event_study_results:
        df_c = event_study_results[outcome]
        pre_sig = df_c[(df_c['is_pre']) & (df_c['p_value'] < 0.05)].shape[0]
        post_sig = df_c[(~df_c['is_pre']) & (~df_c['is_reference']) & (df_c['p_value'] < 0.05)].shape[0]
        print(f"  {label}: {pre_sig} coefs pré sig., {post_sig} coefs pós sig.")

# ---------------------------------------------------------------------------
# 3. Heterogeneidade
# ---------------------------------------------------------------------------
print("\n3. HETEROGENEIDADE (Triple-DiD)")
print("-" * 50)
if len(sig_results := df_het_results[df_het_results['interaction_pval'] < 0.10]) > 0:
    for _, row in sig_results.iterrows():
        print(f"  {row['outcome_label']} × {row['group']}: "
              f"β_inter = {row['interaction']:.4f}{row['interaction_stars']} "
              f"(total = {row['total_effect']:.4f})")
else:
    print("  Nenhum efeito heterogêneo significativo (p<0.10)")

# ---------------------------------------------------------------------------
# 4. Robustez
# ---------------------------------------------------------------------------
print("\n4. ROBUSTEZ")
print("-" * 50)
for test_type in df_robust['test_type'].unique():
    sub = df_robust[df_robust['test_type'] == test_type]
    n_sig = (sub['p_value'] < 0.10).sum()
    n_total = len(sub)
    status = "OK" if test_type in ['Placebo', 'Differential Trends'] and n_sig == 0 else ""
    print(f"  {test_type}: {n_sig}/{n_total} significativos {status}")

# ---------------------------------------------------------------------------
# 5. Comparação com abordagem anterior (PNAD)
# ---------------------------------------------------------------------------
print("\n5. COMPARAÇÃO COM ETAPA ANTERIOR (PNAD)")
print("-" * 50)
print("  PNAD (DiD antigo): efeito médio n.s. em renda e horas")
print("  PNAD (heterogeneidade): jovens -0.75*** horas, superior +0.45** horas")
print("  CAGED (esta etapa): ver resultados acima")
print("  Nota: dados e outcomes diferentes — PNAD mede estoques, CAGED mede fluxos")

# ---------------------------------------------------------------------------
# 6. Limitações
# ---------------------------------------------------------------------------
print("\n6. LIMITAÇÕES")
print("-" * 50)
limitacoes = [
    "1. CAGED cobre apenas emprego formal (CLT); informalidade não capturada.",
    "2. Fluxos ≠ estoques: queda em admissões pode indicar menor rotatividade.",
    "3. Índice ILO é global; pode não capturar especificidades brasileiras.",
    "4. Janela Jan/2021–Jun/2025 (54 meses): exclui 2020 (COVID); 2025 limitado a 6 meses.",
    "5. ChatGPT como proxy de IA generativa; difusão gradual, não instantânea.",
    "6. Crosswalk 2d: agregação em 43 sub-major groups perde variação intragrupo.",
    "7. Crosswalk 4d: erro de medição possível (fallback hierárquico 6 níveis; Muendler mapeia CBO 1994, não CBO 2002).",
    "8. Outliers salariais: Jun/2025 apresenta salário agregado ~3× normal; winsorização P1/P99 aplicada.",
]
for lim in limitacoes:
    print(f"  {lim}")

print(f"\n{'=' * 70}")
print("FIM DA ETAPA 2b")
print(f"{'=' * 70}")
```

---

## Limitações desta etapa

1. **Emprego formal apenas:** O CAGED cobre exclusivamente o setor formal (CLT). A informalidade, que representa ~40% da força de trabalho brasileira, não é capturada. Efeitos da IA sobre o setor informal requerem análise complementar com a PNAD (já feita na Etapa anterior).

2. **Fluxos vs. estoques:** O CAGED registra movimentações, não o estoque de empregados. Uma redução em admissões pode refletir menor demanda por trabalho OU menor rotatividade (maior retenção). A interpretação deve considerar ambos os canais.

3. **Difusão gradual da IA:** O tratamento assume que o ChatGPT impactou o mercado de forma abrupta em Nov/2022. Na prática, a difusão de IA generativa é gradual e heterogênea entre setores e empresas. O event study ajuda a capturar essa dinâmica.

4. **Janela temporal (Jan/2021–Jun/2025):** A exclusão de 2020 evita contaminação COVID. Dados de 2025 disponíveis apenas até junho (basedosdados), resultando em 54 períodos totais (23 pré, 31 pós). Ainda assim, o pós-tratamento é 1,3× maior que o pré, com poder estatístico adequado. O event study mostra se o pré-período é suficiente para validar tendências paralelas.

5. **Crosswalk 2d (especificação principal):** Ao agregar a 43 sub-major groups, perdemos variação dentro de cada grupo. A especificação de robustez a 4 dígitos ajuda a avaliar a sensibilidade.

6. **Crosswalk 4d (robustez):** O fallback hierárquico em 6 níveis (match direto CBO↔ISCO-08, via ISCO-88↔08, e agregações 3d/2d/1d) pode introduzir erro de medição. Nota: o arquivo Muendler & Poole (2004) mapeia CBO *1994* (formato X-XX.XX), não a CBO 2002 do CAGED — a estratégia adotada no Notebook 2a usa a similaridade estrutural CBO 2002↔ISCO com tabela oficial ISCO-88↔08. Erro de medição tipicamente atenua coeficientes.

7. **Índice global:** Mesma limitação das etapas anteriores — o índice ILO foi calibrado globalmente.

8. **Outliers salariais:** Jun/2025 apresenta salário médio agregado ~R$11.519 (vs ~R$4.000 normal), causado por poucas células com salários extremos (0,01% das admissões). Winsorização P1/P99 aplicada neste notebook para limitar influência sem perder observações.

9. **Nível de agregação:** A análise ao nível ocupação × mês perde variação intraocupacional. Efeitos podem ser heterogêneos por região, setor, ou tamanho de empresa dentro da mesma ocupação.

---

## Checklist de entregáveis

- [ ] `outputs/tables/balance_table_pre.csv` — Tabela de balanço
- [ ] `outputs/figures/parallel_trends_all_outcomes.png` — Gráfico de tendências paralelas
- [ ] `outputs/tables/did_main_results.csv` — Resultados DiD (4 especificações × N outcomes)
- [ ] `outputs/tables/event_study_*.csv` — Coeficientes do event study
- [ ] `outputs/figures/event_study_all_outcomes.png` — Gráficos do event study
- [ ] `outputs/tables/parallel_trends_test.csv` — Teste formal de tendências paralelas
- [ ] `outputs/tables/heterogeneity_triple_did.csv` — Resultados de heterogeneidade
- [ ] `outputs/tables/robustness_results.csv` — Testes de robustez (4 testes)
- [ ] `outputs/tables/table_did_main.tex` — Tabela LaTeX principal
- [ ] Todos os CHECKPOINTs passando
- [ ] Event study validando tendências paralelas (coeficientes pré n.s.)
- [ ] Placebo temporal não significativo

---

## Estrutura de diretórios esperada

```
etapa2/
├── data/
│   ├── input/
│   │   ├── Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx
│   │   ├── cbo-isco-conc.csv (Muendler CBO 1994→ISCO-88 — referência apenas)
│   │   ├── Correspondência ISCO 08 a 88.xlsx (tabela oficial ISCO-08↔ISCO-88, local)
│   │   └── crosswalk_cbo_isco08_mte.csv (se obtido via LAI — opcional)
│   ├── raw/
│   │   └── caged_{ano}.parquet (2021–2025, até Jun/2025)
│   ├── processed/
│   │   └── ilo_exposure_clean.csv (reusado da Etapa 1)
│   └── output/
│       ├── painel_caged_did_ready.parquet (Notebook 2a)
│       └── painel_caged_did_ready.csv
├── outputs/
│   ├── tables/
│   │   ├── balance_table_pre.csv
│   │   ├── did_main_results.csv
│   │   ├── event_study_*.csv
│   │   ├── parallel_trends_test.csv
│   │   ├── heterogeneity_triple_did.csv
│   │   ├── robustness_results.csv
│   │   └── table_did_main.tex
│   └── figures/
│       ├── parallel_trends_all_outcomes.png
│       └── event_study_all_outcomes.png
├── etapa_2a_preparacao_dados_did.ipynb (Notebook 2a — implementado)
└── etapa_2b_did_analysis_caged.ipynb (Notebook 2b — a implementar)
```
