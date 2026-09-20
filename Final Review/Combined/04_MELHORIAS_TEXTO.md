# 04 — Melhorias no Texto (combinadas)

**Decisão editorial.** Manter a estrutura atual. Revisar afirmações, tabelas, referências e
renderização no lugar. Não acrescentar capítulo de revisão de literatura, novas dimensões de
heterogeneidade, nem nova arquitetura conceitual.

A única adição estrutural é a **Conclusão**, que hoje não existe — completar um esqueleto incompleto
não é reordenar capítulos.

Origem: **[X]** Codex, **[C]** Claude, **[X+C]** ambos.

---

## P0 — Corrigir antes de enviar para a professora

| # | Mudança | Origem | Impacto | Esforço |
|---|---|---|---|---|
| P0.1 | Corrigir o resumo: 10,1% de todos os ocupados e 14,8% dos formais | [X] | Remove erro factual de manchete | **Muito baixo** |
| P0.2 | Reconciliar a A.6 com uma fonte computacional que produza linhas de renda | [X] | Repara a quebra crítica texto↔pacote | Baixo no texto, médio no código |
| P0.3 | Completar a A.5 com `asinh(saldo)` e as linhas do Painel B.2 | [X] | Restaura diagnósticos prometidos | Baixo |
| P0.4 | Reportar ou retirar as promessas de robustez não cumpridas | [X] | Evita afirmação de método sem suporte | Baixo |
| P0.5 | Substituir os links quebrados do Apêndice B por caminhos empacotados | [X+C] | Torna a evidência alcançável | Baixo |
| P0.6 | Regerar a lista completa de referências a partir do `.bib` corrigido | [X] | Restaura completude de citação | Baixo |
| P0.7 | Reconstruir e inspecionar o PDF: nenhuma coluna cortada, nenhum markup impresso | [X] | Torna os diagnósticos legíveis | Médio |
| P0.8 | **Escrever a Seção 6 — Conclusão** | [C] | Fecha a lacuna estrutural mais visível | Médio |
| P0.9 | Corrigir a explicação do Gradiente 4 vazio na §4.2 | [C] | A explicação atual está factualmente incompleta | Baixo |

### P0.1 — o erro dos 10%

A linha 5 diz "cerca de 10% da força de trabalho **formal**". O correto, pelos próprios números do
trabalho: **10,1% da população ocupada total; 14,8% dos formais; 6,7% dos informais.** Corrigir
inclusive fortalece o argumento, porque a concentração no mercado formal é o que justifica a escolha
do CAGED.

### P0.8 — o roteiro da Conclusão

Três a quatro páginas, sem tabela nem figura nova.

**6.1 Retomada das perguntas.** A Introdução faz duas perguntas explícitas. Responda as duas em
texto corrido, na mesma ordem. A resposta à primeira é forte e pode ser afirmada. A segunda é
qualificada — você já tem a formulação certa espalhada na §5.2.6.

**6.2 As três contribuições, revisitadas.** Mensuração, distribuição, evidência empírica. O que cada
uma entregou e o que ficou aquém. Se a V2 acontecer, o crosswalk revisto entra aqui e passa a ser a
contribuição mais concreta.

**6.3 Limitações consolidadas.** Recolher as ressalvas hoje espalhadas por §2.5, §3.1, §4.1, §5.1,
§5.2.6, §5.3 e pela abertura do Apêndice A, e organizá-las em três blocos: limitação de dado
(cobertura, crosswalk, ausência de estoque e de informal), de desenho (exposição não é adoção,
tendências paralelas, multiplicidade) e de escopo (curto prazo, só mercado formal). **A mudança de
forma é o ganho:** hoje o leitor encontra uma ressalva a cada duas páginas e nunca vê o inventário —
lê como insegurança. Reunido com taxonomia, lê como domínio do objeto.

**6.4 Agenda.** O que a Etapa 3 (conectividade) tentou e por que não se sustentou; o desenho com
dados de firma no ambiente seguro da FGV; a pergunta de estoque via RAIS ou PNADc.

**6.5 Implicações.** Curto, sem prescrever política que a evidência não sustenta. O achado
distributivo da Seção 3 sustenta uma observação sobre quem monitorar; o achado empírico não sustenta
recomendação.

### P0.9 — a §4.2

Substituir o parágrafo que começa em *"Um ponto importante dessa classificação..."*. A versão
correta precisa dizer:

- A ponte alcança **11 das 13** ocupações ISCO-08 que a OIT classifica como Gradiente 4, e **16
  CBOs** tocam pelo menos uma delas.
- Ainda assim nenhuma é classificada como G4, e a razão principal é a **assimetria da regra**: G4
  exige `média − desvio ≥ 0,50` enquanto G1–G3 exigem `média + desvio ≥ 0,50`, de modo que uma
  dispersão maior dificulta o topo e facilita a base.
- A dispersão usada agrega variação entre tarefas e variação entre destinos ISCO, o que a infla para
  CBOs com múltiplos destinos (0,079 com um destino contra 0,114 com vários).
- A diluição da média contribui, mas não decide: **207 das 436 CBOs mapeiam para um único destino**,
  e a mediana é 2.

Um exemplo vale mais que a explicação abstrata: a CBO 4121 (operadores de entrada de dados)
corresponde à ISCO 4132 (Data Entry Clerks), a ocupação mais exposta de todo o índice com score
0,70, e sai como Gradiente 3 — falha o corte de média por 0,007.

Se a V2 revisar a regra (`03` §P0.8), este parágrafo vira uma nota metodológica curta mais uma linha
no apêndice de sensibilidade.

---

## P1 — Apertar a interpretação sem mudar a estrutura

### Uma conclusão de alto nível consistente **[X]**

Use a mesma formulação no resumo, na introdução e na conclusão:

> As estimativas não mostram efeito causal nacional robusto sobre os fluxos de trabalho formal ou
> sobre os salários de entrada. Alguns contrastes de subgrupo são compatíveis com mudanças
> localizadas pós-ChatGPT, mas vários diagnósticos de pretrend e de suporte exigem interpretação
> exploratória. O desenho mede exposição ocupacional pré-determinada, não adoção observada de IA, e
> não observa o estoque de emprego.

Substituições específicas:

| Trocar | Por |
|---|---|
| "e não destruição de vínculos" | "compatível com menor rotatividade, mas não identifica a mudança no estoque de emprego" |
| "transformação em curso" | "ocupações com maior potencial de exposição técnica" |
| "os efeitos devem aparecer primeiro" | "a análise examina se as mudanças diferenciais se concentram em" |
| "mecanismos" (casos ocupacionais) | "trajetórias descritivas" ou "caminhos ilustrativos" |
| "efeito" solto | "estimativa", "mudança diferencial" ou "padrão" — reserve "efeito" para frases que enunciem imediatamente as hipóteses de identificação |

### Quatro denominadores, definidos uma vez **[X+C]**

1. **629** códigos CBO4 no universo de classificação;
2. **436** CBO4 oficialmente casadas no painel classificado;
3. **341** CBO4 na amostra estrita tratado-versus-controle;
4. **18.307** observações CBO-mês retidas pelos modelos centrais.

Não rotular as 629 como CBOs observadas do painel analítico. E dizer em prosa que 46% do universo de
classificação fica fora do modelo principal, com a justificativa que já existe no texto — é melhor
dizer você mesmo do que deixar a banca deduzir.

### Justificativa do estimador **[X+C]**

Remover "muitos zeros" como razão central para `log(1+y)` — são **31 de 18.307 células de admissão
(0,169%)** e 17 de desligamento (0,093%) na amostra estrita. Descrevê-lo como transformação
secundária interpretável e introduzir PPML como estimador de contagem preferido na V2.

### Linguagem de heterogeneidade **[X]**

- O DDD de admissões femininas é o contraste demográfico mais limpo — não prova de que a adoção de
  IA prejudicou mulheres.
- Raça/cor: diferencial de fluxo de desligamento, não mecanismo de estoque ou de rotatividade.
- Declarar que **idade não é tempo de casa nem experiência específica da firma**.
- Enfatizar o resultado de desligamento em escolaridade mais que o de admissão, ao discutir robustez.
- Manter o resultado de renda alta fora da conclusão substantiva — suporte fino (3/7 CBOs).
- **[X]** Corrigir uma cautela excessiva: a síntese diz que a evidência de saldo líquido não é
  robusta, mas o Apêndice A.2 contém **dois contrastes normalizados de saldo significativos com
  pretrends de DDD aprovados**. Continuam secundários, mas a afirmação absoluta é forte demais.

### Literatura metodológica de DiD **[C]**

Zero citações hoje, num trabalho cujo resultado central é que as tendências paralelas são rejeitadas.

| Onde | Citar | Para dizer o quê |
|---|---|---|
| §4.1, ao apresentar o desenho | Goodman-Bacon (2021); Callaway e Sant'Anna (2021); Sun e Abraham (2021); de Chaisemartin e D'Haultfœuille (2020) | **Que não se aplicam aqui.** Data de tratamento única e comum → sem adoção escalonada, sem ponderação negativa, TWFE é o estimador correto. É uma força hoje invisível. Um parágrafo. |
| §4.3, ao introduzir o event study | Roth (2022) | Condicionar a interpretação no resultado de um pré-teste distorce a inferência — que é o procedimento atual. Assumir isso é mais forte que ser pego. |
| §4.3 e §5.1 | Rambachan e Roth (2023) | A alternativa construtiva: limites do efeito sob restrição de suavidade da violação. |
| §4.3, estimador de contagem | Silva e Tenreyro (2006); Correia, Guimarães e Zylkin (2020) | Justificar PPML. |
| §4.4, heterogeneidade | Romano e Wolf (2005) ou Benjamini e Hochberg (1995) | Justificar a correção por multiplicidade. |
| §4.3, inferência | Cameron e Miller (2015) | Clusterização e graus de liberdade. |

### Literatura de automação e literatura brasileira **[C]**

- **Automação anterior à IA generativa**, na §2.2 ou §2.3: Acemoglu e Restrepo, Autor e Dorn, Frey e
  Osborne, Webb, Felten–Raj–Seamans. Várias já estão no seu `.bib` e não chegaram ao texto. Ancora o
  trabalho numa tradição.
- **Literatura brasileira**, na Introdução e na §3: o trabalho se justifica pela lacuna de país de
  renda média, então precisa mostrar que conhece o que já se fez no Brasil sobre automação e uso de
  CAGED/RAIS.

---

## P1 — Reparos de apêndice e artefato **[X]**

- Rótulos explícitos B.1 e B.2 na A.5 e na A.6.
- Rótulos e notas em português de forma consistente — a nota geral da A.6 está em inglês.
- Substituir `<br>` dentro de células por formato seguro para o renderizador, por exemplo
  coeficiente e erro-padrão na mesma linha.
- Usar `< 0,001` literal só se o renderizador escapar corretamente; caso contrário `p < 0,001` como
  texto simples.
- Garantir que toda tabela de apêndice caiba em paisagem ou use fonte menor **sem perder colunas** —
  hoje o PDF corta a coluna de suporte, que é o diagnóstico usado para qualificar heterogeneidade.
- Acrescentar uma tabela compacta que dispõe das especificações de robustez: controle ampliado, sem
  controles, controles pré-determinados e Poisson.
- Ligar toda tabela e figura a um CSV de backing empacotado e a um produtor, não a uma URL interna
  de aplicativo.
- Nivelar a hierarquia: B.1–B.3 estão em H2 e deveriam estar em H3.
- "Este anexo reúne" → "Este apêndice reúne". Figura B.3 sem `[file ref: ...]`.

---

## P2 — Limpeza de consistência interna **[X]**

- Corrigir a aritmética e o rótulo do `55+` na linha 277: `0,304 − 0,252 = 0,052`, ≈ **20,6%**, não
  0,056 e 22%.
- Corrigir a frase de volume setorial: **Comércio é o primeiro, com 1,36 milhão**, não Serviços
  Profissionais e Administração Pública.
- Substituir "Anexo 1.1" (linha 185) pelo destino real.
- Substituir "Seção 3.7" (linha 589) por Seção 3.5.3.
- **Remover a cópia duplicada da Figura 3.2** em data URI — hoje ela aparece duas vezes nas páginas
  7–8 do PDF.
- Remover todos os 16 marcadores `file ref` / `ref file`.
- Remover os links de páginas internas do Notion depois das referências.
- Sincronizar Markdown, HTML e PDF num render final único.

### Descrições factuais **[X+C]**

- **Estudo ADP**: estoque de emprego numa amostra ampla de firmas, não só de tecnologia.
- **Novo CAGED**: integração de eSocial, CAGED e Empregador Web.
- **Klein Teeselink**: queda de vagas gradual, cronologia semelhante à do estoque.
- **Aldasoro et al.**: mais de 12 mil firmas da União Europeia **e dos Estados Unidos**.

---

## Bibliografia **[X]**

Use `Final Review/Codex/evidence/bibliography/corrected_library.bib`. Depois:

1. regerar todas as 36 referências;
2. atualizar os quatro registros canônicos de publicação (Bick está como WP de 2024);
3. substituir ou rerrotular os três anexos de preprint que não batem mais com o registro publicado;
4. substituir quatro anexos de export do EBSCO por documentos reais quando conveniente;
5. manter o `.bib` concorrente da raiz fora do build.

Depois de inserir a literatura metodológica do P1, rode a skill `bibcheck` de novo sobre as entradas
novas — o `library.bib` já tem várias chaves `_nodate`, sinal de metadados incompletos.

---

## Depende da V2

### M1 — §4.3, parágrafo de estimador

Se PPML virar principal, reescrever o parágrafo de transformações com o argumento correto (média
condicional em nível versus variável transformada), e reportar efeitos como `100 × (exp(β) − 1)`.

### M2 — §4.3, dois parágrafos curtos novos

**Multiplicidade:** qual é a família pré-especificada, qual correção foi aplicada, e que p nominal e
p ajustado são ambos reportados. **Tendências paralelas:** que o desenho reporta limites de
Rambachan–Roth em vez de apenas rebaixar a linguagem, e como ler o parâmetro de suavidade.

### M3 — §4.4, pré-especificar a família de heterogeneidades

A §5.3 **já faz isso** para os casos ocupacionais — 76 códigos congelados antes da inspeção.
Estender a mesma disciplina às heterogeneidades demográficas é natural, barato, e protege contra a
acusação de garimpo.

### M4 — §5.1, a nova subseção de decomposição de desligamentos

Se `03` §P2.1 for executado, é o maior ganho narrativo do trabalho. A §5.1 passa a poder dizer qual
margem se moveu: se caem as **demissões sem justa causa**, a decisão é da firma; se caem os
**pedidos de demissão**, é o trabalhador, e a alternativa externa piorou. Cabe como subseção dentro
da §5.1, com uma tabela e um event study. Não mexe na estrutura.

E se a proxy de estoque sair, a ressalva "sem observar o estoque" desaparece de boa parte do texto —
muda §5.1, §5.2.6 e §5.3 de uma vez.

### M5 — §5.2, o que reescrever quando os números mudarem

Regerar a §5.1 inteira, os parágrafos de leitura de 5.2.1 a 5.2.5, e a síntese da §5.2.6.

**Preparação que vale fazer agora:** a §5.2.6 hoje é uma síntese de valores específicos ("queda
adicional de 4,4% no DDD para mulheres", "+15,0% na faixa até 2 salários mínimos"). Se a V2 mudar os
números, ela é reescrita inteira. Reescrevê-la desde já em torno do **padrão** — efeito médio nulo,
ajuste seletivo nos fluxos, concentração nos perfis que a Seção 3 identificou — deixa o parágrafo
estável a mudanças numéricas e é uma escrita melhor de qualquer forma.

### M6 — §4.1 e §4.2, refletir o novo painel

- **Tabela 4.2.1**: janela de "2021-01 a 2025-06, 54 meses" para "2021-01 a 2026-05, 65 meses", com
  23 pré e 42 pós.
- **§4.1**: acrescentar que o painel usa movimentações no prazo **e** fora do prazo, líquidas de
  exclusões, e por quê. Um parágrafo — é uma decisão de construção que demonstra domínio da fonte e
  que hoje nem aparece.
- **Tabelas 4.2.2 e 4.2.3**: mudam com a reclassificação de gradiente.

### M7 — Reportar a reconciliação como resultado

Uma tabela no Apêndice A e um parágrafo na §4.2. Rode o modelo antigo nos dois painéis e reporte a
diferença. Demonstra que você identificou uma ameaça específica, mediu e reportou — o que distingue
um trabalho cuidadoso de um correto por acaso. Se o coeficiente se mover pouco, é evidência a favor
do resultado original.

---

## Ordem de trabalho sugerida **[X]**

1. Aplicar as correções factuais e interpretativas (P0.1, P0.9, descrições factuais, linguagem).
2. Inserir a A.5 completa e corrigir o mapeamento da A.6.
3. Acrescentar a disposição compacta de robustez.
4. Substituir os links de artefato e regerar as referências.
5. Escrever a Conclusão.
6. Remover os detritos de export.
7. Renderizar HTML e PDF uma vez.
8. Inspecionar cada página de apêndice em largura total.
9. Re-rodar a auditoria afirmação↔artefato antes de enviar.

## Não-objetivos explícitos **[X]**

- sem reordenação de capítulos;
- sem novas famílias empíricas de subgrupo;
- sem tentativa de tornar os resultados mais significativos;
- sem polimento exaustivo de prosa antes de os bloqueadores materiais estarem resolvidos;
- **sem afirmar que uma cobertura pós-tratamento mais longa repara pretrends falhos.**
