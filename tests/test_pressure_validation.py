"""Support checks and match-resampling invariants, using fictional observations."""

import json
from pathlib import Path
import unittest

import pandas as pd

from rr_pressure.data import fingerprints, sha256
from rr_pressure.pressure_validation import bootstrap_comparisons, context_support


def observations():
    rows = []
    for match, base in [("m1", 0), ("m2", 4), ("m3", 2)]:
        for pressure in (False, True):
            for i in range(3):
                rows.append(dict(event_id=f"{match}:{pressure}:{i}", match_id=match, phase="early", pressure_full=pressure,
                    extras_wides=0, batter_runs=base + int(pressure), is_wicket=False, dismissal_type=""))
    return pd.DataFrame(rows)


class SupportTests(unittest.TestCase):
    def test_no_ordinary_control_never_counts_as_supported(self):
        frame = observations()
        late = frame.loc[frame.pressure_full].copy()
        late["phase"] = "late"
        support = context_support(pd.concat([frame, late]), ["phase"], 3, 2).set_index("phase")
        self.assertTrue(support.loc["early", "supported"])
        self.assertFalse(support.loc["late", "supported"])
        self.assertEqual(support.loc["late", "ordinary_events"], 0)
        self.assertTrue(support.loc["late", "pressure_without_ordinary"])

    def test_many_balls_in_one_match_do_not_satisfy_match_evidence(self):
        frame = observations()
        frame["match_id"] = "single"
        self.assertFalse(context_support(frame, ["phase"], 3, 2).supported.any())

    def test_whole_match_bootstrap_preserves_paired_difference(self):
        frame = observations()
        support = context_support(frame, ["phase"], 3, 2)
        results = bootstrap_comparisons(frame, support, ["phase"], 40, 17)
        batting = results.loc[results.metric.eq("batter_runs_per_100_nonwide")]
        for column in ("estimate", "p10", "p90"):
            self.assertTrue((batting[column].sub(100).abs() < 1e-10).all())
        self.assertTrue(results.unit.eq("whole_match").all())
        pd.testing.assert_frame_equal(results, bootstrap_comparisons(frame, support, ["phase"], 40, 17))

    def test_support_does_not_depend_on_outcomes_or_names(self):
        frame = observations()
        expected = context_support(frame, ["phase"], 3, 2)
        frame["batter_runs"] = 6
        frame["is_wicket"] = True
        pd.testing.assert_frame_equal(expected, context_support(frame, ["phase"], 3, 2))


class FullCoverageArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.out = cls.root / "reports/full_reconciliation_2026-11-01"
        cls.pressure = cls.root / "reports/pressure_validation_2026-11-01"
        if not (cls.pressure / "manifest.json").exists():
            raise unittest.SkipTest("Private full-cohort artifacts unavailable")

    def test_all_supplied_matches_accounted_for_and_full_matches_kept(self):
        raw_matches = pd.read_csv(self.root / "6af3166e7b922_data_pack/matches.csv", dtype=str)
        matches = pd.read_csv(self.out / "matches.csv", dtype={"match_id": str})
        expected = set(raw_matches.loc[raw_matches.match_date <= "2026-11-01", "match_id"])
        self.assertEqual(set(matches.match_id), expected)
        self.assertFalse(matches.match_id.duplicated().any())
        corrections = pd.read_parquet(self.out / "verified_corrections.parquet")
        counts = corrections.groupby("match_id").size()
        accepted = matches.loc[matches.accepted].set_index("match_id")
        self.assertEqual(set(counts.index), set(accepted.index))
        self.assertEqual(counts.sort_index().tolist(), accepted.supplied_events.sort_index().tolist())
        self.assertTrue(accepted.alignment_pass.all() and accepted.score_pass.all())
        self.assertTrue(accepted.primary_scope.all())
        self.assertTrue(accepted.match_date.le("2026-11-01").all())
        self.assertTrue(accepted.external_date.le("2026-11-01").all())
        self.assertFalse(accepted.member.duplicated().any())
        self.assertTrue(accepted.date_offset_days.abs().le(1).all())

    def test_original_values_survive_review_and_uncertain_scores_stay_out(self):
        corrections = pd.read_parquet(self.out / "verified_corrections.parquet")
        raw = pd.read_csv(self.root / "6af3166e7b922_data_pack/ball_by_ball.csv", dtype=str, keep_default_na=False)
        raw["event_id"] = raw.match_id + ":" + raw.innings + ":" + raw.innings_ball_num
        joined = corrections.merge(raw[["event_id", "runs", "extras_type", "is_wicket"]], on="event_id", validate="one_to_one")
        self.assertTrue(joined.recorded_runs.eq(joined.runs.astype(int)).all())
        self.assertTrue(joined.recorded_extras_category.eq(joined.extras_type).all())
        self.assertTrue(joined.loc[joined.reviewed_retirement, "is_wicket"].eq("false").all())
        states = pd.read_parquet(self.out / "verified_preball_states.parquet")
        self.assertFalse(states.event_id.duplicated().any())
        self.assertTrue((states.balls_remaining > 0).all() and (states.wickets_before < 10).all())
        self.assertEqual(set(states.event_id), set(corrections.event_id))

    def test_manifests_raw_hashes_and_frozen_pressure_settings(self):
        manifest = json.loads((self.out / "manifest.json").read_text())
        self.assertEqual(manifest["source_sha256"], fingerprints(self.root / "6af3166e7b922_data_pack"))
        prior = json.loads((self.root / "reports/eda_2026-11-01/manifest.json").read_text())
        self.assertEqual(prior["config_sha256"], sha256(self.root / "configs/analysis_preregistration.json"))
        for directory in (self.out, self.pressure):
            receipt = json.loads((directory / "manifest.json").read_text())
            for name, digest in receipt["output_sha256"].items():
                self.assertEqual(sha256(directory / name), digest, name)
        pressure = json.loads((self.pressure / "manifest.json").read_text())
        self.assertEqual(pressure["reconciliation_manifest_sha256"], sha256(self.out / "manifest.json"))
        gate = json.loads((self.pressure / "model_gate.json").read_text())
        self.assertFalse(gate["models_fitted"] or gate["pressure_rule_changed"])
        if gate["late_phase_has_no_ordinary_controls"]:
            self.assertFalse(gate["global_pressure_change_comparison_ready"])
