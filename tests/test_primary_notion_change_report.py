import sys
import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from build_primary_notion_change_report import (
    build_artifacts,
    canonicalize_notion_snapshot,
    choose_claim_action,
    load_tsv,
    summarize_primary_rows,
    unique_anchor,
)


class PrimaryNotionChangeReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.run_dir = (
            ROOT
            / "references"
            / "claim_audit"
            / "runs"
            / "codex_sol_max"
            / "20260807T141925Z_current"
        )

    def test_snapshot_canonicalization_ignores_only_expiring_image_parameters(self) -> None:
        old = (
            "Texto estável\n"
            "![](https://prod-files-secure.s3.us-west-2.amazonaws.com/a/image.png?X-Amz-Date=OLD)\n"
        )
        refreshed = (
            "Texto estável\n"
            "![](https://prod-files-secure.s3.us-west-2.amazonaws.com/a/image.png?X-Amz-Date=NEW)\n"
        )
        changed = refreshed.replace("Texto estável", "Texto alterado")

        self.assertEqual(
            canonicalize_notion_snapshot(old),
            canonicalize_notion_snapshot(refreshed),
        )
        self.assertNotEqual(
            canonicalize_notion_snapshot(old),
            canonicalize_notion_snapshot(changed),
        )

    def test_snapshot_canonicalization_compares_dissertation_body_not_wrapper_metadata(self) -> None:
        old = '<properties>{"Resumo por IA":"old"}</properties><content>Texto estável</content>'
        refreshed = '<properties>{"Resumo por IA":"new"}</properties><content>Texto estável</content>'
        changed = '<properties>{"Resumo por IA":"new"}</properties><content>Texto alterado</content>'

        self.assertEqual(
            canonicalize_notion_snapshot(old),
            canonicalize_notion_snapshot(refreshed),
        )
        self.assertNotEqual(
            canonicalize_notion_snapshot(old),
            canonicalize_notion_snapshot(changed),
        )

    def test_primary_summary_counts_rows_claims_occurrences_and_verdicts(self) -> None:
        rows = [
            {
                "row_id": "ROW-1",
                "claim_id": "CLM-1",
                "occurrence_id": "CIT-1",
                "fact_checked": "SUPPORTED",
                "issue_codes": "",
                "needs_new_source": "false",
            },
            {
                "row_id": "ROW-2",
                "claim_id": "CLM-2",
                "occurrence_id": "CIT-2",
                "fact_checked": "PARTIALLY_SUPPORTED",
                "issue_codes": "PARTIAL_SCOPE",
                "needs_new_source": "true",
            },
            {
                "row_id": "ROW-3",
                "claim_id": "CLM-2",
                "occurrence_id": "CIT-3",
                "fact_checked": "OVERSTATED",
                "issue_codes": "GENERALIZATION_OVERCLAIM",
                "needs_new_source": "true",
            },
        ]

        summary = summarize_primary_rows(rows)

        self.assertEqual(summary["rows"], 3)
        self.assertEqual(summary["unique_claims"], 2)
        self.assertEqual(summary["unique_occurrences"], 3)
        self.assertEqual(summary["verdicts"]["SUPPORTED"], 1)
        self.assertEqual(summary["non_supported_rows"], 2)
        self.assertEqual(summary["non_supported_claims"], 1)
        self.assertEqual(summary["claims_needing_new_source"], 1)

    def test_grouped_claim_prefers_citation_membership_when_one_source_supports_it(self) -> None:
        rows = [
            {
                "citation_key": "supporting_source",
                "fact_checked": "SUPPORTED",
                "issue_codes": "",
                "needs_new_source": "false",
            },
            {
                "citation_key": "overstated_source",
                "fact_checked": "OVERSTATED",
                "issue_codes": "GENERALIZATION_OVERCLAIM",
                "needs_new_source": "true",
            },
        ]

        action = choose_claim_action(rows)

        self.assertEqual(action["change_type"], "CITATION_MEMBERSHIP")
        self.assertEqual(action["supported_keys"], ["supporting_source"])
        self.assertEqual(action["challenged_keys"], ["overstated_source"])

    def test_unique_anchor_returns_a_single_exact_match(self) -> None:
        corpus = (
            "Primeiro parágrafo sem relação. "
            "O ajuste de Benjamini e Hochberg controla a taxa de falsas descobertas. "
            "Último parágrafo sem relação."
        )
        excerpt = "O ajuste de Benjamini e Hochberg controla a taxa de falsas descobertas."

        anchor, count = unique_anchor(excerpt, corpus)

        self.assertEqual(count, 1)
        self.assertIn(anchor, corpus)
        self.assertGreaterEqual(len(anchor.split()), 6)

    def test_real_primary_inventory_matches_frozen_contract(self) -> None:
        rows = load_tsv(self.run_dir / "claim_inventory_audited_current.tsv")

        summary = summarize_primary_rows(rows)

        self.assertEqual(summary["rows"], 213)
        self.assertEqual(summary["unique_claims"], 175)
        self.assertEqual(summary["unique_occurrences"], 59)
        self.assertEqual(
            summary["verdicts"],
            {
                "SUPPORTED": 164,
                "PARTIALLY_SUPPORTED": 32,
                "OVERSTATED": 14,
                "CONTRADICTED": 1,
                "NOT_VERIFIABLE": 2,
            },
        )
        self.assertEqual(summary["non_supported_rows"], 49)
        self.assertEqual(summary["non_supported_claims"], 45)
        self.assertEqual(summary["claims_needing_new_source"], 22)

    def test_generated_artifacts_cover_primary_findings_and_citation_hygiene(self) -> None:
        result = build_artifacts(ROOT, write=False)
        queue = result["queue"]
        status = result["citation_status"]
        row_coverage = result["row_coverage"]

        self.assertEqual(len({row["change_id"] for row in queue}), len(queue))
        self.assertTrue(all(row["approval_status"] == "PROPOSED" for row in queue))
        self.assertEqual(len(status), 60)
        self.assertEqual(sum(row["link_in_text"] == "AUSENTE" for row in status), 29)
        self.assertEqual(sum(row["citation_in_references"] == "NÃO" for row in status), 9)
        self.assertEqual(result["reference_summary"]["target"], 23)
        self.assertEqual(result["reference_summary"]["add"], 9)
        self.assertEqual(result["reference_summary"]["remove"], 1)
        self.assertFalse(result["semantic_match"])
        self.assertEqual(result["deferred_occurrences"], ["CIT-CUR-002"])
        self.assertEqual(
            result["deferred_row_ids"], ["ROW-CUR-0005", "ROW-CUR-0006"]
        )
        deferred_actions = [
            row for row in queue if row["proposal_mode"] == "DEFERRED_DEEP_AUDIT"
        ]
        self.assertEqual(len(deferred_actions), 1)
        self.assertIn("ROW-CUR-0006", deferred_actions[0]["covered_row_ids"])

        non_supported = {
            row["row_id"]
            for row in result["primary_rows"]
            if row["fact_checked"] != "SUPPORTED"
        }
        supported_mismatch = {
            row["row_id"]
            for row in result["primary_rows"]
            if row["fact_checked"] == "SUPPORTED"
            and "PDF_VERSION_MISMATCH" in row["issue_codes"]
        }
        self.assertEqual(len(non_supported), 49)
        self.assertEqual(len(supported_mismatch), 19)
        self.assertTrue(non_supported <= set(row_coverage))
        self.assertTrue(supported_mismatch <= set(row_coverage))
        self.assertEqual(len(row_coverage), 213)

        notion_actions = [
            row for row in queue if row["target_system"] in {"NOTION", "BOTH"}
        ]
        self.assertTrue(
            all(int(row["expected_match_count"]) == 1 for row in notion_actions)
        )


if __name__ == "__main__":
    unittest.main()
