# Versioned Dissertation Replication Package

This directory separates the empirical package into immutable research
generations.

```text
Replication Package/
├── README.md
├── V1/
├── V2/
└── _archive/             development history, not public package input
```

## V1

`V1/` is the byte-audited snapshot of the package that existed at the
start of the final review on 25 July 2026. It is intentionally preserved
with its known strengths and defects; it must not be silently patched.

Run its public interface with:

```bash
python V1/run_replication.py \
  --section all \
  --mode reproduce
```

The full V1 instructions, requirements, tests, and data contract remain
inside `V1/README.md`.

Because V1 is immutable, its historical quick-start block still says
`cd "Replication Package"`. After this versioned migration, interpret
that location as `Replication Package/V1`, or use the wrapper command
shown above. The stale directory name is documented rather than patched
inside the frozen snapshot.

## V2

`V2/` is the current five-component replication package. Its typed registry
covers the 53 computational tables and figures in Sections 3--5 and
Appendices A--D. Table 2.1 is excluded because it is a literature synthesis.

The public runner supports an offline analytical-bundle replay and a complete
official-source rebuild:

```bash
python V2/run_replication.py --target all --mode reproduce \
  --data-dir /path/to/replication-v2-bundle

python V2/run_replication.py --target all --mode full \
  --data-dir /path/to/replication-v2-bundle \
  --raw-dir /path/to/replication-v2-raw-cache
```

The Git distribution contains code, metadata, manifests, and the signed
reference. The analytical bundle and raw-source cache are separate artifacts;
see `V2/DATA_AVAILABILITY.md` for their integrity and access contracts.

## Technical schema naming

Some V1 internals use names such as `dissertation_replication_v2`.
Those identifiers describe an internal technical schema revision and
do not identify the empirical generation. They remain unchanged inside
the immutable V1 snapshot.

## Audit authority

The V2 signed reference, publication index, narrative-number registry,
cross-language receipts, and reproducibility instructions are all inside
`V2/`. Development plans and logs are preserved under `_archive/` and are not
inputs to a public run. Statistical significance is never a release gate; the
gates are data integrity, identification, portability, and claim-to-artifact
consistency.
