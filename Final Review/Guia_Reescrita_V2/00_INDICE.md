# Guia de reescrita das Seções 4 e 5

**Fase 10.** Data: 28 de julho de 2026.
**Escopo:** Seções 4, 5, Apêndice A e Apêndice B. Resumo e introdução ficam para rodada separada.
**Este guia não altera o texto.** Ele lista o que mudar, com o número novo e a fonte.

---

## Por onde começar

Se você só tiver uma tarde, faça nesta ordem:

1. **`01_TABELAS.md` → a Tabela A.1.** Ela certifica hoje o pretrend do salário como
   `pass (p=0,932)`. Na V2 é `fail (p=1,6e-04)`. É a célula que sustenta o único resultado
   significativo do trabalho e ela afirma o oposto dos dados. É o reparo mais urgente.
2. **`03_METODOLOGIA_E_REFERENCIAS.md` → Bloco 1.** Quatro referências e um parágrafo resolvem a
   lacuna mais visível: o silêncio sobre por que o TWFE é válido aqui.
3. **`05_SECAO_5.md` → a qualificação do salário.** Um quarto do diferencial é composição
   educacional. Escrever isso antes que perguntem fortalece o resultado.

---

## Os oito eixos

| Arquivo | O que traz |
|---|---|
| `01_TABELAS.md` | 18 tabelas, com caminho do artefato e o número que muda |
| `02_FIGURAS.md` | 14 figuras, com caminho; três do Apêndice B adiadas |
| `03_METODOLOGIA_E_REFERENCIAS.md` | grade dos artigos empíricos lidos, as cinco frases citáveis, e as ~15 referências metodológicas a baixar |
| `04_SECAO_4.md` | mudanças na Seção 4, com equações prontas em LaTeX |
| `05_SECAO_5.md` | números e interpretações que mudam, subseção por subseção |
| `06_LITERATURA_POR_SUBSECAO.md` | conexões com a literatura, revistas contra os números novos |
| `07_ROBUSTEZ.md` | o que entra na §4.5 e o que entra na §5 |
| `08_ADICOES_V2.md` | o que a V2 tem e o texto não usa, com recomendação de incluir ou não |

---

## Os quatro fatos que definem o tamanho do trabalho

| Fato | Onde |
|---|---|
| `library.bib` tem 36 entradas e **zero referências metodológicas** | `references/library.bib` |
| Três dos oito artigos empíricos são citados **zero vezes**, incluindo o único brasileiro | contagem no `.md` |
| Os **quatro** números da Tabela 4.2.1 mudam | `painel_nacional_support.json` |
| A equação da §4.3 traz `X'γ` no modelo principal, e é linear | linha 383 do `.md` |

---

## O que muda de conclusão, não só de número

Cinco itens. São os que exigem reescrever argumento, não trocar dígito.

1. **A assimetria de gênero nas admissões não sobrevive.** DDD vai de +0,0446 (p = 0,018) para
   +0,0116 (BH p = 0,907).
2. **A leitura de idade inverte.** Não é que os jovens sejam atingidos — é que os de 41 a 49 são
   poupados. O DDD de 22–25 é −0,019, não significativo.
3. **O salário exige qualificação.** Entre 23% e 29% do diferencial é composição educacional; o
   componente de preço fica em −3,6% a −3,9%.
4. **A acomodação silenciosa perde apoio.** A decomposição de desligamentos não a confirma:
   demissão sem justa causa dá −0,00002 com BH p = 0,9995.
5. **A falha de tendências paralelas ganha explicação.** O controle é 68% mais volátil e 64% mais
   sazonal que o tratado. Isso converte uma admissão defensiva em argumento com número.

---

## Estado das rodadas

| Rodada | Situação |
|---|---|
| 0 — mapa de fontes | incorporada aos demais documentos |
| 1 — leitura dos artigos | completa: os oito lidos, com página em toda afirmação |
| 2 — tabelas e figuras | completa, caminhos conferidos por comando |
| 3 — Seção 4 | completa, equações conferidas contra o código |
| 4 — Seção 5 | completa |
| 5 — adições | completa |
| 6 — varreduras | duas de três fecham; ver abaixo |

### O que a leitura completa dos oito rendeu

Quatro achados que não existiam na primeira passada:

1. **O placebo temporal da V2 tem precedente idêntico** em Teutloff et al. (2025, p. 12) — descartar
   o período pós e datar um evento falso dentro do pré verdadeiro.
2. **Teutloff reconhece o problema de multiplicidade e declina de corrigi-lo**, recomendando olhar
   as caudas. A V2 aplica Benjamini-Hochberg sobre famílias declaradas. É um ponto onde o seu
   trabalho é mais rigoroso que o publicado.
3. **Hosseini Maasoum tem adoção escalonada** (2023–2025), que é o caso em que Goodman-Bacon
   importa. O seu não é — o que reforça o argumento do §4.1. E o arcabouço teórico deles fornece o
   mecanismo que falta à sua §5.2.3.
4. **Aldasoro não usa DiD**: é variável instrumental sobre survey anual. O texto o cita hoje ao lado
   de estudos de DiD como se fosse evidência do mesmo tipo.

### Resultado das varreduras

- **Varredura 1 — todo artefato colocado:** 32 de 32 aparecem no guia. ✅
- **Varredura 2 — itens da auditoria da V1:** os itens de Seções 4 e 5 têm destino. Os itens 1, 2,
  16, 17 e 18 são de outras seções ou de renderização e ficam fora do escopo desta rodada.
- **Varredura 3 — achados Nível 2 da Fase 9:** os seis aparecem. Três foram acrescentados depois da
  primeira varredura, que os havia pegado em falta: a não monotonicidade do score e as 193 sem
  score entraram na §4.2; a volatilidade do controle entrou na §5.1.

---

## Regras que valeram para produzir este guia

- Nenhuma afirmação sem número e sem fonte verificável.
- Toda equação conferida contra a fórmula que o código executa, não contra o que o texto diz.
- Toda afirmação sobre um artigo de referência com página do PDF.
- Nenhuma alteração no texto da dissertação nem no `Replication Package/`.
