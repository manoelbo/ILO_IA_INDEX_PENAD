# 03 — Melhorias no Código

Organizado em três faixas por retorno, não por esforço.

- **P0** — corrige erro. Sem isso o resultado não é defensável.
- **P1** — torna o resultado defensável. Fecha as portas que um parecerista abre.
- **P2** — torna o resultado mais conclusivo. É aqui que mora a chance de achado novo.

Cada item traz alvo, o que fazer, esforço relativo e se muda número publicado.

---

## P0 — Corrige erro

### P0.1 Incluir movimentações fora do prazo e subtrair exclusões

**Alvo:** `src/scripts/etapa_2a_preparacao_dados_did_caged_ilo.py:436-455` (a query de extração).
**Muda número:** sim, provavelmente o mais.
**Esforço:** baixo no Base dos Dados; médio se for pelo FTP.

O painel deve ser MOV + FOR − EXC. Hoje é só MOV, e a fração omitida cai de 8,61% (2021) para
1,29% (2024) — ver `01_AUDITORIA_CODIGO.md` §1.

No Base dos Dados, é uma união de três tabelas com um sinal:

```sql
SELECT *, 1 AS peso_registro FROM `basedosdados.br_me_caged.microdados_movimentacao`
UNION ALL
SELECT *, 1 FROM `basedosdados.br_me_caged.microdados_movimentacao_fora_prazo`
UNION ALL
SELECT *, -1 FROM `basedosdados.br_me_caged.microdados_movimentacao_excluida`
```

Confira antes o schema das três — a de exclusões pode não ter todas as colunas. Se a V2 for pelo
FTP do MTE, os três arquivos já vêm separados por competência.

**Entregável obrigatório:** uma tabela de reconciliação mês a mês, painel antigo × painel novo, e
o modelo principal rodado nos dois. A diferença entre os dois coeficientes é um resultado que vale
publicar num apêndice — mostra que você testou e quantificou uma ameaça específica.

### P0.2 Revisar a regra de classificação de gradiente

**Alvo:** `src/scripts/run_treatment_scenario_grid.py:168-190` e `:412`.
**Muda número:** sim, muda a composição dos grupos.
**Esforço:** baixo.

Três mudanças, todas a serem **pré-registradas antes de olhar o resultado**:

1. **Média ponderada por emprego entre destinos ISCO**, no lugar de `np.nanmean`. Hoje um destino
   ISCO com 200 vínculos no Brasil pesa igual a um com 200 mil.
2. **Separar as duas fontes de dispersão.** Usar o DP entre tarefas da OIT na regra de gradiente;
   reportar a dispersão entre destinos como métrica de qualidade do crosswalk, não como parte do
   score. Hoje `pooled_equal_weight_sd` soma as duas, e como o G4 exige `média − DP ≥ 0,50`
   enquanto G1–G3 exigem `média + DP ≥ 0,50`, o desvio inflado empurra CBOs para fora do G4 e para
   dentro dos gradientes baixos.
3. **Alternativa a testar:** classificar no nível do destino ISCO, onde o gradiente é nativo, e
   agregar os rótulos ponderados por emprego — em vez de agregar scores e classificar depois.

As três entram na grade de sensibilidade. Se o G4 continuar vazio depois disso, aí sim a
explicação da §4.2 está certa e você tem como demonstrar.

### P0.3 Tirar os controles contemporâneos da especificação principal

**Alvo:** `src/scripts/section4_event_study/config.py` e `estimation.py:72-74`.
**Muda número:** sim — o salário de admissão vai de −0,0207 (p=0,140) para −0,0251 (p=0,086).
Mas atenção: a variante com controles pré-tratamento interagidos dá **−0,0217 com p=0,251**, menos
significativa que as duas. Faça a troca porque é o correto, não esperando que resolva significância.
**Esforço:** baixo. A infraestrutura já existe (`post_pre_*` em `data.py:95-125`).

Hierarquia final:

1. Principal: sem controles de composição contemporâneos.
2. Robustez: características pré-tratamento interagidas com tempo calendário.
3. Descritiva condicional: com controles contemporâneos, rotulada como potencialmente
   pós-tratamento e explicitamente **não** interpretada como efeito total.

E nunca usar composição contemporânea dos admitidos como controle preferido para outcomes de
desligamento — isso não tem defesa.

### P0.4 Excluir transferências dos fluxos

**Alvo:** `etapa_2a...py:719-749`.
**Muda número:** sim, em magnitude a verificar.
**Esforço:** baixo — a coluna já está no parquet.

Hoje admissão é `saldo_movimentacao == 1` e desligamento é `== -1`, sem olhar
`tipo_movimentacao`. Transferências entre estabelecimentos do mesmo grupo entram como admissão e
desligamento reais. Filtrar por tipo antes de agregar.

### P0.5 Unificar as regras de winsorização

**Alvo:** `etapa_2b...py:214-229` e `section4_event_study/data.py:85-86`.
**Muda número:** possivelmente.
**Esforço:** baixo.

Adotar uma regra só, e a defensável é a que a §5.3 já usa: percentis 1 e 99 **dentro de
CBO × ano**, não incondicional sobre o painel inteiro. E aplicar a mesma regra ao salário nominal
e ao real — hoje `ln_salario_adm` usa o winsorizado e `ln_salario_real_adm`, que é o publicado,
usa o bruto.

### P0.6 Unificar a convenção de janela do event study

**Alvo:** `section4_event_study/estimation.py:177` (agrupa caudas em ±12/24) e
`section4_5_final/section5_2_dynamic_figures.py:53` (`strict_no_tail_binning`).
**Muda número:** sim, no N e nos p-valores dos pretrends.
**Esforço:** baixo.

Adotar janela balanceada sem agrupamento de caudas, conforme o seu `final_review_planning.md` §2.5,
e reportar o longo prazo em horizontes nomeados. Isso resolve de uma vez a discrepância entre a
Tabela A.1 (N=18.307) e a Figura 5.1 (N=12.538).

### P0.7 Correções de higiene

| Item | Alvo | O quê |
|---|---|---|
| `.fillna(0)` | `etapa_2a...py:759-763` | Preencher zero só nas contagens; salário e composição viram NaN quando o fluxo é zero. Afeta 63 células — corrija por correção, não por impacto. |
| IC do event study | `estimation.py:258` | Usar t com os graus de liberdade do cluster, não 1,96 fixo. |
| Verificação | `V1/code/sections4_5/analysis.py:15-20` | Acrescentar `ln_salario_real_adm` ao `CORE_OUTCOMES` — hoje só `ln_salario_adm` é replicado, e o publicado é o real. |
| Artefatos | `V1/code/sections4_5/pipeline.py:241-242` e `contracts.py:223,229` | Renomear `table_a_6_income_*_diagnostics`, que são gerados de `table_5_2_6_heterogeneity_education.csv`. |
| Definição de tratamento | `painel_2b_ready.parquet` | Remover `alta_exp` do parquet ou marcá-lo explicitamente como legado; atualizar `outputs/crosswalk_explanation/`, que ainda descreve a regra P80 obsoleta. |
| Cache do crosswalk | `caged_mte_crosswalk.py` | Distribuir `mte_cbo2002_cbo94_ciuo88_by_family.csv` no pacote, com hash. |

---

## P1 — Torna o resultado defensável

### P1.1 PPML como estimador principal para contagens

**Muda número:** sim.
**Esforço:** baixo — `pf.fepois` já é usado na robustez.

Admissões, desligamentos e fluxo bruto passam a ser estimados por PPML com efeitos fixos e erros
clusterizados; `log(y+1)` vira secundário. Reportar efeito como `100 × (exp(β) − 1)`.

Nota importante: o argumento **não** é "muitos zeros" — o painel tem 0,27% de zeros. O argumento é
que PPML estima o efeito sobre a média condicional em nível, que é o estimando de interesse,
enquanto `log(y+1)` estima um efeito sobre uma variável transformada cujo mapeamento para
percentual depende da escala da célula. Com admissões variando de 3 a milhares por célula, isso
não é detalhe.

### P1.2 HonestDiD / Rambachan–Roth para os outcomes com pretrend falho

**Muda número:** não muda os pontos; acrescenta limites.
**Esforço:** médio. Não há implementação Python madura — é caso de rodar em R (`HonestDiD`) sobre
os coeficientes do event study exportados.

Este é o item de maior retorno por unidade de esforço do documento inteiro. Hoje, quando o teste de
tendências paralelas falha, a resposta do trabalho é rebaixar a linguagem para "exploratório".
Rambachan e Roth dão a alternativa: assumir que a violação pós-tratamento é no máximo M vezes a
violação pré-tratamento observada, e reportar o intervalo do efeito em função de M. Você sai de
"não posso concluir nada" para "o efeito é negativo desde que a violação de tendência não seja mais
que 1,5 vez a observada no pré".

Como bônus, resolve o problema que Roth (2022) aponta: condicionar a interpretação no resultado de
um pré-teste distorce a inferência — que é exatamente o procedimento atual.

### P1.3 Correção por testes múltiplos

**Muda número:** sim, nos p-valores da heterogeneidade.
**Esforço:** baixo (Benjamini-Hochberg) a médio (Romano-Wolf com bootstrap).

São cinco dimensões de heterogeneidade × quatro outcomes × contrastes DDD — da ordem de 40 testes
sem ajuste, o que o próprio texto reconhece. Pré-especificar a família (sugestão: os contrastes DDD
dos quatro outcomes principais nas cinco dimensões) e reportar p ajustado ao lado do p nominal.

Isso vai enfraquecer alguns achados. É o preço de poder chamar os que sobreviverem de robustos.

### P1.4 Falsificação explícita

**Muda número:** não.
**Esforço:** baixo — o cenário `placebo_dec2021` já existe.

Promover o placebo temporal de resultado de robustez a exercício de falsificação reportado no
corpo. Acrescentar um placebo de grupo: reatribuir tratamento aleatoriamente entre CBOs preservando
a distribuição de tamanho, muitas vezes, e verificar onde o coeficiente observado cai na
distribuição.

Observação: na extensão Anatel o placebo de dez/2021 **falha** (+0,0469\*\*\*). Isso é um alerta —
o mesmo teste precisa passar no desenho nacional para a interpretação se sustentar.

### P1.5 Exposição contínua como especificação paralela

**Muda número:** acrescenta.
**Esforço:** baixo — o cenário já existe como robustez.

O score contínuo padronizado usa toda a informação do índice, não depende dos cortes de gradiente,
e permite um gráfico dose-resposta que é muito mais persuasivo que uma comparação binária. Deve
subir de robustez para especificação paralela reportada lado a lado com a binária.

Isso também contorna parcialmente o problema do G4 vazio: se o efeito for monotônico no score, a
ausência de uma categoria de topo deixa de ser fatal.

### P1.6 Efeitos fixos de setor × mês

**Muda número:** sim.
**Esforço:** médio — exige reconstruir o painel em CBO × CNAE × mês.

`cnae_2_secao` e `cnae_2_subclasse` já estão no parquet e não são usados. Com CNAE×mês, choques
setoriais deixam de ser confundidos com exposição ocupacional — hoje, se o setor financeiro teve um
ciclo próprio, isso entra inteiro no coeficiente. Atenção ao suporte: pode haver células
CBO×CNAE×mês muito finas, e a tabela de suporte precisa ser reportada.

### P1.7 Testes na camada de construção

**Muda número:** não.
**Esforço:** baixo.

Nenhum dos 138 testes cobre `etapa_2a`, que é onde estão os achados 1, 4, 5, 8 e 9 da auditoria. O
teste mais forte do pacote prova que o mesmo painel produz o mesmo coeficiente — não prova nada
sobre o painel estar certo. Adicionar testes de: soma de fluxos por mês contra o agregado oficial
do PDET; ausência de células com salário zero; tipos de movimentação esperados; e balanceamento do
painel.

---

## P2 — Torna o resultado mais conclusivo

Estes são os exercícios com maior chance de produzir achado novo. Todos saem dos microdados que
você já vai reprocessar — nenhum exige base nova.

### P2.1 Decompor desligamentos por tipo de movimentação

**Este é o item de maior retorno do plano inteiro.**

A dissertação encontra desligamentos caindo e não consegue interpretar. A §5.1 diz: *"como
admissões e desligamentos caem simultaneamente, o padrão é compatível com menor movimentação dos
fluxos"* — e depois precisa recuar, porque menor movimentação e destruição de vínculos não são
distinguíveis sem observar o estoque.

`tipo_movimentacao` distingue, entre outros:

| Família | Interpretação econômica |
|---|---|
| Demissão sem justa causa | Decisão da firma. É aqui que deslocamento por IA apareceria. |
| Desligamento a pedido | Decisão do trabalhador. Queda indica mercado mais frouxo ou menor confiança em recolocação. |
| Término de contrato | Margem de contrato temporário. |
| Aposentadoria e morte | Ruído demográfico, deve sair. |
| Transferência | Não é evento de mercado de trabalho, deve sair (ver P0.4). |

O teste é direto e a interpretação é limpa nos dois sentidos:

- Se os desligamentos caem porque **demissões sem justa causa** caem → as firmas estão retendo, o
  que é incompatível com deslocamento e compatível com ajuste pela porta de entrada.
- Se caem porque **pedidos de demissão** caem → é o trabalhador que está segurando o emprego, o
  que indica deterioração da alternativa externa nas ocupações expostas — um resultado bem mais
  forte e mais próximo do que a literatura de IA vem encontrando.

Qualquer um dos dois é publicável e resolve a ambiguidade central do trabalho.

### P2.2 Isolar admissões de primeiro emprego e de aprendiz

O enquadramento da dissertação, herdado de Brynjolfsson, Chandar e Chen, é a **porta de entrada**.
Hoje isso é aproximado por faixa etária — que o próprio `final_review_planning.md` §3 corretamente
proíbe de traduzir como senioridade ou tempo de casa.

`tipo_movimentacao` tem "Admissão por primeiro emprego": a medida direta de entrada no mercado
formal, sem precisar supor nada sobre idade. E `indicador_aprendiz` (a extrair) identifica contratos
de aprendizagem, que é a porta de entrada juvenil institucionalizada no Brasil.

Um DiD sobre admissões de primeiro emprego em ocupações expostas é a tradução mais fiel possível do
exercício de referência para o contexto brasileiro, e usa uma variável que os autores americanos
não têm.

### P2.3 Proxy de estoque por saldo acumulado

A frase "o CAGED não observa o estoque" aparece, em variações, ao longo de toda a Seção 5 e é a
maior limitação declarada do trabalho. Ela é contornável.

O saldo acumulado desde uma base é uma medida de **variação de estoque** por CBO. Ancorado num
nível inicial, vira índice de emprego. Três rotas, em ordem de custo:

1. **Índice normalizado.** Acumular o saldo mensal por CBO a partir de jan/2021 e normalizar em 100
   na base. Não dá nível absoluto, mas dá exatamente o objeto que Brynjolfsson et al. estimam —
   emprego relativo — e torna a comparação com o artigo de referência direta em vez de aproximada.
2. **Ancoragem na RAIS.** Estoque por CBO em dez/2020 da RAIS, acumulando o saldo do CAGED em
   cima. Dá nível. Custo: baixar e processar a RAIS.
3. **Validação externa com a PNADc.** O painel de 16 trimestres em
   `archive/etapa5_did_ocupacional/data/raw/pnad_panel_2021q1_2024q4.parquet` (2.955.122 linhas)
   mede estoque de ocupados diretamente, e o crosswalk COD→ISCO tem 99,2% de cobertura contra 69,3%
   do CBO. Um DiD trimestral por COD sobre estoque de ocupados é uma validação independente do
   resultado do CAGED — e cobre também informais, que é a outra grande limitação do trabalho.

A rota 1 é quase gratuita e já melhora muito o texto. A rota 3 é o exercício mais valioso do
documento inteiro se você tiver energia, porque ataca as duas maiores limitações declaradas
(estoque e informalidade) com dado que já está no disco.

### P2.4 Salário-hora

Extrair `horas_contratuais` e reportar salário por hora ao lado do salário mensal. Sem isso, uma
queda de 2% no salário de admissão pode ser preço, jornada, ou os dois. Com
`indicador_trabalho_parcial` e `indicador_trabalho_intermitente`, dá para separar a margem de
jornada da margem de preço — que é uma decomposição que a literatura de referência discute e o
trabalho hoje não consegue endereçar.

### P2.5 Heterogeneidade por porte e por natureza do empregador

`tamanho_estabelecimento_janeiro` já está no parquet. `tipo_empregador` e `tipo_estabelecimento`
são de extrair. Dois usos:

- **Porte**: adoção de IA é fortemente graduada por tamanho de firma. Se o efeito se concentra em
  estabelecimentos grandes, isso é evidência indireta de que o canal é adoção — que é exatamente o
  que o desenho hoje não observa.
- **Setor público vs privado**: emprego público não responde a pressão competitiva de IA. Se o
  efeito aparece no privado e não no público dentro das mesmas ocupações expostas, é um teste de
  falsificação forte e barato.

### P2.6 Sensibilidade da medida de exposição

Três testes quase gratuitos, todos usando colunas que já estão na planilha da OIT:

1. **Vintage 2023 do índice** (`mean_score_2023`, `SD_2023`, `potential23`) contra o de 2025.
2. **Discordância entre modelos**: `predicted_score_2025_gpt4o` vs `predicted_score_2025_gemini`.
   A divergência é uma medida direta de erro de medida do índice, e restringir a amostra às
   ocupações onde os dois modelos concordam é um teste de robustez natural.
3. **Concordância com índices concorrentes**: correlação de postos com o índice da Anthropic no
   nível da CBO, usando `data/processed/anthropic_automation_augmentation_cbo.parquet`. Isso também
   preenche a lacuna T6 da auditoria de texto.

---

## Ordem de execução sugerida

```
P0.1 fora do prazo ─┐
P0.4 transferências ─┼─→ painel reconstruído ─→ reconciliação vs painel antigo (GATE)
P0.7 fillna         ─┘                              │
                                                    ▼
P0.2 gradiente ──────────────────→ classificação revista (GATE: G4 preenchido ou explicado)
                                                    │
                                                    ▼
P0.3 controles + P0.5 winsor + P0.6 janela ──→ modelo principal re-estimado
                                                    │
                                                    ▼
P1.1 PPML → P1.5 contínuo → P1.6 CNAE×mês → P1.2 HonestDiD → P1.3 multiplicidade → P1.4 placebo
                                                    │
                                                    ▼
P2.1 tipos de desligamento → P2.2 primeiro emprego → P2.3 estoque → P2.4/2.5/2.6
```

O gate depois de P0.1 é o mais importante. Se a reconciliação mostrar que o coeficiente muda
pouco, a Seção 5 sobrevive quase intacta e o resto vira melhoria incremental. Se mudar muito, você
descobre isso antes de investir no resto.
