"""Treatment and control assignments."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import MATCHED_MTE_STATUS


EXPOSED_G1_G2 = {"Exposed: Gradient 1", "Exposed: Gradient 2"}
EXPOSED_G3_G4 = {"Exposed: Gradient 3", "Exposed: Gradient 4"}
EXPOSED_G1_G4 = EXPOSED_G1_G2 | EXPOSED_G3_G4


def _matched(classification: pd.DataFrame) -> pd.Series:
    return classification["mte_match_status"].eq(MATCHED_MTE_STATUS)


def _roles_from_masks(classification: pd.DataFrame, treat: pd.Series, control: pd.Series, scenario_id: str) -> pd.DataFrame:
    out = classification[["cbo_4d", "mte_match_status", "cbo_ilo_gradient"]].copy()
    role = np.select([treat, control], ["treated", "control"], default="excluded")
    out["scenario_id"] = scenario_id
    out["scenario_role"] = role
    out["scenario_treat"] = out["scenario_role"].eq("treated").astype(int)
    return out


def assign_single_gradient_roles(classification: pd.DataFrame, gradient_label: str, scenario_id: str) -> pd.DataFrame:
    gradient = classification["cbo_ilo_gradient"].astype(str)
    matched = _matched(classification)
    return _roles_from_masks(
        classification,
        matched & gradient.eq(gradient_label),
        matched & gradient.eq("Not Exposed"),
        scenario_id,
    )


def assign_roles(classification: pd.DataFrame, scenario_id: str) -> pd.DataFrame:
    gradient = classification["cbo_ilo_gradient"].astype(str)
    matched = _matched(classification)

    if scenario_id == "main_strict":
        return _roles_from_masks(
            classification,
            matched & gradient.isin(EXPOSED_G1_G4),
            matched & gradient.eq("Not Exposed"),
            scenario_id,
        )
    if scenario_id == "main_broad_control":
        return _roles_from_masks(
            classification,
            matched & gradient.isin(EXPOSED_G1_G4),
            matched & gradient.isin({"Not Exposed", "Minimal Exposure"}),
            scenario_id,
        )
    if scenario_id == "high_exposure_strict":
        return _roles_from_masks(
            classification,
            matched & gradient.isin(EXPOSED_G3_G4),
            matched & gradient.eq("Not Exposed"),
            scenario_id,
        )
    if scenario_id == "medium_exposure_strict":
        return _roles_from_masks(
            classification,
            matched & gradient.isin(EXPOSED_G1_G2),
            matched & gradient.eq("Not Exposed"),
            scenario_id,
        )
    if scenario_id == "mte_top20_benchmark":
        role = classification["role__baseline_mte2d_top20_vs_rest"].fillna("excluded").astype(str)
        out = classification[["cbo_4d", "mte_match_status", "cbo_ilo_gradient"]].copy()
        out["scenario_id"] = scenario_id
        out["scenario_role"] = np.where(role.isin(["treated", "control"]), role, "excluded")
        out["scenario_treat"] = out["scenario_role"].eq("treated").astype(int)
        return out
    raise ValueError(f"Unknown scenario_id: {scenario_id}")


def apply_roles(panel: pd.DataFrame, roles: pd.DataFrame) -> pd.DataFrame:
    role_cols = ["cbo_4d", "scenario_id", "scenario_role", "scenario_treat"]
    out = panel.merge(roles[role_cols], on="cbo_4d", how="left")
    out["scenario_role"] = out["scenario_role"].fillna("excluded")
    out = out[out["scenario_role"].isin(["treated", "control"])].copy()
    out["scenario_treat"] = out["scenario_treat"].astype(int)
    out["post_treat"] = out["post"].astype(int) * out["scenario_treat"]
    return out


def continuous_sample(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel[
        panel["mte_match_status"].eq(MATCHED_MTE_STATUS)
        & panel["continuous_exposure"].notna()
        & panel["cbo_ilo_gradient"].ne("No score")
    ].copy()
    out["post_continuous_exposure"] = out["post"].astype(int) * pd.to_numeric(out["continuous_exposure"], errors="coerce")
    return out


def validate_base_and_broad_roles(strict: pd.DataFrame, broad: pd.DataFrame) -> None:
    strict_included = strict[strict["scenario_role"].isin(["treated", "control"])]
    broad_control = broad[broad["scenario_role"].eq("control")]
    strict_control = strict[strict["scenario_role"].eq("control")]
    if set(strict_control["cbo_ilo_gradient"].dropna().unique()) != {"Not Exposed"}:
        raise RuntimeError("The strict base control must be exactly Not Exposed.")
    if "Minimal Exposure" in set(strict_included["cbo_ilo_gradient"].dropna().unique()):
        raise RuntimeError("Minimal Exposure entered the strict base sample.")
    if "No score" in set(strict_included["cbo_ilo_gradient"].dropna().unique()):
        raise RuntimeError("No score entered the strict base sample.")
    if not strict_included["mte_match_status"].eq(MATCHED_MTE_STATUS).all():
        raise RuntimeError("Unmatched MTE rows entered the strict base sample.")
    if set(broad_control["cbo_ilo_gradient"].dropna().unique()) != {"Not Exposed", "Minimal Exposure"}:
        raise RuntimeError("The broad control must be exactly Not Exposed plus Minimal Exposure.")
    if broad_control["cbo_4d"].nunique() <= strict_control["cbo_4d"].nunique():
        raise RuntimeError("Broad control did not add Minimal Exposure CBOs.")


def role_summary(roles: pd.DataFrame, scenario_label: str) -> dict[str, object]:
    return {
        "scenario_id": roles["scenario_id"].iloc[0],
        "scenario_label": scenario_label,
        "treated_cbo": int((roles["scenario_role"] == "treated").sum()),
        "control_cbo": int((roles["scenario_role"] == "control").sum()),
        "excluded_cbo": int((roles["scenario_role"] == "excluded").sum()),
        "treated_gradients": "; ".join(sorted(roles.loc[roles["scenario_role"].eq("treated"), "cbo_ilo_gradient"].dropna().unique())),
        "control_gradients": "; ".join(sorted(roles.loc[roles["scenario_role"].eq("control"), "cbo_ilo_gradient"].dropna().unique())),
    }
