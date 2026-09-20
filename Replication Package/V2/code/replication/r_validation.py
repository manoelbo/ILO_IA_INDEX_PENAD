#!/usr/bin/env python3
"""Export model contracts and validate the complete independent R replay.

The R process receives analytical bases and declarative model contracts only.
It never reads Python coefficients.  Python and R outputs are joined only after
both engines have completed, using stable model and event-time identifiers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = PACKAGE_ROOT / "code"
MODELS_ROOT = PACKAGE_ROOT / "code" / "caged" / "models"
for module_root in (CODE_ROOT, MODELS_ROOT):
    if str(module_root) not in sys.path:
        sys.path.insert(0, str(module_root))

from common.merge_audit import audited_merge
from event_study import event_time_from_period
from group_event_studies import DIMENSIONS as EVENT_DIMENSIONS
from heterogeneity import (
    ALTERNATIVE_DIMENSIONS,
    DIMENSIONS,
    OUTCOMES,
    estimable_lower_terms,
)
from national_event_study_extended import OUTCOMES as EXTENDED_OUTCOMES
from pretrend_national_variants import wage_coverage_sample
from sector_models import load_model_data, sector_model_contract
from specification_ladder import ladder_contract, prepare_ladder_data


NUMERIC_TOLERANCE = 1e-6
DIAGNOSTIC_P_VALUE_TOLERANCE = 2e-5
DIAGNOSTIC_RELATIVE_TOLERANCE = 1e-3
EXACT_FIELDS = (
    "n_obs",
    "minimum_clusters",
    "sample_id",
    "status",
    "reference_event_time",
)
REFERENCE_EVENT_TIME = -1
R_INPUT_DIR = PACKAGE_ROOT / "data" / "derived" / "r_validation"
R_OUTPUT_DIR = PACKAGE_ROOT / "results" / "replication" / "complete_r"
CONTRACT_PATH = R_INPUT_DIR / "model_contracts.csv"


def _formula(
    outcome: str,
    term: str,
    fixed_effects: Iterable[str],
    controls: Iterable[str] = (),
) -> str:
    right = " + ".join((term, *tuple(controls)))
    return f"{outcome} ~ {right} | {' + '.join(fixed_effects)}"


def _event_formula(
    outcome: str,
    interaction: str,
    fixed_effects: Iterable[str],
) -> str:
    return (
        f"{outcome} ~ i(event_time, {interaction}, ref=-1) | "
        + " + ".join(fixed_effects)
    )


def _contract_row(
    *,
    analysis_family: str,
    model_id: str,
    data_file: str,
    model_type: str,
    outcome: str,
    estimator: str,
    formula: str,
    term: str,
    cluster_variables: str,
    sample_filter: str,
    sample_id: str,
    event_min: int | None = None,
    event_max: int | None = None,
    diagnostic_lead_min: int | None = None,
    expected_status: str = "estimated",
    python_source: str,
    python_selector: str,
    python_coefficient_source: str | None = None,
    python_coefficient_selector: str | None = None,
) -> dict[str, Any]:
    return {
        "analysis_family": analysis_family,
        "model_id": model_id,
        "data_file": data_file,
        "model_type": model_type,
        "outcome": outcome,
        "estimator": estimator,
        "formula": formula,
        "term": term,
        "cluster_variables": cluster_variables,
        "sample_filter": sample_filter,
        "sample_id": sample_id,
        "event_min": event_min,
        "event_max": event_max,
        "reference_event_time": (
            REFERENCE_EVENT_TIME if model_type == "event" else None
        ),
        "diagnostic_lead_min": diagnostic_lead_min,
        "comparison_scope": (
            "diagnostic" if diagnostic_lead_min is not None else "coefficient"
        ),
        "expected_status": expected_status,
        "python_source": python_source,
        "python_selector": python_selector,
        "python_coefficient_source": (
            python_coefficient_source or python_source
        ),
        "python_coefficient_selector": (
            python_coefficient_selector or python_selector
        ),
    }


def _family_groups(
    dimensions: dict[str, dict[str, Any]],
) -> Iterable[tuple[str, str, str]]:
    for dimension, specification in dimensions.items():
        for group_id, _ in specification["groups"]:
            yield dimension, specification["kind"], group_id


def _national_static_contracts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sample_flag = {
        "v_a": "sample_v_a == 1",
        "expanded_minimal": "sample_expanded_minimal == 1",
        "continuous": "sample_continuous == 1",
    }
    for step in ladder_contract():
        period_filter = (
            f"periodo_num >= {step['start_period']} & "
            f"periodo_num <= {step['end_period']}"
        )
        for outcome, estimator in OUTCOMES:
            rows.append(
                _contract_row(
                    analysis_family="national_static",
                    model_id=f"national_static::{step['step_id']}::{outcome}",
                    data_file="national.csv.gz",
                    model_type="static",
                    outcome=outcome,
                    estimator=estimator,
                    formula=_formula(
                        outcome,
                        step["treatment_term"],
                        ("cbo_4d", "periodo"),
                        step["controls"],
                    ),
                    term=step["treatment_term"],
                    cluster_variables="cbo_4d",
                    sample_filter=(
                        f"{sample_flag[step['sample']]} & {period_filter}"
                    ),
                    sample_id=(
                        f"{step['sample']}:{step['start_period']}-"
                        f"{step['end_period']}"
                    ),
                    python_source="models/specification_ladder.csv",
                    python_selector=json.dumps(
                        {"step_id": step["step_id"], "outcome": outcome},
                        sort_keys=True,
                    ),
                )
            )
    return rows


def _sector_static_contracts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for specification in sector_model_contract():
        for outcome, estimator in OUTCOMES:
            level_id = specification["level_id"]
            rows.append(
                _contract_row(
                    analysis_family="sector_static",
                    model_id=f"sector_static::{level_id}::{outcome}",
                    data_file="sector.csv.gz",
                    model_type="static",
                    outcome=outcome,
                    estimator=estimator,
                    formula=_formula(
                        outcome,
                        "post_treat",
                        specification["fixed_effects"],
                    ),
                    term="post_treat",
                    cluster_variables="+".join(
                        specification["cluster_variables"]
                    ),
                    sample_filter="TRUE",
                    sample_id="cbo4_by_cnae_division:202101-202605",
                    python_source="models/sector_fixed_effect_ladder.csv",
                    python_selector=json.dumps(
                        {"level_id": level_id, "outcome": outcome},
                        sort_keys=True,
                    ),
                )
            )
    return rows


def _family_static_contracts(
    *,
    family_id: str,
    dimensions: dict[str, dict[str, Any]],
    data_file: str,
    source: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    analysis_family = f"family_{family_id.lower()}_static"
    for dimension, kind, group_id in _family_groups(dimensions):
        lower_terms, _ = estimable_lower_terms(kind)
        fixed_effects = (
            ("cbo_4d", "periodo", "subgroup")
            if kind == "micro"
            else ("cbo_4d", "periodo")
        )
        for outcome, estimator in OUTCOMES:
            rows.append(
                _contract_row(
                    analysis_family=analysis_family,
                    model_id=(
                        f"family_{family_id}::{dimension}::{group_id}::"
                        f"{outcome}"
                    ),
                    data_file=data_file,
                    model_type="static",
                    outcome=outcome,
                    estimator=estimator,
                    formula=_formula(
                        outcome,
                        "post_treat_group",
                        fixed_effects,
                        lower_terms,
                    ),
                    term="post_treat_group",
                    cluster_variables="cbo_4d",
                    sample_filter=(
                        f"dimension == '{dimension}' & group_id == '{group_id}'"
                    ),
                    sample_id=f"family_{family_id}:{dimension}:{group_id}",
                    python_source=source,
                    python_selector=json.dumps(
                        {
                            "dimension": dimension,
                            "group_id": group_id,
                            "outcome": outcome,
                        },
                        sort_keys=True,
                    ),
                )
            )
    return rows


def _family_c_contracts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    configurations = (
        ("A", DIMENSIONS, "family_a.csv.gz"),
        ("B", ALTERNATIVE_DIMENSIONS, "family_b.csv.gz"),
    )
    for source_family, dimensions, data_file in configurations:
        for dimension, _, group_id in _family_groups(dimensions):
            for outcome, estimator in OUTCOMES:
                rows.append(
                    _contract_row(
                        analysis_family="family_c_group_did",
                        model_id=(
                            f"family_C::{dimension}::{group_id}::{outcome}"
                        ),
                        data_file=data_file,
                        model_type="static",
                        outcome=outcome,
                        estimator=estimator,
                        formula=_formula(
                            outcome,
                            "post_treat",
                            ("cbo_4d", "periodo"),
                        ),
                        term="post_treat",
                        cluster_variables="cbo_4d",
                        sample_filter=(
                            f"dimension == '{dimension}' & "
                            f"group_id == '{group_id}' & subgroup == 'target' "
                            "& event_time >= -23 & event_time <= 23"
                        ),
                        sample_id=(
                            f"family_{source_family}_target:{dimension}:"
                            f"{group_id}"
                        ),
                        python_source="models/group_did_results.csv",
                        python_selector=json.dumps(
                            {
                                "dimension": dimension,
                                "group_id": group_id,
                                "outcome": outcome,
                            },
                            sort_keys=True,
                        ),
                    )
                )
    return rows


def _national_event_contracts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, minimum, maximum, source, outcomes in (
        (
            "balanced",
            -23,
            23,
            "models/event_study_coefficients.csv",
            OUTCOMES,
        ),
        (
            "extended",
            -23,
            41,
            "models/national_event_study_extended_coefficients.csv",
            EXTENDED_OUTCOMES,
        ),
    ):
        for outcome, estimator in outcomes:
            rows.append(
                _contract_row(
                    analysis_family="national_event",
                    model_id=f"national_event::{label}::{outcome}",
                    data_file="national.csv.gz",
                    model_type="event",
                    outcome=outcome,
                    estimator=estimator,
                    formula=_event_formula(
                        outcome,
                        "treated_main",
                        ("cbo_4d", "periodo"),
                    ),
                    term="treated_main",
                    cluster_variables="cbo_4d",
                    sample_filter="sample_v_a == 1",
                    sample_id=f"v_a:event_{minimum}_{maximum}",
                    event_min=minimum,
                    event_max=maximum,
                    python_source=source,
                    python_selector=json.dumps({"outcome": outcome}, sort_keys=True),
                )
            )
    return rows


def _group_event_contracts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for figure_dimension, specification in EVENT_DIMENSIONS.items():
        for group_id, _ in specification["groups"]:
            source_panel, source_dimension = specification["sources"][group_id]
            data_file = (
                "family_a.csv.gz"
                if source_panel == "frozen"
                else "family_b.csv.gz"
            )
            for outcome, estimator in (
                ("admissoes", "ppml"),
                ("ln_salario_real_adm", "ols"),
            ):
                rows.append(
                    _contract_row(
                        analysis_family="group_event",
                        model_id=(
                            f"group_event::{figure_dimension}::{group_id}::"
                            f"{outcome}"
                        ),
                        data_file=data_file,
                        model_type="event",
                        outcome=outcome,
                        estimator=estimator,
                        formula=_event_formula(
                            outcome,
                            "treatment",
                            ("cbo_4d", "periodo"),
                        ),
                        term="treatment",
                        cluster_variables="cbo_4d",
                        sample_filter=(
                            f"dimension == '{source_dimension}' & "
                            f"group_id == '{group_id}' & subgroup == 'target'"
                        ),
                        sample_id=(
                            f"{source_panel}:{source_dimension}:{group_id}:target"
                        ),
                        event_min=-23,
                        event_max=41,
                        python_source=(
                            "models/group_event_study_coefficients.csv"
                        ),
                        python_selector=json.dumps(
                            {
                                "dimension": figure_dimension,
                                "group_id": group_id,
                                "outcome": outcome,
                            },
                            sort_keys=True,
                        ),
                    )
                )
    return rows


def _canary_contract() -> dict[str, Any]:
    return _contract_row(
        analysis_family="canary_event",
        model_id="canary_event::age_22_25::ln_salario_real_adm",
        data_file="family_a.csv.gz",
        model_type="event",
        outcome="ln_salario_real_adm",
        estimator="ols",
        formula=_event_formula(
            "ln_salario_real_adm",
            "treatment",
            ("cbo_4d", "periodo"),
        ),
        term="treatment",
        cluster_variables="cbo_4d",
        sample_filter=(
            "dimension == 'age_canaries' & group_id == 'age_22_25' & "
            "subgroup == 'target'"
        ),
        sample_id="family_A:age_canaries:age_22_25:target",
        event_min=-23,
        event_max=41,
        python_source="models/canaries_22_25_wage_event_study.csv",
        python_selector=json.dumps({}, sort_keys=True),
    )


def _pretrend_contracts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    # The frozen and extended national models also validate every event point.
    for label, minimum, maximum, lead_minimum, source in (
        ("balanced", -23, 23, -23, "diagnostics/pretrend_diagnostics.csv"),
        ("extended", -23, 41, -23, "diagnostics/pretrend_power_check.csv"),
        ("sample_2022", -11, 41, -11, "diagnostics/pretrend_sample_2022.csv"),
    ):
        for outcome, estimator in OUTCOMES:
            rows.append(
                _contract_row(
                    analysis_family="national_pretrend",
                    model_id=f"national_pretrend::{label}::{outcome}",
                    data_file="national.csv.gz",
                    model_type="event",
                    outcome=outcome,
                    estimator=estimator,
                    formula=_event_formula(
                        outcome,
                        "treated_main",
                        ("cbo_4d", "periodo"),
                    ),
                    term="treated_main",
                    cluster_variables="cbo_4d",
                    sample_filter=(
                        "sample_v_a == 1"
                        + (" & periodo_num >= 202201" if label == "sample_2022" else "")
                    ),
                    sample_id=f"v_a:{label}:{minimum}_{maximum}",
                    event_min=minimum,
                    event_max=maximum,
                    diagnostic_lead_min=lead_minimum,
                    python_source=source,
                    python_selector=json.dumps(
                        {
                            "outcome": outcome,
                            "specification": label,
                            "joint_lead_window": f"{lead_minimum}_to_-2",
                        },
                        sort_keys=True,
                    ),
                    python_coefficient_source=(
                        "diagnostics/"
                        "pretrend_national_variants_coefficients.csv"
                    ),
                    python_coefficient_selector=json.dumps(
                        {
                            "model_id": (
                                f"national_pretrend::{label}::{outcome}"
                            )
                        },
                        sort_keys=True,
                    ),
                )
            )

    for label, interaction, sample_filter in (
        ("expanded_minimal", "treatment", "sample_expanded_minimal == 1"),
        ("continuous", "exposure_z", "sample_continuous == 1"),
    ):
        source_id = (
            "04_include_minimal_as_control"
            if label == "expanded_minimal"
            else "05_continuous_exposure"
        )
        for outcome, estimator in OUTCOMES:
            rows.append(
                _contract_row(
                    analysis_family="national_pretrend",
                    model_id=f"national_pretrend::{label}::{outcome}",
                    data_file="national.csv.gz",
                    model_type="event",
                    outcome=outcome,
                    estimator=estimator,
                    formula=_event_formula(
                        outcome,
                        interaction,
                        ("cbo_4d", "periodo"),
                    ),
                    term=interaction,
                    cluster_variables="cbo_4d",
                    sample_filter=sample_filter,
                    sample_id=f"{label}:event_-23_23",
                    event_min=-23,
                    event_max=23,
                    diagnostic_lead_min=-23,
                    python_source="diagnostics/pretrend_ladder_variants.csv",
                    python_selector=json.dumps(
                        {"outcome": outcome, "specification_id": source_id},
                        sort_keys=True,
                    ),
                    python_coefficient_source=(
                        "diagnostics/"
                        "pretrend_national_variants_coefficients.csv"
                    ),
                    python_coefficient_selector=json.dumps(
                        {
                            "model_id": (
                                f"national_pretrend::{label}::{outcome}"
                            )
                        },
                        sort_keys=True,
                    ),
                )
            )
    rows.append(
        _contract_row(
            analysis_family="national_pretrend",
            model_id="national_pretrend::wage_complete_coverage::ln_salario_real_adm",
            data_file="national.csv.gz",
            model_type="event",
            outcome="ln_salario_real_adm",
            estimator="ols",
            formula=_event_formula(
                "ln_salario_real_adm",
                "treated_main",
                ("cbo_4d", "periodo"),
            ),
            term="treated_main",
            cluster_variables="cbo_4d",
            sample_filter="sample_v_a == 1 & complete_wage_coverage == 1",
            sample_id="v_a:wage_complete_coverage:event_-23_23",
            event_min=-23,
            event_max=23,
            diagnostic_lead_min=-23,
            python_source="diagnostics/pretrend_wage_balanced_coverage.csv",
            python_selector=json.dumps({}, sort_keys=True),
            python_coefficient_source=(
                "diagnostics/pretrend_national_variants_coefficients.csv"
            ),
            python_coefficient_selector=json.dumps(
                {
                    "model_id": (
                        "national_pretrend::wage_complete_coverage::"
                        "ln_salario_real_adm"
                    )
                },
                sort_keys=True,
            ),
        )
    )
    return rows


def _sector_pretrend_contracts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for specification in sector_model_contract()[:2]:
        for outcome, estimator in OUTCOMES:
            level_id = specification["level_id"]
            rows.append(
                _contract_row(
                    analysis_family="sector_pretrend",
                    model_id=f"sector_pretrend::{level_id}::{outcome}",
                    data_file="sector.csv.gz",
                    model_type="event",
                    outcome=outcome,
                    estimator=estimator,
                    formula=_event_formula(
                        outcome,
                        "treated_main",
                        specification["fixed_effects"],
                    ),
                    term="treated_main",
                    cluster_variables="+".join(
                        specification["cluster_variables"]
                    ),
                    sample_filter="TRUE",
                    sample_id=f"sector:{level_id}:event_-23_23",
                    event_min=-23,
                    event_max=23,
                    diagnostic_lead_min=-23,
                    python_source="diagnostics/pretrend_level2.csv",
                    python_selector=json.dumps(
                        {"outcome": outcome, "specification_id": level_id},
                        sort_keys=True,
                    ),
                    python_coefficient_source=(
                        "diagnostics/pretrend_level2_coefficients.csv"
                    ),
                    python_coefficient_selector=json.dumps(
                        {
                            "model_id": (
                                f"sector_pretrend::{level_id}::{outcome}"
                            )
                        },
                        sort_keys=True,
                    ),
                )
            )
    return rows


def _family_pretrend_contracts() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    configurations = (
        (
            "A",
            DIMENSIONS,
            "family_a.csv.gz",
            "diagnostics/ddd_pretrends.csv",
        ),
        (
            "B",
            ALTERNATIVE_DIMENSIONS,
            "family_b.csv.gz",
            "diagnostics/ddd_alternative_partitions_pretrends.csv",
        ),
    )
    for family_id, dimensions, data_file, source in configurations:
        for dimension, _, group_id in _family_groups(dimensions):
            base_filter = (
                f"dimension == '{dimension}' & group_id == '{group_id}'"
            )
            for outcome, estimator in OUTCOMES:
                selector = json.dumps(
                    {
                        "dimension": dimension,
                        "group_id": group_id,
                        "outcome": outcome,
                    },
                    sort_keys=True,
                )
                rows.append(
                    _contract_row(
                        analysis_family="ddd_pretrend",
                        model_id=(
                            f"ddd_pretrend::{family_id}::{dimension}::"
                            f"{group_id}::{outcome}"
                        ),
                        data_file=data_file,
                        model_type="event",
                        outcome=outcome,
                        estimator=estimator,
                        formula=_event_formula(
                            outcome,
                            "treat_group",
                            (
                                "cbo_4d^subgroup",
                                "periodo^subgroup",
                                "periodo^treatment",
                            ),
                        ),
                        term="treat_group",
                        cluster_variables="cbo_4d",
                        sample_filter=base_filter,
                        sample_id=f"family_{family_id}:{dimension}:{group_id}",
                        event_min=-23,
                        event_max=23,
                        diagnostic_lead_min=-23,
                        python_source=source,
                        python_selector=selector,
                        python_coefficient_source=(
                            "diagnostics/ddd_pretrends_coefficients.csv"
                            if family_id == "A"
                            else (
                                "diagnostics/"
                                "ddd_alternative_partitions_"
                                "pretrends_coefficients.csv"
                            )
                        ),
                        python_coefficient_selector=json.dumps(
                            {
                                "model_id": (
                                    f"ddd_pretrend::{family_id}::{dimension}::"
                                    f"{group_id}::{outcome}"
                                )
                            },
                            sort_keys=True,
                        ),
                    )
                )
                rows.append(
                    _contract_row(
                        analysis_family="group_pretrend",
                        model_id=(
                            f"group_pretrend::{family_id}::{dimension}::"
                            f"{group_id}::{outcome}"
                        ),
                        data_file=data_file,
                        model_type="event",
                        outcome=outcome,
                        estimator=estimator,
                        formula=_event_formula(
                            outcome,
                            "treatment",
                            ("cbo_4d", "periodo"),
                        ),
                        term="treatment",
                        cluster_variables="cbo_4d",
                        sample_filter=base_filter + " & subgroup == 'target'",
                        sample_id=(
                            f"family_{family_id}_target:{dimension}:{group_id}"
                        ),
                        event_min=-23,
                        event_max=23,
                        diagnostic_lead_min=-23,
                        expected_status="estimated",
                        python_source=source,
                        python_selector=selector,
                        python_coefficient_source=(
                            "diagnostics/ddd_pretrends_coefficients.csv"
                            if family_id == "A"
                            else (
                                "diagnostics/"
                                "ddd_alternative_partitions_"
                                "pretrends_coefficients.csv"
                            )
                        ),
                        python_coefficient_selector=json.dumps(
                            {
                                "model_id": (
                                    f"group_pretrend::{family_id}::"
                                    f"{dimension}::{group_id}::{outcome}"
                                )
                            },
                            sort_keys=True,
                        ),
                    )
                )
    return rows


def build_caged_model_contracts() -> pd.DataFrame:
    """Return the complete, coefficient-free CAGED R model registry."""
    rows = [
        *_national_static_contracts(),
        *_sector_static_contracts(),
        *_family_static_contracts(
            family_id="A",
            dimensions=DIMENSIONS,
            data_file="family_a.csv.gz",
            source="diagnostics/ddd_multiplicity_results.csv",
        ),
        *_family_static_contracts(
            family_id="B",
            dimensions=ALTERNATIVE_DIMENSIONS,
            data_file="family_b.csv.gz",
            source="diagnostics/ddd_alternative_partitions.csv",
        ),
        *_family_c_contracts(),
        *_national_event_contracts(),
        *_group_event_contracts(),
        _canary_contract(),
        *_pretrend_contracts(),
        *_sector_pretrend_contracts(),
        *_family_pretrend_contracts(),
    ]
    frame = pd.DataFrame(rows)
    if frame["model_id"].duplicated().any():
        duplicates = frame.loc[frame["model_id"].duplicated(), "model_id"]
        raise RuntimeError(f"Duplicate R model IDs: {duplicates.tolist()}")
    return frame.sort_values("model_id").reset_index(drop=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_csv_gzip(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    frame.to_csv(
        temporary,
        index=False,
        float_format="%.17g",
        compression={"method": "gzip", "mtime": 0},
    )
    os.replace(temporary, path)


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def _prepare_national(data_dir: Path) -> pd.DataFrame:
    panel = pd.read_parquet(data_dir / "derived" / "painel_nacional.parquet")
    variants = pd.read_csv(
        data_dir / "derived" / "treatment_variants.csv",
        dtype={"cbo_4d": str},
    )
    data = prepare_ladder_data(panel, variants)
    data["event_time"] = event_time_from_period(data["periodo_num"])
    exposed = data["gradient_v_a"].astype(str).str.startswith("Exposed")
    data["sample_v_a"] = (
        exposed | data["gradient_v_a"].eq("Not Exposed")
    ).astype(int)
    data["sample_expanded_minimal"] = (
        data["sample_v_a"].eq(1)
        | data["gradient_v_a"].eq("Minimal Exposure")
    ).astype(int)
    data["sample_continuous"] = data["exposure_z"].notna().astype(int)
    data["treatment"] = exposed.astype(int)
    data["post_treat"] = data["post"].astype(int) * data["treatment"]
    retained, _ = wage_coverage_sample(panel)
    complete = set(retained["cbo_4d"].astype(str))
    data["complete_wage_coverage"] = (
        data["cbo_4d"].astype(str).isin(complete).astype(int)
    )
    return data


def _prepare_sector(data_dir: Path) -> pd.DataFrame:
    data = load_model_data(data_dir / "derived" / "painel_cbo_divisao.parquet")
    data["periodo_num"] = (
        data["periodo"].astype(str).str.replace("-", "", regex=False).astype(int)
    )
    data["event_time"] = event_time_from_period(data["periodo_num"])
    return data


def _prepare_family(path: Path) -> pd.DataFrame:
    data = pd.read_parquet(path)
    data["event_time"] = event_time_from_period(data["periodo_num"])
    return data


def export_caged_inputs(
    *,
    data_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Export deterministic CSV inputs and coefficient-free model contracts."""
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    frames = {
        "national.csv.gz": _prepare_national(data_dir),
        "sector.csv.gz": _prepare_sector(data_dir),
        "family_a.csv.gz": _prepare_family(
            data_dir / "derived" / "painel_heterogeneity_ddd.parquet"
        ),
        "family_b.csv.gz": _prepare_family(
            data_dir
            / "derived"
            / "painel_heterogeneity_ddd_alternative_partitions.parquet"
        ),
    }
    records: list[dict[str, Any]] = []
    for filename, frame in frames.items():
        path = output_dir / filename
        _atomic_csv_gzip(frame, path)
        records.append(
            {
                "bytes": path.stat().st_size,
                "columns": len(frame.columns),
                "path": filename,
                "rows": len(frame),
                "sha256": _sha256(path),
            }
        )
    contracts = build_caged_model_contracts()
    contract_path = output_dir / "model_contracts.csv"
    _atomic_csv(contracts, contract_path)
    records.append(
        {
            "bytes": contract_path.stat().st_size,
            "columns": len(contracts.columns),
            "path": contract_path.name,
            "rows": len(contracts),
            "sha256": _sha256(contract_path),
        }
    )
    manifest = {
        "contains_python_coefficients": False,
        "format_version": 1,
        "inputs": records,
        "model_contracts": len(contracts),
        "status": "ready_for_independent_r_replication",
    }
    manifest_path = output_dir / "manifest.json"
    temporary = manifest_path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, manifest_path)
    return manifest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("export", "compare"))
    parser.add_argument("--data-dir", type=Path, default=PACKAGE_ROOT / "data")
    parser.add_argument("--input-dir", type=Path, default=R_INPUT_DIR)
    parser.add_argument("--results-dir", type=Path, default=PACKAGE_ROOT / "results")
    parser.add_argument("--r-output-dir", type=Path, default=R_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.action == "export":
        result = export_caged_inputs(
            data_dir=args.data_dir.resolve(),
            output_dir=args.input_dir.resolve(),
        )
    else:
        result = compare_caged_results(
            contracts_path=args.input_dir.resolve() / "model_contracts.csv",
            results_dir=args.results_dir.resolve(),
            r_output_dir=args.r_output_dir.resolve(),
        )
    print(json.dumps(result, sort_keys=True))
    return 0


def _compare_honest_did_inputs(
    results_dir: Path,
    r_output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Validate that HonestDiD consumes independently estimated R inputs."""
    python_coefficients = pd.read_csv(
        results_dir / "diagnostics" / "honest_did_event_coefficients.csv"
    )
    r_coefficients = pd.read_csv(
        r_output_dir / "honest_did_event_coefficients.csv"
    )
    coefficient_key = ["outcome", "position", "event_time"]
    if python_coefficients.duplicated(coefficient_key).any() or r_coefficients.duplicated(
        coefficient_key
    ).any():
        raise RuntimeError("HonestDiD coefficient input keys are not unique")
    coefficient_comparison = audited_merge(
        python_coefficients,
        r_coefficients,
        merge_id="complete_r_honest_did_coefficients",
        on=coefficient_key,
        how="outer",
        suffixes=("_python", "_r"),
        indicator=True,
        validate="one_to_one",
    )
    coefficient_comparison["coefficient_absolute_difference"] = (
        coefficient_comparison["coefficient_python"]
        - coefficient_comparison["coefficient_r"]
    ).abs()
    coefficient_comparison["same_estimator"] = coefficient_comparison[
        "estimator_python"
    ].astype(str).eq(coefficient_comparison["estimator_r"].astype(str))
    coefficient_comparison["same_is_pre"] = coefficient_comparison[
        "is_pre_python"
    ].astype(str).str.lower().eq(
        coefficient_comparison["is_pre_r"].astype(str).str.lower()
    )
    coefficient_comparison["comparison_pass"] = (
        coefficient_comparison["_merge"].eq("both")
        & coefficient_comparison["coefficient_absolute_difference"].le(
            NUMERIC_TOLERANCE
        )
        & coefficient_comparison[["same_estimator", "same_is_pre"]].all(
            axis=1
        )
    )

    python_covariance = pd.read_csv(
        results_dir / "diagnostics" / "honest_did_event_vcov_long.csv"
    )
    r_covariance = pd.read_csv(
        r_output_dir / "honest_did_event_vcov_long.csv"
    )
    covariance_key = [
        "outcome",
        "row_position",
        "column_position",
        "row_event_time",
        "column_event_time",
    ]
    if python_covariance.duplicated(covariance_key).any() or r_covariance.duplicated(
        covariance_key
    ).any():
        raise RuntimeError("HonestDiD covariance input keys are not unique")
    covariance_comparison = audited_merge(
        python_covariance,
        r_covariance,
        merge_id="complete_r_honest_did_covariance",
        on=covariance_key,
        how="outer",
        suffixes=("_python", "_r"),
        indicator=True,
        validate="one_to_one",
    )
    covariance_comparison["covariance_absolute_difference"] = (
        covariance_comparison["covariance_python"]
        - covariance_comparison["covariance_r"]
    ).abs()
    covariance_comparison["comparison_pass"] = (
        covariance_comparison["_merge"].eq("both")
        & covariance_comparison["covariance_absolute_difference"].le(
            NUMERIC_TOLERANCE
        )
    )

    coefficient_failures = int(
        (~coefficient_comparison["comparison_pass"]).sum()
    )
    covariance_failures = int(
        (~covariance_comparison["comparison_pass"]).sum()
    )
    status = {
        "coefficient_rows": int(len(coefficient_comparison)),
        "coefficient_rows_failed": coefficient_failures,
        "covariance_rows": int(len(covariance_comparison)),
        "covariance_rows_failed": covariance_failures,
        "maximum_coefficient_absolute_difference": float(
            coefficient_comparison[
                "coefficient_absolute_difference"
            ].max()
        ),
        "maximum_covariance_absolute_difference": float(
            covariance_comparison["covariance_absolute_difference"].max()
        ),
        "numeric_tolerance": NUMERIC_TOLERANCE,
        "status": (
            "pass"
            if coefficient_failures == 0 and covariance_failures == 0
            else "fail"
        ),
    }
    return (
        coefficient_comparison.sort_values(coefficient_key).reset_index(
            drop=True
        ),
        covariance_comparison.sort_values(covariance_key).reset_index(
            drop=True
        ),
        status,
    )


def compare_caged_results(
    *,
    contracts_path: Path,
    results_dir: Path,
    r_output_dir: Path,
) -> dict[str, Any]:
    """Join independent outputs and enforce the cross-language contract."""
    contracts = pd.read_csv(contracts_path)
    r_status_path = r_output_dir / "r_status.json"
    r_status = json.loads(r_status_path.read_text(encoding="utf-8"))
    if r_status.get("status") != "pass" or int(r_status["failed_models"]) != 0:
        raise RuntimeError("The independent R run did not complete")

    coefficient_contracts = contracts.loc[
        contracts["expected_status"].eq("estimated")
    ].copy()
    diagnostic_contracts = contracts.loc[
        contracts["comparison_scope"].eq("diagnostic")
    ].copy()
    python_coefficients = _python_coefficient_results(
        coefficient_contracts,
        results_dir,
    )
    r_coefficients = pd.read_csv(r_output_dir / "r_model_results.csv")
    r_coefficients = r_coefficients.loc[
        r_coefficients["model_id"].isin(coefficient_contracts["model_id"])
    ].copy()
    coefficient_comparison = _compare_coefficients(
        python_coefficients,
        r_coefficients,
    )

    python_diagnostics = _python_diagnostic_results(
        diagnostic_contracts,
        results_dir,
    )
    r_diagnostics = pd.read_csv(r_output_dir / "r_pretrend_diagnostics.csv")
    diagnostic_comparison = _compare_diagnostics(
        python_diagnostics,
        r_diagnostics,
    )
    (
        honest_coefficient_comparison,
        honest_covariance_comparison,
        honest_status,
    ) = _compare_honest_did_inputs(results_dir, r_output_dir)

    _atomic_csv(
        coefficient_comparison,
        r_output_dir / "python_r_model_comparison.csv",
    )
    _atomic_csv(
        diagnostic_comparison,
        r_output_dir / "python_r_pretrend_comparison.csv",
    )
    _atomic_csv(
        honest_coefficient_comparison,
        r_output_dir / "python_r_honest_did_coefficient_comparison.csv",
    )
    _atomic_csv(
        honest_covariance_comparison,
        r_output_dir / "python_r_honest_did_vcov_comparison.csv",
    )
    coefficient_failure = ~coefficient_comparison["comparison_pass"].astype(bool)
    diagnostic_failure = ~diagnostic_comparison["comparison_pass"].astype(bool)
    status = {
        "coefficient_rows": int(len(coefficient_comparison)),
        "coefficient_rows_failed": int(coefficient_failure.sum()),
        "coefficient_models": int(len(coefficient_contracts)),
        "contracts": int(len(contracts)),
        "diagnostic_models": int(len(diagnostic_comparison)),
        "diagnostic_models_failed": int(diagnostic_failure.sum()),
        "exact_fields": list(EXACT_FIELDS),
        "honest_did_input_comparison": honest_status,
        "max_coefficient_absolute_difference": float(
            coefficient_comparison["coefficient_absolute_difference"].max()
        ),
        "max_diagnostic_absolute_difference": float(
            diagnostic_comparison["maximum_numeric_absolute_difference"].max()
        ),
        "max_standard_error_absolute_difference": float(
            coefficient_comparison["standard_error_absolute_difference"].max()
        ),
        "numeric_tolerance": NUMERIC_TOLERANCE,
        "diagnostic_p_value_tolerance": DIAGNOSTIC_P_VALUE_TOLERANCE,
        "diagnostic_relative_tolerance": DIAGNOSTIC_RELATIVE_TOLERANCE,
        "explicit_failed_estimation_contracts": int(
            contracts["expected_status"].eq("failed_estimation").sum()
        ),
        "r_models": int(r_status["contracts"]),
        "status": (
            "pass"
            if (
                not coefficient_failure.any()
                and not diagnostic_failure.any()
                and honest_status["status"] == "pass"
                and int(r_status.get("honest_did_coefficient_rows", -1)) == 92
                and int(r_status.get("honest_did_covariance_rows", -1))
                == 4232
            )
            else "fail"
        ),
    }
    status_path = r_output_dir / "comparison_status.json"
    temporary = status_path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, status_path)
    if status["status"] != "pass":
        raise RuntimeError("Complete Python-R comparison failed")
    return status


def _read_result(
    cache: dict[str, pd.DataFrame],
    results_dir: Path,
    relative: str,
) -> pd.DataFrame:
    if relative not in cache:
        path = results_dir / relative
        if not path.is_file():
            raise FileNotFoundError(f"Python result is missing: {path}")
        cache[relative] = pd.read_csv(path)
    return cache[relative]


def _selector(payload: str) -> dict[str, Any]:
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("Python selector must be a JSON object")
    return value


def _filter_rows(
    frame: pd.DataFrame,
    selector: dict[str, Any],
    *,
    ignored: frozenset[str] = frozenset(),
) -> pd.DataFrame:
    selected = frame
    for column, value in selector.items():
        if column in ignored:
            continue
        if column not in selected.columns:
            raise KeyError(f"Selector column is absent: {column}")
        if isinstance(value, bool):
            observed = selected[column].astype(str).str.lower().map(
                {"true": True, "false": False}
            )
            selected = selected.loc[observed.eq(value)]
        else:
            selected = selected.loc[selected[column].astype(str).eq(str(value))]
    return selected.copy()


def _result_value(row: pd.Series, *candidates: str) -> Any:
    for column in candidates:
        if column in row.index and not pd.isna(row[column]):
            return row[column]
    raise KeyError(f"None of the result fields exist: {candidates}")


def _python_coefficient_results(
    contracts: pd.DataFrame,
    results_dir: Path,
) -> pd.DataFrame:
    cache: dict[str, pd.DataFrame] = {}
    records: list[dict[str, Any]] = []
    for contract in contracts.itertuples(index=False):
        source = str(contract.python_coefficient_source)
        selector = str(contract.python_coefficient_selector)
        frame = _read_result(cache, results_dir, source)
        selected = _filter_rows(frame, _selector(selector))
        if contract.model_type == "static":
            if len(selected) != 1:
                raise RuntimeError(
                    f"Python static selector returned {len(selected)} rows: "
                    f"{contract.model_id}"
                )
        else:
            expected = int(contract.event_max - contract.event_min + 1)
            if len(selected) != expected:
                raise RuntimeError(
                    f"Python event selector returned {len(selected)} rather "
                    f"than {expected} rows: {contract.model_id}"
                )
        for row in selected.itertuples(index=False):
            series = pd.Series(row._asdict())
            event_time = (
                int(_result_value(series, "event_time"))
                if contract.model_type == "event"
                else np.nan
            )
            is_reference = bool(
                event_time == REFERENCE_EVENT_TIME
                if contract.model_type == "event"
                else False
            )
            standard_error = (
                0.0
                if is_reference and pd.isna(series.get("standard_error"))
                else float(_result_value(series, "standard_error"))
            )
            records.append(
                {
                    "analysis_family": contract.analysis_family,
                    "model_id": contract.model_id,
                    "outcome": contract.outcome,
                    "estimator": contract.estimator,
                    "term": (
                        str(_result_value(series, "term"))
                        if "term" in series.index and not pd.isna(series["term"])
                        else contract.term
                    ),
                    "event_time": event_time,
                    "is_reference": is_reference,
                    "coefficient": float(
                        _result_value(series, "coefficient")
                    ),
                    "standard_error": standard_error,
                    "n_obs": int(_result_value(series, "n_obs")),
                    "minimum_clusters": int(
                        _result_value(
                            series,
                            "minimum_clusters",
                            "n_clusters",
                        )
                    ),
                    "sample_id": contract.sample_id,
                    "status": str(
                        series.get(
                            "result_status",
                            series.get("status", "estimated"),
                        )
                    ),
                    "reference_event_time": (
                        REFERENCE_EVENT_TIME
                        if contract.model_type == "event"
                        else np.nan
                    ),
                }
            )
    return pd.DataFrame(records)


def _comparison_key(frame: pd.DataFrame) -> pd.DataFrame:
    keyed = frame.copy()
    keyed["event_key"] = keyed["event_time"].fillna(1_000_000).astype(int)
    return keyed


def _compare_coefficients(
    python: pd.DataFrame,
    r: pd.DataFrame,
) -> pd.DataFrame:
    key = ["model_id", "event_key"]
    left = _comparison_key(python)
    right = _comparison_key(r)
    if left.duplicated(key).any() or right.duplicated(key).any():
        raise RuntimeError("Cross-language coefficient keys are not unique")
    comparison = audited_merge(
        left,
        right,
        merge_id="complete_r_coefficients",
        on=key,
        how="outer",
        suffixes=("_python", "_r"),
        indicator=True,
        validate="one_to_one",
    )
    comparison["coefficient_absolute_difference"] = (
        comparison["coefficient_python"] - comparison["coefficient_r"]
    ).abs()
    comparison["standard_error_absolute_difference"] = (
        comparison["standard_error_python"]
        - comparison["standard_error_r"]
    ).abs()
    exact_columns: list[str] = []
    for field in EXACT_FIELDS:
        left_field = f"{field}_python"
        right_field = f"{field}_r"
        name = f"same_{field}"
        if field in {"n_obs", "minimum_clusters", "reference_event_time"}:
            left_values = comparison[left_field].fillna(-1).astype(int)
            right_values = comparison[right_field].fillna(-1).astype(int)
            comparison[name] = left_values.eq(right_values)
        else:
            comparison[name] = comparison[left_field].astype(str).eq(
                comparison[right_field].astype(str)
            )
        exact_columns.append(name)
    comparison["comparison_pass"] = (
        comparison["_merge"].eq("both")
        & comparison["coefficient_absolute_difference"].le(NUMERIC_TOLERANCE)
        & comparison["standard_error_absolute_difference"].le(
            NUMERIC_TOLERANCE
        )
        & comparison[exact_columns].all(axis=1)
    )
    return comparison.sort_values(key).reset_index(drop=True)


DIAGNOSTIC_NUMERIC_FIELDS = (
    "joint_lead_count",
    "joint_lead_statistic",
    "joint_lead_p_value",
    "lead_covariance_min_eigenvalue",
    "lead_covariance_rank_tolerance",
    "lead_covariance_psd_tolerance",
    "linear_pretrend_coefficient",
    "linear_pretrend_standard_error",
    "linear_pretrend_p_value",
    "dynamic_pre_p_lt_005",
    "dynamic_min_p_value",
)


def _diagnostic_selection(
    contract: Any,
    frame: pd.DataFrame,
) -> pd.DataFrame:
    selector = _selector(contract.python_selector)
    if contract.model_id.startswith("national_pretrend::balanced::"):
        selector = {"outcome": contract.outcome}
    elif contract.model_id.startswith("national_pretrend::extended::"):
        selector = {
            "outcome": contract.outcome,
            "specification_id": "extended_full_sample",
            "joint_lead_window": "-23_to_-2",
        }
    elif contract.model_id.startswith("national_pretrend::sample_2022::"):
        selector = {"outcome": contract.outcome}
    return _filter_rows(
        frame,
        selector,
        ignored=frozenset({"specification"}),
    )


def _diagnostic_prefix(contract: Any) -> str:
    if contract.analysis_family == "ddd_pretrend":
        return "ddd_"
    if contract.analysis_family == "group_pretrend":
        return "group_pretrend_"
    return ""


def _python_diagnostic_results(
    contracts: pd.DataFrame,
    results_dir: Path,
) -> pd.DataFrame:
    cache: dict[str, pd.DataFrame] = {}
    records: list[dict[str, Any]] = []
    for contract in contracts.itertuples(index=False):
        frame = _read_result(cache, results_dir, contract.python_source)
        selected = _diagnostic_selection(contract, frame)
        if len(selected) != 1:
            raise RuntimeError(
                f"Python diagnostic selector returned {len(selected)} rows: "
                f"{contract.model_id}"
            )
        source = selected.iloc[0]
        prefix = _diagnostic_prefix(contract)

        def named(field: str) -> Any:
            candidate = prefix + field
            if candidate in source.index:
                return source[candidate]
            if field in source.index:
                return source[field]
            return np.nan

        def named_any(*fields: str) -> Any:
            for field in fields:
                value = named(field)
                if not pd.isna(value):
                    return value
            return np.nan

        pretrend_status_field = (
            prefix + "pretrend_status"
            if prefix
            else "pretrend_status"
        )
        status_field = (
            "ddd_status"
            if prefix == "ddd_"
            else "group_pretrend_status"
            if prefix == "group_pretrend_"
            else None
        )
        n_obs = named("n_obs")
        minimum_clusters = named_any(
            "minimum_clusters", "n_clusters", "clusters"
        )
        record = {
            "analysis_family": contract.analysis_family,
            "model_id": contract.model_id,
            "outcome": contract.outcome,
            "estimator": contract.estimator,
            **{field: named(field) for field in DIAGNOSTIC_NUMERIC_FIELDS},
            "lead_covariance_positive_semidefinite": named(
                "lead_covariance_positive_semidefinite"
            ),
            "lead_covariance_dimension": named(
                "lead_covariance_dimension"
            ),
            "lead_covariance_rank": named("lead_covariance_rank"),
            "lead_covariance_full_rank": named(
                "lead_covariance_full_rank"
            ),
            "lead_covariance_condition_number": named(
                "lead_covariance_condition_number"
            ),
            "pretrend_status": source[pretrend_status_field],
            "n_obs": float(n_obs) if not pd.isna(n_obs) else np.nan,
            "minimum_clusters": (
                float(minimum_clusters)
                if not pd.isna(minimum_clusters)
                else np.nan
            ),
            "sample_id": contract.sample_id,
            "status": (
                str(source[status_field])
                if status_field and status_field in source.index
                else "estimated"
            ),
            "reference_event_time": int(
                source.get("reference_event_time", REFERENCE_EVENT_TIME)
            ),
        }
        records.append(record)
    return pd.DataFrame(records)


def _compare_diagnostics(
    python: pd.DataFrame,
    r: pd.DataFrame,
) -> pd.DataFrame:
    comparison = audited_merge(
        python,
        r,
        merge_id="complete_r_pretrend_diagnostics",
        on="model_id",
        how="outer",
        suffixes=("_python", "_r"),
        indicator=True,
        validate="one_to_one",
    )
    numeric_difference_columns: list[str] = []
    numeric_pass_columns: list[str] = []
    for field in DIAGNOSTIC_NUMERIC_FIELDS:
        difference = f"{field}_absolute_difference"
        python_values = comparison[f"{field}_python"]
        r_values = comparison[f"{field}_r"]
        both_present = python_values.notna() & r_values.notna()
        same_missingness = python_values.notna().eq(r_values.notna())
        comparison[difference] = (python_values - r_values).abs()
        pass_field = f"{field}_pass"
        threshold = NUMERIC_TOLERANCE
        if field == "joint_lead_statistic":
            threshold = NUMERIC_TOLERANCE + (
                DIAGNOSTIC_RELATIVE_TOLERANCE
                * python_values.abs()
            )
        elif field in {
            "joint_lead_p_value",
            "linear_pretrend_p_value",
        }:
            threshold = DIAGNOSTIC_P_VALUE_TOLERANCE
        comparison[pass_field] = same_missingness & (
            ~both_present | comparison[difference].le(threshold)
        )
        numeric_difference_columns.append(difference)
        numeric_pass_columns.append(pass_field)
    comparison["maximum_numeric_absolute_difference"] = comparison[
        numeric_difference_columns
    ].max(axis=1, skipna=True)

    exact_pairs = (
        *EXACT_FIELDS,
        "pretrend_status",
        "lead_covariance_positive_semidefinite",
        "lead_covariance_dimension",
        "lead_covariance_rank",
        "lead_covariance_full_rank",
    )
    exact_pass_columns: list[str] = []
    for field in exact_pairs:
        name = f"same_{field}"
        left = comparison[f"{field}_python"]
        right = comparison[f"{field}_r"]
        both_present = left.notna() & right.notna()
        same_missingness = left.notna().eq(right.notna())
        if field in {
            "n_obs",
            "minimum_clusters",
            "reference_event_time",
            "lead_covariance_dimension",
            "lead_covariance_rank",
        }:
            same = left.fillna(-1).astype(int).eq(right.fillna(-1).astype(int))
        else:
            same = left.astype(str).eq(right.astype(str))
        comparison[name] = same_missingness & (~both_present | same)
        exact_pass_columns.append(name)
    comparison["comparison_pass"] = (
        comparison["_merge"].eq("both")
        & comparison[numeric_pass_columns].all(axis=1)
        & comparison[exact_pass_columns].all(axis=1)
    )
    return comparison.sort_values("model_id").reset_index(drop=True)


if __name__ == "__main__":
    raise SystemExit(main())
