# V1-V2 Reconciliation

The V1 baseline is the frozen local Base dos Dados MOV extract. The V2 vintage is the official MTE FTP reconstruction using MOV + FOR - EXC.

## Blocking 2021 check

- V1 movements: 36,554,795.
- V2 movements: 39,103,072.
- Absolute delta: 2,548,277.
- Percentage delta: 6.97%.
- MOV revision: 0.
- FOR contribution: 2,680,702.
- EXC contribution: -132,425.

The plan requires this delta to be positive and on the order of 8%. The observed positive delta is of that order and therefore passes the blocking check. No numerical tolerance was introduced beyond that written contract.

## Monthly summary

- admissoes: mean monthly delta 2.58%; maximum absolute percentage delta 10.37% in 202101.
- desligamentos: mean monthly delta 3.05%; maximum absolute percentage delta 12.63% in 202101.
- movimentacoes: mean monthly delta 2.80%; maximum absolute percentage delta 11.40% in 202101.
- Largest absolute monthly movement delta: 324,150 in 202101.

## Decomposition

For each flow and month, the CSV decomposes the total delta as `MOV revision + FOR contribution + EXC contribution`, where the EXC contribution is negative.

The optional live BigQuery comparison was not required for this local reconciliation. The frozen V1 extracts already provide the exact Base dos Dados MOV rows used by V1.
