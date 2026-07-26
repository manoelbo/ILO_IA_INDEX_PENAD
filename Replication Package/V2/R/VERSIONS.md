# R Environment Versions

Provisioned on 25 July 2026 with R 4.4.1 on macOS arm64.

| Package | Version |
|---|---:|
| `fixest` | 0.14.0 |
| `HonestDiD` | 0.2.6 |
| `data.table` | 1.17.0 |

Verification:

```bash
Rscript -e 'library(fixest); library(HonestDiD); library(data.table)'
```

The five-model Python-R cross-replication uses an independent base-R
fixed-effect and IPF PPML implementation rather than calling `fixest`.
`HonestDiD` and `data.table` remain the declared backends for the sensitivity
analysis and its input handling.
