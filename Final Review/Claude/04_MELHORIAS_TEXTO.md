# 04 — Melhorias no Texto

Restrição respeitada em todo o documento: **a estrutura das seções 1 a 5 não muda.** As adições
propostas cabem dentro das seções que já existem, exceto a Conclusão, que é a completude de um
esqueleto incompleto e não uma reorganização.

Ordem: primeiro o que fazer independentemente da V2, depois o que depende dela.

---

## Parte I — Independe da V2

### M1. Escrever a Seção 6 — Conclusão

**Prioridade: máxima. Faça mesmo que não faça mais nada.**

Três a quatro páginas, sem tabela nova, sem figura nova. Roteiro:

**6.1 Retomada das perguntas.** A Introdução faz duas perguntas explícitas — quem está exposto, e
se ocupações expostas mudaram diferencialmente. Responda as duas em texto corrido, nessa ordem,
sem hedge novo. A resposta à primeira é forte e você pode afirmá-la. A resposta à segunda é
qualificada, e você já tem a formulação certa espalhada pela §5.2.6.

**6.2 As três contribuições, revisitadas.** A Introdução declara mensuração, distribuição e
evidência empírica. Diga o que cada uma entregou e o que ficou aquém. Sobre a de mensuração, se a
V2 acontecer, aqui entra o crosswalk revisto — que passa a ser a contribuição mais concreta do
trabalho.

**6.3 Limitações consolidadas.** Recolher as ressalvas hoje espalhadas por §2.5, §3.1, §4.1, §5.1,
§5.2.6, §5.3 e pela abertura do Apêndice A, e organizá-las em três blocos: limitação de dado
(cobertura, crosswalk, ausência de estoque, ausência de informal), limitação de desenho (exposição
não é adoção, tendências paralelas, multiplicidade), e limitação de escopo (curto prazo, só
mercado formal). Ver M2 — a mudança de forma é o ganho aqui.

**6.4 Agenda.** O que a Etapa 3 (conectividade) tentou e por que não se sustentou; o desenho com
dados de firma no ambiente seguro da FGV, que o seu `final_review_planning.md` Task 6 já
especifica; e a pergunta de estoque via RAIS ou PNADc.

**6.5 Implicações.** Curto, e sem prescrever política que a evidência não sustenta. O achado
distributivo da Seção 3 é forte o suficiente para sustentar uma observação sobre quem deve ser
monitorado; o achado empírico não sustenta recomendação.

### M2. Consolidar as limitações — a mesma informação, outro efeito

**Prioridade: alta. Esforço: baixo, é recorte e colagem.**

Hoje o leitor encontra uma ressalva a cada duas páginas e nunca vê o inventário completo. Isso lê
como insegurança. O mesmo conteúdo, reunido em §6.3 com uma taxonomia, lê como domínio do objeto.

Nas seções 2 a 5, deixe apenas a ressalva local estritamente necessária para não induzir o leitor
ao erro naquele ponto, e remeta ao §6.3 para o resto.

### M3. Acrescentar a literatura metodológica de DiD

**Prioridade: alta. É a lacuna mais visível do trabalho.**

Hoje: zero citações de metodologia de DiD, num trabalho cujo resultado central é que as tendências
paralelas são rejeitadas.

**Onde entra, e o que cada uma faz pelo texto:**

| Onde | Citar | Para dizer o quê |
|---|---|---|
| §4.1, ao apresentar o desenho | Goodman-Bacon (2021); Callaway e Sant'Anna (2021); Sun e Abraham (2021); de Chaisemartin e D'Haultfœuille (2020) | **Que não se aplicam aqui.** O tratamento tem data única e comum (dez/2022), então não há adoção escalonada, não há ponderação negativa, e o TWFE é o estimador correto. Hoje isso é uma força invisível do desenho. Um parágrafo. |
| §4.3, ao introduzir o event study | Roth (2022) | Pré-testar tendências e condicionar a interpretação no resultado do pré-teste distorce a inferência — que é o procedimento atual do texto. Assumir isso explicitamente é mais forte do que ser pego. |
| §4.3 e §5.1 | Rambachan e Roth (2023) | A alternativa construtiva: limites do efeito sob restrição de suavidade da violação. Se a V2 implementar (P1.2 do doc 03), aqui entram os resultados. |
| §4.3, sobre estimador de contagem | Silva e Tenreyro (2006); Correia, Guimarães e Zylkin (2020) | Justificar PPML. |
| §4.4, sobre heterogeneidade | Romano e Wolf (2005) ou Benjamini e Hochberg (1995) | Justificar a correção por testes múltiplos. |
| §4.3, sobre inferência | Cameron e Miller (2015) | Clusterização e graus de liberdade. |

**Cuidado:** confira cada entrada antes de inserir. O `references/library.bib` já tem várias
chaves `_nodate`, sinal de metadados incompletos. Existe uma skill `bibcheck` no projeto que faz
verificação entrada por entrada — vale rodar antes de entregar.

### M4. Acrescentar literatura de automação e literatura brasileira

**Prioridade: média.**

- **Automação anterior à IA generativa**, na §2.2 ou §2.3: Acemoglu e Restrepo sobre robôs e
  tarefas, Autor e Dorn sobre polarização, Frey e Osborne, Webb, Felten–Raj–Seamans. Várias já
  estão no seu `.bib` e não chegaram ao texto. Isso ancora o trabalho numa tradição em vez de
  parecer que a economia do trabalho começou em 2023.
- **Literatura brasileira**, na Introdução e na §3: o trabalho se justifica pela lacuna de país de
  renda média, então precisa mostrar que conhece o que já se fez no Brasil sobre automação,
  mudança tecnológica e uso de CAGED/RAIS. Uma banca brasileira vai perguntar.

### M5. Corrigir a explicação do Gradiente 4 vazio na §4.2

**Prioridade: alta. Independe da V2 — a explicação atual está factualmente incompleta.**

Ver `02_AUDITORIA_TEXTO.md` §T9 e `01_AUDITORIA_CODIGO.md` §2 para a verificação.

Substituir o parágrafo que começa em *"Um ponto importante dessa classificação..."*. A versão
correta precisa dizer:

- A ponte alcança 11 das 13 ocupações ISCO-08 classificadas pela OIT como Gradiente 4, e 16 CBOs
  tocam pelo menos uma delas.
- Ainda assim nenhuma CBO é classificada como Gradiente 4, e a razão principal é a **assimetria da
  regra**: o Gradiente 4 exige `média − desvio ≥ 0,50` enquanto os gradientes 1 a 3 exigem
  `média + desvio ≥ 0,50`, de modo que uma dispersão maior dificulta o topo e facilita a base.
- A dispersão usada agrega variação entre tarefas e variação entre destinos ISCO, o que a infla
  para CBOs com múltiplos destinos.
- A diluição da média contribui, mas não é o fator decisivo: **207 das 436 CBOs mapeiam para um
  único destino**, e a mediana de destinos por CBO é 2.

Um exemplo concreto vale mais que a explicação abstrata: a CBO 4121 (operadores de entrada de
dados) corresponde à ISCO 4132 (Data Entry Clerks), a ocupação mais exposta de todo o índice da OIT
com score 0,70, e sai classificada como Gradiente 3 — falha o corte de média por 0,007.

Se a V2 acontecer e a regra for revista (P0.2), este parágrafo vira uma nota metodológica curta
mais uma linha no apêndice de sensibilidade, o que é bem melhor.

### M6. Remover a afirmação de "muitos zeros"

**Prioridade: média. Esforço: uma frase.**

O parágrafo após a Tabela 4.3.1 diz que os fluxos são *"contagens com muitos zeros"*. Medido:
0,27% das células têm zero admissões; a mediana é 479 admissões por célula. A frase deve sair,
e a escolha de transformação precisa de outra justificativa — ver M9.

### M7. Explicitar a amostra efetiva de estimação na §4.2

**Prioridade: média. Esforço: duas frases.**

O texto reporta 436 CBOs com score (69,3% de 629) e 92,5% dos fluxos. Correto. Falta dizer que a
amostra do modelo principal tem **341 CBOs** — 75 tratadas mais 266 controles — porque as 95 de
Minimal Exposure e as 193 sem score ficam fora. São 46% do universo de classificação. Está
implícito no N=18.307 do Apêndice A; é melhor dizer você mesmo, com a justificativa que já existe
no texto, do que deixar a banca deduzir.

### M8. Fechar as pendências do referee2

**Prioridade: alta para as duas primeiras, baixa para o resto. Checklist:**

- [ ] **Apêndice A.6**: no export HTML os cabeçalhos das T22/T23 estão trocados com linhas de
      dados (90 células fora de posição). Confira qual export vai ser entregue — o `.md` atual
      aparenta estar correto. Se for o HTML, reinserir sem reordenar.
- [ ] **Apêndice B**: os seis links de tabela retornam HTTP 404. Embutir as tabelas no apêndice ou
      anexar os arquivos com caminho relativo que funcione fora do Notion.
- [ ] Propagar a formulação fluxo-vs-estoque da §5.1 para N042, N076, N086 e N117.
- [ ] §5.2.2: trocar "não há evidência de que a exposição à IA tenha ampliado" por formulação de
      diferencial pós-ChatGPT.
- [ ] Nivelar a hierarquia dos apêndices — B.1 a B.3 estão em H2 e deveriam estar em H3.
- [ ] "Este anexo reúne" → "Este apêndice reúne".
- [ ] Figura B.3 sem o rótulo `[file ref: ...]`.
- [ ] Traduzir a nota geral da Tabela A.6, que está em inglês.
- [ ] Corrigir as quatro descrições factuais: estudo ADP (estoque, amostra ampla de firmas, não só
      tecnologia), Novo CAGED (eSocial + CAGED + Empregador Web), Klein Teeselink (queda gradual,
      cronologia semelhante à do estoque), Aldasoro et al. (UE **e** EUA).

---

## Parte II — Depende da V2

### M9. §4.3 — reescrever o parágrafo de estimador

Se PPML virar principal, o parágrafo de transformações precisa mudar. O argumento correto não é
zeros — é que PPML estima o efeito sobre a média condicional em nível, que é o estimando de
interesse, enquanto `log(y+1)` estima efeito sobre variável transformada cujo mapeamento para
percentual depende da escala da célula. Com admissões variando de 3 a milhares por célula, isso é
material. Reportar efeitos como `100 × (exp(β) − 1)`.

### M10. §4.3 — acrescentar dois parágrafos curtos

- **Multiplicidade**: qual é a família de testes pré-especificada, qual correção foi aplicada, e
  que p nominal e p ajustado são ambos reportados.
- **Tendências paralelas**: que o desenho reporta limites de Rambachan–Roth em vez de apenas
  rebaixar a linguagem quando o teste falha, e como ler o parâmetro de suavidade.

### M11. §4.4 — pré-especificar a família de heterogeneidades

Hoje as heterogeneidades são apresentadas como escolhas motivadas pela literatura, o que está
certo, mas sem declaração de que o conjunto foi fixado antes de olhar os resultados. Como a §5.3
**já faz isso** para os casos ocupacionais — 76 códigos congelados antes da inspeção —, estender a
mesma disciplina às heterogeneidades demográficas é natural e barato, e protege contra a acusação
de garimpo.

### M12. §5.1 — a nova subseção de decomposição de desligamentos

**Se P2.1 for executado, este é o maior ganho narrativo do trabalho.**

Hoje a §5.1 encontra desligamentos caindo, sugere menor movimentação dos fluxos, e precisa recuar
porque não observa o estoque. Com a decomposição por tipo de movimentação, a §5.1 passa a poder
dizer qual margem se moveu:

- se caem as **demissões sem justa causa**, a decisão é da firma — retenção, incompatível com
  deslocamento e compatível com ajuste pela porta de entrada;
- se caem os **pedidos de demissão**, a decisão é do trabalhador — deterioração da alternativa
  externa nas ocupações expostas, que é um resultado mais forte.

Isso cabe como subseção dentro da §5.1, com uma tabela e um event study. Não mexe na estrutura.

E, se a proxy de estoque (P2.3) sair, a ressalva "sem observar o estoque" desaparece de boa parte
do texto — o que muda a §5.1, a §5.2.6 e a §5.3 de uma vez.

### M13. §5.2 — o que reescrever quando os números mudarem

Os parágrafos que descrevem magnitude e significância precisam ser regerados a partir das novas
tabelas: §5.1 inteira, os parágrafos de leitura de cada subseção de 5.2.1 a 5.2.5, e a síntese da
§5.2.6.

**Preparação que vale fazer agora:** a §5.2.6 hoje é uma síntese de achados específicos ("queda
adicional de 4,4% no DDD para mulheres", "+15,0% nas admissões da faixa até 2 salários mínimos").
Se a V2 mudar os números, ela é reescrita inteira. Reescrevê-la desde já em torno do **padrão**, e
não dos valores — o padrão é: efeito médio nulo, ajuste seletivo nos fluxos, concentração nos
perfis que a Seção 3 identificou como mais expostos — deixa o parágrafo estável a mudanças
numéricas e é uma escrita melhor de qualquer forma.

### M14. §4.2 e §4.1 — refletir o novo painel

Se a V2 acontecer:

- **Tabela 4.2.1** (escopo do painel): observações, CBOs, meses e janela mudam. A janela vai de
  "2021-01 a 2025-06, 54 meses" para "2021-01 a 2026-05, 65 meses", com 23 meses pré e 42 pós.
- **§4.1**, ao descrever o CAGED: acrescentar que o painel usa movimentações no prazo **e** fora do
  prazo, líquidas de exclusões, e por quê. Um parágrafo. É uma decisão de construção que
  demonstra domínio da fonte e que hoje nem aparece.
- **Tabelas 4.2.2 e 4.2.3**: mudam com a reclassificação de gradiente.

### M15. Reportar a reconciliação como resultado

Não é uma seção nova — é uma tabela no Apêndice A e um parágrafo na §4.2.

Quando o painel for reconstruído com fora do prazo, rode o modelo antigo nos dois painéis e
reporte a diferença. Isso demonstra que você identificou uma ameaça específica à validade, mediu, e
reportou — que é exatamente o que distingue um trabalho cuidadoso de um trabalho correto por
acaso. Se o coeficiente se mover pouco, é evidência a favor do resultado original. Se se mover
muito, você achou algo que precisava ser achado.
