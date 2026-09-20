# GitHub and Zenodo Release Checklist

## Author prerequisite

- [ ] Create or identify one Zenodo account.
- [ ] Prefer ORCID sign-in and link GitHub account `manoelbo`.
- [ ] Confirm author name, ORCID, affiliation, and release title.

## Release preparation

- [ ] Freeze the public-file allowlist.
- [ ] Validate the analytical bundle manifest.
- [ ] Complete raw-source redistribution verdicts.
- [ ] Assemble the clean repository staging tree.
- [ ] Validate the R Companion after relocation.
- [ ] Scan for secrets, absolute paths, internal documents, and oversized files.

## DOI and GitHub

- [ ] Create an unpublished Zenodo draft.
- [ ] Reserve the Zenodo DOI.
- [ ] Add DOI and repository metadata to `CITATION.cff` and README.
- [ ] Create `manoelbo/generative-ai-brazil-labor-replication` from the clean staging tree.
- [ ] Enable GitHub Pages for the R Companion.

## Release artifacts

- [ ] Build `replication-package-v2.zip`.
- [ ] Build `analytical-bundle-v2.tar.zst`.
- [ ] Export `dissertation-code-companion.html`.
- [ ] Generate `SHA256SUMS.txt`.
- [ ] Generate `RELEASE_MANIFEST.json`.

## Independent release validation

- [ ] Clone the public repository into a fresh directory.
- [ ] Unpack and validate the downloaded analytical bundle.
- [ ] Run the complete test suite.
- [ ] Run offline `reproduce` against the exact release candidate.
- [ ] Verify deterministic outputs and Python-R contracts.
- [ ] Verify local and GitHub Pages versions of the R Companion.

## Human checkpoint

- [ ] Review GitHub repository contents and presentation.
- [ ] Review Zenodo preview, citation, licenses, authors, and file list.
- [ ] Explicitly approve Zenodo publication.

## Publication

- [ ] Publish the Zenodo record.
- [ ] Verify DOI resolution and public downloads.
- [ ] Tag the audited commit as `v2.0.0`.
- [ ] Create the GitHub Release and cross-link the DOI.
- [ ] Record final DOI, URLs, commit, tag, hashes, and timestamp.

## Optional raw-source archive

- [ ] Publish `_raw/v2` only under a separate DOI after the rights gate passes.
- [ ] Otherwise retain provider URLs, vintages, acquisition instructions, and exact hashes only.
