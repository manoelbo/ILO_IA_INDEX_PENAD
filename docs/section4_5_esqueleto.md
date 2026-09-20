# Esqueleto Das Seções 4 E 5

Este documento organiza a versão atual das Seções 4 e 5 da dissertação. Ele deve servir como roteiro de escrita, não como relatório bruto de resultados. A estrutura foi inspirada no estilo já usado nas Seções 2 e 3: cada subseção começa delimitando o problema, explica a escolha metodológica e só depois apresenta tabelas ou figuras.

A mudança central em relação às versões anteriores é narrativa. A hipótese não deve ser apresentada como "queda no salário de admissão". A hipótese da dissertação é mais ampla: a difusão da IA generativa pode estar associada a uma **reconfiguração do mercado de trabalho formal**, observável em admissões, desligamentos, salários, saldo líquido e composição dos trabalhadores admitidos ou desligados.

## Orientação Geral De Escrita

O texto deve ser visual-first. A seção empírica deve funcionar como uma sequência de figuras interpretadas, com tabelas de coeficientes entrando como apoio e auditoria. A inspiração visual vem de *Canaries in the Coal Mine*: séries normalizadas, painéis por idade, comparação entre grupos e leitura do descolamento após novembro de 2022.

A lógica de apresentação deve ser:

1. Primeiro, mostrar o desenho empírico e a construção da amostra.
2. Depois, mostrar que o efeito médio nacional é fraco ou pouco robusto.
3. Em seguida, mostrar que a heterogeneidade por idade e grupos ocupacionais revela padrões mais informativos.
4. Por fim, separar claramente robustez, conectividade e resultados nulos.

## Fontes De Verdade Dos Resultados

Usar estes arquivos como referência antes de escrever qualquer número:

| Bloco | Artefato principal | Uso no texto |
|---|---|---|
| Decisão metodológica | `outputs/dissertation_section4/section4_final_model_decision_report.md` | Justificar modelo base e mudanças metodológicas |
| Modelo nacional | `outputs/dissertation_section4/final_event_study/tables/main_results_3plus1.md` | Resultados médios de admissões, desligamentos e salários |
| Salário real | `outputs/dissertation_section4/final_event_study/tables/real_wage_main_results_3plus1.md` | Mostrar que deflacionar por IPCA não muda a leitura com FE de mês |
| Saldo líquido | `outputs/dissertation_section4/final_event_study/tables/net_flow_results.md` | Complementar fluxos de admissão e desligamento |
| Grupos ocupacionais | `outputs/dissertation_section4/manual_occupation_groups_extension/occupation_groups_report.md` | Principal extensão substantiva |
| Auditoria dos grupos | `outputs/dissertation_section4/manual_occupation_groups_extension/audit/manual_group_cbo_audit.md` | Listar CBOs incluídas em cada grupo |
| Conectividade | `outputs/dissertation_section4/connectivity_extension/section4_connectivity_report.md` | Extensão espacial, preferencialmente apêndice |
| Seleção de achados | `outputs/dissertation_section4/result_evaluation/top_30_results_for_dissertation.md` | Inventário de resultados; não copiar mecanicamente |

Nota: a seleção `Top 30` é um insumo de triagem. Ela ajuda a localizar achados, mas a decisão final de escrita deve respeitar pretrends, clareza narrativa e risco de p-hacking.

## Decisões Metodológicas Que Precisam Aparecer

| Tema | Decisão atual | Como escrever |
|---|---|---|
| Tratamento principal | Gradientes `G1-G4` vs. `Not Exposed` | "O grupo tratado reúne ocupações com exposição relevante segundo a classificação da OIT; o controle principal é formado apenas por ocupações `Not Exposed`." |
| Controle | `Minimal Exposure` fora do controle principal | "O grupo de exposição mínima é excluído do controle base para preservar contraste limpo." |
| Crosswalk | CBO/MTE para ISCO/OIT, sem fallback numérico solto | "A amostra final privilegia correspondências ocupacionais institucionalmente defensáveis, ainda que isso reduza cobertura." |
| Outcomes | Admissões, desligamentos, salários reais e saldo líquido | "Os outcomes capturam margens distintas da reconfiguração do mercado formal." |
| Saldo líquido | Complementar, não substituto | "O saldo resume a direção líquida dos fluxos, mas pode esconder movimentos opostos em admissões e desligamentos." |
| Pretrends | Hard gate de interpretação causal | "Resultados com falha de pretrend são tratados como sugestivos ou exploratórios." |
| Conectividade | Apêndice/extensão | "A evidência espacial é informativa, mas não deve organizar a contribuição principal." |

# 4 Estratégia Empírica

A Seção 4 deve explicar como a pergunta empírica é transformada em desenho de identificação. Ela não deve antecipar todos os resultados. O objetivo é fazer o leitor entender por que o CAGED permite observar a dinâmica formal depois do ChatGPT, como a exposição ocupacional é mapeada para CBO e quais hipóteses sustentam a comparação entre ocupações expostas e não expostas.

## 4.1 Do Retrato Da Exposição À Dinâmica Do Mercado Formal

**Função da subseção:** fazer a ponte entre as Seções 2 e 3 e a análise causal/exploratória com CAGED.

**Mensagem central:** a PNAD mostra quem está exposto; o CAGED permite observar se ocupações expostas tiveram trajetórias diferenciais de admissão, desligamento e salário depois da difusão do ChatGPT.

Texto sugerido:

> As seções anteriores mostram que a exposição à IA no Brasil está concentrada em ocupações formais, administrativas, técnicas e profissionais. Esta seção desloca a análise do retrato transversal para a dinâmica temporal do emprego formal, usando o CAGED para investigar se ocupações mais expostas apresentaram mudanças diferenciais após o lançamento do ChatGPT.

**Figura sugerida:** linha do tempo da estratégia empírica.

- Janela pré e pós.
- Marco em 30/11/2022.
- Referência do event study em `t=-1`.
- Unidade principal: CBO 4 dígitos por mês.

## 4.2 O Choque Do ChatGPT Como Evento De Difusão Tecnológica

**Função da subseção:** justificar o evento temporal usado no DiD/event study.

**Mensagem central:** o lançamento público do ChatGPT não é tratado como adoção imediata por todas as firmas, mas como início de uma difusão rápida e visível da IA generativa.

Pontos que devem entrar:

- Data do choque: 30 de novembro de 2022.
- Adoção efetiva é heterogênea e não observada diretamente.
- O desenho mede mudanças diferenciais em ocupações mais expostas depois do choque, não adoção direta da tecnologia.
- A interpretação deve ser mais cuidadosa que "efeito causal puro da IA".

**Subtítulo alternativo:** "Novembro De 2022 Como Quebra De Exposição, Não Como Adoção Universal".

## 4.3 Dados Do CAGED E Construção Do Painel Ocupação-Mês

**Função da subseção:** explicar a unidade de análise e a diferença em relação ao artigo *Canaries*.

**Mensagem central:** o CAGED observa fluxos administrativos do mercado formal. Por isso, a dissertação adapta a lógica do artigo de referência para admissões, desligamentos e salários de entrada/saída, em vez de replicar um painel firma-estoque.

Pontos que devem entrar:

- Fonte: CAGED.
- Unidade principal: CBO 4 dígitos por mês.
- Período de análise.
- Diferença entre fluxo e estoque.
- Outcomes construídos a partir de admissões e desligamentos.
- Limitação: não é a mesma unidade firma-quintil-mês do artigo de referência.

**Figura sugerida:** pipeline CAGED -> CBO -> painel CBO-mês.

## 4.4 Da CBO Ao Índice Da OIT: Crosswalk E Amostra Elegível

**Função da subseção:** defender a mudança metodológica mais importante do trabalho.

**Mensagem central:** a versão final usa apenas uma correspondência mais defensável entre CBO e OIT, mesmo que isso reduza cobertura e enfraqueça resultados.

Pontos que devem entrar:

- O índice da OIT está em ISCO-08.
- A CBO se relaciona historicamente com a ISCO-88.
- A ponte final evita fallback numérico solto.
- CBOs sem match MTE ou sem score ficam fora da amostra principal.
- `No score` não entra.
- `Minimal Exposure` não entra no controle principal.

**Figura sugerida:** diagrama do crosswalk.

```mermaid
flowchart LR
  A["CAGED: CBO 2002"] --> B["Crosswalk MTE/CBO"]
  B --> C["Família ISCO"]
  C --> D["ILO Global Index"]
  D --> E["Gradiente OIT por CBO"]
  E --> F["Painel analítico CBO-mês"]
```

## 4.5 Definição De Tratamento: Exposição Relevante Versus Não Exposição

**Função da subseção:** deixar claro o contraste principal.

**Mensagem central:** o modelo base compara ocupações nos gradientes de exposição da OIT com ocupações não expostas. O grupo de exposição mínima é excluído para evitar contaminar o controle.

Especificação base:

- Tratados: `Exposed: Gradient 1`, `Exposed: Gradient 2`, `Exposed: Gradient 3`, `Exposed: Gradient 4`.
- Controle: `Not Exposed`.
- Excluídos: `Minimal Exposure`, `No score`, sem match MTE e classificações inválidas.

Nota para escrita:

> A regra aceita G1-G4 como tratados, mas a classificação final observada no CAGED não contém CBOs em `Exposed: Gradient 4`. Na prática, o contraste observado é G1-G3 versus `Not Exposed`. Isso deve ser reportado como característica da amostra, não como erro.

## 4.6 Especificação Econométrica

**Função da subseção:** apresentar o DiD/event study sem sobrecarregar o leitor.

**Mensagem central:** o modelo compara a mudança pós-ChatGPT nas ocupações expostas em relação às não expostas, controlando por efeitos fixos de ocupação e mês.

Modelo base:

```text
Y_{c,t} = beta post_treat_{c,t} + X_{c,t}'gamma + alpha_c + delta_t + epsilon_{c,t}
```

Onde:

- `c` é a CBO 4 dígitos.
- `t` é o mês.
- `alpha_c` são efeitos fixos de ocupação.
- `delta_t` são efeitos fixos de mês.
- `post_treat` é a interação entre pós-ChatGPT e tratamento.
- Erros-padrão são clusterizados por CBO 4 dígitos.

Cuidados de interpretação:

- Controles contemporâneos de composição podem ser pós-tratamento.
- Por isso, a versão sem controles ou com controles pré-tratamento interagidos deve aparecer como robustez importante.
- Event studies e pretrends definem o grau de confiança causal.

## 4.7 Outcomes: Fluxos, Salários E Saldo Líquido

**Função da subseção:** explicar que a hipótese não está presa ao salário.

**Mensagem central:** a reconfiguração do mercado formal pode aparecer em quatro margens: entrada, saída, remuneração e saldo líquido.

Outcomes principais:

- `ln_admissoes`: fluxo de entrada.
- `ln_desligamentos`: fluxo de saída.
- `ln_salario_real_adm`: salário real de admissão.
- `ln_salario_real_desl`: salário real de desligamento, complementar.

Outcome complementar:

- `asinh_saldo`: transformação do saldo líquido `admissões - desligamentos`.
- `saldo_per_pre_adm`: saldo normalizado pelas admissões pré-ChatGPT.

Como escrever o saldo:

> O saldo líquido resume a direção líquida do fluxo formal, mas não substitui admissões e desligamentos separadamente. Um saldo estável pode esconder queda simultânea de admissões e desligamentos; por isso, o saldo é interpretado como síntese complementar.

## 4.8 Heterogeneidade E Mecanismos

**Função da subseção:** antecipar por que a análise não termina no efeito médio nacional.

**Mensagem central:** se a IA afeta a porta de entrada do mercado, o efeito pode estar concentrado em jovens e em ocupações digitalizadas, mesmo quando o efeito médio nacional é fraco.

Blocos de heterogeneidade:

- Renda.
- Idade.
- Sexo.
- Escolaridade.
- Raça/cor.
- Faixas etárias estilo *Canaries*: 22-25, 26-30, 31-34, 35-40, 41-49, 50+.

Grupos ocupacionais que devem aparecer no texto:

1. **Núcleo de Software e TI**.
2. **Atendimento e Contato com Cliente**.
3. **Finanças, Contabilidade e Administração**.
4. **Comunicação, Linguagem e Conteúdo**.

Subtítulo alternativo:

> "Onde A Reconfiguração Deve Aparecer Primeiro: Jovens E Ocupações Digitalizadas".

## 4.9 Validação, Robustez E Critérios De Leitura

**Função da subseção:** proteger a seção de overclaiming.

**Mensagem central:** o trabalho adota uma hierarquia explícita de evidência. Resultados com pretrend aprovado podem sustentar leitura mais forte; resultados com pretrend falho entram como sugestivos ou limitação.

Critérios:

- Pretrend aprovado: pode entrar como evidência mais forte.
- Pretrend falho: mencionar apenas como sugestivo, exploratório ou limitação.
- Sem pretrend formal: não classificar como headline causal.
- Resultado exploratório sem match MTE: apêndice ou nota de mecanismo, nunca evidência principal.

# 5 Resultados

A Seção 5 deve ser escrita como uma narrativa de evidências. O ponto de partida é o modelo nacional, mas o ponto substantivo mais forte está na heterogeneidade por idade e nos grupos ocupacionais. A seção deve evitar transformar todos os resultados em uma lista de coeficientes. A pergunta que organiza o capítulo é: **onde a reconfiguração aparece, onde ela não aparece, e com que grau de confiança?**

## 5.1 Validação Do Desenho: O Que Pode Ser Lido Como Evidência Forte

**Função da subseção:** abrir os resultados com a regra de interpretação.

**Mensagem central:** antes de discutir magnitude, é preciso verificar se os event studies sustentam a comparação entre tratados e controles.

Material visual:

- Figura com event studies nacionais para:
  - admissões;
  - desligamentos;
  - salário real de admissão;
  - saldo líquido.

Como escrever:

> Os event studies cumprem dois papéis. Primeiro, mostram a dinâmica dos efeitos ao redor do lançamento do ChatGPT. Segundo, funcionam como diagnóstico de validade do desenho: quando há divergência prévia entre tratados e controles, a interpretação causal deve ser reduzida.

## 5.2 Efeitos Médios Nacionais: Reconfiguração Sem Ruptura Agregada

**Função da subseção:** mostrar o resultado médio do modelo base.

**Mensagem central:** no agregado nacional, não há evidência robusta de uma ruptura média forte nas ocupações expostas. Isso não derruba a hipótese; desloca a análise para heterogeneidade e mecanismos.

Resultados atuais a mencionar:

| Outcome | Coeficiente | p-valor | Leitura |
|---|---:|---:|---|
| Admissões | -0,0309 | 0,241 | Sinal negativo, sem significância; pretrend problemático |
| Desligamentos | -0,0417 | 0,102 | Sinal negativo, sugestivo; pretrend problemático |
| Salário real de admissão | -0,0207 | 0,140 | Sinal negativo, pretrend mais limpo, mas sem significância convencional |
| Salário real de desligamento | 0,0067 | 0,734 | Sem evidência de efeito médio |

Frase sugerida:

> O modelo nacional sugere que, no nível médio das ocupações formais, a exposição à IA não se traduz em uma queda agregada estatisticamente clara de admissões, desligamentos ou salários. A ausência de efeito médio forte é um resultado substantivo: se há reconfiguração, ela parece concentrada em margens específicas, perfis demográficos ou grupos ocupacionais.

## 5.3 Fluxos De Entrada, Saída E Saldo Líquido

**Função da subseção:** conectar admissões, desligamentos e saldo como margens complementares.

**Mensagem central:** admissões e desligamentos devem ser lidos juntos. O saldo ajuda a resumir a direção líquida, mas seus pretrends limitam a interpretação causal.

Resultados atuais:

| Medida | Coeficiente | p-valor | Pretrend | Leitura |
|---|---:|---:|---|---|
| `asinh(saldo)` | -0,6597 | 0,081 | Falha | Sinal líquido negativo, sugestivo |
| `saldo/admissões pré` | 0,0119 | 0,537 | Falha | Sem evidência líquida robusta |
| `saldo/fluxo total` | 0,0042 | 0,629 | Não usar como headline | Sem evidência líquida robusta |

Como escrever:

> O saldo líquido aponta para uma possível contração relativa em algumas especificações, mas as falhas de pretrend impedem tratá-lo como evidência causal central. Sua função na dissertação é complementar a leitura de admissões e desligamentos, não substituí-las.

Figura sugerida:

- Painel com admissões, desligamentos e saldo líquido no mesmo padrão visual.
- Marcar claramente quais séries têm pretrend problemático.

## 5.4 Heterogeneidade Demográfica: A Porta De Entrada Do Mercado

**Função da subseção:** trazer a inspiração central de *Canaries*.

**Mensagem central:** a literatura internacional sugere que jovens são mais afetados porque entram no mercado em ocupações expostas no momento da difusão tecnológica. A dissertação deve testar essa margem, mas sem forçar resultado quando a evidência não aparece.

Material visual:

- Painéis por idade no estilo *Canaries*.
- Faixas: 22-25, 26-30, 31-34, 35-40, 41-49, 50+.
- Mostrar séries normalizadas a partir do período pré-ChatGPT.

Como escrever:

> A análise por coortes de carreira é central porque trabalhadores jovens ajustam-se na margem de entrada. Em ocupações onde a IA reduz a demanda por tarefas iniciais, o efeito deve aparecer primeiro nas admissões e salários de entrada desses grupos.

Cuidados:

- Não usar `idade_media_adm` como se fosse efeito causal sobre jovens.
- Preferir reconstrução por microdados e faixas etárias.
- Distinguir resultado nacional de resultado por grupo ocupacional.

## 5.5 Grupos Ocupacionais: Onde A Reconfiguração Aparece Com Mais Clareza

**Função da subseção:** apresentar a principal extensão substantiva.

**Mensagem central:** o efeito médio nacional é fraco, mas grupos ocupacionais diretamente ligados a tarefas digitais e cognitivas mostram padrões mais alinhados à hipótese de reconfiguração.

### 5.5.1 Núcleo De Software E TI

**Papel no texto:** principal evidência de mecanismo.

Grupo:

- `2123`, `2124`, `3171`, `3172`.

Resultados a mencionar:

- Efeito médio em salário real de admissão: `-0,0425***`, mas com pretrend falho.
- Coorte 22-25: salário real de admissão `-0,0477***`, `p=0,000`, com pretrend aprovado.
- Faixa 14-24 do projeto: salário real de admissão `-0,0940**`, `p=0,021`, com pretrend aprovado.

Como escrever:

> O Núcleo de Software e TI é o grupo em que a hipótese aparece com mais força substantiva. O efeito médio do grupo deve ser lido com cautela por causa do pretrend, mas a heterogeneidade jovem apresenta um padrão mais consistente: trabalhadores no início da carreira mostram queda nos salários reais de admissão após o choque.

Figuras prioritárias:

- Painéis normalizados por idade para Software/TI.
- Forest plot de efeitos por outcome.
- Heatmap de heterogeneidade jovem/perfil.

### 5.5.2 Atendimento E Contato Com Cliente

**Papel no texto:** grupo de comparação ligado a tarefas textuais, voz e atendimento.

Mensagem esperada:

> Atendimento e contato com cliente é teoricamente relevante porque IA generativa atua diretamente em interação textual e suporte. A evidência deve ser apresentada como triagem de mecanismo: útil para comparar com Software/TI, mas não como headline se os resultados forem instáveis.

Figura sugerida:

- Painel normalizado por idade, ao lado de Software/TI.
- Ou linha no forest plot dos quatro grupos.

### 5.5.3 Finanças, Contabilidade E Administração

**Papel no texto:** grupo alinhado à OIT e à literatura sobre tarefas administrativas.

Mensagem esperada:

> Finanças, contabilidade e administração representam ocupações de escritório com alta exposição a tarefas cognitivas padronizadas. Mesmo quando os coeficientes não são fortes, o grupo ajuda a mostrar se a reconfiguração está restrita a tecnologia ou se se espalha para rotinas administrativas.

Figura sugerida:

- Forest plot por outcome.
- Heatmap de perfis.

### 5.5.4 Comunicação, Linguagem E Conteúdo

**Papel no texto:** grupo teoricamente próximo à IA generativa, mas com menor poder amostral.

Mensagem esperada:

> Comunicação, linguagem e conteúdo é um grupo conceitualmente importante porque LLMs atuam diretamente sobre escrita, tradução, marketing e produção textual. No entanto, se o número de CBOs ou observações for pequeno, os resultados devem entrar como evidência exploratória ou apêndice.

Figura sugerida:

- Painel comparativo entre os quatro grupos.
- Marcar status de poder/pretrend no gráfico ou legenda.

### 5.5.5 Síntese Dos Grupos

Figura principal recomendada:

- **Figura 5:** comparação entre os quatro grupos ocupacionais.

Formato preferido:

- Forest plot com coeficientes por grupo e outcome.
- Separar visualmente resultados com pretrend aprovado, falho ou sem teste.

Mensagem final da subseção:

> A evidência por grupos ocupacionais sugere que a reconfiguração não aparece de forma homogênea no mercado formal. Ela é mais visível em ocupações ligadas a software e TI, especialmente entre jovens, enquanto os demais grupos funcionam como contraste e teste de mecanismo.

## 5.6 Conectividade Municipal: Extensão Espacial, Não Resultado Central

**Função da subseção:** decidir o papel da conectividade.

**Mensagem central:** a conectividade é uma hipótese interessante de adoção, mas os resultados atuais não são fortes o bastante para estruturar a seção principal.

Resultados atuais:

| Outcome | Coeficiente DDD | p-valor | Pretrend | Leitura |
|---|---:|---:|---|---|
| Admissões | -0,0161 | 0,018 | Falha | Sugestivo, não causal forte |
| Desligamentos | -0,0053 | 0,517 | Falha | Sem evidência robusta |
| Salário real de admissão | -0,0009 | 0,834 | Falha | Sem evidência robusta |
| Salário real de desligamento | -0,0054 | 0,272 | Falha | Sem evidência robusta |

Recomendação:

- Não usar conectividade como seção central.
- Colocar em apêndice ou em parágrafo curto no fim da Seção 5.
- Manter apenas se for útil para mostrar que a hipótese espacial foi testada e não encontrou evidência forte.

Texto sugerido:

> A conectividade municipal é uma extensão natural, pois adoção de IA depende de infraestrutura digital. Contudo, a evidência atual é limitada: a especificação mais forte mostra queda adicional pequena em admissões em municípios mais conectados, mas os testes de pretrend falham. Por isso, a conectividade é tratada como evidência sugestiva e não como resultado central da dissertação.

## 5.7 Robustez, Resultados Nulos E Limites

**Função da subseção:** mostrar honestidade metodológica sem gerar ruído.

**Mensagem central:** alguns testes enfraquecem a narrativa forte, mas fortalecem a credibilidade do trabalho ao mostrar limites claros.

Entram no texto principal:

- Salário real versus nominal: não muda a leitura porque FE de mês absorve o deflator comum.
- Modelo com e sem controles contemporâneos: importante porque controles de composição podem ser pós-tratamento.
- `Minimal Exposure` no controle como robustez ampla.
- Saldo líquido como complemento, com pretrend reportado.
- Pretrends como critério de interpretação.

Entram no apêndice:

- Conectividade municipal.
- Resultados completos de heterogeneidade.
- Tabelas longas de grupos ocupacionais.
- Especificações exploratórias sem match MTE.

Evitar no corpo principal:

- Muitos cutoffs alternativos sem motivação.
- Resultados legados do crosswalk antigo.
- Tabelas com dezenas de linhas que não mudam a interpretação.

## 5.8 Síntese Interpretativa

**Função da subseção:** fechar o capítulo com uma resposta equilibrada.

Mensagem sugerida:

> Os resultados não indicam uma ruptura média ampla do emprego formal em ocupações expostas à IA após o lançamento do ChatGPT. A evidência nacional agregada é fraca e, em alguns outcomes, limitada por pretrends. No entanto, a análise por grupos ocupacionais revela padrões mais consistentes em ocupações de Software e TI, especialmente entre trabalhadores jovens. Assim, a dissertação aponta menos para um choque agregado imediato e mais para uma reconfiguração localizada, concentrada na porta de entrada de ocupações digitalizadas.

# Matriz De Decisão Para A Escrita

| Bloco | Entra no texto principal? | Papel | Justificativa |
|---|---|---|---|
| Modelo nacional base | Sim | Espinha dorsal | Define o estimando principal, mesmo com efeitos médios fracos |
| Event studies nacionais | Sim | Validação | Mostram pretrends e evitam overclaiming |
| Salário real | Sim | Robustez essencial | Confirma que o resultado não depende de salário nominal |
| Saldo líquido | Sim, curto | Complemento de fluxos | Ajuda a falar de reconfiguração líquida, mas pretrends limitam |
| Heterogeneidade jovem | Sim | Evidência substantiva | Conecta a dissertação ao artigo de referência |
| Núcleo de Software e TI | Sim | Principal mecanismo | Resultado mais claro, especialmente entre jovens |
| Atendimento e Contato com Cliente | Sim, como contraste | Triagem de mecanismo | Grupo teoricamente relevante para IA generativa |
| Finanças, Contabilidade e Administração | Sim, como contraste | Triagem de mecanismo | Grupo alinhado a tarefas administrativas expostas |
| Comunicação, Linguagem e Conteúdo | Sim, com cautela | Triagem de mecanismo | Grupo conceitualmente forte, potencialmente menor N |
| Conectividade | Apêndice/parágrafo curto | Extensão sugestiva | Pretrends DDD falham |
| Resultados legados | Não | Apenas histórico interno | Crosswalk antigo não deve ser defendido |
| Grupos sem match MTE | Apêndice | Exploratórios | Não entram como evidência principal |

# Menu De Figuras Recomendado

## Figura 4.1: Linha Do Tempo E Desenho Empírico

Mostrar pré, pós, data do ChatGPT, tratamento ocupacional e unidade CBO-mês.

## Figura 4.2: Pipeline De Dados E Crosswalk

Mostrar CAGED -> CBO -> crosswalk MTE/ISCO -> OIT -> painel final.

## Figura 5.1: Event Study Nacional Por Outcome

Painéis para admissões, desligamentos, salário real de admissão e saldo líquido.

## Figura 5.2: Coortes De Carreira No Núcleo De Software E TI

Painéis normalizados no estilo *Canaries* para 22-25, 26-30, 31-34, 35-40, 41-49 e 50+.

## Figura 5.3: Comparação Entre Grupos Ocupacionais

Mostrar os quatro grupos:

- Núcleo de Software e TI.
- Atendimento e Contato com Cliente.
- Finanças, Contabilidade e Administração.
- Comunicação, Linguagem e Conteúdo.

## Figura 5.4: Forest Plot De Efeitos Por Grupo E Outcome

Coeficientes e intervalos de confiança para admissões, desligamentos e salário real de admissão.

## Figura 5.5: Heatmap De Heterogeneidade

Linhas por grupo ocupacional e perfil; colunas por outcome; marcação de pretrend/poder.

## Figura A.1: Conectividade Municipal

Figura de apêndice, não central, mostrando por que a evidência espacial é sugestiva e limitada.

# Lista Curta De Resultados A Mencionar

## Resultados centrais

1. O efeito médio nacional é fraco: não há ruptura agregada robusta em admissões, desligamentos ou salários.
2. Salário real de admissão tem sinal negativo no modelo nacional, mas não é estatisticamente forte.
3. Fluxos e saldo líquido ajudam a falar de reconfiguração, mas são limitados por pretrends.
4. O Núcleo de Software e TI concentra a evidência mais promissora.
5. Jovens em Software/TI apresentam queda salarial mais clara, especialmente 22-25 e 14-24.

## Resultados de contraste

6. Atendimento e Contato com Cliente deve aparecer como grupo teoricamente relevante, mas não como headline automático.
7. Finanças, Contabilidade e Administração deve aparecer como teste de tarefas administrativas expostas.
8. Comunicação, Linguagem e Conteúdo deve aparecer como grupo conceitualmente próximo da IA generativa, com cautela por poder/pretrend.
9. Conectividade municipal deve ser mencionada como teste feito, mas não como evidência central.

## Limitações que precisam aparecer

10. A dissertação observa fluxos formais, não estoque de emprego.
11. O crosswalk final é mais defensável, mas reduz cobertura.
12. `Minimal Exposure` não é controle no modelo principal.
13. Pretrend falho impede leitura causal forte.
14. Resultados exploratórios sem match MTE não entram como evidência principal.

# Checklist Antes De Escrever

- Confirmar que todos os números citados estão nos CSVs ou Markdown finais.
- Conferir se cada figura tem fonte e nota de interpretação.
- Não chamar resultado com pretrend falho de causal.
- Não apresentar conectividade como mecanismo comprovado.
- Não recuperar resultados do crosswalk antigo.
- Harmonizar a introdução depois da escrita das Seções 4 e 5, porque a introdução atual ainda pode estar mais forte do que os resultados finais permitem.

# Próximo Passo De Escrita

Escrever primeiro a Seção 4.1 a 4.5, porque elas dependem pouco da seleção final de figuras. Depois montar as figuras 5.1 a 5.3 e, só então, escrever os resultados. A sequência recomendada é:

1. Finalizar texto metodológico do CAGED, crosswalk e tratamento.
2. Escolher as figuras nacionais e de Software/TI.
3. Escrever a Seção 5 com base nas figuras.
4. Decidir se conectividade fica em apêndice ou em parágrafo curto no corpo.
5. Voltar à introdução e ajustar a promessa empírica à evidência final.
