"""Section 3 analytic-data invariants."""

from __future__ import annotations

import math

import pandas as pd

from common.validation import ValidationCheck, check_equal


EXPECTED_ROWS = 207_901
EXPECTED_STATES = 27
EXPECTED_POPULATION = 97_783_776.18040435


def analytic_checks(frame: pd.DataFrame) -> list[ValidationCheck]:
    population = float(frame["peso"].sum())
    population_matches = math.isclose(
        population,
        EXPECTED_POPULATION,
        rel_tol=0,
        abs_tol=1e-6,
    )
    return [
        check_equal(
            "section3_rows",
            len(frame),
            EXPECTED_ROWS,
            "PNAD–ILO analytic cross-section observations.",
        ),
        check_equal(
            "section3_states",
            int(frame["sigla_uf"].nunique()),
            EXPECTED_STATES,
            "Brazilian federal units represented.",
        ),
        check_equal(
            "section3_year",
            sorted(pd.to_numeric(frame["ano"]).dropna().astype(int).unique()),
            [2025],
            "The public Section 3 source period is fixed.",
        ),
        check_equal(
            "section3_quarter",
            sorted(
                pd.to_numeric(frame["trimestre"]).dropna().astype(int).unique()
            ),
            [3],
            "The public Section 3 source period is fixed.",
        ),
        ValidationCheck(
            check_id="section3_weighted_population",
            status="PASS" if population_matches else "FAIL",
            observed=f"{population:.8f}",
            expected=f"{EXPECTED_POPULATION:.8f} ± 1e-6",
            detail="Sum of PNAD person weights.",
        ),
    ]
