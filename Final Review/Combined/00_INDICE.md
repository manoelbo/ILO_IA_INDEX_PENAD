# Revisão Final — Versão Combinada

**Data:** 25 de julho de 2026
**Fontes:** `Final Review/Codex/` e `Final Review/Claude/`, duas auditorias independentes do
mesmo material
**Objeto:** Dissertação "Exposição ocupacional à IA e emprego formal no Brasil" — texto, código e
replication package

---

## O que é este conjunto

Duas auditorias independentes rodaram sobre o mesmo trabalho. Elas convergiram em várias coisas,
divergiram em algumas, e — mais importante — **cada uma encontrou coisas que a outra não viu**.
Este conjunto reúne o melhor dos dois, resolve as divergências, e marca a origem de cada achado
para você poder voltar ao documento original.

Notação usada em todos os arquivos:

| Marca | Significado |
|---|---|
| **[X]** | Achado do Codex |
| **[C]** | Achado do Claude |
| **[X+C]** | Os dois chegaram nele de forma independente — sinal forte |
| **[!]** | Os dois discordaram; a resolução está no texto |

## Arquivos

| # | Arquivo | Conteúdo |
|---|---|---|
| 00 | `00_INDICE.md` | Este arquivo. Método, resumo, e o mapa de divergências. |
| 01 | `01_AUDITORIA_CODIGO.md` | 24 achados de código e pacote, unificados por severidade. |
| 02 | `02_AUDITORIA_TEXTO.md` | 20 achados de texto, estrutura, render e bibliografia. |
| 03 | `03_MELHORIAS_CODIGO.md` | P0/P1/P2 combinados, com gates de release. |
| 04 | `04_MELHORIAS_TEXTO.md` | Correções priorizadas, com ordem de trabalho. |
| 05 | `05_PLANO_V2.md` | Plano da V2: contrato do Codex + ingestão e novos outcomes do Claude. |
| 06 | `06_CONCLUSAO_RECOMENDACAO.md` | **Comece aqui.** Veredito reconciliado e o que fazer amanhã. |

---

## Veredito combinado

**Não circular o PDF atual.** Existe um erro factual na primeira página, uma quebra entre o
Apêndice A.6 do texto e o do pacote, links quebrados, e uma lista de referências incompleta.
Nada disso exige nova pesquisa — mas exige uma rodada de correção antes de qualquer envio.

**Fazer a V2.** Os dois conjuntos chegaram nisso por caminhos diferentes e concordam. O Codex
chega por reprodutibilidade e semântica de construção; o Claude chega por integridade dos dados de
origem. As duas razões são suficientes sozinhas.

**A V2 pode começar hoje.** Este é o ponto onde os dois conjuntos divergiam e onde a combinação
resolve — ver a divergência D1 abaixo.

---

## Os cinco achados que mais importam

Em ordem de gravidade, com a origem marcada.

### 1. As declarações fora do prazo estão fora do painel **[C]**

O pipeline consulta só `microdados_movimentacao`. As tabelas `..._fora_prazo` (8,6 milhões de
registros) e `..._excluida` (607 mil) nunca entram. A fração omitida cai de **8,61% em 2021 para
1,29% em 2024**, e a queda difere entre grupos ocupacionais em cerca de 2 pontos percentuais entre
tratados e controles — num efeito estimado de 3–4%. Produz mecanicamente o sinal e a falha de
tendência paralela que a §5.1 reporta. Detalhe em `01` §1.

### 2. O `reproduce` é, em boa parte, um renderizador de saídas congeladas **[X]**

Só quatro modelos nacionais são re-estimados. Event studies, pretrends, DDD, heterogeneidades,
Poisson, salário real e casos ocupacionais são copiados ou renderizados a partir de CSVs
congelados. O sucesso do `reproduce` prova integridade de empacotamento, não reconstrução
científica. Detalhe em `01` §2.

### 3. O Apêndice A.6 do texto e o do pacote são objetos diferentes **[X]**

Os artefatos chamados `table_a_6_income_*` são gerados a partir de
`table_5_2_6_heterogeneity_education.csv`. As linhas produzidas são categorias de escolaridade, não
faixas de renda. Os testes passam porque o diretório de referência contém a mesma saída errada —
**a identidade byte-a-byte validou um erro semântico**. Detalhe em `01` §3.

### 4. Células de fluxo zero recebem salários artificiais, e valores absurdos sobrevivem **[X+C]**

62 células com zero admissões carregam o mesmo salário médio positivo (R$ 1.104,7868), das quais 31
entram na amostra principal, com controles demográficos zerados. Salários de desligamento chegam a
~R$ 203,3 milhões, com sete células acima de R$ 1 milhão **dentro da amostra principal**. Detalhe
em `01` §4.

### 5. O resumo da primeira página tem um erro factual **[X]**

A linha 5 diz "cerca de 10% da força de trabalho **formal**". Os números do próprio trabalho são
10,1% da população ocupada total e **14,8%** dos formais. Verificado nas linhas 5 e 21 do
Markdown. Detalhe em `02` §1.

---

## Mapa das divergências

### D1 — A V2 pode começar hoje? **[!]**

**Codex:** NO-GO. O contrato exige 15–20 GiB livres; há 8,45 GiB. "Nenhum dado do autor pode ser
apagado para satisfazer esse gate."

**Claude:** o gate abre sem apagar nada insubstituível. Existem **4,2 GB** em painéis municipais
**derivados** que pertencem à extensão Anatel, documentada como excluída da dissertação:
`painel_caged_municipio.parquet` (962 MB), `painel_3b_df_reg.parquet` (774 MB),
`painel_caged_municipio_anatel_v2.parquet` (766 MB), `painel_section4_connectivity_ready.parquet`
(734 MB), `painel_caged_municipio_anatel.parquet` (514 MB), `painel_3b_df_ext.parquet` (390 MB),
`section4_connectivity_canaries_age_outcomes.parquet` (172 MB).

**Resolução:** os dois estão certos dentro da própria premissa. Painel derivado não é dado do
autor — é cache reconstruível a partir de `data/raw/` e dos scripts, que permanecem no repositório.
Removê-los leva o espaço de 8,5 GiB para ~12,7 GiB. Somando os 94 MB do CSV bruto do Anthropic
Economic Index, que alimenta um derivado de 11,5 KB, o gate abre.

Além disso, o plano de ingestão do `05` é mais leve do que 15–20 GiB: processando competência a
competência com descarte, o pico fica em 1–2 GB. **O gate de armazenamento está aberto.**

### D2 — O Gradiente 4 vazio é força ou defeito? **[!]**

**Codex:** lista "nenhuma CBO4 em G4, e o código expõe esse fato" entre as **forças confirmadas**,
e recomenda manter o contrato reportando que G4 é vazio.

**Claude:** o G4 está vazio por artefato da fórmula. A ponte alcança 11 das 13 ocupações ISCO-08
que a OIT classifica como G4, e 16 CBOs tocam pelo menos uma. A regra é assimétrica — G4 exige
`média − desvio ≥ 0,50` enquanto G1–G3 exigem `média + desvio ≥ 0,50` — e o desvio usado soma
dispersão entre destinos à dispersão entre tarefas. A CBO 4121 (entrada de dados) corresponde à
ocupação mais exposta do índice inteiro (0,70) e sai como G3, falhando o corte por 0,007.

**Resolução:** as duas coisas são verdade e não se contradizem. É uma força que o código exponha o
fato; é um defeito que a §4.2 explique o fato pela razão errada. **Mantenha o contrato do Codex**
(G1–G4 versus Not Exposed, reportando a realização G1–G3) **e acrescente o diagnóstico do Claude**
como sensibilidade pré-registrada. Ver `03` §P1.8.

### D3 — Entram novos outcomes? **[!]**

**Codex:** não. "Sem novas famílias de outcome, sem novas buscas de subgrupo." Os metadados extras
entram como *validação*, não como resultado.

**Claude:** sim — decomposição de desligamentos por tipo de movimentação, admissões de primeiro
emprego, e proxy de estoque. Você aprovou isso explicitamente.

**Resolução:** a preocupação do Codex é legítima e é sobre garimpo. Mas a distinção que importa é
outra: esses não são **novos subgrupos**, são **decomposições de um outcome que já está no texto**,
e respondem a uma pergunta que o próprio texto formula e declara não conseguir responder
("menor rotatividade ou destruição de vínculos?"). A disciplina do Codex se aplica na forma:
pré-registrar antes de olhar, limitar a família, aplicar a mesma correção de multiplicidade, e
reportar suporte. Com isso, entram. Ver `03` §P2 e `05` §3, WP7.

### D4 — Quão grave é o bug do `fillna`? **[!]**

**Codex:** major. **Claude:** baixo (63 de 23.319 células, 0,27%).

**Resolução:** o Codex está certo e a medida do Claude estava no estágio errado do pipeline. O
Claude mediu `painel_caged_did_ready.parquet` (pré-winsorização), onde as células aparecem como
zero. O Codex mediu o painel de estimação (pós-winsorização), onde o piso substituiu o zero por
R$ 1.104,7868 — um salário **positivo e plausível**, que passa despercebido em qualquer inspeção
visual, e 31 dessas células entram na amostra principal. Some a isso os salários de desligamento
de até R$ 203 milhões que o Codex encontrou. **Severidade: alta.** Adotado o diagnóstico do Codex.

---

## Onde os dois convergiram

Convergência independente é o sinal mais forte que este exercício produz. Os dois conjuntos, sem se
consultarem, chegaram a:

- Controles de composição contemporâneos são potencialmente pós-tratamento e não devem ser a
  especificação principal.
- PPML como estimador principal para contagens; `log(1+y)` como secundário.
- A justificativa de "muitos zeros" para `log(y+1)` é falsa.
- Janela de evento balanceada, sem agrupamento de caudas, com horizontes nomeados.
- Pretrends estimados sobre o modelo e a amostra exatos do resultado reportado.
- Correção de multiplicidade por família de outcome.
- HonestDiD / Rambachan–Roth onde compatível.
- DDD só com o triplo explícito e todos os termos de ordem inferior.
- A estrutura de capítulos não muda.
- Linguagem causal e de estoque precisa ser contida em vários pontos.
- A V1 deve permanecer congelada; correções vão para a V2.

Boa parte disso já estava no seu `final_review_planning.md`, o que significa que seu próprio
diagnóstico estava certo — o que faltava era execução e os achados de origem dos dados.

---

## O que cada conjunto trouxe de exclusivo

**Só o Codex viu:** o erro dos 10% na primeira página · o `reproduce` como renderizador · a
semântica errada da A.6 no pacote · os salários de desligamento de R$ 203 milhões · a A.5
incompleta · a robustez prometida e não reportada · a coluna de suporte cortada no PDF e o markup
literal (`<br>`, `&lt;0,001`) · os erros aritméticos e de referência cruzada da Seção 3 · a Figura
3.2 duplicada · a bibliografia com 21 registros citados ausentes, com `corrected_library.bib`
pronto · as definições demográficas divergentes entre módulos · o painel desbalanceado (8 a 54
meses por CBO) · a validação da `results/reference` que não é ancorada em manifesto.

**Só o Claude viu:** as declarações fora do prazo · o mecanismo do Gradiente 4 vazio · a ausência
de seção de Conclusão · a ausência total de literatura metodológica de DiD · `tipo_movimentacao`
baixado e nunca usado · `horas_contratuais` nunca extraída · a solução do gate de armazenamento ·
o painel PNADc de 16 trimestres órfão em `archive/` · as três variantes de sensibilidade da medida
de exposição já disponíveis na planilha da OIT.

**Infraestrutura que só o Codex produziu** e que vale usar: `Final Review/Codex/evidence/` tem
scripts executáveis, logs de reprodução, `findings_ledger.csv`, `claim_artifact_matrix.csv`,
`baseline_manifest.csv` e a bibliografia corrigida. Não refaça isso.
