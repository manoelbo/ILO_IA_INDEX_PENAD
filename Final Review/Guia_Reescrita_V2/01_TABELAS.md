# Tabelas a substituir

**Rodada 2 do guia.** Caminhos conferidos por comando em 28 de julho de 2026.

Raiz dos artefatos: `Replication Package/V2/results/tables/`. Toda tabela existe em par
`.csv` (auditoria) e `.md` (para colar no texto). Use o `.md`.

**São 18 tabelas.** Uma é nova.

---

## Seção 4 — quatro tabelas, todas com números novos

| ID | Linha | Artefato novo | O que muda |
|---|---:|---|---|
| **4.2.1** Escopo do painel | 331 | `table_4_2_1_panel_scope.md` | **os quatro valores** |
| **4.2.2** Classificação das CBOs | 346 | `table_4_2_2_treatment_classification.md` | V-A idêntica, mas entram as três variantes pré-registradas |
| **4.2.3** Cobertura por grupo | 366 | `table_4_2_3_panel_coverage.md` | números novos |
| **4.3.1** Outcomes | 403 | `table_4_3_1_outcomes.md` | **de 4 para 5 outcomes**; estimador de contagem vira PPML |

### 4.2.1 é a que mais quebra

| | V1 (impresso) | V2 |
|---|---:|---:|
| Observações CBO-mês | 23.319 | **22.049** |
| CBOs únicos | 436 | **341** |
| Meses | 54 | **65** |
| Janela | 2021-01 a 2025-06 | **2021-01 a 2026-05** |

Os 436 da V1 eram as CBOs com correspondência oficial na ponte MTE; a amostra estimada tinha 341
(75 tratadas mais 266 controle). A auditoria da V1 já apontava essa contradição — item 8, *"o
universo de CBOs é internamente contraditório"*. Resolva declarando os dois números com nomes
diferentes.

**Afirmação afetada, linha 336:** *"preservando aproximadamente 23 meses anteriores ao evento e 31
meses posteriores"* → 23 anteriores e **42** posteriores.

### 4.3.1 muda de forma, não só de número

Entra o fluxo bruto como quinto outcome, e o rótulo das contagens tem de mudar: o coeficiente PPML
é **semi-elasticidade da média condicional em nível**, não log-log. Manter "Admissões (log)" seria
erro de interpretação, não de estética.

---

## Seção 5 — sete tabelas, mais uma nova

| ID | Linha | Artefato novo | O que muda |
|---|---:|---|---|
| **5.1** Resultados nacionais | 428 | `table_5_1_national_results.md` | todos os coeficientes |
| **5.1.1** Controle setorial | **nova** | `table_5_1_1_sector_control.md` | não existe no texto |
| **5.2.1** Sexo | 464 | `table_5_2_1_sex.md` | números, estrelas e coluna de pretrend |
| **5.2.2** Raça/cor | 512 | `table_5_2_2_race.md` | idem |
| **5.2.3** Faixa etária | 556 | `table_5_2_3_age.md` | idem |
| **5.2.4** Escolaridade | 623 | `table_5_2_4_education.md` | idem |
| **5.2.5** Faixa salarial | 671 | `table_5_2_5_income.md` | idem, mais rótulo de suporte |
| **5.3.1** Casos ocupacionais | 734 | `table_5_3_1_occupation_cases.md` | base temporal e janela-resumo |

### 5.1 — os números

| Outcome | V1 | V2 |
|---|---:|---:|
| Admissões | −0,0309 (0,0263) | **−0,0538** (0,0386) |
| Desligamentos | −0,0417 (0,0254) | −0,0420 (0,0347) |
| Salário real de admissão | −0,0207 (0,0140) | **−0,0507** (0,0103), p < 0,001 |
| Saldo (asinh) | −0,6597 (0,3773) | −0,5513 (0,3783) |

**Afirmação que cai, linha 440:** *"nenhum é estatisticamente significativo"*. O salário rejeita a
5% com folga. E *"As reduções aproximadas são de 3,0%, 4,1% e 2,0%"* → 5,4%, 4,2% e 5,1%.

### 5.1.1 é nova e precisa entrar

O **nível 2** — efeitos fixos de CBO4 × seção CNAE e seção CNAE × mês — está declarado
`co_principal_sector` no contrato congelado e não aparece em lugar nenhum do texto. Controlando por
setor, as admissões vão de −0,0538 (p = 0,164) para **−0,0751 (p = 0,036)** e passam a rejeitar; o
salário encolhe de −0,0507 para −0,0356.

Klein Teeselink (2025, p. 11) usa efeitos fixos de indústria × período na **equação principal**, e
Canaries usa firma × tempo. A ausência desse exercício no texto é lacuna, não escolha.

### 5.2.x — três mudanças estruturais, não só de número

1. **Estrelas passam a vir do p ajustado por BH**, não do nominal. São 34 contrastes nominalmente
   significativos e 21 sobreviventes.
2. **Entra uma coluna de pretrend** em toda linha. Com as 51 células de diagnóstico falhando, um
   coeficiente sozinho convida ao excesso de leitura.
3. **Entra a nota que separa DiD dentro do grupo de heterogeneidade.** Está pronta e verbatim nos
   `.md` renderizados — copie de lá.

A nota existe porque 22 dos 26 grupos mostram queda salarial significativa, o que **não é
heterogeneidade**: é o efeito nacional aparecendo em todo grupo. O teste de diferença entre grupos
é o DDD do Apêndice A, onde sobrevivem 2 contrastes salariais em 100.

---

## Apêndice A — seis tabelas

| ID | Linha | Artefato novo | O que muda |
|---|---:|---|---|
| **A.1** Diagnósticos nacionais | 774 | `table_a_1_national_diagnostics.md` | **o pretrend do salário** |
| **A.2** DDD sexo | 796 | `table_a_2_sex.md` | nominal e BH lado a lado |
| **A.3** DDD raça | 822 | `table_a_3_race.md` | **passa a ter seis categorias** |
| **A.4** DDD idade | 837 | `table_a_4_age.md` | dois painéis com família declarada |
| **A.5** DDD escolaridade | 931 | `table_a_5_education.md` | nominal e BH lado a lado |
| **A.6** DDD renda | 958 | `table_a_6_income.md` | idem, mais suporte |

### A.1 é o reparo mais urgente do texto inteiro

A tabela impressa certifica o pretrend do salário como **`pass (p=0,932)`**. Na V2 é
**`fail (p=1,6e-04)`**, com 11 dos 22 leads individualmente significativos.

É a célula que dá credibilidade ao único resultado significativo do trabalho, e ela afirma hoje o
oposto do que os dados dizem. O artefato novo já traz a nota explícita, e há um teste no pacote que
falha se ela voltar a dizer `pass`.

**O Painel B.2 também muda:** as construções `saldo/admissões pré` e `saldo/fluxo total` não
existem na V2. Foram substituídas pelo proxy cumulativo (+1,429; EP 1,309; p = 0,276), com a nota
de que não é estoque de emprego. **A.1 é a única tabela que mantém um Painel B.2** — nas de
heterogeneidade ele foi cortado.

### A.3 e A.4 mudam de forma

**A.3** passa a reportar as **seis** categorias raciais, não só Branca e Negra. A categoria amarela
tem os maiores coeficientes de toda a família — admissões −0,277, BH p < 1e-4 — e a V1 não a
reportava.

**A.4** traz dois painéis: faixas PNAD/IBGE (Família B, 30 testes) e coortes Canaries (Família A,
100 testes), com o identificador de família visível em cada um. São partições diferentes do mesmo
fenômeno e o leitor precisa ver as duas.

---

## Como usar

Cada `.md` renderizado já contém a nota de rodapé correta, com a família de multiplicidade, o
tamanho dela e a fonte do número. **Copie a nota junto com a tabela.** Ela foi escrita antes da
renderização justamente para não ser racionalizada depois.

O relatório `Replication Package/V2/results/RENDERIZACAO_8B.md` traz, para cada artefato, a fonte e
se a afirmação que ele sustentava mudou.
