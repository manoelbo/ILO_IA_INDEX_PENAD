from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPORT = PACKAGE_ROOT / "COMPARACAO_V1_V2.md"


def test_v1_v2_comparison_covers_required_changes_and_mechanisms() -> None:
    text = REPORT.read_text(encoding="utf-8")
    required_phrases = {
        "MOV + FOR − EXC",
        "Wage missingness",
        "Wage winsorization",
        "Contemporary controls",
        "Count estimator",
        "Treatment classification",
        "Separation mechanisms",
        "Cumulative net-flow proxy",
        "Hourly wage and schedules",
        "Establishment size",
        "Public/private falsification",
        "Anthropic comparison",
    }

    assert all(phrase in text for phrase in required_phrases)


def test_v1_v2_comparison_contains_the_complete_task_14_gate() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "Task 14 gate" in text
    assert "-0.030879 (0.026288)" in text
    assert "-0.041658 (0.025418)" in text
    assert "-0.020706 (0.013992)" in text
    assert "-0.659661 (0.377251)" in text
    assert "Only the admission-wage result crosses the 5%" in text
