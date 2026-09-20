# 01 — Auditoria do Código

Cada achado traz: arquivo e linha, o que foi verificado, severidade, e se exige re-rodar.

Severidades: **Crítico** = ameaça a validade do resultado · **Alto** = enfraquece a defesa
· **Médio** = inconsistência que a banca pode cobrar · **Baixo** = higiene.

> **Nota sobre caminhos.** Durante esta revisão o `Replication Package/` foi reestruturado em
> `V1/` e `V2/`. Os caminhos do pacote abaixo já usam o prefixo `Replication Package/V1/`. Os
> caminhos em `src/scripts/` não mudaram — é a árvore de trabalho do autor, de onde o pacote é
> derivado.

---

## Parte I — Achados que ameaçam a validade

### 1. As declarações fora do prazo e as exclusões nunca entram no painel

**Severidade: Crítico. Exige re-rodar.**

**Onde.** `src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py:436-455` (`download_caged_ano`)
consulta uma única tabela:

```sql
SELECT {COLUNAS_CAGED}
FROM `basedosdados.br_me_caged.microdados_movimentacao`
WHERE ano = {ano}
```

**O que foi verificado.** O dataset `basedosdados.br_me_caged` tem seis tabelas. Três importam:

| Tabela | Registros | Consultada pelo pipeline? |
|---|---:|---|
| `microdados_movimentacao` | 275.291.553 | Sim |
| `microdados_movimentacao_fora_prazo` | 8.609.944 | **Não** |
| `microdados_movimentacao_excluida` | 607.497 | **Não** |

O Novo CAGED trabalha com três competências: movimentações declaradas no prazo (MOV),
declaradas fora do prazo (FOR) e exclusões posteriores (EXC). A estatística oficial do PDET é
MOV + FOR − EXC. O painel usa só MOV.

**Por que isso é crítico e não apenas incompleto.** A fração omitida cai fortemente ao longo da
janela de análise — e a janela de análise é exatamente o eixo da identificação:

| Ano | Movimentações no painel | Fora do prazo omitidas | % omitida |
|---|---:|---:|---:|
| 2021 | 36.554.795 | 3.148.673 | **8,61%** |
| 2022 | 42.475.516 | 1.314.097 | 3,09% |
| 2023 | 44.485.982 | 811.237 | 1,82% |
| 2024 | 48.996.040 | 634.108 | 1,29% |
| 2025 | 47.721.335 | 668.446 | 1,40% |

O pré-tratamento (2021–nov/2022) perde entre 3% e 8,6% das movimentações. O pós-tratamento perde
entre 1,3% e 1,8%. Isso sozinho já produz uma quebra de nível na fronteira do tratamento.

Pior: a queda **não é uniforme entre ocupações**. Share de movimentações fora do prazo, por grande
grupo CBO:

| Grande grupo CBO | 2021 | 2024 | Δ (p.p.) |
|---|---:|---:|---:|
| 1 Dirigentes | 9,80% | 1,71% | 8,09 |
| 2 Profissionais ciências e artes *(tratado)* | 8,19% | 1,60% | 6,59 |
| 3 Técnicos de nível médio *(tratado)* | 7,89% | 1,45% | 6,44 |
| **4 Administrativo** *(núcleo do grupo tratado)* | **7,13%** | **1,17%** | **5,96** |
| 5 Serviços e comércio *(controle)* | 9,66% | 1,47% | 8,19 |
| 6 Agropecuária *(controle)* | 14,62% | 1,08% | **13,54** |
| 7 Bens e serviços industriais *(controle)* | 7,78% | 1,14% | 6,64 |
| 8 Indústria de processos contínuos *(controle)* | 6,42% | 0,84% | 5,58 |
| 9 Manutenção e reparação *(controle)* | 8,92% | 1,23% | 7,69 |

Os grupos que compõem majoritariamente o **controle** perdiam em torno de 2 pontos percentuais
**a mais** de cobertura em 2021 do que os grupos tratados, e essa diferença desaparece no pós.
Mecanicamente: os fluxos do controle aparecem artificialmente deprimidos no pré e "se recuperam"
no pós. Isso produz exatamente (i) um coeficiente DiD **negativo** para o grupo tratado e (ii) uma
**falha de tendência paralela**. Os dois são precisamente o que a Seção 5.1 reporta: −3,1% em
admissões (pretrend falha, p=0,001) e −4,2% em desligamentos (pretrend falha, p=0,031).

**O que isso não prova.** Não prova que os resultados são artefato. A composição interna de cada
grande grupo não é idêntica à composição do grupo tratado formal, e o efeito líquido sobre o
coeficiente pode ser menor que a diferença bruta de cobertura. O que está provado é que a
construção atual **não permite distinguir** efeito de artefato de cobertura, e que a magnitude do
artefato potencial é da mesma ordem do efeito estimado.

**Por que ninguém pegou isso antes.** As duas rodadas de referee2 auditaram consistência entre o
texto e os CSVs de saída, e a replicação cruzada Python↔R confirmou que o mesmo insumo produz o
mesmo número nas duas linguagens. Nenhuma delas questionou se o insumo estava completo. O seu
`final_review_planning.md` chega perto na Task 3 — "prior competencies can be revised by late
declarations and exclusions" — mas trata isso como razão para refazer a extração em vintage único,
não como uma tabela que está faltando.

**Correção.** Consultar as três tabelas e construir MOV + FOR − EXC. No Base dos Dados isso é uma
união de três queries. Se a V2 for pelo FTP do MTE, os três arquivos já vêm separados por mês
(`CAGEDMOV`, `CAGEDFOR`, `CAGEDEXC`).

**Gate de aceitação sugerido.** Antes de qualquer reinterpretação, rodar o modelo atual sobre o
painel corrigido e reportar quanto o coeficiente se move só por causa dessa inclusão. Esse número
é, por si só, um resultado que vale reportar num apêndice de robustez.

---

### 2. O Gradiente 4 está vazio por causa da fórmula de classificação

**Severidade: Alto. Exige re-rodar. Corrige uma explicação errada no texto.**

**Onde.** `src/scripts/run_treatment_scenario_grid.py:168-190`.

```python
def pooled_equal_weight_sd(scores, sds):
    mean_score = float(np.mean(scores))
    variances = [(sd**2) + ((score - mean_score) ** 2) for score, sd in zip(scores, sds)]
    return float(np.sqrt(np.mean(variances)))

def classify_ilo_mean_sd(mean_score, sd_score):
    if mean_score >= 0.60 and mean_score - sd_score >= 0.50:  return "Exposed: Gradient 4"
    if 0.50 <= mean_score < 0.60 and mean_score + sd_score >= 0.50: return "Exposed: Gradient 3"
    if 0.40 <= mean_score < 0.50 and mean_score + sd_score >= 0.50: return "Exposed: Gradient 2"
    if mean_score < 0.40 and mean_score + sd_score >= 0.50: return "Exposed: Gradient 1"
    ...
```

**O que foi verificado.** Recomputei a planilha da OIT e cruzei com a saída
`outputs/treatment_scenario_grid/scenario_cbo_classification.csv`.

O índice da OIT tem 427 ocupações ISCO-08 de 4 dígitos, das quais **13 são Gradiente 4**:

| ISCO-08 | Ocupação | média | DP |
|---|---|---:|---:|
| 4132 | Data Entry Clerks | 0,70 | 0,03 |
| 4131 | Typists and Word Processing Operators | 0,65 | 0,05 |
| 4311 | Accounting and Bookkeeping Clerks | 0,64 | 0,07 |
| 4312 | Statistical, Finance and Insurance Clerks | 0,64 | 0,02 |
| 3311 | Securities and Finance Dealers and Brokers | 0,63 | 0,04 |
| 4419 | Clerical Support Workers NEC | 0,63 | 0,03 |
| 2413 | Financial Analysts | 0,62 | 0,06 |
| 4313 | Payroll Clerks | 0,61 | 0,08 |
| 5244 | Contact Centre Salespersons | 0,61 | 0,10 |
| 4110 | General Office Clerks | 0,60 | 0,10 |
| 3312 | Credit and Loans Officers | 0,60 | 0,04 |
| 2513 | Web and Multimedia Developers | 0,60 | 0,08 |
| 4416 | Personnel Clerks | 0,60 | 0,09 |

A ponte MTE alcança **362 das 427** ocupações ISCO-08, incluindo **11 das 13 de Gradiente 4**
(só 3311 e 3312 ficam de fora). **16 CBOs tocam pelo menos um destino de Gradiente 4** — e
**nenhuma delas é classificada como Gradiente 4**:

| CBO | Título | nº destinos | média | DP agregado | Gradiente atribuído |
|---|---|---:|---:|---:|---|
| 4121 | Operadores de equipamentos de entrada e transmissão de dados | 3 | 0,593 | 0,138 | Gradient 3 |
| 4110 | Agentes, assistentes e auxiliares administrativos | 4 | 0,580 | 0,117 | Gradient 3 |
| 4122 | Contínuos | 5 | 0,562 | 0,128 | Gradient 3 |
| 4131 | Auxiliares de contabilidade | 3 | 0,560 | 0,128 | Gradient 3 |
| 3515 | Técnicos em secretariado, taquígrafos e estenotipistas | 5 | 0,548 | 0,126 | Gradient 3 |
| 2124 | Analistas de tecnologia da informação | 7 | 0,547 | 0,093 | Gradient 3 |
| 4223 | Operadores de telemarketing e afins | 2 | 0,535 | 0,164 | Gradient 3 |

**O mecanismo.** A regra é assimétrica. Gradiente 4 exige `média − DP ≥ 0,50`; os gradientes 1 a 3
exigem `média + DP ≥ 0,50`. Um desvio-padrão maior **dificulta** o G4 e **facilita** os gradientes
inferiores. E o desvio usado não é o desvio entre tarefas da OIT — é `pooled_equal_weight_sd`, que
**soma a dispersão entre destinos ISCO à dispersão entre tarefas**. Verificado: o DP médio é 0,079
para as 207 CBOs com um único destino e 0,114 para as 229 com mais de um.

Veja o caso decisivo. A CBO 4121, "Operadores de equipamentos de entrada e transmissão de dados",
é o equivalente brasileiro de ISCO 4132 (Data Entry Clerks), a ocupação **mais exposta de todo o
índice da OIT**, com score 0,70 e DP 0,03. No painel ela sai com média 0,593 e DP 0,138, e:

- falha o primeiro teste do G4 por 0,007 (`0,593 < 0,60`);
- falha o segundo por larga margem (`0,593 − 0,138 = 0,455 < 0,50`).

Nenhuma CBO atinge sequer `média ≥ 0,60`. O teto empírico é 0,593.

**Consequência para o texto.** A §4.2 explica assim: *"como uma mesma CBO costuma corresponder a
vários códigos ISCO-08, a exposição atribuída à ocupação vem da agregação desses destinos. Essa
média tende a diluir os picos."* Isso está parcialmente certo e omite o que decide. Duas correções
factuais: **207 das 436 CBOs (47%) mapeiam para exatamente um destino ISCO** — para elas não existe
diluição alguma; e o que efetivamente bloqueia o G4 é o termo de desvio, não a média.

**Correções possíveis, da mais barata à mais ambiciosa.**

1. Ponderar a média entre destinos ISCO por emprego, em vez de `np.nanmean` simples
   (`run_treatment_scenario_grid.py:412`). A CBO 4121 mapeia para três destinos incluindo o 4132;
   ponderada pelo emprego brasileiro de digitadores, a média sobe.
2. Separar as duas fontes de dispersão: usar o DP entre tarefas da OIT na regra de gradiente e
   reportar a dispersão entre destinos como medida de qualidade do crosswalk, não como parte do
   score.
3. Classificar no nível do destino ISCO (onde o gradiente é nativo) e agregar os **rótulos**
   ponderados por emprego, em vez de agregar os **scores** e depois classificar.

Qualquer uma delas deve ser pré-registrada antes de olhar os resultados, e as três devem entrar na
grade de sensibilidade.

---

### 3. Controles pós-tratamento na especificação principal

**Severidade: Alto. Exige re-rodar.**

**Onde.** `src/scripts/section4_event_study/estimation.py:72-74`, com a fórmula efetiva:

```
ln_admissoes ~ post_treat + idade_media_adm + pct_mulher_adm
             + pct_superior_adm + pct_negra_adm | cbo_4d + periodo
```

Os quatro controles descrevem a composição **dos admitidos no mês t**. Se a IA muda quem é
contratado — que é justamente a hipótese do trabalho — eles são desfecho, não controle.

`section4_event_study/data.py:100-105` reconhece o problema em comentário e oferece interações
`post_pre_*` com características pré-tratamento. A especificação publicada usa a versão
contemporânea mesmo assim.

**Magnitude verificada** em `outputs/dissertation_section4/section4_final_model_decision_report.md:33`,
a escada completa para o salário de admissão (N=18.307, 341 CBOs):

| Especificação | Coeficiente | p |
|---|---:|---:|
| Sem controles | **−0,0251\*** (0,0146) | 0,086 |
| Controles pré-tratamento × pós | −0,0217 | 0,251 |
| Controles contemporâneos completos *(publicado)* | −0,0207 (0,0140) | 0,140 |

Duas leituras, e vale registrar as duas honestamente. A primeira é que o controle problemático é o
que tira a significância marginal do único resultado que passa no teste de tendências paralelas. A
segunda é que a alternativa recomendada — controles pré-tratamento interagidos com o pós — dá
p=0,251, **menos** significativo que qualquer das outras duas. Trocar a especificação principal é
a decisão metodologicamente correta, mas não é a decisão que salva o resultado, e o texto não deve
dar a entender que é.

**Correção.** Principal sem controles contemporâneos. Controles pré-tratamento interagidos com
tempo como robustez. Especificação com controles contemporâneos rotulada como descritiva
condicional. É exatamente o que o seu `final_review_planning.md` §2.3 já decidiu.

---

## Parte II — Inconsistências de construção

### 4. `tipo_movimentacao` é baixado e nunca usado

**Severidade: Alto (oportunidade). Exige re-rodar.**

`COLUNAS_CAGED` inclui `tipo_movimentacao`
(`src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py:122-138`), mas a agregação usa apenas o
saldo (`etapa_2a...py:719-749`):

```python
df_adm = df[df['saldo_movimentacao'] == 1]
df_des = df[df['saldo_movimentacao'] == -1]
```

Grep confirma: `tipo_movimentacao` aparece 3 vezes no repositório, todas na declaração do SELECT.
Zero uso analítico. Consequências:

- **Transferências entre estabelecimentos contam como admissão e desligamento reais.** Uma
  reestruturação societária vira fluxo de mercado de trabalho.
- **Demissão sem justa causa, pedido de demissão e término de contrato são um evento só.** Essa é
  a decomposição que responde à pergunta que o texto declara não conseguir responder — se
  desligamentos caem porque as firmas demitem menos ou porque os trabalhadores pedem demissão
  menos, a interpretação é completamente diferente.
- **Admissão por primeiro emprego não é isolada.** É a medida mais direta da "porta de entrada",
  que é o enquadramento central da dissertação e do artigo de referência.

Ver `03_MELHORIAS_CODIGO.md` §P2 para o desenho proposto.

### 5. `horas_contratuais` nunca foi extraída

**Severidade: Médio. Exige re-rodar (nova extração).**

A tabela do Base dos Dados tem `horas_contratuais`. O `COLUNAS_CAGED` não pede. Consequência: todo
resultado salarial da dissertação é **salário mensal contratual**, que mistura preço da hora e
jornada. Uma queda de 2% no salário de admissão pode ser 2% menos por hora, ou a mesma hora com
jornada 2% menor, ou qualquer combinação. Como `indicador_trabalho_parcial` e
`indicador_trabalho_intermitente` também não são extraídos, não há como separar.

Isso importa porque a literatura de referência discute margem de horas explicitamente.

### 6. Colunas baixadas e não usadas

**Severidade: Médio (oportunidade).**

Das 16 colunas extraídas, quatro nunca entram em nenhuma agregação:

| Coluna | Situação | Uso possível |
|---|---|---|
| `categoria` | Baixada, nunca usada | Excluir aprendizes e intermitentes da amostra principal, ou tratá-los à parte |
| `cnae_2_subclasse` | Baixada, nunca usada | Efeito fixo CNAE×mês; painel CBO×CNAE |
| `tamanho_estabelecimento_janeiro` | Baixada, nunca usada | Heterogeneidade por porte — adoção de IA é fortemente graduada por tamanho |
| `cnae_2_secao` | Só como binário `secao == "J"` na Etapa 3a | Idem acima |

Nunca pedidas ao BigQuery, mas disponíveis: `tipo_empregador` e `tipo_estabelecimento` (permitem
separar setor público, que não responde a pressão competitiva de IA), `indicador_aprendiz`,
`indicador_fora_prazo`, `origem_informacao`, `tipo_deficiencia`.

### 7. Duas regras de winsorização no mesmo trabalho

**Severidade: Médio.**

`src/scripts/etapa_2b_analise_did_caged_ilo.py:214-229` winsoriza `salario_medio_adm` nos
percentis 1 e 99 **incondicionais, sobre o painel inteiro** — ou seja, uma ocupação estruturalmente
bem paga é cortada por comparação com ocupações mal pagas, e não por comparação consigo mesma.

A Seção 5.3 usa outra regra: percentis 1 e 99 **dentro de CBO de 6 dígitos × ano**
(`src/scripts/section5_3_occupation_cases/`), que é a regra defensável.

Além disso, `ln_salario_adm` usa o salário winsorizado, enquanto `ln_salario_real_adm` — o outcome
efetivamente publicado na Tabela 5.1 — é construído a partir do salário **não** winsorizado e
depois deflacionado (`section4_event_study/data.py:85-86`). São dois tratamentos de outlier
diferentes para a mesma variável dentro do mesmo modelo.

### 8. `.fillna(0)` no merge admissões × desligamentos

**Severidade: Baixo. Verificado como menor do que parece.**

`src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py:759-763`:

```python
painel = painel_adm.merge(painel_des, on=['cbo_4d','ano','mes'], how='outer').fillna(0)
```

Uma célula sem admissões recebe `salario_medio_adm = 0`, que depois vira
`log(clip(0, lower=1)) = 0` — uma observação salarial espúria de log(1).

**Quantificado no painel real** (`data/output/painel_caged_did_ready.parquet`, 23.319 linhas):
62 células com zero admissões (0,27%), 44 com zero desligamentos, **63 com `ln_salario_adm = 0`**.
É um bug real e deve ser corrigido para NaN, mas não move resultado. Corrija por higiene, não por
urgência.

### 9. Duas definições de tratamento vivas no mesmo arquivo

**Severidade: Médio.**

O parquet `painel_2b_ready.parquet` carrega simultaneamente:

- `alta_exp` — top 20% do `exposure_score_2d`, limiar 0,382857
  (`etapa_2a...py:1460-1497`), que dirige todas as saídas de `etapa_2b`;
- a classificação por gradiente da OIT (`main_strict`), que dirige tudo o que é publicado.

As duas **não são aninhadas**: o limiar 0,3829 fica *abaixo* do
`ILO_MINIMAL_EXPOSURE_BOUNDARY = 0.40`. Quem abrir as saídas de `etapa_2b` chega a números
diferentes dos da dissertação. Pior, o explicador em prosa
`outputs/crosswalk_explanation/caged_crosswalk_explanation.md` ainda descreve a regra P80 como se
fosse a definição em vigor — está obsoleto.

### 10. Duas convenções de janela de event study

**Severidade: Médio.**

`section4_event_study/estimation.py:177` agrupa as caudas:
`t_binned = clip(tempo_relativo_meses, -12, 24)`.
`section4_5_final/section5_2_dynamic_figures.py:53` usa `WINDOW_RULE = "strict_no_tail_binning"`.

Por isso a Tabela A.1 tem N=18.307 e a Figura 5.1 tem N=12.538 para o mesmo exercício. A nota de
rodapé da A.1 reconcilia isso, o que é honesto, mas a solução certa é ter uma convenção só.

### 11. Intervalos de confiança do event study usam 1,96

**Severidade: Baixo.**

`section4_event_study/estimation.py:258` usa `coef ± 1.96·se`, enquanto os p-valores ao lado vêm
do CRV1 com correção de amostra pequena sobre 341 clusters. Com 341 clusters a diferença é
pequena, mas é uma inconsistência visível: a figura e a tabela usam distribuições diferentes.

---

## Parte III — Replication Package

### 12. O que está genuinamente bom

Registro porque muda o custo da V2:

- Contratos declarativos em `V1/code/sections4_5/contracts.py` — 23 `TableSpec` e 13 `FigureSpec`,
  cada um nomeando sua função de origem.
- SHA-256 de todos os insumos, código e artefatos nos `reference_manifest.json`.
- `V1/tests/test_sections4_5.py` re-estima os quatro modelos principais do zero em pyfixest e
  exige `max_abs_difference ≤ 1e-12`. Observado: 5,2e-17.
- Replicação cruzada Python↔R independente batendo a 5,385e-12
  (`code/replication/referee2_replicate_sections4_5_main.{py,R}`).
- 138 funções de teste. `--dry-run` com preflight FOUND/BIGQUERY/MISSING por insumo.
- Testes de segurança destrutiva: `prepare_output_directory` se recusa a apagar diretório com
  `run_manifest.json` inválido.

**Isso é infraestrutura de qualidade de periódico.** É a razão principal pela qual a V2 é viável:
a máquina de verificação já existe e vai pegar regressão sozinha.

### 13. `--mode full` não roda como distribuído

**Severidade: Médio.**

`Replication Package/V1/data/raw/{section3,sections4_5}/` contêm apenas `.gitkeep`. Para rodar em
modo completo faltam ~1,9 GB de parquets do CAGED e quatro arquivos de crosswalk
(`cbo-isco-conc.csv`, `isco_08_to_88.xlsx`, `isco_08_structure.xlsx`, a planilha da OIT). Só
`--mode reproduce` funciona numa máquina limpa. Isso é comum e defensável, mas o README deve dizer
com todas as letras que o modo completo exige reconstituir os insumos, e dar as instruções.

### 14. A re-estimação de verificação testa um outcome diferente do publicado

**Severidade: Médio.**

`Replication Package/V1/code/sections4_5/analysis.py:15-20` define os quatro outcomes replicados:

```python
CORE_OUTCOMES = (
    ("ln_admissoes",     "main_results_3plus1.csv", "ln_admissoes"),
    ("ln_desligamentos", "main_results_3plus1.csv", "ln_desligamentos"),
    ("ln_salario_adm",   "main_results_3plus1.csv", "ln_salario_adm"),
    ("asinh_saldo",      "net_flow_results.csv",    "asinh_saldo"),
)
```

Repare: `ln_salario_adm` (nominal, winsorizado) e **não** `ln_salario_real_adm`, que é o que a
Tabela 5.1 publica. Os dois batem a 1e-16 apenas porque o deflator do IPCA é um efeito puramente
mensal, absorvido pelo efeito fixo `periodo`. A verificação continua válida como teste de
reprodução, mas **não verifica a construção do salário real** — que é exatamente onde está a
inconsistência de winsorização do achado 7.

### 15. Artefatos com nome enganoso congelados por contrato

**Severidade: Baixo, mas visível.**

- `Replication Package/V1/code/sections4_5/pipeline.py:241-242` mapeia explicitamente:

  ```python
  "table_a_6_income_main_diagnostics":     "table_5_2_6_heterogeneity_education.csv",
  "table_a_6_income_net_flow_diagnostics": "table_5_2_6_heterogeneity_education.csv",
  ```

  Ou seja, os artefatos com "income" no nome são gerados a partir da tabela de **escolaridade**.
  Os nomes constam também de `contracts.py:223,229`, então estão congelados por contrato.
  Documentado em comentário, não no README.
- `table_4_2_outcomes.md` contém `lo g ( y + 1 )` — um bug de espaçamento do formatador matemático,
  agora congelado permanentemente pela comparação byte-a-byte.
- `build_section4_5_final_package.py` está fora do `FULL_DAG`, mas `pipeline.py:136` exige
  exatamente 48 arquivos `.py` do autor — código morto congelado por contrato.

### 16. A camada onde está o bug não tem teste

**Severidade: Médio.**

Os 138 testes são todos contratos sobre `outputs/`: dimensões de figura, paridade de linhas de
tabela, colunas de pretrend. **Nenhum teste cobre `src/scripts/etapa_2a_*`**, que é a camada de
construção de dados — exatamente onde estão os achados 1, 4, 5, 8 e 9. O teste mais forte do
pacote (re-estimação a 1e-12) prova que o mesmo painel produz o mesmo coeficiente; não prova nada
sobre o painel estar certo.

### 17. Dependência de rede não fixada

**Severidade: Baixo.**

`src/scripts/caged_mte_crosswalk.py` raspa
`cbo.mte.gov.br/cbosite/pages/tabua/FiltroConversao_CBO2002_CBO94_CIUO88.jsf` família por família.
O cache existe localmente
(`outputs/crosswalk_audit/source_dictionaries/mte_cbo2002_cbo94_ciuo88_by_family.csv`, 1.550
linhas) mas não é distribuído no pacote. Se o site mudar, o modo completo quebra e não há como
reconstruir a versão usada. O cache deve ir para o pacote com hash.

---

## Parte IV — Extensões fora da dissertação

### 18. A extensão Anatel foi corretamente excluída

**Sem ação necessária. Registro para você não reabrir.**

A Etapa 3 (Triple-DiD com conectividade municipal) está completa em código e saídas
(`outputs/dissertation_section4/connectivity_extension/`, amostra de 3.557.921 observações, 339
CBOs, 657 municípios), e não aparece na dissertação — zero ocorrências de "Anatel",
"conectividade" ou "municip" no texto.

A exclusão está certa. Os quatro outcomes falham o teste de tendências prévias com p=0,0000
(admissões: 10 de 11 coeficientes pré significativos; desligamentos: 11 de 11); o **placebo
temporal de dezembro de 2021 é significativo** (+0,0469\*\*\*, +0,0509\*\*\*), que é uma falha de
falsificação; e os coeficientes grandes (−0,3850, −0,4647) vêm da estrutura de efeitos fixos mais
fraca e **trocam de sinal** na especificação com diagnóstico (+0,3641, +0,0919).

Duas observações técnicas, caso você reconsidere no futuro: em
`outputs/tables/triple_did_main_etapa3b.csv` as linhas `ln_salario_mulher`, `ln_salario_homem` e
`ln_salario_jovem` têm magnitudes (−0,50, −0,32, −0,63) compatíveis com contagens de admissão, não
com salários — o rótulo parece trocado. E `section4_connectivity/config.py` lê
`painel_caged_municipio_anatel.parquet` (4,56 M linhas) enquanto o cache da etapa 3b é construído
sobre `_v2` (5,53 M linhas): dois painéis municipais vivos com contagens diferentes.

### 19. Ativos prontos e não usados

**Sem severidade — oportunidade.**

- **Painel PNADc de 16 trimestres**, 2021Q1–2024Q4, 2.955.122 linhas, em
  `archive/etapa5_did_ocupacional/data/raw/pnad_panel_2021q1_2024q4.parquet`. A PNADc observa
  **estoque** de ocupados, informalidade e horas — as três coisas que o texto repete que o CAGED
  não permite ver. E o crosswalk COD→ISCO tem 99,2% de cobertura contra 69,3% do CBO.
- **Índice da OIT, vintage 2023.** A planilha tem `mean_score_2023`, `SD_2023` e `potential23`
  além das colunas de 2025. Reclassificar com o vintage anterior é um teste de sensibilidade de
  medida quase gratuito.
- **Divergência entre modelos.** A planilha traz `predicted_score_2025_gpt4o` e
  `predicted_score_2025_gemini` separados. A discordância entre os dois é uma medida direta de erro
  de medida do índice.
- **Anthropic Economic Index**: 129 MB em `EconomicIndex/release_2026_01_15/` reduzidos a um
  arquivo de 11,5 KB usado em um único split de robustez.

---

## Índice de severidade

| # | Achado | Severidade | Re-rodar? |
|---|---|---|---|
| 1 | Fora do prazo e exclusões fora do painel | **Crítico** | Sim |
| 2 | Gradiente 4 vazio por causa da fórmula | Alto | Sim |
| 3 | Controles pós-tratamento no principal | Alto | Sim |
| 4 | `tipo_movimentacao` não usado | Alto | Sim |
| 5 | `horas_contratuais` não extraída | Médio | Sim |
| 6 | Colunas baixadas e não usadas | Médio | Sim |
| 7 | Duas regras de winsorização | Médio | Sim |
| 9 | Duas definições de tratamento | Médio | Não |
| 10 | Duas convenções de janela | Médio | Sim |
| 13 | `--mode full` não roda | Médio | Não |
| 14 | Verificação testa outcome diferente | Médio | Não |
| 16 | Sem teste na camada de construção | Médio | Não |
| 8 | `.fillna(0)` | Baixo | Sim |
| 11 | IC com 1,96 | Baixo | Sim |
| 15 | Artefatos com nome enganoso | Baixo | Não |
| 17 | Crosswalk raspado sem cache no pacote | Baixo | Não |
