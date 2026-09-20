"""Manual occupation-group definitions for Section 4 exploratory extensions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


MATCHED_MTE_STATUS = "matched_official_mte"
CONTROL_GRADIENT = "Not Exposed"


@dataclass(frozen=True)
class ManualOccupationGroup:
    group_id: str
    label_pt: str
    short_label_pt: str
    cbo_codes: frozenset[str]
    description_pt: str
    exploratory_only: bool = False
    recommended_location_pt: str = "apêndice"


GROUP_SPECS: tuple[ManualOccupationGroup, ...] = (
    ManualOccupationGroup(
        group_id="software_it_core",
        label_pt="Núcleo de Software e TI",
        short_label_pt="Software e TI",
        cbo_codes=frozenset({"2123", "2124", "3171", "3172"}),
        description_pt=(
            "Ocupações de software, desenvolvimento de sistemas, administração de TI, análise de TI e suporte técnico "
            "com match MTE oficial."
        ),
        recommended_location_pt="texto principal da extensão",
    ),
    ManualOccupationGroup(
        group_id="digital_it_with_data_entry",
        label_pt="Ocupações Digitais e de TI com Entrada de Dados",
        short_label_pt="Digital/TI + dados",
        cbo_codes=frozenset({"2123", "2124", "3171", "3172", "4121"}),
        description_pt=(
            "Robustez que adiciona operadores de entrada e transmissão de dados ao núcleo de software e TI."
        ),
        recommended_location_pt="robustez da extensão",
    ),
    ManualOccupationGroup(
        group_id="clear_tech_no_mte",
        label_pt="Tecnologia clara sem match MTE",
        short_label_pt="Tech sem MTE",
        cbo_codes=frozenset({"1236", "1425", "2122"}),
        description_pt=(
            "CBOs claramente ligados a TI/computação, mas sem match MTE oficial no crosswalk atual."
        ),
        exploratory_only=True,
        recommended_location_pt="auditoria/exploratório",
    ),
    ManualOccupationGroup(
        group_id="clerical_office_automation",
        label_pt="Escritório e Rotinas Administrativas",
        short_label_pt="Escritório/admin",
        cbo_codes=frozenset({"3515", "4102", "4110", "4121", "4122", "4131", "4132", "4142"}),
        description_pt="Ocupações administrativas, escriturárias e de entrada de dados expostas a automação de escritório.",
        recommended_location_pt="triagem de mecanismo",
    ),
    ManualOccupationGroup(
        group_id="customer_contact",
        label_pt="Atendimento e Contato com Cliente",
        short_label_pt="Atendimento",
        cbo_codes=frozenset({"4211", "4221", "4222", "4223", "5241"}),
        description_pt="Ocupações de atendimento, recepção, telefonia, telemarketing e contato comercial com clientes.",
        recommended_location_pt="triagem de mecanismo",
    ),
    ManualOccupationGroup(
        group_id="finance_accounting_admin",
        label_pt="Finanças, Contabilidade e Administração",
        short_label_pt="Finanças/admin",
        cbo_codes=frozenset({"2521", "2522", "3511", "3513", "3517", "4102", "4131", "4132"}),
        description_pt="Ocupações de finanças, contabilidade, administração, seguros e serviços bancários.",
        recommended_location_pt="triagem de mecanismo",
    ),
    ManualOccupationGroup(
        group_id="creative_communication_language",
        label_pt="Comunicação, Linguagem e Conteúdo",
        short_label_pt="Comunicação/conteúdo",
        cbo_codes=frozenset({"2531", "2611", "2612", "2614", "2617", "2624", "3751", "7661"}),
        description_pt="Ocupações de comunicação, jornalismo, tradução, publicidade, design e conteúdo multimídia.",
        recommended_location_pt="triagem de mecanismo",
    ),
)

GROUP_SPEC_BY_ID = {spec.group_id: spec for spec in GROUP_SPECS}
OFFICIAL_GROUP_IDS = {
    spec.group_id: set(spec.cbo_codes)
    for spec in GROUP_SPECS
    if not spec.exploratory_only
}
EXPLORATORY_GROUP_IDS = {
    spec.group_id: set(spec.cbo_codes)
    for spec in GROUP_SPECS
    if spec.exploratory_only
}

FALSE_POSITIVE_PROGRAMMING_CBO = {"2394", "3911", "2527"}
NON_SOFTWARE_BROAD_FALSE_POSITIVE_CBO = {"3250", "3251", "3252", "2011", "2012", "2032", "3951"}


def normalize_cbo(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(4)


def get_group_spec(group_id: str) -> ManualOccupationGroup:
    try:
        return GROUP_SPEC_BY_ID[group_id]
    except KeyError as exc:
        raise ValueError(f"Unknown manual occupation group: {group_id}") from exc


def official_group_ids() -> list[str]:
    return [spec.group_id for spec in GROUP_SPECS if not spec.exploratory_only]


def all_group_ids() -> list[str]:
    return [spec.group_id for spec in GROUP_SPECS]


def manual_group_audit(classification: pd.DataFrame) -> pd.DataFrame:
    if "cbo_4d" not in classification.columns:
        raise RuntimeError("Manual occupation-group audit requires column cbo_4d.")
    base = classification.copy()
    base["cbo_4d"] = normalize_cbo(base["cbo_4d"])
    title_col = "source_cbo_title" if "source_cbo_title" in base.columns else "cbo_title"
    rows: list[dict[str, object]] = []
    for spec in GROUP_SPECS:
        selected = base[base["cbo_4d"].isin(spec.cbo_codes)].copy()
        for row in selected.itertuples(index=False):
            row_dict = row._asdict()
            mte_status = row_dict.get("mte_match_status", "")
            gradient = row_dict.get("cbo_ilo_gradient", "")
            rows.append(
                {
                    "group_id": spec.group_id,
                    "group_label": spec.label_pt,
                    "short_label": spec.short_label_pt,
                    "cbo_4d": row_dict.get("cbo_4d"),
                    "cbo_title": row_dict.get(title_col, ""),
                    "mte_match_status": mte_status,
                    "cbo_ilo_gradient": gradient,
                    "official_model_eligible": (not spec.exploratory_only)
                    and (mte_status == MATCHED_MTE_STATUS),
                    "exploratory_only": spec.exploratory_only,
                    "recommended_location": spec.recommended_location_pt,
                    "description": spec.description_pt,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(
            columns=[
                "group_id",
                "group_label",
                "short_label",
                "cbo_4d",
                "cbo_title",
                "mte_match_status",
                "cbo_ilo_gradient",
                "official_model_eligible",
                "exploratory_only",
                "recommended_location",
                "description",
            ]
        )
    return out.sort_values(["group_id", "cbo_4d"]).reset_index(drop=True)


def build_manual_group_roles(
    classification: pd.DataFrame,
    group_id: str,
    allow_exploratory_treated: bool = False,
) -> pd.DataFrame:
    spec = get_group_spec(group_id)
    classified = classification.copy()
    classified["cbo_4d"] = normalize_cbo(classified["cbo_4d"])
    in_group = classified["cbo_4d"].isin(spec.cbo_codes)
    matched = classified["mte_match_status"].eq(MATCHED_MTE_STATUS)
    if spec.exploratory_only and allow_exploratory_treated:
        treated = in_group
    else:
        treated = matched & in_group & ~spec.exploratory_only
    control = matched & classified["cbo_ilo_gradient"].eq(CONTROL_GRADIENT) & ~in_group

    keep_cols = [
        "cbo_4d",
        "mte_match_status",
        "cbo_ilo_gradient",
    ]
    for col in ["source_cbo_title", "source_cbo_2d_title", "source_cbo_3d_title"]:
        if col in classified.columns:
            keep_cols.append(col)
    roles = classified[keep_cols].copy()
    roles["manual_group_id"] = spec.group_id
    roles["manual_group_label"] = spec.label_pt
    roles["manual_group_short_label"] = spec.short_label_pt
    roles["manual_group_exploratory_only"] = spec.exploratory_only
    roles["manual_group_member"] = in_group.to_numpy()
    roles["scenario_id"] = f"manual_group_{spec.group_id}_vs_not_exposed"
    roles["scenario_role"] = np.select([treated, control], ["treated", "control"], default="excluded")
    roles["scenario_treat"] = roles["scenario_role"].eq("treated").astype(int)
    return roles
