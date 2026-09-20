# Revisão Final — Auditoria e Plano (Claude)

**Data:** 25 de julho de 2026
**Objeto:** Dissertação "Exposição ocupacional à IA e emprego formal no Brasil" — texto, código e replication package
**Auditor:** Claude (Opus 5), sessão única, acesso de leitura ao repositório e ao BigQuery do projeto

---

## Como ler estes documentos

| # | Arquivo | Para quê serve |
|---|---|---|
| 00 | `00_INDICE.md` | Este arquivo. Método, escopo e o resumo dos achados. |
| 01 | `01_AUDITORIA_CODIGO.md` | O que está errado ou frágil no código, com arquivo e linha. |
| 02 | `02_AUDITORIA_TEXTO.md` | O que está errado ou frágil no texto, com seção e parágrafo. |
| 03 | `03_MELHORIAS_CODIGO.md` | O que fazer no código, priorizado por retorno. |
| 04 | `04_MELHORIAS_TEXTO.md` | O que fazer no texto, priorizado por retorno. |
| 05 | `05_PLANO_V2.md` | Plano executável da nova rodada e da estrutura V1/V2. |
| 06 | `06_CONCLUSAO_RECOMENDACAO.md` | **Comece por aqui se tiver 10 minutos.** Vale fazer a V2? |

Se você só tem tempo para dois arquivos, leia o **06** e depois o **01**.

### Relação com o conjunto do Codex

Durante esta sessão, o Codex produziu um conjunto paralelo em `Final Review/Codex/`, com a mesma
numeração, e já reestruturou o `Replication Package/` em `V1/` (congelada) e `V2/` (com um contrato
metodológico pré-especificado e status "NOT EXECUTED"). Isso é o que você pediu — dois olhares
independentes sobre o mesmo material.

Onde os dois conjuntos **concordam**: PPML como principal para contagens, remoção dos controles de
composição contemporâneos da especificação causal, janela balanceada sem agrupamento de caudas,
correção de multiplicidade, HonestDiD, e disciplina de DDD. Boa parte disso já estava no seu
`final_review_planning.md`, então a convergência é esperada e é um bom sinal.

Onde este conjunto **acrescenta** — são os pontos que não aparecem no contrato da V2 já escrito:

1. As declarações fora do prazo e as exclusões estão fora do painel, com viés diferencial no tempo
   e entre ocupações (`01` §1).
2. O Gradiente 4 está vazio por causa da assimetria da regra de classificação, não da diluição da
   média como diz a §4.2 da dissertação (`01` §2).
3. Decomposição de desligamentos por tipo de movimentação, admissões de primeiro emprego, e proxy
   de estoque (`03` §P2.1–P2.3).
4. O gate de armazenamento tem solução: 4,2 GB de painéis municipais derivados pertencem a uma
   extensão excluída da dissertação (`05` §2.2b).

---

## Método

O que foi efetivamente lido e verificado:

- **Texto**: `Dissertação/Dissertação de Mestrado 33fcc8ca461080cb8412e25e5b5b6ba3.md` (1.043 linhas),
  integral. PDF conferido (40 páginas). Lista de referências conferida contra as citações no corpo.
- **Código**: `Replication Package/` inteiro (277 arquivos, ~26.700 linhas de Python);
  `src/scripts/` (38 scripts); `code/replication/` (5 scripts de auditoria).
- **Auditorias anteriores**: `correspondence/referee2/` (38 arquivos, duas rodadas completas),
  os blindspot reports em `outputs/*/audit/`, e o seu `final_review_planning.md`.
- **Dados**: schema e cobertura consultados **ao vivo no BigQuery** (`basedosdados.br_me_caged`,
  `br_ibge_pnadc`); inventário do FTP do MTE consultado ao vivo; parquets locais em `data/`
  inspecionados; planilha do índice da OIT aberta e recomputada.

O que **não** foi feito: nenhum arquivo do projeto foi alterado, nenhuma estimação foi re-rodada,
nenhum dado foi baixado. Toda quantificação abaixo vem de leitura ou de consulta a fonte.

**Limite honesto desta auditoria:** os dois achados principais são *diagnósticos de construção*,
verificados na fonte, mas o efeito deles sobre os coeficientes publicados só pode ser medido
reconstruindo o painel. Onde eu digo "da mesma ordem de grandeza", isso é uma comparação de
magnitudes, não uma estimativa do viés.

---

## Resumo dos achados

### O que está bom, e é melhor do que a média

Vale registrar antes de criticar, porque isso muda a recomendação final. O replication package é
genuinamente sólido: contratos declarativos, hashes SHA-256 dos insumos e artefatos, replicação
independente Python↔R que bate a 5,4e-12, 138 testes, e um teste que re-estima os quatro modelos
principais do zero e exige concordância a 1e-12. Duas rodadas de referee interno fecharam 39 de 44
achados. Isso é infraestrutura de qualidade de periódico, e é o que torna a V2 barata: a máquina
de reprodução já existe.

O que essas auditorias **não** cobriram foi o desenho de pesquisa e a construção dos dados na
origem. É aí que estão os problemas.

### Os dois achados que mudam o julgamento

**1. As declarações fora do prazo estão fora do painel, e a omissão é diferencial.**

O pipeline consulta apenas `basedosdados.br_me_caged.microdados_movimentacao`. As tabelas irmãs
`microdados_movimentacao_fora_prazo` (8.609.944 registros) e `microdados_movimentacao_excluida`
(607.497) nunca são consultadas. A fração omitida cai de **8,61% em 2021 para 1,29% em 2024** — e a
queda difere entre grupos ocupacionais em cerca de 2 pontos percentuais entre tratados e controles,
num efeito estimado de 3–4%. O sinal do artefato é o mesmo dos coeficientes publicados, e a forma
é a de uma quebra de tendência pré-tratamento. Detalhe e tabelas em `01`, §1.

**2. O Gradiente 4 está vazio por causa da fórmula, não por causa dos dados.**

A ponte MTE alcança 11 das 13 ocupações ISCO-08 que a OIT classifica como Gradiente 4, e 16 CBOs
tocam pelo menos uma delas. Nenhuma é classificada como G4. A causa é a assimetria da regra: G4
exige `média − desvio ≥ 0,50` enquanto G1–G3 exigem `média + desvio ≥ 0,50`, e o desvio usado
soma dispersão entre destinos à dispersão entre tarefas. O desvio infla, e infla contra o G4.
A explicação que está hoje na §4.2 da dissertação atribui isso à diluição da média — que é parte
da história, mas não é a parte que decide. Detalhe em `01`, §2.

### O que está faltando e é barato

`tipo_movimentacao` é baixado e nunca usado: todo desligamento é tratado como um só evento, sem
distinguir demissão sem justa causa de pedido de demissão ou fim de contrato. Essa decomposição
responde diretamente à pergunta que o texto declara não conseguir responder — "menor rotatividade
ou destruição de vínculos?". `horas_contratuais` nunca foi extraída, então todo resultado salarial
é salário mensal contratual, que confunde preço e jornada. E um painel PNADc de 16 trimestres com
2,9 milhões de linhas está órfão em `archive/` — a PNADc observa **estoque**, que é a ressalva mais
repetida do texto inteiro.

### O que eu conferi e achei menor do que parecia

Registro para você não gastar energia à toa:

- O bug do `.fillna(0)` (`etapa_2a...py:759-763`), que injeta `ln_salario_adm = 0`, atinge **63 de
  23.319 células (0,27%)**. É real e deve ser corrigido, mas não move resultado.
- A afirmação de que o painel tem "muitos zeros", usada para justificar `log(y+1)` em vez de PPML,
  é **falsa**: 62 células com zero admissões (0,27%), mediana de 479 admissões por célula. A frase
  precisa sair do texto, mas a escolha de estimador se resolve por outro argumento.
- A extensão Anatel foi corretamente deixada de fora: o placebo temporal de dez/2021 é
  significativo, o que é uma falha de falsificação.

---

## Recomendação em uma linha

**Fazer a V2, com escopo fechado.** A omissão do fora do prazo não é defensável numa banca, e
corrigi-la obriga a reconstruir o painel de qualquer forma. Uma vez reconstruindo, estender até
05/2026 e adicionar os outcomes de metadados custa pouco a mais. A estrutura da dissertação não
muda. Justificativa completa, com plano B caso você decida reduzir escopo no meio, em `06`.
