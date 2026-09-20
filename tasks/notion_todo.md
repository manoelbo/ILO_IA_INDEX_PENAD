# TODO — Atualizar a dissertação no Notion

Plano: `tasks/notion_plan.md`. Fonte das mudanças: `Final Review/Guia_Reescrita_V2/`.
Alvo: `325cc8ca461082d794db01323b295bb5`.

**Regras:** `update_content` sempre, `replace_content` nunca · Seções 1 a 3 não são tocadas ·
`old_str` sempre extraído do snapshot, nunca digitado de memória · toda âncora conferida como
ocorrência única antes de aplicar.

---

## Fase 0 — Preparação

- [x] **T0.1** Snapshot e extração de âncoras — S

## Fase 1 — Reparos factuais (alto risco primeiro)

- [x] **T1.1** Tabela A.1 — o pretrend do salário deixa de dizer `pass` — S
- [x] **T1.2** Tabela 5.1 e os quatro parágrafos da §5.1 — M

## ✅ Checkpoint A — a mecânica funciona

- [x] As duas substituições aplicaram sem erro
- [x] Seções 1 a 3 intactas: 27 imagens no documento
- [x] **Parar e mostrar ao autor** — aprovado em 28/07

## Fase 2 — Seção 4

- [x] **T2.1** §4.1 — CAGED vs PNADc, TWFE, correção do ADP — M
- [x] **T2.2** §4.2 — painel, três tabelas, limitações da medida — M
- [x] **T2.3** §4.3 — as quatro equações e a Tabela 4.3.1 — M
- [x] **T2.4** §4.4 famílias de multiplicidade e §4.5 nova de robustez — M

## ✅ Checkpoint B — Seção 4 completa

- [x] Subseções consistentes entre si — varredura por comando, 8 de 8
- [ ] **Todas as equações renderizam** — verificação visual PENDENTE: extensão do Chrome não
      conectada, precisa do autor
- [ ] Revisão do autor

## Fase 3 — Seção 5.2

- [x] **T3.1** §5.2.1 Sexo — a assimetria de gênero cai — M
- [x] **T3.2** §5.2.2 Raça/cor — agregado mais forte que os componentes, com explicação — M
- [x] **T3.3** §5.2.3 Idade — a leitura inverte; 22–25 no salário ganha parágrafo — M
- [x] **T3.4** §5.2.4 Escolaridade e §5.2.5 Renda — S
- [x] **T3.5** §5.2.6 Síntese — S

## ✅ Checkpoint C — Seção 5.2 completa

- [x] As cinco subseções e a síntese contam a mesma história
- [x] Nenhuma afirmação de heterogeneidade sem respaldo no BH
- [ ] Revisão do autor

## Fase 4 — Apêndice A

- [x] **T4.1** A.2 e A.3 — nominal e BH lado a lado, seis categorias raciais — M
- [x] **T4.2** A.4, A.5 e A.6 — dois painéis na A.4, suporte na A.6 — M

## Fase 5 — Seção 5.3 e Apêndice B

- [x] **T5.1** §5.3 e Tabela 5.3.1 — base nov/2022, 12 meses terminais — M
- [x] **T5.2** Apêndice B — texto, títulos e links removidos (0 ocorrências de `Apêndice B`).
      **Pendente:** 3 blocos de imagem órfãos, logo antes de REFERÊNCIAS — precisam ser apagados
      à mão no Notion, porque a URL assinada do S3 muda a cada fetch e não serve de âncora. — S

## Fase 6 — Figuras (bloqueada em upload)

- [ ] **T6.1** Destravar o upload das PNGs — S
- [x] **T6.2** Figura 5.2.3.3 gerada em 28/07 — `code/models/canaries_wage_event_study.py` estima e
      `code/render/canaries_wage_figure.py` renderiza. Wald conjunto dos 22 leads p = 0,585 na janela
      congelada, reconciliando com o artefato; 0 leads significativos; pós − pré = −0,0507 contra
      DiD de −0,0517. **Armadilha:** o diagnóstico do grupo roda só sobre `subgroup == 'target'`;
      incluir o complemento dá p = 0,0089 e leva à conclusão oposta.
- [ ] **T6.3** Substituir as 13 e inserir a 5.2.6 e a 5.2.3.3 — M

## ✅ Checkpoint D — varredura final

- [x] **T7.1** Varredura final rodada em 28/07. **Texto: limpo.** Nenhum número da V1 sobreviveu;
      nenhuma remissão órfã; os números-chave batem entre Seção 4, Seção 5 e Apêndice A.
      Quatro "achados" da varredura foram conferidos e são legítimos: `0,0446` é EP na 5.2.2,
      `pass (p=0,932)` está dentro da nota que documenta a correção, e `Painel B.1`/`B.2` só
      existem na A.1, a única tabela que mantém dois painéis.

      **Três pendências de imagem, todas para resolver no Notion:**
      1. A **Figura 5.2.3.3** está com a imagem errada — a colocada tem 1094×630, e a gerada tem
         5383×1821. Recolocar `results/figures/figure_5_2_3_3_canaries_22_25_wage.png`.
      2. Sobraram **duas cópias** de `figure_5_2_2_1_race_admissions.png` e
         `figure_5_2_2_2_race_wage.png` no fim da Seção 3, logo após a Figura 3.10. As corretas já
         estão nos lugares certos, na §5.2.2 — estas duas são para apagar.
      3. Continuam as **3 imagens órfãs** do antigo Apêndice B, depois da Figura 5.3.2
         (4336×1734 cada).

      Depois disso o documento fecha com 26 imagens. A Figura 5.2.6 foi conferida por hash
      perceptual e está correta (100% de correspondência com o forest plot).

---

## Cinco coisas que não podem passar batido

1. **A Tabela A.1 não pode continuar dizendo `pass` no pretrend do salário.** É o reparo mais
   urgente e por isso é a primeira tarefa.
2. **Nenhuma substituição pode atingir as Seções 1 a 3.** Toda âncora é conferida como ocorrência
   única antes de aplicar, e a contagem de imagens é verificada no Checkpoint A.
3. **Equação que passa em busca de string pode estar quebrada na tela.** A verificação da T2.3 é
   visual.
4. **Nunca "todas as tabelas primeiro".** O fatiamento é por subseção, para que o documento não
   fique com tabela nova e parágrafo velho.
5. **As figuras não bloqueiam o texto.** Fases 1 a 5 rodam com as figuras antigas no lugar.

---

## Decisões fechadas em 28/07

| # | Decisão |
|---|---|
| 1 | **Apêndice B sai do texto** — duas remissões na §5.3 e a seção inteira |
| 2 | **Entra a Figura 5.2.3.3**, coorte 22–25 no salário; precisa ser estimada |
| 4 | **Tabela 5.1.1 entra na §5.1**, só o Painel A; o Painel B tem três matrizes não-PSD |
| 6 | **Asteriscos em tabela do Notion precisam ser escapados** (`\*\*`), senão viram negrito |
| 5 | **"Resumo por IA" do Notion** fica como está e é limpo na varredura final |
| 3 | **Separador decimal já resolvido** na T8B.17 — vírgula em tudo, ponto só como milhar |

Contagem de imagens ao longo do trabalho: **27** hoje → **24** após remover o Apêndice B → **26**
ao fim, com a 5.2.6 e a 5.2.3.3.

---

## Referências metodológicas a acrescentar ao `.bib` (achado da Fase 2)

Oito citações metodológicas entraram na Seção 4. Destas, **7 não existem** em
`Citações Dissertação Mestrado.bib` (35 entradas):

| Citação | Onde entrou |
|---|---|
| Goodman-Bacon (2021) | §4.1, parágrafo do TWFE |
| Callaway e Sant'Anna (2021) | §4.1, parágrafo do TWFE |
| Sun e Abraham (2021) | §4.1, parágrafo do TWFE |
| de Chaisemartin e D'Haultfœuille (2020) | §4.1, parágrafo do TWFE |
| Silva e Tenreyro (2006) | §4.3, justificativa do PPML |
| Benjamini e Hochberg (1995) | §4.4, multiplicidade |
| Rambachan e Roth (2023) | §4.5, item 6 |

Já estão no `.bib`: Klein Teeselink (2025), Teutloff *et al.* (2025), Humlum e Vestergaard (2025).
**Chen e Roth (2024) NÃO está** — o `chen` encontrado é Brynjolfsson, Chandar e **Chen**.
São 8 entradas a criar.

---

## Estado em 28/07 — retomada

**Feito e verificado por comando:** T0.1, T1.1, T1.2, T1.3 (Tabela 5.1.1), Checkpoint A,
T2.1–T2.4 (Seção 4 inteira), Checkpoint B, T3.1–T3.5 (Seção 5.2 inteira), Checkpoint C, **T4.1**
(Apêndice A.2 e A.3).

**Próximo:** Fase 6 — figuras (T6.1 upload, T6.2 gerar a 5.2.3.3, T6.3 substituir 13 e inserir 2)
e Fase 7 — varredura final.

**Contagens atuais do documento:** 27 imagens, 26 tabelas (caíram 4: os Painéis B.2 de A.2,
A.4 ×2 e A.6 foram removidos; entrou a 5.1.1).

**Ferramentas de apoio no repo:**
- `tasks/notion_decode.py` — decodifica o envelope do fetch sem corromper LaTeX. Use
  `carregar(caminho)` e `normalizar_imagens(texto)`; NÃO use replaces encadeados.
- `tasks/notion_snapshot.txt` — última safra decodificada, fonte de todas as âncoras.

**Três armadilhas já encontradas, não repetir:**
1. Asterisco em célula de tabela precisa ser escapado (`\*\*\*`), senão o Notion consome como negrito.
2. Ao recortar seção para verificar, use `find(alvo, inicio)` — `find('5.3')` casa antes da seção.
3. Nunca preencher célula sem o valor à vista. Na A.4 o artefato veio truncado por `head -50`
   e eu preenchi 9 células de `MDE 80%`/`N` de memória; foram detectadas e corrigidas contra
   `table_a_4_age.md`. Ler o artefato inteiro antes de transcrever.
4. Âncora do Apêndice A tem escapes (`\<br\>`); transcreva para arquivo e valide contra o
   snapshot com difflib ANTES de enviar.


---

## Fase 6 — receita verificada em 28/07 para trocar as figuras

O autor subiu os 14 PNGs à mão, num bloco `Files Upload` no fim da página. **As URLs do S3
preservam o nome do arquivo**, então dá para identificar cada imagem sem ambiguidade.

**Três fatos descobertos por teste, não por suposição:**

1. `notion-create-attachment` **aceita a URL assinada** de uma imagem já subida no Notion e devolve
   um `file-upload://<id>` **estável**. O HEAD da URL dá 403, mas o GET funciona e isso basta.
2. A URL assinada **casa** em `old_str` (testado com substituição idêntica de um trecho único da
   assinatura). Ela expira em 300 s, então a janela é curta.
3. A âncora barata não é a URL: é a linha `\[file ref: ...\]`, que existe em **13 figuras**, é
   curta e **única em todas**. Trocá-la por `<image src="file-upload://<id>"></image>` insere a
   figura nova exatamente acima da antiga.

**Passo a passo por figura:**

```
1. ntn files create < "Replication Package/V2/results/figures/<arquivo>.png"   -> devolve id
2. update_content: old_str = "\[file ref: <nome antigo>.png\]"
                   new_str = "<image src=\"file-upload://<id>\"></image>"
```

O passo 1 exige `ntn login` (feito uma vez). Sem o login, a alternativa é `notion-create-attachment`
com a URL assinada de cada imagem — funciona, mas custa ~1.700 caracteres por chamada.

**Estado:** Figura 5.1 já trocada (id `3abcc8ca-4610-8149-8d55-00b2bdf91d7a`). Faltam 12 das 13,
mais a inserção da 5.2.6 e da 5.2.3.3.

**O que sobra para o autor apagar à mão no Notion, no fim:**
- as **13 imagens antigas**, cada uma logo abaixo da nova (a nova vem primeiro no par);
- as **3 imagens órfãs** do antigo Apêndice B, logo antes de `REFERÊNCIAS`;
- o bloco `Files Upload` inteiro, no fim da página, depois que todas as 14 forem reanexadas.
