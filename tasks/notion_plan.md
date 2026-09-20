# Plano — Atualizar a dissertação no Notion a partir do Guia_Reescrita_V2

**Data:** 28 de julho de 2026
**Alvo:** `Dissertação de Mestrado V2` — `325cc8ca461082d794db01323b295bb5`
**Fonte das mudanças:** `Final Review/Guia_Reescrita_V2/` (9 documentos)
**Escopo:** Seções 4, 5, Apêndice A e Apêndice B. Seções 1 a 3 não são tocadas.

---

## Visão geral

O documento tem **193.231 caracteres**. As Seções 4 e 5 mais apêndices ocupam do caractere 66.947
ao fim — **126.284 caracteres, 65% do documento**. Dentro desse trecho há **23 blocos de tabela**,
**16 imagens** e **1 bloco de equação**.

Fora do escopo ficam 11 imagens e ~67 mil caracteres das Seções 1 a 3.

O plano aplica as mudanças **no lugar**, por substituição de trechos, e nunca por reescrita
integral da página.

---

## Decisões de arquitetura

### 1. `update_content`, nunca `replace_content`

Três razões, e a primeira decide:

**As 11 imagens das Seções 1 a 3 se perderiam.** Elas estão hospedadas no S3 do Notion com URL
assinada. Uma reescrita integral obrigaria a re-subir todas — inclusive as que não mudam.

**O escopo é cirúrgico.** Seções 1 a 3 são metade do documento e estão fora. Substituição por
trecho respeita isso por construção.

**Falha em vez de corromper.** Se um `old_str` não bater exatamente, a operação falha e nada muda.
Numa reescrita de 193 mil caracteres, um erro contamina tudo.

### 2. Fatiamento vertical por subseção, não por tipo de artefato

Cada tarefa entrega **uma subseção inteira e coerente** — tabela, números do texto e interpretação
juntos — em vez de "todas as tabelas, depois todos os parágrafos".

O motivo é que o estado intermediário importa: se eu trocar todas as tabelas primeiro, o documento
passa horas com tabela nova e parágrafo velho dizendo o contrário. Fatiado por subseção, cada
tarefa deixa o documento internamente consistente naquele ponto.

**A exceção é figura**, que fica numa fase própria por estar bloqueada em upload.

### 3. As âncoras exatas saem de um arquivo, não da memória

`notion-fetch` devolve a página inteira e estoura o contexto. O fluxo por lote é:

```
fetch → salvar em arquivo → extrair old_str exato via python → montar update_content → aplicar
```

Nunca digitar um `old_str` de memória. Sempre extrair do arquivo salvo.

### 4. Alto risco primeiro

As duas tabelas **factualmente erradas** — A.1 e 5.1 — vêm antes de tudo. Se a mecânica de
substituição não funcionar, é melhor descobrir na primeira tarefa.

---

## Grafo de dependências

```
T0.1 snapshot e âncoras
   │
   ├── Fase 1: reparos factuais (A.1, 5.1)        ← alto risco, primeiro
   │      │
   │      ├── Fase 2: Seção 4 (define os termos usados na Seção 5)
   │      │      │
   │      │      └── Fase 3: Seção 5.2 (heterogeneidades)
   │      │             │
   │      │             └── Fase 4: Apêndice A (espelha a 5.2)
   │      │
   │      └── Fase 5: 5.3 e Apêndice B (independente)
   │
   └── Fase 6: figuras  ← bloqueada em upload, roda em paralelo quando destravar
          │
          └── Fase 7: varredura final
```

A Seção 4 vem antes da 5 porque define os termos que a 5 usa — famílias de multiplicidade,
estimador, o que é DiD dentro do grupo contra DDD. Escrever a 5 antes obrigaria a reescrever
depois.

---

## Fase 0 — Preparação

### T0.1 — Snapshot e extração de âncoras

**Descrição.** Buscar a página, salvar o conteúdo cru, e extrair para um arquivo de trabalho os
trechos exatos que cada tarefa vai substituir.

**Critérios de aceitação:**
- [ ] `tasks/notion_snapshot.txt` com o conteúdo desescapado.
- [ ] `tasks/notion_ancoras.json` com, para cada edição planejada, o `old_str` exato e o intervalo
      de caracteres onde ele ocorre.
- [ ] Cada `old_str` ocorre **exatamente uma vez** no documento. Âncora ambígua é erro de
      preparação, não de execução.

**Verificação:** contagem de ocorrências de cada âncora = 1.

**Dependências:** nenhuma. **Tamanho:** S.

---

## Fase 1 — Os dois reparos factuais

### T1.1 — Tabela A.1

**Descrição.** É o reparo mais urgente do documento. A tabela certifica hoje o pretrend do salário
como `pass (p=0,932)`; na V2 é `fail (p=1,6e-04)`. É a célula que sustenta o único resultado
significativo do trabalho.

Substitui o Painel B.1 inteiro, troca o Painel B.2 pelo proxy cumulativo, e reescreve a nota.

**Fonte:** `01_TABELAS.md` §Apêndice A · `Replication Package/V2/results/tables/table_a_1_national_diagnostics.md`

**Critérios de aceitação:**
- [ ] Nenhuma célula da A.1 diz `pass` para o salário.
- [ ] A nota registra explicitamente que é `fail (p=1,6e-04)`, não `pass`.
- [ ] O Painel B.2 é o proxy cumulativo (+1,429; EP 1,309; p = 0,276), com a nota de que não é
      estoque de emprego.
- [ ] Os cinco outcomes aparecem, incluindo fluxo bruto.

**Verificação:** re-buscar a página e conferir que `pass (p=0,932)` não ocorre mais e que
`1,6e-04` ocorre.

**Dependências:** T0.1. **Tamanho:** S.

---

### T1.2 — Tabela 5.1 e os quatro parágrafos da §5.1

**Descrição.** Troca a tabela e as quatro afirmações que caem: *"nenhum é estatisticamente
significativo"*, as reduções de 3,0/4,1/2,0%, a qualificação *"para os fluxos"*, e *"redução
modesta"*.

Acrescenta a explicação da falha de tendências paralelas com os números de volatilidade — o item
que converte uma admissão defensiva em argumento.

**Fonte:** `01_TABELAS.md` §Seção 5 · `05_SECAO_5.md` §5.1

**Critérios de aceitação:**
- [ ] Tabela 5.1 com os quatro coeficientes da V2.
- [ ] Nenhuma frase afirma que nenhum coeficiente é significativo.
- [ ] O parágrafo de comparabilidade do controle está presente, com 14,0% contra 8,3% e 44,7%
      contra 27,3%.
- [ ] A qualificação do salário está presente: 23% a 29% é composição, preço fica em −3,6% a −3,9%.

**Verificação:** re-buscar e conferir que `-0,0309` não ocorre na §5.1 e que `−0,0507` ocorre.

**Dependências:** T0.1. **Tamanho:** M.

---

## ✅ Checkpoint A — a mecânica funciona

- [ ] As duas substituições aplicaram sem erro de correspondência.
- [ ] As Seções 1 a 3 estão intactas: contagem de imagens do documento continua 27.
- [ ] O autor conferiu visualmente as duas tabelas no Notion.

**Parar aqui e mostrar ao autor.** Se a mecânica falhar, falha barato.

---

## Fase 2 — Seção 4

### T2.1 — §4.1

**Descrição.** Três acréscimos e uma correção: o argumento CAGED versus PNADc, o parágrafo de por
que o TWFE é válido, a convenção de novembro de 2022, e a correção da descrição do estudo ADP.

Os textos estão prontos em `04_SECAO_4.md` e podem ser colados.

**Critérios de aceitação:**
- [ ] O argumento CAGED versus PNADc cobre frequência, natureza do registro e fluxo contra estoque.
- [ ] O parágrafo do TWFE cita Goodman-Bacon, Callaway–Sant'Anna, Sun–Abraham e de Chaisemartin, e
      diz que **não se aplicam**.
- [ ] A descrição do ADP corrigida menciona regressão de Poisson e efeitos fixos de firma×tempo.

**Dependências:** Checkpoint A. **Tamanho:** M.

---

### T2.2 — §4.2 e as três tabelas do painel

**Descrição.** Reescreve a construção do painel — vintage `MOV + FOR − EXC`, reconciliação PDET,
regra de ausência, domínios inválidos, winsorização — e substitui as Tabelas 4.2.1, 4.2.2 e 4.2.3.

Acrescenta as duas limitações da medida que a Fase 9 mediu: a não monotonicidade do score e as 193
CBOs sem score, mais o teto de 0,5933 do Gradiente 4.

**Critérios de aceitação:**
- [ ] Os quatro números da 4.2.1: 22.049, 341, 65, 2026-05.
- [ ] A frase de janela diz 23 meses antes e **42** depois.
- [ ] A faixa de sobreposição `[0,280; 0,320]` e as 193 sem score estão declaradas com número.
- [ ] O teto de 0,5933 contra o limiar de 0,60 aparece.

**Dependências:** T2.1. **Tamanho:** M.

---

### T2.3 — §4.3, as equações

**Descrição.** Substitui a equação única atual — que traz `X'γ` no modelo principal e é linear —
pelas quatro da V2: PPML estático, linear estático, event study e DDD. Mais a justificativa do PPML
e a distinção entre DiD dentro do grupo e DDD. Substitui a Tabela 4.3.1.

O Notion aceita `$$…$$` em bloco e `` $`…`$ `` inline; as equações de `04_SECAO_4.md` já estão
nesse formato.

**Critérios de aceitação:**
- [ ] `X_{c,t}'\gamma` não aparece mais na equação principal.
- [ ] As quatro equações renderizam no Notion sem erro de LaTeX.
- [ ] A justificativa do PPML cita Silva e Tenreyro, Chen e Roth, e registra que o Canaries usa o
      mesmo estimador pelo mesmo motivo.
- [ ] A tabela de distinção DiD-dentro-do-grupo contra DDD está presente.
- [ ] Tabela 4.3.1 com cinco outcomes e o rótulo de contagem corrigido para semi-elasticidade.

**Verificação:** abrir a página e confirmar que as equações renderizam, não que o texto-fonte está
lá. LaTeX quebrado passa em busca de string e falha visualmente.

**Dependências:** T2.2. **Tamanho:** M.

---

### T2.4 — §4.4 e a §4.5 nova

**Descrição.** Acrescenta a pré-especificação das três famílias de multiplicidade à §4.4, e cria a
§4.5 de robustez com os oito exercícios, uma frase cada.

**Critérios de aceitação:**
- [ ] As três famílias estão declaradas com tamanho: A com 100, B com 30, C com 130.
- [ ] A justificativa de por que A e B ficam separadas está escrita.
- [ ] A §4.5 lista os oito exercícios **sem números** — ela declara desenho, não resultado.
- [ ] A regra de parada está escrita: falha no placebo seria reportada como falha.

**Dependências:** T2.3. **Tamanho:** M.

---

## ✅ Checkpoint B — Seção 4 completa

- [ ] As quatro subseções mais a nova estão consistentes entre si.
- [ ] Todas as equações renderizam.
- [ ] Nenhum termo da Seção 4 contradiz o que a Seção 5 vai usar.
- [ ] Revisão do autor antes de seguir.

---

## Fase 3 — Seção 5.2

Cinco tarefas, uma por subseção. Cada uma troca a tabela e reescreve a interpretação junto, para
que o documento nunca fique com tabela nova e texto velho.

### T3.1 — §5.2.1 Sexo

**A maior baixa do trabalho.** A assimetria de gênero nas admissões não sobrevive: DDD vai de
+0,0446 (p = 0,018) para +0,0116 (BH p = 0,907).

**Critérios de aceitação:**
- [ ] Tabela 5.2.1 com estrelas do BH, coluna de pretrend e a nota que separa DiD dentro do grupo
      de heterogeneidade.
- [ ] A síntese não afirma mais retração diferencial de admissões femininas.
- [ ] A afirmação de nulo informativo está escrita: exposição desigual, ajuste não diferencial.
- [ ] A comparação com Canaries vira convergência, não contraste.

**Dependências:** Checkpoint B. **Tamanho:** M.

---

### T3.2 — §5.2.2 Raça/cor

**Critérios de aceitação:**
- [ ] Tabela 5.2.2 com o agregado `Negra`.
- [ ] A explicação de por que o agregado é mais forte que os componentes está escrita — contrastes
      diferentes, complementos diferentes.
- [ ] A concentração em pardos está declarada.

**Dependências:** T3.1. **Tamanho:** M.

---

### T3.3 — §5.2.3 Idade

**A leitura inverte.** Não são os jovens atingidos: são os de 41–49 poupados.

**Critérios de aceitação:**
- [ ] Tabela 5.2.3 com as faixas PNAD.
- [ ] O texto diz que o DDD de 22–25 é −0,019 e não significativo, e que o de 41–49 é +0,084 com
      BH p = 0,0043.
- [ ] O achado de 22–25 no salário — o único cujo pretrend passa — tem parágrafo próprio, com a
      ressalva de que é 1 entre 100 contrastes.
- [ ] A comparação com Canaries é precisa, não analógica.

**Dependências:** T3.2. **Tamanho:** M.

---

### T3.4 — §5.2.4 Escolaridade e §5.2.5 Renda

**Critérios de aceitação:**
- [ ] Superior mantém direção com a qualificação de BH p = 0,055.
- [ ] A afirmação sobre renda intermediária nos desligamentos é removida — não se sustenta.
- [ ] A faixa de renda alta aparece na tabela com o rótulo `thin` e **não** entra na prosa.

**Dependências:** T3.3. **Tamanho:** M.

---

### T3.5 — §5.2.6 Síntese

**Critérios de aceitação:**
- [ ] A síntese reflete os cinco eixos reescritos.
- [ ] A frase de multiplicidade está presente: 34 nominais, 21 sobreviventes.
- [ ] Espaço reservado para a Figura 5.2.6, a ser inserida na Fase 6.

**Dependências:** T3.4. **Tamanho:** S.

---

## ✅ Checkpoint C — Seção 5.2 completa

- [ ] As cinco subseções e a síntese contam a mesma história.
- [ ] Nenhuma afirmação de heterogeneidade sobrevive sem respaldo no BH.
- [ ] Revisão do autor.

---

## Fase 4 — Apêndice A

### T4.1 — A.2 e A.3

**Critérios de aceitação:**
- [ ] Nominal e BH lado a lado, nove colunas, família declarada.
- [ ] Nenhuma das duas tem Painel B.2.
- [ ] A.3 com as seis categorias raciais, incluindo amarela e indígena.

**Dependências:** Checkpoint C. **Tamanho:** M.

---

### T4.2 — A.4, A.5 e A.6

**Critérios de aceitação:**
- [ ] A.4 com os dois painéis e o identificador de família visível em cada um.
- [ ] A.6 com o rótulo de suporte na célula da renda alta.
- [ ] Nenhuma tem Painel B.2.

**Dependências:** T4.1. **Tamanho:** M.

---

## Fase 5 — Seção 5.3 e Apêndice B

### T5.1 — §5.3 e Tabela 5.3.1

**Critérios de aceitação:**
- [ ] Base de normalização em novembro de 2022, não outubro.
- [ ] Medida-resumo nos 12 meses terminais, junho de 2025 a maio de 2026.
- [ ] A composição dos casos é reportada: 53 dos 76 códigos num só caso, 60 de 80 com confiança
      `medium`.
- [ ] Sem estrela, sem p-valor, sem linguagem causal.

**Dependências:** Checkpoint A. **Tamanho:** M.

---

### T5.2 — Apêndice B

**Descrição.** **Decidido em 28/07: o Apêndice B sai do texto.** Em vez de manter um apêndice
prometido e não entregue, o texto deixa de prometê-lo. Prometer e não entregar foi o achado nº 6 da
auditoria da V1.

**Critérios de aceitação:**
- [ ] As duas remissões ao Apêndice B na §5.3 removidas.
- [ ] A seção `## Apêndice B` inteira removida, com B.1, B.2, B.3 e os cinco links externos.
- [ ] As três imagens do Apêndice B removidas junto — a contagem de imagens do documento cai de 27
      para 24.
- [ ] Nenhuma remissão órfã ao Apêndice B sobra em lugar nenhum do documento.

**Verificação:** buscar `Apêndice B` no documento e confirmar zero ocorrências.

**Dependências:** T5.1. **Tamanho:** S.

---

## Fase 6 — Figuras

**Bloqueada.** O MCP do Notion aceita anexo por conteúdo de texto ou por URL HTTPS pública. As 14
figuras são PNGs locais somando 9,7 MB, e o `ntn` não está instalado.

### T6.1 — Destravar o upload

Três saídas, em ordem de esforço do autor: arrastar as 14 no Notion; hospedar em URL pública e me
passar os links; instalar o `ntn`.

**Critérios de aceitação:**
- [ ] As 14 imagens existem no Notion ou têm URL pública acessível.

**Dependências:** nenhuma técnica; depende do autor. **Tamanho:** S.

---

### T6.2 — Gerar a Figura 5.2.3.3

**Descrição.** **Decidido em 28/07: entra uma 15ª figura**, o event study da coorte 22–25 no
salário. É o único contraste do trabalho cujo pretrend passa e hoje está invisível.

**Precisa ser estimada.** O `group_event_study_coefficients.csv` cobre as 15 partições principais e
não inclui as coortes Canaries. Exige rodar o event study de `age_22_25` no salário no pacote de
replicação, com a mesma janela, a mesma linha da média pré e a mesma fronteira de +23.

**Critérios de aceitação:**
- [ ] `figure_5_2_3_3_canaries_22_25_wage.png` gerada a 300 dpi, com as três marcações.
- [ ] O CSV de coeficientes sai junto, como nas demais.
- [ ] A legenda traz a ressalva: 1 entre 100 contrastes, sem ajuste sobre a família de pretrends.
- [ ] A suíte do pacote continua passando.

**Dependências:** T3.3. **Tamanho:** M.

---

### T6.3 — Substituir as 13 e inserir as duas novas

**Critérios de aceitação:**
- [ ] As 13 referências apontam para as figuras novas, com janela `−23…+41`.
- [ ] A Figura 5.2.6 está inserida na §5.2.6.
- [ ] A Figura 5.2.3.3 está inserida na §5.2.3, depois da 5.2.3.2.
- [ ] As 11 imagens das Seções 1 a 3 estão intactas.
- [ ] As legendas explicam a linha da média pré e a fronteira de +23.

**Dependências:** T6.1, T6.2, T3.5. **Tamanho:** M.

---

## ✅ Checkpoint D — Fase 7, varredura final

### T7.1 — Varredura

- [ ] Nenhum número da V1 sobrevive nas Seções 4 e 5: buscar `23.319`, `-0,0309`, `-0,0207`,
      `pass (p=0,932)`, `436`, `54 meses`.
- [ ] Contagem de imagens: 27 antes; 24 após remover o Apêndice B; **26** ao fim, com a 5.2.6 e a
      5.2.3.3 inseridas.
- [ ] Seções 1 a 3 byte-idênticas ao snapshot da T0.1.
- [ ] Todas as equações renderizam.
- [ ] Os 9 documentos do guia têm cada item aplicado ou declarado como não aplicado.

---

## Riscos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| `old_str` não bate por diferença de escape ou espaço | Médio — falha, não corrompe | Extrair sempre do snapshot, nunca digitar de memória; conferir ocorrência única na T0.1 |
| Equação LaTeX quebra ao renderizar | Alto — passa em busca de string e falha na tela | Verificação visual obrigatória na T2.3, não só busca textual |
| Uma substituição atinge trecho das Seções 1 a 3 | **Alto** | Toda âncora conferida como ocorrência única antes de aplicar; varredura de imagens no Checkpoint A |
| Contexto estoura ao buscar a página | Médio | `notion-fetch` sempre para arquivo, extração por python; nunca ler os 193 mil caracteres |
| Documento fica com tabela nova e texto velho | Médio | Fatiamento vertical por subseção; nunca "todas as tabelas primeiro" |
| Figuras nunca destravam | Médio | Fases 1 a 5 não dependem delas; o texto fica correto mesmo com figura antiga |

---

## Decisões do autor — fechadas em 28 de julho de 2026

| # | Questão | Decisão |
|---|---|---|
| 1 | Apêndice B | **Remover do texto.** As duas remissões da §5.3 e a seção inteira saem. |
| 2 | Figura para a coorte 22–25 | **Sim.** Entra como Figura 5.2.3.3 e precisa ser estimada. |
| 3 | Separador decimal | **Já resolvido.** As tabelas renderizadas na T8B.17 usam vírgula, com ponto só como separador de milhar. Nada a fazer. |

Nenhuma pergunta em aberto.
