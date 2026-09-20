# Sections 4–5 v2: remaining corrections

The Round 2 audit confirms that most Round 1 corrections were implemented. Apply the following remaining changes.

## 1. [MAJOR] Appendix A.6 / T22–T23

Issue: Correct income values are structurally scrambled.

Evidence: All expected rows are present, but T22 uses a high-income observation as its header and places the true header at row 9; T23 uses a middle-income observation as its header and places the true header at row 3.

Recommended Portuguese replacement/action:

> Substitua novamente os dois painéis pela tabela A.6 de reposição, preservando a primeira linha como cabeçalho e a ordem faixa de renda × outcome.

## 2. [MAJOR] Appendix B / N161

Issue: The appendix table links are not accessible.

Evidence: All six links were rewritten as app.notion.com/p/outputs URLs, return HTTP 404, and their targets are not bundled with the HTML export.

Recommended Portuguese replacement/action:

> Incorpore as tabelas essenciais diretamente no Apêndice B ou anexe os arquivos ao export com links relativos que funcionem fora do Notion.

## 3. [MODERATE] N042, N076, N086 and N117

Issue: Flow outcomes still imply a stock conclusion.

Evidence: The revised text still contrasts lower turnover with net job destruction even though the model does not observe employment stocks.

Recommended Portuguese replacement/action:

> Troque as conclusões sobre 'menor rotatividade, e não destruição líquida' por 'menor movimentação relativa dos fluxos; sem observar o estoque, não é possível distinguir esse padrão de mudanças no número líquido de vínculos'.

## 4. [MODERATE] N071, N117 and N118

Issue: Some synthesis language still treats exposure as effect.

Evidence: Phrases such as 'efeitos da exposição à IA' and 'ausência de impacto agregado' are stronger than an exposure-by-post estimand with imprecise coefficients.

Recommended Portuguese replacement/action:

> Use 'diferenciais pós-ChatGPT entre ocupações expostas e não expostas' e 'ausência de evidência agregada robusta', em vez de 'efeitos da exposição' e 'ausência de impacto'.

## 5. [MINOR] N154 / Appendix A.5 note

Issue: The significance legend remains malformed.

Evidence: The text still contains '\ p<0,10' and a trailing '\*'.

Recommended Portuguese replacement/action:

> Use '* p<0,10; ** p<0,05; *** p<0,01' e remova a barra e o asterisco solto ao final.

## 6. [MINOR] N114

Issue: Spaces remain before two citation commas.

Evidence: 'Klein Teeselink (2025) ,' and 'Brynjolfsson, Chandar e Chen (2025) ,' remain.

Recommended Portuguese replacement/action:

> Remova os dois espaços antes das vírgulas.

## 7. [MINOR] Appendix heading hierarchy

Issue: Appendix heading levels are inconsistent.

Evidence: Appendices A and B are H2; A.1–A.6 are H3, but B.1–B.3 are also H2.

Recommended Portuguese replacement/action:

> Formate 'Apêndice A' e 'Apêndice B' no mesmo nível superior e A.1–A.6/B.1–B.3 um nível abaixo.

## 8. [MINOR] N161 / Appendix B introduction

Issue: Appendix terminology regressed.

Evidence: The new appendix begins with 'Este anexo reúne'.

Recommended Portuguese replacement/action:

> Troque 'Este anexo reúne' por 'Este apêndice reúne'.

## 9. [MINOR] N167 / Figure B.3 metadata

Issue: The third appendix figure lacks a file-ref label.

Evidence: B.1 and B.2 use 'file ref:'; B.3 contains only the filename.

Recommended Portuguese replacement/action:

> Use '[file ref: figure_b_3_occupation_cases_by_education.png]'.
