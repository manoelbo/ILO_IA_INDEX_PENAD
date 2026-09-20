"""Reorder original methodology paragraphs and apply documented factual fixes."""
from pathlib import Path
import re
P=Path(__file__).resolve().parents[1]
s=(P/'source/section_04.md').read_text()
def span(start,end):
    return s[s.index(start):s.index(end)].strip()
def paragraph(start):
    return next(line for line in s.splitlines() if line.startswith(start))

data='\n'.join([
'# 4 Estratégia empírica',
'## 4.1 Dados e construção do painel CAGED',
paragraph('No Brasil, o equivalente'),
paragraph('A escolha do CAGED'),paragraph('Primeiro, a **frequência**'),
paragraph('Essa escolha também').replace('na Apêndice D','no Apêndice D'),
span('Enquanto a PNAD Contínua','O principal desafio metodológico')])
data=data.replace('Tabela 4.2.1','Tabela 4.1.1').replace(' \\\\*','*')
cross=span('O principal desafio metodológico','## **4.3')
old=paragraph('Para as 436 CBOs')
new='Para as 436 CBOs com correspondência, uma mesma ocupação brasileira pode apontar para mais de um código ISCO-08. Nesses casos, agrego as pontuações disponíveis e aplico a regra da OIT, que considera tanto o nível médio quanto a dispersão da exposição. As famílias tratadas apontam, em média, para 2,89 destinos ISCO cada, contra 1,65 no grupo de controle. A Tabela 4.2.1 apresenta os grupos resultantes.\n**REVISAR COM MANÉ — R01: compressão das pontuações e direção do erro de mensuração**\nA agregação pode comprimir as pontuações mais altas e reduzir a separação entre grupos. Isso não demonstra, porém, que o coeficiente da regressão seja um limite inferior em magnitude. Essa leitura exigiria hipóteses adicionais sobre o erro de mensuração, sua relação com os desfechos e a seleção das ocupações que recebem pontuação. Como o crosswalk perde ocupações tanto no topo quanto na base da estrutura ocupacional e pode mudar a classificação binária, a direção do viés no contraste estimado permanece indeterminada.'
cross=cross.replace(old,new)
cross=cross.replace('Tabela 4.2.2','Tabela 4.2.1').replace('Tabela 4.2.3','Tabela 4.2.2')
cross=cross.replace('Por isso, a análise principal reúne os Gradientes 1 a 3 como grupo exposto.','A regra de tratamento reúne os Gradientes 1 a 4; na amostra efetiva, somente os Gradientes 1 a 3 estão presentes.')
cross=cross.replace('Essa diluição é atenuada pela forma como o grupo de tratamento foi definido.','A definição binária reduz parte da sensibilidade a mudanças entre gradientes, embora não elimine o erro de mensuração.')
cross=cross.replace('Assim, uma ocupação cuja pontuação foi diluída continua classificada como exposta, ainda que em um gradiente mais baixo do que teria sob uma correspondência perfeita.','Assim, uma ocupação que muda entre esses quatro gradientes continua classificada como exposta; a regra não evita mudanças que atravessem a fronteira entre exposição, exposição mínima e não exposição.')
cross=cross.replace('O painel contém 630 famílias de CBO de quatro dígitos.','Os dois universos têm denominadores distintos. O crosswalk contém 629 famílias, das quais 193 não recebem pontuação. O painel observado contém essas famílias e a CBO 2414, ausente da tabela de correspondência e presente em cinco células entre julho de 2025 e maio de 2026. Ela permanece sem pontuação e fora da amostra principal. O painel contém, portanto, 630 famílias de CBO de quatro dígitos, das quais 194 não recebem pontuação.')

ident='\n'.join([
'## 4.3 Desenho de identificação por diferenças em diferenças',
paragraph('O desenho não capta'),
'O lançamento ocorreu no fim de novembro; na codificação do painel, janeiro de 2021 a novembro de 2022 é o pré-período e dezembro de 2022 a maio de 2026 é o pós-período. Todas as ocupações expostas recebem a mesma data de início. O contraste compara a mudança das ocupações expostas com a mudança das não expostas, mantendo os grupos definidos antes da estimação.',
'**REVISAR COM MANÉ — R02: hipótese de identificação e alcance dos efeitos fixos**',
'A hipótese contrafactual é que, sem a difusão da IA generativa, os dois grupos teriam seguido trajetórias paralelas nos desfechos. Os efeitos fixos de ocupação retiram diferenças permanentes entre CBOs; os de mês retiram choques comuns a todas elas. Eles não retiram automaticamente choques que atingem de modo diferente o trabalho administrativo e o trabalho manual, nem tendências próprias de cada grupo. Os coeficientes descrevem diferenciais pós-evento associados à exposição potencial. Para atribuí-los à tecnologia seriam necessárias, além dessa comparação, condições de identificação que os diagnósticos não sustentam.',
paragraph('A literatura recente alerta')])

principal=span('Como os resultados têm formatos diferentes','Além do modelo estático')
principal=principal.replace('Admissões e desligamentos são contagens','Admissões, desligamentos e fluxo bruto são contagens')
principal=principal.replace('Para interpretar $`\\beta`$ como efeito, as trajetórias dos grupos precisariam ser paralelas antes do evento.','Para interpretar $`\\beta`$ como efeito, seria necessária a hipótese contrafactual de tendências paralelas na ausência do evento, apoiada por trajetórias prévias compatíveis.')
event=span('Além do modelo estático','Idade média, participação feminina').replace('^{+41}','^{+23}')
event+='\nA janela balanceada do estudo de eventos vai de janeiro de 2021 a novembro de 2024 (−23 a +23), com novembro de 2022 omitido. Ela é distinta da janela completa do modelo estático, que chega a maio de 2026 (+41). A equação acima se aplica ao PPML; para salário em log e saldo em asinh, uso a mesma soma de interações na forma linear. Os coeficientes anteriores ao evento são diagnósticos da comparação, os posteriores descrevem sua dinâmica e a média de k = 0 a +23 é o estimando usado no exercício de sensibilidade. Essa média normalizada não é o coeficiente pós da regressão estática.'
outcomes=span('O PPML é usado','Por fim, a análise de heterogeneidade')
outcomes=outcomes.replace('A mesma comparação é aplicada a quatro resultados principais: admissões, desligamentos, salário real de admissão e saldo líquido.','A análise acompanha cinco desfechos: admissões, desligamentos, fluxo bruto, salário real de admissão e saldo líquido. A tabela nacional destaca quatro deles; o fluxo bruto, soma das entradas e saídas, permanece nas tabelas setoriais, nas heterogeneidades completas e no apêndice.')
outcomes=outcomes.replace('Tabela 4.3.1','Tabela 4.4.1')
inference='\n'.join([
'### 4.4.4 Inferência e especificações adicionais',
paragraph('Idade média, participação feminina').replace('em testes de robustez que usam medidas calculadas antes do evento.','em especificações separadas: uma interage características prévias com o pós e outra inclui composição contemporânea, sem substituir o modelo principal.'),
'A inferência usa erros-padrão agrupados por CBO de quatro dígitos e distribuição t com graus de liberdade iguais ao menor número de clusters menos um. No modelo nacional, são 341 clusters e 340 graus de liberdade. Estrelas indicam o p-valor declarado em cada tabela e não validam a interpretação causal. Nas heterogeneidades, elas usam os p-valores BH das famílias originais.',
'A especificação setorial é co-principal. No painel por ocupação, setor e mês, ela absorve efeitos fixos de CBO × seção da CNAE e de seção da CNAE × mês. A comparação passa a ocorrer entre ocupações do mesmo setor e mês, com agrupamento dos erros por CBO. Esse desenho controla choques mensais comuns ao setor, mas não garante trajetórias paralelas entre as ocupações que nele trabalham. A comparação com o nível nacional está na Tabela 5.2.1; a inferência alternativa com agrupamento em duas dimensões permanece como diagnóstico na Seção 4.6 e no pacote.'])
heter=span('Por fim, a análise de heterogeneidade','## **4.4')
heter=heter.replace('As tabelas do corpo apresentam o primeiro; o Apêndice A apresenta o segundo.','As tabelas da Seção 5.3 priorizam o DDD; o Apêndice A reúne os DDDs completos, os DiDs dentro dos grupos e suas figuras de apoio.')
heter=heter.replace('Por fim, a análise','A análise')
heter+='\nNa equação linear, o parâmetro de interesse é a interação tripla e os termos de ordem inferior identificados são mantidos. Para os desfechos de contagem, o mesmo preditor entra na média condicional exponencial do PPML. Os termos invariantes que são absorvidos pelos efeitos fixos não são identificados separadamente. O DDD é estimado em seu próprio modelo; não é obtido subtraindo mecanicamente DiDs estimados em amostras separadas. Cada perfil é comparado com seu complemento na partição informada. Em sexo, as duas orientações expressam o mesmo contraste com sinais opostos; nas demais partições, os complementos podem mudar.'
heter+='\n'+span('A literatura internacional sugere','## **4.5')
heter=heter.replace('As famílias A e B ficam separadas porque a família B apenas usa definições alternativas de grupos já testados na família A. Por exemplo, as faixas de 18 a 24 e de 22 a 25 anos são duas formas próximas de examinar trabalhadores jovens, não hipóteses independentes. Juntá-las trataria essas repetições como novos testes e distorceria a correção.','As famílias A e B foram declaradas separadamente para distinguir partições principais e alternativas. Por exemplo, as faixas de 18 a 24 e de 22 a 25 anos examinam populações que se sobrepõem. A revisão preserva esse desenho de multiplicidade e seus p-valores, sem refazer o ajuste ao selecionar linhas para as tabelas do corpo.')
heter+='\nOs DiDs dentro dos grupos e seus estudos de eventos usam a janela balanceada −23 a +23. Os DDDs estáticos usam a amostra própria registrada de cada modelo, e os diagnósticos DDD usam estudos de eventos com efeitos fixos mais saturados: CBO × subgrupo, mês × subgrupo e mês × tratamento. Por isso, os tamanhos amostrais e os diagnósticos de um DiD não devem ser atribuídos ao DDD correspondente.'
diag=s[s.index('Os testes a seguir'):].strip()
diag=diag[:diag.index('**Por que a exposição mínima')].strip()
diag=diag.replace('conforme a Tabela 5.1.1','conforme a Seção 4.4.4 e a Tabela 5.2.1')
diag+='\nOs diagnósticos de pré-tendências combinam teste conjunto dos coeficientes anteriores, inclinação linear GLS e inspeção dos coeficientes individuais. Suporte ocupacional, posto e positividade da matriz de covariância são verificados antes de interpretar os testes. Uma matriz com posto insuficiente não produz um teste conjunto válido: os coeficientes mensais permanecem publicados, mas o teste e a inclinação GLS ficam indefinidos. “Não rejeitada” e “alerta” também não equivalem a identificação causal assegurada.\nA extensão espacial foi interrompida antes da estimação do contraste de tratamento porque a variação identificadora se concentrava em poucas Unidades da Federação. O Apêndice B.3 preserva o diagnóstico de suporte e os placebos; não há coeficientes espaciais a interpretar. Os exercícios de estoque formal e informalidade são apresentados no Apêndice D, com diagnósticos próprios no Apêndice B.'
result='\n'.join([data,'## 4.2 Correspondência CBO–OIT e definição dos grupos',cross,ident,'## 4.4 Especificações econométricas e desfechos','### 4.4.1 Especificação principal',paragraph('A especificação foi construída'),principal,'### 4.4.2 Estudo de eventos',event,'### 4.4.3 Desfechos e transformações',outcomes,inference,'## 4.5 Heterogeneidades',heter,'## 4.6 Diagnósticos, placebos e robustez',diag])+'\n'
(P/'sections/04_method.md').write_text(result)
print(len(result))
