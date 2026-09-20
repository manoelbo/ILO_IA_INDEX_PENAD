"""Immutable analytic-input checks for dissertation Sections 4–5."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from common.validation import ValidationCheck, check_equal
from .contracts import (
    EVENT_TIME_MAX,
    EVENT_TIME_MIN,
    EVENT_TIME_REFERENCE,
    EXPECTED_CLASSIFIED_CBO4,
    EXPECTED_MAIN_CONTROL_CBO4,
    EXPECTED_MAIN_TREATED_CBO4,
    EXPECTED_OCCUPATION_CASE_CBO6,
    EXPECTED_PANEL_CBO4,
    EXPECTED_PANEL_MONTHS,
    EXPECTED_PANEL_OBSERVATIONS,
)


def input_paths(data_root: Path) -> dict[str, Path]:
    """Return every frozen input used by the public validation pipeline."""
    return {
        "panel": data_root / "data" / "output" / "painel_2b_ready.parquet",
        "classification": (
            data_root
            / "outputs"
            / "treatment_scenario_grid"
            / "scenario_cbo_classification.csv"
        ),
        "case_dictionary": (
            data_root
            / "backing_data"
            / "section5_3_occupation_cases"
            / "occupation_case_dictionary.csv"
        ),
        "event_study": (
            data_root
            / "backing_data"
            / "national_event_study"
            / "event_study_coefficients_long.csv"
        ),
    }


def validate_analytic_inputs(
    data_root: Path,
) -> tuple[list[ValidationCheck], dict[str, object]]:
    """Validate panel, treatment, event-time, and occupation-case contracts."""
    paths = input_paths(data_root)
    missing = [path for path in paths.values() if not path.is_file()]
    if missing:
        rendered = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing Sections 4–5 analytic inputs:\n{rendered}")

    panel = pd.read_parquet(paths["panel"], columns=["cbo_4d", "periodo"])
    classification = pd.read_csv(
        paths["classification"],
        dtype={"cbo_4d": "string"},
        usecols=[
            "cbo_4d",
            "mte_match_status",
            "cbo_ilo_gradient",
            "role__trat_expostos",
        ],
    )
    case_dictionary = pd.read_csv(
        paths["case_dictionary"],
        dtype={"cbo_6d": "string"},
        usecols=["cbo_6d", "primary_included"],
    )
    event_data = pd.read_csv(
        paths["event_study"],
        usecols=["t", "is_reference"],
    )

    roles = classification["role__trat_expostos"].value_counts()
    treated_categories = set(
        classification.loc[
            classification["role__trat_expostos"].eq("treated"),
            "cbo_ilo_gradient",
        ].dropna()
    )
    minimal_is_excluded = bool(
        classification.loc[
            classification["cbo_ilo_gradient"].eq("Minimal Exposure"),
            "role__trat_expostos",
        ]
        .eq("excluded")
        .all()
    )
    event_reference_values = set(
        event_data.loc[event_data["is_reference"].astype(bool), "t"].astype(int)
    )
    primary_case_codes = case_dictionary.loc[
        case_dictionary["primary_included"].astype(bool), "cbo_6d"
    ].drop_duplicates()

    checks = [
        check_equal(
            "panel_observations",
            int(len(panel)),
            EXPECTED_PANEL_OBSERVATIONS,
            "Rows in the default CBO4-month panel.",
        ),
        check_equal(
            "panel_cbo4",
            int(panel["cbo_4d"].nunique()),
            EXPECTED_PANEL_CBO4,
            "Unique four-digit occupations.",
        ),
        check_equal(
            "panel_months",
            int(panel["periodo"].nunique()),
            EXPECTED_PANEL_MONTHS,
            "Unique months.",
        ),
        check_equal(
            "panel_window",
            (str(panel["periodo"].min()), str(panel["periodo"].max())),
            ("2021-01", "2025-06"),
            "Analytic-panel time window.",
        ),
        check_equal(
            "classified_cbo4",
            int(len(classification)),
            EXPECTED_CLASSIFIED_CBO4,
            "Complete CBO4 classification universe.",
        ),
        check_equal(
            "matched_cbo4",
            int(
                classification["mte_match_status"]
                .eq("matched_official_mte")
                .sum()
            ),
            EXPECTED_PANEL_CBO4,
            "Official MTE crosswalk matches.",
        ),
        check_equal(
            "main_treated_cbo4",
            int(roles.get("treated", 0)),
            EXPECTED_MAIN_TREATED_CBO4,
            "G1–G4 occupations in the strict treatment.",
        ),
        check_equal(
            "main_control_cbo4",
            int(roles.get("control", 0)),
            EXPECTED_MAIN_CONTROL_CBO4,
            "Not Exposed occupations in the strict control.",
        ),
        check_equal(
            "minimal_exposure_excluded",
            minimal_is_excluded,
            True,
            "Minimal Exposure must be excluded from the main model.",
        ),
        check_equal(
            "treated_categories",
            treated_categories,
            {
                "Exposed: Gradient 1",
                "Exposed: Gradient 2",
                "Exposed: Gradient 3",
            },
            "Observed treated categories; G4 has no CBO4 in the crosswalk.",
        ),
        check_equal(
            "event_time_min",
            int(event_data["t"].min()),
            EVENT_TIME_MIN,
            "Lower event-time bound.",
        ),
        check_equal(
            "event_time_max",
            int(event_data["t"].max()),
            EVENT_TIME_MAX,
            "Upper event-time bound.",
        ),
        check_equal(
            "event_time_reference",
            event_reference_values,
            {EVENT_TIME_REFERENCE},
            "Omitted event-study reference period.",
        ),
        check_equal(
            "occupation_case_cbo6",
            int(len(primary_case_codes)),
            EXPECTED_OCCUPATION_CASE_CBO6,
            "Non-overlapping primary CBO6 codes across six occupation cases.",
        ),
    ]
    denominators = {
        "panel_observations": int(len(panel)),
        "panel_cbo4": int(panel["cbo_4d"].nunique()),
        "panel_months": int(panel["periodo"].nunique()),
        "panel_start": str(panel["periodo"].min()),
        "panel_end": str(panel["periodo"].max()),
        "classified_cbo4": int(len(classification)),
        "matched_cbo4": int(
            classification["mte_match_status"].eq("matched_official_mte").sum()
        ),
        "main_treated_cbo4": int(roles.get("treated", 0)),
        "main_control_cbo4": int(roles.get("control", 0)),
        "event_time_min": EVENT_TIME_MIN,
        "event_time_max": EVENT_TIME_MAX,
        "event_time_reference": EVENT_TIME_REFERENCE,
        "occupation_case_cbo6": int(len(primary_case_codes)),
    }
    return checks, denominators
