# Data Availability

## Distribution model

The Git repository contains code, small redistributable metadata, expected
schemas, and signed manifests. Large data are distributed separately:

- the **analytical bundle** contains only the inputs required by `reproduce`;
- the **raw-source cache** is optional and is used by `full`;
- generated outputs are never inputs to an estimator;
- `results/reference/` is a signed comparison authority and is immutable during
  public runs.

Mount or copy the analytical bundle at `data/`, or pass its root explicitly
with `--data-dir`. The expected file set, byte sizes, schemas, encodings, and
SHA-256 digests are recorded in `config/analytical_bundle_manifest.csv`.
`code/replication/data_manifest.py validate` checks a received bundle before
estimation. Keep the output root disjoint from both the analytical bundle and
the raw-source cache: the runner rejects an output that equals, contains, or is
contained by either input root, including paths that overlap through a symlink.

Keep the optional raw-source cache outside the public package. Its expected
layout places the 195 CAGED archives and their inventory at the cache root,
with `section3/`, `rais/`, `pnadc/`, and `spatial/` subdirectories. Pass that
root with `--raw-dir`; the local development cache prepared for this release is
recorded by `../_raw/v2/raw_cache_manifest.json` and is excluded from Git. When
that registry is present, preflight verifies the exact path set, byte sizes,
and SHA-256 digests before construction. Registered missing files may still be
downloaded by `full`; altered or unregistered files are rejected.

## Source inventory

| Source | Vintage used | Acquisition route | Redistribution |
|---|---|---|---|
| Novo CAGED | January 2021--May 2026, official archive state captured in July 2026 | MTE/PDET public microdata archive | Raw archives remain in the `full` cache; the analytical bundle contains derived panels |
| RAIS | 2016--2024 | Base dos Dados mirror of MTE RAIS public microdata | The bundle contains occupation-year aggregates, not identified records |
| PNAD Contínua | 2012 Q1--2026 Q1 for the complementary panel; 2025 Q3 for Section 3 | IBGE quarterly microdata and frozen query extracts | The bundle contains analytical extracts and panels |
| ILO--NASK occupational exposure index | 2025 release, Working Paper 140 | ILO publication data workbook | The small source workbook is hash-validated; users remain responsible for ILO terms |
| Anatel fixed broadband | 2021--2022 source years and July 2026 archive vintage | Anatel open-data ZIP members | The bundle contains the analytical panel; the large extracted members remain in the `full` flow |
| IBGE geography and SIDRA | Census 2022 municipality geography and PNAD TIC 2021 table 7334 | IBGE public downloads/API snapshot | Frozen public extracts are included when redistribution permits |
| Occupational and industry classifications | CBO/ISCO and CNAE 2.0 versions named in the source manifest | Official MTE, ILO, and CONCLA files | Small crosswalk and metadata files are hash-validated |

The analytical bundle also carries a small, signed set of CAGED construction
backing data. These files record facts that cannot be recovered from the final
panels alone, such as raw-row exclusions and build-stage coverage. In
`reproduce`, `code/caged/backing.py` validates the backing against the frozen
panels before materializing it as output. In `full`, the same files are rebuilt
from official sources and must converge to the signed reference.

The machine-readable source registry is `config/data_sources.csv`. It records
the provider URL, vintage, acquisition timestamp, byte size, schema reference,
encoding, SHA-256 digest or manifest, and the provider-terms URL. Provider terms
govern source data even though the package code is MIT-licensed.

Official access pages:

- MTE/PDET Novo CAGED and RAIS microdata:
  <https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged>
- IBGE PNAD Contínua microdata:
  <https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Trimestral/Microdados/>
- Anatel open data:
  <https://www.gov.br/anatel/pt-br/dados/dados-abertos>
- ILO 2025 occupational-exposure index:
  <https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure>

## Modes and network access

`reproduce` must run with network access disabled. A network request in this
mode is a package defect. `full` may access official providers only for a
missing source. Every acquired file is checked against its recorded vintage
metadata before it can enter construction.

The Novo CAGED FTP listing uses Latin-1 percent-encoded file names, while the
text members are UTF-8, semicolon-delimited, and use decimal commas. MOV and
FOR have 28 source columns; EXC has 30. The fact-month variable, rather than
the archive month, defines time for late declarations. These properties are
validated by the ingestion code and are not manual parsing instructions.

Some acquisition routes require user-supplied credentials or billing. In
particular, every `full` run containing PNADc requires an explicit
`--billing-project`; the runner checks this before validating or reconstructing
any data. Credentials are never stored in this package.

## Integrity and disclosure

Novo CAGED is reconstructed as `MOV + FOR - EXC`. The source manifest preserves
all 195 archive hashes, and the rebuilt monthly aggregates must reconcile with
the adjusted PDET series in every month. RAIS and PNADc support gates are
evaluated before their coefficients. The spatial analysis stops when support
fails and therefore never creates a real-treatment result for Family F.

No individual-level output is published. Researchers must still comply with
the current terms and disclosure rules of every original provider.

## Frozen construction rules

The following data-construction decisions are part of the replication
contract, not run-time choices:

- the Novo CAGED fact window is January 2021 through May 2026: 65 fact months
  and 195 MOV, FOR, and EXC archives;
- `competenciamov` defines the fact month. FOR records must be strictly older
  than their archive month; the 11 observed same-month EXC records are retained
  in their stated fact month, while future-dated EXC records are invalid;
- undocumented `tipoempregador = 1` and `tipoestabelecimento = -1` values are
  preserved without semantic recoding and remain outside public/private
  assignments;
- transfer codes 70 and 80 have zero physical rows in the frozen vintage. The
  declared transfer filter therefore remains visible but is inert;
- positive nominal wages are winsorized at approximate P1/P99 within CBO4 and
  calendar year before aggregation. Zero-flow cells have missing mean wages;
- CBO4 `2414`, absent from the frozen treatment universe, is preserved as
  `No score` and excluded from the principal contrast; and
- the administrative CNAE `secao = Z, subclasse = 9999999` is preserved as an
  explicit undocumented bucket and is never mapped to an official division.
