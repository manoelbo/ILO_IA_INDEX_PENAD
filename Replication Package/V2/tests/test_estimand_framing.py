"""Guard the estimand framing that Phase 8A corrected.

Internal development notes used to juxtapose the static headline
coefficient (-0.050740, averaged over `t = 0…+41` against the whole
pre-period) with the statement that the HonestDiD interval does not exclude
zero at `M = 0`. Read together, that says the headline is fragile. It is not
what the numbers say: the sensitivity analysis targets the event-study
average over `t = 0…+23` normalised against November 2022, whose unadjusted
interval already includes zero.

Nothing about either number is wrong. The juxtaposition is what misleads, so
these tests fail if either claim reappears without its window and estimand.
"""

from __future__ import annotations

import re
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ("RESEARCH_DESIGN.md",)
STATIC_HEADLINE = "-0.050740"
# Only inferential claims are guarded. A note about how long the HonestDiD
# node takes to run is not a claim about identification, so mentioning the
# method by name is not the trigger; asserting something about zero is.
SENSITIVITY_MARKERS = (
    "M = 0",
    "M=0",
    "exclude zero",
    "excludes zero",
    "excluding zero",
)
EVENT_STUDY_TARGET = "average_post_event_time_0_to_23"
EVENT_STUDY_WORDS = ("event-study", "event study")


def blocks(text: str) -> list[str]:
    """Paragraphs, plus every markdown table row as its own block.

    A table row is a self-contained claim: a reader scanning the comparison
    table sees one row at a time, so the qualification has to be inside it.
    """

    found: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        rows = [
            line
            for line in paragraph.splitlines()
            if line.lstrip().startswith("|")
        ]
        if rows:
            found.extend(rows)
        else:
            found.append(paragraph)
    return [block for block in found if block.strip()]


def read(document: str) -> str:
    return (PACKAGE_ROOT / document).read_text(encoding="utf-8")


def test_static_headline_always_declares_its_estimand() -> None:
    for document in DOCUMENTS:
        for block in blocks(read(document)):
            if STATIC_HEADLINE not in block:
                continue
            assert "static" in block.lower(), (
                f"{document}: the static headline {STATIC_HEADLINE} appears "
                "without saying it is the static estimand:\n"
                f"{block.strip()}"
            )


def test_sensitivity_claims_always_declare_their_target() -> None:
    for document in DOCUMENTS:
        for block in blocks(read(document)):
            if not any(marker in block for marker in SENSITIVITY_MARKERS):
                continue
            lowered = block.lower()
            assert EVENT_STUDY_TARGET in block, (
                f"{document}: a sensitivity claim omits the target estimand "
                f"{EVENT_STUDY_TARGET}:\n{block.strip()}"
            )
            assert any(word in lowered for word in EVENT_STUDY_WORDS), (
                f"{document}: a sensitivity claim omits the event-study "
                f"window it refers to:\n{block.strip()}"
            )


def test_guard_rejects_the_original_juxtaposition() -> None:
    """The guard must fail on the text it was written to prevent."""

    original = (
        "The principal no-control estimates are -0.053772 for admissions "
        "and -0.050740 for real admission wage. Only admission wage rejects "
        "at 5%. The wage HonestDiD interval does not exclude zero even at "
        "`M = 0`."
    )
    triggers = [
        block
        for block in blocks(original)
        if any(marker in block for marker in SENSITIVITY_MARKERS)
    ]
    assert triggers, "the guard must recognise the original claim"
    assert all(EVENT_STUDY_TARGET not in block for block in triggers)
    assert all("static" not in block.lower() for block in blocks(original))


def test_documents_state_that_the_two_estimands_differ() -> None:
    for document in DOCUMENTS:
        text = read(document)
        assert EVENT_STUDY_TARGET in text or "event-study estimand" in text
        assert "-0.015363" in text, (
            f"{document}: the event-study post average must be stated "
            "explicitly so the reader can see it is a different number "
            "from the static headline"
        )
