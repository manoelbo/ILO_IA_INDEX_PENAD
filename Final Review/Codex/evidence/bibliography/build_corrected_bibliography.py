#!/usr/bin/env python3
"""Create a review-only corrected bibliography without changing the source."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


CANONICAL_REPLACEMENTS = {
    "brynjolfsson_generative_2024": """@article{brynjolfsson_generative_2024,
\ttitle = {Generative {AI} at Work},
\tauthor = {Brynjolfsson, Erik and Li, Danielle and Raymond, Lindsey},
\tjournaltitle = {The Quarterly Journal of Economics},
\tvolume = {140},
\tnumber = {2},
\tpages = {889--942},
\tdate = {2025-05},
\tdoi = {10.1093/qje/qjae044},
\turl = {https://academic.oup.com/qje/article/140/2/889/7990658},
\turldate = {2026-07-25},
\tfile = {PDF:pdfs/brynjolfsson_generative_2024.pdf:application/pdf},
}
""",
    "dellacqua_navigating_2023": """@article{dellacqua_navigating_2023,
\ttitle = {Navigating the Jagged Technological Frontier: Field Experimental Evidence of the Effects of Artificial Intelligence on Knowledge Worker Productivity and Quality},
\tauthor = {Dell'Acqua, Fabrizio and McFowland, III, Edward and Mollick, Ethan and Lifshitz, Hila and Kellogg, Katherine C. and Rajendran, Saran and Krayer, Lisa and Candelon, François and Lakhani, Karim R.},
\tjournaltitle = {Organization Science},
\tvolume = {37},
\tnumber = {2},
\tpages = {403--423},
\tdate = {2026-03},
\tdoi = {10.1287/orsc.2025.21838},
\turl = {https://pubsonline.informs.org/doi/10.1287/orsc.2025.21838},
\turldate = {2026-07-25},
\tfile = {PDF:pdfs/dellacqua_navigating_2023.pdf:application/pdf},
}
""",
    "bick_rapid_2024": """@article{bick_rapid_2024,
\ttitle = {The Rapid Adoption of Generative {AI}},
\tauthor = {Bick, Alexander and Blandin, Adam and Deming, David J.},
\tjournaltitle = {Management Science},
\tdate = {2026-01-20},
\tnote = {Articles in Advance},
\tdoi = {10.1287/mnsc.2025.02523},
\turl = {https://pubsonline.informs.org/doi/10.1287/mnsc.2025.02523},
\turldate = {2026-07-25},
\tfile = {PDF:pdfs/bick_rapid_2024.pdf:application/pdf},
}
""",
    "stanford_institute_for_human-centered_artificial_intelligence_ai_2026": """@report{stanford_institute_for_human-centered_artificial_intelligence_ai_2026,
\ttitle = {The {AI} Index 2026 Annual Report},
\tauthor = {Sajadieh, Sha and Fattorini, Loredana and Perrault, Raymond and Gil, Yolanda and Parli, Vanessa and Santarlasci, Lapo and Pava, Juan and Maslej, Nestor and Altman, Russ and Brynjolfsson, Erik and Brodley, Carla and Clark, Jack and Dignum, Virginia and Kumar, Vipin and Landay, James and Lyons, Terah and Manyika, James and Niebles, Juan Carlos and Shoham, Yoav and Tabassi, Elham and Wald, Russell and Walsh, Toby and Weld, Dan},
\tinstitution = {{AI} Index Steering Committee, Institute for Human-Centered Artificial Intelligence, Stanford University},
\tlocation = {Stanford, CA},
\ttype = {Annual Report},
\tdate = {2026-04},
\tpagetotal = {425},
\tdoi = {10.48550/arXiv.2606.15708},
\turl = {https://hai.stanford.edu/ai-index/2026-ai-index-report},
\turldate = {2026-07-25},
\tfile = {PDF:pdfs/stanford_institute_for_human-centered_artificial_intelligence_ai_2026.pdf:application/pdf},
}
""",
}


def _entry_pattern(key: str) -> re.Pattern[str]:
    return re.compile(
        rf"^@\w+\{{{re.escape(key)},\n.*?^\}}\n?",
        flags=re.MULTILINE | re.DOTALL,
    )


def extract_entry(text: str, key: str) -> str:
    matches = list(_entry_pattern(key).finditer(text))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one entry for {key}, found {len(matches)}")
    return matches[0].group(0)


def replace_entry(text: str, key: str, replacement: str) -> str:
    pattern = _entry_pattern(key)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one entry for {key}, found {len(matches)}")
    return pattern.sub(replacement, text, count=1)


def replace_in_entry(
    text: str,
    key: str,
    old: str,
    new: str,
) -> str:
    entry = extract_entry(text, key)
    if entry.count(old) != 1:
        raise ValueError(f"expected text exactly once in {key}: {old}")
    return replace_entry(text, key, entry.replace(old, new, 1))


def remove_field(text: str, key: str, field: str) -> str:
    entry = extract_entry(text, key)
    pattern = re.compile(
        rf"^\t{re.escape(field)}\s*=\s*.*,\n",
        flags=re.MULTILINE,
    )
    updated, count = pattern.subn("", entry, count=1)
    if count != 1:
        raise ValueError(f"expected field {field} exactly once in {key}")
    return replace_entry(text, key, updated)


def build_corrected_bibliography(source: str) -> str:
    corrected = source
    for key, replacement in CANONICAL_REPLACEMENTS.items():
        corrected = replace_entry(corrected, key, replacement)

    field_changes = (
        (
            "gmyrek_generative_2025",
            "\tisbn = {978-92-2-042184-0},",
            "\tisbn = {978-92-2-042185-7},",
        ),
        (
            "gmyrek_generative_2025",
            "\tpages = {72},",
            "\tpagetotal = {72},",
        ),
        (
            "benitez_mirror_2024",
            "\tinstitution = {Inter-American Development Bank},",
            "\tnumber = {IDB-WP-1624},\n"
            "\ttype = {IDB Working Paper},\n"
            "\tinstitution = {Inter-American Development Bank},",
        ),
        (
            "autor_putting_2013",
            "\tissue = {S1},",
            "\tnumber = {S1},",
        ),
        (
            "aldasoro_ai_2026",
            "\tpages = {40},",
            "\tpagetotal = {40},",
        ),
        (
            "aldasoro_ai_2026",
            "\tdate = {2026-01},",
            "\tdate = {2026-01-13},",
        ),
        (
            "klein_teeselink_generative_2025",
            "\tpages = {46},",
            "\tpagetotal = {46},",
        ),
        (
            "hosseini_maasoum_generative_2025",
            "\tpages = {109},",
            "\tpagetotal = {109},",
        ),
        (
            "chandar_tracking_2025",
            "\tpages = {23},",
            "\tpagetotal = {23},",
        ),
    )
    for key, old, new in field_changes:
        corrected = replace_in_entry(corrected, key, old, new)

    corrected = remove_field(
        corrected,
        "brynjolfsson_canaries_2025",
        "abstract",
    )
    return corrected


def bib_keys(text: str) -> list[str]:
    return re.findall(r"^@\w+\{([^,]+),", text, flags=re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.read_text(encoding="utf-8")
    corrected = build_corrected_bibliography(source)
    source_keys = bib_keys(source)
    corrected_keys = bib_keys(corrected)
    if source_keys != corrected_keys:
        raise ValueError("corrected bibliography changed entry keys or order")
    if len(corrected_keys) != 36:
        raise ValueError(f"expected 36 entries, found {len(corrected_keys)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(corrected, encoding="utf-8")
    print(f"Wrote {len(corrected_keys)} corrected entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
