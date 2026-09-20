# Tabela 4.3.1 — Outcomes da análise

| Grupo | ID | Outcome | Definição | Transformação e estimador | Leitura do coeficiente | Estimador verificado | Fonte |
|---|---|---|---|---|---|---|---|
| Fluxos | admissoes | Admissões (PPML, nível) | Número de admissões formais na CBO-mês | PPML sobre a contagem em nível | Semi-elasticidade; não é log-log | ppml | results/models/specification_ladder.csv |
| Fluxos | desligamentos | Desligamentos (PPML, nível) | Número de desligamentos formais na CBO-mês | PPML sobre a contagem em nível | Semi-elasticidade; não é log-log | ppml | results/models/specification_ladder.csv |
| Fluxos | n_movimentacoes | Fluxo bruto (PPML, nível) | Admissões mais desligamentos na CBO-mês | PPML sobre a contagem em nível | Semi-elasticidade; não é log-log | ppml | results/models/specification_ladder.csv |
| Salários | ln_salario_real_adm | Salário real de admissão (log) | Salário médio de admissão deflacionado pelo IPCA | Log; OLS | Diferença aproximada em proporção | ols | results/models/specification_ladder.csv |
| Saldo | asinh_saldo | Saldo líquido (asinh) | Admissões menos desligamentos na CBO-mês | asinh; OLS | Não interpretar como percentual | ols | results/models/specification_ladder.csv |

- Admissões, desligamentos e fluxo bruto entram no PPML em nível.
- O coeficiente PPML é uma semi-elasticidade, não uma elasticidade log-log.
