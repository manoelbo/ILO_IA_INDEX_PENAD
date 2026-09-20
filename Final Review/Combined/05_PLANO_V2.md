# 05 — Plano da V2 (combinado)

Base: o contrato congelado e os gates de aceitação do Codex, mais a ingestão MOV+FOR−EXC, a revisão
da regra de gradiente, e os novos outcomes de metadados do Claude.

> **Revisão 2 — 26/07/2026.** Este documento foi atualizado depois da verificação de campo do FTP e
> de três decisões do autor. As mudanças estão explicadas em `tasks/plan_update.md`. Em resumo:
> corte fixado em **maio/2026**; encoding do conteúdo corrigido para **UTF-8**; **hierarquia de
> efeitos fixos restaurada** conforme o `final_review_planning.md` §2.4 do autor; e a recomendação
> de admissões por primeiro emprego **retirada** por inviabilidade dos dados.

**Regra de decisão.** V2 é uma atualização metodológica condicional, **não** uma busca por
significância. Prossegue apenas se um vintage oficial único puder ser congelado e reconciliado, os
modelos preferidos forem estimáveis com suporte adequado, e a V2 resolver ao menos uma fraqueza
material da V1.

---

## 1. Estado atual

A estrutura já existe (criada em 25/07/2026, 16:15):

```
Replication Package/
├── README.md          ← separação por geração de pesquisa
├── V1/                ← pacote atual congelado, intacto (verificado)
└── V2/README.md       ← status "NOT EXECUTED" + contrato metodológico
```

Falta: `V1/FROZEN.md` (marcador dentro da árvore, para ninguém editar por engano) e
`COMPARACAO_V1_V2.md` — uma linha por mudança: o que mudou, por quê, e o efeito no coeficiente
principal. É o documento que a banca vai querer.

**Regra do V1:** depois de congelada, não se edita. Nem para corrigir typo.

---

## 2. Auditoria dos gates

| Gate | Status | Evidência |
|---|---|---|
| CAGED oficial até maio/2026 | **Disponível** | 65 competências contínuas, jan/2021–mai/2026, verificadas no FTP |
| CAGED oficial junho/2026 | Ainda não | Previsto para 30/07/2026 |
| Vintage local único | **NO-GO** | Parquets locais param em jun/2025 e são anteriores às revisões de jun/2026 |
| IPCA | Parcial | Junho/2026 publicado; o insumo local para em dez/2025 |
| Arquitetura de ingestão V2 | **NO-GO** | A V1 carrega anos inteiros em memória, duplica brutos em `work/`, e descarta metadados |
| Ambientes Python/R isolados | **NO-GO** | Pacotes R da V2 e ambientes fixados não provisionados |
| Suporte de tratamento | Condicional | 75 tratadas G1–G3, 266 controles; G4 vazio — ver §5 |
| **Armazenamento** | **Aberto** | Ver §2.1 — este gate mudou |

### 2.1 O gate de armazenamento está aberto **[C]**

> **Atualização de 26/07/2026:** o autor liberou espaço por conta própria. Medição atual: **43 GiB
> livres**. O gate está aberto com folga e **não é mais necessário apagar os painéis derivados
> listados abaixo** — a tabela fica como registro de onde há espaço recuperável, se voltar a
> apertar. O restante desta subseção descreve a situação de 25/07.

O contrato exige 15–20 GiB; havia 8,5 GiB livres em 460 GiB, a 98% de capacidade. O plano do Codex
registra "nenhum dado do autor pode ser apagado para satisfazer este gate" e conclui NO-GO.

**O gate abre sem apagar nada insubstituível.** Existem 4,2 GB em painéis municipais **derivados**
que pertencem à extensão Anatel, documentada como excluída da dissertação:

| Arquivo | Tamanho |
|---|---:|
| `data/processed/painel_caged_municipio.parquet` | 962 MB |
| `data/cache/painel_3b_df_reg.parquet` | 774 MB |
| `data/output/painel_caged_municipio_anatel_v2.parquet` | 766 MB |
| `data/output/painel_section4_connectivity_ready.parquet` | 734 MB |
| `data/output/painel_caged_municipio_anatel.parquet` | 514 MB |
| `data/cache/painel_3b_df_ext.parquet` | 390 MB |
| `data/processed/section4_connectivity_canaries_age_outcomes.parquet` | 172 MB |
| **Total** | **4,2 GB** |

Todos são reconstruíveis a partir de `data/raw/` e dos scripts, que permanecem no repositório.
Painel derivado é cache, não dado do autor. Isso leva o espaço de 8,5 para ~12,7 GiB. Some os 94 MB
de `data/input/aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv`, que alimentam um derivado de 11,5 KB
e podem ir para `archive/`.

Além disso, **a arquitetura de ingestão do §3 é mais leve que 15–20 GiB**: processando competência a
competência com descarte, o pico fica em 1–2 GB. O permanente é ~3 GB do vintage comprimido, que
vale guardar para reprodutibilidade. Corrigir a arquitetura (que já é um gate NO-GO do Codex)
resolve o de armazenamento junto.

### 2.2 Corte: maio de 2026 — **decidido**

**O autor fixou o corte em 2026-05 em 25/07/2026. Não revisitar.**

O FTP tem até `202605`, verificado. Junho sairia em 30/07/2026. A decisão de não esperar tem duas
razões: junho acrescentaria um mês a um pós-tratamento que já terá 42, com ganho estatístico
desprezível; e seria o mês **mais incompleto** de toda a série, sem nenhuma declaração tardia
recebida (ver §3.5).

Janela final: **2021-01 a 2026-05 = 65 competências, 195 arquivos.**

O que **não** se pode fazer: misturar uma cauda nova de meses com um vintage histórico antigo. O MTE
republica o histórico — os arquivos de 2021-01 têm data de 08/06/2026.

---

## 3. Construção do vintage

### 3.1 Por que o FTP e não o Base dos Dados

| Fonte | Cobertura | Observação |
|---|---|---|
| `basedosdados.br_me_caged` | jan/2021 a **nov/2025** | Atualizado em 07/07/2026. Tem as três tabelas. |
| FTP `ftp.mtps.gov.br/pdet/microdados/NOVO CAGED/` | jan/2020 a **mai/2026** | Três `.7z` por mês. |

O Base dos Dados fica ~7 meses atrás. Para chegar a 05/2026 não há atalho.

### 3.2 Inventário e custo

Estrutura verificada em `202101` e `202605`:

```
NOVO CAGED/{AAAA}/{AAAAMM}/CAGEDMOV{AAAAMM}.7z    ~36–54 MB
                          /CAGEDFOR{AAAAMM}.7z    ~1–2 MB
                          /CAGEDEXC{AAAAMM}.7z    ~60–140 KB
```

65 competências × 3 arquivos = **195 arquivos**, ~3 GB comprimidos (o Codex mediu 2,897 GiB só de
CAGEDMOV). Ferramentas: `py7zr` via `uv --with py7zr`, ou `brew install p7zip` — nenhuma instalada
hoje.

**Correção de encoding (verificada em campo, 25/07/2026).** A versão anterior deste documento dizia
latin-1 para o conteúdo. Está errado:

- **Conteúdo dos `.txt`: UTF-8.** Separador `;`, decimal vírgula (`44,00`, `2940,00`).
- **Nomes de arquivo no servidor FTP: latin-1.** Arquivos com acento no nome exigem percent-encoding
  latin-1 — por exemplo `Movimenta%E7%E3o.xlsx`, não `%C3%A7%C3%A3o`.

MOV e FOR têm **28 colunas**; EXC tem **30** (acrescenta `competênciaexc` e `indicadordeexclusão`).
Lista completa e dicionários oficiais em `tasks/plan.md` §1.3 e §1.5.

### 3.5 Incompletude do fim da série — restrição nova

Medido no FTP: os arquivos FOR alcançam **12 meses para trás**; os EXC alcançam até 76 competências.
Em `CAGEDFOR202605`, 100% das linhas referem-se a meses anteriores, e 68,7% ao mês imediatamente
anterior.

Consequência: com corte em 2026-05, `202605` tem só o próprio MOV, `202604` tem MOV + 1 mês de FOR,
e assim por diante. **Os últimos ~12 meses são progressivamente incompletos** — é o espelho exato do
problema que a auditoria encontrou no início da V1.

**Tratamento obrigatório:** medir a curva de completude por competência e **por grande grupo CBO**.
Se a fração vinda de FOR diferir entre grupos tratado e controle em mais de 1 ponto percentual nos
meses recentes, aparar a cauda. Caso contrário, manter a janela inteira — a incompletude uniforme é
absorvida pelo efeito fixo de mês. Detalhe na Tarefa 9 de `tasks/plan.md`.

### 3.3 Procedimento

1. Congelar URLs oficiais do MTE, timestamp de recuperação, SHA-256 locais, bytes, schema,
   encoding e competências disponíveis, em `V2/data/vintage/manifest.json`. Sem isso, "vintage único
   congelado" é só uma frase.
2. **Reconstruir a janela inteira** jan/2021 até o corte. Não anexar só meses novos — declarações
   tardias e correções de fonte revisam competências anteriores.
3. **Construir MOV + FOR − EXC.** Este é o achado crítico da auditoria (`01` §1) e não estava no
   contrato original da V2.
4. Exportar tabela de revisão comparando o vintage V2 com os totais mensais e células da V1.
5. **Reconciliar com os agregados oficiais do PDET.** Qualquer tolerância precisa ser explicada por
   restrição de amostra documentada, não silenciosamente aceita. É o gate que teria pegado o achado
   do fora do prazo.
6. Atualizar o IPCA e todo insumo de preço até o mesmo corte — o local para em dez/2025.
7. Preservar brutos fora do pacote distribuído; publicar só insumos analíticos derivados.

**Gate adicional [C]:** para as competências que existem nas duas fontes (jan/2021 a nov/2025),
reconciliar o extrato do FTP contra o do Base dos Dados — contagens por mês, por CBO 2 dígitos, e
distribuição de salário. Se não bater, o problema é no parser, não nos dados. Atenção: o FTP usa os
nomes originais do MTE (`cbo2002ocupacao`, `graudeinstrucao`, `racacor`, `salariomensal`), e o Base
dos Dados aplica normalizações — incluindo a mensalização do salário a partir de
`unidadesalariocodigo` — que passam a ser sua responsabilidade.

### 3.4 Contrato de metadados

A V2 retém os metadados de origem antes da agregação, cada campo com um papel explícito.

| Metadado | Papel permitido |
|---|---|
| `tipo_movimentacao` | Construir e auditar os fluxos **+ [C] decomposição de desligamentos como outcome (`03` §P2.1)**. Ver a ressalva abaixo sobre admissões. |
| CNAE | **[C] Painel enriquecido co-principal** (ver §4.1) e diagnóstico de composição setorial |
| Município e UF | Diagnóstico de cobertura e merge; só a extensão espacial existente |
| Porte do estabelecimento | Diagnóstico de amostra **+ [C] heterogeneidade pré-registrada, `03` §P2.5** |
| Unidade de salário, valor fixo, **horas**, salário mensal | Validar mensalização e missingness **+ [C] salário-hora como outcome, `03` §P2.4** |
| Sexo, raça/cor, escolaridade, idade | Heterogeneidade pré-especificada existente, com validação de código bruto |
| `tipo_empregador`, `tipo_estabelecimento` | **[C]** Falsificação público vs privado |
| `indicador_aprendiz` | **[C]** Porta de entrada juvenil |
| Campos CBO e descrições oficiais | Crosswalk, suporte e transparência dos casos ocupacionais |

Códigos desconhecidos, identificadores duplicados, CBO ou CNAE inválidos e combinações impossíveis
de salário/contagem são condições **fail-fast**.

**Ressalva sobre admissões — recomendação retirada.** A auditoria propunha isolar admissões por
primeiro emprego (`03` §P2.2). Medição em campo mostrou que **o tipo de admissão deixou de ser
informado entre abril e julho de 2021**: a fração "Admissão de Tipo Ignorado" salta de 0,00% em
2021-04 para 97,84% em 2021-07 e chega a 99,94% em 2026-05. A variável morre 18 meses antes do
evento, e usá-la produziria efeito inteiramente espúrio. **P2.2 está cancelado.** O substituto
parcial é `indicador_aprendiz` / `categoria = 103`, cuja continuidade precisa ser validada do mesmo
jeito antes do uso.

Em contraste, a decomposição de **desligamentos** está disponível na janela inteira, com menos de
0,12% de tipo ignorado, e com uma repartição rica: demissão sem justa causa cai de 47,0% (2021-01)
para 42,1% (2026-05) enquanto pedido de demissão sobe de 31,2% para 36,1%. **P2.1 segue como o
exercício de maior valor do plano.**

---

## 4. Contrato de desenho congelado

| Elemento | Contrato V2 |
|---|---|
| População | Movimentações do Novo CAGED desde janeiro de 2021 |
| Corte | **Maio/2026 — fixado pelo autor em 25/07/2026, não revisitar** |
| Evento | Lançamento público do ChatGPT, 30 de novembro de 2022 |
| Primeiro mês tratado | Dezembro de 2022 |
| Referência | Novembro de 2022 (`t = −1`) |
| Tratamento | Gradientes G1–G4 da OIT |
| Controle | `Not Exposed` |
| Exclusões | `Minimal Exposure` e ocupações sem score aceito |
| Estimador de contagem principal | PPML com efeitos fixos e inferência clusterizada por CBO |
| Secundário | OLS em `log(1+y)`, interpretado como estimando de variável transformada |
| Estimador salarial principal | OLS no log do salário real de admissão, células válidas |
| Complementares | Salário real de desligamento e `asinh(saldo)` |
| Efeitos fixos | **Hierarquia de quatro níveis — ver §4.1** |
| Inferência | CRV1 por CBO4 no principal; bidirecional CBO4 × divisão CNAE como robustez do painel setorial |
| Janela mensal principal | `t = −23` a `t = +23`, sem recorte de caudas |
| Sensibilidade pandemia | Amostra iniciando em janeiro de 2022 |
| Sensibilidade recente | Amostra terminando em dezembro de 2025 |

O rótulo de tratamento deve divulgar a distribuição realizada. Se nenhuma ocupação aceita pertencer
ao G4, o tratamento empírico é efetivamente G1–G3 ainda que a regra pré-especificada seja G1–G4 —
**mas ver §5 antes de aceitar isso como dado.**

### 4.1 Hierarquia de efeitos fixos — restaurada

> **Mudança da revisão 2.** A versão anterior classificava CNAE como "robustez enriquecida, sujeita
> a suporte". Isso rebaixava o `final_review_planning.md` §2.4 do autor, que tratava o modelo
> enriquecido por indústria como **principal**. A hierarquia original está restaurada, com o gate de
> suporte decidindo **o peso**, não a existência.

| Nível | Especificação | Papel |
|---|---|---|
| 1 | `cbo_4d` + `periodo` | **Benchmark nacional.** Comparável à V1 e à literatura. Sempre reportado. |
| 2 | `cbo_4d × cnae` + `cnae × periodo` | **Principal enriquecido.** Sempre reportado, lado a lado com o nível 1. |
| 3 | acrescenta `cbo_2d × periodo` | **Diagnóstico de suporte**, não teste de robustez — ver ressalva. |
| 4 | firma × CBO e firma × mês | Fora desta rodada. Exige dados da FGV. |

**Por que o nível 2 volta a ser principal.** O grupo tratado é concentrado em apoio administrativo,
que por sua vez é concentrado em finanças, informação e comunicação, e serviços profissionais. Esses
setores tiveram ciclo próprio entre 2021 e 2026 — demissões em tecnologia, ciclo de crédito, Selic.
Sem `cnae × periodo`, esse ciclo entra no coeficiente como se fosse exposição à IA. É o confundidor
mais plausível do desenho, e a auditoria já indicava isso: o desequilíbrio de covariáveis na linha
de base é severo em todas as dimensões, com diferença normalizada de 1,248 em ensino superior.

Há um ganho possível adicional: se as tendências paralelas falham porque setores expostos se
recuperaram da pandemia em ritmo diferente, `cnae × periodo` absorve isso.

**Por que não substituir o nível 1 pelo 2.** O nível 2 muda o estimando. Deixa de ser "ocupações
expostas versus não expostas no Brasil" e passa a ser "dentro do setor, expostas versus não
expostas". Se parte do efeito da IA for realocar emprego **entre** setores, o nível 2 absorve
exatamente o que se quer medir. Por isso os dois são reportados sempre, e **a comparação entre eles
é resultado**: coeficiente estável nos dois é evidência contra confundimento setorial; coeficiente
que se move muito é um achado a explicar.

**Ressalva sobre o nível 3.** A exposição é fortemente correlacionada dentro de grupo CBO de 2
dígitos — o grupo 4 (administrativo) é quase todo exposto, o grupo 6 (agropecuária) quase todo não
exposto. `cbo_2d × periodo` pode absorver quase toda a variação de tratamento, produzindo um
coeficiente estimado sobre um subconjunto minúsculo com erro-padrão enorme. Isso **não** é evidência
de que o efeito não sobrevive; é evidência de que a variação não sobrevive.

Por isso o nível 3 entra como **diagnóstico de suporte**, com a tabela de variação de tratamento
remanescente publicada **antes** do coeficiente, e enquadrado como "quanta variação sobrevive" e não
como "o efeito é robusto".

**Inferência no painel setorial.** Clusterização bidirecional CBO4 × CNAE como robustez, usando
**divisão** CNAE (~87 categorias), não seção (~19) — poucos clusters numa das dimensões produz
cobertura abaixo do nominal. Reportar o número de clusters em cada dimensão. Nunca como principal.

**Gate de suporte (bloqueante para o nível 3, informativo para o 2).** Antes de estimar qualquer
nível acima de 1, publicar: número de células por combinação, percentil 10, e — o mais importante —
**quantas CBOs tratadas e de controle coexistem dentro da mesma célula de efeito fixo**. Se no nível
3 essa coexistência cair abaixo de 20 CBOs tratadas, o nível 3 é reportado apenas como diagnóstico,
sem interpretação substantiva.

### Horizontes dinâmicos

- Dezembro/2022 a novembro/2023
- Dezembro/2023 a novembro/2024
- Dezembro/2024 a novembro/2025
- Dezembro/2025 ao corte, explicitamente marcado como parcial

Lançamentos de produto são anotações, não datas de evento alternativas. Um teste conjunto de
pretrend não significativo **não é prova** de tendências paralelas.

---

## 5. Adição ao contrato: diagnóstico da regra de gradiente **[C]**

O contrato original manda reportar que o G4 é vazio. A auditoria mostra que o vazio é artefato da
fórmula (`01` §6): a ponte alcança 11 das 13 ocupações ISCO-08 de G4, 16 CBOs tocam pelo menos uma,
e a regra é assimétrica — G4 exige `média − DP ≥ 0,50` enquanto G1–G3 exigem `média + DP ≥ 0,50`,
com um DP que soma dispersão entre destinos à dispersão entre tarefas.

**Mantenha o contrato** (G1–G4 versus `Not Exposed`, reportando a realização) **e acrescente três
variantes de sensibilidade, pré-registradas antes de olhar resultado** — detalhe em `03` §P0.8:
média ponderada por emprego entre destinos; separação das duas fontes de dispersão; agregação de
rótulos em vez de scores.

**Gate:** ou o G4 deixa de estar vazio, ou você tem uma demonstração de que está vazio por razão
substantiva. Qualquer um dos dois resolve o problema do texto.

---

## 6. Pacotes de trabalho

Cada um tem um gate. Não passe do gate sem ele fechado.

### WP0 — Abrir os gates
Liberar os 4,2 GB de painéis derivados (§2.1). Provisionar ambientes Python e R isolados e fixados.
Corrigir a arquitetura de ingestão para processamento em lote sem duplicar brutos.
**Gate:** ≥15 GiB livres; ambientes reproduzem a V1 a partir de `V1/`.

### WP1 — Congelar a V1 — *quase concluído*
A movimentação já foi feita. Falta escrever `V1/FROZEN.md` e rodar a suíte a partir do novo caminho.
**Gate:** os testes passam **a partir de `V1/`** e o `reference_manifest.json` mantém
`failure_count: 0`. Mover uma árvore inteira é o tipo de operação que quebra caminho relativo em
silêncio.

### WP2 — Ingestão e reconciliação
Baixar os 195 arquivos, montar MOV + FOR − EXC, escrever o manifesto do vintage.
**Gate:** contagens do FTP batem com o Base dos Dados nas competências comuns; manifesto completo;
tabela mostrando mês a mês quantas movimentações entraram por FOR e saíram por EXC; reconciliação
com os agregados oficiais do PDET.

### WP3 — Painel reconstruído
Aplicar P0.2 (missingness), P0.9 (transferências), P0.10 (winsorização). Construir os dois painéis:
nacional CBO4×mês e enriquecido CBO4×CNAE×mês. Validar domínios, revisões, continuidade e merges
antes de agregar.
**Gate — o mais importante do plano:** rodar o **modelo antigo, sem nenhuma outra mudança**, sobre o
painel novo, e reportar o delta de cada coeficiente publicado.

- Delta pequeno → a Seção 5 sobrevive quase intacta, o resto é incremental, e você já tem um
  apêndice de robustez valioso.
- Delta grande → você achou algo real, e precisa saber **antes** de investir nos WPs seguintes.

### WP4 — Classificação de tratamento
Implementar as três variantes de sensibilidade do §5.
**Gate:** G4 preenchido ou explicado por razão substantiva.

### WP5 — Núcleo econométrico
P0.3 (controles), P0.6 (janela), PPML, exposição contínua, **e a hierarquia de efeitos fixos do
§4.1** — níveis 1 e 2 co-principais, nível 3 como diagnóstico de suporte, clusterização bidirecional
como robustez.
**Gate:** escada de especificações completa; **tabela de coexistência tratado/controle por célula de
efeito fixo publicada antes de qualquer estimativa de nível 2 ou 3**; nenhuma escolha de janela,
controle ou estimador feita depois de ver p-valor — registre isso num log de decisões.

### WP6 — Re-estimação completa e diagnóstico
P0.5 (re-estimar todo artefato inferencial), P0.7 (linhagem), Rambachan–Roth, multiplicidade,
falsificação, testes na camada de construção.
**Gate:** todo outcome tem pretrend sobre o modelo e a amostra exatos; toda heterogeneidade tem p
nominal e p ajustado; **o placebo temporal do desenho nacional não é significativo**. Se falhar como
falhou na extensão Anatel, isso é informação decisiva e precisa aparecer.

### WP7 — Mecanismos e novos outcomes
`03` §P2.1 a §P2.6, pré-registrados, com tabela de suporte para cada um.
**Gate:** nenhum exercício reportado sem sua tabela de suporte; correção de multiplicidade aplicada à
família ampliada.

### WP8 — Regeneração e texto
Regerar tabelas e figuras; aplicar `04`; fechar as pendências do referee2; escrever a Conclusão;
render único de Markdown, HTML e PDF.
**Gate:** todo número tem CSV de origem nomeado; nenhum link quebrado; nenhuma coluna cortada no
PDF; a suíte de contratos passa.

### WP9 — Auditoria final
Rodada 3 do referee2. Replicação cruzada Python↔R sobre os novos modelos. Produzir
`COMPARACAO_V1_V2.md`.
**Gate:** nenhum achado major ou moderate em aberto.

### Dependências

```
WP0 gates ─→ WP1 congelar V1
                 ↓
            WP2 ingestão ──→ GATE reconciliação (FTP vs BD vs PDET)
                 ↓
            WP3 painel ────→ GATE delta do modelo antigo no painel novo   ★ decide o resto
                 ↓
            WP4 tratamento → GATE G4
                 ↓
            WP5 núcleo → WP6 re-estimação e diagnóstico → GATE placebo
                 ↓
            WP7 mecanismos → WP8 regeneração e texto → WP9 auditoria
```

---

## 7. Gates de aceitação

**Dado.** Todo mês esperado aparece exatamente uma vez. Nenhum estado, CBO, CNAE ou componente de
fonte silenciosamente ausente. As revisões V1/V2 são quantificadas. Os agregados oficiais reconciliam
ou o desvio tem explicação documentada de amostra.

**Modelo.** PPML converge e reporta diagnóstico de separação e descarte. Tratamento e controle batem
com o contrato congelado. Suporte de cluster adequado. Estimativas dinâmicas usam o modelo exato, sem
recorte. DDD e multiplicidade passam em teste automatizado.

**Artefato.** Toda tabela, figura e número do manuscrito mapeia para backing gerado. Python e R usam
amostras idênticas e concordam a pelo menos seis decimais, ou a discrepância é diagnosticada. O PDF
final não tem link quebrado, tabela embaralhada, figura duplicada, conteúdo cortado ou evidência de
apêndice inacessível.

---

## 8. O que fica de fora

**Extensão Anatel.** Não volta. Os quatro outcomes falham pretrends com p=0,0000, o placebo temporal
de dez/2021 é significativo — falha de falsificação — e os coeficientes grandes trocam de sinal na
especificação com diagnóstico. Vira agenda na Conclusão.

**Atualização da PNADc para 2026 Q1 na Seção 3.** Tecnicamente possível — o Base dos Dados já tem.
Mas a Seção 3 está sólida, validada com números fixados (207.901 observações, 97.783.776 pessoas), e
atualizar significa regerar 5 tabelas e 10 figuras para ganhar dois trimestres num retrato
transversal. **Não vale**, a menos que a entrega escorregue muito.

**Painel PNADc de 16 trimestres.** **Fora — decidido pelo autor em 25/07/2026.** É `03` §P2.3 rota
3, e continua sendo o exercício de maior valor potencial, porque ataca estoque e informalidade ao
mesmo tempo. Mas é base diferente, unidade diferente e frequência diferente — na prática um segundo
estudo empírico. Fica para rodada separada.

**Validação de difusão brasileira via Google Trends.** **Fora desta rodada — decidido em
26/07/2026.** Era a Task 13 do `final_review_planning.md`, prioridade P1. Três razões para adiar:
é fonte de dados nova numa rodada já longa; mede consciência (interesse de busca), não adoção no
trabalho; e — a mais séria — **convida ao garimpo de data de corte**, exatamente o que o §3 do plano
do autor proíbe. Além disso não muda nenhuma estimativa: é ativo de texto, não de código. **Entra na
rodada do texto.**

**Admissões por primeiro emprego.** Fora — inviável. Ver a ressalva no fim do §3.4.

**Dados de firma no ambiente seguro da FGV.** Especificar, não executar. Vira agenda.

**RAIS para ancorar estoque em nível.** Fora do escopo. A proxy normalizada entrega a maior parte do
valor a uma fração do custo.

---

## 9. Riscos

| Risco | Probabilidade | O que fazer |
|---|---|---|
| **Os resultados enfraquecem** | **Alta** | Esperado, e seu próprio plano já registra. Escreva a dissertação que os dados sustentam. Um nulo bem medido, com Rambachan–Roth e falsificação, é academicamente mais forte que um efeito frágil. |
| O parser do FTP não reconcilia | Média | Gate do WP2. Se não bater em uma semana, caia para o Base dos Dados até nov/2025 — ainda são +5 meses, e **todas** as correções P0/P1/P2 continuam válidas, inclusive o fora do prazo (o BD tem as três tabelas). |
| A movimentação para `V1/` quebrou caminhos | Média | Gate do WP1, antes de qualquer outra coisa. |
| Suporte insuficiente em CBO×CNAE | Média | Tabela de coexistência tratado/controle é gate do WP5. Se for fino, o nível 2 continua reportado mas com a limitação declarada. |
| **Sobrecontrole no nível 2** — CNAE×mês absorve efeito de realocação entre setores | Média | Por isso os níveis 1 e 2 são co-principais e nunca substitutos. A diferença entre eles é reportada como resultado. |
| **`cbo_2d × periodo` mata a variação de tratamento** | **Alta** | Esperado. Publicar a variação remanescente antes do coeficiente e enquadrar o nível 3 como diagnóstico, não como teste de robustez. |
| Clusterização bidirecional com poucos clusters | Média | Usar divisão CNAE (~87), nunca seção (~19). Reportar o número de clusters em cada dimensão. |
| Mais especificações = mais tentação de garimpo | Média | Todas pré-registradas antes de estimar e **todas reportadas**, inclusive as feias. Uma escada só vale se os degraus ruins aparecem. |
| Os resultados invertem de sinal | Baixa | Se acontecer, é o achado. Reporte com a reconciliação ao lado. |
| Escopo cresce e o tempo acaba | Média | Ver §10. |

**Condições de parada.** Registre `NOT EXECUTED` em vez de resultado parcial se: o vintage não puder
ser congelado ou reconciliado; os modelos preferidos falharem suporte ou convergência de um jeito que
mude o estimando; ou implementar a V2 exigir mudar a estrutura da dissertação.

---

## 10. Se o tempo acabar no meio

Ordem de valor decrescente:

0. **WP0 + WP1.** Liberar disco, provisionar ambiente, fechar o congelamento da V1. Meia hora a um
   dia. Sem isso nada começa.
1. **WP2 + WP3.** Resolve o problema crítico da auditoria e produz um apêndice de robustez que
   nenhum trabalho comparável tem.
2. **+ WP4 + WP5.** Núcleo defensável: estimador certo, controles certos, classificação corrigida.
3. **+ WP6.** Rambachan–Roth, multiplicidade e re-estimação completa. É aqui que o trabalho passa de
   "cuidadoso" para "metodologicamente sólido".
4. **+ WP7 parcial, só P2.1.** A decomposição de desligamentos. Se puder fazer um exercício novo só,
   faça esse.
5. **+ o resto do WP7.**

**WP8 e WP9 são obrigatórios em qualquer cenário** — não adianta resultado novo com texto velho.

E as correções de texto do `04` §P0 são **independentes de tudo isso**. Se a V2 travar por qualquer
motivo, elas ainda devem ser feitas antes de qualquer envio.
