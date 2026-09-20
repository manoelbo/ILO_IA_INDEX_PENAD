# Adições possíveis — o que a V2 tem e o texto não usa

**Rodada 5 do guia.**

Critério: um item entra **se sustenta ou qualifica uma afirmação do texto**, não porque existe. A
V2 produziu muito material; nem tudo merece página numa dissertação de mestrado.

---

## Incluir — quatro itens

### 1. Nível 2 setorial — **a mais importante**

`results/models/sector_level1_vs_level2.csv` · Tabela 5.1.1 nova

Efeitos fixos de CBO4 × seção CNAE e seção CNAE × mês. Está declarado `co_principal_sector` no
contrato congelado e **não aparece em lugar nenhum do texto**.

Controlando por setor, as admissões vão de −0,0538 (p = 0,164) para **−0,0751 (p = 0,036)**; o
salário encolhe de −0,0507 para −0,0356, ou seja, cerca de 30% do diferencial salarial é entre
setores e não entre ocupações dentro do setor.

**Por que incluir:** responde à objeção mais previsível de uma banca — *"isso não é só composição
setorial?"* — e a resposta é forte. Além disso, Klein Teeselink (2025, p. 11) usa exatamente essa
especificação como principal, e Canaries usa firma × tempo, ainda mais saturado. Não ter esse
exercício é lacuna, não escolha.

**Onde:** §5.1, logo depois da Tabela 5.1, e um parágrafo na §4.3.

---

### 2. Horizontes longos

`results/models/long_run_horizon_estimates.csv` · `LONG_RUN_HORIZONS.md`

Quatro horizontes: dez/2022–nov/2023, dez/2023–nov/2024, dez/2024–nov/2025, dez/2025–mai/2026
(parcial).

O salário é **plano**: −0,0514 / −0,0507 / −0,0481 / −0,0548, todos rejeitando a 5%.

**Por que incluir:** é a evidência mais direta de que o diferencial salarial não é ruído de um
período curto. E resolve uma confusão que o leitor terá — a média pós do event study é −0,0154 e o
estático é −0,0507; a diferença é de normalização, não de janela.

**Onde:** §5.1, três frases e uma tabela pequena.

---

### 3. Decomposição de desligamentos

`results/mechanisms/separation_static_results.csv`

Seis famílias que reconciliam exatamente com o agregado.

**Por que incluir:** porque ela **testa a hipótese central do trabalho** e não a confirma. Demissão
sem justa causa dá −0,00002 (BH p = 0,9995); pedido de demissão −0,1166 (BH p = 0,3299).

Incluir um teste que não confirma sua própria hipótese é o tipo de coisa que uma banca respeita, e
que fica muito ruim se ela descobrir que você tinha e não reportou.

**Onde:** §5.1, na discussão da acomodação silenciosa.

---

### 4. Salário-hora e margens de jornada

`results/mechanisms/hourly_wage_results.csv`

Salário-hora real **−0,0695** (BH p = 0,0001), horas semanais +0,0016 não significativo, jornada
parcial e intermitente nulas.

**Por que incluir:** elimina de uma vez a objeção de que o resultado salarial é jornada. O
diferencial por hora é **maior** que o mensal, e as horas não se movem.

**Onde:** §5.1, uma frase dentro da qualificação do salário.

---

## Incluir se sobrar espaço — dois itens

### 5. Sensibilidade da medida de exposição

`results/mechanisms/exposure_sensitivity_results.csv`

Safra 2023 da OIT, consenso GPT-4o/Gemini, índice da Anthropic. O consenso dá salário −0,056 com
BH p = 0,0000468 — o resultado sobrevive a restringir às ocupações onde dois modelos concordam.

**Por que:** a contribuição declarada nº 1 é de mensuração, e este exercício mostra que o achado
não depende de uma escolha de índice. Meia página.

**Onde:** §4.5 ou §5.1.

---

### 6. Forest plot de síntese

`results/figures/figure_5_2_6_group_outcome_forest.png`

**Por que:** a §5.2.6 não tem figura nenhuma, e o leitor sai de cinco subseções com 100 números.
Mostra a paisagem inteira e torna a multiplicidade visível — 130 contrastes, 40 sobreviventes.

**Onde:** §5.2.6.

---

## Não incluir — três itens

### 7. Proxy cumulativo de fluxo líquido

`results/mechanisms/stock_proxy_result.csv` · +1,429 (EP 1,309; p = 0,276)

**Por que não:** não é significativo, e o nome convida ao erro que o texto passou o trabalho todo
evitando — tratar fluxo como estoque. Ele já entra no Painel B.2 da Tabela A.1 com a nota de que
não é estoque. Deixe ali.

### 8. Heterogeneidade por porte do estabelecimento

`results/mechanisms/employer_size_ddd_results.csv` · 50 modelos, **zero rejeições após BH**

**Por que não:** cinquenta modelos e nenhum sobrevivente. Vale uma linha na §4.5 dizendo que foi
testado e não achou nada — o que é informação —, mas não vale tabela.

### 9. Falsificação público versus privado

**Por que não:** não foi executada, e por bom motivo: os campos oficiais codificam forma de
registro, não propriedade. Está declarada como não execução no pacote. Uma frase na §4.5 basta.

---

## Uma adição que não é da V2 mas resolve uma lacuna antiga

A auditoria da V1 registrou (item 14) que a Tabela 2.1 compara quatro índices de exposição **em
conceito e nunca em dado**. O material existe:
`data/processed/anthropic_automation_augmentation_cbo.parquet` e as correlações de posto já
calculadas em `results/mechanisms/exposure_rank_correlations.csv`.

Spearman de −0,1214 para 92 correspondências diretas entre o índice da OIT e o da Anthropic. É um
número desconfortável — os índices concordam pouco — e por isso mesmo vale reportar: mostra que a
escolha do índice importa, o que fortalece a contribuição de mensuração em vez de enfraquecê-la.

**Está fora do escopo desta rodada** (é Seção 2), mas fica registrado para quando você chegar lá.
