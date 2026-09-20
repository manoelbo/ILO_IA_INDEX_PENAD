# Plano de Avaliação das Decisões Metodológicas

**Insumo:** `metodology-audit.md` (143 decisões inventariadas, 2026-08-08)
**Configuração escolhida:** profundidade escalonada por risco · veredito + ação recomendada · ordem por risco à tese
**Estimativa:** 6 a 8 sessões

---

## 1. O que esta avaliação é — e o que ela não repete

Já existe auditoria substancial neste projeto, e ela cobriu **outro eixo**:

| Trabalho anterior | Eixo | Veredito |
| --- | --- | --- |
| `correspondence/referee2/2026-06-14_stage2_methodology_audit.md` | Interpretação dos resultados salariais | "Major revision to the dissertation interpretation, not rejection of the empirical strategy" |
| `correspondence/referee2/..._round1_...` e `..._round2_...` | **Fidelidade**: número ↔ artefato ↔ texto, tabela por tabela, alegação por alegação | MAJOR REVISIONS narrowly scoped; 38 fixed, 3 partially_fixed, 1 unresolved |
| `Final Review/Claude/`, `Final Review/Codex/` | Correção de código e de texto | — |
| `Final Review/Auditoria_V2/` | Evidência de auditoria (composição, jackknife, concentração) | — |

Esta avaliação é de **defensabilidade**, não de fidelidade. A pergunta anterior era *"o número no texto corresponde ao artefato?"*. A pergunta agora é *"esta escolha era a certa, e ela se sustenta sob interrogatório?"*. Uma decisão pode estar perfeitamente implementada, perfeitamente reportada, e ainda assim ser indefensável — e é isso que o trabalho anterior não testou.

Os ledgers antigos entram como **insumo**: eles me dizem quais números são confiáveis, então eu não gasto esforço reverificando aritmética.

**Fora de escopo:** as 4 ações pendentes do round 2 (A.6 desordenada, tabelas do Apêndice B em link 404, duas mudanças de linguagem de estimando, limpeza de legendas). São itens de fidelidade e devem ser tratados em paralelo, não dentro desta avaliação. Registro que não verifiquei se já foram resolvidos na V2.5.

---

## 2. Vocabulário de veredito

Seis níveis, cada um mapeado a uma consequência:

| Veredito | Significado | Consequência |
| --- | --- | --- |
| `sólida` | Defensável como está. | Nenhuma ação. |
| `sólida, subdocumentada` | A escolha é certa, mas o texto não a justifica ou não a declara. | Ação de texto. |
| `frágil, reportada` | A escolha é fraca e a fraqueza está declarada. | Considerar reforçar a declaração. |
| `frágil, não reportada` | A escolha é fraca e a fraqueza não aparece. | Declarar obrigatoriamente. |
| `insustentável` | A escolha deveria ser alterada. | Mudança de desenho ou de alegação. |
| `pendente` | Falta checar um artefato ou rodar algo para decidir. | Vira tarefa de verificação. |

Um veredito `sólida` é um resultado, não uma ausência de resultado. Várias decisões deste trabalho são pontos fortes e devem ser nomeadas como tais — é isso que dá a você o que defender, não só o que corrigir.

---

## 3. Os seis critérios

Aplicados na mesma ordem em toda decisão, para que os vereditos sejam comparáveis entre si:

1. **Justificação** — está justificada no texto, ou apenas implementada? Se justificada, a razão dada é a razão real?
2. **Alternativa** — qual era a alternativa concreta? Ela foi considerada? O custo de tê-la rejeitado está reportado?
3. **Momento** — foi tomada antes ou depois de ver resultados? Isso está declarado? Existe evidência (provenance, git, contrato congelado) que sustente a declaração?
4. **Sensibilidade** — existe teste que mostre quanto o resultado depende dela? Qual foi o resultado do teste? Se não existe, é barato produzir?
5. **Direção do viés** — se a decisão estiver errada, para que lado o resultado se move? Contra ou a favor da conclusão que o trabalho defende?
6. **Defensabilidade** — sobrevive à pergunta mais dura que uma banca faria?

O critério 5 é o que separa uma avaliação útil de uma lista de ressalvas. Uma decisão frágil que empurra o resultado **contra** a própria tese é muito mais defensável do que uma que empurra a favor.

---

## 4. Templates por tier

### Tier 1 — análise completa (51 decisões, ~350 palavras cada)

```
### <ID> · <Título>
`<slug>` · Tipo <S|P> · **Veredito: <veredito>**

**A decisão.** <1-2 frases>
**Justificação declarada.** <o que o texto diz, com localização — ou "ausente">
**Alternativa.** <qual era; foi considerada?; custo reportado?>
**Momento.** <ex-ante/ex-post; declarado?; verificável?>
**Sensibilidade.** <teste existe? resultado? evidência: caminho do artefato>
**Direção do viés.** <se errada, o resultado se move para onde; a favor ou contra a tese>
**Pergunta de banca.** <a formulação mais dura> → <a resposta disponível hoje, ou a admissão de que não há>
**AÇÃO.** <o que fazer, onde, e por quê — ou "nenhuma">
**Prioridade.** <alta | média | baixa>
```

### Tier 2 — análise média (77 decisões, ~120 palavras cada)

```
### <ID> · <Título>
`<slug>` · **Veredito: <veredito>**

<parágrafo único cobrindo justificação, alternativa e sensibilidade, com evidência citada>
**AÇÃO.** <ação ou "nenhuma"> · Prioridade: <alta|média|baixa>
```

### Tier 3 — veredito curto (15 decisões, 1 linha no ledger)

Uma linha justificada, sem seção própria. Reservado para decisões onde a alternativa é claramente pior e não há literatura em disputa: `abordagem-por-tarefas`, `limites-do-indice`, `peso-v1028`, `faixas-renda-sm`, `setores-cnae-domiciliar`, `exposicao-ocupacional-nao-setorial`, `determinismo-do-painel`, `sem-refusao-de-familias`, `honestdid-nativo-em-r`, `insumos-congelados`, `tolerancias-declaradas`, `sem-importacao-de-p`, `registro-de-artefatos`, `nove-gates-de-release`, `preservacao-v1`.

---

## 5. Distribuição por tier

| Bloco | Total | T1 | T2 | T3 |
| --- | --- | --- | --- | --- |
| A — Mensuração | 9 | 3 | 4 | 2 |
| B — PNADc descritiva | 10 | 1 | 5 | 4 |
| C — Painel CAGED | 14 | 4 | 9 | 1 |
| D — Crosswalk e tratamento | 14 | 8 | 6 | 0 |
| E — Evento | 4 | 2 | 2 | 0 |
| F — Especificação | 12 | 7 | 5 | 0 |
| G — Heterogeneidade | 10 | 4 | 6 | 0 |
| H — Multiplicidade | 8 | 4 | 3 | 1 |
| I — Identificação | 11 | 5 | 5 | 1 |
| J — Robustez | 12 | 5 | 7 | 0 |
| K — Decomposição salarial | 3 | 1 | 2 | 0 |
| L — Casos ocupacionais | 5 | 1 | 4 | 0 |
| M — Complementares | 14 | 4 | 10 | 0 |
| N — Espacial | 7 | 2 | 5 | 0 |
| O — Pré-registro | 10 | 1 | 3 | 6 |
| **Total** | **143** | **52** | **76** | **15** |

**Correção da estimativa.** Na pergunta eu estimei ~40 / 60 / 43. A atribuição real ficou em **52 / 76 / 15**. Duas razões: o Bloco D (crosswalk) e o Bloco I (identificação) são mais densos em risco do que a estimativa supunha — juntos concentram 12 decisões T1 —, e o pool T3 encolheu porque quase toda decisão procedimental ainda exige um argumento curto, não apenas um "está declarada". Se você quiser voltar mais perto da estimativa original, o corte natural é demover ~10 T1 dos Blocos J e M para T2.

**As 51 decisões Tier 1:**

`indice-oit-principal` · `regra-gradiente-mu-sigma` · `alta-exposicao-g3-g4` · `crosswalk-cod-isco-fallback` · `caged-como-fonte-principal` · `sem-medida-de-adocao` · `winsorizacao-p1-p99` · `janela-2021-2026` · `ponte-institucional-cbo-isco` · `no-score-excluido` · `seletividade-do-no-score` · `agregacao-muitos-para-muitos` · `tratamento-gradientes-1-4` · `exposicao-binaria` · `controle-estrito-not-exposed` · `minimal-como-sensibilidade` · `evento-chatgpt-nov-2022` · `data-unica-sem-staggered` · `ppml-para-contagens` · `asinh-saldo` · `cluster-cbo4` · `inferencia-cluster-t` · `sem-controles-contemporaneos` · `nivel-2-co-principal` · `dois-estimandos-distintos` · `ddd-versus-did-no-grupo` · `renda-mediana-pre-cbo` · `classificacao-de-suporte` · `subgrupos-por-composicao` · `bh-por-familia` · `familias-a-f` · `separacao-familias-a-b` · `diagnosticos-sem-ajuste` · `classificacao-pretendencias` · `diagnostico-rank-psd` · `identificacao-nao-alcancada` · `honestdid-rambachan-roth` · `confusao-escritorio-vs-ia` · `escada-de-especificacoes` · `placebo-temporal` · `proxy-fluxo-cumulativo` · `sensibilidade-winsorizacao` · `auditoria-concentracao` · `decomposicao-salarial` · `desequilibrio-dos-casos` · `rais-janela-2019-2024` · `pnadc-regra-de-maioria` · `sem-desenho-amostral-completo` · `discordancia-declarada` · `emenda-de-suporte` · `piso-de-ufs-efetivas` · `pre-registro-do-desenho`

---

## 6. Fases

Ordem por risco à tese. Cada fase é uma sessão de trabalho com entregável próprio.

| Fase | Bloco(s) | Decisões | T1 | Por que aqui |
| --- | --- | --- | --- | --- |
| **1** | I — Identificação | 11 | 5 | O veredito sobre `identificacao-nao-alcancada` enquadra todos os outros. Se a moldura exploratória se sustenta, várias fragilidades adiante deixam de ser fatais. |
| **2** | D — Crosswalk e tratamento | 14 | 7 | É onde o tratamento é construído. Se o crosswalk não se defende, nada estimado sobre ele se defende. |
| **3** | C — Painel e janela | 14 | 4 | Contém `janela-2021-2026`, o segundo risco estrutural, e as regras de construção que geram os dados. |
| **4** | F + E — Especificação e evento | 16 | 9 | Fase mais densa em T1. Estimador, inferência, controles e datação do evento. |
| **5** | G + H — Heterogeneidade e multiplicidade | 18 | 8 | Os 21 contrastes sobreviventes ao BH são a parte mais citável e a mais atacável do trabalho. |
| **6** | A + B — Mensuração e PNADc | 19 | 4 | Fundamentos conceituais e a etapa descritiva. Menor risco porque a Seção 3 não faz alegação causal. |
| **7** | J + K + L — Robustez, decomposição, casos | 20 | 7 | Módulos que sustentam ou enfraquecem a leitura principal. |
| **8** | M + N + O — Complementares, espacial, processo | 31 | 7 | Volume alto, risco por decisão mais baixo. Fases 7 e 8 podem ser combinadas. |

Fase 9, recomendada e opcional: **roteiro de defesa** (Seção 10).

---

## 7. Mapa de evidência

`results/reference/` está materializado (269 artefatos), então a maioria dos critérios 4 e 5 se responde por inspeção, não por argumento. Mapeamento para as T1 que dependem de evidência — todos os caminhos relativos a `Replication Package/V2/results/reference/artifacts/`:

| Decisão | Artefato que responde |
| --- | --- |
| `janela-2021-2026` | `caged/models/specification_ladder.csv` (degrau `06_start_2022_01`) · `caged/diagnostics/pretrend_sample_2022.csv` |
| `controle-estrito-not-exposed`, `minimal-como-sensibilidade` | `caged/models/specification_ladder.csv` (degrau `04_include_minimal_as_control`) |
| `sem-controles-contemporaneos` | `caged/models/specification_ladder.csv` (degraus `02`, `03`) |
| `exposicao-binaria` | `caged/models/specification_ladder.csv` (degrau `05_continuous_exposure`) |
| `escada-de-especificacoes` | `caged/models/specification_ladder.csv` + `specification_ladder_support.json` |
| `tratamento-gradientes-1-4`, `agregacao-muitos-para-muitos`, `regra-gradiente-mu-sigma` | `caged/treatment/treatment_variant_comparison.csv` + `treatment_variant_support.json` |
| `ponte-institucional-cbo-isco` | `caged/reconciliation/crosswalk_coverage.json` · `treatment_classification_validation.json` |
| `no-score-excluido`, `seletividade-do-no-score` | `caged/audit/c1_score_landscape.csv` · `c2_unscored_profile.csv` |
| `classificacao-pretendencias`, `identificacao-nao-alcancada` | `caged/diagnostics/pretrend_master_table.csv` · `pretrend_diagnostics.csv` · `pretrend_power_check.csv` · `pretrend_ladder_variants.csv` |
| `diagnostico-rank-psd` | `caged/diagnostics/pretrend_diagnostics_support.json` · `ddd_pretrends_support.json` |
| `honestdid-rambachan-roth` | `caged/diagnostics/honest_did_sensitivity.csv` · `honest_did_summary.csv` |
| `bh-por-familia`, `familias-a-f`, `separacao-familias-a-b`, `diagnosticos-sem-ajuste` | `caged/diagnostics/ddd_multiplicity_results.csv` · `ddd_family_support.csv` · `ddd_alternative_partitions.csv` |
| `classificacao-de-suporte`, `renda-mediana-pre-cbo` | `caged/diagnostics/ddd_family_support.csv` · `caged/models/group_did_results_support.json` · `caged/tables/table_5_2_5_income.csv` |
| `ppml-para-contagens` | `caged/models/secondary_log_flow_results.csv` |
| `nivel-2-co-principal` | `caged/models/sector_level1_vs_level2.csv` · `sector_fixed_effect_ladder.csv` |
| `dois-estimandos-distintos` | `caged/models/long_run_horizons.csv` · `long_run_horizon_reconciliation.csv` · `event_study_coefficients.csv` |
| `placebo-temporal`, `evento-chatgpt-nov-2022` | `caged/diagnostics/temporal_placebo_results.csv` · `temporal_placebo_gate.json` |
| `auditoria-concentracao`, `confusao-escritorio-vs-ia` | `caged/audit/b1_concentration.csv` · `b2_leave_one_out.csv` · `b3_drop_three_largest.csv` · `b4_unweighted_comparison.csv` · `cd_exposure_and_control_summary.json` · `d1_pre_period_comparability.csv` |
| `proxy-fluxo-cumulativo` | `caged/mechanisms/stock_proxy_result.csv` · `stock_proxy_support.csv` |
| `decomposicao-salarial` | `caged/audit/a_wage_composition_summary.json` · `a1_education_composition_shift.csv` · `a2_wage_price_composition_split.csv` · `a3_wage_within_dimension_range.csv` |
| `desequilibrio-dos-casos` | `caged/mechanisms/occupation_case_monthly_coverage.csv` · `occupation_case_preperiod_diagnostics.csv` |
| `indice-oit-principal`, `alta-exposicao-g3-g4` | `caged/mechanisms/exposure_sensitivity_results.csv` · `exposure_rank_correlations.csv` · `section3/tables/table_3_2_gradients.csv` |
| `subgrupos-por-composicao` | `caged/reconciliation/continuidade_variaveis.csv` |
| `crosswalk-cod-isco-fallback` | `section3/backing_data/data_build_diagnostics.csv` |
| `rais-janela-2019-2024` | `rais/backing_data/rais_sensitivities.csv` · `rais_pretrends.csv` |
| `pnadc-regra-de-maioria`, `sem-desenho-amostral-completo` | `pnadc/backing_data/pnadc_sensitivities.csv` · `pnadc_support.csv` · `pnadc_results.csv` |
| `discordancia-declarada` | `rais/tables/table_d_1_rais.csv` + `pnadc/tables/table_d_2_pnadc.csv` |
| `emenda-de-suporte`, `piso-de-ufs-efetivas` | `spatial/backing_data/anatel_a6_cluster_structure.csv` · `anatel_a6_status.json` · `family_f_declaration.csv` |
| `pre-registro-do-desenho` | `provenance/*.json` (timestamps) + histórico git |

Três T1 não têm artefato e serão avaliadas por argumento, o que ficará marcado como tal: `sem-medida-de-adocao`, `data-unica-sem-staggered`, `caged-como-fonte-principal`.

---

## 8. Quatro hipóteses de lacuna a testar

Não são achados. São suspeitas do levantamento que a Fase correspondente deve confirmar ou derrubar, e por isso entram com veredito inicial `pendente`:

1. **`sensibilidade-winsorizacao`** — o `RESEARCH_DESIGN.md` afirma que os módulos de robustez retêm "wage missingness and winsorization checks", mas eu não localizei um artefato com corte alternativo (p5/p95 ou sem winsorização). Se não existir, a escolha de p1/p99 é não testada e afeta o resultado mais forte do trabalho. **Fase 7.**
2. **`cluster-cbo4`** — 341 clusters é confortável para a assintótica, mas apenas **75 são tratados**, e não localizei bootstrap wild cluster. Com 75 clusters tratados e efeito concentrado numa família (31,8% da massa), a inferência pode estar otimista. **Fase 4.**
3. **`pre-registro-do-desenho`** — o pré-registro é declarado e internamente consistente, mas não localizei registro externo com timestamp independente. É autodeclarado. Isso não o invalida, mas muda o que se pode alegar sobre ele. **Fase 8.**
4. **`sem-desenho-amostral-completo`** — a limitação está declarada, mas a **magnitude** da subestimação da variância não. Sem ela, o leitor não sabe se os p-valores da família E são levemente ou gravemente otimistas. **Fase 8.**

---

## 9. Regras de honestidade da avaliação

Para que o resultado seja utilizável numa defesa, e não um documento de autoelogio ou de autoflagelação:

1. **Todo veredito cita evidência** — caminho de artefato ou localização no texto. Vereditos por argumento são marcados `[argumentativo]`.
2. **Nenhuma decisão é marcada frágil sem nomear a alternativa** que seria melhor. Crítica sem alternativa é ruído.
3. **Nenhum veredito é abrandado por ser inconveniente.** Se `insustentável` for o veredito correto, ele sai como `insustentável`.
4. **Separar "está errada" de "está certa mas indefendida".** São ações completamente diferentes e a confusão entre as duas inflaria o trabalho de revisão.
5. **Onde o Referee 2 já se pronunciou**, citar e dizer explicitamente se concordo — inclusive quando discordo.
6. **Pontos fortes são registrados como tais.** `mes-de-competencia`, `familia-f-vazia`, `emenda-de-suporte` e `discordancia-declarada` são candidatos a decisões que uma banca elogiaria.
7. **Promoção e demoção de tier em voo** são permitidas e ficam registradas no ledger com a razão. Se uma T2 revelar risco material, ela sobe.

---

## 10. Entregáveis

| Arquivo | Conteúdo | Quando |
| --- | --- | --- |
| `metodology-audit-ledger.md` | Tabela única com as 143 decisões: slug, tier, veredito, evidência, ação, prioridade. É a visão de triagem. | Criado na Fase 1, atualizado ao fim de cada fase |
| `evaluations/fase-1-identificacao.md` … `fase-8-processo.md` | Avaliação por decisão, na profundidade do tier. | Uma por fase |
| `metodology-audit-actions.md` | Lista consolidada de ações, ordenada por prioridade, com esforço estimado e localização exata no texto. | Após a Fase 8 |
| `metodology-audit-defesa.md` | Roteiro de defesa para as decisões que **não podem ser corrigidas, só defendidas** — hoje `confusao-escritorio-vs-ia`, `janela-2021-2026`, `sem-medida-de-adocao`, `subgrupos-por-composicao`. Pergunta provável + resposta + o que não conceder. | Fase 9 (recomendada) |

O `metodology-audit.md` existente não é alterado — ele é o inventário congelado contra o qual a avaliação corre.

---

## 11. Como retomar entre sessões

Cada arquivo de fase abre com um cabeçalho de estado:

```
Fase N — <bloco>
Status: <em andamento | concluída>
Avaliadas: <n>/<total>  ·  Próxima: <slug>
Promoções de tier nesta fase: <slugs + razão>
Vereditos: sólida <n> · subdocumentada <n> · frágil-reportada <n> · frágil-não-reportada <n> · insustentável <n> · pendente <n>
```

Retomar = ler o ledger + o cabeçalho da última fase, e continuar do `Próxima`.

---

## 12. O que eu espero encontrar

Registro a previsão agora para que ela possa ser conferida depois, em vez de ajustada ao resultado:

- A maioria das 143 sai `sólida` ou `sólida, subdocumentada`. O trabalho é metodologicamente cuidadoso e o inventário mostrou isso.
- O gargalo não será decisão errada, e sim **decisão certa não declarada** — sobretudo os cinco parâmetros que só existem em código ou contrato (`inferencia-cluster-t`, `diagnostico-rank-psd`, grade M do HonestDiD, semente do placebo, determinismo do painel).
- Os vereditos duros devem se concentrar em **três lugares**: a coincidência entre a fronteira do índice e a fronteira escritório/não-escritório, a ausência de qualquer mês pré-pandemia, e a inferência com 75 clusters tratados fortemente concentrados.
- Nenhuma decisão deve sair `insustentável`. Se alguma sair, o mais provável é uma lacuna de sensibilidade não testada, não um erro de desenho.
