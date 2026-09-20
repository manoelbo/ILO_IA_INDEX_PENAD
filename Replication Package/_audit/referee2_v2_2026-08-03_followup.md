# Independent Referee 2 Follow-up — Replication Package V2

**Audit date:** 2026-08-03  
**Review round:** Narrow follow-up to the release-blocking output-path finding  
**Audit posture:** Read-only and adversarial  
**Verdict:** **PASS — RELEASE RECOMMENDED.**

## 1. Scope

This follow-up reviews only the remediation requested by the initial Referee 2 report:

- the final output-path safety implementation in `V2/run_replication.py`;
- its regression tests in `V2/tests/test_run_replication.py`;
- the clarification in `V2/README.md` and `V2/DATA_AVAILABILITY.md`;
- the final-code receipt at `V2/provenance/output_path_safety_2026-08-03.json`; and
- whether this pre-execution-only change requires the retained scientific outputs to be re-estimated.

The audited external inputs and retained outputs remain:

| Alias | Absolute path |
|---|---|
| `BUNDLE` | `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/Replication Package/_bundle/v2` |
| `RAW` | `/Users/manebrasil/Documents/Projects/Dissetação Mestrado/Replication Package/_raw/v2` |
| `FULL` | `/private/tmp/v2-full-release-with-billing` |
| `ISOLATED` | `/private/tmp/v2-release-isolated.7DKpzS/reproduce-1` |

No public-package file was edited by this review. The only new audit artifact is this report.

## 2. Resolution of the release blocker

### Finding

**The blocker is fixed.**

`run_replication.py:1397-1403` now defines a symmetric path-overlap predicate covering equality and containment in both directions. `validate_output_dir` at `run_replication.py:1406-1440` resolves the destination and each supplied external input root, then rejects overlap with both the analytical data directory and raw-source directory.

The public entry point resolves `raw_dir` and `data_dir` and passes both to the validator at `run_replication.py:1577-1585`. This occurs before target resolution, DAG construction, preflight, output preparation, deletion handling, temporary runtime creation, input staging, or execution.

For a disjoint destination, the validator still returns the same canonical `output_dir.expanduser().resolve()` value. The new behavior is therefore a pure pre-execution rejection guard.

## 3. Required relationship matrix

The official regression test at `tests/test_run_replication.py:265-297` parametrizes all six mandatory cases with separate data and raw fixture parents. The focused official set passed:

```text
10 passed, 14 deselected in 1.20s
```

I also exercised the validator directly in an independent temporary directory. Results were:

| Input root | Output relationship | Result |
|---|---|---|
| Analytical data | Equal | Rejected |
| Analytical data | Descendant | Rejected |
| Analytical data | Ancestor | Rejected |
| Raw sources | Equal | Rejected |
| Raw sources | Descendant | Rejected |
| Raw sources | Ancestor | Rejected |
| Analytical data through symlink alias | Descendant | Rejected |
| Raw sources through symlink alias | Descendant | Rejected |
| Disjoint sibling output | Disjoint | Accepted without creating it |

The symlink regression in the public suite is at `tests/test_run_replication.py:300-312`; the disjoint positive control is at `tests/test_run_replication.py:315-325`. The implementation is generic across both external roots, and the independent probe confirmed aliases for both data and raw.

## 4. Rejection occurs before every execution or mutation step

The public integration test at `tests/test_run_replication.py:328-374` replaces DAG construction, preflight, output preparation, runtime materialization, full-rebuild preparation, and DAG execution with sentinels. `main()` rejects the overlap with no sentinel call and without creating the destination.

I repeated this adversarially for `--target all --mode full`, additionally instrumenting:

- `resolve_target`;
- `build_dag`;
- `preflight`;
- `prepare_output_directory`;
- `tempfile.TemporaryDirectory`;
- `materialize_execution_root`;
- `prepare_full_rebuild_runtime`;
- `run_dag`;
- `copy_runtime_results`; and
- `subprocess.run`.

The result was `downstream_calls=[]`, the expected `ValueError`, and `output_created=false`. Component staging cannot be reached because both DAG construction and execution remain downstream of the rejection.

The original exploit geometry was also retested against the real frozen roots. A nonexistent output descendant under `BUNDLE` failed at `validate_output_dir`; the corresponding descendant under `RAW` failed at the same decision point. Both candidates remained absent.

## 5. Valid real configurations still pass

The current validator accepts both retained output roots as disjoint from `BUNDLE` and `RAW`. Independent dry runs on the final code also passed without creating output:

### Reproduce dry run

```text
status: PASS
DAG nodes: 46
analytical bundle files: 161
analytical bundle manifest SHA-256:
e650c7c27084884bc2824753104cf785cdec4846a23618d2660900703eb019c8
movement partitions: 77
R: 4.4.1, 73 locked packages
reference artifacts: 267
reference signature: valid
```

### Full dry run

```text
status: PASS
DAG nodes: 54
official archives: 195
raw-cache files: 381 declared, 381 present, 0 missing
movement partitions: 77
R: 4.4.1, 73 locked packages
reference artifacts: 267
reference signature: valid
```

The explicit billing-project argument was supplied for the full dry run. As expected for `--dry-run`, no acquisition, estimation, rendering, or output creation occurred.

## 6. Documentation

The documentation now states the implemented invariant exactly:

- `README.md:84-89` says the output cannot equal, contain, or be contained by either external input root.
- `DATA_AVAILABILITY.md:14-20` repeats the rule and explicitly covers symlink overlap.
- `README.md:143-156` clarifies that the complete test suite expects the analytical bundle mounted or copied at `data/`, while public runs may keep it external and use `--data-dir`.

This closes both the release blocker and the minor verification-command ambiguity from the first report.

## 7. Final-code identity receipt

`provenance/output_path_safety_2026-08-03.json` is internally coherent. Every recorded file hash was independently recomputed and matched:

| File | SHA-256 |
|---|---|
| `DATA_AVAILABILITY.md` | `5d2b04fe76e7344f9ef7bf63787b961ea9ad0c30595fe92bf75beb798dbe7e4d` |
| `README.md` | `3f6606ad704bde9142821ee68b8d36ec615a79a85332d0b29145b2f7c223f065` |
| `code/caged/panel/build_panel.py` | `c6a25555c9c48ce8bedf0071ca9a035fa14a60b4c7459ca4985d3ef6f1bd01e1` |
| `run_replication.py` | `ecb87349436cee5daf4acd3f5d6d47f4c01b533204335c7a704b2a72268b6fc3` |
| `tests/test_run_replication.py` | `80ee4b2c879ec0c753dc5f8da80af2fef6454d0aec7e5553cc5ea084dc719e7c` |
| Signed reference manifest | `35d9084497f070b9333a8df3cdf6701c966a385dc68094a87c7fd8a9f4c9d451` |
| Full run manifest | `0f5fcceb3e6c4468b084b65c656568b18639854672a8e9ff60cda490c65fa017` |
| Isolated reproduce run manifest | `7563cfb8b04d36ba8ff480e1492ede180412816fdbaab49855c895d280075464` |

The receipt itself hashes to:

```text
f3fc0a75f5df09ca38287a2c7e46d0d88d2e3b0c92bc5601b60ed23ece522a6d
```

Its test inventory is consistent with the current tree: an independent collection found exactly **443 tests**. The author-provided complete-suite evidence reports **443 passed with 5 warnings** in 115.78 seconds after temporarily mounting the bundle. The focused 10-test result was independently reproduced in this review.

The public tree contains no cache or local-environment directory, and `data/` contains only `.gitignore`. V1's frozen contract was independently recomputed as 310 file records with the exact digest recorded in the receipt:

```text
0cf0fbb567ce7d7794808bd44f9ce9a89a2d3954f1162cf9311e0abfa90fe8f4
```

## 8. Scientific rerun determination

**No scientific or output-artifact rerun is required for this remediation.**

This conclusion follows from control flow, not convenience:

1. The remedial branch executes before target resolution, DAG construction, preflight, staging, data construction, estimation, rendering, comparison, and serialization.
2. It either raises on an unsafe geometry or returns the same resolved output path previously used for a safe geometry.
3. No estimator, analytical contract, input, renderer, or artifact serializer was changed by the audited remediation.
4. Both retained output geometries remain valid under the new rule.
5. Their run-manifest hashes are unchanged and match the final-code receipt.
6. The independently rerun reproduce and full preflights traverse the expected 46- and 54-node DAGs on the final entry point.

Re-estimating scientific models cannot add evidence about a predicate that executes before those models exist. The new final-code identity receipt is the proportionate provenance bridge between the unchanged retained artifacts and the corrected public entry point.

This software-release decision does not relax the package's scientific interpretation boundaries. Failed pretrends, non-PSD diagnostics, support stops, and the exploratory status of the reported CAGED/DDD estimates remain exactly as documented in the initial audit.

## 9. Follow-up verdict

**PASS — RELEASE RECOMMENDED.**

The sole release blocker from the initial Referee 2 report has been fully addressed. All six required equality/containment relationships are rejected; symlink aliases cannot bypass the rule; disjoint outputs remain accepted; rejection precedes every mutating or executable step; the real reproduce and full dry runs pass; the documentation states both the path invariant and test-data requirement; and the final-code receipt validates against the current files and retained output manifests.

**Major concerns remaining:** None.  
**Minor concerns remaining within this follow-up scope:** None.  
**Release authorization:** Recommended, subject to the unchanged scientific caveats already carried by V2.
