# 02 — Auditoria do Texto (combinada)

20 achados das duas auditorias. Origem: **[X]** Codex, **[C]** Claude, **[X+C]** ambos.

**Veredito combinado: HOLD — não circular o PDF atual.**

O manuscrito tem estrutura coerente, pergunta defensável e uma discussão de suporte, pretrends,
multiplicidade e da distinção entre exposição e adoção que é incomum para o nível. Muitos números
centrais batem com seus arquivos de origem. Mas há um erro factual na primeira página, uma quebra
entre o Apêndice A.6 do texto e o do pacote, uma lacuna estrutural, links quebrados e defeitos de
renderização que um leitor vê de imediato.

**A estrutura de capítulos não precisa mudar.** O trabalho necessário é dirigido.

Fonte canônica auditada: `Dissertação/Dissertação de Mestrado 33fcc8ca461080cb8412e25e5b5b6ba3.md`
(1.043 linhas), comparada com o HTML adjacente, o PDF de 40 páginas, as figuras locais, o pacote V1,
tabelas de backing em `outputs/`, a bibliografia canônica e as rodadas anteriores do referee2.

---

## Parte I — Crítico

### 1. O resumo da primeira página usa a população errada **[X]**

**Localização:** Markdown linha 5; PDF página 1. **Severidade: crítico** — é a primeira frase
substantiva que a professora vai ler.

A linha 5 diz: *"cerca de 10 % da força de trabalho **formal** está em ocupações altamente
expostas"*. Os números do próprio trabalho, na linha 21 e nas tabelas, são:

- **10,1% da população ocupada total**
- **14,8% dos trabalhadores formais**
- 6,7% dos informais

Verificado nas duas linhas. É um erro factual de manchete, e ironicamente subestima o achado: a
concentração no mercado formal é justamente o que sustenta a escolha do CAGED na estratégia
empírica.

### 2. O Apêndice A.6 do texto e o do pacote são objetos diferentes **[X]**

**Severidade: crítico.**

O A.6 do manuscrito (linhas 956–986) contém os grupos de renda pretendidos. Os arquivos V1
chamados `table_a_6_income_*` contêm grupos de **escolaridade**, por causa de
`V1/code/sections4_5/publication.py:335` e `pipeline.py:239`.

A validação da V1 marca os artefatos errados como aprovados porque são byte-idênticos aos arquivos
de referência errados.

**Implicação:** o manuscrito pode conter os valores de renda corretos, mas o pacote público não
consegue produzi-los sob os nomes publicados. A cadeia afirmação→código está quebrada. Ver `01` §3.

---

## Parte II — Estrutura

### 3. Não existe seção de Conclusão **[C]**

**Severidade: alto.** Verificado: nenhum título contendo "conclus", "considera" ou "final" no
documento inteiro.

A estrutura é Introdução → 2 Mensuração → 3 Descritiva → 4 Estratégia → 5 Resultados → Apêndice A →
Apêndice B → Referências. O documento termina numa subseção de resultados descritivos e vai direto
para o apêndice.

É o tipo de ausência que uma banca comenta antes de qualquer coisa metodológica. E é custoso aqui
porque a dissertação **tem** uma boa síntese espalhada — o parágrafo final da §5.2.6 e o da §5.3
fazem quase todo o trabalho. Falta o lugar onde as duas perguntas da Introdução são respondidas
explicitamente, as três contribuições são retomadas, e as limitações viram agenda.

Acrescentar uma Seção 6 não muda a estrutura das seções 1 a 5 — completa um esqueleto incompleto.
Roteiro em `04` §M1.

### 4. As limitações estão dispersas e por isso soam defensivas **[C]**

**Severidade: médio.**

Ressalvas aparecem em §2.5, §3.1, §4.1, §5.1, §5.2.6, §5.3 e na abertura do Apêndice A. Cada uma é
correta. O efeito acumulado é que o leitor encontra uma ressalva a cada duas páginas sem nunca ver
o inventário completo, e o texto passa a impressão de estar se desculpando em vez de delimitar.
Consolidar em §6.3 transforma o mesmo conteúdo de fraqueza em rigor.

---

## Parte III — Alinhamento entre afirmação e evidência

### 5. O Apêndice A.5 não entrega os painéis de escolaridade prometidos **[X]**

**Localizações:** linhas 621 e 929–954. **Severidade: alto.**

O corpo promete DDD de escolaridade, diagnósticos de pretrend, saldo líquido e medidas alternativas
de saldo. A A.5 traz só três outcomes principais e omite `asinh(saldo)` e todas as linhas do Painel
B.2. A tabela completa existe em
`outputs/section4_5_final/tables/table_5_2_6_heterogeneity_education.md`.

É uma omissão consequente porque escolaridade contém um dos resultados de heterogeneidade mais
enfatizados do trabalho.

### 6. Robustez prometida e não reportada **[X]**

**Localizações:** linhas 362, 399 e 407–412. **Severidade: alto.**

O método afirma que a dissertação usa ou avalia: grupo de controle ampliado incluindo
`Minimal Exposure`; modelos sem controles contemporâneos; controles pré-determinados; e modelos de
contagem Poisson. O manuscrito não mostra resultados nem uma tabela compacta de disposição para
nenhum deles. Arquivos de backing fora da dissertação não tornam a afirmação auditável para o
leitor.

### 7. Linguagem causal e de adoção excede o desenho **[X+C]**

**Localizações:** linhas 23, 66, 137–155, 231, 297, 377–395, 420. **Severidade: médio-alto.**

Movimentos problemáticos:

- admissões e desligamentos caindo simultaneamente descritos como "não destruição de vínculos",
  mesmo com o estoque não observado;
- alta exposição descrita como transformação em curso;
- efeitos de subgrupo que "aparecem primeiro";
- o coeficiente DiD descrito como efeito atribuível ao diferencial pós-ChatGPT;
- casos ocupacionais descritivos descritos como mecanismos.

O desenho observa exposição ocupacional potencial, fluxos formais e uma data de evento. Não observa
adoção pela firma, uso pelo trabalhador, estoque de emprego, nem mecanismos isolados. As falhas de
pretrend nos fluxos nacionais limitam ainda mais a interpretação causal.

*Nota:* a solução completa não é editorial. Se a V2 construir a proxy de estoque, a ressalva deixa
de ser necessária em boa parte do texto — ver `03` §P2.3.

### 8. O universo de CBOs é internamente contraditório **[X+C]**

**Localizações:** linhas 331–373. **Severidade: alto.**

O texto alterna entre 629 CBOs no universo de classificação, 436 casadas no painel analítico, 193
sem score e excluídas, e 23.319 células. A linha 364 chama as 629 de "presentes no painel", e a
tabela seguinte mistura um denominador de 629 com células do painel de 436 — fazendo `No score`
parecer ter zero observações.

Faltam também as **341 CBOs** da amostra estrita de estimação (75 tratadas + 266 controles), que
nunca aparecem em prosa apesar de estarem implícitas no N=18.307. São 46% do universo de
classificação fora do modelo principal.

Definir quatro denominadores uma vez e reusar: 629 universo · 436 casadas · 341 amostra estrita ·
18.307 células retidas.

### 9. A explicação do Gradiente 4 vazio está factualmente incompleta **[C]**

**Severidade: alto.**

A §4.2 diz: *"como uma mesma CBO costuma corresponder a vários códigos ISCO-08, a exposição
atribuída à ocupação vem da agregação desses destinos. Essa média tende a diluir os picos."*

Dois problemas verificados em `outputs/treatment_scenario_grid/scenario_cbo_classification.csv`:

1. **207 das 436 CBOs (47%) mapeiam para exatamente um destino ISCO-08.** Para quase metade não
   existe diluição alguma. A mediana de destinos por CBO é 2.
2. **O que bloqueia o G4 não é a média — é o desvio.** G4 exige `média − desvio ≥ 0,50` enquanto
   G1–G3 exigem `média + desvio ≥ 0,50`. Um desvio maior dificulta o topo e facilita a base. E o
   desvio soma dispersão entre destinos à dispersão entre tarefas.

Caso decisivo: a CBO 4121 (operadores de entrada de dados) corresponde à ISCO 4132, a ocupação mais
exposta de todo o índice da OIT (score 0,70), e sai como Gradiente 3 — falha o corte de média por
0,007. Ver `01` §6 para a tabela completa das 16 CBOs afetadas.

### 10. "Muitos zeros" não se sustenta **[X+C]**

**Localização:** linha 412. **Severidade: médio.**

O texto motiva `log(y+1)` com contagens com muitos zeros. Na amostra estrita congelada:

- **31 de 18.307 células de admissão são zero (0,169%)**
- **17 de 18.307 células de desligamento são zero (0,093%)**

E no painel completo: mediana de 479 admissões por célula, percentil 1 igual a 3. A frase precisa
sair, e a escolha de transformação precisa de outra justificativa — ver `04` §M9.

### 11. A lista de referências está incompleta **[X+C]**

**Severidade: alto.**

O manuscrito lista **15 das 36 entradas canônicas** e inclui duas páginas internas do Notion depois
das referências. **Vinte e uma referências citadas estão ausentes da lista.** Bick ainda aparece
como working paper de 2024 em vez do registro publicado atual.

Verificado: a lista tem AGARWAL, ALDASORO, APPEL, AUTOR, BENÍTEZ, BICK, BRASIL, BRYNJOLFSSON,
CHANDAR, ELOUNDOU, GMYREK, HOSSEINI MAASOUM, HUMLUM, KLEIN TEESELINK, OSORIO — sendo uma delas um
decreto de salário mínimo.

Use `Final Review/Codex/evidence/bibliography/corrected_library.bib`, que já está pronto, e
`bibcheck_report.md` para a disposição entrada por entrada.

### 12. Zero citações metodológicas de diferenças em diferenças **[C]**

**Severidade: alto. É a lacuna mais visível do trabalho.**

A Seção 4 monta DiD com efeitos fixos de duas vias, event study, testes de tendências paralelas e
DDD, e não cita **um único** trabalho de metodologia de DiD. Num trabalho cujo resultado central da
§5.1 é literalmente *"os testes de tendências paralelas são rejeitados"*.

Sem essa literatura o texto não consegue:

- **Explicar por que o TWFE está certo aqui.** Como o tratamento tem data única e comum (dez/2022),
  os problemas de ponderação negativa de Goodman-Bacon e Callaway–Sant'Anna **não se aplicam**.
  Isso é uma força do desenho, hoje invisível.
- **Tratar a falha de pretrend de forma construtiva.** Roth (2022) mostra que condicionar a
  interpretação no resultado de um pré-teste distorce a inferência — que é exatamente o
  procedimento atual. Rambachan e Roth (2023) dão a alternativa.

Lista do que citar e onde em `04` §M3.

### 13. Ausência de literatura de automação e de literatura brasileira **[C]**

**Severidade: médio.**

Todas as 15 referências são da fronteira de IA de 2023–2026, exceto Autor–Levy–Murnane (2003) e
Osorio (2003). Não há literatura de automação anterior (Acemoglu–Restrepo, Autor–Dorn, Frey–Osborne,
Webb, Felten et al. — várias já estão no seu `.bib` e não chegaram ao texto), nem literatura
brasileira sobre automação e uso de CAGED/RAIS. O trabalho se justifica pela lacuna de país de renda
média; uma banca brasileira vai perguntar.

### 14. Os índices concorrentes são comparados em tabela e nunca em dado **[C]**

**Severidade: médio.**

A Tabela 2.1 compara quatro índices e a §2.4 escolhe o da OIT. A justificativa é boa, mas
inteiramente conceitual — nenhum número mostra o quanto os índices concordam nas ocupações
brasileiras. O material está no repositório: `data/processed/isco_automation_augmentation_index.csv`
e `anthropic_automation_augmentation_cbo.parquet`, mais crosswalks SOC→ISCO em `data/input/`. Uma
correlação de postos com dispersão resolve em meia página.

### 15. Descrições factuais a corrigir **[X+C]**

- **Estudo ADP** (§4.1): usa estoque de emprego numa amostra ampla de firmas, não só de tecnologia.
- **Novo CAGED** (§4.1): é a integração de eSocial, CAGED e Empregador Web.
- **Klein Teeselink** (§5.1): a queda de vagas é gradual, com cronologia semelhante à do estoque.
- **Aldasoro et al.** (§5.1): mais de 12 mil firmas da União Europeia **e dos Estados Unidos**.

---

## Parte IV — Render e consistência interna

### 16. O PDF remove diagnósticos de suporte e imprime markup **[X]**

**Localização:** PDF páginas 31–37. **Severidade: alto — não é cosmético.**

- A.2–A.6 perdem a coluna final de `CBOs tratadas/controle`;
- `<br>` literal aparece em várias tabelas do apêndice;
- `&lt;0,001` aparece literalmente;
- A.6 não tem rótulo B.1 claro, termina com uma nota em inglês, e omite a definição operacional de
  renda ocupacional pré-tratamento.

**A coluna cortada contém o diagnóstico de suporte usado para qualificar os resultados de
heterogeneidade.** Sem ela, o leitor não consegue avaliar quais achados são finos.

### 17. Erros numéricos e de referência cruzada **[X]**

**Severidade: médio.** Todos na Seção 3, que nenhuma rodada anterior de referee auditou.

- Linha 277: `0,304 − 0,252 = 0,052`, aproximadamente **20,6%**, não 0,056 e 22%; e a categoria
  exibida é `55+`, não `55–59`.
- Linha 313 destaca Serviços Profissionais e Administração Pública como líderes de volume, mas a
  Tabela 3.4 mostra **Comércio em primeiro, com 1,36 milhão**.
- Linha 185 remete a um "Anexo 1.1" inexistente.
- Linha 589 remete a uma Seção 3.7 inexistente; o destino pretendido é a Seção 3.5.3.

### 18. Detritos de export e conteúdo duplicado **[X]**

- **A Figura 3.2 está embutida duas vezes** — uma como data URI e outra como PNG local — produzindo
  duas figuras completas nas páginas 7–8 do PDF.
- Dezesseis marcadores `file ref` ou `ref file` aparecem no manuscrito e no PDF.
- Duas páginas internas de reescrita do Notion aparecem depois da bibliografia.
- Markdown, HTML e PDF têm horários de modificação diferentes e não são um conjunto de release
  sincronizado.

### 19. Pendências editoriais do referee2 R2 **[X+C]**

| ID | Problema |
|---|---|
| R2-002 | Apêndice B: os seis links retornam HTTP 404; os arquivos existem em `outputs/` mas não são anexados. |
| R2-001 | A.6 no HTML com cabeçalhos trocados por linhas de dados (90 células fora de posição). Confira qual export vai ser entregue — o `.md` aparenta estar correto. |
| C021 | §5.2.2 ainda diz "não há evidência de que a exposição à IA tenha ampliado", tratando exposição como efeito. |
| R2-007 | B.1–B.3 em H2 enquanto A.1–A.6 estão em H3. |
| R2-008 | "Este anexo reúne" → "Este apêndice reúne". |
| R2-009 | Figura B.3 sem o rótulo `[file ref: ...]`. |
| — | Nota geral da A.6 em inglês no meio de um apêndice em português. |

---

## Parte V — Blindspot por família de resultado **[X]**

Esta seção vem inteira do Codex e é o exercício mais útil da auditoria de texto.

**Nacionais.** As três estimativas pontuais são negativas, mas admissões e desligamentos falham
pretrend. O pretrend do salário é mais limpo, mas o coeficiente pós é impreciso. Adoção e estoque
não são observados. O manuscrito já reconhece boa parte disso nas linhas 440–456; esse enquadramento
cauteloso deveria controlar também o resumo e a conclusão.

**Sexo.** O DDD de admissões femininas é o contraste demográfico mais limpo. Mas a síntese diz que
a evidência de saldo líquido não é robusta, e **o Apêndice A.2 contém dois contrastes normalizados
de saldo significativos, com pretrends de DDD aprovados**. Continuam secundários e não são outcomes
de estoque, mas a afirmação absoluta de que nenhum contraste de saldo é robusto é forte demais —
uma rara ocorrência de o texto ser cauteloso *contra* si mesmo além do necessário.

**Raça/cor.** O contraste mais claro é em desligamentos. Não estabelece efeito de estoque nem
mecanismo causal de rotatividade. O Apêndice A.3 também carece de hierarquia completa de tabela e de
apresentação do B.2.

**Idade.** O padrão não é monotônico e não reproduz uma concentração clara em 18–24 ou 22–25. Idade
não é tempo de casa e não mede conhecimento tácito específico da firma. A seção de resultados
reporta boa parte dessa discrepância; a motivação conceitual da §4.4 deveria ser igualmente cautelosa.

**Escolaridade.** Desligamentos no ensino superior são mais defensáveis que admissões, porque a
dinâmica das admissões é menos compatível com tendências paralelas. A A.5 incompleta suprime o
contexto diagnóstico completo — é a omissão de apêndice mais importante do manuscrito.

**Renda.** O DDD de desligamentos na renda intermediária tem o padrão mais claro, mas só 28 CBOs
tratadas e 32 controles. O grupo de renda mais alta tem 3/7 e é corretamente tratado como fino. A
tabela de renda do manuscrito é mais defensável que o artefato do pacote, que é semanticamente
errado.

**Casos ocupacionais.** As afirmações fixas conferidas batem com suas matrizes, incluindo o resumo
de sinais 33/36 e a mediana racial de 31,3 pontos percentuais. A seleção semântica congelada é uma
força. São trajetórias normalizadas sem grupo de controle dedicado: ilustram padrões e não
identificam mecanismos.

---

## Forças confirmadas **[X+C]**

- **O manuscrito não precisa de redesenho estrutural.**
- A fórmula do DDD é corretamente descrita como `post × tratamento × subgrupo`.
- Os pretrends de heterogeneidade são distinguidos do teste conjunto nacional do event study.
- Limitações de suporte e multiplicidade são explicitamente divulgadas.
- Todo PNG referenciado localmente existe.
- Números nacionais centrais e afirmações conferidas dos casos ocupacionais batem com o backing.
- **A separação conceitual da §2.1** — exposição não é adoção, não é impacto causal, não é
  substituição — é a melhor página do trabalho e sustenta a leitura correta de tudo o que vem depois.
- **A honestidade metodológica está acima da média do que se publica**: reporta pretrends que
  falham, diz quando o suporte é fino, avisa da ausência de correção por multiplicidade, e apresenta
  "acomodação silenciosa" como hipótese de discussão.
- O congelamento prévio dos 76 códigos dos casos ocupacionais é prática de pré-registro.
- Vários parágrafos já distinguem fluxo de estoque e exposição de adoção — esses trechos são o
  modelo para revisar os que sobraram.
- **A Seção 3 é sólida e independente.** Mesmo que a Seção 5 mude por inteiro na V2, ela se sustenta
  e responde à primeira pergunta de pesquisa.

---

## Conclusão da auditoria

A contribuição principal do trabalho sobrevive à auditoria; o PDF atual não. Corrigir o texto não
exige capítulos novos nem pergunta de pesquisa nova. Exige um release sincronizado em que o universo
da manchete, as tabelas do apêndice, as afirmações de robustez, a bibliografia, os links de artefato
e a linguagem causal estejam todos consistentes com a evidência computacional.
