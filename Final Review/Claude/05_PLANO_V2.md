# 05 — Plano da V2

Plano executável. Assume as três decisões já tomadas: documentos em português, novos outcomes de
metadados entram, e a rota de dados é o FTP do MTE.

---

## 0. Estado atual — o que já foi feito

Durante esta revisão, a estrutura V1/V2 **já foi criada** (verificado em 25/07/2026 às 16:15):

```
Replication Package/
├── README.md          ← explica a separação por geração de pesquisa
├── V1/                ← pacote atual movido inteiro e congelado (intacto, verificado)
│   └── code/ data/ results/ tests/ README.md run_replication.py requirements*.txt
└── V2/
    └── README.md      ← status "NOT EXECUTED" + contrato metodológico pré-especificado
```

Então o WP1 abaixo está **concluído**, e o `V2/README.md` já fixa um contrato metodológico que
coincide em boa parte com o que eu recomendaria: PPML principal para contagens, sem controles de
composição contemporâneos na especificação causal preferida, janela balanceada −23…+23 sem
agrupamento de caudas, novembro de 2022 como referência, pretrends sobre o modelo exato, correção
de multiplicidade, HonestDiD onde compatível, e DDD apenas com o triplo explícito.

**Este plano acrescenta ao contrato existente, não o substitui.** As adições são:

| Adição | Onde está justificada |
|---|---|
| MOV + FOR − EXC explícito na ingestão | `01_AUDITORIA_CODIGO.md` §1 — é o achado crítico |
| Revisão da regra de gradiente (média ponderada, separação da dispersão) | `01_AUDITORIA_CODIGO.md` §2 |
| Decomposição de desligamentos por `tipo_movimentacao` | `03_MELHORIAS_CODIGO.md` §P2.1 |
| Admissões de primeiro emprego e de aprendiz | `03_MELHORIAS_CODIGO.md` §P2.2 |
| Proxy de estoque por saldo acumulado | `03_MELHORIAS_CODIGO.md` §P2.3 |
| Salário-hora via `horas_contratuais` | `03_MELHORIAS_CODIGO.md` §P2.4 |
| Painel PNADc de 16 trimestres como validação de estoque e informalidade | `03_MELHORIAS_CODIGO.md` §P2.3 rota 3 |

Duas coisas ainda faltam na estrutura:

- **`V1/FROZEN.md`** — dizendo o que a V1 reproduz, quando foi congelada, e que os problemas
  conhecidos estão nas auditorias. O `README.md` da raiz cobre parte disso, mas o marcador dentro
  da V1 evita que alguém a edite por engano.
- **`COMPARACAO_V1_V2.md`** — uma linha por mudança: o que mudou, por quê, e qual o efeito no
  coeficiente principal. É o documento que a banca vai querer.

**Regra do V1:** depois de congelada, não se edita. Nem para corrigir typo.

---

## 2. Ingestão dos dados

### 2.1 Por que o FTP e não o Base dos Dados

Verificado nesta auditoria:

| Fonte | Cobertura CAGED | Observação |
|---|---|---|
| `basedosdados.br_me_caged` | 2021-01 a **2025-11** | Atualizado em 07/07/2026. Tem as três tabelas (MOV, FOR, EXC). |
| FTP `ftp.mtps.gov.br/pdet/microdados/NOVO CAGED/` | 2020-01 a **2026-05** | Três arquivos `.7z` por mês. |

O Base dos Dados fica seis meses atrás. Para chegar a 05/2026 não há atalho.

**Nota importante:** o MTE **republica o histórico**. Os arquivos de 2021-01 têm data de
08/06/2026; os de 2026-05, de 30/06/2026. Ou seja, competências antigas são revistas. Isso confirma
a decisão do seu `final_review_planning.md` Task 3: baixar a série inteira em uma extração, nunca
anexar meses novos a um extrato antigo.

### 2.2 Inventário e custo

Estrutura por competência (verificado em `202101` e `202605`):

```
NOVO CAGED/{AAAA}/{AAAAMM}/CAGEDMOV{AAAAMM}.7z    ~36–54 MB
                          /CAGEDFOR{AAAAMM}.7z    ~1–2 MB
                          /CAGEDEXC{AAAAMM}.7z    ~60–140 KB
```

Para 2021-01 a 2026-05: **65 competências × 3 arquivos = 195 arquivos**, ~3 GB comprimidos.
Descomprimidos são CSVs `;`-separados em latin-1, algo entre 15 e 20 GB no total — processáveis mês
a mês com descarte, sem precisar de tudo em disco ao mesmo tempo.

Ferramentas: `py7zr` (via `uv --with py7zr`) ou `brew install p7zip`. Nenhuma das duas está
instalada hoje.

### 2.2b O gate de armazenamento tem solução

O `V2/README.md` registra um gate fechado: o plano exige 15–20 GiB livres e há ~8,45 GiB. Confirmei
— o volume está com 8,5 GiB livres em 460 GiB, a 98% de capacidade.

**Esse gate se abre sem apagar nada insubstituível.** Existem 4,2 GB de painéis municipais
derivados que pertencem à extensão Anatel, que está documentada como excluída da dissertação:

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

Todos são **derivados** — reconstruíveis a partir de `data/raw/` e dos scripts, que continuam no
repositório. Removê-los é limpar cache, não apagar dado de usuário. Isso leva o espaço livre de
8,5 GiB para ~12,7 GiB.

Some a isso os 94 MB de `data/input/aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv`, que alimentam
um arquivo derivado de 11,5 KB e podem ser rebaixados para `archive/`, e os 2,0 GB de
`data/raw/caged_*.parquet`, que serão substituídos pelo novo vintage — embora estes só devam sair
**depois** que a reconciliação do WP2 passar.

Além disso, o plano de ingestão aqui é mais leve do que 15–20 GiB: processando competência a
competência, descomprimindo, agregando e descartando, o pico de uso fica na casa de 1–2 GB por vez.
O total permanente é ~3 GB do vintage comprimido, que vale guardar para reprodutibilidade.

### 2.2c Sobre esperar a competência de junho de 2026

O `V2/README.md` registra que a release de junho de 2026 sai em 30/07/2026 — cinco dias depois do
freeze. Verifiquei o FTP: **05/2026 já está publicado** e é o corte atual.

Vale esperar? Depende do seu prazo. Junho acrescenta um mês a um pós-tratamento que já terá 42. O
ganho estatístico é desprezível. O ganho real é outro: fechar a janela num limite de ano-calendário
ou de semestre é mais fácil de justificar em texto. Se a entrega for depois de 30/07, use junho. Se
for antes, use maio e não perca nada de substância.

O que **não** se pode fazer, e o `V2/README.md` já diz certo, é misturar uma cauda nova de meses com
um vintage histórico antigo — o MTE republica o histórico (os arquivos de 2021-01 têm data de
08/06/2026).

### 2.3 O que muda na extração

Colunas a puxar, além das 16 atuais:

| Coluna | Para quê | Doc 03 |
|---|---|---|
| `tipomovimentacao` | Decompor desligamentos; isolar primeiro emprego; excluir transferências | P0.4, P2.1, P2.2 |
| `horascontratuais` | Salário-hora | P2.4 |
| `indtrabparcial`, `indtrabintermitente` | Separar margem de jornada | P2.4 |
| `indicadoraprendiz` | Porta de entrada juvenil | P2.2 |
| `tipoempregador`, `tipoestabelecimento` | Público vs privado (falsificação) | P2.5 |
| `unidadesalariocodigo`, `valorsalariofixo` | Verificar a normalização do salário | — |
| `indicadordeforadoprazo` | Marcar a origem da competência | P0.1 |

**Atenção ao layout.** O FTP usa os nomes originais do MTE (`cbo2002ocupacao`, `graudeinstrucao`,
`racacor`, `salariomensal`), diferentes dos nomes normalizados do Base dos Dados (`cbo_2002`,
`grau_instrucao`, `raca_cor`, `salario_mensal`). E o Base dos Dados aplica tratamentos que você
passa a ter de replicar: normalização do salário para base mensal a partir de
`unidadesalariocodigo`, e limpeza de códigos inválidos.

**Gate de validação obrigatório:** para as competências que existem nas duas fontes
(2021-01 a 2025-11), reconciliar o extrato do FTP contra o do Base dos Dados. Contagens por mês, por
CBO 2 dígitos, e distribuição de salário. Se não bater, o problema é no seu parser, não nos dados.

### 2.4 Manifesto do vintage

`V2/data/vintage/manifest.json` com, para cada um dos 195 arquivos: URL, data de modificação no
FTP, tamanho, SHA-256 do arquivo baixado, e timestamp do download. Sem isso, "vintage único
congelado" é só uma frase.

### 2.5 Outras fontes

- **PNADc**: o Base dos Dados já tem **2026 Q1**. A Seção 3 usa 3T/2025. Atualizar é opcional —
  ver §5 abaixo.
- **IPCA**: reestender o deflator até 2026-05. Nota: `data/processed/ipca_mensal.parquet` tem 60
  linhas para um painel de 54 meses; conferir na reconstrução.
- **Salário mínimo**: o valor de referência de R$ 1.518 é de 2025. Se a janela chega a 2026,
  precisa do valor de 2026 e de uma nota sobre qual foi usado em cada exercício.

---

## 3. Pacotes de trabalho

Cada pacote tem um gate. **Não passe do gate sem ele fechado** — é o que impede que um erro de
construção contamine tudo o que vem depois.

### WP1 — Congelar a V1 — **já concluído**

A movimentação para `Replication Package/V1/` já foi feita (25/07/2026, 16:15) e a V1 está
intacta. Falta apenas: escrever `V1/FROZEN.md`, e rodar a suíte de testes uma última vez a partir
do novo caminho para confirmar que a movimentação não quebrou nenhum caminho relativo.

**Gate:** os 138 testes passam **a partir de `V1/`** e o `reference_manifest.json` continua com
`failure_count: 0`. Esse teste importa mais do que parece — mover uma árvore inteira é o tipo de
operação que quebra caminho relativo silenciosamente.

### WP2 — Ingestão e reconciliação

Baixar os 195 arquivos, montar MOV + FOR − EXC, escrever o manifesto do vintage.

**Gate:** (a) contagens por mês do FTP batem com o Base dos Dados nas competências comuns;
(b) o manifesto está completo; (c) uma tabela de reconciliação mostra, mês a mês, quantas
movimentações entraram por FOR e quantas saíram por EXC.

### WP3 — Painel reconstruído

Aplicar as correções P0.4 (transferências), P0.5 (winsorização), P0.7 (`fillna`), e construir os
dois painéis: nacional CBO4×mês e enriquecido CBO4×CNAE×mês.

**Gate — o mais importante do plano:** rodar o **modelo antigo, sem nenhuma outra mudança**, sobre
o painel novo, e reportar o delta de cada coeficiente publicado. Esse número decide o resto:

- Delta pequeno → a Seção 5 sobrevive quase intacta, o resto é melhoria incremental, e você já tem
  um apêndice de robustez valioso.
- Delta grande → você achou algo real, e precisa saber disso **antes** de investir nos WPs
  seguintes.

### WP4 — Classificação de tratamento revista

Implementar as três variantes de P0.2 (média ponderada por emprego, separação das fontes de
dispersão, agregação de rótulos), pré-registradas antes de olhar resultado.

**Gate:** ou o Gradiente 4 deixa de estar vazio, ou você tem uma demonstração de que ele está vazio
por razão substantiva e não por artefato da fórmula. Qualquer um dos dois resolve o problema do
texto — o que não pode continuar é a explicação atual.

### WP5 — Núcleo econométrico

P0.3 (controles), P0.6 (janela), P1.1 (PPML), P1.5 (exposição contínua), P1.6 (CNAE×mês).

**Gate:** a escada de especificações está completa e cada degrau é reportável. Nenhuma escolha de
janela, controle ou estimador foi feita depois de ver p-valor — regra que o seu
`final_review_planning.md` §3 já fixa e que deve ficar registrada no log de decisões.

### WP6 — Diagnóstico e inferência

P1.2 (Rambachan–Roth), P1.3 (multiplicidade), P1.4 (falsificação), P1.7 (testes de construção).

**Gate:** todo outcome principal tem teste de tendência prévia sobre **o modelo e a amostra
exatos** do resultado reportado; toda heterogeneidade tem p nominal e p ajustado; o placebo
temporal do desenho nacional não é significativo. Se o placebo nacional falhar como falhou na
extensão Anatel, isso é informação decisiva e precisa aparecer.

### WP7 — Mecanismos e novos outcomes

P2.1 (tipos de desligamento), P2.2 (primeiro emprego e aprendiz), P2.3 (proxy de estoque),
P2.4 (salário-hora), P2.5 (porte e natureza do empregador), P2.6 (sensibilidade da medida).

**Gate:** cada exercício tem tabela de suporte amostral, e nenhum é reportado sem ela.

### WP8 — Regeneração e texto

Regerar as 23 tabelas e as 13 figuras; aplicar as reescritas de `04_MELHORIAS_TEXTO.md`; fechar
as pendências do referee2; escrever a Conclusão.

**Gate:** todo número no texto tem um CSV de origem nomeado; nenhum link quebrado; a suíte de
contratos passa.

### WP9 — Auditoria final

Rodar a rodada 3 do referee2 sobre o texto revisto. Rodar a replicação cruzada Python↔R sobre os
novos modelos principais. Produzir o `COMPARACAO_V1_V2.md`.

**Gate:** nenhum achado major ou moderate em aberto.

---

## 4. Ordem e dependências

```
WP1 congelar V1
   ↓
WP2 ingestão ──→ GATE reconciliação FTP vs BD
   ↓
WP3 painel ────→ GATE delta do modelo antigo no painel novo   ★ decide o resto
   ↓
WP4 tratamento → GATE G4 preenchido ou explicado
   ↓
WP5 núcleo econométrico
   ↓
WP6 diagnóstico ─→ GATE placebo nacional não significativo
   ↓
WP7 mecanismos
   ↓
WP8 regeneração + texto
   ↓
WP9 auditoria final
```

WP1 e WP2 podem começar em paralelo. Do WP3 em diante é sequencial.

---

## 5. O que fica de fora, e por quê

**Extensão Anatel (conectividade municipal).** Não volta. Os quatro outcomes falham tendências
prévias com p=0,0000, o placebo temporal de dez/2021 é significativo — falha de falsificação — e
os coeficientes grandes trocam de sinal na especificação com diagnóstico. O seu próprio plano (§6,
P2) já condiciona geografia a passar antes nos desenhos nacional e setorial. Mantenha excluída e
mencione na agenda da Conclusão.

**Atualização da PNADc para 2026 Q1 na Seção 3.** Tecnicamente possível — o Base dos Dados já tem.
Mas a Seção 3 está sólida, passou por validação com números fixados
(207.901 observações, 97.783.776 pessoas, verificados por teste), e atualizar significa regerar
5 tabelas e 10 figuras para ganhar dois trimestres num retrato transversal. **Não vale**, a menos
que a V2 se estenda e o 3T/2025 comece a parecer velho na data da entrega.

**Painel PNADc de 16 trimestres.** Este é diferente — é o P2.3, rota 3, e é o exercício mais
valioso do plano se houver energia, porque ataca estoque e informalidade ao mesmo tempo. Mas é
**opcional**: entra no WP7 se os WPs anteriores fecharem sem sustos, e sai sem prejuízo se o tempo
apertar.

**Extensão com dados de firma no ambiente seguro da FGV.** Especificar, não executar. Vira agenda
na Conclusão. Seu `final_review_planning.md` Task 6 já tem o desenho.

**RAIS para ancorar o estoque em nível.** Fora do escopo. A proxy normalizada (P2.3 rota 1) entrega
a maior parte do valor a uma fração do custo.

---

## 6. Riscos

| Risco | Probabilidade | O que fazer |
|---|---|---|
| O parser do FTP não reconcilia com o Base dos Dados | Média | É o gate do WP2. Se não bater em uma semana, caia para o Base dos Dados até 2025-11 — ainda são +5 meses e todas as correções P0/P1/P2 continuam válidas. |
| Os resultados enfraquecem com o painel corrigido | **Alta** | É esperado, e seu próprio plano registra isso. A resposta é escrever a dissertação que os dados sustentam. Um nulo bem medido, com Rambachan–Roth e falsificação, é academicamente mais forte do que um efeito frágil. |
| Os resultados invertem de sinal | Baixa | Se acontecer, é o achado. Reporte com a reconciliação ao lado. |
| Suporte insuficiente no painel CBO×CNAE | Média | Tabela de suporte é gate do WP5. Se for fino, CNAE×mês vira robustez em vez de principal. |
| Escopo cresce e o tempo acaba | Média | Ver §7. |
| Espaço em disco | **Já materializado** | 8,5 GiB livres a 98% de capacidade. Solúvel liberando os 4,2 GB de painéis municipais derivados da extensão Anatel — ver §2.2b. |
| A movimentação para `V1/` quebrou caminhos relativos | Média | Gate do WP1: rodar a suíte a partir do novo caminho antes de qualquer outra coisa. |

---

## 7. Se o tempo acabar no meio

Ordem de valor decrescente, para você poder parar em qualquer ponto e ainda ter entregue algo:

0. **Liberar disco (§2.2b) e fechar o WP1.** Meia hora. Sem isso nada mais começa.
1. **WP2–WP3.** Só isso já resolve o problema crítico da auditoria e produz um apêndice de
   robustez que nenhum outro trabalho comparável tem.
2. **+ WP4–WP5.** Núcleo defensável: estimador certo, controles certos, classificação corrigida.
3. **+ WP6.** Rambachan–Roth e multiplicidade. É aqui que o trabalho passa de "cuidadoso" para
   "metodologicamente sólido".
4. **+ WP7 parcial, só P2.1.** A decomposição de desligamentos. Se você só puder fazer um exercício
   novo, faça esse.
5. **+ o resto do WP7.**

WP8 e WP9 são obrigatórios em qualquer cenário — não adianta ter resultado novo e texto velho.
