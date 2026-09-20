# Fase 1 — Bloco I: Portões de identificação e diagnósticos

Status: **concluída**
Avaliadas: 11/11 · Próxima: Fase 2 (Bloco D — crosswalk e tratamento)
Promoções de tier nesta fase: nenhuma
Vereditos: sólida 7 · subdocumentada 2 · frágil-reportada 1 · frágil-não-reportada 1 · insustentável 0 · pendente 0

Itens de verificação abertos gerados nesta fase: 2 (V1, V2 na Seção final)

---

## Resumo da fase

O Bloco I é o mais forte do trabalho. A decisão central — declarar que a identificação causal não foi alcançada, com 51 de 51 células reprovando, em vez de garimpar uma especificação que passasse — é defensável sem ressalvas, e o aparato de diagnóstico está acima da prática corrente na literatura aplicada.

Há **uma exceção séria**, e ela é de omissão, não de erro: o procedimento de Rambachan e Roth é anunciado na §4.5, executado por completo no pacote, replicado em R — e seu resultado **não aparece em nenhum lugar da dissertação**. O resultado é adverso, e é adverso na direção que *reforça* a tese do próprio trabalho. Omiti-lo custa credibilidade sem comprar nada.

---

## I2 · Classificar tendências prévias por três critérios combinados
`classificacao-pretendencias` · Tipo S · **Veredito: sólida, subdocumentada**

**A decisão.** A classificação `pass`/`warning`/`fail` combina três testes: Wald conjunto cluster-robusto sobre todos os leads, inclinação linear por GLS através da referência, e inspeção individual dos leads por t de cluster. É uma conjunção: a célula reprova se **qualquer** um dos três acusar.

**Justificação declarada.** §4.5 e §5.2.5 descrevem o comportamento, e a §5.2.5 mostra o caso concreto: duas faixas de renda com teste conjunto não rejeitado (p = 0,417 e p = 0,277) são classificadas como falha porque têm três coeficientes pré individualmente significativos. A regra em si não é apresentada como regra em nenhum lugar do texto.

**Alternativa.** Reportar apenas o teste conjunto, como faz a maior parte da literatura aplicada. Custo de tê-la rejeitado: não reportado — o texto não diz que a regra escolhida é mais dura que a convenção, o que é justamente o argumento a favor dela.

**Momento.** Ex-ante. O artefato carrega o nome congelado `preregistered_pass_warning_fail` e nomeia cada teste em campo próprio (`cluster_robust_joint_wald_all_leads`, `gls_linear_slope_through_reference`, `individual_cluster_t_lead_inspection`). Verificável.

**Sensibilidade.** O engenho grava um campo `non_rejection_is_proof: False` e um campo `power_reading`. Evidência: `caged/diagnostics/pretrend_power_check.csv`. A regra é auditável linha a linha.

**Direção do viés.** Conservadora. Uma regra conjuntiva reprova mais do que o teste conjunto isolado, portanto **dificulta** a alegação de identificação. Se a regra estiver "errada", ela erra contra o interesse do autor em encontrar efeito. Isso é o oposto de garimpo.

**Pergunta de banca.** *"Com 22 leads e α = 5%, esperam-se por acaso cerca de 1,1 leads significativos. Uma regra que reprova por lead individual não está condenada a reprovar quase sempre, tornando o diagnóstico vazio?"* — A objeção é legítima e o trabalho tem resposta, mas não a dá: os p-valores conjuntos vão de 2×10⁻⁵² a 1,6×10⁻⁴, ou seja, **é o teste conjunto que está fazendo o trabalho**, não a contagem de leads. O critério individual só é decisivo em duas células de renda, e o texto identifica essas duas.

**AÇÃO.** Acrescentar em §4.5 (ou em nota da Tabela A.1) três frases: que a classificação é conjuntiva; que por isso é mais conservadora que o teste conjunto usado na convenção; e que nas células reprovadas o teste conjunto rejeita sozinho, com exceção nomeada das duas faixas de renda. Isso converte uma vulnerabilidade aparente em argumento.
**Prioridade.** Média.

---

## I4 · Registrar rank e PSD separadamente
`diagnostico-rank-psd` · Tipo S · **Veredito: sólida**

**A decisão.** Semidefinição positiva e rank numérico são diagnósticos distintos, com limiar declarado `max(nrow, ncol) × ε × maior valor singular`. Bloco PSD mas deficiente em rank não identifica Wald por inversa nem inclinação GLS, e recebe `not_interpretable_rank_deficient`.

**Justificação declarada.** `RESEARCH_DESIGN.md`; a consequência concreta aparece em §5.2.5 (`not_estimated` na inclinação GLS) e no texto sobre a faixa de renda alta.

**Alternativa.** Tratar covariância não invertível como falha genérica de estimação, ou inverter por pseudo-inversa e publicar o Wald resultante. A segunda é a prática que produz testes sem sentido; rejeitá-la é correto.

**Momento.** Ex-ante, com limiar declarado nas duas linguagens.

**Sensibilidade.** Confirmado em `caged/diagnostics/pretrend_power_check.csv`: todas as especificações nacionais têm `lead_covariance_full_rank = True` e PSD verdadeiro, com tolerâncias gravadas (rank ≈ 4,8×10⁻¹⁶; PSD −1×10⁻⁸). E em `caged/diagnostics/ddd_pretrends_support.json`: exatamente **5** células de grupo com `not_interpretable_rank_deficient`, batendo com o relato do texto sobre a faixa de renda alta.

**Direção do viés.** Neutra a conservadora: retira testes do conjunto em vez de acrescentar rejeições.

**Pergunta de banca.** *"O número de condição de 9.984 na covariância de leads das admissões não indica que o Wald conjunto é numericamente instável, mesmo com rank cheio?"* — Rank cheio com condição ~10⁴ é aceitável em precisão dupla e o p-valor de 10⁻⁵² tem folga de muitas ordens de grandeza. Mas o número de condição está gravado no artefato e não no texto, então a resposta existe e não está publicada.

**AÇÃO.** Nenhuma obrigatória. Opcional: acrescentar a coluna de número de condição à Tabela A.1, o que antecipa a objeção sem custo.
**Prioridade.** Baixa.

---

## I6 · Declarar que a identificação causal não foi alcançada
`identificacao-nao-alcancada` · Tipo S · **Veredito: sólida**

**A decisão.** Os testes de tendências paralelas são rejeitados em praticamente todas as células, e o trabalho declara que os coeficientes descrevem diferenças pós-evento, não efeitos.

**Justificação declarada.** §5.1, §6.2 e o contrato. A §5.1 afirma que nenhuma das 51 células examinadas passa.

**Alternativa.** As alternativas reais eram: escolher a especificação com o melhor diagnóstico e promovê-la; reportar apenas o teste conjunto e usar a célula 22–25 como validação; ou reduzir a janela até a pretendência passar. Todas as três estavam disponíveis. Nenhuma foi tomada.

**Momento.** A regra de não substituir a referência assinada por uma estimativa mais favorável está no contrato congelado (`regra-anti-garimpo`), portanto ex-ante.

**Sensibilidade.** Verificado diretamente: `caged/diagnostics/pretrend_master_table.csv` tem **52 linhas, 51 de dados, e `pretrend_status = fail` em 51 de 51**. Não há uma única célula sobrevivente na tabela mestra. A alegação do texto é literalmente exata.

**Direção do viés.** Custa ao autor a manchete. Esta decisão só tem custo.

**Pergunta de banca.** *"Se nada está identificado, o que a dissertação contribui?"* — Resposta disponível e já escrita em §6.5 e §6.6: uma medida de exposição adaptada ao país, o retrato distributivo, e diagnósticos que delimitam o que os dados podem responder. A pergunta é respondível.

**AÇÃO.** Nenhuma. Esta é a decisão mais defensável do trabalho e deve ser apresentada como escolha deliberada, não como acidente do resultado.
**Prioridade.** —

---

## I8 · Usar HonestDiD para sensibilidade a tendências prévias
`honestdid-rambachan-roth` · Tipo S · **Veredito: frágil, não reportada**

**A decisão.** O procedimento de Rambachan e Roth (2023) substituiria o binário aprova/reprova por uma medida de quanto as tendências poderiam divergir sem alterar a conclusão. Grade M de 0 a 2 em passos de 0,05, `Delta^RM` como principal e `Delta^SD` como complemento de curvatura, mirando o estimando do event study.

**Justificação declarada.** §4.5, item 6, em uma frase: *"O procedimento de Rambachan e Roth (2023) estima quanto as tendências anteriores ao evento poderiam divergir sem alterar a conclusão. Assim, o diagnóstico não se resume a aprovar ou reprovar o teste de tendências paralelas."*

**Alternativa.** Não executar o procedimento, ou executá-lo e reportar. A terceira via adotada — executar, anunciar e não reportar — é a única indefensável das três.

**Momento.** Ex-ante e integralmente implementado. `config/analysis_registry.csv` registra dois nós (`honest_did`, `honest_did_smoothness`), ambos inferenciais, nos modos `reproduce|full`. Há código dedicado (`R/honest_did.R`, `R/honest_did_sd.R`), artefatos (`honest_did_sensitivity.csv`, `honest_did_summary.csv`), duas figuras e validação cruzada Python–R dos insumos.

**Sensibilidade.** O resultado existe e é adverso. De `caged/diagnostics/honest_did_summary.csv`:

| Desfecho | Alvo | Estimativa | IC original | Status | Leitura |
| --- | --- | --- | --- | --- | --- |
| `ln_salario_real_adm` | `average_post_event_time_0_to_23` | −0,01536 (EP 0,01218) | [−0,0392; +0,0085] | **`not_robust_at_M_0`** | O intervalo já inclui zero em M = 0 |
| `asinh_saldo` | idem | −3,3079 (EP 0,7068) | [−4,693; −1,923] | `finite_within_grid` | Robusto só até M = 0,05 |

E sob `Delta^SD`, para os dois desfechos, `breakdown_below_observed_curvature = TRUE`: o ponto de quebra fica **abaixo da curvatura pré-tratamento efetivamente observada** (0,0818 no salário). No salário, 12 dos 12 pontos da grade produzem intervalo não informativo.

**Direção do viés.** Aqui está o ponto que torna a omissão difícil de defender: o resultado **reforça** a conclusão que o trabalho já defende. A §6.2 afirma que a identificação não foi alcançada; o HonestDiD diz exatamente isso, de forma quantificada, para o estimando do event study. A omissão não protege nenhuma alegação do trabalho — ela apenas cria a aparência de reporte seletivo onde não há reporte seletivo em nenhum outro lugar do trabalho.

Verificação direta: a string `HonestDiD` aparece **0 vezes** na dissertação; `Rambachan` aparece **1 vez**, apenas no anúncio da §4.5; o estimando alvo (−0,015363) aparece **0 vezes**; e não há entrada de HonestDiD no registro de 53 publicações (`config/manuscript_artifacts.csv`) nem em `config/numeric_claims.csv`.

**Pergunta de banca.** *"O senhor anuncia Rambachan e Roth na estratégia empírica. Onde está o resultado?"* — Hoje não há resposta. É a pergunta mais barata de fazer e a mais custosa de não ter respondido, porque o examinador só precisa comparar a §4.5 com o índice de tabelas.

**AÇÃO.** Três coisas, na ordem:
1. Acrescentar ao Apêndice A um quadro com o resultado do HonestDiD para os dois desfechos: alvo, estimativa, IC original, status em M = 0, primeiro M com intervalo aberto, e a leitura de `Delta^SD` contra a curvatura observada.
2. Acrescentar uma frase em §5.1 dizendo que, sob o procedimento anunciado na §4.5, o diferencial salarial do event study não é robusto nem em M = 0 — e que isso **converge** com a conclusão de não identificação, em vez de contrariá-la.
3. Declarar por que o procedimento cobre 2 dos 5 desfechos e não os cinco (ver item V2 de verificação).

**Prioridade.** **Alta.** É a única ação da Fase 1 que eu consideraria bloqueante para circulação.

---

## I11 · Nomear a confusão entre exposição e trabalho de escritório
`confusao-escritorio-vs-ia` · Tipo S · **Veredito: frágil, reportada**

**A decisão.** Declarar, em §6.3, que a fronteira desenhada pelo índice e a fronteira entre trabalho de escritório e não-escritório são quase a mesma, de modo que um choque tecnológico e um choque de demanda sobre trabalho administrativo produzem o mesmo coeficiente — e que nenhuma econometria os separa quando a variável de tratamento não os distingue.

**Justificação declarada.** §6.3, em prosa, com os números de concentração (uma família com 31,8% das admissões pré-tratamento do grupo tratado; as cinco maiores somando 65,4%).

**Alternativa.** Havia duas alternativas construtivas, e nenhuma foi tentada: (i) uma tabela de balanceamento pré-tratamento entre tratados e controle, que mostraria o problema em vez de descrevê-lo; (ii) um contraste dentro do trabalho de escritório — comparar ocupações administrativas de alta e baixa pontuação entre si —, que é a única forma de separar tecnologia de ciclo com os dados existentes. A §6.6 registra a segunda como agenda, mas não como tentativa.

**Momento.** A declaração é ex-post, na interpretação. Isso é apropriado: é um diagnóstico sobre o resultado, não uma regra de desenho.

**Sensibilidade.** Os artefatos quantificam o problema com muito mais força do que o texto. De `caged/audit/d1_pre_period_comparability.csv`:

| Indicador pré-tratamento | Tratados (75) | Controle (265) |
| --- | --- | --- |
| Participação com ensino superior | **19,7%** | **4,0%** |
| Salário real médio de admissão | R$ 2.300,58 | R$ 1.962,51 |
| Idade média | 28,9 | 33,8 |
| Desvio-padrão do crescimento mensal | 8,3% | 14,0% |
| Amplitude sazonal | 27,3% | 44,7% |

E de `caged/audit/b1_concentration.csv`: no grupo tratado a maior família responde por 31,8% das admissões, as três maiores por 54,1% e as dez maiores por **80,4%**; os três maiores códigos são 4110, 4211 e 4221 — escritório, caixas e recepção. No controle, a maior família responde por 14,0%.

De `caged/audit/cd_exposure_and_control_summary.json`: `binary_treatment_is_monotone_in_score = false`, com faixa de sobreposição [0,28; 0,32] contendo 64 famílias — 3 tratadas, 30 de controle e 31 excluídas como exposição mínima.

A razão de quase 5 para 1 na participação de ensino superior é o número mais eloquente do conjunto e **não aparece no texto**. É ele que mostra que tratados e controle não são o mesmo tipo de trabalho medido com exposições diferentes: são populações estruturalmente distintas.

**Direção do viés.** Indeterminada em sinal, e isso é o que torna o problema grave em vez de contornável. Um ciclo de aperto monetário sobre comércio e serviços administrativos produz o mesmo sinal negativo que substituição tecnológica. O trabalho não pode dizer para que lado erra.

**Pergunta de banca.** *"Seu grupo tratado é 80% composto por dez famílias de escritório, com cinco vezes mais graduados que o controle. O senhor não está estimando o ciclo do trabalho administrativo brasileiro e chamando de exposição à IA?"* — A resposta honesta hoje é: possivelmente sim, e o desenho não distingue. O texto já concede isso. O que falta é ter a tabela na mão para mostrar que a concessão é informada, não retórica.

**AÇÃO.** Duas:
1. Promover `d1_pre_period_comparability.csv` a **tabela de balanceamento pré-tratamento no Apêndice A**. Uma tabela de balanceamento é padrão em DiD e sua ausência é notável; incluí-la transforma a fragilidade de admissão em evidência.
2. Em §6.3, substituir a formulação em prosa pela referência à tabela e acrescentar a razão de ensino superior (19,7% contra 4,0%), que é o número que sustenta o argumento.

**Prioridade.** Alta (a tabela), média (a reescrita).

---

## Decisões Tier 2

### I1 · Avaliar suporte antes de coeficientes
`suporte-antes-de-coeficientes` · **Veredito: sólida**

Regra estrutural: suporte calculado e publicado antes de qualquer coeficiente, e nenhum critério de continuidade dependendo do coeficiente de tratamento. A verificação mais forte é comportamental, não declaratória — na extensão espacial a regra efetivamente interrompeu o exercício e deixou 12 posições vazias (`spatial/backing_data/family_f_declaration.csv`), o que é a prova de que o portão não é decorativo. Os arquivos `*_support.json` acompanham cada módulo. Alternativa (estimar e depois julgar suporte) é exatamente o que produz seleção por resultado.
**AÇÃO.** Nenhuma. · Prioridade: —

### I3 · Estimar pretendência sobre o modelo e a amostra exatos
`pretendencia-modelo-exato` · **Veredito: sólida**

Verificado em `caged/diagnostics/pretrend_power_check.csv`: o campo `formula` grava `admissoes ~ i(event_time, treated_main, ref=-1) | cbo_4d + periodo`, com `n_obs` e `minimum_clusters` idênticos ao resultado reportado e referência em −1. O teste roda sobre o modelo publicado, não sobre uma versão simplificada. Está acima da prática corrente, em que a pretendência é frequentemente testada num modelo auxiliar com janela e agrupamento diferentes — o que produz diagnóstico que não se aplica ao resultado. Merece ser dito no texto, mas o texto não perde validade por omiti-lo.
**AÇÃO.** Opcional: uma frase em §A.1 registrando que o teste usa o modelo exato. · Prioridade: baixa

### I5 · Publicar coeficientes com diagnósticos indefinidos por construção
`rank-deficiente-visivel` · **Veredito: sólida**

Nas 5 células deficientes em rank, coeficientes e erros-padrão permanecem publicados enquanto Wald e GLS ficam ausentes por construção, com rótulo próprio. A alternativa — suprimir a célula inteira — esconderia informação estimável; a alternativa oposta — publicar um Wald por pseudo-inversa — publicaria um teste sem conteúdo. A escolha do meio é a correta e o rótulo `not_interpretable_rank_deficient` diz ao leitor exatamente o que falta.
**AÇÃO.** Nenhuma. · Prioridade: —

### I7 · Manter resultados falhos visíveis como exploratórios
`resultados-exploratorios-declarados` · **Veredito: sólida, subdocumentada**

A prática está cumprida: falhas de pretendência, blocos deficientes e rótulos de suporte fino permanecem visíveis nos outputs e nas tabelas. Mas há uma imprecisão que corrói justamente esta decisão. A §5.2.3 afirma que a célula 22–25 do salário é *"o único diagnóstico de pré-tendências que não falha entre 100 contrastes"*, enquanto `caged/diagnostics/ddd_pretrends_support.json` registra `group_pretrend_status_counts: {fail: 90, not_interpretable_rank_deficient: 5, pass: 2, warning: 3}` e `ddd_pretrend_status_counts: {fail: 93, pass: 2, warning: 5}` — isto é, **duas** aprovações em cada família, não uma. O próprio Apêndice A.4 exibe a linha Indígena/salário com `pass` nas duas colunas de pretendência. Um leitor que confira o apêndice encontra a contradição, e o custo recai sobre a credibilidade de uma decisão que, no mérito, está correta.
**AÇÃO.** Corrigir "único" na §5.2.3 para a contagem exata, ou qualificar precisamente a qual família, teste e desfecho a unicidade se refere. · Prioridade: média

### I10 · Documentar a diferença de diagnóstico em relação ao artigo de referência
`diferenca-com-canaries` · **Veredito: sólida** · [argumentativo]

Registrar que Brynjolfsson, Chandar e Chen testaram poder preditivo pré-difusão e não o encontraram — de modo que a falha de pretendência aqui é uma **diferença em relação ao caso americano**, não um problema compartilhado pela literatura — é a leitura desfavorável ao autor, e é a correta. A alternativa retórica disponível (apresentar a falha como limitação genérica do campo) estava à mão e foi recusada. Sem artefato correspondente; avaliação por argumento.
**AÇÃO.** Nenhuma. · Prioridade: —

---

## Decisão Tier 3

**I9 · `honestdid-nativo-em-r` — sólida.** HonestDiD roda em R recebendo coeficientes e covariâncias exportados dos modelos ajustados independentemente em R, nunca de resultado do Python (`caged/replication/complete_r/honest_did_event_coefficients.csv`), o que preserva a independência da replicação cruzada. Decisão de engenharia correta e sem alternativa superior.

---

## Itens de verificação abertos

**V1 — Base do "65,4%" da §6.3.** O texto diz que as cinco maiores famílias tratadas somam 65,4% das admissões pré-tratamento; `caged/audit/b1_concentration.csv` registra `top5_share_pct = 66,83` sobre 27.946.025 admissões, enquanto `d1_pre_period_comparability.csv` registra 9.443.185 admissões pré-tratamento para os tratados. As bases parecem diferentes (período completo contra pré-tratamento), o que explicaria a divergência sem erro. **Confirmar qual artefato sustenta o 65,4% antes de tocar no número.** Não é um achado de erro.

**V2 — Cobertura do HonestDiD.** O procedimento cobre `ln_salario_real_adm` e `asinh_saldo`, mas não admissões, desligamentos e fluxo bruto. Verificar se a restrição é técnica (os três são PPML e o `HonestDiD` opera sobre o vetor de coeficientes de event study com covariância, o que é viável) ou uma escolha declarada em algum lugar do contrato. A resposta muda a redação da ação 3 de I8.

---

## Balanço da fase contra a previsão

A previsão da Seção 12 do plano dizia que a maioria sairia `sólida` ou `sólida, subdocumentada`, e que o gargalo seria decisão certa não declarada. **Confirmado nesta fase:** 9 das 11 são sólidas no mérito, e as duas ações de maior prioridade são ambas de reporte — publicar o HonestDiD que já existe, e promover a tabela de balanceamento que já existe. Nenhuma decisão do Bloco I precisa ser mudada; duas precisam ser mostradas.

A previsão também dizia que nenhuma decisão sairia `insustentável`. Mantida nesta fase, mas com a ressalva de que `honestdid-rambachan-roth` chega perto: não pelo desenho, que está correto, e sim pela lacuna entre o que foi anunciado e o que foi publicado.
