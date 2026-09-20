#!/usr/bin/env python3
"""Build the strict CBO treatment classification without Stage 3 inputs."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from run_treatment_scenario_grid import (
    BRIDGE_FILE,
    DATA_OUTPUT,
    ILO_FILE,
    OUTPUT_DIR,
    STAGE2_PANEL,
    add_scenario_roles,
    build_cbo_classification,
    reduce_stage2,
    scenario_specs,
    validate_panel,
    write_classification_csv,
)


ROOT = Path(__file__).resolve().parents[2]
MTE_CACHE_FILE = (
    ROOT
    / "outputs"
    / "crosswalk_audit"
    / "source_dictionaries"
    / "mte_cbo2002_cbo94_ciuo88_by_family.csv"
)


def _split_codes(value: object, width: int) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return sorted(
        {
            code.zfill(width)
            for code in re.findall(r"\d+", str(value))
        }
    )


def build_bridge_from_stage2(
    stage2: pd.DataFrame,
    ilo: pd.DataFrame,
    cache_file: Path,
    bridge_file: Path,
) -> pd.DataFrame:
    """Build the treatment bridge from Stage 2 and the official MTE cache."""
    if not cache_file.is_file():
        raise FileNotFoundError(
            "Stage 2 did not create the official MTE conversion cache: "
            f"{cache_file}"
        )
    cache = pd.read_csv(cache_file, dtype="string")
    required_cache = {"source_cbo_4d", "status"}
    missing_cache = sorted(required_cache - set(cache.columns))
    if missing_cache:
        raise ValueError(f"MTE cache is missing columns: {missing_cache}")

    stage2 = stage2.copy()
    stage2["cbo_4d"] = stage2["cbo_4d"].astype(str).str.zfill(4)
    one_per_cbo = stage2.sort_values(["cbo_4d", "periodo"]).drop_duplicates(
        "cbo_4d"
    )
    one_per_cbo = one_per_cbo.set_index("cbo_4d")

    ilo = ilo.copy()
    ilo["isco_08_str"] = ilo["isco_08_str"].astype(str).str.zfill(4)
    title_map = dict(zip(ilo["isco_08_str"], ilo["occupation_title"]))
    score_map = dict(zip(ilo["isco_08_str"], ilo["exposure_score"]))
    score_2d = (
        ilo.assign(isco_2d=ilo["isco_08_str"].str[:2])
        .groupby("isco_2d")["exposure_score"]
        .mean()
        .to_dict()
    )

    cache["source_cbo_4d"] = (
        cache["source_cbo_4d"].astype(str).str.replace(r"\.0$", "", regex=True)
        .str.zfill(4)
    )
    status_by_cbo = cache.groupby("source_cbo_4d")["status"].agg(
        lambda values: sorted(set(values.dropna().astype(str)))
    )
    rows: list[dict[str, object]] = []
    for cbo_4d, statuses in status_by_cbo.items():
        matched = one_per_cbo.loc[cbo_4d] if cbo_4d in one_per_cbo.index else None
        target_4d = (
            _split_codes(matched["mte_target_isco08_codes"], 4)
            if matched is not None
            else []
        )
        target_2d = (
            _split_codes(matched["mte_target_isco08_2d_codes"], 2)
            if matched is not None
            else []
        )
        rows.append(
            {
                "cbo_4d": cbo_4d,
                "source_cbo_title": "",
                "source_cbo_2d_title": "",
                "source_cbo_3d_title": "",
                "mte_match_status": (
                    matched["mte_match_status"]
                    if matched is not None
                    else "sem_match_mte_no_result"
                ),
                "target_isco08_codes": ", ".join(target_4d),
                "target_isco08_titles": "; ".join(
                    str(title_map.get(code, "")) for code in target_4d
                ),
                "target_isco08_2d_codes": ", ".join(target_2d),
                "target_isco08_2d_titles": "",
                "candidate_scores_mte_4d": ", ".join(
                    f"{float(score_map[code]):.6f}"
                    for code in target_4d
                    if code in score_map
                ),
                "candidate_scores_mte_2d": ", ".join(
                    f"{float(score_2d[code]):.6f}"
                    for code in target_2d
                    if code in score_2d
                ),
                "exposure_score_mte_4d": (
                    matched["exposure_score_mte_4d"]
                    if matched is not None
                    else np.nan
                ),
                "exposure_score_mte_2d": (
                    matched["exposure_score_mte_2d"]
                    if matched is not None
                    else np.nan
                ),
                "mte_cache_statuses": ", ".join(statuses),
            }
        )
    bridge = pd.DataFrame(rows)
    if len(bridge) != 629:
        raise RuntimeError(
            f"Unexpected MTE bridge universe: {len(bridge)} != 629 CBO4."
        )
    if int(bridge["mte_match_status"].eq("matched_official_mte").sum()) != 436:
        raise RuntimeError("The rebuilt MTE bridge must contain 436 matches.")
    bridge_file.parent.mkdir(parents=True, exist_ok=True)
    bridge.to_csv(bridge_file, index=False, lineterminator="\n")
    return bridge


def main() -> None:
    panel_path = (
        STAGE2_PANEL
        if STAGE2_PANEL.is_file()
        else DATA_OUTPUT / "painel_caged_did_ready.parquet"
    )
    required = (ILO_FILE, panel_path)
    missing = [path for path in required if not path.is_file()]
    if missing:
        rendered = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing treatment-classification inputs:\n{rendered}")

    ilo = pd.read_csv(ILO_FILE)
    stage2 = pd.read_parquet(panel_path)
    bridge = (
        pd.read_csv(BRIDGE_FILE)
        if BRIDGE_FILE.is_file()
        else build_bridge_from_stage2(
            stage2,
            ilo,
            MTE_CACHE_FILE,
            BRIDGE_FILE,
        )
    )
    validate_panel(stage2, "Stage 2 panel")
    stage2["cbo_4d"] = stage2["cbo_4d"].astype(str).str.zfill(4)
    bridge["cbo_4d"] = bridge["cbo_4d"].astype(str).str.zfill(4)
    ilo["isco_08_str"] = ilo["isco_08_str"].astype(str).str.zfill(4)

    stage3 = pd.DataFrame(
        columns=[
            "cbo_4d",
            "exposure_score_2d",
            "exposure_score_4d",
            "alta_exp",
            "alta_exp_4d",
            "admissoes",
        ]
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    classification, thresholds = build_cbo_classification(
        ilo,
        bridge,
        reduce_stage2(stage2),
        stage3,
    )
    classification = add_scenario_roles(
        classification,
        scenario_specs(thresholds),
    )
    write_classification_csv(classification)
    print(
        "CBO classification written without municipal Stage 3 inputs: "
        f"{OUTPUT_DIR / 'scenario_cbo_classification.csv'}",
        flush=True,
    )


if __name__ == "__main__":
    main()
