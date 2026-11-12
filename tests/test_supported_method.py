"""Method contracts, chronological leakage and supported-estimand invariants."""

import copy
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from rr_pressure.data import sha256
from rr_pressure.supported_method import (FEATURES, blend_components, chronological_folds,
    delivery_tables, eligibility, estimate_components, selection_interval)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/supported_method_v1.json").read_text())


def events():
    rows = []
    for year in range(2022, 2027):
        for match in range(2):
            for pressure in (False, True):
                rows.append(dict(event_id=f"{year}:{match}:{pressure}", match_id=f"{year}:{match}",
                    match_date=f"{year}-05-01", year=year, innings=1, overid=8, wickets_before=2,
                    family="IPL", striker_id="batter", bowler_id="bowler", pressure_full=pressure,
                    extras_wides=0, extras_noballs=0, extras_byes=0, extras_legbyes=0,
                    batter_runs=2, is_wicket=False, dismissal_type="", dismissed_player_id=""))
    return pd.DataFrame(rows)


class MethodTests(unittest.TestCase):
    def test_targets_and_role_filters_never_enter_features(self):
        d = events()
        f, ids, targets = delivery_tables(d)
        d.loc[0, ["batter_runs", "extras_wides", "extras_noballs"]] = [6, 2, 1]
        d.loc[0, ["is_wicket", "dismissal_type", "dismissed_player_id"]] = [True, "Stump", "batter"]
        changed, changed_ids, changed_targets = delivery_tables(d)
        pd.testing.assert_frame_equal(f, changed)
        self.assertEqual(f.columns.tolist(), ["event_id"] + FEATURES)
        self.assertTrue(ids.loc[0, "batting_opportunity"])
        self.assertFalse(changed_ids.loc[0, "batting_opportunity"])
        self.assertEqual(changed_targets.loc[0, "bowl_runs"], 9)
        self.assertEqual(changed_targets.loc[0, "bowler_wicket"], 1)
        self.assertEqual(targets.loc[0, "bowl_runs"], 2)

    def test_runout_and_byes_have_correct_attribution(self):
        d = events()
        d.loc[0, ["is_wicket", "dismissal_type", "dismissed_player_id"]] = [True, "Run Out", "non_striker"]
        d.loc[0, ["extras_byes", "extras_legbyes"]] = [4, 3]
        _, _, targets = delivery_tables(d)
        self.assertEqual(targets.loc[0, "bowl_runs"], 2)
        self.assertEqual(targets.loc[0, "bowler_wicket"], 0)
        self.assertEqual(targets.loc[0, "striker_wicket"], 0)

    def test_all_folds_are_match_disjoint_and_strictly_chronological(self):
        _, identities, _ = delivery_tables(events())
        folds, summary = chronological_folds(identities, CONFIG)
        for _, fold in folds.groupby("fold_year"):
            train = fold.loc[fold.partition.eq("train")]
            evaluation = fold.loc[fold.partition.eq("evaluate")]
            self.assertFalse(set(train.match_id) & set(evaluation.match_id))
            self.assertLess(train.match_date.max(), evaluation.match_date.min())
        self.assertEqual(summary.train_matches.tolist(), [2, 4, 6, 8])
        self.assertFalse(folds.loc[folds.partition.eq("evaluate"), "year"].eq(2022).any())
        self.assertFalse(folds.loc[folds.partition.eq("train"), "year"].eq(2026).any())

    def test_date_conflicts_and_postcutoff_events_fail_closed(self):
        _, identities, _ = delivery_tables(events())
        changed = identities.copy()
        changed.loc[0, "match_date"] = "2022-05-02"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            chronological_folds(changed, CONFIG)
        changed = identities.copy()
        changed.loc[changed.year.eq(2026), "match_date"] = "2026-11-02"
        with self.assertRaisesRegex(ValueError, "frozen date"):
            chronological_folds(changed, CONFIG)

    def test_support_requires_same_year_and_ignores_outcomes(self):
        config = copy.deepcopy(CONFIG)
        for key in ["peer_minimum_events_per_group", "peer_minimum_matches_per_group",
                    "player_minimum_events_per_group", "player_minimum_matches_per_group"]:
            config[key] = 2
        d = events()
        d = d.loc[d.year.isin([2023, 2024])].copy()
        # Ordinary evidence only in 2023; pressure evidence only in 2024.
        d["pressure_full"] = d.year.eq(2024)
        features, ids, _ = delivery_tables(d)
        exposures = ids.merge(features, on="event_id")
        source = d.assign(extras_type="None")
        players, cells, _ = eligibility(exposures, source, config, "batting", "2025-12-31")
        self.assertFalse(cells.supported.any())
        self.assertEqual(players.supported_pressure_events.sum(), 0)
        exposures["batter_runs"] = 999
        source["batter_runs"] = -999
        again, _, _ = eligibility(exposures, source, config, "batting", "2025-12-31")
        pd.testing.assert_frame_equal(players, again)

    def test_level_does_not_require_ordinary_but_change_does(self):
        config = copy.deepcopy(CONFIG)
        config["roles"]["batting"]["minimum_total_events"] = 2
        config["roles"]["batting"]["minimum_pressure_events"] = 2
        config["minimum_pressure_matches"] = 2
        config["minimum_effective_pressure_events"] = 2
        d = events().loc[lambda x: x.year.eq(2023)].copy()
        d["pressure_full"] = True
        features, ids, _ = delivery_tables(d)
        players, _, _ = eligibility(ids.merge(features, on="event_id"), d.assign(extras_type="None"), config, "batting", "2025-12-31")
        self.assertTrue(players.level_sample_eligible.all())
        self.assertFalse(players.change_sample_eligible.any())
        self.assertFalse(players.blend_sample_eligible.any())

    def test_empty_retention_stays_visible(self):
        d = events()
        features, ids, _ = delivery_tables(d)
        players, cells, _ = eligibility(ids.merge(features, on="event_id").iloc[:0], d.assign(extras_type="None"), CONFIG, "batting", "2026-11-01")
        self.assertEqual(players.source_events.sum(), len(d))
        self.assertEqual(players.retained_events.sum(), 0)
        self.assertFalse(players.coverage_ready.any())
        self.assertTrue(cells.empty)

    def test_source_denominator_must_contain_every_kept_event(self):
        d = events()
        features, ids, _ = delivery_tables(d)
        with self.assertRaisesRegex(ValueError, "source denominator"):
            eligibility(ids.merge(features, on="event_id"), d.iloc[1:].assign(extras_type="None"), CONFIG, "bowling", "2026-11-01")


def contributions():
    rows = []
    for cell, p_count, o_count, p_value, o_value in [("a", 4, 2, 3, 1), ("b", 2, 4, 8, 4)]:
        for pressure, count, value in [(True, p_count, p_value), (False, o_count, o_value)]:
            for i in range(count):
                rows.append(dict(match_id=f"{cell}:{pressure}", cell=cell, pressure_full=pressure, weight=1., contribution=value))
    rows.append(dict(match_id="late", cell="late", pressure_full=True, weight=1., contribution=100.))
    return pd.DataFrame(rows)


class EstimandTests(unittest.TestCase):
    def test_supported_change_uses_pressure_mix_and_excludes_unsupported_late(self):
        result = estimate_components(contributions(), pd.DataFrame({"cell": ["a", "b"]}), ["cell"], 2.)
        self.assertAlmostEqual(result["level_raw"], (4 * 3 + 2 * 8 + 100) / 7)
        self.assertAlmostEqual(result["change_raw"], 2 / 3 * 2 + 1 / 3 * 4)
        self.assertAlmostEqual(result["paired_effective_events"], 2.4)
        self.assertAlmostEqual(result["change"], result["change_raw"] * 2.4 / 4.4)

    def test_lost_bootstrap_group_is_missing_not_dropped_or_zero(self):
        d = contributions()
        copies = {m: 1 for m in d.match_id.unique() if m != "a:False"}
        result = estimate_components(d, pd.DataFrame({"cell": ["a", "b"]}), ["cell"], 2., copies)
        self.assertFalse(result["change_available"])
        self.assertTrue(np.isnan(result["change"]))
        self.assertTrue(np.isfinite(result["level"]))
        self.assertTrue(all(np.isnan(v) for v in blend_components(result["level"], result["change"], CONFIG, True).values()))

    def test_repeated_match_copies_have_correct_effective_count(self):
        d = contributions()
        cells = pd.DataFrame({"cell": ["a", "b"]})
        point = estimate_components(d, cells, ["cell"], 2.)
        twice = estimate_components(d, cells, ["cell"], 2., dict.fromkeys(d.match_id.unique(), 2))
        self.assertAlmostEqual(twice["pressure_effective_events"], 2 * point["pressure_effective_events"])
        self.assertAlmostEqual(twice["paired_effective_events"], 2 * point["paired_effective_events"])
        self.assertAlmostEqual(twice["change_raw"], point["change_raw"])

    def test_recency_weights_control_means_and_effective_counts(self):
        d = pd.DataFrame({"match_id": ["a", "b", "a", "b"], "cell": ["x"] * 4,
            "pressure_full": [True, True, False, False], "weight": [1., .5, 1., .5],
            "contribution": [4., 1., 2., 0.]})
        result = estimate_components(d, pd.DataFrame({"cell": ["x"]}), ["cell"], 2.)
        self.assertAlmostEqual(result["level_raw"], 3.)
        self.assertAlmostEqual(result["pressure_effective_events"], 1.8)
        self.assertAlmostEqual(result["change_raw"], 3 - 2 / 1.5)
        self.assertAlmostEqual(result["paired_effective_events"], .9)

    def test_both_blends_share_missingness_and_eligibility(self):
        self.assertEqual(blend_components(2., 1., CONFIG, True), {"default": 1.7, "registered_variant": 1.5})
        self.assertTrue(all(np.isnan(v) for v in blend_components(2., 1., CONFIG, False).values()))
        self.assertTrue(all(np.isnan(v) for v in blend_components(2., np.nan, CONFIG, True).values()))

    def test_invalid_draws_block_selection_instead_of_disappearing(self):
        result = selection_interval([1.] * 94 + [np.nan] * 6, CONFIG)
        self.assertEqual(result["finite_fraction"], .94)
        self.assertTrue(np.isnan(result["selection_score"]))
        self.assertEqual(selection_interval([1.] * 95 + [np.nan] * 5, CONFIG)["selection_score"], 1.)
        self.assertTrue(np.isnan(selection_interval([], CONFIG)["selection_score"]))


class MethodArtifactTests(unittest.TestCase):
    def test_frozen_outputs_provenance_and_no_models(self):
        out = ROOT / "reports/supported_method_2026-11-01"
        if not (out / "manifest.json").exists():
            self.skipTest("Private method preflight unavailable")
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(manifest["config_sha256"], sha256(ROOT / "configs/supported_method_v1.json"))
        self.assertFalse(manifest["models_fitted"] or manifest["player_scores_created"] or manifest["reserved_outcome_metrics_computed"])
        for name, digest in manifest["output_sha256"].items():
            self.assertEqual(sha256(out / name), digest, name)
        features = pd.read_parquet(out / "features.parquet")
        self.assertEqual(features.columns.tolist(), ["event_id"] + FEATURES)
        identities = pd.read_parquet(out / "identities_and_exposures.parquet")
        targets = pd.read_parquet(out / "targets.parquet")
        self.assertEqual(features.event_id.tolist(), identities.event_id.tolist())
        self.assertEqual(features.event_id.tolist(), targets.event_id.tolist())


if __name__ == "__main__":
    unittest.main()
