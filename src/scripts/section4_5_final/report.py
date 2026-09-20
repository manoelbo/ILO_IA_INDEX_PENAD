"""Reports, manifest, and validation for the final Section 4/5 package."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import (
    AUDIT_DIR,
    CLASSIFICATION_PATH,
    EXPECTED_FIGURES,
    EXPECTED_TABLES,
    FIGURE_DIR,
    OUTPUT_ROOT,
    PANEL_PATH,
    SECTION5_3_ROOT,
    SOURCE_ROOT,
    TABLE_DIR,
)
from .formatting import markdown_table
from .section5_2_tables import validate_section5_2_outputs


def source_inventory() -> pd.DataFrame:
    rows = []
    for path in [PANEL_PATH, CLASSIFICATION_PATH]:
        if path.exists():
            rows.append(
                {
                    "source_file": str(path),
                    "relative_source": str(path.relative_to(OUTPUT_ROOT.parents[1])),
                    "bytes": path.stat().st_size,
                }
            )
    for path in sorted(SOURCE_ROOT.rglob("*")):
        if path.is_file() and path.suffix in {".csv", ".md", ".png"}:
            rel = path.relative_to(SOURCE_ROOT)
            if str(rel).startswith(("final_event_study/", "manual_occupation_groups_extension/", "connectivity_extension/", "result_evaluation/")):
                rows.append(
                    {
                        "source_file": str(path),
                        "relative_source": str(rel),
                        "bytes": path.stat().st_size,
                    }
                )
    for path in sorted(SECTION5_3_ROOT.rglob("*")):
        if path.is_file() and path.suffix in {".csv", ".md", ".png"}:
            rows.append(
                {
                    "source_file": str(path),
                    "relative_source": str(path.relative_to(OUTPUT_ROOT.parents[1])),
                    "bytes": path.stat().st_size,
                }
            )
    return pd.DataFrame(rows)


def write_navigation() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    figures = pd.DataFrame(
        {
            "Figura": EXPECTED_FIGURES,
            "Arquivo": [str((FIGURE_DIR / name).relative_to(OUTPUT_ROOT)) for name in EXPECTED_FIGURES],
            "Papel no texto": [
                "Estratégia empírica",
                "Pipeline de dados e crosswalk",
                "Diagnóstico nacional de event study",
                "Casos ocupacionais: admissões por idade",
                "Casos ocupacionais: salário real de admissão por idade",
                "Apêndice de conectividade",
                "Anexo B: sexo",
                "Anexo B: raça/cor",
                "Anexo B: escolaridade",
            ],
        }
    )
    tables = pd.DataFrame(
        {
            "Tabela": EXPECTED_TABLES,
            "Markdown": [f"tables/{stem}.md" for stem in EXPECTED_TABLES],
            "CSV": [f"tables/{stem}.csv" for stem in EXPECTED_TABLES],
        }
    )

    readme = f"""# Final Sections 4–5 Package

This directory curates the figures and tables used by the final writing of Sections 4 and 5. The occupation-case extension is generated independently under `outputs/section5_3_occupation_cases/`; this package copies its dissertation-facing artifacts without re-estimating them.

## Figures

{markdown_table(figures, list(figures.columns))}

## Tables

{markdown_table(tables, list(tables.columns))}

## Reading rule

Failed pretrends remain suggestive evidence or limitations. In the Section 5.2 tables, Panel A reports the DiD within each group and Panel B reports the formal DDD contrast against its complement; isolated Panel A stars do not establish heterogeneity. Section 5.3 is descriptive: its occupation paths are not occupation-specific causal effects. The retired four manual occupation groups remain only in Table B.5 for auditability and are excluded from the editorial Top 30.
"""
    (OUTPUT_ROOT / "README.md").write_text(readme, encoding="utf-8")

    index = f"""# Índice De Figuras E Tabelas

## Figuras

{markdown_table(figures, list(figures.columns))}

## Tabelas

{markdown_table(tables, list(tables.columns))}
"""
    (OUTPUT_ROOT / "figure_table_index.md").write_text(index, encoding="utf-8")


def write_manifest(generated_tables: dict[str, pd.DataFrame]) -> None:
    rows = []
    for stem in EXPECTED_TABLES:
        source_policy = (
            "copied from the audited Section 5.3 occupation-case package"
            if "occupation_case" in stem
            else (
                "legacy manual-group diagnostics retained for appendix audit only"
                if stem == "table_b_5_legacy_manual_group_diagnostics"
                else "curated from final dissertation_section4 outputs"
            )
        )
        rows.append(
            {
                "artifact": f"tables/{stem}.csv",
                "kind": "table_csv",
                "bytes": (TABLE_DIR / f"{stem}.csv").stat().st_size,
                "rows": len(generated_tables.get(stem, pd.DataFrame())),
                "source_policy": source_policy,
            }
        )
        rows.append(
            {
                "artifact": f"tables/{stem}.md",
                "kind": "table_markdown",
                "bytes": (TABLE_DIR / f"{stem}.md").stat().st_size,
                "rows": len(generated_tables.get(stem, pd.DataFrame())),
                "source_policy": source_policy,
            }
        )
    for name in EXPECTED_FIGURES:
        source_policy = (
            "copied from the audited Section 5.3 occupation-case package"
            if "occupation_cases" in name
            else "generated from final curated CSVs or methodology outline"
        )
        rows.append(
            {
                "artifact": f"figures/{name}",
                "kind": "figure_png",
                "bytes": (FIGURE_DIR / name).stat().st_size,
                "rows": "",
                "source_policy": source_policy,
            }
        )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(AUDIT_DIR / "manifest.csv", index=False)
    text = f"""# Manifesto Do Pacote Final

{markdown_table(manifest, list(manifest.columns))}
"""
    (OUTPUT_ROOT / "MANIFEST.md").write_text(text, encoding="utf-8")


def write_audit() -> None:
    inventory = source_inventory()
    inventory.to_csv(AUDIT_DIR / "source_inventory.csv", index=False)
    audit_text = f"""# Final-Package Audit

## Sources

The main causal results use:

- `outputs/dissertation_section4/final_event_study/`
- `outputs/dissertation_section4/connectivity_extension/`
- `outputs/dissertation_section4/result_evaluation/`

The descriptive occupation cases use:

- `outputs/section5_3_occupation_cases/`

The Section 4 descriptive tables also use:

- `data/output/painel_2b_ready.parquet`
- `outputs/treatment_scenario_grid/scenario_cbo_classification.csv`

The deprecated four manual occupation groups are used only to create the legacy diagnostic Table B.5. Their former bar chart, forest plot, heatmap, focal Software/IT table, and group tables are not headline artifacts.

## Inventory

- Tracked source files: {len(inventory)}
- Manifest: `MANIFEST.md`
- Index: `figure_table_index.md`
"""
    (AUDIT_DIR / "source_audit.md").write_text(audit_text, encoding="utf-8")


def validate_package() -> None:
    retired_headline_stems = {
        "figure_5_2_software_it_canaries_age.png",
        "figure_5_3_occupation_group_comparison.png",
        "figure_5_4_group_outcome_forest.png",
        "figure_5_5_heterogeneity_heatmap.png",
        "table_5_3_software_it_young_heterogeneity",
        "table_5_4_1_occupation_group_main_results",
        "table_5_4_2_occupation_group_heterogeneity_sex",
        "table_5_4_3_occupation_group_heterogeneity_income",
        "table_5_4_4_occupation_group_heterogeneity_age_canaries",
        "table_5_4_5_occupation_group_heterogeneity_race_color",
        "table_5_4_6_occupation_group_heterogeneity_education",
    }
    if retired_headline_stems.intersection(EXPECTED_FIGURES + EXPECTED_TABLES):
        raise RuntimeError("Retired manual occupation outputs remain in the headline contract.")
    missing = []
    empty = []
    for stem in EXPECTED_TABLES:
        for suffix in [".csv", ".md"]:
            path = TABLE_DIR / f"{stem}{suffix}"
            if not path.exists():
                missing.append(path)
            elif path.stat().st_size == 0:
                empty.append(path)
    for name in EXPECTED_FIGURES:
        path = FIGURE_DIR / name
        if not path.exists():
            missing.append(path)
        elif path.stat().st_size == 0:
            empty.append(path)
    for path in [OUTPUT_ROOT / "README.md", OUTPUT_ROOT / "MANIFEST.md", OUTPUT_ROOT / "figure_table_index.md", AUDIT_DIR / "source_audit.md"]:
        if not path.exists():
            missing.append(path)
        elif path.stat().st_size == 0:
            empty.append(path)
    if missing:
        raise RuntimeError("Missing final Section 4/5 artifacts: " + ", ".join(str(p) for p in missing))
    if empty:
        raise RuntimeError("Empty final Section 4/5 artifacts: " + ", ".join(str(p) for p in empty))

    section52_validation = validate_section5_2_outputs(TABLE_DIR)
    navigation_paths = [OUTPUT_ROOT / "README.md", OUTPUT_ROOT / "MANIFEST.md", OUTPUT_ROOT / "figure_table_index.md"]
    navigation_texts = [path.read_text(encoding="utf-8") for path in navigation_paths]
    missing_navigation = [stem for stem in EXPECTED_TABLES if any(stem not in text for text in navigation_texts)]
    if missing_navigation:
        raise RuntimeError("Expected tables missing from package navigation: " + ", ".join(missing_navigation))

    import matplotlib.image as mpimg

    unreadable = []
    for name in EXPECTED_FIGURES:
        try:
            img = mpimg.imread(FIGURE_DIR / name)
            if img.size == 0:
                unreadable.append(FIGURE_DIR / name)
        except Exception:
            unreadable.append(FIGURE_DIR / name)
    if unreadable:
        raise RuntimeError("Unreadable figure files: " + ", ".join(str(p) for p in unreadable))

    copied_tables = {
        "table_5_3_1_occupation_case_exposure_summary": "table_5_3_1_occupation_case_exposure_summary",
        "table_b_1_occupation_case_age_terminal_matrix": "occupation_case_age_terminal_matrix",
        "table_b_2_occupation_case_preperiod_diagnostics": "occupation_case_preperiod_diagnostics",
        "table_b_3_occupation_case_sensitivity_matrix": "occupation_case_sensitivity_matrix",
        "table_b_4_occupation_case_demographic_terminal_matrix": "occupation_case_demographic_terminal_matrix",
    }
    table_parity = all(
        pd.read_csv(TABLE_DIR / f"{target}.csv").equals(
            pd.read_csv(SECTION5_3_ROOT / "tables" / f"{source}.csv")
        )
        for target, source in copied_tables.items()
    )
    copied_figures = [
        name for name in EXPECTED_FIGURES if "occupation_cases" in name
    ]
    figure_parity = all(
        (FIGURE_DIR / name).read_bytes()
        == (SECTION5_3_ROOT / "figures" / name).read_bytes()
        for name in copied_figures
    )
    if not table_parity:
        raise RuntimeError("Section 5.3 source and final-package CSVs differ.")
    if not figure_parity:
        raise RuntimeError("Section 5.3 source and final-package PNGs differ.")

    validation = pd.DataFrame(
        [
            {"check": "expected_tables_csv_md", "status": "pass", "count": len(EXPECTED_TABLES)},
            {"check": "expected_figures_readable", "status": "pass", "count": len(EXPECTED_FIGURES)},
            {"check": "manifest_exists", "status": "pass", "count": 1},
            {"check": "readme_manifest_index_parity", "status": "pass", "count": len(EXPECTED_TABLES)},
            {"check": "legacy_outputs_not_headline_sources", "status": "pass", "count": 1},
            {"check": "section5_3_csv_source_parity", "status": "pass", "count": len(copied_tables)},
            {"check": "section5_3_png_source_parity", "status": "pass", "count": len(copied_figures)},
        ]
    )
    validation = pd.concat([validation, section52_validation], ignore_index=True)
    validation.to_csv(AUDIT_DIR / "validation_checks.csv", index=False)
    (AUDIT_DIR / "validation_checks.md").write_text(
        "# Validação Do Pacote Final\n\n" + markdown_table(validation, list(validation.columns)) + "\n",
        encoding="utf-8",
    )
