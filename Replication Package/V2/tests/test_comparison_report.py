from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DESIGN = PACKAGE_ROOT / "RESEARCH_DESIGN.md"


def test_public_design_covers_required_robustness_and_mechanisms() -> None:
    text = " ".join(DESIGN.read_text(encoding="utf-8").lower().split())
    required_phrases = {
        "wage missingness",
        "winsorization",
        "contemporary controls",
        "count-estimator",
        "treatment-classification",
        "separation flows",
        "cumulative net-flow proxy",
        "hourly wages and schedules",
        "establishment size",
        "public/private falsification",
        "alternative exposure measures",
    }

    assert all(phrase in text for phrase in required_phrases)


def test_public_design_preserves_the_identification_gate() -> None:
    text = " ".join(DESIGN.read_text(encoding="utf-8").split())

    assert "do not pass the complete identifying diagnostics" in text
    assert "exploratory treated-versus-control" in text
    assert "not an unqualified causal effect" in text
