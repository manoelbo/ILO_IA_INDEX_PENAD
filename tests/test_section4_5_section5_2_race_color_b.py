import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from build_section5_2_race_color_b import (  # noqa: E402
    DIMENSION,
    DYNAMIC_OUTCOMES,
    GROUPS,
    _validate_dynamic_frames,
)
from section4_5_final.section5_2_dynamic_figures import (  # noqa: E402
    EVENT_TIMES,
    PATH_ROLES,
)


class RaceColorBinaryAlternativeTests(unittest.TestCase):
    @staticmethod
    def _frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        coefficients = []
        pretrends = []
        paths = []
        for group_index, (group_id, group_label) in enumerate(GROUPS):
            sign = 1 if group_index == 0 else -1
            for outcome in DYNAMIC_OUTCOMES:
                pretrends.append(
                    {
                        "dimension": DIMENSION,
                        "group_id": group_id,
                        "group_label": group_label,
                        "outcome": outcome,
                    }
                )
                for t in EVENT_TIMES:
                    value = 0.0 if t == -1 else sign * (t + 1) / 100.0
                    coefficients.append(
                        {
                            "dimension": DIMENSION,
                            "group_id": group_id,
                            "group_label": group_label,
                            "outcome": outcome,
                            "t": t,
                            "coef": value,
                            "se": 0.05,
                            "p_value": 0.50,
                        }
                    )
                    for role in PATH_ROLES:
                        paths.append(
                            {
                                "dimension": DIMENSION,
                                "group_id": group_id,
                                "group_label": group_label,
                                "outcome": outcome,
                                "scenario_role": role,
                                "t": t,
                            }
                        )
        return pd.DataFrame(coefficients), pd.DataFrame(pretrends), pd.DataFrame(paths)

    def test_binary_contract_contains_only_white_and_black_groups(self) -> None:
        self.assertEqual(
            GROUPS,
            [
                ("race_white", "Branca"),
                ("race_black_combined", "Negra (preta e parda)"),
            ],
        )

    def test_dynamic_ddd_coefficients_must_be_mirrored(self) -> None:
        coefficients, pretrends, paths = self._frames()

        _validate_dynamic_frames(coefficients, pretrends, paths)

        bad = coefficients.copy()
        bad.loc[
            bad["group_id"].eq("race_black_combined") & bad["t"].eq(0),
            "coef",
        ] = 0.25
        with self.assertRaisesRegex(RuntimeError, "mirrored"):
            _validate_dynamic_frames(bad, pretrends, paths)


if __name__ == "__main__":
    unittest.main()
