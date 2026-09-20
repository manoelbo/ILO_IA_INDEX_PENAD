# Tabela 5.1.1 — Controle setorial

## Painel A — Especificações co-principais

| Resultado | Nível 1 coef. | EP | p | Nível 1 N / clusters | Pretrend nível 1 | Nível 2 coef. | EP  | p  | Nível 2 N / clusters | Pretrend nível 2 | Diferença N2 − N1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Admissões (PPML, nível) | −0,0538 | 0,0386 | 0,164 | 22.049 / 341 | fail (p<0,001) | −0,0751 | 0,0356 | 0,036 | 804.574 / 341 | fail (p<0,001) | −0,0213 |
| Desligamentos (PPML, nível) | −0,0420 | 0,0347 | 0,227 | 22.049 / 341 | fail (p<0,001) | −0,0664 | 0,0348 | 0,057 | 804.665 / 341 | fail (p<0,001) | −0,0244 |
| Fluxo bruto (PPML, nível) | −0,0481 | 0,0353 | 0,174 | 22.049 / 341 | fail (p<0,001) | −0,0707 | 0,0343 | 0,040 | 804.735 / 341 | fail (p<0,001) | −0,0226 |
| Salário real de admissão (log) | −0,0507 | 0,0103 | <0,001 | 22.012 / 341 | fail (p<0,001) | −0,0356 | 0,0064 | <0,001 | 682.889 / 341 | fail (p<0,001) | 0,0151 |
| Saldo líquido (asinh) | −0,5513 | 0,3783 | 0,146 | 22.049 / 341 | fail (p<0,001) | −0,1395 | 0,0734 | 0,058 | 804.735 / 341 | fail (p<0,001) | 0,4118 |

## Painel B — Robustez de inferência do nível 2

| Resultado | Coeficiente | EP | p | Pretrend conjunto | Matriz dos leads PSD | N | Clusters |
|---|---|---|---|---|---|---|---|
| Admissões (PPML, nível) | −0,0751 | 0,0384 | 0,054 | fail (p=0,269†) — não interpretável (matriz não PSD) | não | 804.574 | 341 CBO4; 87 divisões CNAE |
| Desligamentos (PPML, nível) | −0,0664 | 0,0382 | 0,085 | fail (p=0,555†) — não interpretável (matriz não PSD) | não | 804.665 | 341 CBO4; 87 divisões CNAE |
| Fluxo bruto (PPML, nível) | −0,0707 | 0,0377 | 0,064 | fail (p<0,001†) — não interpretável (matriz não PSD) | não | 804.735 | 341 CBO4; 87 divisões CNAE |
| Salário real de admissão (log) | −0,0356 | 0,0069 | <0,001 | fail (p<0,001) | sim | 682.889 | 341 CBO4; 87 divisões CNAE |
| Saldo líquido (asinh) | −0,1395 | 0,0797 | 0,084 | fail (p<0,001) | sim | 804.735 | 341 CBO4; 87 divisões CNAE |

- O nível 1 compara ocupações expostas e não expostas em toda a economia; o nível 2 compara dentro da mesma seção CNAE no mesmo mês, absorvendo choques setoriais. As duas especificações são co-principais no contrato congelado e respondem a perguntas diferentes: o nível 2 não substitui o nível 1, ele informa quanto do diferencial é entre ocupações e quanto é entre setores. Os pretrends de ambas falham nos cinco outcomes.
- † No painel de robustez bidirecional, a matriz de covariância dos leads não é positiva semidefinida para admissões, desligamentos e fluxo bruto. Os p-valores de pretrend 0,269 e 0,555 exibidos para admissões e desligamentos não são interpretáveis e não podem ser lidos como “passou”.
- O nível 3 fica fora das colunas principais: é `support_diagnostic` e retém 55 CBOs tratadas em células coexistentes.
- Não há estrelas. Os cinco outcomes dos níveis 1 e 2 têm pretrend `fail`; a tabela não sustenta leitura causal.
