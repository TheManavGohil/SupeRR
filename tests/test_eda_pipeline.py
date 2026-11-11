import json
from pathlib import Path
import unittest

import pandas as pd

from rr_pressure.cli import FEATURES
from rr_pressure.data import checked_merge, fingerprints
from rr_pressure.eda import match_bootstrap
from rr_pressure.state import before_events, innings_quality

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/analysis_preregistration.json").read_text())


def event(number=1, over=1, wicket=False, extra="None"):
    return {"innings": 1, "innings_ball_num": number, "overid": over,
            "is_wicket": wicket, "extras_type": extra}


def match():
    return {"result": "Team A Won by 10 runs", "first_inn_revised_overs": "",
            "second_inn_revised_overs": "", "revised_target": ""}


class StateTests(unittest.TestCase):
    def test_dimension_join_rejects_duplicated_and_missing_parents(self):
        left = pd.DataFrame({"match_id": ["1", "1"]})
        with self.assertRaises(ValueError):
            checked_merge(left, pd.DataFrame({"match_id": ["1", "1"]}), ["match_id"], "match")
        with self.assertRaises(ValueError):
            checked_merge(left, pd.DataFrame({"match_id": ["2"]}), ["match_id"], "match")
        self.assertEqual(len(checked_merge(left, pd.DataFrame({"match_id": ["1"]}), ["match_id"], "match")), 2)

    def test_current_and_future_wickets_do_not_change_current_features(self):
        rows = [event(i + 1) for i in range(6)]
        original = list(before_events(rows, CONFIG["rule_pressure"]))
        rows[3]["is_wicket"] = True
        rows[5]["is_wicket"] = True
        altered = list(before_events(rows, CONFIG["rule_pressure"]))
        self.assertEqual(original[3], altered[3])
        self.assertEqual(altered[4]["wickets_before"], 1)
        self.assertEqual(altered[5]["wickets_before"], 1)

    def test_illegal_event_does_not_advance_remaining_balls(self):
        rows = [event(1, extra="wide"), event(2, extra="Overstep"), event(3), event(4)]
        states = list(before_events(rows, CONFIG["rule_pressure"]))
        self.assertEqual([s["legal_balls_before"] for s in states], [0, 0, 0, 1])
        self.assertEqual([s["balls_remaining"] for s in states], [120, 120, 120, 119])

    def test_unknown_extras_and_sequence_gaps_exclude_entire_innings(self):
        rows = [event(1), event(2, extra="other"), event(3)]
        self.assertEqual(innings_quality(rows, match()), "unknown_extra_category")
        self.assertEqual(innings_quality([event(1), event(3)], match()), "event_sequence_gap")

    def test_adjustments_and_superovers_have_separate_cohorts(self):
        self.assertEqual(innings_quality([event()], match() | {"revised_target": "100"}), "adjusted_or_rain")
        self.assertEqual(innings_quality([event() | {"innings": 3}], match()), "super_over")

    def test_wicket_margin_conflict_is_quarantined(self):
        rows = [event(i + 1, wicket=i == 0) | {"innings": 2} for i in range(4)]
        self.assertEqual(innings_quality(rows, match() | {"result": "A Won by 8 wickets"}), "wicket_margin_conflict")

    def test_match_bootstrap_preserves_paired_contexts(self):
        rows = []
        for mid, runs in [("1", 1), ("2", 6)]:
            for pressure in (False, True):
                rows.append({"match_id": mid, "pressure_proxy": pressure, "extras_type": "None", "recorded_runs": runs,
                             "event_id": f"{mid}:{pressure}", "bowler_credited_wicket": False})
        output = match_bootstrap(pd.DataFrame(rows), 100, seed=9)
        difference = output[(output.metric == "recorded_runs_per_100_nonwide") &
                            (output.group == "pressure_minus_ordinary_descriptive")].iloc[0]
        self.assertEqual(difference["estimate"], 0)
        self.assertEqual(difference["p10"], 0)
        self.assertEqual(difference["p90"], 0)

    def test_feature_allowlist_has_no_outcomes_or_retrospective_batting_order(self):
        forbidden = {"recorded_runs", "is_wicket", "win_team_id", "result", "stroke", "bowl_speed", "batting_order"}
        self.assertFalse(set(FEATURES) & forbidden)


@unittest.skipUnless((ROOT / "reports/eda_2026-11-01/manifest.json").exists(), "Run EDA first for artifact checks")
class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = pd.read_parquet(ROOT / "data/processed/score_independent_states.parquet")
        cls.accepted = cls.events[cls.events.eligible_proxy]
        cls.manifest = json.loads((ROOT / "reports/eda_2026-11-01/manifest.json").read_text())

    def test_raw_hashes_and_reconciliation_regression(self):
        self.assertEqual(fingerprints(ROOT / "6af3166e7b922_data_pack"), self.manifest["source_sha256"])
        self.assertTrue(self.manifest["reconciliation_regression_pass"])
        self.assertEqual(len(self.events), 200999)
        self.assertEqual(len(self.accepted), 160186)
        self.assertEqual(int(self.accepted.pressure_proxy.sum()), 50737)

    def test_unverified_scores_are_null_and_exclusions_do_not_get_states(self):
        for column in ("score_before", "chase_target", "required_run_rate", "tight_chase", "pressure_full"):
            self.assertTrue(self.events[column].isna().all())
        self.assertFalse(self.events.mode_a_ready.any())
        rejected = self.events[~self.events.quality.eq("accepted_proxy")]
        self.assertTrue(rejected.legal_balls_before.isna().all())

    def test_terminal_states_and_cutoff(self):
        self.assertTrue(self.accepted.legal_balls_before.between(0, 119).all())
        self.assertTrue(self.accepted.wickets_before.between(0, 9).all())
        self.assertTrue(self.events.match_date.le("2026-11-01").all())

    def test_runouts_not_credited_and_outcomes_join_one_to_one(self):
        self.assertFalse(self.events.loc[self.events.dismissal_type.eq("RunOut"), "bowler_credited_wicket"].any())
        features = pd.read_parquet(ROOT / "data/processed/preball_features.parquet")
        outcomes = pd.read_parquet(ROOT / "data/processed/delivery_outcomes.parquet")
        self.assertEqual(len(features.merge(outcomes, on="event_id", validate="one_to_one")), len(self.accepted))
        self.assertEqual(list(features.columns), FEATURES)


if __name__ == "__main__":
    unittest.main()
