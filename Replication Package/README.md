# Section 3 Descriptive Analysis Replication Package

This folder contains the official supplementary script for the dissertation's
Section 3 descriptive analysis.

The package is post-build by design. It uses the already constructed analytic
file at `data/output/pnad_ilo_merged.csv` and does not download PNAD data,
query BigQuery, rebuild CAGED panels, or import exploratory notebooks.

## Run

From the project root:

```bash
python "Replication Package/replicate_section3_descriptive.py" --strict
```

To skip PNG generation and only write tables plus the claims audit:

```bash
python "Replication Package/replicate_section3_descriptive.py" --strict --skip-figures
```

## Outputs

The default output directory is `Replication Package/outputs/`.

- `section3_claims_audit.md`: human-readable audit of all registered claims
- `section3_claims_audit.csv`: machine-readable claim registry
- `MANIFEST.md`: data sources and denominators
- `tables/table_3_*.md` and `tables/table_3_*.csv`: stable supplemental tables
- `figures/figure_3_*.png`: stable supplemental figures

`WARN` items identify text/table harmonization issues in the dissertation.
`FAIL` is reserved for missing source files or validation failures that prevent
replication.
