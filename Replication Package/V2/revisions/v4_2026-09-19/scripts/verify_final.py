"""Verify the Notion readback and frozen sources without estimating models."""
import concurrent.futures
import hashlib
import json
import re
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
before = (OUT / "source/notion_before.md").read_text()
after = (OUT / "notion_after.md").read_text()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalize(text):
    # Notion escapes literal Markdown punctuation on serialization.
    text = re.sub(r"\\([\[\]*<>])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def cells(table):
    return [normalize(cell) for cell in re.findall(r"<td[^>]*>(.*?)</td>", table, re.S)]


def section(text, start, end):
    return text[text.index(start):text.index(end)]


def canonical(text):
    return normalize(re.sub(r"(https://[^\s)?]+)\?[^\s)]+", r"\1", text))


actual_tables = [cells(table) for table in re.findall(r"<table[^>]*>.*?</table>", after, re.S)]
table_matches = {}
for source in sorted((OUT / "tables").glob("*.md")):
    expected = cells(source.read_text())
    table_matches[source.name] = sum(table == expected for table in actual_tables)
assert all(count == 1 for count in table_matches.values()), table_matches

unchanged = {
    label: canonical(section(before, start, end)) == canonical(section(after, start, end))
    for label, start, end in [
        ("section_2", "# 2 Mensuração", "# 3 Análise"),
        ("section_3", "# 3 Análise", "# 4 Estratégia"),
    ]
}
assert all(unchanged.values()), unchanged
hashes = json.loads((OUT / "evidence/source_hashes.json").read_text())
hash_checks = {name: digest((ROOT / name).read_bytes()) == expected for name, expected in hashes.items()}
assert all(hash_checks.values())

conclusion = section(after, "# 7 Conclusão", "## Apêndice A")
paragraphs = [line for line in conclusion.splitlines() if line.strip() and not line.startswith(("#", "**REVISAR", "<empty-block", "---"))]
assert len(paragraphs) == 7, len(paragraphs)
counts = {
    "tables": len(actual_tables),
    "images_including_preexisting_empty_block": len(re.findall(r"^!\[", after, re.M)),
    "equations": after.count("$$") // 2,
    "review_markers": len(re.findall(r"^\*\*REVISAR COM MANÉ", after, re.M)),
    "manual_markers": len(re.findall(r"^\*\*PENDÊNCIA MANUAL", after, re.M)),
    "conclusion_paragraphs": len(paragraphs),
}
assert counts == {"tables": 40, "images_including_preexisting_empty_block": 40, "equations": 5, "review_markers": 10, "manual_markers": 12, "conclusion_paragraphs": 7}, counts
assert "2 dos 100 contrastes salariais" not in after
assert not re.search(r"^### 5\.2\.\d", after, re.M)

original_image_paths = re.findall(r"^!\[.*?\]\(([^)?]*)", before, re.M)
final_image_paths = re.findall(r"^!\[.*?\]\(([^)?]*)", after, re.M)
assert all(final_image_paths.count(url) == original_image_paths.count(url) for url in set(original_image_paths))

figures = json.loads((OUT / "evidence/figure_numbering.json").read_text())
for index in range(1, 4):
    filename = next((OUT / "figures").glob(f"figure_a_8_{index}_*.png"))
    figures.append({"old": "5.2.6", "new": f"A.8.{index}", "file": str(filename.relative_to(OUT))})


def check_image(figure):
    offset = after.index("**Figura " + figure["new"] + " —", after.index("### A.3 Sexo"))
    match = re.search(r"^!\[.*?\]\((.*?)\)", after[offset:], re.M)
    data = urllib.request.urlopen(match[1], timeout=60).read()
    local = OUT / figure["file"]
    target = OUT / "evidence/downloaded_final_images" / local.name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(data)
    result = {"number": figure["new"], "file": figure["file"], "bytes": len(data), "sha256": digest(data), "identical_to_local": data == local.read_bytes()}
    assert result["identical_to_local"], result
    return result


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    image_checks = list(pool.map(check_image, figures))

report = {
    "notion_page": "https://app.notion.com/p/3e0cc8ca461080c08ca1fe386472b72e",
    "snapshot_last_edited_at": json.loads((OUT / "notion_after.json").read_text())["page_last_edited_at"],
    "counts": counts,
    "generated_table_matches": table_matches,
    "unchanged_sections": unchanged,
    "frozen_numerical_source_hashes_match": hash_checks,
    "all_original_image_blocks_preserved": True,
    "uploaded_image_checks": image_checks,
    "remote_visual_inspection": "unavailable: browser control timed out; connector readback and downloaded-file verification completed",
    "manual_cleanup": "12 original image blocks remain in section 5.3, each marked M01-M12; appendix destinations are verified",
    "regressions_run": 0,
}
(OUT / "evidence/final_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"counts": counts, "tables_verified": len(table_matches), "images_verified": len(image_checks), "source_files_unchanged": len(hash_checks)}, indent=2))
