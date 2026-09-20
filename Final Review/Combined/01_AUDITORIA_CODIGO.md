# 01 — Auditoria do Código (combinada)

24 achados das duas auditorias, unificados por severidade. Origem marcada: **[X]** Codex,
**[C]** Claude, **[X+C]** ambos, **[!]** houve divergência resolvida.

**Veredito combinado:** revisões maiores necessárias. Não há um defeito único que invalide todos os
resultados — os quatro coeficientes nacionais centrais foram reproduzidos independentemente em
Python e R, com diferença máxima de ~2,2e-12. Mas o pacote não é, hoje, autoridade computacional
para todas as afirmações do texto, e a construção dos dados na origem tem um problema não
endereçado.

> **Caminhos.** O `Replication Package/` foi reestruturado em `V1/` e `V2/` durante a revisão.
> Caminhos do pacote levam o prefixo `Replication Package/V1/`. Caminhos em `src/scripts/` são a
> árvore de trabalho do autor, de onde o pacote é derivado.

---

## Resultados de reprodução verificados **[X]**

| Verificação | Resultado |
|---|---|
| Testes do pacote | 16/16 passam |
| Reprodução em cópia temporária, sem figuras | Exit 0; 116 arquivos |
| Modelos centrais re-estimados independentemente | 4/4 batem |
| Observações Python vs R | Idênticas: 18.307 |
| Clusters Python vs R | Idênticos: 341 CBO4 |
| Diferença numérica máxima entre linguagens | ~2,2e-12 |
| Reconstrução completa a partir de dados brutos | **Não estabelecida** |
| Replay independente de toda tabela inferencial | **Não estabelecida** |

---

## Parte I — Crítico e alto

### 1. As declarações fora do prazo e as exclusões nunca entram no painel **[C]**

**Severidade: Crítico. Exige re-rodar.**

`src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py:436-455` consulta uma tabela só:

```sql
SELECT {COLUNAS_CAGED} FROM `basedosdados.br_me_caged.microdados_movimentacao` WHERE ano = {ano}
```

O Novo CAGED trabalha com três competências. A estatística oficial do PDET é MOV + FOR − EXC.

| Tabela | Registros | Consultada? |
|---|---:|---|
| `microdados_movimentacao` | 275.291.553 | Sim |
| `microdados_movimentacao_fora_prazo` | 8.609.944 | **Não** |
| `microdados_movimentacao_excluida` | 607.497 | **Não** |

A fração omitida cai ao longo da janela — e a janela é o eixo da identificação:

| Ano | No painel | Fora do prazo omitida | % |
|---|---:|---:|---:|
| 2021 | 36.554.795 | 3.148.673 | **8,61%** |
| 2022 | 42.475.516 | 1.314.097 | 3,09% |
| 2023 | 44.485.982 | 811.237 | 1,82% |
| 2024 | 48.996.040 | 634.108 | 1,29% |
| 2025 | 47.721.335 | 668.446 | 1,40% |

E a queda **não é uniforme entre ocupações** (share fora do prazo, 2021 → 2024):

| Grande grupo CBO | 2021 | 2024 | Δ (p.p.) |
|---|---:|---:|---:|
| 2 Profissionais ciências e artes *(tratado)* | 8,19% | 1,60% | 6,59 |
| 3 Técnicos de nível médio *(tratado)* | 7,89% | 1,45% | 6,44 |
| **4 Administrativo** *(núcleo tratado)* | **7,13%** | **1,17%** | **5,96** |
| 5 Serviços e comércio *(controle)* | 9,66% | 1,47% | 8,19 |
| 6 Agropecuária *(controle)* | 14,62% | 1,08% | **13,54** |
| 7 Bens e serviços industriais *(controle)* | 7,78% | 1,14% | 6,64 |
| 8 Indústria processos contínuos *(controle)* | 6,42% | 0,84% | 5,58 |
| 9 Manutenção e reparação *(controle)* | 8,92% | 1,23% | 7,69 |

Os grupos de controle perdiam ~2 p.p. **a mais** de cobertura em 2021 do que os tratados, e a
diferença some no pós. Isso deprime os fluxos do controle no pré e os recupera no pós, produzindo
(i) um DiD negativo para o tratado e (ii) falha de tendência paralela — que é exatamente o que a
§5.1 reporta (−3,1% em admissões com pretrend p=0,001; −4,2% em desligamentos com p=0,031).

**O que não está provado:** que os resultados sejam artefato. A composição de cada grande grupo não
é idêntica à do grupo tratado formal. **O que está provado:** que a construção atual não permite
distinguir, e que a magnitude potencial é da mesma ordem do efeito estimado.

**Correção:** MOV + FOR − EXC. No Base dos Dados, união de três queries com sinal. No FTP, os três
arquivos já vêm separados. Ver `03` §P0.1.

### 2. O `reproduce` é, em boa parte, um renderizador de saídas congeladas **[X]**

**Severidade: Alto.**

O pipeline público copia 48 arquivos de backing e renderiza artefatos a partir deles. Só quatro
modelos nacionais são re-estimados:

- `Replication Package/V1/code/sections4_5/pipeline.py:66`
- `Replication Package/V1/code/sections4_5/analysis.py:65`

Event studies, pretrends exatos, DDD, heterogeneidades, Poisson, salário real e casos ocupacionais
não são re-estimados. Um `reproduce` bem-sucedido prova integridade de empacotamento e renderização,
não reconstrução independente da maioria das estimativas.

O pacote hoje mistura três conceitos que precisam ser rotulados separadamente:

1. re-estimação verdadeira (4 outcomes nacionais);
2. validação de tabelas de backing congeladas;
3. renderização determinística de artefatos de publicação.

**[C] complementa:** o alvo do replay é `ln_salario_adm` (nominal, winsorizado), enquanto a Tabela
5.1 publica `ln_salario_real_adm`. Em `V1/code/sections4_5/analysis.py:15-20`:

```python
CORE_OUTCOMES = (
    ("ln_admissoes",     "main_results_3plus1.csv", "ln_admissoes"),
    ("ln_desligamentos", "main_results_3plus1.csv", "ln_desligamentos"),
    ("ln_salario_adm",   "main_results_3plus1.csv", "ln_salario_adm"),
    ("asinh_saldo",      "net_flow_results.csv",    "asinh_saldo"),
)
```

Os dois batem a 1e-16 só porque o deflator do IPCA é efeito puramente mensal, absorvido pelo efeito
fixo `periodo`. A verificação é válida como teste de reprodução, mas **não verifica a construção do
salário real** — que é onde está a inconsistência de winsorização do achado 6.

### 3. O Apêndice A.6 é semanticamente errado no pacote **[X]**

**Severidade: Crítico.**

Os artefatos com "income" no nome são construídos com dados de escolaridade. O carregador lê as
duas fontes, mas as chamadas da A.6 passam `education`:

- `V1/code/sections4_5/publication.py:215` e `:335`
- `V1/code/sections4_5/pipeline.py:239-242`
- `V1/code/sections4_5/contracts.py:223,229`

Confirmado no mapeamento:

```python
"table_a_6_income_main_diagnostics":     "table_5_2_6_heterogeneity_education.csv",
"table_a_6_income_net_flow_diagnostics": "table_5_2_6_heterogeneity_education.csv",
```

As linhas geradas são "Fundamental ou menos", "Médio", "Superior" — não faixas de renda. **Os
testes passam porque o diretório de referência contém a mesma saída errada. A identidade
byte-a-byte validou um erro semântico.**

**Consequência:** o texto pode conter os valores de renda corretos, mas o pacote público não
consegue produzi-los sob os nomes de artefato publicados. A cadeia afirmação→código está quebrada.

*Nota de reconciliação:* o referee2 R2 registrou que a A.6 do manuscrito contém as 18 linhas de
renda corretas, com cabeçalho embaralhado no HTML. Ou seja: o texto foi corrigido à mão a partir de
`table_5_2_3_heterogeneity_income.csv`, enquanto o artefato do pacote continua vindo da escolaridade.
As duas coisas são verdade e precisam ser resolvidas juntas.

### 4. Células de fluxo zero recebem valores artificiais, e salários absurdos sobrevivem **[X+C] [!]**

**Severidade: Alto.** *(O Claude classificou como baixo; o Codex está certo — ver a divergência D4
no `00`.)*

Após o merge externo, o pipeline preenche faltantes com zero para salários e demografia, e depois
winsoriza:

- `V1/.../etapa_2a_preparacao_dados_did_caged_ilo.py:783` (`src/scripts/...:759-763`)
- `V1/.../etapa_2b_analise_did_caged_ilo.py:194` (`src/scripts/...:214-229`)

No painel congelado:

- **62 células com zero admissões carregam o mesmo salário médio positivo (R$ 1.104,7868)** — o
  piso da winsorização substituiu o zero por um valor plausível, que não chama atenção em inspeção
  visual. **31 delas entram na amostra principal**, com controles demográficos zerados.
- 44 células de zero desligamento têm salário de desligamento zero.
- **Salários de desligamento chegam a ~R$ 203,3 milhões, com sete células acima de R$ 1 milhão
  dentro da amostra principal.**

Confirmei os três números de forma independente em `data/output/painel_2b_ready.parquet` (23.319
linhas): 62 células com zero admissões, **todas com o mesmo valor 1.104,7868** (um único valor
distinto — é o piso da winsorização); salário de desligamento máximo de **R$ 203.320.402,86**; oito
células acima de R$ 1 milhão no painel completo.

**Detalhe adicional que fecha o diagnóstico:** o `salario_medio_adm` tem máximo de R$ 13.930,38 —
está winsorizado. O `salario_medio_desl` tem máximo de R$ 203 milhões — **não está**. A winsorização
de `etapa_2b:214-229` cobre `salario_medio_adm` e `salario_sm` e deixa o salário de desligamento
inteiramente sem tratamento de outlier. É por isso que valores impossíveis sobrevivem só de um lado.

**Consequência:** os outcomes salariais e os controles de composição não são bem definidos em
células de fluxo zero, valores inválidos extremos sobrevivem à estimação num dos dois outcomes
salariais, e a substituição do zero por um valor plausível torna o defeito invisível em inspeção
visual. Exige um contrato novo de missingness e validação de domínio, aplicado aos dois lados.

### 5. Controles pós-tratamento na especificação principal **[X+C]**

**Severidade: Alto.**

A especificação preferida inclui idade média e as participações de mulheres, ensino superior e
negros **entre os admitidos do mês t**:

- `V1/.../section4_event_study/config.py:33`
- `V1/.../section4_event_study/estimation.py:46`

Se a exposição afeta a composição das admissões — que é a hipótese do trabalho — essas variáveis
são mediadoras ou colisores. A alternativa com controles pré-determinados interagidos com o pós
existe no código (`data.py:95`, `pipeline.py:1140`) e não é a preferida.

**Escada verificada** (`outputs/dissertation_section4/section4_final_model_decision_report.md:33`,
salário de admissão, N=18.307, 341 CBOs):

| Especificação | Coeficiente | p |
|---|---:|---:|
| Sem controles | **−0,0251\*** (0,0146) | 0,086 |
| Controles pré-tratamento × pós | −0,0217 | 0,251 |
| Controles contemporâneos *(publicado)* | −0,0207 (0,0140) | 0,140 |

Duas leituras honestas: o controle problemático é o que tira a significância marginal do único
outcome que passa no pretrend; e a alternativa recomendada dá p=0,251, **menos** significativa que
as outras duas. Trocar a especificação é o correto — mas não é o que salva o resultado, e o texto
não deve sugerir que seja.

### 6. O Gradiente 4 está vazio por artefato da fórmula **[C] [!]**

**Severidade: Alto. Corrige uma explicação errada no texto.**

*(O Codex lista o G4 vazio entre as forças. Ver a divergência D2 no `00` — as duas leituras
coexistem.)*

`src/scripts/run_treatment_scenario_grid.py:168-190`:

```python
def pooled_equal_weight_sd(scores, sds):
    mean_score = float(np.mean(scores))
    variances = [(sd**2) + ((score - mean_score) ** 2) for score, sd in zip(scores, sds)]
    return float(np.sqrt(np.mean(variances)))

def classify_ilo_mean_sd(mean_score, sd_score):
    if mean_score >= 0.60 and mean_score - sd_score >= 0.50:  return "Exposed: Gradient 4"
    if 0.50 <= mean_score < 0.60 and mean_score + sd_score >= 0.50: return "Exposed: Gradient 3"
    ...
```

O índice da OIT tem 427 ocupações ISCO-08, das quais **13 em Gradiente 4** — Data Entry Clerks
(0,70), Typists (0,65), Accounting and Bookkeeping Clerks (0,64), Statistical/Finance/Insurance
Clerks (0,64), Securities and Finance Dealers (0,63), Clerical Support NEC (0,63), Financial
Analysts (0,62), Payroll Clerks (0,61), Contact Centre Salespersons (0,61), General Office Clerks
(0,60), Credit and Loans Officers (0,60), Web and Multimedia Developers (0,60), Personnel Clerks
(0,60).

A ponte MTE alcança 362 das 427 ocupações, **incluindo 11 das 13 de G4**, e **16 CBOs tocam pelo
menos um destino G4** — nenhuma classificada como G4:

| CBO | Título | destinos | média | DP | Gradiente |
|---|---|---:|---:|---:|---|
| 4121 | Operadores de equipamentos de entrada e transmissão de dados | 3 | 0,593 | 0,138 | G3 |
| 4110 | Agentes, assistentes e auxiliares administrativos | 4 | 0,580 | 0,117 | G3 |
| 4122 | Contínuos | 5 | 0,562 | 0,128 | G3 |
| 4131 | Auxiliares de contabilidade | 3 | 0,560 | 0,128 | G3 |
| 2124 | Analistas de tecnologia da informação | 7 | 0,547 | 0,093 | G3 |
| 4223 | Operadores de telemarketing e afins | 2 | 0,535 | 0,164 | G3 |

**Mecanismo:** a regra é assimétrica. G4 exige `média − DP ≥ 0,50`; G1–G3 exigem
`média + DP ≥ 0,50`. Um DP maior dificulta o topo e facilita a base. E o DP usado soma dispersão
entre destinos ISCO à dispersão entre tarefas — verificado: 0,079 para as 207 CBOs de destino único
contra 0,114 para as 229 de múltiplos destinos.

A CBO 4121 corresponde à ISCO 4132, a ocupação mais exposta do índice inteiro, e falha o corte de
média por 0,007 e o de dispersão por 0,045. Nenhuma CBO atinge `média ≥ 0,60`; o teto empírico é
0,593.

**Consequência para o texto:** a §4.2 atribui o G4 vazio à diluição da média sobre destinos
múltiplos. **207 das 436 CBOs (47%) mapeiam para um único destino** — para quase metade não há
diluição alguma, e o que decide é o termo de dispersão. Ver `02` §9.

### 7. Os modelos de fluxo principais falham seus pretrends **[X+C]**

**Severidade: Alto.**

`V1/results/reference/sections4_5/tables/table_a_1_national_main_diagnostics.csv:2` e
`V1/README.md:577` marcam admissões, desligamentos e saldo líquido como pretrend falho.

Coeficientes pós-tratamento nulos ou não nulos não reparam identificação. Linguagem causal geral
sobre efeitos de fluxo não é sustentada pelo desenho atual. Ver `03` §P1.2 para a resposta
construtiva (Rambachan–Roth) em vez de apenas rebaixar a linguagem.

### 8. `tipo_movimentacao` é baixado e nunca usado **[C]**

**Severidade: Alto (oportunidade). Exige re-rodar.**

`COLUNAS_CAGED` inclui `tipo_movimentacao`
(`src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py:122-138`), mas a agregação usa só o saldo
(`:719-749`):

```python
df_adm = df[df['saldo_movimentacao'] == 1]
df_des = df[df['saldo_movimentacao'] == -1]
```

Grep confirma 3 ocorrências no repositório, todas na declaração do SELECT. Zero uso analítico.
Consequências:

- **Transferências entre estabelecimentos contam como admissão e desligamento reais** — uma
  reestruturação societária vira fluxo de mercado de trabalho.
- **Demissão sem justa causa, pedido de demissão e término de contrato são um evento só** — é a
  decomposição que responde à pergunta que o texto declara não conseguir responder.
- **Admissão por primeiro emprego não é isolada** — é a medida mais direta da "porta de entrada",
  que é o enquadramento central do trabalho.

Ver `03` §P2.1 e §P2.2.

---

## Parte II — Moderado

### 9. `full` é uma reconstrução híbrida, não linhagem completa **[X]**

O DAG completo injeta ativos derivados congelados — exposição, IPCA, pares dinâmicos, metadados
ocupacionais (`V1/code/sections4_5/full_pipeline.py:269`, `pipeline.py:202`). O manifesto público
final não carrega URLs de origem, datas de recuperação, hashes brutos, esquemas e linhagem completa
de entrada/saída por estágio. `full` ainda não pode ser interpretado como reconstrução a partir de
fontes brutas identificadas.

### 10. Agrupamento de caudas pool meses heterogêneos **[X+C]**

`V1/.../section4_event_study/estimation.py:175` recorta o tempo de evento em `[-12,+24]`. O
coeficiente `-12` agrupa os meses −23…−12, e `+24` agrupa 24…30. As figuras públicas de janela
estrita usam outra amostra e outro estimando — `section4_5_final/section5_2_dynamic_figures.py:53`
define `WINDOW_RULE = "strict_no_tail_binning"`. É por isso que a Tabela A.1 tem N=18.307 e a
Figura 5.1 tem N=12.538. Os rótulos não comunicam o pooling de forma consistente.

### 11. Contratos de merge e missingness incompletos **[X]**

O painel congelado não tem linhas CBO4-mês duplicadas, mas é **desbalanceado: CBOs individuais têm
entre 8 e 54 meses**. Os gates atuais não verificam sistematicamente cardinalidade de merge,
contagem de não-casados, deltas de linhas, missingness de outcome e de controle, nem suporte em
janela balanceada.

### 12. Definições demográficas divergem entre módulos **[X]**

O painel agregado define superior completo com os códigos `{9,10,11,80}`; um módulo de
heterogeneidade inclui também o `8`. Sexo desconhecido ou ausente entra no denominador como
não-feminino. A categoria `60+` não tem limite superior imposto.

### 13. Fontes do crosswalk não versionadas criptograficamente **[X+C]**

A cadeia institucional é conservadora e proíbe fallback numérico CBO=ISCO — isso é uma força. Mas
`src/scripts/caged_mte_crosswalk.py` raspa `cbo.mte.gov.br/.../FiltroConversao_...jsf` ao vivo, e
o cache existe localmente
(`outputs/crosswalk_audit/source_dictionaries/mte_cbo2002_cbo94_ciuo88_by_family.csv`, 1.550 linhas)
sem ser distribuído no pacote. Contagens esperadas são verificadas; hashes de conteúdo e vintages de
origem não são insumos contratuais públicos.

### 14. Duas regras de winsorização no mesmo trabalho **[C]**

`src/scripts/etapa_2b_analise_did_caged_ilo.py:214-229` winsoriza nos percentis 1 e 99
**incondicionais sobre o painel inteiro** — uma ocupação estruturalmente bem paga é cortada por
comparação com ocupações mal pagas. A Seção 5.3 usa percentis 1 e 99 **dentro de CBO6 × ano**, que
é a regra defensável. Além disso `ln_salario_adm` usa o winsorizado e `ln_salario_real_adm`, o
publicado, usa o bruto.

### 15. As saídas de referência não são âncora independente **[X]**

O pacote compara artefatos regerados com o diretório `results/reference` atual, mas **não valida
antes, criptograficamente, esse diretório contra o `reference_manifest.json`**. A comparação de PNG
usa dimensões e RMS de miniatura em escala de cinza, que pode não detectar mudanças materiais
localizadas. Combinado com o achado 3, é assim que um erro semântico atravessa a suíte inteira.

### 16. Duas definições de tratamento vivas no mesmo arquivo **[C]**

`painel_2b_ready.parquet` carrega simultaneamente `alta_exp` (top 20% do `exposure_score_2d`,
limiar 0,382857, `etapa_2a...py:1460-1497`), que dirige as saídas de `etapa_2b`, e a classificação
por gradiente da OIT, que dirige o que é publicado. As duas **não são aninhadas** — 0,3829 fica
abaixo do `ILO_MINIMAL_EXPOSURE_BOUNDARY = 0.40`. E
`outputs/crosswalk_explanation/caged_crosswalk_explanation.md` ainda descreve a regra P80 obsoleta
como se fosse a definição vigente.

### 17. `--mode full` não roda como distribuído **[X+C]**

`Replication Package/V1/data/raw/{section3,sections4_5}/` contêm só `.gitkeep`. Faltam ~1,9 GB de
parquets do CAGED e quatro arquivos de crosswalk. Só `--mode reproduce` funciona numa máquina
limpa. É defensável, mas o README precisa dizer isso com todas as letras.

### 18. Validação de insumo da Seção 3 incompleta **[X]**

O construtor da Seção 3 ignora valores de período ausentes ao afirmar 2025Q3, e não exige pesos
finitos positivos nem valida o domínio de todo código demográfico.

### 19. `horas_contratuais` nunca foi extraída **[C]**

A tabela do Base dos Dados tem `horas_contratuais`; o `COLUNAS_CAGED` não pede. Todo resultado
salarial é **salário mensal contratual**, que mistura preço da hora e jornada. Uma queda de 2% pode
ser 2% menos por hora, a mesma hora com jornada 2% menor, ou qualquer combinação. Como
`indicador_trabalho_parcial` e `indicador_trabalho_intermitente` também não são extraídos, não há
como separar.

### 20. Colunas baixadas e não usadas **[C]**

| Coluna | Situação | Uso possível |
|---|---|---|
| `categoria` | Baixada, nunca usada | Excluir aprendizes e intermitentes, ou tratá-los à parte |
| `cnae_2_subclasse` | Baixada, nunca usada | CNAE×mês FE; painel CBO×CNAE |
| `tamanho_estabelecimento_janeiro` | Baixada, nunca usada | Heterogeneidade por porte |
| `cnae_2_secao` | Só como binário `== "J"` na Etapa 3a | Idem |

Nunca pedidas: `tipo_empregador` e `tipo_estabelecimento` (separar setor público, que não responde a
pressão competitiva de IA — teste de falsificação barato), `indicador_aprendiz`,
`indicador_fora_prazo`, `origem_informacao`, `tipo_deficiencia`.

### 21. A camada onde estão os bugs não tem teste **[C]**

Os testes são todos contratos sobre `outputs/`. **Nenhum cobre `src/scripts/etapa_2a_*`**, que é
onde estão os achados 1, 4, 8, 14, 16, 19 e 20. O teste mais forte do pacote prova que o mesmo
painel produz o mesmo coeficiente; não prova nada sobre o painel estar certo.

---

## Parte III — Baixo

### 22. Intervalos de confiança do event study usam 1,96 **[C]**

`section4_event_study/estimation.py:258` usa `coef ± 1.96·se`, enquanto os p-valores ao lado vêm do
CRV1 com correção de amostra pequena sobre 341 clusters. Com 341 clusters a diferença é pequena, mas
figura e tabela usam distribuições diferentes.

### 23. Artefatos com nome enganoso congelados por contrato **[X+C]**

Além da A.6 (achado 3): `table_4_2_outcomes.md` contém `lo g ( y + 1 )`, um bug de espaçamento do
formatador matemático agora congelado pela comparação byte-a-byte. E
`build_section4_5_final_package.py` está fora do `FULL_DAG`, mas `pipeline.py:136` exige exatamente
48 arquivos `.py` do autor — código morto congelado por contrato.

### 24. A extensão Anatel foi corretamente excluída **[C]** — sem ação

Registro para não reabrir. A Etapa 3 está completa em código e saídas
(`outputs/dissertation_section4/connectivity_extension/`, 3.557.921 observações, 339 CBOs, 657
municípios) e não aparece na dissertação. A exclusão está certa: os quatro outcomes falham
tendências prévias com p=0,0000; o **placebo temporal de dezembro de 2021 é significativo**
(+0,0469\*\*\*, +0,0509\*\*\*), que é falha de falsificação; e os coeficientes grandes trocam de sinal
na especificação com diagnóstico.

Duas observações caso reconsidere: em `outputs/tables/triple_did_main_etapa3b.csv` as linhas
`ln_salario_mulher/homem/jovem` têm magnitudes compatíveis com contagens, não salários — rótulo
provavelmente trocado. E `section4_connectivity/config.py` lê o painel v1 (4,56 M linhas) enquanto o
cache da 3b é construído sobre o v2 (5,53 M linhas).

---

## Forças confirmadas **[X+C]**

Importa registrar, porque muda o custo da V2.

- Um ponto de entrada, caminhos relativos, dependências fixadas, insumos analíticos congelados,
  papéis de tratamento explícitos, validação automatizada.
- O contraste principal é implementado como 75 CBOs G1–G3 contra 266 `Not Exposed`;
  `Minimal Exposure` e `No score` excluídos.
- DDD estático e dinâmico incluem o triplo e todos os termos de ordem inferior.
- Erros-padrão clusterizados por CBO4.
- A cadeia oficial do crosswalk é explícita e **não equipara exposição ausente a exposição zero**.
- A Seção 3 fixa o SHA-256 da planilha da OIT e reporta cobertura ponderada.
- Testes de segurança destrutiva: `prepare_output_directory` recusa apagar diretório com
  `run_manifest.json` inválido.
- Replicação cruzada Python↔R independente sobre os quatro modelos centrais.

**Isso é infraestrutura acima da média.** É a razão pela qual a V2 é viável: a máquina existe, o que
falta é insumo correto e cobertura de re-estimação.

---

## Conclusão da auditoria

O pacote é útil e substancialmente melhor que um arquivo de notebooks irreprodutível. Mas hoje
combina três conceitos que precisam ser rotulados separadamente — re-estimação, validação de tabela
congelada, e renderização — e a construção dos dados na origem tem um problema não endereçado que é
da mesma ordem de grandeza do efeito estimado.

A V1 deve permanecer congelada como evidência da linha de base submetida. As correções materiais
pertencem à V2, com um vintage de dados novo e um DAG completo de modelo a artefato.

**Índice de severidade**

| # | Achado | Origem | Severidade | Re-rodar? |
|---|---|---|---|---|
| 1 | Fora do prazo e exclusões fora do painel | [C] | **Crítico** | Sim |
| 3 | A.6 semanticamente errada no pacote | [X] | **Crítico** | Não |
| 2 | `reproduce` é renderizador | [X] | Alto | Sim |
| 4 | Fluxo zero com valores artificiais; salários absurdos | [X+C] | Alto | Sim |
| 5 | Controles pós-tratamento no principal | [X+C] | Alto | Sim |
| 6 | G4 vazio por artefato da fórmula | [C] | Alto | Sim |
| 7 | Pretrends dos fluxos falham | [X+C] | Alto | — |
| 8 | `tipo_movimentacao` não usado | [C] | Alto | Sim |
| 9–21 | Moderados | — | Médio | Vários |
| 22–24 | Baixos e sem ação | — | Baixo | — |
