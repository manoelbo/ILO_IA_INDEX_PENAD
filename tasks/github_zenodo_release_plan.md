# GitHub and Zenodo Release Plan

## Objective

Publish Dissertation Replication Package V2 as a citable, versioned, and independently downloadable research artifact. Zenodo will be the archival authority and DOI provider. A new clean GitHub repository will provide navigable code, documentation, issue tracking, and a browser-accessible R Companion.

## Fixed release architecture

- Canonical archive: one Zenodo record for the public replication package and analytical bundle.
- Code mirror: `https://github.com/manoelbo/generative-ai-brazil-labor-replication`.
- Git history: a new repository created from an audited export; never reuse the current project repository or its history.
- Main Zenodo record contents:
  - `replication-package-v2.zip`: code, documentation, signed reference outputs, tests, and R Companion sources;
  - `analytical-bundle-v2.tar.zst`: the frozen inputs required by offline `reproduce`;
  - `dissertation-code-companion.html`: directly downloadable reading companion;
  - `SHA256SUMS.txt`: archive-level integrity contract;
  - `RELEASE_MANIFEST.json`: versions, byte sizes, hashes, source commit, and creation environment.
- The optional `_raw/v2` source cache is excluded from the main record. It may become a separate Zenodo dataset only after a provider-by-provider redistribution review.
- GitHub contains no analytical bundle, raw data, credentials, local paths, internal AI documents, development logs, or inherited binary history.
- The public release version is `v2.0.0`, matching `CITATION.cff`, the Git tag, GitHub Release, Zenodo metadata, and release manifest.

## Dependency graph

```text
Zenodo account and ownership
            |
            v
Release scope and rights gate
            |
            v
Clean public export and validation
            |
            v
Reserve Zenodo DOI
            |
            v
Embed DOI and repository metadata
            |
            v
Create clean public GitHub repository
            |
            v
Build and hash release archives
            |
            v
Fresh-download replication audit
            |
            v
Human publication checkpoint
            |
            v
Publish Zenodo record and GitHub Release
```

## Tasks

### Task 1: Establish Zenodo ownership

**Description:** Create or identify the author's Zenodo account, preferably using ORCID and then linking GitHub. Account creation and authentication remain author-controlled actions.

**Acceptance criteria:**

- [ ] One Zenodo account is active and its email is verified when required.
- [ ] ORCID and GitHub are linked to the same Zenodo account without creating duplicates.
- [ ] Two-factor authentication is enabled on the linked ORCID or GitHub identity.
- [ ] The author is confirmed as the owner of the future deposit.

**Verification:**

- [ ] Zenodo dashboard opens and permits creation of a draft upload.
- [ ] Linked Accounts shows the intended ORCID and GitHub identities.

**Dependencies:** None.

### Task 2: Freeze the distributable scope and rights decision

**Description:** Define exactly which local files belong in the public software artifact, analytical bundle, and optional source-cache record. Reconcile every raw provider with its redistribution terms before any raw file is uploaded.

**Acceptance criteria:**

- [ ] Public code export is defined by an explicit path allowlist.
- [ ] Analytical bundle matches `config/analytical_bundle_manifest.csv` exactly.
- [ ] `_raw/v2` is excluded from the main deposit.
- [ ] Each optional raw source has an explicit `allowed`, `restricted`, or `link-only` redistribution verdict with a terms URL.

**Verification:**

- [ ] Manifest validation passes for the analytical bundle.
- [ ] A release inventory reports no files outside the allowlist.
- [ ] Secret, absolute-path, internal-document, and large-file scans pass.

**Dependencies:** Task 1 only for recording final ownership metadata; technical inventory can begin independently.

### Task 3: Assemble and test a clean public repository tree

**Description:** Export V2 into an isolated staging directory with V2 as the repository root. Add the R Companion under `r-companion/` and expose its rendered HTML through `docs/index.html` for GitHub Pages. Adjust only packaging paths and links; do not change estimands, samples, model contracts, or reference values.

**Acceptance criteria:**

- [ ] The staging tree contains only public package files and approved generated artifacts.
- [ ] The R Companion opens locally and all repository-relative links resolve.
- [ ] No path points above the repository root.
- [ ] The current project worktree and `Replication Package/V1` remain unchanged.

**Verification:**

- [ ] Public-file allowlist test passes.
- [ ] Runner interface and portability tests pass from the staging tree.
- [ ] R Companion link and HTML structure checks pass.
- [ ] `git diff --no-index` confirms that scientific code differs from V2 only where packaging paths require it.

**Dependencies:** Task 2.

### Task 4: Reserve the Zenodo DOI and finalize metadata

**Description:** Create an unpublished Zenodo draft, reserve its DOI, and incorporate the reserved identifier into the release metadata before the final archives and Git tag are created.

**Acceptance criteria:**

- [ ] A DOI is reserved but the Zenodo record remains unpublished.
- [ ] `CITATION.cff` includes DOI, repository URL, release date, and version.
- [ ] README includes citation instructions, DOI badge, bundle download instructions, and R Companion link.
- [ ] Zenodo metadata includes title, abstract, author, ORCID, affiliation, keywords, license information, related repository URL, and dissertation relationship.

**Verification:**

- [ ] `CITATION.cff` validates against CFF 1.2.0.
- [ ] Reserved DOI is identical across all metadata files.
- [ ] Zenodo preview displays the intended citation and contributor order.

**Dependencies:** Tasks 1 and 3.

### Task 5: Create the clean public GitHub repository

**Description:** Initialize Git in the isolated staging tree, create a single reviewed release-history baseline, and create the new public repository with GitHub CLI. The existing `ILO_IA_INDEX_PENAD` remote is never modified.

**Acceptance criteria:**

- [ ] Repository is created at `manoelbo/generative-ai-brazil-labor-replication` with default branch `main`.
- [ ] Initial history contains no file from the parent project outside the audited staging tree.
- [ ] Branch protection and a minimal issue/contact policy are configured where supported.
- [ ] GitHub Pages serves the R Companion from `docs/`.

**Verification:**

- [ ] Fresh anonymous clone succeeds.
- [ ] GitHub file-size and secret scans pass.
- [ ] README, license, citation metadata, and Pages URL render correctly.

**Dependencies:** Task 4.

### Task 6: Build deterministic release artifacts

**Description:** Create the code archive, analytical-bundle archive, standalone companion HTML, checksums, and machine-readable release manifest from the audited sources. Do not create a monolithic archive containing the raw cache.

**Acceptance criteria:**

- [ ] Every published file has a SHA-256 digest, byte size, media type, and role.
- [ ] Archives unpack without warnings and preserve required relative paths.
- [ ] Analytical files match the signed bundle manifest after unpacking.
- [ ] No archive contains caches, credentials, absolute paths, or unapproved raw sources.

**Verification:**

- [ ] `sha256sum` or `shasum -a 256` verifies all entries in `SHA256SUMS.txt`.
- [ ] Archive listing matches the release allowlist exactly.
- [ ] A second archive build is content-equivalent; any unavoidable container-hash difference is documented.

**Dependencies:** Tasks 3 and 4.

### Task 7: Audit the exact downloadable release candidate

**Description:** Validate the artifacts that will actually be uploaded, not the source directories from which they were built. Use a fresh isolated directory and no network during `reproduce`.

**Acceptance criteria:**

- [ ] Fresh clone plus downloaded analytical bundle completes the registered offline reproduction.
- [ ] All reference, narrative-claim, Python-R, and scientific-gate validations pass.
- [ ] Two consecutive reproductions are deterministic under the locked environment.
- [ ] The R Companion opens from both GitHub Pages and the downloaded standalone HTML.

**Verification:**

- [ ] Full V2 test suite passes in the isolated release tree.
- [ ] `run_manifest.json` records the expected source commit and bundle hashes.
- [ ] Generated publication set equals the registered 53-artifact set.
- [ ] No reference file is modified by the public runner.

**Dependencies:** Tasks 5 and 6.

### Checkpoint: Author review before irreversible publication

- [ ] Author reviews the public GitHub repository.
- [ ] Author reviews the Zenodo preview and exact file list.
- [ ] Author confirms author name, ORCID, affiliation, title, abstract, license statements, and citation.
- [ ] Author explicitly authorizes publication of the Zenodo record.

### Task 8: Publish and verify the release

**Description:** Publish the approved Zenodo record, tag the identical Git commit as `v2.0.0`, create the GitHub Release, and verify all permanent links and citations.

**Acceptance criteria:**

- [ ] Zenodo DOI resolves publicly and every file downloads successfully.
- [ ] Git tag and GitHub Release identify the exact commit recorded by Zenodo.
- [ ] GitHub and Zenodo link to each other.
- [ ] README and `CITATION.cff` contain the active DOI.

**Verification:**

- [ ] Anonymous DOI resolution and archive download succeed.
- [ ] Downloaded hashes match `SHA256SUMS.txt`.
- [ ] A final smoke reproduction succeeds from the public URLs.
- [ ] Release evidence records URLs, DOI, commit, tag, file hashes, and publication timestamp.

**Dependencies:** Task 7 and explicit author approval.

### Task 9: Decide whether to archive the frozen raw-source cache

**Description:** Treat `_raw/v2` as a separate preservation decision. If every included source permits redistribution, publish a separately licensed Zenodo dataset related to the main replication-package DOI. Otherwise retain only hashes, provider URLs, vintages, and acquisition instructions.

**Acceptance criteria:**

- [ ] Every source has a documented rights decision.
- [ ] No provider material is presented as MIT-licensed.
- [ ] A separate DOI is used if the raw cache is published.

**Verification:**

- [ ] Raw archive hashes match `raw_cache_manifest.json` after download.
- [ ] The main `reproduce` release remains usable without the raw-cache record.

**Dependencies:** Task 8; may be deferred indefinitely.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Current repository contains unrelated history and large blobs | High | Build a clean isolated repository from an explicit allowlist; never push the current `.git`. |
| Raw-source redistribution terms differ from the MIT code license | High | Exclude raw sources from the main record and perform a provider-level rights review. |
| Zenodo publication creates a persistent scholarly record | High | Reserve DOI early, keep the record as a draft, and require an explicit author checkpoint before publishing. |
| GitHub and Zenodo artifacts drift | High | Record the exact Git commit and file hashes in `RELEASE_MANIFEST.json`; validate downloaded artifacts. |
| Large archives are corrupted or incomplete | Medium | Use source manifests, SHA-256 checks, resumable upload where available, and post-upload downloads. |
| R Companion links break after relocation | Medium | Add repository-relative link tests and verify both local and GitHub Pages versions. |
| A future update silently replaces the released evidence | High | Use new Git tags and Zenodo versions; never overwrite a published scientific version. |

## Definition of done

- The public GitHub repository is a clean, navigable mirror of the approved package code.
- The Zenodo DOI resolves to the exact audited code, analytical bundle, R Companion, checksums, and release manifest.
- A researcher can clone the repository, download the bundle, verify hashes, and run offline `reproduce` from the published instructions.
- The raw-source cache is either separately and lawfully archived or explicitly excluded with complete acquisition metadata.
- The current private project history, V1, internal documents, and local credentials were never published or modified.
