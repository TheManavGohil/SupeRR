"""Synthetic fixtures only: no competition data is published with tests."""

import unittest

import pandas as pd

from rr_pressure.external import select_pilot, team_key


class SelectionTests(unittest.TestCase):
    def test_stratification_string_booleans_and_no_replacement(self):
        rows = []
        for year in range(2022, 2027):
            for family in ("IPL", "T20I"):
                for day in range(1, 5):
                    rows.append(dict(match_id=f"{year}-{family}-{day}", date=f"{year}-01-0{day}",
                        year=year, family=family, two_innings_present="True", cohort="ordinary",
                        kind="runs", run_margin_pass_a="True" if day == 1 else "False",
                        run_margin_pass_b="False", chase_combined_a="", chase_combined_b="",
                        wicket_margin_pass="", innings1_unknown_extra_events=int(day == 4),
                        innings2_unknown_extra_events=0, innings1_unit_extra_events=day,
                        innings2_unit_extra_events=0))
        frame = pd.DataFrame(rows)
        chosen = select_pilot(frame)
        self.assertEqual(len(chosen), 20)
        self.assertEqual(chosen.groupby(["year", "family"]).size().tolist(), [2] * 10)
        self.assertTrue(chosen.match_id.str.endswith(("-2", "-4")).all())
        pd.testing.assert_frame_equal(chosen, select_pilot(frame.sample(frac=1, random_state=6)))

    def test_team_rename_is_explicit(self):
        self.assertEqual(team_key("Royal Challengers Bangalore"), team_key("Royal Challengers Bengaluru"))
        self.assertNotEqual(team_key("India"), team_key("India A"))


if __name__ == "__main__":
    unittest.main()
