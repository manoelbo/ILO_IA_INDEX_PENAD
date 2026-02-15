# Plano de Implementação — Etapa 1b

**Referência:** `revisao_etapa1b_dissertacao.md`
**Notebook alvo:** `etapa_1b_analise_dados_ilo_pnadc.ipynb`
**Data:** 14 de fevereiro de 2026

---

## Estrutura do Notebook (Referência Rápida)

| Célula | Tipo | Conteúdo |
|--------|------|----------|
| 0 | markdown | Título, contextualização, objetivos |
| 1 | markdown | Header "1. Configuração do ambiente" |
| 2 | code | pip install |
| 3 | code | Imports, constantes, carregamento de dados |
| 4 | markdown | Header "2. Perfil da exposição" |
| 5 | code | Histograma, KDE, gradientes, Gini, Lorenz, comparação internacional |
| 6 | markdown | Header "3. Desigualdade e renda" |
| 7 | code | Quintis, decis, LOWESS, curva de concentração, regressão quantílica |
| 8 | markdown | Header "4. Gênero e raça" |
| 9 | code | Exposição por sexo/raça, KDE, Oaxaca-Blinder |
| 10 | markdown | Header "5. Formalidade" |
| 11 | code | Formal vs informal, paradoxo, interação |
| 12 | markdown | Header "6. Setor e ocupação" |
| 13 | code | ANOVA setores, grupos ocupacionais, cross-tab educação |
| 14 | markdown | Header "7. Região" |
| 15 | code | ANOVA regional, ranking UF |
| 16 | markdown | Header "7b. Região (Mapas)" |
| 17 | code | Mapas coropléticos |
| 18 | markdown | Header "8. Análise multivariada" |
| 19 | code | WLS, Mincer, robustez |
| 20 | markdown | Header "9. Síntese e conclusões" |
| 21 | code | Síntese impressa |

---

# A. EDIÇÃO DE BLOCOS DE MARKDOWN

Alterações em células markdown já existentes no notebook.

---

### A1. Célula 0 — Atualizar contextualização e objetivos

**Ponto da revisão:** #2 (salário mínimo), #4 (comparação internacional), #32 (idade/escolaridade ausente)

**O que fazer:** Adicionar na seção "Contextualização" uma nota de rodapé sobre a fonte do salário mínimo. Na seção "Objetivo da Análise", confirmar que a linha "Idade e instrução" será de fato implementada (ou removê-la se decidir não fazer). Atualizar a referência de comparação internacional para mencionar que será feita com o grupo upper-middle-income do WP140, não com a média global.

**Texto sugerido para adicionar ao final da contextualização:**

```
> **Nota:** O salário mínimo vigente de R$ 1.518 segue o Decreto nº XX.XXX/2025.
> Os dados da PNADc referem-se ao 3º trimestre de 2025 e são combinados ao
> índice de exposição ILO WP140 (versão 2025). Como o índice foi construído
> para a classificação ISCO-08, utilizou-se um crosswalk COD→ISCO-08 que
> introduz potencial erro de medida (ver Limitações, Seção 9).
```

---

### A2. Célula 4 — Adicionar nota sobre ICs e thresholds

**Ponto da revisão:** #3 (ICs colapsados), #5 (thresholds dos gradientes)

**O que fazer:** Adicionar ao markdown da Célula 4 duas notas metodológicas: (1) que os ICs reportados são baseados em SRS reponderada e podem estar subestimados; (2) que os gradientes de exposição seguem exatamente os thresholds do WP140 (ou declarar se foram adaptados).

**Texto sugerido para adicionar:**

```
> **Nota sobre intervalos de confiança:** Os ICs reportados nesta seção
> tratam a amostra como aleatória simples reponderada (SRS com pesos V1028).
> Como a PNADc utiliza desenho amostral complexo (estratificação +
> conglomeração), os ICs reais são mais amplos. Os valores reportados devem
> ser interpretados como limites inferiores da incerteza.

> **Nota sobre gradientes ILO:** Os thresholds de classificação dos gradientes
> de exposição (Not Exposed, Minimal Exposure, Gradients 1-4) seguem
> exatamente a definição do WP140 (Gmyrek et al., 2025, Tabela 1, p. 14),
> baseada nos scores de exposição e nos indicadores SML (Save, Modify, Learn).
```

---

### A3. Célula 6 — Destacar não-monotonicidade Q4 > Q5

**Ponto da revisão:** #6 (Q4 > Q5), #7 (R² individual vs agregado)

**O que fazer:** Expandir o markdown para alertar o leitor sobre dois achados importantes antes de ver a tabela: (1) a relação exposição-renda não é monotônica; (2) a diferença entre R² individual e agregado.

**Texto sugerido para adicionar após a lista de análises:**

```
> **Atenção interpretativa:** A relação entre exposição e renda NÃO é
> monotônica — o quintil Q4 apresenta renda média superior ao Q5.
> Isso ocorre porque o Q5 concentra ocupações administrativas e de saúde
> com alta exposição mas renda relativamente moderada, enquanto o Q4
> inclui gerentes e profissionais liberais de setores menos expostos mas
> com remuneração elevada.
>
> O R² individual da regressão renda~exposição é muito baixo (0.034),
> enquanto o R² agregado por decis é alto (0.653). Essa diferença ilustra
> a falácia ecológica: padrões de grupo não se traduzem automaticamente
> em padrões individuais (Robinson, 1950).
```

---

### A4. Célula 8 — Justificar categorias raciais

**Ponto da revisão:** #12 (agregação Preto+Pardo), #13 (categoria "Outras")

**O que fazer:** Adicionar ao markdown uma justificativa metodológica para a agregação racial utilizada.

**Texto sugerido para adicionar:**

```
> **Nota sobre categorias raciais:** Seguindo convenção estabelecida na
> literatura brasileira de desigualdade (Osorio, 2003; Soares, 2000),
> as categorias Preta e Parda do IBGE foram agregadas em "Negra".
> A categoria "Outras" agrega Amarelos e Indígenas (1.0M de trabalhadores).
> Embora esses grupos tenham realidades socioeconômicas distintas, o
> tamanho amostral reduzido de cada um individualmente limita análises
> desagregadas robustas. Resultados para "Outras" devem ser interpretados
> com cautela.
```

---

### A5. Célula 10 — Corrigir texto sobre interpretação da interação

**Ponto da revisão:** #15 (interpretação invertida)

**O que fazer:** O markdown atual menciona que a investigação do "paradoxo" inclui regressão com interação. Após os resultados do código mostrarem coeficiente negativo, o texto interpretativo precisa refletir isso. Alterar o markdown para alertar sobre a direção do efeito.

**Texto sugerido para substituir/adicionar:**

```
> **Interpretação da interação:** O coeficiente da interação
> exposição×formalidade é **negativo** (-1.21, p<0.001). Isso significa que
> o retorno da exposição sobre a renda é MENOR para trabalhadores formais
> do que para informais. Profissionais liberais informais de alta exposição
> (consultores, advogados autônomos, médicos com CNPJ) capturam mais
> retorno da exposição à IA do que empregados formais equivalentes.
```

---

### A6. Célula 12 — Adicionar nota sobre R² tautológico

**Ponto da revisão:** #17 (R² artefato), #18 (sorting)

**O que fazer:** Adicionar nota explicando que o R² alto da ANOVA por grupo ocupacional é esperado por construção e discutir o mecanismo de sorting.

**Texto sugerido para adicionar:**

```
> **Nota metodológica:** O R² elevado da ANOVA por grupo ocupacional
> (≈0.68) é em grande parte um artefato da construção do índice ILO,
> que atribui scores por ocupação ISCO a 4 dígitos. Como os grandes
> grupos são agrupamentos a 1 dígito dessas ocupações, a alta explicação
> é esperada e não constitui um achado empírico.
>
> A variação de exposição DENTRO dos grupos, observada na cross-tab com
> educação, é mínima — confirmando que o índice é uma propriedade da
> ocupação, não do indivíduo. A correlação exposição-escolaridade no
> nível individual opera via sorting: trabalhadores mais educados acessam
> ocupações de maior exposição.
```

---

### A7. Célula 18 — Expandir nota sobre erros-padrão

**Ponto da revisão:** #21 (HC1 insuficiente), #22 (R² tautológico no M3)

**O que fazer:** A nota metodológica atual menciona WLS + HC1. Expandir para explicitar a limitação e adicionar alerta sobre o R² do M3.

**Texto sugerido para substituir a nota atual:**

```
> **Nota metodológica:** Todas as regressões usam WLS com pesos V1028
> e erros-padrão robustos a heterocedasticidade (HC1, Wooldridge 2020).
> HC1 NÃO corrige para o desenho amostral complexo da PNADc
> (estratificação + conglomeração). Como robustez, recomenda-se comparar
> com erros-padrão clusterizados por UPA.
>
> **Sobre o R² do Modelo M3 (≈0.74):** Como o modelo inclui grande grupo
> ocupacional como controle e o índice de exposição é definido por
> ocupação, o alto poder explicativo é em parte mecânico. A interpretação
> deve focar nos coeficientes das variáveis demográficas (sexo, raça,
> idade) condicionando na ocupação.
```

---

### A8. Célula 20 — Adicionar limitações faltantes à síntese

**Ponto da revisão:** #26 (crosswalk como limitação), #30 (defasagem do índice)

**O que fazer:** Expandir a lista de limitações no markdown da síntese.

**Texto sugerido para adicionar à lista de limitações:**

```
7. Crosswalk COD→ISCO-08 introduz erro de medida; o índice ILO foi
   construído para ISCO-08 e a conversão pode gerar mismatches
   (teste de robustez com matches 4-digit mitiga parcialmente)
8. O índice ILO reflete a capacidade tecnológica de 2024/2025;
   a rápida evolução da IA generativa pode torná-lo defasado
9. Erros-padrão tratam amostra como SRS; valores reais podem ser
   maiores com desenho amostral complexo
```

---

# B. EDIÇÃO DE BLOCOS DE CÓDIGO

Alterações em células de código já existentes no notebook.

---

### B1. Célula 3 — Adicionar cálculo de d de Cohen ponderado

**Ponto da revisão:** #10 (valores t absurdos)

**O que fazer:** Adicionar ao bloco de funções auxiliares (Célula 3) uma função para calcular o d de Cohen ponderado, que será usada em substituição aos t-values nas seções 4 e 5.

**Implementação:**

```python
def weighted_cohen_d(x1, w1, x2, w2):
    """d de Cohen ponderado para dois grupos."""
    m1 = np.average(x1, weights=w1)
    m2 = np.average(x2, weights=w2)
    v1 = np.average((x1 - m1)**2, weights=w1)
    v2 = np.average((x2 - m2)**2, weights=w2)
    n1, n2 = w1.sum(), w2.sum()
    pooled_sd = np.sqrt((n1 * v1 + n2 * v2) / (n1 + n2))
    return (m1 - m2) / pooled_sd if pooled_sd > 0 else 0.0
```

---

### B2. Célula 5 — Atualizar tabela de comparação internacional

**Ponto da revisão:** #4 (comparação com upper-middle-income)

**O que fazer:** Substituir a tabela de comparação atual por uma versão expandida que inclua o grupo de renda correspondente do WP140.

**Implementação:** Localizar o bloco `COMPARACAO COM LITERATURA INTERNACIONAL` e substituir por:

```python
print(f"""
{'Estudo':<32} {'Grupo':<22} {'Media':<12} {'% Alta Exp.':<12}
{'-'*78}
{'Presente (ILO 2025)':<32} {'Brasil':<22} {mean_geral:.3f}{'':>5} {pct_alta:.1f}%
{'Gmyrek et al. (2025)':<32} {'Upper-middle-income':<22} {'~0.29':<12} {'--':<12}
{'Gmyrek et al. (2025)':<32} {'High-income':<22} {'~0.36':<12} {'--':<12}
{'Gmyrek et al. (2025)':<32} {'Global':<22} {'0.30':<12} {'--':<12}
{'Eloundou et al. (2023)':<32} {'EUA':<22} {'--':<12} {'19.0%':<12}

Nota: O Brasil ({mean_geral:.3f}) se posiciona dentro do esperado para
paises de renda media-alta (upper-middle-income ≈ 0.29, WP140 Tabela 4).
""")
```

---

### B3. Célula 5 — Mostrar nomes completos das ocupações no Top 5

**Ponto da revisão:** #5 (nomes por extenso)

**O que fazer:** No loop que imprime o Top 5 ocupações por gradiente, adicionar uma lookup para o nome completo da ocupação (não apenas o grande grupo). Se o dataframe contiver uma coluna com a descrição ISCO ou COD, usá-la. Se não, criar um dicionário de nomes ou carregar de arquivo auxiliar.

**Implementação:** Localizar a linha que imprime `score=...` e adicionar o nome da ocupação. Exemplo:

```python
# Dentro do loop Top 5 por gradiente, substituir:
#   print(f"    {cod} ({gg}): {pop:.2f}M trabalhadores, score={score:.3f}")
# por:
    nome_ocup = df_cod_lookup.get(cod, 'Nome não disponível')  # lookup
    print(f"    {cod} - {nome_ocup} ({gg}): {pop:.2f}M trabalhadores, score={score:.3f}")
```

Se não existir lookup de nomes, criar uma nota: `# TODO: adicionar dicionário COD→nome_ocupação`

---

### B4. Célula 7 — Destacar não-monotonicidade e adicionar nota sobre QuantReg

**Ponto da revisão:** #6 (Q4 > Q5), #8 (QuantReg sem pesos)

**O que fazer:** (1) Após imprimir a razão Q5/Q1, adicionar um print que destaque Q4 > Q5. (2) Antes da regressão quantílica, adicionar nota sobre a ausência de pesos.

**Implementação:**

```python
# Após a razão Q5/Q1, adicionar:
renda_q4 = tab_quintil.loc['Q4', 'Renda Media (R$)']
if renda_q4 > renda_q5:
    print(f"\n  ⚠ ATENCAO: Q4 (R$ {renda_q4:,.0f}) > Q5 (R$ {renda_q5:,.0f})")
    print(f"  A relacao exposicao-renda NAO e monotonica.")
    print(f"  Q4 concentra gerentes e profissionais liberais de alta renda")
    print(f"  em setores de exposicao moderada.")

# Antes da regressão quantílica, adicionar:
print("\n  NOTA: QuantReg do statsmodels nao suporta pesos amostrais")
print("  nativamente. Os coeficientes podem diferir de uma estimacao")
print("  ponderada. Limitacao declarada.")
```

---

### B5. Célula 9 — Substituir t-values por d de Cohen

**Ponto da revisão:** #10 (valores t absurdos)

**O que fazer:** Manter os testes t para informação interna, mas adicionar cálculo e impressão do d de Cohen ponderado, que é a métrica mais informativa para a dissertação.

**Implementação:**

```python
# Após o teste t de gênero, adicionar:
d_sexo = weighted_cohen_d(
    sub_h['exposure_score'].values, sub_h['peso'].values,
    sub_m['exposure_score'].values, sub_m['peso'].values
)
print(f"  d de Cohen (H-M): {d_sexo:.3f} ({'pequeno' if abs(d_sexo)<0.5 else 'medio' if abs(d_sexo)<0.8 else 'grande'})")

# Repetir para raça:
d_raca = weighted_cohen_d(
    sub_br['exposure_score'].values, sub_br['peso'].values,
    sub_ne['exposure_score'].values, sub_ne['peso'].values
)
print(f"  d de Cohen (B-N): {d_raca:.3f} ({'pequeno' if abs(d_raca)<0.5 else 'medio' if abs(d_raca)<0.8 else 'grande'})")
```

---

### B6. Célula 9 — Refinar interpretação Oaxaca-Blinder

**Ponto da revisão:** #11 (componente explicado > 100%)

**O que fazer:** Substituir o texto interpretativo do Oaxaca-Blinder de gênero por uma versão mais precisa.

**Implementação:** Localizar o bloco de interpretação e substituir:

```python
print(f"""
  Interpretacao: {pct_explicado:.0f}% do gap de genero e explicado por
  diferencas em escolaridade, ocupacao, regiao e formalidade.
  O componente explicado > 100% indica que, se mulheres tivessem
  a mesma composicao ocupacional que homens, seu gap de exposicao
  seria AINDA MAIOR. Mulheres estao sub-representadas nas ocupacoes
  de alta exposicao apesar de possuirem caracteristicas (escolaridade)
  que predizem maior exposicao — evidencia de segregacao ocupacional.
""")
```

---

### B7. Célula 11 — Corrigir interpretação da interação exposição×formalidade

**Ponto da revisão:** #15 (interpretação invertida — SEVERIDADE ALTA)

**O que fazer:** O texto interpretativo atual diz "Coeficiente positivo na interação = formais se beneficiam mais da exposição", mas o coeficiente real é NEGATIVO (-1.21). Corrigir a interpretação.

**Implementação:** Localizar o print de interpretação e substituir por:

```python
coef_interacao = model_interacao.params['exposure_score:formal']
direcao = "MENOR" if coef_interacao < 0 else "MAIOR"
beneficiario = "informais" if coef_interacao < 0 else "formais"

print(f"""
  Interpretacao: A interacao exposicao:formal e significativa
  (coef = {coef_interacao:.4f}, p<0.001).
  O retorno da exposicao sobre a renda e {direcao} para trabalhadores
  formais do que para informais.
  Trabalhadores {beneficiario} de alta exposicao capturam mais retorno,
  possivelmente refletindo profissionais liberais autonomos (consultores,
  advogados, medicos com CNPJ) que operam na informalidade mas em
  ocupacoes de alta qualificacao e alta exposicao a IA.
""")
```

---

### B8. Célula 13 — Corrigir setores críticos IA no gráfico

**Ponto da revisão:** #16 (setores não aparecendo em vermelho)

**O que fazer:** Verificar se a constante `SETORES_CRITICOS_IA` existe e se os nomes matcham com os nomes no dataframe. Se não existir, definir. Se existir mas não matchar, corrigir os nomes.

**Implementação:**

```python
# Verificar se SETORES_CRITICOS_IA está definida; se não, definir:
SETORES_CRITICOS_IA = [
    'Finanças e Seguros',
    'Informação e Comunicação',
    'Serviços Profissionais',
]

# No bloco do gráfico, verificar que os nomes matcham:
print("Setores no df:", sorted(df_score['setor_agregado'].unique()))
print("Setores criticos:", SETORES_CRITICOS_IA)
# Verificar interseção:
matched = [s for s in SETORES_CRITICOS_IA if s in df_score['setor_agregado'].unique()]
print(f"Match: {len(matched)}/{len(SETORES_CRITICOS_IA)}")
```

---

### B9. Célula 19 — Adicionar robustez com winsorização

**Ponto da revisão:** #25 (winsorização como robustez adicional)

**O que fazer:** Após o teste de robustez com matches 4-digit, adicionar um segundo teste winzorizando a renda nos percentis 1% e 99%.

**Implementação:**

```python
# Robustez 2: Winsorização da renda
print("\n" + "=" * 70)
print("ROBUSTEZ 2: WINZORIZACAO DA RENDA (P1-P99)")
print("=" * 70)

p1 = df_mincer['rendimento_habitual'].quantile(0.01)
p99 = df_mincer['rendimento_habitual'].quantile(0.99)
df_winsor = df_mincer.copy()
df_winsor['renda_winsor'] = df_winsor['rendimento_habitual'].clip(lower=p1, upper=p99)
df_winsor['log_renda_w'] = np.log(df_winsor['renda_winsor'].clip(lower=1))

mincer_winsor = smf.wls(
    'log_renda_w ~ exposure_score + C(sexo_texto) + C(raca_agregada) + '
    'idade + I(idade**2) + C(nivel_instrucao) + formal + C(regiao) + C(setor_agregado)',
    data=df_winsor, weights=df_winsor['peso']
).fit(cov_type='HC1')

coef_orig = mincer2.params['exposure_score']
coef_winsor = mincer_winsor.params['exposure_score']
print(f"  Coef. exposicao (original):     {coef_orig:+.4f}")
print(f"  Coef. exposicao (winsorizado):  {coef_winsor:+.4f}")
print(f"  Diferenca: {abs(coef_orig - coef_winsor):.4f}")
```

---

### B10. Célula 19 — Adicionar robustez com cluster por UPA

**Ponto da revisão:** #1 (desenho amostral), #21 (HC1 insuficiente)

**O que fazer:** Rodar ao menos o modelo Mincer 2 com erros-padrão clusterizados por UPA (se a variável UPA estiver disponível no dataframe). Se UPA não estiver no dataframe, adicionar comentário indicando que deve ser incorporada na etapa de preparação de dados (etapa 1a).

**Implementação:**

```python
# Robustez 3: Cluster por UPA (se disponível)
if 'upa' in df_mincer.columns or 'UPA' in df_mincer.columns:
    upa_col = 'upa' if 'upa' in df_mincer.columns else 'UPA'
    mincer_cluster = smf.wls(
        'log_renda ~ exposure_score + C(sexo_texto) + C(raca_agregada) + '
        'idade + I(idade**2) + C(nivel_instrucao) + formal + C(regiao) + C(setor_agregado)',
        data=df_mincer, weights=df_mincer['peso']
    ).fit(cov_type='cluster', cov_kwds={'groups': df_mincer[upa_col]})

    print(f"\n  SE (HC1):    {mincer2.bse['exposure_score']:.4f}")
    print(f"  SE (Cluster): {mincer_cluster.bse['exposure_score']:.4f}")
    print(f"  Razao: {mincer_cluster.bse['exposure_score']/mincer2.bse['exposure_score']:.2f}x")
else:
    print("\n  ⚠ Variavel UPA nao encontrada no dataframe.")
    print("  Adicionar na etapa 1a (preparacao de dados) para permitir")
    print("  clusterizacao dos erros-padrao.")
```

---

### B11. Célula 21 — Atualizar síntese com achados corrigidos

**Ponto da revisão:** #6, #15, #26

**O que fazer:** Atualizar a síntese final para refletir: (1) a não-monotonicidade Q4>Q5; (2) a interpretação correta da interação formalidade; (3) as limitações adicionais.

**Implementação:** No print da síntese, alterar:

```python
# Seção 2 (Desigualdade e Renda) — adicionar:
print("   - ATENCAO: relacao nao-monotonica (Q4 > Q5 em renda)")

# Seção 4 (Formalidade) — corrigir:
print('   - Interacao exposicao x formalidade: retorno MENOR para formais')
print('   - Informais de alta exposicao capturam mais retorno (profissionais liberais)')

# Limitações — adicionar itens 7-9 conforme A8
```

---

# C. ADIÇÃO DE BLOCOS DE MARKDOWN E CÓDIGO

Novas células a serem inseridas no notebook.

---

### C1. Nova Seção: "4b. Idade e Escolaridade" (inserir após Célula 9)

**Ponto da revisão:** #32

**Descrição:** Seção descritiva dedicada a idade e nível de instrução, cumprindo o prometido no objetivo. Inserir um bloco markdown + um bloco de código.

**Markdown:**

```markdown
### 4b. Idade e escolaridade
Exposição média por faixa etária e por nível de instrução.

**Análises:**
- Exposição média por faixa etária (5 em 5 anos) com ICs
- Exposição média por nível de instrução com ICs
- KDE sobrepostas por nível de instrução
- Cross-tab: faixa etária × nível de instrução × exposição média
```

**Código:**

```python
# Etapa 1b.4b - Idade e Escolaridade

# ======================================================================
# 4b.1 - Exposição por faixa etária
# ======================================================================
bins_idade = [14, 19, 24, 29, 34, 39, 44, 49, 54, 59, 64, 100]
labels_idade = ['15-19', '20-24', '25-29', '30-34', '35-39',
                '40-44', '45-49', '50-54', '55-59', '60-64', '65+']
df_score['faixa_etaria'] = pd.cut(df_score['idade'], bins=bins_idade, labels=labels_idade)

rows_idade = []
for faixa in labels_idade:
    sub = df_score[df_score['faixa_etaria'] == faixa]
    if len(sub) < 10:
        continue
    mean_e, ci_lo, ci_hi = weighted_ci(sub['exposure_score'], sub['peso'])
    rows_idade.append({
        'Faixa': faixa, 'Exp. Media': mean_e,
        'IC Inf': ci_lo, 'IC Sup': ci_hi,
        'Pop. (milhoes)': sub['peso'].sum() / 1e6,
    })

tab_idade = pd.DataFrame(rows_idade).set_index('Faixa')
display(tab_idade.round(3))

fig, ax = plt.subplots(figsize=(12, 5))
ax.errorbar(range(len(tab_idade)), tab_idade['Exp. Media'],
            yerr=[tab_idade['Exp. Media']-tab_idade['IC Inf'],
                  tab_idade['IC Sup']-tab_idade['Exp. Media']],
            fmt='o-', capsize=4, color='steelblue', linewidth=2)
ax.set_xticks(range(len(tab_idade)))
ax.set_xticklabels(tab_idade.index, rotation=45)
ax.set_ylabel('Exposição Média')
ax.set_xlabel('Faixa Etária')
ax.set_title('Exposição à IA Generativa por Faixa Etária')
plt.tight_layout()
plt.show()

# ======================================================================
# 4b.2 - Exposição por nível de instrução
# ======================================================================
# (análogo ao acima, agrupar por nivel_instrucao ou edu_simples)

# ======================================================================
# 4b.3 - KDE sobrepostas por nível de instrução (#41)
# ======================================================================
fig, ax = plt.subplots(figsize=(10, 5))
edu_order = ['Sem/Fund.Inc.', 'Fund.Comp.', 'Med.Comp.', 'Sup.Comp.']
cores_edu = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']
for edu, cor in zip(edu_order, cores_edu):
    sub = df_score[df_score['edu_simples'] == edu]
    if len(sub) < 100:
        continue
    kde = gaussian_kde(sub['exposure_score'].values,
                       weights=sub['peso'].values / sub['peso'].sum())
    x = np.linspace(0.05, 0.75, 200)
    ax.plot(x, kde(x), color=cor, linewidth=2, label=edu)
ax.set_xlabel('Score de Exposição')
ax.set_ylabel('Densidade')
ax.set_title('Distribuição de Exposição por Nível de Instrução')
ax.legend()
plt.tight_layout()
plt.show()
```

---

### C2. Nova Seção: "5b. Augmentation vs. Automation" (inserir após Célula 11)

**Ponto da revisão:** #31 — a análise mais importante sugerida

**Descrição:** Análise central que dialoga diretamente com o framework do WP140. Comparar sistematicamente os grupos Augmentation (Gradientes 1-2) e High Transformation (Gradientes 3-4).

**Markdown:**

```markdown
### 5b. Augmentation vs. Automação
Comparação entre trabalhadores em gradientes de complementaridade (G1-G2)
e de transformação radical (G3-G4), seguindo a distinção central do WP140.

**Análises:**
- Perfil comparativo: renda, gênero, raça, escolaridade, formalidade, setor
- Gráfico de barras agrupadas lado a lado
- Testes de diferença entre os dois grupos

> **Referência WP140:** "The results suggest that most occupations and
> industries are more likely to be transformed through augmentation rather
> than automation" (Gmyrek et al., 2025, p.1). Esta seção investiga se
> esse padrão se confirma para o Brasil.
```

**Código:**

```python
# Etapa 1b.5b - Augmentation vs. Automação

AUGMENTATION = ['Exposed: Gradient 1', 'Exposed: Gradient 2']
HIGH_TRANSFORM = ['Exposed: Gradient 3', 'Exposed: Gradient 4']

df_score['tipo_exposicao'] = np.where(
    df_score['exposure_gradient'].isin(AUGMENTATION), 'Augmentation (G1-G2)',
    np.where(df_score['exposure_gradient'].isin(HIGH_TRANSFORM), 'Alta Transformação (G3-G4)',
    'Não/Mínima Exposição'))

# Apenas os dois grupos de interesse
df_aug = df_score[df_score['tipo_exposicao'].isin(
    ['Augmentation (G1-G2)', 'Alta Transformação (G3-G4)'])]

rows_tipo = []
for tipo in ['Augmentation (G1-G2)', 'Alta Transformação (G3-G4)']:
    sub = df_aug[df_aug['tipo_exposicao'] == tipo]
    sub_r = sub[sub['tem_renda'] == 1]
    rows_tipo.append({
        'Tipo': tipo,
        'Pop. (milhões)': sub['peso'].sum() / 1e6,
        'Exp. Média': weighted_mean(sub['exposure_score'], sub['peso']),
        'Renda Média': weighted_mean(sub_r['rendimento_habitual'], sub_r['peso']),
        '% Mulheres': weighted_mean((sub['sexo_texto']=='Mulher').astype(int), sub['peso'])*100,
        '% Formal': weighted_mean(sub['formal'], sub['peso'])*100,
        '% Sup. Completo': weighted_mean(
            (sub['edu_simples']=='Sup.Comp.').astype(int), sub['peso'])*100,
    })

tab_tipo = pd.DataFrame(rows_tipo).set_index('Tipo')
display(tab_tipo.round(1))

# Gráfico de barras agrupadas
metricas = ['Renda Média', '% Mulheres', '% Formal', '% Sup. Completo']
fig, axes = plt.subplots(1, len(metricas), figsize=(16, 5))
for ax, met in zip(axes, metricas):
    vals = [tab_tipo.loc[t, met] for t in tab_tipo.index]
    bars = ax.bar(range(len(vals)), vals, color=['steelblue', '#d62728'])
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(['Augment.', 'Alta Transf.'], fontsize=9)
    ax.set_title(met, fontsize=10)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.5,
                f'{v:.1f}', ha='center', fontsize=9)
plt.suptitle('Augmentation vs. Alta Transformação: Perfil Comparativo', fontsize=13)
plt.tight_layout()
plt.show()
```

---

### C3. Novos Gráficos na Seção 3: Heatmap e Bubble Chart (inserir na Célula 7)

**Ponto da revisão:** #33 (heatmap), #34 (bubble chart)

**Descrição:** Dois gráficos adicionais para a seção de desigualdade e renda.

**Código para heatmap (adicionar ao final da Célula 7):**

```python
# ======================================================================
# 3.X - Heatmap bidimensional exposição × renda
# ======================================================================
df_renda['decil_renda'] = pd.qcut(
    df_renda['rendimento_habitual'], 10,
    labels=[f'R{i}' for i in range(1, 11)])

cross = df_renda.groupby(['decil_exposure', 'decil_renda'])['peso'].sum().unstack(fill_value=0)
cross = cross / 1e6  # em milhões

fig, ax = plt.subplots(figsize=(12, 8))
sns.heatmap(cross, cmap='YlOrRd', annot=True, fmt='.1f', ax=ax,
            cbar_kws={'label': 'Trabalhadores (milhões)'})
ax.set_xlabel('Decil de Renda')
ax.set_ylabel('Decil de Exposição')
ax.set_title('Distribuição Conjunta: Exposição à IA × Renda')
plt.tight_layout()
plt.show()
```

**Código para bubble chart (adicionar ao final da Célula 7):**

```python
# ======================================================================
# 3.Y - Scatter plot de ocupações (bubble chart)
# ======================================================================
ocup_agg = df_renda.groupby('cod_ocupacao').apply(lambda g: pd.Series({
    'exp_media': weighted_mean(g['exposure_score'], g['peso']),
    'renda_media': weighted_mean(g['rendimento_habitual'], g['peso']),
    'pop': g['peso'].sum() / 1e6,
    'grande_grupo': g['grande_grupo'].mode().iloc[0] if len(g['grande_grupo'].mode()) > 0 else 'Outros',
})).reset_index()

fig, ax = plt.subplots(figsize=(14, 9))
grupos = ocup_agg['grande_grupo'].unique()
cores_gg = plt.cm.tab10(np.linspace(0, 1, len(grupos)))
for grupo, cor in zip(sorted(grupos), cores_gg):
    sub = ocup_agg[ocup_agg['grande_grupo'] == grupo]
    ax.scatter(sub['exp_media'], sub['renda_media'],
               s=sub['pop']*50, alpha=0.6, color=cor, label=grupo, edgecolor='white')
ax.set_xlabel('Exposição Média')
ax.set_ylabel('Renda Média (R$)')
ax.set_title('Ocupações: Exposição vs. Renda (tamanho = população)')
ax.legend(fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))
plt.tight_layout()
plt.show()
```

---

### C4. Regressão Quantílica Contínua (substituir/expandir na Célula 7)

**Ponto da revisão:** #35

**Descrição:** Expandir a regressão quantílica de 5 pontos para faixa contínua.

**Código:**

```python
# ======================================================================
# 3.Z - Regressão quantílica contínua (tau 0.05 a 0.95)
# ======================================================================
taus = np.arange(0.05, 0.96, 0.05)
coefs_qr = []
for tau in taus:
    mod = smf.quantreg(
        'log_renda ~ exposure_score + C(sexo_texto) + C(raca_agregada) + '
        'idade + I(idade**2) + C(nivel_instrucao) + formal',
        data=df_quant
    ).fit(q=tau, max_iter=1000)
    coefs_qr.append({
        'tau': tau,
        'coef': mod.params['exposure_score'],
        'ci_lo': mod.conf_int().loc['exposure_score', 0],
        'ci_hi': mod.conf_int().loc['exposure_score', 1],
    })
qr_df = pd.DataFrame(coefs_qr)

fig, ax = plt.subplots(figsize=(10, 6))
ax.fill_between(qr_df['tau'], qr_df['ci_lo'], qr_df['ci_hi'],
                alpha=0.2, color='steelblue')
ax.plot(qr_df['tau'], qr_df['coef'], 'o-', color='steelblue', linewidth=2, markersize=4)
ax.axhline(0, color='gray', linestyle='--', linewidth=0.5)
# OLS para referência
coef_ols = mincer2.params['exposure_score']
ax.axhline(coef_ols, color='red', linestyle='--', linewidth=1, label=f'OLS = {coef_ols:.3f}')
ax.set_xlabel('Quantil (τ)')
ax.set_ylabel('Coeficiente de Exposição')
ax.set_title('Regressão Quantílica: Efeito da Exposição ao Longo da Distribuição de Renda')
ax.legend()
plt.tight_layout()
plt.show()
```

---

### C5. Gráfico Sankey: Escolaridade → Ocupação → Gradiente (nova célula após Seção 6)

**Ponto da revisão:** #36

**Descrição:** Diagrama de fluxo mostrando o sorting educação → ocupação → exposição.

**Código:**

```python
# ======================================================================
# 6b - Sankey: Escolaridade → Grupo Ocupacional → Gradiente
# ======================================================================
# Agregar fluxos
flows = df_score.groupby(['edu_simples', 'grande_grupo', 'exposure_gradient'])['peso'].sum().reset_index()
flows = flows[flows['peso'] > 500000]  # filtrar fluxos pequenos

# Usar plotly para Sankey
try:
    import plotly.graph_objects as go

    # Construir nós e links
    edu_cats = sorted(flows['edu_simples'].unique())
    gg_cats = sorted(flows['grande_grupo'].unique())
    grad_cats = [g for g in GRADIENT_ORDER if g in flows['exposure_gradient'].unique()]
    all_nodes = list(edu_cats) + list(gg_cats) + list(grad_cats)

    sources, targets, values = [], [], []
    # Edu → GG
    for _, row in flows.groupby(['edu_simples', 'grande_grupo'])['peso'].sum().reset_index().iterrows():
        sources.append(all_nodes.index(row['edu_simples']))
        targets.append(all_nodes.index(row['grande_grupo']))
        values.append(row['peso'] / 1e6)
    # GG → Gradiente
    for _, row in flows.groupby(['grande_grupo', 'exposure_gradient'])['peso'].sum().reset_index().iterrows():
        sources.append(all_nodes.index(row['grande_grupo']))
        targets.append(all_nodes.index(row['exposure_gradient']))
        values.append(row['peso'] / 1e6)

    fig = go.Figure(go.Sankey(
        node=dict(label=all_nodes, pad=15, thickness=20),
        link=dict(source=sources, target=targets, value=values)))
    fig.update_layout(title='Fluxo: Escolaridade → Ocupação → Gradiente de Exposição',
                      font_size=10, width=1200, height=700)
    fig.show()
except ImportError:
    print("plotly nao instalado. Instalar com: %pip install plotly")
```

---

### C6. Decomposição Shift-Share Regional (nova célula na Seção 7)

**Ponto da revisão:** #37

**Código:**

```python
# ======================================================================
# 7c - Decomposição Shift-Share: Nordeste vs Sudeste
# ======================================================================
def shift_share(df, regiao_a, regiao_b, var_grupo='setor_agregado'):
    """Decompoe diferenca de exposicao entre duas regioes."""
    da = df[df['regiao'] == regiao_a]
    db = df[df['regiao'] == regiao_b]
    total_a, total_b = da['peso'].sum(), db['peso'].sum()

    grupos = set(da[var_grupo].unique()) | set(db[var_grupo].unique())
    composicao = 0
    for g in grupos:
        sa = da[da[var_grupo]==g]
        sb = db[db[var_grupo]==g]
        share_a = sa['peso'].sum() / total_a if total_a > 0 else 0
        share_b = sb['peso'].sum() / total_b if total_b > 0 else 0
        exp_g = weighted_mean(df[df[var_grupo]==g]['exposure_score'],
                              df[df[var_grupo]==g]['peso'])
        composicao += (share_a - share_b) * exp_g

    exp_a = weighted_mean(da['exposure_score'], da['peso'])
    exp_b = weighted_mean(db['exposure_score'], db['peso'])
    total_diff = exp_a - exp_b
    residual = total_diff - composicao

    return total_diff, composicao, residual

for par in [('Sudeste', 'Nordeste'), ('Sudeste', 'Norte'), ('Sul', 'Nordeste')]:
    diff, comp, resid = shift_share(df_score, par[0], par[1])
    print(f"\n{par[0]} vs {par[1]}:")
    print(f"  Diferenca total: {diff:+.4f}")
    print(f"  Efeito composicao (setor): {comp:+.4f} ({comp/diff*100:.1f}%)")
    print(f"  Residual: {resid:+.4f} ({resid/diff*100:.1f}%)")
```

---

### C7. Índice de Vulnerabilidade Composta (nova célula após Seção 7b)

**Ponto da revisão:** #39

**Código:**

```python
# ======================================================================
# 7d - Índice de Vulnerabilidade Composta
# ======================================================================
mediana_renda = weighted_quantile(df_renda['rendimento_habitual'], df_renda['peso'], 0.5)

df_score['vulneravel'] = (
    df_score['exposure_gradient'].isin(HIGH_EXPOSURE_GRADIENTS) &
    df_score['edu_simples'].isin(['Sem/Fund.Inc.', 'Fund.Comp.']) &
    (df_score['formal'] == 0)
).astype(int)

# Se renda disponível, adicionar critério
df_score.loc[df_score['tem_renda']==1, 'vulneravel'] = (
    df_score.loc[df_score['tem_renda']==1, 'vulneravel'] &
    (df_score.loc[df_score['tem_renda']==1, 'rendimento_habitual'] < mediana_renda)
).astype(int)

pop_vuln = df_score[df_score['vulneravel']==1]['peso'].sum() / 1e6
pct_vuln = pop_vuln / (df_score['peso'].sum()/1e6) * 100

print(f"Trabalhadores em vulnerabilidade composta: {pop_vuln:.2f}M ({pct_vuln:.1f}%)")
print("(Alta exposição + Baixa escolaridade + Informalidade + Baixa renda)")

# Mapa por UF
vuln_uf = df_score.groupby('sigla_uf').apply(lambda g: pd.Series({
    'pct_vulneravel': g[g['vulneravel']==1]['peso'].sum() / g['peso'].sum() * 100,
    'vol_vulneravel': g[g['vulneravel']==1]['peso'].sum() / 1e6,
})).reset_index()

# (Plotar mapa usando gdf já carregado na seção 7b)
gdf_vuln = gdf.merge(vuln_uf, left_on='abbrev_state', right_on='sigla_uf')
_plot_map(gdf_vuln, 'pct_vulneravel',
          'Vulnerabilidade Composta à IA por Estado\n(Alta exposição + Baixa escolaridade + Informal + Baixa renda)',
          'Reds', 'abbrev_state', fmt='.1f', pct=True, extra_label='vol_vulneravel')
```

---

### C8. Tabela Comparativa Brasil vs. WP140 (nova célula na Seção 2)

**Ponto da revisão:** #40

**Código:**

```python
# ======================================================================
# 2.X - Tabela Comparativa Brasil vs. WP140
# ======================================================================
print("=" * 90)
print("COMPARACAO ESTRUTURADA: BRASIL vs. WP140 (por grupo de renda)")
print("=" * 90)

comparacao = pd.DataFrame({
    'Indicador': [
        'Exposição média',
        '% Não Exposto',
        '% Alta Exposição (G3-G4)',
        'Setor mais exposto',
        'Ocupação mais exposta',
        'Gap gênero (M-H)',
    ],
    'Brasil (este estudo)': [
        f'{mean_geral:.3f}',
        f'{pct_nao_exposto:.1f}%',
        f'{pct_alta:.1f}%',
        'Finanças e Seguros',
        'Apoio administrativo',
        f'+{gap_sexo:.3f}',
    ],
    'Upper-Middle (WP140)': [
        '~0.29', '~52%', '~11%',
        'Financial services', 'Clerical support',
        'Mulheres > Homens',
    ],
    'High-Income (WP140)': [
        '~0.36', '~35%', '~20%',
        'Financial services', 'Clerical support',
        'Mulheres > Homens',
    ],
    'Global (WP140)': [
        '0.30', '~50%', '~12%',
        'Financial services', 'Clerical support',
        'Mulheres > Homens',
    ],
})
display(comparacao.set_index('Indicador'))
```

---

# D. ADIÇÃO DE NOTAS BIBLIOGRÁFICAS

Notas de conexão entre os dados do notebook e o WP140 (e outras referências), para serem inseridas como blocos markdown ou comentários em código.

---

### D1. Célula 0 — Nota sobre o framework de task-based approach

**Inserir no markdown introdutório:**

```
> **Conexão com WP140:** O índice de exposição da OIT segue a abordagem
> task-based (Autor, 2015; Acemoglu & Restrepo, 2019), onde cada ocupação
> é decomposta em tarefas e cada tarefa é avaliada quanto à capacidade de
> modelos de IA generativa de realizá-la. O WP140 estende trabalhos
> anteriores (Felten et al., 2021; Eloundou et al., 2023) ao incorporar
> validação humana e distinguir entre potencial de automação e de
> complementaridade (augmentation).
```

---

### D2. Célula 4 — Nota conectando gradientes com WP140

**Inserir no markdown:**

```
> **Sobre os gradientes (WP140, Seção 2.3):** Os gradientes de exposição
> refletem não apenas o nível de exposição mas o TIPO de impacto esperado.
> Gradientes 1-2 indicam que a IA é mais propensa a complementar o
> trabalho humano (augmentation), enquanto Gradientes 3-4 indicam maior
> potencial de transformação das tarefas ou substituição. Essa distinção
> é fundamental para políticas públicas: o mesmo nível de exposição pode
> representar oportunidade (augmentation) ou risco (automação), dependendo
> do contexto ocupacional. Referência: WP140, Figura 2 (p. 14) e
> Tabela 1 (p. 13).
```

---

### D3. Célula 6 — Nota conectando renda com WP140

**Inserir no markdown:**

```
> **Conexão com WP140:** O WP140 encontra que, globalmente, ocupações de
> maior exposição tendem a ser de maior renda (Tabela 2, p. 20), o que é
> consistente com a hipótese de complementaridade. Para países de renda
> média-alta como o Brasil, esse padrão é esperado mas menos pronunciado
> do que em países de alta renda, onde o setor de serviços profissionais
> é proporcionalmente maior. A razão Q5/Q1 de 2.23x encontrada aqui está
> alinhada com essa expectativa.
```

---

### D4. Célula 8 — Nota sobre gênero no WP140

**Inserir no markdown:**

```
> **Conexão com WP140 (gênero):** O WP140 (Seção 3.2, p. 24-26) encontra
> que mulheres estão sistematicamente mais expostas à IA generativa em
> todas as regiões do mundo, principalmente pela concentração feminina
> em trabalho clerical (ISCO Major Group 4). No Brasil, confirmamos esse
> padrão (gap de +0.044). O WP140 destaca que esse resultado pode ter
> implicações distributivas ambíguas: se a IA complementa o trabalho
> clerical, mulheres se beneficiam; se automatiza, mulheres são mais
> vulneráveis. A decomposição Oaxaca-Blinder que realizamos aprofunda
> essa análise para além do que o WP140 oferece.
>
> **Contribuição original (raça):** A análise por raça não é contemplada
> no WP140, que trabalha com dados globais sem essa desagregação. O gap
> racial de exposição (+0.048 para brancos) é uma contribuição específica
> desta dissertação ao debate sobre IA e desigualdade no Brasil.
```

---

### D5. Célula 10 — Nota sobre formalidade como contribuição original

**Inserir no markdown:**

```
> **Contribuição original (formalidade):** A distinção formal/informal
> não aparece no WP140 (irrelevante em países de alta renda onde a
> informalidade é marginal). No Brasil, onde ~57% da força de trabalho
> é informal, essa dimensão é central. A OIT tem interesse particular
> na questão (ILO, 2018 — Women and Men in the Informal Economy) e
> esta análise conecta dois temas prioritários da agenda OIT:
> IA generativa e informalidade.
```

---

### D6. Célula 12 — Nota sobre hierarquia ocupacional

**Inserir no markdown:**

```
> **Conexão com WP140 (Tabela 2):** O ranking ocupacional brasileiro replica
> a hierarquia global do WP140: Clerical Support Workers (Apoio
> Administrativo) é o grupo mais exposto, seguido de Professionals e
> Managers. Elementary Occupations está na base. A única diferença
> notável é que no Brasil, "Serviços e Vendedores" tem exposição
> relativamente alta (0.305 vs ~0.25 global), possivelmente pela
> estrutura do comércio brasileiro que incorpora mais tarefas
> administrativas/digitais nas funções de venda.
```

---

### D7. Célula 14 — Nota sobre dimensão geográfica

**Inserir no markdown:**

```
> **Conexão com WP140 (dimensão geográfica):** O WP140 analisa variação
> entre países (Figura 6, p. 22-23) e encontra que países de maior
> renda per capita têm maior exposição, refletindo sua estrutura
> produtiva mais intensiva em serviços. Replicamos esse padrão DENTRO
> do Brasil: regiões de maior PIB per capita (Sudeste, Sul,
> Centro-Oeste) apresentam maior exposição. O DF (0.326) supera
> inclusive a média de high-income countries (~0.36 no WP140), refletindo
> a concentração de serviços públicos e profissionais qualificados.
```

---

### D8. Célula 18 — Nota sobre extensão metodológica

**Inserir no markdown:**

```
> **Extensão do WP140:** O WP140 trabalha exclusivamente com dados
> agregados por ocupação e não realiza análise no nível individual.
> A equação de Mincer aumentada com o score de exposição como regressor
> é uma extensão metodológica que permite: (1) controlar por
> características individuais (sexo, raça, idade, escolaridade); (2)
> estimar o "prêmio" de exposição na renda condicionando na composição
> da força de trabalho; (3) testar interações (exposição×formalidade,
> exposição×gênero). Essa abordagem segue a sugestão implícita do WP140
> de que pesquisas futuras devem "explore the relationship between
> exposure and labour market outcomes at the individual level" (p. 39).
```

---

### D9. Célula 20 — Nota de síntese sobre posicionamento do Brasil

**Inserir no markdown da síntese:**

```
> **Posicionamento do Brasil no contexto global (WP140):**
> O Brasil se posiciona como caso típico de país de renda média-alta:
> exposição média (0.278) ligeiramente inferior à média global (0.30)
> e consistente com o grupo upper-middle-income (~0.29). A proporção de
> trabalhadores em alta exposição (10.1%) está abaixo de países de alta
> renda (~20%) mas acima de países de baixa renda (~5%). As extensões
> originais desta dissertação — raça, formalidade, análise regional e
> equação de Mincer — preenchem lacunas deixadas pelo WP140 para o
> contexto de países em desenvolvimento.
```

---

# CHECKLIST DE IMPLEMENTAÇÃO

## A. Edições em Blocos de Markdown

- [ ] **A1.** Célula 0 — Atualizar contextualização (salário mínimo, crosswalk, comparação upper-middle-income)
- [ ] **A2.** Célula 4 — Adicionar nota sobre ICs subestimados e thresholds dos gradientes
- [ ] **A3.** Célula 6 — Destacar não-monotonicidade Q4>Q5 e falácia ecológica
- [ ] **A4.** Célula 8 — Justificar agregação racial (Osorio 2003, Soares 2000)
- [ ] **A5.** Célula 10 — Corrigir texto sobre direção da interação exposição×formalidade
- [ ] **A6.** Célula 12 — Nota sobre R² tautológico e mecanismo de sorting
- [ ] **A7.** Célula 18 — Expandir nota metodológica (HC1 insuficiente, R² do M3)
- [ ] **A8.** Célula 20 — Adicionar limitações 7-9 (crosswalk, defasagem, SEs)

## B. Edições em Blocos de Código

- [ ] **B1.** Célula 3 — Adicionar função `weighted_cohen_d`
- [ ] **B2.** Célula 5 — Atualizar tabela de comparação internacional (upper-middle-income)
- [ ] **B3.** Célula 5 — Mostrar nomes completos das ocupações no Top 5
- [ ] **B4.** Célula 7 — Destacar Q4>Q5 e adicionar nota QuantReg sem pesos
- [ ] **B5.** Célula 9 — Adicionar d de Cohen ponderado para gênero e raça
- [ ] **B6.** Célula 9 — Refinar interpretação Oaxaca-Blinder (explicado > 100%)
- [ ] **B7.** Célula 11 — **URGENTE** Corrigir interpretação da interação (coef. negativo)
- [ ] **B8.** Célula 13 — Corrigir match de `SETORES_CRITICOS_IA` no gráfico
- [ ] **B9.** Célula 19 — Adicionar robustez com winsorização P1-P99
- [ ] **B10.** Célula 19 — Adicionar robustez com cluster por UPA
- [ ] **B11.** Célula 21 — Atualizar síntese com achados corrigidos

## C. Adição de Blocos de Markdown e Código

- [ ] **C1.** Nova seção 4b: Idade e Escolaridade (markdown + código)
- [ ] **C2.** Nova seção 5b: Augmentation vs. Automação (markdown + código)
- [ ] **C3.** Heatmap exposição×renda e Bubble chart de ocupações (código na seção 3)
- [ ] **C4.** Regressão quantílica contínua tau 0.05–0.95 (código na seção 3)
- [ ] **C5.** Gráfico Sankey: Escolaridade → Ocupação → Gradiente (após seção 6)
- [ ] **C6.** Decomposição Shift-Share regional (nova célula na seção 7)
- [ ] **C7.** Índice de Vulnerabilidade Composta + mapa (após seção 7b)
- [ ] **C8.** Tabela comparativa estruturada Brasil vs. WP140 (na seção 2)

## D. Adição de Notas Bibliográficas

- [ ] **D1.** Célula 0 — Nota sobre task-based approach (Autor 2015, Acemoglu & Restrepo 2019)
- [ ] **D2.** Célula 4 — Nota conectando gradientes com WP140 Seção 2.3 e Figura 2
- [ ] **D3.** Célula 6 — Nota conectando renda com WP140 Tabela 2
- [ ] **D4.** Célula 8 — Nota sobre gênero no WP140 Seção 3.2 + contribuição original (raça)
- [ ] **D5.** Célula 10 — Nota sobre formalidade como contribuição original (agenda OIT)
- [ ] **D6.** Célula 12 — Nota sobre hierarquia ocupacional (WP140 Tabela 2)
- [ ] **D7.** Célula 14 — Nota sobre dimensão geográfica (WP140 Figura 6)
- [ ] **D8.** Célula 18 — Nota sobre extensão metodológica (análise individual)
- [ ] **D9.** Célula 20 — Nota de síntese sobre posicionamento do Brasil no WP140

---

**Total de ações: 8 (A) + 11 (B) + 8 (C) + 9 (D) = 36 ações**

**Prioridade de execução sugerida:**
1. B7 (corrigir interpretação invertida — urgente)
2. B1 + B5 (adicionar d de Cohen para substituir t-values)
3. C2 (Augmentation vs. Automação — maior valor analítico)
4. C1 (Idade e Escolaridade — prometida mas ausente)
5. Notas D1–D9 (conectam com WP140 — rápidas de adicionar)
6. Restante por ordem de seção
