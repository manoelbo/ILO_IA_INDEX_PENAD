# Plano de Implementação: Replication Package V2

**Origem:** `Final Review/Combined/05_PLANO_V2.md` (contrato), `03_MELHORIAS_CODIGO.md` (correções),
`01_AUDITORIA_CODIGO.md` (achados).
**Escopo desta rodada:** dados, código e pacote de replicação. **O texto da dissertação fica de
fora** — será tratado depois, separadamente.
**Data:** 25 de julho de 2026.

---

## LEIA ISTO PRIMEIRO

Este documento é para ser **executado**, não interpretado. Regras:

1. **Não improvise.** Se um fato não estiver aqui nem for verificável por comando, **pare e
   pergunte**. Não invente nomes de coluna, códigos, caminhos ou limiares.
2. **Não pule gates.** Todo Checkpoint tem critérios que precisam ser cumpridos e registrados.
   **Bloqueantes** (pare e reporte, sem exceção): **A**, **B**, **F**. **Não bloqueantes**
   (registre e siga): **C**, **D**, **E**, **G**, **H**. Nunca contorne um critério — cumprir e
   seguir é diferente de ignorar.
3. **Nunca edite `Replication Package/V1/`.** É uma linha de base congelada. Se você precisar de
   algo dela, copie para a V2.
4. **Nunca escolha especificação depois de ver p-valor.** Toda escolha de janela, controle,
   estimador ou limiar é pré-registrada neste documento. Se precisar mudar, registre a mudança e o
   motivo em `V2/DECISIONS.md` **antes** de rodar.
5. **Não apague dados originais** sem instrução explícita. Arquivos `.txt` descompactados temporários
   podem e devem ser apagados após uso; `.7z` baixados e parquets da V1 não.

---

## 1. Verdade de campo já verificada

Estes fatos foram confirmados ao vivo em 25/07/2026. **Use-os. Não os re-descubra e não os
contradiga sem evidência.**

### 1.1 Ambiente

| Item | Valor |
|---|---|
| Espaço livre em disco | **43 GiB** (gate de ≥15 GiB **ABERTO com folga**) |
| `7z` / `p7zip` no PATH | **Não instalado** — use `uv run --with py7zr` |
| `uv` | Disponível em `/opt/homebrew/bin/uv` |
| R | 4.4.1 em `/usr/local/bin/R`; só `data.table` instalado |
| Python do sistema | **Sem pacotes** — sempre use `uv` |
| Projeto GCP | `mestrado-pnad-2026`, ADC presente (opcional, só para validação) |

> `Replication Package/V2/README.md` ainda diz que o gate de armazenamento está fechado.
> **Está desatualizado.** Corrija na Tarefa 3.

### 1.2 FTP do MTE — estrutura confirmada

Base: `ftp://ftp.mtps.gov.br/pdet/microdados/NOVO CAGED/`

```
{AAAA}/{AAAAMM}/CAGEDMOV{AAAAMM}.7z    35–53 MB
                CAGEDFOR{AAAAMM}.7z    0,9–2 MB
                CAGEDEXC{AAAAMM}.7z    60–140 KB
```

- **65 competências** de 2021-01 a 2026-05 (12+12+12+12+12+5). Confirmado.
- Total ≈ **3 GB comprimidos**.
- Velocidade medida: **51 MB em 10,2 s (~5 MB/s)**. O download completo leva ~10–15 min.
- Descompactação: **3 s** para gerar um `.txt` de 453 MB.
- Leitura em pandas: **5 s** para 4,3 milhões de linhas.

**Armadilha nº 1 — encoding duplo.** Os **nomes de arquivo** no servidor são **latin-1**; o
**conteúdo** dos arquivos é **UTF-8**. O plano de origem diz latin-1 para o conteúdo — **está
errado**.

Para baixar arquivos com acento no nome, use percent-encoding **latin-1**. Exemplo real que
funciona:

```bash
curl -o layout.xlsx \
  "ftp://ftp.mtps.gov.br/pdet/microdados/NOVO%20CAGED/Layout%20N%E3o-identificado%20Novo%20Caged%20Movimenta%E7%E3o.xlsx"
```

Os arquivos `CAGEDMOV/FOR/EXC` não têm acento, então bastam `%20` nos espaços de `NOVO CAGED`.

### 1.3 Schema dos arquivos

Separador `;` · encoding **UTF-8** · decimal **vírgula** (`44,00`, `2940,00`) · **cabeçalho na
primeira linha** · nomes de coluna **com acentos e cedilha**.

**CAGEDMOV e CAGEDFOR — 28 colunas, nesta ordem:**

```
competênciamov, região, uf, município, seção, subclasse, saldomovimentação,
cbo2002ocupação, categoria, graudeinstrução, idade, horascontratuais, raçacor,
sexo, tipoempregador, tipoestabelecimento, tipomovimentação, tipodedeficiência,
indtrabintermitente, indtrabparcial, salário, tamestabjan, indicadoraprendiz,
origemdainformação, competênciadec, indicadordeforadoprazo, unidadesaláriocódigo,
valorsaláriofixo
```

**CAGEDEXC — 30 colunas:** as mesmas, mais `competênciaexc` e `indicadordeexclusão`, inseridas
depois de `competênciadec`.

**Armadilha nº 2 — `competênciamov` ≠ competência do arquivo.**
Em `CAGEDFOR202605`, todas as linhas têm `competênciamov` **anterior** a 202605 (verificado: 100%).
O nome do arquivo é o mês da **declaração**; `competênciamov` é o mês do **fato**. **Sempre agregue
por `competênciamov`.**

### 1.4 Alcance retroativo de FOR e EXC — medido

Em `CAGEDFOR202605` (80.230 linhas):

| `competênciamov` | Linhas | % |
|---|---:|---:|
| 202604 | 55.124 | 68,7% |
| 202603 | 7.554 | 9,4% |
| 202602 | 4.180 | 5,2% |
| 202601 | 3.574 | 4,5% |
| ... até 202505 | — | cauda |

**FOR alcança 12 meses para trás.** `CAGEDEXC202605` alcança **76 competências**, até 202001.

**Consequência de desenho (importante).** Com corte em 202605, os meses recentes do painel ainda
não receberam suas declarações tardias. `202605` tem só o próprio MOV; `202604` tem MOV + 1 mês de
FOR; e assim por diante. **Os últimos ~12 meses são progressivamente incompletos.** Isso é o espelho
do problema que a auditoria encontrou na V1 — ver Tarefa 9, que trata disso explicitamente.

### 1.5 Dicionário oficial de `tipomovimentação`

Baixado de `NOVO CAGED/Layout Não-identificado Novo Caged Movimentação.xlsx`. **Esta é a
autoridade.**

| Código | Descrição | Sinal |
|---|---|---|
| 10 | Admissão por primeiro emprego | + |
| 20 | Admissão por reemprego | + |
| 25 | Admissão por contrato trabalho prazo determinado | + |
| 31 | Desligamento por demissão **sem** justa causa | − |
| 32 | Desligamento por demissão **com** justa causa | − |
| 33 | Culpa recíproca | − |
| 35 | Admissão por reintegração | + |
| 40 | Desligamento **a pedido** | − |
| 43 | Término contrato trabalho prazo determinado | − |
| 45 | Desligamento por término de contrato | − |
| 50 | Desligamento por aposentadoria | − |
| 60 | Desligamento por morte | − |
| 70 | Admissão por transferência | + |
| 80 | Desligamento por transferência | − |
| 90 | Desligamento por acordo entre empregado e empregador | − |
| **97** | **Admissão de Tipo Ignorado** | + |
| **98** | **Desligamento de Tipo Ignorado** | − |
| 99 | Não identificado | ? |

Outros dicionários confirmados no mesmo arquivo:

- `sexo`: 1 = Homem, **3 = Mulher**, 9 = Não identificado.
- `graudeinstrução`: 8 = Superior **Incompleto**; **9 = Superior Completo**, 10 = Mestrado,
  11 = Doutorado, 80 = Pós-graduação completa. → **Superior completo = {9, 10, 11, 80}. O código 8
  NÃO entra.** (Isso resolve a divergência entre módulos apontada na auditoria.)
- `raçacor`: 1 Branca, 2 Preta, 3 Parda, 4 Amarela, 5 Indígena, 6 Não informada, 9 NI.
  → Negra = {2, 3}.
- `categoria`: 101 Empregado geral, **103 Aprendiz**, 104 Doméstico, 106 Temporário,
  111 Intermitente, 999 NI.
- `unidadesaláriocódigo`: 1 Hora, 2 Dia, 3 Semana, 4 Quinzena, **5 Mês**, 6 Tarefa, 7 Variável, 99 NI.
- `tipoempregador`: 0 CNPJ raiz, 2 CPF, 9 NI.
- `indicadordeforadoprazo` e `indicadordeexclusão`: 0 Não, 1 Sim.

### 1.6 ACHADO QUE MATA UMA RECOMENDAÇÃO — leia com atenção

Medi a cobertura de `tipomovimentação` em quatro competências:

| Competência | Admissões | % admissão "tipo ignorado" (97) | % primeiro emprego (10) |
|---|---:|---:|---:|
| 2021-01 | 1.550.075 | **0,00%** | 6,82% |
| 2021-04 | 1.396.311 | **0,00%** | 6,22% |
| 2021-07 | 1.666.051 | **97,84%** | 0,23% |
| 2021-10 | 1.760.739 | 99,67% | 0,13% |
| 2022-01 | 1.777.646 | 99,26% | 0,07% |
| 2022-11 | 1.747.894 | 99,79% | 0,01% |
| 2026-05 | 2.207.303 | 99,94% | — |

**O tipo de admissão deixou de ser informado entre abril e julho de 2021.** A partir daí, ~99% das
admissões são "Tipo Ignorado".

**Consequência: a recomendação P2.2 (isolar admissões por primeiro emprego) está MORTA.** A
variável existe no pré-tratamento e desaparece 18 meses antes do evento. Usá-la produziria um
"efeito" inteiramente espúrio. **Não implemente P2.2 na forma original.** O substituto parcial é
`indicadoraprendiz` / `categoria = 103` — mas **valide a continuidade dele do mesmo jeito antes de
usar** (Tarefa 9).

**Em contraste, a decomposição de desligamentos é excelente e está disponível na janela inteira:**

| Competência | % desl. tipo ignorado | % 31 (sem justa causa) | % 40 (a pedido) | % 43 (fim contrato) |
|---|---:|---:|---:|---:|
| 2021-01 | 0,00% | 47,0% | 31,2% | 17,6% |
| 2022-11 | 0,05% | 47,6% | 31,8% | 17,4% |
| 2023-01 | 0,05% | 46,8% | 34,3% | 15,7% |
| 2026-05 | 0,12% | 42,1% | 36,1% | 17,4% |

**P2.1 é o exercício de maior valor do plano e é totalmente viável.** Demissões caindo de 47% para
42% e pedidos subindo de 31% para 36% é, por si só, um fato interessante.

**Sobre transferências (P0.9):** em 2026-05 os códigos 70 e 80 têm **zero linhas**. Transferências
podem não estar sendo reportadas no Novo CAGED. **Verifique mês a mês na Tarefa 9 antes de escrever
qualquer filtro** — se forem sempre zero, o filtro é inócuo e deve ser documentado como tal, não
removido.

### 1.7 Salário

O layout diz que `salário` é "Salário mensal declarado" — já mensalizado. `valorsaláriofixo` com
`unidadesaláriocódigo` é o valor bruto declarado. A fração com unidade **diferente de mês** caiu de
16,35% (2021-01) para ~8,2% (2026-05) — é uma mudança de composição que precisa entrar nos
diagnósticos (Tarefa 9).

---

## 2. Decisões de arquitetura

| Decisão | Escolha | Motivo |
|---|---|---|
| Fonte dos dados | **FTP do MTE, exclusivamente** | Gratuito, oficial, chega a 2026-05. Base dos Dados para em 2025-11. |
| Base dos Dados | **Não assinar.** Uso opcional só para validação agregada até 2025-11 | Decisão do autor. |
| Reaproveitar parquets da V1 | **Não.** Download completo do zero | O MTE republica o histórico; misturar vintages invalida o vintage único. |
| Corte | **2026-05. Decidido pelo autor em 25/07/2026 — não revisitar.** | Junho sai em 30/07 e seria o mês mais incompleto da série. Ganho estatístico desprezível sobre 42 meses de pós. |
| Processamento | **Uma competência por vez**, descartando `.txt` | Pico de disco ~1 GB. Nunca carregar o ano inteiro em memória. |
| Formato intermediário | **Parquet particionado por competência** | Permite reprocessar um mês sem refazer tudo. |
| Ambiente Python | **`uv` com `pyproject.toml` fixado dentro de `V2/`** | Isolamento e reprodutibilidade. |
| Estimação | **`pyfixest`** (já usado na V1) + **R para HonestDiD** | Continuidade; HonestDiD não tem Python maduro. |
| Ordem | **Gates bloqueantes** | O gate da Tarefa 14 decide se vale seguir. |

### Estrutura de diretórios alvo

```
Replication Package/V2/
├── README.md                    ← atualizar (Tarefa 3)
├── DECISIONS.md                 ← log de decisões, append-only
├── pyproject.toml               ← ambiente fixado
├── run_replication.py           ← CLI, mesma interface da V1
├── code/
│   ├── ingest/                  ← Fase 1
│   │   ├── ftp_inventory.py
│   │   ├── download.py
│   │   ├── parse.py
│   │   └── build_movements.py
│   ├── panel/                   ← Fase 2
│   │   ├── crosswalk.py
│   │   ├── treatment.py
│   │   └── aggregate.py
│   ├── estimation/              ← Fases 4-5
│   │   ├── models.py
│   │   ├── event_study.py
│   │   └── diagnostics.py
│   ├── mechanisms/              ← Fase 6
│   └── common/
│       ├── contracts.py
│       ├── manifest.py
│       └── validation.py
├── data/
│   ├── vintage/                 ← manifest.json + os 195 .7z
│   ├── interim/                 ← parquet por competência
│   └── derived/                 ← painéis analíticos
├── results/
│   ├── reference/
│   └── reconciliation/          ← V1 vs V2
├── tests/
└── R/                           ← HonestDiD e replicação cruzada
```

---

## 3. Correções ao plano de origem

O `05_PLANO_V2.md` foi escrito antes desta verificação. Corrija estes pontos:

| Onde | Dizia | Correto |
|---|---|---|
| §3.2 | conteúdo em `latin-1` | Conteúdo **UTF-8**; **nomes de arquivo** em latin-1 |
| §3.4 e `03` §P2.2 | admissões de primeiro emprego como outcome | **Inviável** — variável morre em 2021 (§1.6) |
| §2.1 | 8,5 GiB livres, gate a resolver | **43 GiB livres, gate aberto com folga** |
| `03` §P0.9 | excluir transferências | **Verificar primeiro** — códigos 70/80 podem ser sempre zero |
| — | (ausente) | **Incompletude dos últimos ~12 meses** — nova Tarefa 9 |

---

## 4. Fases e tarefas

Notação: **XS/S/M** = tamanho. Nenhuma tarefa deve passar de 5 arquivos.

---

### FASE 0 — Ambiente e congelamento da V1

#### Tarefa 1: Provisionar o ambiente Python da V2

**Descrição.** Criar `Replication Package/V2/pyproject.toml` com dependências fixadas e verificar que
o ambiente instala do zero.

Use como base as versões da V1 (`Replication Package/V1/requirements.txt`) e acrescente
`py7zr` e `requests`. Não atualize versões sem registrar em `DECISIONS.md`.

**Critérios de aceitação:**
- [ ] `V2/pyproject.toml` existe, com versões **exatas** (`==`), não faixas.
- [ ] `uv sync` roda sem erro a partir de `V2/`.
- [ ] `uv run python -c "import pyfixest, pandas, pyarrow, py7zr; print('ok')"` imprime `ok`.

**Verificação:** `cd "Replication Package/V2" && uv sync && uv run python -c "import pyfixest; print(pyfixest.__version__)"`

**Dependências:** Nenhuma. **Tamanho:** S.

---

#### Tarefa 2: Provisionar o ambiente R

**Descrição.** Instalar os pacotes R necessários e registrar as versões. Necessários: `fixest`,
`HonestDiD`, `data.table`. Só `data.table` está instalado hoje.

**Critérios de aceitação:**
- [ ] `Rscript -e 'library(fixest); library(HonestDiD); library(data.table)'` roda sem erro.
- [ ] `V2/R/renv.lock` **ou** `V2/R/VERSIONS.md` registra as versões instaladas.

**Verificação:** `Rscript -e 'cat(as.character(packageVersion("fixest")), as.character(packageVersion("HonestDiD")))'`

**Dependências:** Nenhuma. **Tamanho:** XS.

> Se `HonestDiD` não instalar (depende de `CVXR`, que às vezes falha no macOS), **não invente
> alternativa**. Registre a falha em `DECISIONS.md` e siga — a Tarefa 20 fica bloqueada e será
> reportada como tal.

---

#### Tarefa 3: Verificar e congelar a V1

**Descrição.** Confirmar que a V1 ainda reproduz **a partir do novo caminho** `V1/` (a árvore foi
movida e caminhos relativos podem ter quebrado), escrever `V1/FROZEN.md`, e corrigir o
`V2/README.md`, que ainda diz que o gate de armazenamento está fechado.

**Critérios de aceitação:**
- [ ] A suíte de testes da V1 passa executando **de dentro de `V1/`**.
- [ ] `python V1/run_replication.py --section all --mode reproduce --dry-run` roda sem erro.
- [ ] `V1/FROZEN.md` existe e diz: o que reproduz, data do congelamento, e que os problemas
      conhecidos estão em `Final Review/Combined/01_AUDITORIA_CODIGO.md`.
- [ ] `V2/README.md` atualizado: gate de armazenamento **aberto**, 43 GiB livres.
- [ ] **Nenhum arquivo dentro de `V1/` foi modificado** além do `FROZEN.md` novo.

**Verificação:**
```bash
cd "Replication Package/V1" && uv run --with pytest pytest tests/ -q
git status --porcelain "Replication Package/V1" | grep -v FROZEN.md   # deve sair vazio
```

**Dependências:** Tarefa 1. **Tamanho:** S.

---

### ✅ CHECKPOINT A — Fundação

- [ ] Ambientes Python e R provisionados e versionados.
- [ ] A V1 reproduz a partir de `V1/` e está congelada.
- [ ] ≥15 GiB livres confirmados por `df -h`.
- [ ] **BLOQUEANTE.** Se a V1 não reproduzir a partir de `V1/`, ou se um ambiente não provisionar,
      pare e reporte. Não siga com fundação quebrada.

---

### FASE 1 — Ingestão do vintage

#### Tarefa 4: Inventário do FTP

**Descrição.** Listar todas as competências e arquivos disponíveis, registrar tamanho e data de
modificação de cada um.

**O corte já está decidido: 2026-05.** O autor decidiu em 25/07/2026. **Não implemente lógica de
detecção de corte, não olhe se `202606` apareceu, e não revisite esta escolha** — nem que a
competência de junho esteja publicada quando você executar. Apenas registre a decisão em
`V2/DECISIONS.md` reproduzindo esta justificativa: junho sairia em 30/07 e seria o mês mais
incompleto da série, com ganho estatístico desprezível sobre 42 meses de pós-tratamento.

Janela final: **2021-01 a 2026-05 = 65 competências**.

**Critérios de aceitação:**
- [ ] `V2/data/vintage/ftp_inventory.csv` com uma linha por arquivo: `competencia`, `tipo`
      (MOV/FOR/EXC), `url`, `bytes`, `data_modificacao_ftp`.
- [ ] O inventário tem exatamente **65 competências**, de `202101` a `202605`, sem buracos.
- [ ] Contagem esperada: **3 arquivos por competência = 195 linhas**. Qualquer competência com
      menos de 3 é **erro bloqueante** — pare e reporte.
- [ ] Se `202606` (ou posterior) existir no FTP, ele **não** entra no inventário.
- [ ] A decisão do corte está registrada em `V2/DECISIONS.md`.

**Verificação:** o CSV tem exatamente 195 linhas e `competencia` é contínua de `202101` a `202605`.

**Dependências:** Tarefa 1. **Tamanho:** S.
**Arquivo:** `V2/code/ingest/ftp_inventory.py`

---

#### Tarefa 5: Downloader com retomada e hash

**Descrição.** Baixar os arquivos do inventário com retomada, tentativas e verificação de
integridade.

Requisitos obrigatórios:
- Baixar para `.part` e renomear só ao concluir — nunca deixar arquivo truncado com nome final.
- Pular arquivo já baixado cujo tamanho bate com o inventário.
- 3 tentativas por arquivo, com espera crescente.
- Calcular SHA-256 de cada arquivo baixado.
- Envolver a execução longa em `caffeinate -i` para o Mac não dormir.

**Critérios de aceitação:**
- [ ] Todos os arquivos do inventário estão em `V2/data/vintage/` com o tamanho esperado.
- [ ] `V2/data/vintage/manifest.json` registra, por arquivo: `url`, `bytes`, `sha256`,
      `data_modificacao_ftp`, `baixado_em` (ISO-8601 UTC).
- [ ] Rodar o script duas vezes **não rebaixa nada** e não altera o manifesto.
- [ ] Nenhum `.part` sobrou.

**Verificação:**
```bash
uv run python V2/code/ingest/download.py --verify-only   # deve reportar 0 divergências
```

**Dependências:** Tarefa 4. **Tamanho:** M.
**Tempo esperado:** 10–20 min, ~3 GB.

---

#### Tarefa 6: Parser de uma competência com validação de domínio

**Descrição.** Função que recebe um `.7z`, descompacta em diretório temporário, lê o `.txt`, valida,
normaliza e devolve um DataFrame — **apagando o `.txt` ao final**.

Especificação obrigatória:
- Ler com `sep=';'`, `encoding='utf-8'`, `dtype=str` (converter depois, explicitamente).
- **Normalizar nomes de coluna**: remover acentos → `competenciamov`, `regiao`, `municipio`,
  `secao`, `saldomovimentacao`, `cbo2002ocupacao`, `graudeinstrucao`, `racacor`,
  `tipomovimentacao`, `tipodedeficiencia`, `salario`, `origemdainformacao`, `competenciadec`,
  `unidadesalariocodigo`, `valorsalariofixo`, `competenciaexc`, `indicadordeexclusao`.
- Converter decimais: `salario`, `valorsalariofixo`, `horascontratuais` usam **vírgula**.
- Validar domínios contra o dicionário de §1.5. Código fora do domínio = **fail-fast**, com o
  código e a contagem no erro.
- Aceitar 28 colunas (MOV/FOR) ou 30 (EXC). Qualquer outro número = erro.

**Critérios de aceitação:**
- [ ] Parseia MOV, FOR e EXC de 2021-01 e de 2026-05 sem erro.
- [ ] Nenhum `.txt` permanece em disco após a execução.
- [ ] Um código inválido injetado num arquivo de teste **levanta exceção** com mensagem clara.
- [ ] Teste unitário com um CSV sintético de 5 linhas cobrindo os três tipos.

**Verificação:** `uv run --with pytest pytest V2/tests/test_parse.py -q`

**Dependências:** Tarefa 5. **Tamanho:** M.
**Arquivos:** `V2/code/ingest/parse.py`, `V2/tests/test_parse.py`

---

#### Tarefa 7: Construir a base de movimentações MOV + FOR − EXC

**Descrição.** Para cada competência do inventário, ler os três arquivos e produzir um parquet
por **`competenciamov`** (não por competência de arquivo — ver armadilha nº 2 em §1.3).

Lógica obrigatória:
1. MOV(c) → todas as linhas têm `competenciamov = c`.
2. FOR(c) → linhas com `competenciamov < c`. **Somar** ao mês de referência.
3. EXC(c) → linhas com `competenciamov < c`. **Subtrair** do mês de referência.
4. Acrescentar uma coluna `origem` ∈ {`MOV`, `FOR`, `EXC`} e `competencia_arquivo`.
5. Gravar particionado: `V2/data/interim/movimentacoes/competenciamov=AAAAMM/part.parquet`.

Como "subtrair": as linhas de EXC representam movimentações a **remover**. Grave-as com uma coluna
`peso ∈ {+1, −1}` (+1 para MOV e FOR, −1 para EXC). Toda agregação posterior **soma `peso`** em vez
de contar linhas. Não tente casar linha a linha — o microdado é não-identificado e não tem chave.

**Critérios de aceitação:**
- [ ] Existe uma partição por competência de 2021-01 até o corte, sem buracos.
- [ ] `peso` só assume +1 e −1; a contagem de −1 bate com o total de linhas dos EXC processados.
- [ ] Uma tabela `V2/results/reconciliation/origem_por_competencia.csv` reporta, por
      `competenciamov`: linhas de MOV, de FOR, de EXC, e o líquido.
- [ ] Pico de disco durante a execução < 2 GB (medir e registrar).

**Verificação:** somar `peso` por competência e comparar com MOV−EXC+FOR calculado à parte.

**Dependências:** Tarefa 6. **Tamanho:** M.
**Arquivo:** `V2/code/ingest/build_movements.py`

---

#### Tarefa 8: Reconciliação com o V1 e com a Base dos Dados

**Descrição.** Quantificar a diferença entre o vintage V2 e o que a V1 usou. **Este é o entregável
que justifica a rodada inteira.**

Comparações obrigatórias:
1. **V2 vs V1**, por `competenciamov`, para 2021-01 a 2025-06: total de admissões, de
   desligamentos, e o delta absoluto e percentual.
2. **Decomposição do delta**: quanto vem de FOR, quanto de EXC, quanto de revisão do próprio MOV.
3. **V2 vs Base dos Dados** (opcional, gratuito, só até 2025-11): contagens por competência e por
   CBO de 2 dígitos. Use o BigQuery com o projeto `mestrado-pnad-2026`. **Se a autenticação falhar,
   registre e pule** — não é bloqueante.

**Critérios de aceitação:**
- [ ] `V2/results/reconciliation/v1_vs_v2_mensal.csv` com as colunas acima.
- [ ] `V2/results/reconciliation/RECONCILIACAO.md` resume: delta médio, delta máximo, e o mês de
      maior divergência.
- [ ] O delta de 2021 é **positivo e da ordem de 8%** (é o efeito do FOR). Se não for, **pare** —
      o parser está errado.

**Verificação:** o sinal e a ordem de grandeza batem com a auditoria (`01` §1).

**Dependências:** Tarefa 7. **Tamanho:** M.

---

#### Tarefa 9: Curva de completude e validação de continuidade das variáveis

**Descrição.** Três diagnósticos que decidem escolhas de desenho. **Nenhum modelo roda antes disto.**

**9a — Completude por competência.** Para cada `competenciamov`, calcular quantos meses de FOR ela
já pôde receber (= corte − competenciamov, limitado a 12) e a fração de linhas que vieram de FOR.
Produzir uma curva. **Os últimos ~12 meses são incompletos** (§1.4).

**9b — A incompletude é diferencial?** Repetir 9a **por grande grupo CBO** (primeiro dígito de
`cbo2002ocupacao`). Se a fração de FOR diferir entre grupos nos meses recentes, o mesmo viés que
contaminou a V1 no início contaminará a V2 no fim.

**9c — Continuidade das variáveis.** Para cada competência, reportar a fração de
"não identificado"/"tipo ignorado" em: `tipomovimentacao` (separado por admissão e desligamento),
`categoria`, `indicadoraprendiz`, `unidadesalariocodigo`, `racacor`, `graudeinstrucao`,
`tipoempregador`. E a contagem dos códigos 70 e 80 (transferências).

**Critérios de aceitação:**
- [ ] `V2/results/reconciliation/completude_por_competencia.csv` e um gráfico PNG.
- [ ] `V2/results/reconciliation/completude_por_grupo_cbo.csv`.
- [ ] `V2/results/reconciliation/continuidade_variaveis.csv`.
- [ ] `V2/DECISIONS.md` registra **a regra de janela escolhida**, entre:
      **(A)** usar a janela toda e incluir efeito fixo de mês (a incompletude uniforme é absorvida);
      **(B)** aparar os últimos K meses. **Escolha (A) por padrão**; só vá para (B) se 9b mostrar
      diferencial entre grupos tratado e controle acima de 1 ponto percentual.
- [ ] Registrar se as transferências (70/80) são sempre zero. Se forem, o filtro de P0.9 é inócuo —
      **documente, não remova**.

**Verificação:** revisão humana dos três CSVs. **Pare e mostre ao autor.**

**Dependências:** Tarefa 7. **Tamanho:** M.

---

### ✅ CHECKPOINT B — Vintage congelado

- [ ] 195 arquivos baixados, com hash, e manifesto completo.
- [ ] Movimentações MOV+FOR−EXC particionadas, sem buracos.
- [ ] Reconciliação V1 vs V2 pronta, com o delta de ~8% em 2021 confirmado.
- [ ] Curva de completude e regra de janela decididas e registradas.
- [ ] **BLOQUEANTE.** Se o delta de 2021 não for positivo e da ordem de +8%, o parser está errado —
      pare e reporte. Se a curva de completude (Tarefa 9b) mostrar diferencial acima de 1 p.p.
      entre grupos tratado e controle nos meses recentes, pare e reporte antes de escolher a
      regra de janela.

---

### FASE 2 — Painel analítico

#### Tarefa 10: Congelar o crosswalk CBO → ISCO-08

**Descrição.** Copiar o cache existente do crosswalk para a V2 e fixá-lo por hash. **Não raspe o
site do MTE** — o cache já existe em
`outputs/crosswalk_audit/source_dictionaries/mte_cbo2002_cbo94_ciuo88_by_family.csv` (1.550 linhas).

Também copiar e fixar por hash: `data/input/cbo-isco-conc.csv`,
`data/input/Correspondência ISCO 08 a 88.xlsx`, `data/input/ISCO 08 Estruturas e Definições.xlsx`,
`data/input/Final_Scores_ISCO08_Gmyrek_et_al_2025.xlsx`
(SHA-256 esperado: `c1940b87e7293b1eb95b530b6d3da7cd806b61d217c4bff1e69372b2cff5c90a`).

**Critérios de aceitação:**
- [ ] Todos os insumos em `V2/data/vintage/crosswalk/` com SHA-256 no manifesto.
- [ ] O hash da planilha da OIT bate com o esperado. Se não bater, **pare**.
- [ ] Reproduz a cobertura conhecida: **436 CBOs com score, 193 sem** — se divergir, pare e reporte.

**Verificação:** contar CBOs casadas e comparar com 436/193.

**Dependências:** Tarefa 7. **Tamanho:** S.

---

#### Tarefa 11: Reproduzir a classificação de tratamento atual

**Descrição.** Portar a regra de gradiente da V1 **sem alterações**, para servir de linha de base.
Fonte: `src/scripts/run_treatment_scenario_grid.py:168-190`.

**Critérios de aceitação:**
- [ ] Reproduz exatamente: 0 em G4, 31 em G3, 31 em G2, 13 em G1, 95 Minimal, 266 Not Exposed,
      193 No score.
- [ ] Se qualquer contagem divergir, **pare** — a portabilidade está errada.

**Verificação:** comparar com `outputs/treatment_scenario_grid/scenario_cbo_classification.csv`.

**Dependências:** Tarefa 10. **Tamanho:** S.

---

#### Tarefa 12: Agregar o painel nacional CBO4 × mês

**Descrição.** Construir o painel principal a partir das movimentações, com **a semântica de
missingness corrigida**.

Regras obrigatórias (estas são as correções P0.2, P0.5, P0.10 da auditoria):
- Unidade: `cbo_4d` (4 primeiros dígitos de `cbo2002ocupacao`) × `competenciamov`.
- Contagens: somar `peso`, não contar linhas.
- **Salário e composição são `NaN` quando o fluxo correspondente é zero — NUNCA zero.** Este é o
  bug que colocou 62 células com salário artificial de R$ 1.104,7868 na V1.
- **Winsorizar salário nos percentis 1 e 99 DENTRO de CBO4 × ano**, e aplicar a **mesma** regra ao
  salário de admissão e ao de desligamento. Na V1 só o de admissão era winsorizado, e o de
  desligamento chegava a R$ 203 milhões.
- Rejeitar antes de agregar: `salario <= 0`, `salario > 1e6`, `idade` fora de [14, 90],
  `cbo_4d` não numérico ou `0000`.
- Deflacionar pelo IPCA até o corte (o insumo local para em dez/2025 — estenda).

**Critérios de aceitação:**
- [ ] Nenhuma célula com fluxo zero tem salário não nulo.
- [ ] Salário máximo de admissão e de desligamento ambos abaixo de R$ 1 milhão.
- [ ] Relatório de suporte: nº de CBOs, meses por CBO (mín/máx), células totais.
- [ ] Teste automatizado que falha se qualquer uma das duas primeiras condições for violada.

**Verificação:** `uv run --with pytest pytest V2/tests/test_panel.py -q`

**Dependências:** Tarefas 9, 11. **Tamanho:** M.

---

#### Tarefa 13: Painel enriquecido CBO4 × CNAE × mês

**Descrição.** Mesma lógica da Tarefa 12, acrescentando CNAE à chave. **Este painel alimenta o
modelo co-principal do nível 2** (Tarefa 18b), não apenas uma robustez — a hierarquia foi restaurada
na revisão 2.

Guarde **dois níveis de CNAE**: `secao` (~19 categorias, para os efeitos fixos) e `divisao`
(~87 categorias, necessária para a clusterização bidirecional da Tarefa 18b). Não descarte a
divisão achando que a seção basta.

**Critérios de aceitação:**
- [ ] Agregar o painel enriquecido por CBO4 × mês **reproduz exatamente** o painel da Tarefa 12
      nas contagens. Se não reproduzir, há erro de agregação.
- [ ] `secao` e `divisao` CNAE ambas presentes e válidas contra o dicionário.
- [ ] Tabela de suporte: células por CBO4×CNAE×mês, percentil 10, e — o mais importante —
      **quantas CBOs tratadas e de controle coexistem dentro da mesma célula `cnae × periodo`**.
- [ ] Nenhuma linha duplicada em CBO4×CNAE×mês.

**Verificação:** comparação numérica entre os dois painéis.

**Dependências:** Tarefa 12. **Tamanho:** S.

---

#### Tarefa 14: ★ GATE PRINCIPAL — modelo antigo no painel novo

**Descrição.** Rodar a **especificação exata da V1**, sem nenhuma outra mudança, sobre o painel novo,
e medir o quanto cada coeficiente publicado se move.

Especificação da V1 a replicar literalmente:
```
ln_admissoes ~ post_treat + idade_media_adm + pct_mulher_adm
             + pct_superior_adm + pct_negra_adm | cbo_4d + periodo
```
com `vcov={"CRV1": "cbo_4d"}`, tratamento G1–G4 vs `Not Exposed`, janela 2021-01 a 2025-06.

Coeficientes de referência da V1: admissões **−0,0309** (0,0263); desligamentos **−0,0417**
(0,0254); salário real de admissão **−0,0207** (0,0140); `asinh(saldo)` **−0,6597** (0,3773).

**Critérios de aceitação:**
- [ ] `V2/results/reconciliation/gate_modelo_antigo.csv` com, por outcome: coeficiente V1,
      coeficiente V2, delta absoluto, delta percentual, e ambos os erros-padrão.
- [ ] O relatório declara explicitamente se algum coeficiente **muda de sinal** ou **cruza
      significância a 5%**.

**Verificação:** revisão humana. **Este resultado decide o resto do plano.**

**Dependências:** Tarefa 12. **Tamanho:** M.

---

### ✅ CHECKPOINT C — ★ Medição de referência (NÃO bloqueante)

- [ ] Painel nacional e enriquecido construídos, com missingness correta.
- [ ] Delta do modelo antigo quantificado por outcome.
- [ ] Relatório escrito e salvo.

**O autor autorizou seguir direto (25/07/2026). NÃO pare aqui.** Registre o resultado, escreva o
relatório e continue para a Fase 3, qualquer que seja o delta — inclusive se algum coeficiente
mudar de sinal ou cruzar significância.

Ainda assim, este é o resultado mais importante da rodada. Ele deve aparecer **no topo** de
`RECONCILIACAO.md` e ser repetido no `COMPARACAO_V1_V2.md` da Tarefa 32. Não o enterre num CSV.

Interpretação: delta pequeno → a Seção 5 sobrevive e o resto é incremental. Delta grande → é um
achado por si só e muda a narrativa. Qualquer um dos dois é resultado publicável, e nenhum dos
dois é motivo para mudar especificação.

> **Distinção importante para o executor.** Este checkpoint deixou de bloquear porque ele mede um
> *resultado*, não detecta um *defeito*. Os checkpoints que continuam **bloqueantes** são os que
> sinalizam pipeline quebrado: **B** (reconciliação — se o delta de 2021 não for ~+8%, o parser
> está errado) e **F** (placebo temporal significativo — o desenho não se sustenta). Esses dois
> você para e reporta, sem exceção.

---

### FASE 3 — Classificação de tratamento

#### Tarefa 15: Três variantes de gradiente

**Descrição.** Implementar as variantes de sensibilidade de `03` §P0.8, **pré-registradas antes de
olhar qualquer resultado**.

Contexto: a regra atual é assimétrica — G4 exige `média − DP ≥ 0,50` enquanto G1–G3 exigem
`média + DP ≥ 0,50` — e o DP soma dispersão entre destinos ISCO à dispersão entre tarefas. Por isso
nenhuma CBO chega a G4, embora 16 CBOs toquem uma das 13 ocupações ISCO-08 classificadas como G4.

- **V-A (base):** regra atual, inalterada (= Tarefa 11).
- **V-B:** média entre destinos ISCO **ponderada por emprego** (use admissões pré-tratamento do
  próprio painel como peso), no lugar de `np.nanmean`.
- **V-C:** usar **apenas o DP entre tarefas da OIT** na regra; reportar a dispersão entre destinos
  como métrica separada de qualidade do crosswalk.
- **V-D:** classificar no nível do destino ISCO (onde o gradiente é nativo) e agregar os **rótulos**
  ponderados por emprego.

**Critérios de aceitação:**
- [ ] Tabela comparando as quatro variantes: nº de CBOs por gradiente, e quantas mudam de grupo.
- [ ] Relatório específico sobre a CBO **4121** (operadores de entrada de dados), que corresponde à
      ISCO 4132 (score 0,70, a mais exposta do índice) e sai como G3 na regra atual.
- [ ] `V2/DECISIONS.md` declara **V-A como principal** e B/C/D como sensibilidade, **antes** de
      qualquer estimação.

**Verificação:** revisão humana da tabela comparativa.

**Dependências:** Tarefa 14. **Tamanho:** M.

---

### ✅ CHECKPOINT D — Tratamento

- [ ] Quatro variantes implementadas e comparadas.
- [ ] Principal e sensibilidades declaradas por escrito antes de estimar.

---

### FASE 4 — Núcleo econométrico

#### Tarefa 16: Módulo de estimação

**Descrição.** Implementar os estimadores do contrato congelado (`05` §4).

- **Contagens (admissões, desligamentos, fluxo bruto): PPML principal** (`pyfixest.fepois`).
  Reportar efeito como `100 × (exp(β) − 1)`. Registrar convergência, separação e células
  descartadas.
- Secundário: OLS em `log(1+y)`.
- **Salário: OLS no log do salário real, só em células com salário válido.**
- Complementar: `asinh(saldo)`.
- **Sem controles de composição contemporâneos na especificação principal.**
- Efeitos fixos: o módulo precisa aceitar a especificação como **parâmetro**, porque a Tarefa 18b
  roda três níveis (`cbo_4d + periodo` · `cbo_4d^cnae + cnae^periodo` · o anterior mais
  `cbo_2d^periodo`). Não fixe os efeitos fixos no código.
- Erros CRV1 por `cbo_4d` no principal; o módulo deve aceitar clusterização **bidirecional** como
  opção, para a Tarefa 18b.

**Critérios de aceitação:**
- [ ] Todo modelo devolve: coeficiente, EP, IC, p, N, nº de clusters, células descartadas.
- [ ] IC calculado com **t nos graus de liberdade do cluster**, não 1,96 fixo.
- [ ] A fórmula principal **não contém** `idade_media_adm`, `pct_mulher_adm`, `pct_superior_adm`
      nem `pct_negra_adm` — teste automatizado que falha se contiver.

**Verificação:** `uv run --with pytest pytest V2/tests/test_models.py -q`

**Dependências:** Tarefa 15. **Tamanho:** M.

---

#### Tarefa 17: Event study balanceado

**Descrição.** Event study **sem agrupamento de caudas**, janela `t = −23` a `t = +23`, referência
`t = −1` (nov/2022). Mais horizontes nomeados para o período longo.

Horizontes: dez/2022–nov/2023 · dez/2023–nov/2024 · dez/2024–nov/2025 · dez/2025–corte
(**marcado como parcial**).

**Critérios de aceitação:**
- [ ] Uma única convenção de janela em todo o código — a V1 tinha duas, e por isso a Tabela A.1 e a
      Figura 5.1 tinham N diferentes (18.307 vs 12.538).
- [ ] Nenhum coeficiente agrupa meses heterogêneos.
- [ ] Teste que falha se a grade de tempo de evento tiver buraco ou se `t = −1` não for a referência.

**Verificação:** inspecionar a grade de coeficientes exportada.

**Dependências:** Tarefa 16. **Tamanho:** M.

---

#### Tarefa 18: Escada de controles, amostras e medida de exposição

**Descrição.** Rodar e tabular a escada de **controles e amostras**, com efeitos fixos fixados no
nível 1 (`cbo_4d + periodo`). A escada de **efeitos fixos** é a Tarefa 18b. **Todas as
especificações são reportadas**, nenhuma escolhida por p-valor.

Degraus: sem controles (principal) · controles pré-tratamento × pós · controles contemporâneos
(descritiva condicional, rotulada como potencialmente pós-tratamento) · controle ampliado incluindo
`Minimal Exposure` · exposição contínua padronizada · sensibilidade iniciando em jan/2022 ·
sensibilidade terminando em dez/2025.

**Critérios de aceitação:**
- [ ] Uma tabela com todos os degraus, para todos os outcomes principais.
- [ ] A exposição contínua é reportada **lado a lado** com a binária, não escondida na robustez.
- [ ] Nenhum degrau foi omitido por dar resultado feio — conferir contra a lista acima.

**Verificação:** revisão humana da tabela.

**Dependências:** Tarefa 17. **Tamanho:** M.

---

#### Tarefa 18b: Escada de efeitos fixos e inferência setorial

**Descrição.** Implementar a hierarquia de efeitos fixos de `Final Review/Combined/05_PLANO_V2.md`
§4.1. **Esta tarefa foi acrescentada na revisão 2** — restaura o `final_review_planning.md` §2.4 do
autor, que a versão anterior do plano havia rebaixado.

| Nível | Especificação | Papel |
|---|---|---|
| 1 | `cbo_4d + periodo` | **Benchmark nacional.** Sempre reportado. |
| 2 | `cbo_4d^cnae + cnae^periodo` | **Principal enriquecido.** Sempre reportado, lado a lado com o nível 1. |
| 3 | nível 2 + `cbo_2d^periodo` | **Diagnóstico de suporte**, não teste de robustez. |

Mais: **clusterização bidirecional `cbo_4d` × **divisão** CNAE** como robustez do painel setorial.
Use divisão (~87 categorias), **nunca seção (~19)** — poucos clusters numa das dimensões produz
cobertura abaixo do nominal.

**Ordem obrigatória: a tabela de suporte sai ANTES dos coeficientes.** Ela precisa reportar, por
nível de efeito fixo:

- número de células;
- percentil 10 de observações por célula;
- **quantas CBOs tratadas e de controle coexistem dentro da mesma célula de efeito fixo** — esta é
  a métrica que importa, não a contagem total de células.

**Critérios de aceitação:**
- [ ] Níveis 1 e 2 estimados e reportados **lado a lado**, para todos os outcomes principais.
- [ ] A diferença entre os níveis 1 e 2 é reportada explicitamente como resultado, com uma frase de
      leitura: estável → evidência contra confundimento setorial; instável → achado a explicar.
- [ ] Tabela de coexistência tratado/controle publicada antes de qualquer coeficiente de nível 2 ou 3.
- [ ] Se no nível 3 a coexistência cair abaixo de **20 CBOs tratadas**, o nível 3 é reportado
      **apenas como diagnóstico**, com a variação remanescente ao lado e **sem interpretação
      substantiva**. Registre em `DECISIONS.md`.
- [ ] Clusterização bidirecional reportada com o número de clusters em cada dimensão. **Nunca como
      principal.**

**Ressalvas para o executor — leia antes de interpretar:**

1. O nível 2 **muda o estimando**. Deixa de ser "expostas versus não expostas no Brasil" e passa a
   ser "dentro do setor, expostas versus não expostas". Se parte do efeito for realocação entre
   setores, o nível 2 absorve exatamente o que se quer medir. Por isso 1 e 2 são co-principais e
   nunca substitutos.
2. **Espere que o nível 3 mate a variação.** A exposição é fortemente correlacionada dentro de grupo
   CBO de 2 dígitos — o grupo 4 (administrativo) é quase todo exposto, o 6 (agropecuária) quase todo
   não exposto. Um coeficiente que colapsa no nível 3 **não** é evidência de que o efeito não
   sobrevive; é evidência de que a variação não sobrevive. Não escreva a primeira conclusão.
3. Clusterização bidirecional às vezes produz erro-padrão **menor** que unidirecional. Se isso
   acontecer, reporte assim mesmo e não promova a bidirecional a principal.

**Verificação:** revisão humana da tabela de suporte antes de olhar qualquer coeficiente.

**Dependências:** Tarefas 13, 18. **Tamanho:** M.

---

### ✅ CHECKPOINT E — Núcleo

- [ ] PPML converge para todos os outcomes de contagem.
- [ ] Event study sem agrupamento, convenção única.
- [ ] Escada de controles e amostras completa (T18).
- [ ] Níveis 1 e 2 de efeitos fixos reportados lado a lado, com a diferença entre eles comentada.
- [ ] Tabela de coexistência tratado/controle publicada **antes** dos coeficientes de nível 2 e 3.
- [ ] Nível 3 enquadrado como diagnóstico, não como teste de robustez.

---

### FASE 5 — Diagnóstico e inferência

#### Tarefa 19: Pretrends sobre o modelo exato

**Descrição.** Testar tendências prévias **no mesmo modelo e na mesma amostra** do resultado
reportado. Na V1 isso não acontecia.

**Critérios de aceitação:**
- [ ] Cada outcome tem: teste conjunto dos leads, teste de tendência linear pré, e a classificação
      pass/warning/fail — os três **nomeados distintamente**, nunca tratados como o mesmo teste.
- [ ] O N e o nº de clusters do teste batem **exatamente** com os do modelo reportado.
- [ ] O relatório declara explicitamente que um pretrend não significativo **não é prova** de
      tendências paralelas.

**Verificação:** conferir N e clusters entre a tabela de resultado e a de diagnóstico.

**Dependências:** Tarefa 18. **Tamanho:** M.

---

#### Tarefa 20: HonestDiD / Rambachan–Roth em R

**Descrição.** Para os outcomes lineares, exportar os coeficientes do event study e sua matriz de
covariância, e rodar `HonestDiD` em R para obter limites do efeito em função do parâmetro de
suavidade M.

**Critérios de aceitação:**
- [ ] `V2/R/honest_did.R` lê os coeficientes exportados e devolve os intervalos por M.
- [ ] Reportar, para cada outcome, o **maior M para o qual o intervalo exclui zero** — este é o
      número que substitui "os pretrends falham, logo é exploratório".
- [ ] Um gráfico de sensibilidade por outcome.

**Verificação:** `Rscript V2/R/honest_did.R` roda e produz os CSVs.

**Dependências:** Tarefas 2, 19. **Tamanho:** M.

> Se a Tarefa 2 falhou em instalar `HonestDiD`, registre esta tarefa como **bloqueada** e siga.
> Não substitua por uma aproximação caseira.

---

#### Tarefa 21: Correção por testes múltiplos

**Descrição.** Aplicar correção à família de heterogeneidades, **pré-especificada**.

Família: os contrastes DDD dos outcomes principais nas cinco dimensões existentes (sexo, raça/cor,
idade, escolaridade, renda). Método: Romano–Wolf se viável, senão Benjamini–Hochberg.

**Critérios de aceitação:**
- [ ] Toda tabela de heterogeneidade traz **p nominal e p ajustado lado a lado**.
- [ ] A família está declarada em `V2/DECISIONS.md` **antes** de rodar.
- [ ] DDD implementado **só** com `post × tratamento × subgrupo` mais todos os termos de ordem
      inferior — teste automatizado que verifica a presença dos quatro termos.

**Verificação:** `uv run --with pytest pytest V2/tests/test_ddd.py -q`

**Dependências:** Tarefa 19. **Tamanho:** M.

---

#### Tarefa 22: Falsificação

**Descrição.** Dois exercícios.

- **Placebo temporal:** evento falso em dez/2021, amostra restrita ao período pré-tratamento
  verdadeiro.
- **Placebo de grupo:** reatribuir tratamento aleatoriamente entre CBOs preservando a distribuição
  de tamanho, 500 repetições, e localizar o coeficiente observado na distribuição.

**Critérios de aceitação:**
- [ ] O placebo temporal do desenho nacional **não é significativo a 5%**. Se for, **pare e reporte**
      — na extensão Anatel esse mesmo teste falhou, e é informação decisiva.
- [ ] O placebo de grupo reporta o percentil do coeficiente observado.

**Verificação:** revisão humana.

**Dependências:** Tarefa 18. **Tamanho:** M.

---

### ✅ CHECKPOINT F — Diagnóstico

- [ ] Pretrends sobre o modelo exato, com os três testes nomeados distintamente.
- [ ] Limites de HonestDiD, ou bloqueio registrado.
- [ ] p ajustado em toda heterogeneidade.
- [ ] **BLOQUEANTE — placebo temporal nacional não significativo a 5%.** Se for significativo, o
      desenho não se sustenta: pare e reporte. Não siga para a Fase 6, e não ajuste especificação
      para "consertar" o placebo.

---

### FASE 6 — Mecanismos

#### Tarefa 23: Decomposição de desligamentos por tipo — **maior valor do plano**

**Descrição.** Estimar o desenho principal separadamente para cada família de desligamento.

Famílias (códigos de §1.5):
- **Demissão sem justa causa** = 31 → decisão da firma
- **A pedido** = 40 → decisão do trabalhador
- **Término de contrato** = 43 + 45
- **Com justa causa** = 32 + 33
- **Acordo** = 90
- **Excluir do total:** aposentadoria (50), morte (60), transferência (80)
- **Reportar à parte:** tipo ignorado (98)

Interpretação pré-registrada: se caírem as **demissões**, a decisão é da firma — retenção. Se caírem
os **pedidos**, é o trabalhador — deterioração da alternativa externa. **Registre esta interpretação
em `DECISIONS.md` antes de ver o resultado.**

**Critérios de aceitação:**
- [ ] Tabela e event study por família.
- [ ] Tabela de suporte por família (algumas são pequenas — acordo é 1%).
- [ ] A soma das famílias reproduz o total de desligamentos, menos as excluídas.
- [ ] Correção de multiplicidade aplicada à família ampliada.

**Verificação:** conferência da soma.

**Dependências:** Tarefas 21, 22. **Tamanho:** M.

---

#### Tarefa 24: Proxy de estoque por saldo acumulado

**Descrição.** Acumular o saldo mensal por CBO desde jan/2021 e normalizar em 100 na base, criando
um índice de emprego relativo — o objeto que a literatura de referência estima.

**Critérios de aceitação:**
- [ ] Série por CBO, normalizada, com o DiD estimado sobre ela.
- [ ] O relatório declara que é **variação acumulada de fluxo**, não estoque em nível, e que não
      incorpora saídas não registradas.

**Verificação:** inspecionar a série de algumas CBOs grandes.

**Dependências:** Tarefa 23. **Tamanho:** S.

---

#### Tarefa 25: Salário-hora e margem de jornada

**Descrição.** Usar `horascontratuais` para construir salário por hora, e `indtrabparcial` /
`indtrabintermitente` para separar a margem de jornada da margem de preço.

**Critérios de aceitação:**
- [ ] Salário-hora reportado ao lado do mensal, para o mesmo desenho.
- [ ] Diagnóstico da cobertura de `horascontratuais` por competência (Tarefa 9c).
- [ ] Se a cobertura tiver quebra estrutural como a de `tipomovimentacao`, **não use como outcome** —
      reporte a quebra.

**Verificação:** conferir a continuidade antes de estimar.

**Dependências:** Tarefa 23. **Tamanho:** S.

---

#### Tarefa 26: Porte e natureza do empregador

**Descrição.** Heterogeneidade por `tamestabjan` (porte) e falsificação por `tipoempregador` /
`tipoestabelecimento` (público vs privado).

Lógica da falsificação: emprego público não responde a pressão competitiva de IA. Se o efeito
aparecer no privado e não no público **dentro das mesmas ocupações expostas**, é evidência a favor.

**Critérios de aceitação:**
- [ ] Tabela de suporte por faixa de porte e por natureza.
- [ ] O contraste público vs privado é reportado como falsificação, com a lógica declarada antes.

**Dependências:** Tarefa 23. **Tamanho:** S.

---

#### Tarefa 27: Sensibilidade da medida de exposição

**Descrição.** Três testes usando colunas já presentes na planilha da OIT.

- Vintage **2023** (`mean_score_2023`, `SD_2023`, `potential23`) contra o de 2025.
- Discordância entre modelos: `predicted_score_2025_gpt4o` vs `predicted_score_2025_gemini`;
  restringir às ocupações onde os dois concordam.
- Correlação de postos com o índice da Anthropic em
  `data/processed/anthropic_automation_augmentation_cbo.parquet`.

**Critérios de aceitação:**
- [ ] Os três reportados, com o coeficiente principal recalculado em cada um.

**Dependências:** Tarefa 23. **Tamanho:** M.

---

### ✅ CHECKPOINT G — Mecanismos

- [ ] Decomposição de desligamentos completa, com suporte.
- [ ] Todo exercício novo tem tabela de suporte e p ajustado.

---

### FASE 7 — Empacotamento

#### Tarefa 28: Contratos e manifesto da V2

**Descrição.** Portar o padrão de contratos da V1 (`V1/code/sections4_5/contracts.py`) e acrescentar
**contratos semânticos**: rótulos de tabela, conjuntos de categorias permitidas, unidades, e ID de
fonte.

Isso corrige o defeito que deixou os artefatos `table_a_6_income_*` serem gerados da tabela de
escolaridade sem que nenhum teste percebesse.

**Critérios de aceitação:**
- [ ] Todo artefato declara sua fonte e as categorias que pode conter.
- [ ] Um teste que injeta a tabela errada numa saída **falha**.
- [ ] `results/reference` é validado contra manifesto assinado **antes** de qualquer comparação.

**Verificação:** o teste de injeção falha como esperado.

**Dependências:** Tarefa 27. **Tamanho:** M.

---

#### Tarefa 29: `run_replication.py` da V2

**Descrição.** CLI com a mesma interface da V1:
`--section {all,3,4-5} --mode {reproduce,full} [--raw-dir] [--output-dir] [--skip-figures] [--dry-run]`.

**Requisito central:** no modo `reproduce`, **todo artefato inferencial é re-estimado**, não
renderizado de CSV congelado. Na V1 só quatro modelos nacionais eram re-estimados.

**Critérios de aceitação:**
- [ ] `--dry-run` imprime o DAG completo e o preflight de insumos.
- [ ] `reproduce` re-estima: event studies, pretrends, DDD, PPML, salário real, heterogeneidades e
      mecanismos.
- [ ] O log distingue explicitamente `re-estimado`, `estimativa congelada validada` e
      `artefato renderizado`.

**Verificação:** `uv run python V2/run_replication.py --dry-run`

**Dependências:** Tarefa 28. **Tamanho:** M.

---

#### Tarefa 30: Suíte de testes da V2

**Descrição.** Testes que viram gates de release.

Mínimo obrigatório:
1. Salário é `NaN` sempre que o fluxo correspondente é zero.
2. Salários inválidos são rejeitados antes da agregação.
3. A fórmula principal não contém controles contemporâneos.
4. Toda tabela inferencial tem um teste de estimador vivo, não um CSV copiado.
5. A grade do event study é completa e sem agrupamento.
6. Todo merge reporta unicidade e delta de linhas.
7. Fixtures de códigos demográficos incluem desconhecido e ausente.
8. Todos os arquivos de referência batem com o manifesto.
9. **Os totais mensais reconciliam com o agregado oficial** — o teste que teria pegado o achado do
   fora do prazo.
10. Superior completo = `{9,10,11,80}`, sem o código 8.

**Critérios de aceitação:**
- [ ] Os dez testes existem e passam.
- [ ] **Há teste cobrindo a camada de construção de dados** — na V1 não havia nenhum.

**Verificação:** `cd "Replication Package/V2" && uv run --with pytest pytest tests/ -q`

**Dependências:** Tarefa 29. **Tamanho:** M.

---

#### Tarefa 31: Replicação cruzada Python ↔ R

**Descrição.** Implementação independente em R dos modelos centrais, comparada com a Python.

**Critérios de aceitação:**
- [ ] Mesma amostra: N e nº de clusters idênticos.
- [ ] Coeficientes e erros-padrão concordam a **pelo menos seis decimais**, ou a discrepância é
      diagnosticada por escrito.
- [ ] Cobre no mínimo os quatro outcomes principais **mais** o salário real de admissão — na V1 o
      salário real não era verificado.

**Verificação:** `Rscript V2/R/cross_replication.R` e comparação automatizada.

**Dependências:** Tarefas 2, 30. **Tamanho:** M.

---

#### Tarefa 32: `COMPARACAO_V1_V2.md`

**Descrição.** Documento com **uma linha por mudança**: o que mudou, por quê, e o efeito no
coeficiente principal.

**Critérios de aceitação:**
- [ ] Cobre: vintage (FOR/EXC), missingness de salário, winsorização, controles, janela, estimador,
      classificação de tratamento, e cada mecanismo novo.
- [ ] Cada linha traz o delta numérico quando aplicável.
- [ ] Inclui a tabela do gate da Tarefa 14.

**Dependências:** Tarefa 31. **Tamanho:** S.

---

### ✅ CHECKPOINT H — Pacote pronto

- [ ] Suíte completa passa.
- [ ] Replicação cruzada concorda a seis decimais.
- [ ] `COMPARACAO_V1_V2.md` completo.
- [ ] **Entregar ao autor. O texto da dissertação é uma rodada separada.**

---

## 5. Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| O parser não reconcilia com a V1 nem com o PDET | Alto | Gate da Tarefa 8. Se o delta de 2021 não for ~+8%, o parser está errado — não siga. |
| Os resultados enfraquecem | **Esperado** | Não é motivo para mudar especificação. Reporte o que os dados sustentam. |
| Últimos meses incompletos criam viés no fim | Médio | Tarefa 9b mede. Se houver diferencial >1 p.p. entre tratado e controle, apare os últimos meses. |
| `HonestDiD` não instala | Médio | Registre bloqueio. Não improvise substituto. |
| Suporte fino em CBO4×CNAE | Médio | Gate da Tarefa 18: vira robustez em vez de principal. |
| FTP fora do ar durante o download | Baixo | Retomada e tentativas na Tarefa 5. |
| Disco enche | Baixo | 43 GiB livres, pico previsto ~4 GB. Monitorar na Tarefa 7. |

## 6. Condições de parada

Registre `NOT EXECUTED` e pare, em vez de entregar resultado parcial, se:

- o vintage não puder ser congelado ou reconciliado (Tarefa 8);
- o placebo temporal nacional for significativo (Tarefa 22);
- os modelos preferidos falharem convergência ou suporte de um jeito que mude o estimando;
- executar exigir mudar a estrutura da dissertação.

## 7. Decisões do autor — 25/07/2026

Não há perguntas em aberto. As três decisões abaixo estão fechadas. **Não as reabra.**

| # | Decisão | Efeito no plano |
|---|---|---|
| 1 | **Corte fixado em 2026-05.** Executar agora, sem esperar a competência de junho. | Tarefa 4: janela 2021-01 a 2026-05, 65 competências, 195 arquivos. Nenhuma lógica de detecção de corte. |
| 2 | **Checkpoint C não bloqueia.** Seguir direto para a Fase 3 qualquer que seja o delta. | Checkpoint C vira medição de referência. Registre e continue. **B e F continuam bloqueantes.** |
| 3 | **Painel PNADc de 16 trimestres fica fora.** | Não implementar. Fica como rodada separada, se houver energia depois. |

Se surgir uma questão nova durante a execução que exija decisão do autor, **pare, registre em
`V2/DECISIONS.md` e pergunte** — não escolha por conta própria.

## 8. Fora de escopo desta rodada

Nada disto deve ser implementado, mesmo que pareça uma boa ideia durante a execução:

- **Texto da dissertação.** Nenhuma edição em `Dissertação/`. É uma rodada separada.
- **Painel PNADc de 16 trimestres** (`archive/etapa5_did_ocupacional/`) — decisão 3 acima.
- **Admissões por primeiro emprego** — variável morre em 2021, ver §1.6.
- **Validação de difusão via Google Trends** (Task 13 do `final_review_planning.md`). Adiada em
  26/07/2026 para a rodada do texto. Motivos: fonte nova numa rodada já longa; mede consciência e
  não adoção no trabalho; e **convida ao garimpo de data de corte**, que o §3 do plano do autor
  proíbe. Não muda nenhuma estimativa — é ativo de texto.
- **Extensão Anatel / conectividade municipal** — falha falsificação, ver `05` §8.
- **Atualização da Seção 3 / PNADc 2026 Q1** — a Seção 3 fica congelada como está.
- **RAIS** para ancorar estoque em nível.
- **Base dos Dados paga.** O autor decidiu não assinar. Uso gratuito só como validação opcional e
  não bloqueante até 2025-11.
