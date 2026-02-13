# Etapa 5: DiD Ocupacional - Análise do Impacto da IA no Mercado de Trabalho Brasileiro

## Visão Geral

Este módulo implementa uma análise **Difference-in-Differences (DiD)** para estimar o efeito causal do lançamento da IA Generativa (ChatGPT, novembro 2022) sobre o mercado de trabalho brasileiro, usando variação na intensidade de exposição ocupacional.

## Pergunta de Pesquisa

> "Após o lançamento do ChatGPT, trabalhadores em ocupações mais expostas à IA Generativa experimentaram mudanças diferenciais em emprego, horas trabalhadas ou rendimentos, comparados a trabalhadores em ocupações menos expostas?"

## Estratégia de Identificação

- **Tratamento**: Ocupações com alta exposição à IA (top 20% do índice ILO)
- **Controle**: Ocupações com baixa exposição
- **Timing**: Novembro 2022 (lançamento do ChatGPT)
- **Dados**: PNAD Contínua 2021Q1 - 2024Q4 (16 trimestres, ~70-80M observações)

## Estrutura do Projeto

```
etapa5_did_ocupacional/
├── config/
│   └── settings.py              # Configuração centralizada
├── src/
│   ├── utils/
│   │   ├── weighted_stats.py    # Estatísticas ponderadas
│   │   ├── validators.py        # Validações DiD
│   │   └── plotting.py          # Gráficos
│   ├── 01_download_panel_pnad.py   # Download BigQuery (16 trimestres)
│   ├── 02_clean_panel_data.py      # Limpeza
│   ├── 03_create_variables.py      # Criação de variáveis DiD
│   ├── 04_merge_exposure.py        # Merge com índice ILO
│   ├── 05_create_treatment.py      # Definição de tratamento
│   ├── 06_balance_table.py         # Balanço pré-tratamento
│   ├── 07_parallel_trends.py       # Tendências paralelas
│   └── 08_quintile_analysis.py     # Análise por quintil
├── data/
│   ├── raw/                     # Dados brutos PNAD
│   ├── processed/               # Dados processados
│   └── external/                # Índices ILO
└── outputs/
    ├── tables/                  # Tabelas CSV + LaTeX
    ├── figures/                 # Gráficos PNG
    └── logs/                    # Logs de execução
```

## Instalação

### 1. Instalar dependências

```bash
cd etapa5_did_ocupacional
pip install -r requirements.txt
```

### 2. Configurar Google Cloud (para download via BigQuery)

```bash
# Autenticar com Google Cloud
gcloud auth application-default login
```

**Importante**: Certifique-se de que o projeto GCP `mestrado-pnad-2026` está configurado em [config/settings.py](config/settings.py).

## Execução do Pipeline

### Fase 1: Data Acquisition (~10-15 min)

```bash
# Download de 16 trimestres do BigQuery
python src/01_download_panel_pnad.py

# Se precisar reautenticar:
python src/01_download_panel_pnad.py --reauth
```

**Output**: `data/raw/pnad_panel_2021q1_2024q4.parquet` (~70-80M observações)

### Fase 2: Data Preparation (~10-15 min)

```bash
# Limpeza
python src/02_clean_panel_data.py

# Criação de variáveis (temporal, outcomes, demográficas)
python src/03_create_variables.py

# Merge com índice de exposição ILO
python src/04_merge_exposure.py

# Criação de variáveis de tratamento
python src/05_create_treatment.py
```

**Output Final**: `data/processed/pnad_panel_did_ready.parquet` (**Dataset analítico final**)

### Fase 3: Pre-Regression Diagnostics (~5 min)

```bash
# Tabela de balanço (pré-tratamento)
python src/06_balance_table.py

# Tendências paralelas (visual + estatístico)
python src/07_parallel_trends.py

# Análise por quintil de exposição
python src/08_quintile_analysis.py
```

**Outputs**:
- `outputs/tables/balance_table_pre.csv`
- `outputs/tables/parallel_trends_test_results.csv`
- `outputs/figures/parallel_trends_*.png`
- `outputs/figures/love_plot.png`

## Variáveis Criadas

### Variáveis Temporais

- `periodo`: String "2021T1", "2021T2", etc. (para gráficos)
- `periodo_num`: Numérico 20211, 20212, etc. (para cálculos)
- `tempo_relativo`: Distância do período de referência (-7, ..., 0, ..., 8)
- `post`: Dummy = 1 se período >= 2023T1 (pós-ChatGPT)

### Variáveis de Outcome

- `ocupado`: Binary (estar ocupado)
- `formal`: Binary (emprego formal)
- `ln_renda`: Log do rendimento habitual
- `horas_trabalhadas`: Horas trabalhadas na semana de referência

### Variáveis de Tratamento

- `exposure_score`: Índice contínuo de exposição [0, 1]
- `alta_exp`: Binary = 1 se exposição >= p80 (top 20%)
- `alta_exp_10`, `alta_exp_25`: Variações (top 10%, top 25%)
- `quintil_exp`: Categórica [Q1 (Baixa), Q2, Q3, Q4, Q5 (Alta)]
- `did`: post × alta_exp (interação DiD principal)

### Variáveis de Controle

- **Demográficas**: idade, mulher, negro_pardo, jovem, faixa_etaria
- **Educação**: superior, medio
- **Regional**: regiao, grande_grupo (ocupacional)

## Validações Implementadas

### 1. Completude do Painel

- ✓ 16 trimestres presentes (2021Q1 - 2024Q4)
- ✓ Mínimo 150k observações por trimestre
- ✓ 27 UFs em cada trimestre

### 2. Cobertura de Exposição

- ✓ >= 95% cobertura (ponderada pela população)
- ✓ Ocupações sem match documentadas

### 3. Atribuição de Tratamento

- ✓ Tratamento constante dentro de ocupação
- ✓ Variação entre ocupações
- ✓ Observações suficientes em todas as células (post × tratamento)

### 4. Tendências Paralelas

- **Visual**: Gráficos de tendências pré-tratamento
- **Estatístico**: Teste de pré-tendências (H0: coeficientes = 0)

### 5. Balanço de Covariáveis

- **Critério**: Diferença normalizada < |0.25|
- **Covariáveis testadas**: Idade, sexo, raça, educação, renda, formalidade

## Outputs Principais

### Tabelas

| Arquivo | Descrição |
|---------|-----------|
| `balance_table_pre.csv` | Balanço de covariáveis (pré-tratamento) |
| `exposure_thresholds.csv` | Thresholds de exposição (p80, p90, p75) |
| `treatment_definition_summary.csv` | Cross-tab post × tratamento |
| `quintile_characteristics_pre.csv` | Características por quintil |
| `parallel_trends_test_results.csv` | Testes estatísticos de pré-tendências |

### Figuras

| Arquivo | Descrição |
|---------|-----------|
| `parallel_trends_ocupado.png` | Tendências de ocupação |
| `parallel_trends_ln_renda.png` | Tendências de renda |
| `parallel_trends_formal.png` | Tendências de formalidade |
| `parallel_trends_all_outcomes.png` | Painel 2×2 multi-outcome |
| `love_plot.png` | Love plot (balanço) |
| `exposure_distribution_by_quintile.png` | Box plot de exposição por quintil |

## Critérios de Sucesso

### ✅ Fase 1 Completa

- [x] 16 trimestres baixados
- [x] ~70-80M observações totais
- [x] Todas 27 UFs presentes

### ✅ Fase 2 Completa

- [x] Dataset final: `pnad_panel_did_ready.parquet`
- [x] Cobertura de exposição >= 95%
- [x] Todas as variáveis criadas
- [x] Tratamento validado

### ✅ Fase 3 Completa

- [x] Tabela de balanço gerada
- [x] Gráficos de tendências paralelas
- [x] Testes estatísticos executados
- [x] Análise por quintil completa

## Próximos Passos (Fora do Escopo Atual)

### Fase 4: Regression Analysis

- DiD médio (average treatment effect)
- Event study (efeitos período-a-período)
- Heterogeneidade (por idade, sexo, educação)
- Robustez (placebo, thresholds alternativos, exclusão IT)

### Fase 5: Results & Interpretation

- Tabelas para publicação
- Seção da dissertação
- Implicações de política

## Dependências Externas

### De etapa1_ia_generativa

- Padrões de código (logging, configuração)
- Funções de estatística ponderada
- Mapeamentos regionais

### De etapa3_crosswalk_onet_isco08

- **Arquivo crítico**: `outputs/cod_automation_augmentation_index_final.csv`
- Contém índice de exposição com imputação hierárquica
- Garante cobertura de ~100% das ocupações COD

## Solução de Problemas

### Erro: "Arquivo de exposição não encontrado"

```bash
# Verificar se etapa3 foi executada
ls ../etapa3_crosswalk_onet_isco08/outputs/cod_automation_augmentation_index_final.csv

# Se não existir, executar etapa3 primeiro
cd ../etapa3_crosswalk_onet_isco08
python src/03_hierarchical_imputation.py
```

### Erro: "Autenticação BigQuery"

```bash
# Reautenticar
python src/01_download_panel_pnad.py --reauth

# Ou configurar manualmente
gcloud auth application-default login
```

### Cobertura de exposição < 95%

1. Verificar arquivo de exposição (deve usar etapa3 com imputação)
2. Revisar merge em `04_merge_exposure.py`
3. Checar `outputs/tables/unmatched_occupation_codes.csv`

### Tendências não-paralelas

1. **Revisar graficamente**: `outputs/figures/parallel_trends_*.png`
2. **Checar testes**: `outputs/tables/parallel_trends_test_results.csv`
3. **Considerar**: Ocupações de TI podem ter tendências específicas (boom pós-pandemia)
4. **Soluções**:
   - Adicionar occupation-specific trends na regressão (Fase 4)
   - Excluir ocupações de TI como robustez
   - Usar janela temporal mais curta

## Referências

### Metodológicas

- Angrist & Pischke (2009). *Mostly Harmless Econometrics*
- Cunningham (2021). *Causal Inference: The Mixtape*

### Substantivas

- Brynjolfsson et al. (2025). Canaries in the Coal Mine? (Stanford Digital Economy Lab)
- Gmyrek, Berg et al. (2025). GenAI and Jobs: ILO Working Paper

### Dados

- IBGE. PNAD Contínua: https://www.ibge.gov.br/estatisticas/sociais/trabalho/17270-pnad-continua.html
- Base dos Dados: https://basedosdados.org/

## Licença

Projeto acadêmico - Mestrado

## Contato

[Seu nome e contato]

---

**Última atualização**: Fevereiro 2026
**Versão**: 1.0
