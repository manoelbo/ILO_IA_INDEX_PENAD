# Tabela 5.1 — Resultados médios nacionais

| Resultado | Estimador | Coeficiente | EP | IC 95% | p | Pretrend | N | Fonte |
|---|---|---|---|---|---|---|---|---|
| Admissões (PPML, nível) | PPML | −0,0538 | 0,0386 | [−0,1296; 0,0221] | 0,164 | fail | 22.049 | results/models/specification_ladder.csv |
| Desligamentos (PPML, nível) | PPML | −0,0420 | 0,0347 | [−0,1103; 0,0262] | 0,227 | fail | 22.049 | results/models/specification_ladder.csv |
| Salário real de admissão (log) | OLS | −0,0507 | 0,0103 | [−0,0711; −0,0304] | <0,001 | fail | 22.012 | results/models/specification_ladder.csv |
| Saldo líquido (asinh) | OLS | −0,5513 | 0,3783 | [−1,2954; 0,1929] | 0,146 | fail | 22.049 | results/models/specification_ladder.csv |

- Coeficientes da especificação principal 01_no_controls.
- Os quatro pretrends falham; as estimativas não identificam um efeito causal médio nacional.
- Admissões e desligamentos são semi-elasticidades PPML em nível.
