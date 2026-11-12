"""Training isolation, shrinkage, role exposure and match-level validation."""

import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from rr_pressure.baseline import (HistoricalPeers, TARGETS, development_gate, fit_fold,
    match_draws, metrics, pooled_metrics)
from rr_pressure.data import sha256
from rr_pressure.supported_method import FEATURES


ROOT = Path(__file__).resolve().parents[1]
METHOD = json.loads((ROOT / "configs/supported_method_v1.json").read_text())
VALIDATION = json.loads((ROOT / "configs/baseline_validation_v1.json").read_text())


def data():
    rows = []
    for year in [2022, 2023, 2024, 2025, 2026]:
        for family in ["IPL", "T20I"]:
            for match in range(2):
                for innings in [1, 2]:
                    for ball in range(4):
                        rows.append(dict(event_id=f"{year}:{family}:{match}:{innings}:{ball}",
                            match_id=f"{year}:{family}:{match}", match_date=f"{year}-05-01", year=year,
                            family=family, innings=innings, phase="01-06", wicket_band="0-2", pressure_full=ball > 1,
                            batting_opportunity=ball != 3, bat_runs=float(ball), bowl_runs=float(ball + (ball == 3)),
                            striker_wicket=int(ball == 2), bowler_wicket=int(ball == 2)))
    return pd.DataFrame(rows)


class PeerModelTests(unittest.TestCase):
    def test_recursive_means_match_hand_calculation(self):
        x = pd.DataFrame({"family": ["IPL", "IPL", "T20I", "T20I"], "innings": [1, 2, 1, 2],
            "phase": ["01-06"] * 4, "wicket_band": ["0-2"] * 4})
        model = HistoricalPeers(METHOD["expectation_model"]["hierarchy"], 2).fit(x, [4., 0., 0., 0.])
        family = (4 + 2 * 1) / 4
        innings = (4 + 2 * family) / 3
        phase = (4 + 2 * innings) / 3
        finest = (4 + 2 * phase) / 3
        result = model.predict(x)
        self.assertAlmostEqual(result.prediction.iloc[0], finest)
        self.assertEqual(result.family_prediction.iloc[0], 2.)
        self.assertTrue(result.backoff_depth.eq(4).all())

    def test_unseen_cell_and_family_back_off_without_target_encoding(self):
        d = data().loc[lambda x: x.year.eq(2022)]
        model = HistoricalPeers(METHOD["expectation_model"]["hierarchy"], 200).fit(d[FEATURES], d.bat_runs)
        x = d[FEATURES].iloc[:2].copy()
        x.iloc[0, x.columns.get_loc("wicket_band")] = "6-9"
        x.iloc[1, x.columns.get_loc("family")] = "UNSEEN"
        p = model.predict(x)
        self.assertEqual(p.backoff_depth.tolist(), [3, 0])
        self.assertEqual(p.prediction.iloc[1], model.global_mean)
        self.assertEqual(p.family_prediction.iloc[1], model.global_mean)

    def test_player_id_or_outcome_cannot_enter_feature_matrix(self):
        d = data()
        for column in ["player_id", "pressure_full", "bat_runs"]:
            with self.assertRaisesRegex(ValueError, "allowlist"):
                HistoricalPeers(METHOD["expectation_model"]["hierarchy"], 200).fit(d[FEATURES].assign(**{column: 1}), d.bat_runs)

    def test_evaluation_and_future_outcomes_do_not_change_predictions_or_scales(self):
        d = data()
        first, models = fit_fold(d, 2023, 200, METHOD)
        changed = d.copy()
        changed.loc[changed.year.ge(2023), ["bat_runs", "bowl_runs"]] = 100.
        changed.loc[changed.year.ge(2023), ["striker_wicket", "bowler_wicket"]] = 1
        second, new_models = fit_fold(changed, 2023, 200, METHOD)
        self.assertEqual(models, new_models)
        for c in ["prediction", "global_prediction", "family_prediction", "training_scale"]:
            np.testing.assert_array_equal(first[c], second[c])
        self.assertFalse(first.outcome.equals(second.outcome))

    def test_role_denominators_and_training_membership(self):
        d = data()
        predictions, models = fit_fold(d, 2023, 200, METHOD)
        self.assertTrue(predictions.year.eq(2023).all())
        self.assertTrue(predictions.training_last_date.lt("2023-01-01").all())
        year = d.loc[d.year.eq(2023)]
        for target, (role, _) in TARGETS.items():
            expected = year.loc[year.batting_opportunity] if role == "batting" else year
            self.assertEqual(set(predictions.loc[predictions.target.eq(target), "event_id"]), set(expected.event_id))
            self.assertEqual(models[target]["training_events"], len(expected))
        with self.assertRaisesRegex(ValueError, "development years only"):
            fit_fold(d, 2026, 200, METHOD)

    def test_match_date_conflict_fails(self):
        d = data()
        d.loc[0, "match_date"] = "2022-05-02"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            fit_fold(d, 2023, 200, METHOD)


class ValidationTests(unittest.TestCase):
    def test_bernoulli_loss_handles_zero_and_one_without_mutating_prediction(self):
        p, _ = fit_fold(data(), 2023, 200, METHOD)
        p["prediction"] = 0.
        p["family_prediction"] = 1.
        result = metrics(p, VALIDATION)
        self.assertTrue(np.isfinite(result.log_loss.dropna()).all())
        self.assertTrue(p.prediction.eq(0).all())

    def test_pooled_metrics_weight_exposure_instead_of_averaging_years(self):
        rows = []
        for year, n, value in [(2023, 1, 0.), (2024, 3, 4.)]:
            rows.append(dict(prior_events=200, target="bat_runs", model="hierarchical", events=n, year=year,
                primary_loss=value, mae=value, log_loss=np.nan, mean_bias=value, observed_mean=value, predicted_mean=value))
        self.assertAlmostEqual(pooled_metrics(pd.DataFrame(rows)).primary_loss.iloc[0], 3.)

    def test_bootstrap_counts_whole_matches_once_across_targets_and_innings(self):
        p, _ = fit_fold(data(), 2023, 200, METHOD)
        matches, weights = match_draws(p, VALIDATION)
        self.assertEqual(len(matches), 4)
        self.assertEqual(weights.shape, (1000, 4))
        for _, group in matches.groupby(["family", "year"]):
            self.assertTrue((weights[:, group.index].sum(axis=1) == len(group)).all())
        matches2, weights2 = match_draws(p.sample(frac=1, random_state=8), VALIDATION)
        pd.testing.assert_frame_equal(matches, matches2)
        np.testing.assert_array_equal(weights, weights2)

    def test_good_loss_does_not_erase_calibration_alert(self):
        rows = []
        for year in [2023, 2024, 2025]:
            for target in TARGETS:
                for model in ["hierarchical", "global", "family"]:
                    rows.append(dict(prior_events=200, year=year, target=target, model=model, events=100,
                        primary_loss=1. if model == "hierarchical" else 2., mae=1., log_loss=1., mean_bias=0., observed_mean=1., predicted_mean=1.))
        annual = pd.DataFrame(rows)
        gate = development_gate(annual, pooled_metrics(annual), pd.DataFrame({"material_alert": [True]}), VALIDATION)
        self.assertTrue(gate["benchmark_gate_passed"])
        self.assertFalse(gate["ready_for_reserved_evaluation"])
        self.assertFalse(gate["reference_scales_frozen_for_final_ratings"])


class BaselineArtifactTests(unittest.TestCase):
    def test_outputs_are_development_only_and_match_recorded_provenance(self):
        out = ROOT / "reports/baseline_development_2026-11-01"
        if not (out / "manifest.json").exists():
            self.skipTest("Private baseline artifacts unavailable")
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertTrue(manifest["models_fitted"])
        self.assertFalse(manifest["reserved_outcome_metrics_computed"] or manifest["player_scores_created"])
        self.assertEqual(manifest["model_fold_setting_bundles"], 15)
        self.assertEqual(manifest["method_config_sha256"], sha256(ROOT / "configs/supported_method_v1.json"))
        self.assertEqual(manifest["validation_config_sha256"], sha256(ROOT / "configs/baseline_validation_v1.json"))
        for name, digest in manifest["output_sha256"].items():
            self.assertEqual(sha256(out / name), digest, name)
        predictions = pd.read_parquet(out / "default_development_predictions.parquet")
        self.assertEqual(set(predictions.year), {2023, 2024, 2025})
        self.assertFalse(predictions.duplicated(["event_id", "target"]).any())
        self.assertTrue(predictions.training_last_date.lt(predictions.match_date).all())
        self.assertNotIn("striker_id", predictions)
        self.assertNotIn("bowler_id", predictions)


if __name__ == "__main__":
    unittest.main()
