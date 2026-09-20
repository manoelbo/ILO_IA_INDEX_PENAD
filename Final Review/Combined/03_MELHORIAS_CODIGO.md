# 03 — Melhorias no Código (combinadas)

**Regra de decisão.** Ranqueado por impacto científico, não por significância estatística. A V1 é
uma linha de base congelada e não deve ser corrigida silenciosamente. Correções materiais vão para a
V2 e são documentadas mesmo que as estimativas fiquem mais fracas ou nulas.

Origem: **[X]** Codex, **[C]** Claude, **[X+C]** ambos.

- **P0** — corrige erro. Sem isso o resultado não é defensável.
- **P1** — torna o resultado defensável.
- **P2** — torna o resultado mais conclusivo.

---

## P0 — Obrigatório

| # | Mudança | Origem | Impacto | Esforço |
|---|---|---|---|---|
| P0.1 | Incluir MOV + FOR − EXC na ingestão | [C] | Remove o viés diferencial de cobertura | Baixo (BD) / Médio (FTP) |
| P0.2 | Reconstruir missingness de salário: `NA` quando o fluxo é zero; rejeitar salários inválidos antes de agregar | [X+C] | Elimina salários artificiais e controles contaminados | Médio |
| P0.3 | Tirar controles de composição contemporâneos do modelo principal | [X+C] | Remove condicionamento pós-tratamento | Baixo |
| P0.4 | Corrigir a A.6 para usar a fonte de renda; assertar rótulos permitidos e distinção semântica de A.5 | [X] | Elimina uma tabela falsa conhecida | Baixo |
| P0.5 | Re-estimar todo artefato inferencial a partir dos insumos analíticos | [X] | Converte reprodutibilidade de renderização em reprodutibilidade científica | **Alto** |
| P0.6 | Substituir o recorte de caudas por janela balanceada `−23…+23` e horizontes nomeados | [X+C] | Alinha estimando, figura e teste de pretrend | Médio |
| P0.7 | Publicar linhagem completa bruto→saída: URL, data, vintage, checksum, tamanho, schema, hashes por estágio, deltas de linha | [X] | Torna o `full` auditável | Médio |
| P0.8 | Revisar a regra de classificação de gradiente | [C] | Corrige o artefato que esvazia o G4 | Baixo |
| P0.9 | Excluir transferências dos fluxos via `tipo_movimentacao` | [C] | Remove eventos que não são de mercado de trabalho | Baixo |
| P0.10 | Unificar as regras de winsorização | [C] | Elimina dois tratamentos de outlier para a mesma variável | Baixo |

### Detalhe dos itens que exigem explicação

**P0.1 — MOV + FOR − EXC.** No Base dos Dados é uma união de três tabelas com sinal:

```sql
SELECT *,  1 AS peso FROM `basedosdados.br_me_caged.microdados_movimentacao`
UNION ALL SELECT *,  1 FROM `basedosdados.br_me_caged.microdados_movimentacao_fora_prazo`
UNION ALL SELECT *, -1 FROM `basedosdados.br_me_caged.microdados_movimentacao_excluida`
```

Confira antes o schema das três; a de exclusões pode não ter todas as colunas. No FTP, os três
arquivos já vêm separados por competência.

**Entregável obrigatório:** tabela de reconciliação mês a mês, painel antigo × painel novo, e o
modelo antigo rodado nos dois. A diferença entre os dois coeficientes é um resultado publicável — é
a demonstração de que você identificou uma ameaça específica, mediu, e reportou.

**P0.5 — o item mais caro e o mais importante do ponto de vista de pacote.** Hoje só quatro modelos
nacionais são re-estimados. Event studies, pretrends exatos, DDD, PPML, salário real,
heterogeneidades e casos ocupacionais são renderizados de CSVs congelados. Até que isso mude, o
pacote não é autoridade computacional para a maioria das afirmações do texto.

**P0.8 — regra de gradiente.** Três variantes, **todas pré-registradas antes de olhar resultado**:

1. **Média ponderada por emprego** entre destinos ISCO, no lugar de `np.nanmean`
   (`run_treatment_scenario_grid.py:412`). Hoje um destino com 200 vínculos pesa igual a um com
   200 mil.
2. **Separar as duas fontes de dispersão.** Usar o DP entre tarefas da OIT na regra; reportar a
   dispersão entre destinos como métrica de qualidade do crosswalk. Hoje `pooled_equal_weight_sd`
   soma as duas, e como G4 exige `média − DP ≥ 0,50` e G1–G3 exigem `média + DP ≥ 0,50`, o DP
   inflado empurra CBOs para fora do topo.
3. **Classificar no nível do destino ISCO**, onde o gradiente é nativo, e agregar os **rótulos**
   ponderados por emprego — em vez de agregar scores e classificar depois.

**Gate:** ou o G4 deixa de estar vazio, ou você tem uma demonstração de que ele está vazio por razão
substantiva. Qualquer um dos dois resolve o problema do texto (`02` §9). O que não pode continuar é
a explicação atual. **Mantenha o contrato G1–G4 versus `Not Exposed`** e reporte a realização —
isso é do Codex e continua valendo.

**P0.10 — winsorização.** Adotar percentis 1 e 99 **dentro de CBO × ano**, que é a regra que a §5.3
já usa, e aplicar a mesma ao salário nominal e ao real. Hoje `etapa_2b:214-229` usa percentis
incondicionais sobre o painel inteiro para `ln_salario_adm`, enquanto `ln_salario_real_adm` — o
publicado — vem do bruto.

### Higiene junto com o P0

| Item | Alvo | O quê |
|---|---|---|
| Verificação | `V1/code/sections4_5/analysis.py:15-20` | Acrescentar `ln_salario_real_adm` ao `CORE_OUTCOMES`; hoje só o nominal é replicado |
| Artefatos | `V1/code/sections4_5/pipeline.py:241-242`, `contracts.py:223,229` | Renomear `table_a_6_income_*`, gerados da tabela de escolaridade |
| IC do event study | `estimation.py:258` | Usar t com os graus de liberdade do cluster, não 1,96 fixo |
| Tratamento legado | `painel_2b_ready.parquet` | Remover `alta_exp` ou marcá-lo como legado; atualizar `outputs/crosswalk_explanation/`, que descreve a regra P80 obsoleta |
| Cache do crosswalk | `caged_mte_crosswalk.py` | Distribuir `mte_cbo2002_cbo94_ciuo88_by_family.csv` no pacote, com hash |

---

## P1 — Gates metodológicos e de validação

### Estimadores de contagem e salário **[X+C]**

- PPML como modelo preferido para admissões e desligamentos.
- OLS em `log(1+y)` só como estimando secundário. **O argumento não é "muitos zeros"** — são 0,169%
  de células zero na amostra estrita. O argumento é que PPML estima o efeito sobre a média
  condicional em nível, enquanto `log(1+y)` estima efeito sobre variável transformada cujo
  mapeamento para percentual depende da escala da célula.
- Salário real de admissão só onde existe salário válido.
- `asinh(saldo)` como complementar, nunca percentual.
- Registrar convergência, separação, células descartadas, observações, clusters e efeitos fixos de
  todo modelo PPML.

### Construção de dados e merges **[X]**

- Checagens fail-fast de domínio para tipo de movimentação, sexo, raça/cor, escolaridade, idade,
  CBO, CNAE, município, porte e campos de salário.
- Preservar o código feminino explícito `sexo = 3`.
- Definir categorias desconhecidas/ausentes e denominadores **antes** de agregar.
- Assertar unicidade e cardinalidade esperada antes e depois de cada merge.
- Reportar chaves não casadas e ganho/perda de linhas por estágio.
- Exigir meses contínuos e reportar suporte de CBO por janela — o painel atual tem CBOs com **entre
  8 e 54 meses**.
- **Unificar as definições demográficas**: superior completo é `{9,10,11,80}` no painel agregado e
  inclui `8` num módulo de heterogeneidade.

### Tratamento e crosswalk **[X+C]**

- Congelar toda fonte de crosswalk por checksum e data de recuperação.
- Manter `G1–G4 versus Not Exposed` como contraste principal, reportando explicitamente que G4 é
  vazio **se continuar sendo** depois do P0.8.
- Manter `Minimal Exposure` fora do contraste principal.
- Controle ampliado, exposição contínua e benchmark MTE legado só como robustez rotulada.
- **[C]** Promover a exposição contínua de robustez a **especificação paralela** reportada lado a
  lado com a binária: usa toda a informação do índice, não depende dos cortes, e permite um gráfico
  dose-resposta. Se o efeito for monotônico no score, a ausência de uma categoria de topo deixa de
  ser fatal.

### Dinâmica e inferência de subgrupo **[X+C]**

- Estimar pretrends **no modelo e na amostra exatos** do resultado reportado.
- **Não interpretar pretrend não significativo como prova de tendências paralelas.**
- **HonestDiD / Rambachan–Roth** para os modelos lineares compatíveis. Este é o item de maior
  retorno por unidade de esforço do documento. Hoje, quando o pretrend falha, a resposta é rebaixar
  a linguagem para "exploratório". Rambachan–Roth permite dizer "o efeito é negativo desde que a
  violação pós não exceda M vezes a observada no pré". Não há implementação Python madura — rode em
  R (`HonestDiD`) sobre os coeficientes exportados do event study.
- DDD só como `post × tratamento × subgrupo` mais todos os termos de ordem inferior.
- Reportar suporte por célula de subgrupo e ajustar multiplicidade por família de outcome
  (Romano–Wolf ou Benjamini–Hochberg). São ~40 testes sem ajuste hoje.
- Resultados de suporte fino ou pretrend falho permanecem exploratórios.
- **[C]** Falsificação explícita: promover o placebo temporal (`placebo_dec2021`, já existe) a
  exercício reportado no corpo, e acrescentar placebo de grupo por reatribuição aleatória de
  tratamento preservando a distribuição de tamanho. *Alerta:* na extensão Anatel o placebo de
  dez/2021 **falha**. O mesmo teste precisa passar no desenho nacional.

### Efeitos fixos de setor **[X+C]**

`cnae_2_secao` e `cnae_2_subclasse` já estão no parquet e não são usados. Com CNAE×mês, choques
setoriais deixam de ser confundidos com exposição ocupacional. Sujeito a gate de suporte — pode
haver células CBO×CNAE×mês muito finas.

### Integridade de referência e artefato **[X]**

- **Validar `results/reference` contra um manifesto assinado antes de comparar** saídas regeradas.
  Hoje a comparação é contra o diretório atual, o que permitiu que o erro semântico da A.6
  atravessasse a suíte inteira.
- Contratos semânticos para rótulos de tabela, conjuntos de categorias permitidas, unidades,
  tamanhos de amostra e IDs de fonte.
- Substituir a comparação de figura por miniatura pela comparação exata dos dados de backing mais um
  limiar de image-diff significativo.
- Mapear todo número do manuscrito a produtor, especificação, vintage de insumo e hash de saída.

### Testes na camada de construção **[C]**

Nenhum dos testes cobre `src/scripts/etapa_2a_*`, que é onde estão os achados 1, 4, 8, 14, 16, 19 e
20 da auditoria. Adicionar: soma de fluxos por mês contra o agregado oficial do PDET; ausência de
células com salário zero; tipos de movimentação esperados; balanceamento do painel.

---

## P2 — Torna o resultado mais conclusivo **[C]**

> **Nota de divergência.** O Codex recomenda explicitamente *não* adicionar novas famílias de
> outcome. A preocupação é legítima e é sobre garimpo. A distinção que resolve: estes **não são
> novos subgrupos** — são **decomposições de outcomes que já estão no texto**, e respondem a uma
> pergunta que o próprio texto formula e declara não conseguir responder. A disciplina do Codex se
> aplica na forma: pré-registrar antes de olhar, limitar a família, aplicar a mesma correção de
> multiplicidade, reportar suporte. Com isso, entram. Ver a divergência D3 no `00`.

### P2.1 Decompor desligamentos por tipo de movimentação — **maior retorno do plano**

A §5.1 encontra desligamentos caindo e não consegue interpretar: *"o padrão é compatível com menor
movimentação dos fluxos"* — e precisa recuar, porque menor movimentação e destruição de vínculos não
são distinguíveis sem observar o estoque.

`tipo_movimentacao` distingue:

| Família | Interpretação econômica |
|---|---|
| Demissão sem justa causa | Decisão da firma. É onde deslocamento por IA apareceria. |
| Desligamento a pedido | Decisão do trabalhador. Queda indica alternativa externa pior. |
| Término de contrato | Margem de contrato temporário. |
| Aposentadoria e morte | Ruído demográfico — deve sair. |
| Transferência | Não é evento de mercado de trabalho — deve sair (P0.9). |

A interpretação é limpa nos dois sentidos: se caem as **demissões**, as firmas estão retendo —
incompatível com deslocamento, compatível com ajuste pela porta de entrada. Se caem os **pedidos**,
é o trabalhador segurando o emprego — deterioração da alternativa externa nas ocupações expostas,
resultado mais forte e mais próximo do que a literatura vem encontrando. Qualquer um dos dois
resolve a ambiguidade central do trabalho.

### P2.2 Isolar admissões de primeiro emprego e de aprendiz

O enquadramento do trabalho é a **porta de entrada**, hoje aproximada por faixa etária — que o seu
próprio `final_review_planning.md` §3 proíbe de traduzir como senioridade ou tempo de casa.

`tipo_movimentacao` tem "admissão por primeiro emprego": a medida direta de entrada no mercado
formal, sem supor nada sobre idade. E `indicador_aprendiz` identifica contratos de aprendizagem, a
porta de entrada juvenil institucionalizada no Brasil. É a tradução mais fiel possível do exercício
de referência para o contexto brasileiro — e usa uma variável que os autores americanos não têm.

### P2.3 Proxy de estoque por saldo acumulado

"O CAGED não observa o estoque" aparece ao longo de toda a Seção 5 e é a maior limitação declarada.
É contornável. Três rotas, em ordem de custo:

1. **Índice normalizado.** Acumular o saldo mensal por CBO desde jan/2021 e normalizar em 100 na
   base. Não dá nível absoluto, mas dá exatamente o objeto que Brynjolfsson et al. estimam — emprego
   relativo — e torna a comparação direta em vez de aproximada. **Quase gratuito.**
2. **Ancoragem na RAIS.** Estoque por CBO em dez/2020, acumulando o saldo em cima. Dá nível. Custo:
   baixar e processar a RAIS. *Fora do escopo recomendado.*
3. **Validação externa com a PNADc.** O painel de 16 trimestres em
   `archive/etapa5_did_ocupacional/data/raw/pnad_panel_2021q1_2024q4.parquet` (2.955.122 linhas) mede
   estoque de ocupados diretamente, e o crosswalk COD→ISCO tem 99,2% de cobertura contra 69,3% do
   CBO. Um DiD trimestral por COD sobre estoque de ocupados é validação independente do resultado do
   CAGED — e cobre **informais**, a outra grande limitação do trabalho. **É o exercício mais valioso
   do plano se houver energia.**

### P2.4 Salário-hora

Extrair `horas_contratuais` e reportar salário por hora ao lado do mensal. Sem isso, uma queda de 2%
pode ser preço, jornada, ou os dois. Com `indicador_trabalho_parcial` e
`indicador_trabalho_intermitente`, dá para separar as margens.

### P2.5 Heterogeneidade por porte e natureza do empregador

`tamanho_estabelecimento_janeiro` já está no parquet; `tipo_empregador` e `tipo_estabelecimento` são
de extrair.

- **Porte:** adoção de IA é fortemente graduada por tamanho. Se o efeito se concentra em
  estabelecimentos grandes, é evidência indireta de que o canal é adoção — que o desenho hoje não
  observa.
- **Público vs privado:** emprego público não responde a pressão competitiva de IA. Se o efeito
  aparece no privado e não no público dentro das mesmas ocupações expostas, é um teste de
  falsificação forte e barato.

### P2.6 Sensibilidade da medida de exposição

Três testes quase gratuitos, com colunas que já estão na planilha da OIT:

1. **Vintage 2023** (`mean_score_2023`, `SD_2023`, `potential23`) contra o de 2025.
2. **Discordância entre modelos**: `predicted_score_2025_gpt4o` vs `predicted_score_2025_gemini`. A
   divergência é medida direta de erro de medida do índice; restringir às ocupações onde os dois
   concordam é robustez natural.
3. **Concordância com índices concorrentes**: correlação de postos com o índice da Anthropic no
   nível da CBO, usando `data/processed/anthropic_automation_augmentation_cbo.parquet`. Preenche
   também a lacuna §14 da auditoria de texto.

---

## Testes que devem virar gates de release **[X]**

1. A.6 contém só as faixas de renda pré-especificadas e tem o hash de fonte correto.
2. Salário é ausente sempre que o fluxo correspondente é zero.
3. Salários inválidos e implausíveis são reportados e tratados antes da agregação.
4. A fórmula principal não contém controles de composição contemporâneos.
5. Toda tabela inferencial tem um teste de estimador vivo, não só um arquivo de backing copiado.
6. Os horizontes do event study são completos e nunca recortados.
7. Todo merge reporta unicidade, status de casamento e deltas de linha.
8. Fixtures de códigos demográficos incluem valores desconhecidos e ausentes.
9. Python e R concordam em observações, coeficientes e erros-padrão a pelo menos seis decimais.
10. Todos os arquivos de referência batem com o manifesto imutável.
11. **[C]** Os totais mensais de fluxo reconciliam com o agregado oficial do PDET — este é o gate
    que teria pegado o achado do fora do prazo.

---

## Ordem de execução

```
P0.1 fora do prazo ─┐
P0.9 transferências ─┼─→ painel reconstruído ─→ GATE: reconciliação vs painel antigo  ★
P0.2 missingness    ─┘                                    │
                                                          ▼
P0.8 gradiente ─────────────→ GATE: G4 preenchido ou explicado
                                                          │
                                                          ▼
P0.3 controles + P0.6 janela + P0.10 winsor ──→ modelo principal re-estimado
                                                          │
                                                          ▼
P0.4 A.6 + P0.5 re-estimação completa + P0.7 linhagem
                                                          │
                                                          ▼
P1: PPML → contínuo → CNAE×mês → HonestDiD → multiplicidade → placebo → integridade
                                                          │
                                                          ▼
P2: tipos de desligamento → primeiro emprego → estoque → salário-hora → porte → medida
```

O gate depois de P0.1 é o mais importante. Se a reconciliação mostrar que o coeficiente muda pouco,
a Seção 5 sobrevive quase intacta. Se mudar muito, você descobre antes de investir no resto.

---

## Onde não gastar tempo agora **[X]**

- refatoração cosmética de módulos já legíveis;
- renomear todo identificador de schema interno legado;
- **novas dimensões de heterogeneidade** que não estão na dissertação (note: os P2 acima não são
  novas dimensões, são decomposições de outcomes existentes — ver a nota de divergência);
- ajustar modelos para recuperar significância;
- expandir a estrutura de capítulos.
