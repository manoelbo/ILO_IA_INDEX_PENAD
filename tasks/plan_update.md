# Nota de atualização do plano — revisão 2

**Data:** 26 de julho de 2026
**Documentos alterados:** `Final Review/Combined/05_PLANO_V2.md` · `tasks/plan.md` · `tasks/todo.md`
**Motivo:** verificação de campo do FTP do MTE + três decisões do autor + restauração de uma
hierarquia que a revisão 1 havia rebaixado sem justificativa.

---

## Resumo

Sete mudanças. Três vieram de medição em campo, três de decisão do autor, e uma é **correção de um
erro meu**: eu havia rebaixado uma decisão de desenho do `final_review_planning.md` do autor sem
perceber, e três itens dele ficaram de fora.

| # | Mudança | Origem | Impacto |
|---|---|---|---|
| 1 | Hierarquia de efeitos fixos restaurada; CNAE×mês volta a co-principal | **Correção** | Alto |
| 2 | `cbo_2d × periodo` acrescentado como diagnóstico de suporte | **Omissão minha** | Médio |
| 3 | Clusterização bidirecional CBO × divisão CNAE | **Omissão minha** | Baixo |
| 4 | Google Trends adiado para a rodada do texto | Decisão | Escopo |
| 5 | Corte fixado em maio/2026 | Decisão do autor | Alto |
| 6 | Encoding corrigido: conteúdo UTF-8, nomes de arquivo latin-1 | Medição | Alto |
| 7 | Admissões por primeiro emprego canceladas | Medição | Alto |

---

## 1. Hierarquia de efeitos fixos restaurada

**O que estava errado.** O `final_review_planning.md` §2.4 do autor definia quatro níveis, com o
**modelo enriquecido por indústria como principal** (nível 2). Na consolidação com o conjunto do
Codex, isso virou "robustez enriquecida, sujeita a suporte" — um rebaixamento que passou sem
justificativa e que eu não peguei ao escrever `tasks/plan.md`.

**O que mudou.** Restaurada a hierarquia original, com uma diferença: o gate de suporte agora decide
**o peso** da especificação, não a existência dela.

| Nível | Especificação | Papel |
|---|---|---|
| 1 | `cbo_4d + periodo` | Benchmark nacional. Sempre reportado. |
| 2 | `cbo_4d^cnae + cnae^periodo` | **Principal enriquecido.** Sempre reportado, lado a lado com o 1. |
| 3 | nível 2 + `cbo_2d^periodo` | Diagnóstico de suporte. |
| 4 | firma × CBO, firma × mês | Fora desta rodada. |

**Por que importa.** O grupo tratado é concentrado em apoio administrativo, que por sua vez é
concentrado em finanças, informação e comunicação, e serviços profissionais. Esses setores tiveram
ciclo próprio entre 2021 e 2026 — demissões em tecnologia, ciclo de crédito, Selic. Sem
`cnae × periodo`, esse ciclo entra no coeficiente como se fosse exposição à IA. É o confundidor mais
plausível do desenho inteiro, e a auditoria já dava o indício: o desequilíbrio de covariáveis na
linha de base é severo em todas as dimensões, com diferença normalizada de 1,248 em ensino superior.

Há um ganho possível adicional: se as tendências paralelas falham porque setores expostos se
recuperaram da pandemia em ritmo diferente, `cnae × periodo` absorve isso — e pode ser justamente o
que salva a identificação.

**Por que não substituir o nível 1 pelo 2.** O nível 2 **muda o estimando**. Deixa de ser "ocupações
expostas versus não expostas no Brasil" e passa a ser "dentro do setor, expostas versus não
expostas". Se parte do efeito da IA for realocar emprego **entre** setores, o nível 2 absorve
exatamente o que se quer medir. Por isso os dois são co-principais e nunca substitutos.

**A comparação entre eles vira resultado.** Coeficiente estável nos dois níveis é evidência contra
confundimento setorial. Coeficiente que se move muito é um achado a explicar. Isso está como critério
de aceitação da Tarefa 18b.

## 2. `cbo_2d × periodo` como diagnóstico de suporte

**O que faltava.** O §2.4 do autor tinha "Occupation-cycle robustness: add CBO2×month fixed effects
when within-cell treatment support is adequate". O `tasks/plan.md` tinha apenas "cluster em CBO2" —
que é clusterização, não efeito fixo. São coisas diferentes: um controla ciclo de grande família
ocupacional, o outro só ajusta a inferência.

**Como entrou, e por que com ressalva.** A exposição é fortemente correlacionada dentro de grupo CBO
de 2 dígitos: o grupo 4 (administrativo) é quase todo exposto, o grupo 6 (agropecuária) quase todo
não exposto. `cbo_2d × periodo` pode absorver **quase toda** a variação de tratamento.

O resultado típico é um coeficiente estimado sobre um subconjunto minúsculo, com erro-padrão enorme.
E aí vem a armadilha de leitura: parece que "o efeito não sobrevive ao controle", quando na verdade
a **variação** não sobreviveu.

Por isso o nível 3 entra como **diagnóstico**, não como teste de robustez, com duas salvaguardas:

- a tabela de coexistência tratado/controle por célula sai **antes** do coeficiente;
- se a coexistência cair abaixo de **20 CBOs tratadas**, o nível 3 é reportado sem interpretação
  substantiva.

## 3. Clusterização bidirecional CBO4 × divisão CNAE

**O que faltava.** O §2.4 do autor pedia "Two-way CBO and CNAE clustering should be evaluated as a
robustness check for the industry panel". Não estava no plano.

**Como entrou.** Como robustez do painel setorial, com duas exigências técnicas:

- usar **divisão** CNAE (~87 categorias), **nunca seção** (~19). Clusterização bidirecional com
  poucos clusters numa das dimensões produz cobertura abaixo do nominal;
- reportar o número de clusters em cada dimensão.

Consequência prática: a Tarefa 13 agora precisa guardar `secao` **e** `divisao`. Isso está no
critério de aceitação.

Alerta de honestidade registrado no plano: bidirecional às vezes dá erro-padrão **menor** que
unidirecional. Se acontecer, reporte assim mesmo e não promova a bidirecional a principal.

## 4. Google Trends adiado

**O que era.** Task 13 do `final_review_planning.md`, prioridade P1: validar com dados brasileiros
de busca que 30/11/2022 é a data relevante para o Brasil, sem substituir o evento.

**Por que fica fora desta rodada.** Três razões, em ordem de peso:

1. **Convida ao garimpo de data de corte.** Se a série sugerir outra data, a tentação de mover o
   evento é forte — e o §3 do plano do autor proíbe explicitamente ("nenhum limiar de interesse de
   busca é promovido a evento principal"). Ter o dado à mão aumenta a tentação sem aumentar a
   disciplina.
2. **Mede consciência, não adoção.** Interesse de busca normalizado não é uso no trabalho.
3. **É ativo de texto, não de código.** Não muda nenhuma estimativa; muda um parágrafo.

**Onde foi parar.** Registrado em `tasks/plan.md` §8 e em `05_PLANO_V2.md` §8 como fora de escopo,
com a justificativa, para não parecer esquecimento. Entra na rodada do texto.

## 5. Corte fixado em maio de 2026

Decisão do autor em 25/07/2026. A Tarefa 4 perdeu a lógica de detecção de corte e agora manda
explicitamente ignorar `202606` mesmo que exista no FTP quando a execução acontecer.

Justificativa registrada: junho acrescentaria um mês a um pós-tratamento que já terá 42, com ganho
estatístico desprezível, e seria o mês **mais incompleto** de toda a série.

Janela final: **2021-01 a 2026-05 = 65 competências, 195 arquivos.**

## 6. Encoding corrigido

O `05_PLANO_V2.md` dizia que os arquivos descompactados são CSVs em **latin-1**. Verificado em
campo: **está errado, e de um jeito que quebraria o parser**.

- **Conteúdo dos `.txt`: UTF-8.** Separador `;`, decimal vírgula.
- **Nomes de arquivo no servidor FTP: latin-1.** Baixar arquivo com acento no nome exige
  percent-encoding latin-1 — `Movimenta%E7%E3o.xlsx`, não `%C3%A7%C3%A3o`.

Os nomes de coluna vêm com acento e cedilha (`competênciamov`, `saldomovimentação`,
`cbo2002ocupação`), e precisam ser normalizados. MOV e FOR têm 28 colunas; EXC tem 30.

Também entrou uma restrição de desenho que não estava em nenhum dos planos: **os arquivos FOR
alcançam 12 meses para trás e os EXC até 76**, o que torna os últimos ~12 meses do painel
progressivamente incompletos — o espelho exato do problema que a auditoria encontrou no início da
V1. Tratamento na Tarefa 9.

## 7. Admissões por primeiro emprego canceladas

Era a recomendação P2.2 da auditoria, e **está morta**. Medição em campo:

| Competência | % admissão "tipo ignorado" | % primeiro emprego |
|---|---:|---:|
| 2021-04 | 0,00% | 6,22% |
| 2021-07 | 97,84% | 0,23% |
| 2026-05 | 99,94% | — |

O tipo de admissão deixou de ser informado entre abril e julho de 2021 — 18 meses antes do evento.
Usar a variável produziria um efeito inteiramente espúrio.

**A decomposição de desligamentos continua e segue sendo o exercício de maior valor do plano**:
menos de 0,12% de tipo ignorado na janela inteira, com demissão sem justa causa caindo de 47,0% para
42,1% e pedido de demissão subindo de 31,2% para 36,1%.

---

## Riscos novos que estas mudanças introduzem

| Risco | Mitigação registrada |
|---|---|
| Sobrecontrole no nível 2 absorve realocação entre setores | Níveis 1 e 2 co-principais, nunca substitutos. A diferença é reportada como resultado. |
| `cbo_2d × periodo` mata a variação de tratamento | **Esperado.** Tabela de variação remanescente antes do coeficiente; enquadrado como diagnóstico. |
| Bidirecional com poucos clusters | Divisão CNAE, nunca seção. Número de clusters reportado. |
| **Mais especificações = mais tentação de garimpo** | Todas pré-registradas antes de estimar e **todas reportadas**, inclusive as feias. Uma escada só vale se os degraus ruins aparecem. |

O último é o que mais merece atenção. A escada saiu de nove degraus para doze. Isso aumenta a
superfície para escolher o resultado mais bonito depois de ver os p-valores. O antídoto continua
sendo o mesmo e precisa ser levado a sério: **o `DECISIONS.md` é escrito antes da estimação, e
nenhum degrau é omitido da tabela final por dar resultado feio.**

---

## O que não mudou

- O contrato de tratamento: G1–G4 versus `Not Exposed`, `Minimal Exposure` excluída.
- PPML principal para contagens, `log(1+y)` secundário.
- Sem controles de composição contemporâneos no principal.
- Janela de evento `−23…+23` sem recorte de caudas, referência nov/2022.
- Os checkpoints bloqueantes continuam sendo **A**, **B** e **F**. O **C** segue não bloqueante,
  conforme decisão do autor de 25/07.
- A ordem das fases e o número de fases.
