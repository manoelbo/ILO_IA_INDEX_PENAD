# Fase 8A — Diagnósticos e correções da V2

**Data:** 26 de julho de 2026
**Escopo:** dados e conclusões. **Nenhuma alteração no texto da dissertação.**
**Pré-requisito:** V2 entregue e com Checkpoints A–H fechados.
**Sucessora:** Fase 8B (geração de tabelas e figuras) — **não autorizada** até o Gate 8A fechar.

---

## LEIA ISTO PRIMEIRO

1. **Não improvise.** Se um fato não estiver aqui nem for verificável por comando, pare e pergunte.
2. **Não escolha especificação por p-valor nem por resultado de pretrend.** Esta fase produz
   diagnósticos; a decisão sobre especificação principal é do autor, no Gate 8A.
3. **Não edite `Replication Package/V1/`.**
4. Registre toda decisão em `Replication Package/V2/DECISIONS.md` **antes** de rodar.
5. Todos os painéis e estimadores necessários **já existem**. Esta fase não constrói dados novos.

### Decisões já fechadas pelo autor

| # | Decisão |
|---|---|
| 1 | **Mês de referência: novembro de 2022** (`t = −1`). É o que a V2 já usa — nada muda aqui. A Seção 5.3 usa outubro de 2022 como base; a harmonização fica para a Fase 8B. |
| 2 | Blocos de diagnóstico e correção ficam **nesta fase**, separados da geração de artefatos. |
| 3 | **Não pensar no texto agora.** O objetivo é gerar dados e chegar a conclusões. |

---

## Contexto: por que esta fase existe

A V2 rodou os diagnósticos de tendência prévia sobre **um único modelo** —
`balanced_dynamic_exact_model`, janela −23 a +23, amostra completa. Verificado em
`results/diagnostics/pretrend_diagnostics.csv`: cinco linhas, um `model_name`, uma janela.

Todos os cinco outcomes falham. Mas nenhuma das especificações que poderiam explicar ou resolver a
falha foi diagnosticada, embora todas já estejam estimadas na escada.

E há uma regressão de cobertura em relação à V1: as tabelas do Apêndice A da V1 traziam as colunas
`Pretrend grupo`, `Pretrend DDD` e `Poder grupo`. A V2 não produz nenhuma das três.

**A hipótese a testar** é do autor e é plausível: a violação vem da recuperação pandêmica
diferencial. O pré-período é jan/2021 a nov/2022 — o auge da recuperação do emprego formal
brasileiro. As ocupações de controle (serviços, comércio, agropecuária) caíram mais na pandemia e
recuperaram mais rápido; as tratadas (administrativas, profissionais) migraram para trabalho remoto
e tinham menos terreno a recuperar.

O sinal bate: a inclinação linear pré das admissões é **−0,0060** (p = 7,2e-13) — o grupo tratado
cresce mais devagar que o controle no pré-período.

---

## Parte 1 — Diagnósticos

### T8A.1 — Pretrend na amostra que começa em 2022-01, com teste de poder

**Este é o teste central da fase. Leia a ressalva antes de implementar.**

A escada já tem `06_start_2022_01` como coeficiente estático. Falta o diagnóstico dinâmico.

**Ressalva metodológica obrigatória.** Começar em 2022-01 deixa **11 meses de pré-tratamento**
(jan–nov/2022) em vez de 23. Um teste conjunto sobre 11 leads tem menos poder que sobre 22. Se ele
deixar de rejeitar, isso pode significar duas coisas completamente diferentes:

- a violação de fato estava em 2021 e sumiu; **ou**
- o teste ficou fraco demais para detectar a mesma violação.

**Não é possível distinguir as duas sem o teste de poder abaixo, e o resultado não deve ser
interpretado sem ele.**

**Implementação:**

1. Estimar o event study na amostra jan/2022 → corte, com `t = −1` em nov/2022, janela
   `t = −11 … +41`.
2. Rodar os três diagnósticos nomeados distintamente, como já é feito no modelo nacional: teste
   conjunto dos leads, tendência linear pré, e leads individuais.
3. **Teste de poder — decisivo.** Rodar o teste conjunto na **amostra completa** (jan/2021)
   restrito aos **mesmos 11 leads** (`t = −11 … −1`). Comparar com o resultado do passo 2.

**Como ler o teste de poder:**

| Amostra completa, 11 leads | Amostra 2022, 11 leads | Conclusão |
|---|---|---|
| Rejeita | Não rejeita | A violação estava em 2021. **Hipótese da pandemia confirmada.** |
| Não rejeita | Não rejeita | O ganho é de **poder**, não de substância. A hipótese não está confirmada. |
| Rejeita | Rejeita | A violação não é específica de 2021. |

**Critérios de aceitação:**
- [ ] `results/diagnostics/pretrend_sample_2022.csv` com os três testes para os cinco outcomes.
- [ ] `results/diagnostics/pretrend_power_check.csv` com o teste de 11 leads na amostra completa.
- [ ] Um quadro-resumo com a leitura da tabela acima, por outcome.
- [ ] **Nenhuma recomendação de especificação principal neste artefato.** Só o diagnóstico.

**Tamanho:** M.

---

### T8A.2 — Pretrend no nível 2 (CNAE × mês)

O nível 2 é co-principal e está estimado (`sector_fixed_effect_ladder.csv`), mas nunca foi
diagnosticado. Testa se a violação é recuperação **setorial**.

Isso tem respaldo na literatura: Klein Teeselink (2025) controla explicitamente por choques
setoriais, e Brynjolfsson, Chandar e Chen (2025) usam efeitos fixos de firma × tempo, que são ainda
mais saturados.

**Implementação:** event study com `cbo_section + section_period` como efeitos fixos, `t = −1` em
nov/2022, mesma janela do nacional. Cluster em `cbo_4d`; reportar também a versão bidirecional com
divisão CNAE.

**Critérios de aceitação:**
- [ ] `results/diagnostics/pretrend_level2.csv` com os três testes para os cinco outcomes.
- [ ] Comparação lado a lado com os testes do nível 1, na mesma tabela.
- [ ] Tabela de suporte reportada **antes** dos coeficientes.

**Tamanho:** M.

---

### T8A.3 — Pretrend na exposição contínua e no controle ampliado

Dois degraus da escada já estimados e nunca diagnosticados: `05_continuous_exposure` e
`04_include_minimal_as_control`.

O segundo interessa porque `Minimal Exposure` é adjacente ao grupo tratado na escala de exposição, e
provavelmente teve trajetória pandêmica mais parecida que agropecuária e construção.

**Critérios de aceitação:**
- [ ] `results/diagnostics/pretrend_ladder_variants.csv` com os três testes para os dois degraus.
- [ ] Para a exposição contínua, o diagnóstico é sobre a interação `score × tempo de evento`.

**Tamanho:** S.

---

### T8A.4 — Pretrend do DDD, pretrend por grupo e poder

**Recupera três colunas que a V1 tinha e a V2 perdeu.** O cabeçalho das tabelas A.x da V1 é:

```
Grupo, Resultado, DDD grupo–complemento, p DDD, Pretrend grupo, Pretrend DDD, Poder grupo,
N grupo, CBOs trat./controle
```

A V2 produz coeficiente, EP, IC, p nominal, p ajustado BH e suporte — e nenhuma das três colunas de
diagnóstico.

**Por que isto pode ser o achado mais importante da fase.** A hipótese de identificação do DDD é
diferente e mais fraca que a do DiD: exige que a *diferença entre grupos* teria evoluído em paralelo
entre ocupações expostas e não expostas. Qualquer violação que atinja tratados e controles
igualmente entre os grupos demográficos é diferenciada fora.

Na V1 esse padrão já aparecia: o DDD de sexo nas admissões tinha "tendências prévias compatíveis" e
o de raça nos desligamentos tinha "tendências paralelas favoráveis", **enquanto os pretrends do DiD
nacional falhavam**.

**Implementação:**
1. Pretrend do **DDD**: event study do termo triplo `post × treatment × subgroup` por contraste.
2. Pretrend do **DiD por grupo**: exige o DiD por grupo, que a Fase 8B vai estimar. **Nesta fase,
   estimar apenas o dinâmico necessário ao diagnóstico**, não a tabela completa.
3. **Poder por grupo**: MDE (efeito mínimo detectável) a 80% de poder, dado o EP estimado. Reportar
   como a V1 reportava.

**Critérios de aceitação:**
- [ ] `results/diagnostics/ddd_pretrends.csv` cobrindo os 100 contrastes já estimados.
- [ ] Coluna de poder por grupo.
- [ ] Um resumo contando quantos DDD passam no pretrend contra quantos DiD nacionais passam.

**Tamanho:** M.

---

### T8A.5 — Especificação com controle de tendência pré

Humlum e Vestergaard (2025) enfrentaram exatamente este problema — tendências que antecedem os
chatbots — e a solução deles foi controlar por elas dentro do DiD: *"because these trends entirely
predate AI chatbots, the pooled difference-in-differences (which control for pre-trends) are precise
zeros"*.

**Ressalva que deve constar do artefato:** uma tendência linear por CBO ajustada no pré-período e
extrapolada sobre 42 meses de pós pode absorver parte de um efeito de difusão gradual. É
especificação de robustez rotulada, **nunca principal**. No caso de Humlum ela produziu zeros
precisos, o que mostra que não fabricou efeito — mas o risco na direção oposta existe.

**Implementação:** DiD com tendência linear específica por CBO estimada no pré-período. Reportar
lado a lado com a versão sem tendência.

**Critérios de aceitação:**
- [ ] `results/models/pretrend_control_specification.csv`, cinco outcomes.
- [ ] A ressalva acima no `.md` que acompanha.
- [ ] Rotulada como robustez em `DECISIONS.md`.

**Tamanho:** M.

---

### T8A.6 — Pretrend do salário com cobertura completa

O painel de salário tem ~15% menos células que o de fluxos (682.889 contra 804.929 no nível 2),
porque célula sem admissão não tem salário. Se o conjunto de CBOs com salário válido muda mês a mês
no pré-período, isso sozinho produz leads oscilantes.

Isso é consistente com o padrão observado: a tendência **linear** do salário **não** é significativa
(p = 0,221), mas o teste conjunto rejeita (p = 1,6e-04) com 11 de 22 leads individualmente
significativos. Ruído oscilante, não divergência.

**Implementação:** repetir o event study do salário restrito às CBOs com salário válido em **todos**
os meses da janela. Reportar quantas CBOs sobram.

**Critérios de aceitação:**
- [ ] `results/diagnostics/pretrend_wage_balanced_coverage.csv`.
- [ ] Contagem de CBOs retidas e descartadas.
- [ ] Comparação dos três testes contra a versão sem restrição.

**Tamanho:** S.

---

## Parte 2 — Correções da V2 entregue

### T8A.7 — Estimar os quatro horizontes longos

`results/models/long_run_horizons.csv` tem cinco colunas — `event_time`, `periodo`, `periodo_num`,
`horizon`, `partial_horizon`. É **tabela de mapeamento, sem nenhum coeficiente**. Era exigência do
contrato congelado.

Horizontes: dez/2022–nov/2023 · dez/2023–nov/2024 · dez/2024–nov/2025 · dez/2025–mai/2026
(**marcado como parcial**).

**Por que importa mais do que parece.** O event study balanceado termina em nov/2024. O coeficiente
estático cobre até mai/2026. No salário real, a média dos coeficientes pós do event study é
**−0,0154** enquanto o estático é **−0,0507**. Os últimos coeficientes visíveis na figura são
praticamente zero (t=18: −0,0005; t=20: +0,0013; t=21: +0,0115).

Isso implica que **o efeito salarial está concentrado depois de novembro de 2024** — o período que a
V1 não tinha. Os horizontes tornam isso explícito.

**Critérios de aceitação:**
- [ ] `results/models/long_run_horizon_estimates.csv` com coeficiente, EP, IC, p, N e clusters por
      horizonte, para os cinco outcomes.
- [ ] Mesmo estimador e mesma inferência do principal.
- [ ] O quarto horizonte explicitamente marcado como parcial.
- [ ] Um `.md` que reconcilia a soma dos horizontes com o coeficiente estático.

**Tamanho:** M.

---

### T8A.8 — Corrigir o enquadramento do HonestDiD

`README.md` e `COMPARACAO_V1_V2.md` justapõem, sem ressalva:

> As estimativas principais [...] −0,050740 para salário real de admissão. Só o salário rejeita a
> 5%. [...] O intervalo HonestDiD do salário não exclui zero nem em M = 0.

Lido junto, isso diz que o resultado da manchete é frágil. Mas o alvo do HonestDiD é
`average_post_event_time_0_to_23`, com estimativa **−0,0154 e EP 0,0122** — cujo intervalo original
já é [−0,039; +0,009] e **já inclui zero antes de qualquer ajuste**.

São estimandos diferentes, em janelas diferentes. Nenhum número está errado; a justaposição é que
induz ao erro.

**Critérios de aceitação:**
- [ ] Os dois documentos declaram, em cada afirmação, **qual janela e qual estimando**.
- [ ] Fica explícito que o alvo do HonestDiD não é o coeficiente estático da manchete.
- [ ] Um teste em `tests/` que falha se as duas afirmações voltarem a aparecer sem qualificação de
      janela.

**Tamanho:** S.

---

### T8A.9 — Acrescentar DeltaSD ao HonestDiD

Foi usado apenas `C-LF DeltaRM` — magnitudes relativas, que limita a violação pós pelo **máximo** da
violação pré. Para um pré-período oscilante mas sem tendência (que é o caso do salário: linear
p = 0,221), basta um lead ruidoso grande para o limite explodir.

**DeltaSD** limita a curvatura em vez da magnitude, e é a escolha mais informativa nesse padrão.

**Critérios de aceitação:**
- [ ] `honest_did_sensitivity.csv` com as duas restrições, coluna `Delta` distinguindo.
- [ ] Para cada outcome e cada restrição, o **maior M em que o intervalo exclui zero**.
- [ ] Gráfico com as duas curvas sobrepostas.

**Tamanho:** M.

---

## ✅ GATE 8A — bloqueante

Não iniciar a Fase 8B sem fechar.

- [ ] Os seis diagnósticos rodaram e produziram artefato.
- [ ] O teste de poder da T8A.1 está reportado **junto** com o resultado da amostra de 2022 —
      nunca separado.
- [ ] Os quatro horizontes estão estimados e reconciliam com o estático.
- [ ] O enquadramento do HonestDiD está corrigido nos dois documentos.
- [ ] `DECISIONS.md` registra tudo, **sem** recomendar mudança de especificação principal.
- [ ] **Um relatório único** — `results/diagnostics/DIAGNOSTICO_PRETRENDS.md` — com uma tabela:
      especificação × outcome × teste conjunto × tendência linear × leads individuais × veredito.
- [ ] **PARAR. Entregar ao autor. A decisão sobre especificação principal é dele.**

---

## Recomendação sobre a especificação principal

O autor perguntou se a amostra de 2022 deve virar co-principal caso resolva os pretrends. Minha
recomendação, para constar antes de o diagnóstico rodar:

**Reportar as duas como co-principais, e não deixar o resultado do pretrend decidir qual é "a"
resposta.**

Três razões.

**Primeira, e é a que mais pesa:** promover uma especificação porque ela passa num pré-teste é
seleção sobre o diagnóstico — exatamente o que Roth (2022) mostra que distorce a inferência, e
exatamente o que a regra 10 do `final_review_planning.md` do autor proíbe ("do not select the start
date [...] based on p-values or pretrend-test outcomes").

**Segunda:** o pré-período cai de 23 para 11 meses. Sem o teste de poder da T8A.1, um "passou" pode
ser só ausência de poder.

**Terceira:** a amostra completa é o que o contrato congelado pré-registrou, e a de 2022 já está
pré-registrada como sensibilidade. Reportar as duas honra o pré-registro; substituir uma pela outra
depois de ver o resultado, não.

**O que muda conforme o diagnóstico:** não qual é a principal, mas **o que o texto pode afirmar**.
Se o teste de poder mostrar que a violação estava mesmo em 2021, o autor ganha uma frase forte e
defensável — *a violação de tendência paralela se concentra na recuperação pandêmica de 2021, e o
desenho é mais credível a partir de 2022* — sem precisar reescrever qual especificação é a
principal.

---

## Fase 8B — esboço, NÃO autorizada

Fica para depois do Gate 8A, e o desenho dela depende do resultado do diagnóstico.

| Bloco | Conteúdo | Escala |
|---|---|---|
| Janela | Estender o event study para `t = −23 … +41`, com a fronteira de +23 marcada. Precedente: Canaries usa a amostra inteira, jan/2021–jul/2025, sem truncar. | S |
| Estimação p/ tabelas | DiD por grupo (~80 modelos) · faixas etárias PNAD · casos ocupacionais da Seção 5.3 | L |
| Estimação p/ figuras | Event study por grupo (12 figuras × 2 painéis) · trajetórias dos casos por idade | L |
| Renderização | **23 tabelas** e **16 figuras** — 13 das seções principais mais 3 do Apêndice B | L |
| Harmonização | Base temporal da Seção 5.3 (hoje out/2022) contra a referência nov/2022 | S |

**Por que 8B espera:** se o diagnóstico mudar a especificação preferida ou a janela, as 16 figuras e
as 23 tabelas mudam junto. Gerar artefato antes de fechar o diagnóstico é retrabalho garantido.
