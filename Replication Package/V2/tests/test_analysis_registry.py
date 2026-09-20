from __future__ import annotations

from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

import run_replication as runner


def _dag_ids(*, target: str, mode: str) -> set[str]:
    return {
        node.node_id
        for node in runner.build_dag(
            target=target,
            mode=mode,
            raw_dir=runner.DEFAULT_RAW_DIR,
            data_dir=runner.DEFAULT_DATA_DIR,
            output_dir=Path("/tmp/dissertation-replication-registry-test"),
        )
    }


def test_dag_matches_the_typed_analysis_registry_for_every_public_target() -> None:
    from registry import expected_node_ids

    for mode in ("reproduce", "full"):
        for target in ("all", *runner.COMPONENTS):
            assert _dag_ids(target=target, mode=mode) == expected_node_ids(
                target=target,
                mode=mode,
            )


def test_caged_render_outputs_are_derived_from_the_manuscript_registry() -> None:
    from registry import expected_publication_outputs

    phase8b = set(runner._phase8b_render_outputs())
    registered = expected_publication_outputs(
        component="caged",
        include_markdown_pairs=True,
    )
    canaries = "figures/figure_5_2_3_3_canaries_22_25_wage.png"

    assert phase8b == (registered - {canaries}) | {
        "backing_data/figure_5_2_6_group_outcome_forest.csv",
        "RENDERIZACAO_8B.md",
    }


def test_orphaned_narrative_diagnostics_are_first_class_caged_nodes() -> None:
    expected = {
        "audit_wage_composition",
        "audit_occupation_concentration",
        "audit_exposure_and_control",
        "audit_transfer_share",
    }

    assert expected <= _dag_ids(target="caged", mode="reproduce")
