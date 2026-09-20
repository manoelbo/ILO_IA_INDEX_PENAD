# 02 — Auditoria do Texto

Fonte auditada: `Dissertação/Dissertação de Mestrado 33fcc8ca461080cb8412e25e5b5b6ba3.md`
(1.043 linhas) e `Dissertação/Dissertao_de_Mestrado.pdf` (40 páginas).

Severidades: **Alto** = a banca vai cobrar · **Médio** = enfraquece sem ser fatal ·
**Baixo** = higiene editorial.

---

## Parte I — Estrutura

### T1. Não existe seção de Conclusão

**Severidade: Alto.**

A estrutura atual é: Introdução → 2 Mensuração → 3 Análise Descritiva → 4 Estratégia Empírica →
5 Resultados → Apêndice A → Apêndice B → Referências. O documento termina na §5.3, que é uma
subseção de resultados descritivos sobre casos ocupacionais, e vai direto para o apêndice.

Isso é o tipo de ausência que uma banca comenta antes de qualquer coisa metodológica. E é
particularmente custoso neste trabalho, porque a dissertação **tem** uma síntese boa espalhada —
o parágrafo final da §5.2.6 e o da §5.3 fazem quase todo o trabalho. Falta o lugar onde as duas
perguntas da Introdução são respondidas explicitamente, onde as três contribuições declaradas são
retomadas, e onde as limitações viram agenda.

Você pediu para não mudar a estrutura. Acrescentar uma Seção 6 não muda a estrutura das seções 1
a 5 — completa o esqueleto que já está lá. Ver `04_MELHORIAS_TEXTO.md` §M1 para o roteiro.

### T2. As limitações estão dispersas e por isso soam defensivas

**Severidade: Médio.**

As ressalvas aparecem em §2.5 (limitações da medida), §3.1 (três limitações da base descritiva),
§4.1 (duas ressalvas do CAGED vs ADP), §5.1, §5.2.6, §5.3 e na abertura do Apêndice A. Cada uma é
correta. O efeito acumulado é que o leitor encontra uma ressalva a cada duas páginas sem nunca ver
o inventário completo, e o texto passa a impressão de estar se desculpando em vez de delimitar.

Consolidar numa subseção dentro da Conclusão — com a distinção entre limitação de dado, de desenho
e de escopo — transforma o mesmo conteúdo de fraqueza em rigor.

---

## Parte II — Literatura

### T3. A lista de referências tem 15 entradas

**Severidade: Alto.**

Contagem verificada da seção REFERÊNCIAS: AGARWAL, ALDASORO, APPEL, AUTOR, BENÍTEZ, BICK, BRASIL,
BRYNJOLFSSON, CHANDAR, ELOUNDOU, GMYREK, HOSSEINI MAASOUM, HUMLUM, KLEIN TEESELINK, OSORIO.
Quinze — sendo uma delas um decreto do salário mínimo.

O `references/library.bib` tem 36 entradas e o `Citações Dissertação Mestrado.bib` tem 35, várias
com chave `_nodate` (Acemoglu robots, Autor polarization, Autor putting, Adamczyk skills, Hui
short-term, Azagirre). Ou seja: você leu mais do que citou, e a bibliografia coletada não chegou
ao texto.

Quinze referências para uma dissertação de mestrado em economia do trabalho é pouco, e a
composição chama mais atenção que o número: **todas** são da fronteira de IA de 2023–2026, exceto
Autor–Levy–Murnane (2003) e Osorio (2003). Não há literatura de automação anterior, não há
literatura brasileira, e não há metodologia.

### T4. Zero citações metodológicas de diferenças em diferenças

**Severidade: Alto. É a lacuna mais visível do trabalho.**

A Seção 4 monta um DiD com efeitos fixos de duas vias, um event study, testes de tendências
paralelas e modelos DDD, e não cita **um único** trabalho de metodologia de DiD. Isso num trabalho
cujo resultado central da §5.1 é literalmente *"os testes de tendências paralelas são rejeitados"*.

O problema não é formal. Sem essa literatura, o texto não tem como:

- **Explicar por que o TWFE está certo aqui.** Como o tratamento tem data única e comum
  (dez/2022), os problemas de ponderação negativa de Goodman-Bacon e de Callaway–Sant'Anna
  **não se aplicam**. Isso é uma força do desenho, e hoje ela está invisível. Um parágrafo citando
  essa literatura para dizer "não se aplica aqui, e eis por quê" vale muito.
- **Tratar a falha de pretrend de forma construtiva.** Roth (2022) mostra que pré-testar tendências
  e condicionar a análise no resultado do pré-teste distorce a inferência — que é exatamente o que
  o texto faz ao rebaixar para "exploratório" quando o teste falha. Rambachan e Roth (2023) dão a
  alternativa: reportar limites do efeito sob restrições de suavidade da violação. Isso converte a
  maior fraqueza do trabalho em uma seção de método.

Lista concreta do que citar e onde, em `04_MELHORIAS_TEXTO.md` §M3.

### T5. Ausência de literatura brasileira

**Severidade: Médio.**

O trabalho justifica-se pela lacuna de evidência em país de renda média, mas não dialoga com
nenhum estudo brasileiro sobre automação, mudança tecnológica e mercado de trabalho, nem com a
literatura de uso do CAGED e da RAIS. Uma banca brasileira vai perguntar. Isso também é uma
oportunidade: posicionar o trabalho contra o que já se fez no Brasil fortalece a contribuição
declarada nº 2 (distributiva).

### T6. Os índices concorrentes são comparados em tabela e nunca em dado

**Severidade: Médio.**

A Tabela 2.1 compara quatro índices (GPT Exposure, GENOE, Anthropic Economic Index, ILO Global
Index) e a §2.4 escolhe o da OIT por dois critérios. A justificativa é boa. Mas a comparação é
inteiramente conceitual: nenhum número mostra o quanto os índices concordam entre si nas ocupações
brasileiras.

Isso é uma pena, porque o material está no repositório: `data/processed/` tem
`isco_automation_augmentation_index.csv` e `anthropic_automation_augmentation_cbo.parquet`, e há
crosswalks SOC→ISCO em `data/input/`. Uma correlação de postos entre o índice da OIT e o da
Anthropic no nível da CBO, com um gráfico de dispersão, resolveria em meia página e daria à
escolha do índice uma base empírica em vez de apenas argumentativa.

---

## Parte III — Alinhamento entre afirmação e evidência

### T7. O texto ainda infere estoque a partir de fluxo em pontos residuais

**Severidade: Médio. Já mapeado pelo referee2 R2 (achado R2-003).**

A §5.1 foi corrigida e agora diz certo: *"como o modelo não observa o estoque de emprego, ele não
permite concluir se houve ou não destruição líquida de vínculos"*. Mas a mesma formulação não foi
propagada para todos os parágrafos de síntese. O referee2 R2 localiza os resíduos em N042, N076,
N086 e N117.

Vale notar que a solução real não é editorial. Se a V2 construir a proxy de estoque por saldo
acumulado, ou validar contra o painel PNADc, a ressalva deixa de ser necessária em boa parte do
texto — ver `03_MELHORIAS_CODIGO.md` §P2.3.

### T8. "Exposição" ainda vira "efeito" em alguns pontos de síntese

**Severidade: Médio. Referee2 R2, achado R2-004.**

Construções como "efeitos da exposição à IA" e "ausência de impacto agregado" são mais fortes do
que um estimando exposição×pós com coeficientes imprecisos. A forma correta, que o próprio texto
usa em outros lugares, é "diferenciais pós-ChatGPT entre ocupações expostas e não expostas" e
"ausência de evidência agregada robusta".

### T9. A explicação do Gradiente 4 vazio está incompleta e a parte principal está errada

**Severidade: Alto. Este é o achado da auditoria de código que mais afeta o texto.**

A §4.2 diz:

> *"Um ponto importante dessa classificação é que nenhuma CBO de quatro dígitos ficou no Gradiente
> 4 [...] Isso é uma consequência direta do crosswalk: como uma mesma CBO costuma corresponder a
> vários códigos ISCO-08, a exposição atribuída à ocupação vem da agregação desses destinos. Essa
> média tende a diluir os picos."*

Dois problemas factuais, verificados em `outputs/treatment_scenario_grid/scenario_cbo_classification.csv`:

1. **207 das 436 CBOs (47%) mapeiam para exatamente um destino ISCO-08.** Para quase metade da
   amostra não existe diluição alguma. A mediana de destinos por CBO é 2.
2. **A média não é o que bloqueia o G4 — é o desvio.** A regra de classificação exige, para o
   Gradiente 4, `média − desvio ≥ 0,50`, enquanto os gradientes 1 a 3 exigem `média + desvio ≥ 0,50`.
   Um desvio maior dificulta o G4 e facilita os inferiores. E o desvio usado soma a dispersão entre
   destinos ISCO à dispersão entre tarefas.

O caso decisivo: a CBO 4121 (Operadores de equipamentos de entrada e transmissão de dados)
corresponde a ISCO 4132 (Data Entry Clerks), a ocupação **mais exposta de todo o índice da OIT**,
com score 0,70. No painel ela sai com média 0,593 e desvio 0,138, e é classificada como Gradiente 3
— falha o corte de média por 0,007 e o corte de dispersão por 0,045.

O parágrafo precisa ser reescrito com a explicação correta, independentemente de a V2 acontecer.
Como está, ele atribui a um fator (relação muitos-para-muitos) o que é causado principalmente por
outro (a assimetria da regra), e um leitor atento que abrir o código vai notar.

### T10. A afirmação de "muitos zeros" é falsa e sustenta uma escolha de estimador

**Severidade: Médio. Verificado com dado.**

A Tabela 4.3.1 e o parágrafo seguinte justificam a transformação `log(y+1)` assim:
*"Os fluxos de admissões e desligamentos são contagens com muitos zeros, o que motiva o log(y+1)
no modelo principal e os modelos de Poisson na robustez."*

Medido em `data/output/painel_caged_did_ready.parquet` (23.319 células):

- 62 células com zero admissões — **0,27%**
- 44 células com zero desligamentos
- mediana de 479 admissões por célula ocupação-mês; percentil 1 igual a 3

O painel nacional praticamente não tem zeros. A frase deve sair. E, sem ela, o argumento para
preferir `log(y+1)` a PPML desaparece — o que o seu `final_review_planning.md` §2.2 já tinha
concluído por outro caminho.

### T11. Descrições factuais a corrigir

**Severidade: Médio. Já registradas nas auditorias anteriores; repito para o checklist.**

- **Estudo ADP** (§4.1): usa estoque de emprego numa amostra ampla de firmas, não apenas firmas de
  tecnologia.
- **Novo CAGED** (§4.1): é a integração de eSocial, CAGED e Empregador Web — não é declaração
  direta de todas as firmas ao CAGED.
- **Klein Teeselink** (§5.1): a queda de vagas é gradual e com cronologia semelhante à do estoque,
  não anterior ao ajuste de emprego.
- **Aldasoro et al.** (§5.1): mais de 12 mil firmas da União Europeia **e dos Estados Unidos**, não
  só europeias.

### T12. Cobertura do painel: um número precisa de contexto

**Severidade: Médio.**

A §4.2 reporta: *"Entre as 629 CBOs de quatro dígitos presentes no painel, 436 receberam
correspondência oficial e score de exposição, o que representa 69,3% [...] essas ocupações
concentram 92,5% dos fluxos observados."*

Os números estão corretos. O que falta é a consequência: das 629, apenas **341 entram na amostra de
estimação** (as 75 tratadas mais as 266 controles), porque as 95 de Minimal Exposure e as 193 sem
score são excluídas. São 46% do universo de classificação fora do modelo principal. Isso está
implícito na Tabela 4.2.3 e no N=18.307 do Apêndice A, mas nunca é dito em prosa. É melhor dizer
você mesmo, com a justificativa, do que deixar a banca descobrir.

---

## Parte IV — Pendências editoriais do referee2

Estas vêm da Rodada 2 (`correspondence/referee2/2026-07-25_round2_sections4_5_report.md`), verdito
**HOLD**. Nenhuma muda resultado; todas são visíveis.

| ID | Problema | Severidade |
|---|---|---|
| R2-001 | Apêndice A.6: no export HTML os cabeçalhos das tabelas T22/T23 estão trocados com linhas de dados — 90 células fora de posição. **Confira qual export vai ser entregue**: no `.md` atual a A.6 aparece correta. | Alto no HTML |
| R2-002 | Apêndice B: os seis links de tabela foram reescritos como URLs `app.notion.com/p/outputs/...` e retornam HTTP 404. Os arquivos existem localmente mas não são anexados ao export. | Alto |
| R2-007 | Hierarquia de títulos: Apêndices A e B são H2, A.1–A.6 são H3, mas B.1–B.3 também são H2. | Baixo |
| R2-008 | "Este anexo reúne" no Apêndice B; o resto do texto usa "apêndice". | Baixo |
| R2-009 | Figura B.3 sem o rótulo `[file ref: ...]` que B.1 e B.2 têm. | Baixo |
| C021 | §5.2.2, conclusão de raça: ainda diz "não há evidência de que a exposição à IA tenha ampliado", que trata exposição como efeito. | Médio |
| — | A nota geral da Tabela A.6 está **em inglês** ("Notes: coefficients are DDD estimates…") no meio de um apêndice em português. | Baixo |

---

## Parte V — O que está bom no texto

Registro porque a recomendação final depende disso.

- **A separação conceitual da §2.1 é excelente.** Exposição não é adoção, não é impacto causal, não
  é substituição. É a melhor página do trabalho e sustenta a leitura correta de tudo o que vem
  depois.
- **A honestidade sobre limites é genuína e rara.** O texto reporta pretrends que falham, diz
  quando o suporte amostral é fino, avisa que não há correção por testes múltiplos, e apresenta
  "acomodação silenciosa" explicitamente como hipótese de discussão. Muita dissertação de mestrado
  não faz isso; várias publicações também não.
- **A ponte entre a Seção 3 e a Seção 5 funciona.** O argumento de que os mesmos perfis
  identificados como mais expostos (mulheres, mais escolarizados, renda intermediária) são os que
  concentram os primeiros sinais de ajuste dá unidade narrativa ao trabalho.
- **O congelamento prévio dos casos ocupacionais** da §5.3 — 76 códigos CBO de 6 dígitos, definidos
  semanticamente antes de olhar os resultados — é uma prática de pré-registro que vale explicitar
  ainda mais, porque protege contra a acusação de garimpo.
- **A Seção 3 é sólida e independente.** Mesmo que a Seção 5 mude por inteiro na V2, a análise
  descritiva se sustenta sozinha e responde à primeira pergunta de pesquisa.

Esse último ponto importa para a decisão da V2: metade da dissertação não está em risco.
