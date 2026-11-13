"""Leakage, state contracts and convex model checks for the fixed amendment."""

import copy
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from rr_pressure.baseline import fit_fold, TARGETS
from rr_pressure.context_baseline import (WeightedContextModel, candidate_gate, candidate_metrics,
    candidate_pooled, context_basis, fit_context_fold, sigmoid)
from rr_pressure.data import sha256
from test_baseline import data as original_data, METHOD, VALIDATION


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/context_baseline_v2.json").read_text())
COLUMNS = CONFIG["context_groups"] + CONFIG["required_states"]


def data():
    d = original_data()
    d["legal_balls_before"] = d.event_id.str.rsplit(":", n=1).str[-1].astype(int)
    d["balls_remaining"] = 120 - d.legal_balls_before
    d["score_before"] = 2 * d.legal_balls_before
    d["wickets_before"] = d.legal_balls_before.ge(3).astype(int)
    d["recent_wickets"] = d.wickets_before
    d["chase_target"] = np.where(d.innings.eq(2), 180., np.nan)
    d["runs_required"] = d.chase_target - d.score_before
    return d


class ContextStateTests(unittest.TestCase):
    def test_state_only_basis_and_first_innings_chase_zeros(self):
        d = data()
        matrix, names, counts = context_basis(d[COLUMNS], CONFIG)
        for name in ["chase_target_rate", "required_rate", "required_rate_above_1"]:
            self.assertTrue((matrix[d.innings.eq(1), names.index(name)] == 0).all())
        self.assertEqual(matrix.shape[1], len(names))
        self.assertEqual(counts["required_rate_clipped"], 0)
        for name in ["bat_runs", "pressure_full", "striker_id"]:
            with self.assertRaisesRegex(ValueError, "allowlist"):
                context_basis(d[COLUMNS].assign(**{name: 1}), CONFIG)

    def test_invalid_and_future_target_states_are_rejected(self):
        d = data()[COLUMNS]
        for column, value in [("chase_target", 180.), ("balls_remaining", 0), ("wickets_before", 10)]:
            changed = d.copy()
            changed.loc[0, column] = value
            with self.assertRaises(ValueError):
                context_basis(changed, CONFIG)
        changed = d.copy()
        changed.loc[changed.innings.eq(2), "runs_required"] = 999
        with self.assertRaisesRegex(ValueError, "chase target"):
            context_basis(changed, CONFIG)

    def test_extreme_required_rate_is_clipped_and_disclosed(self):
        d = data()[COLUMNS].loc[lambda x: x.innings.eq(2)].iloc[:1].copy()
        d["legal_balls_before"], d["balls_remaining"] = 119, 1
        d["score_before"], d["runs_required"] = 100, 80
        x, names, diagnostics = context_basis(d, CONFIG)
        self.assertEqual(x[0, names.index("required_rate")], 6.)
        self.assertEqual(diagnostics["required_rate_clipped"], 1)


class ContextNumericsTests(unittest.TestCase):
    def test_weighted_ridge_matches_independent_normal_equation(self):
        x = np.column_stack([np.ones(5), np.arange(5.)])
        y, w = np.array([0., 1., 1., 3., 5.]), np.array([1., 2., 3., 4., 5.])
        model = WeightedContextModel("runs", CONFIG).fit(x, y, w, ["intercept", "x"])
        z = model.transform(x)
        expected = np.linalg.solve(z.T @ np.diag(w) @ z + np.diag([0., 100.]), z.T @ np.diag(w) @ y)
        np.testing.assert_allclose(model.coef, expected)
        self.assertLess(model.gradient_norm, 1e-10)

    def test_logistic_gradient_and_probability_domain(self):
        x = np.column_stack([np.ones(20), np.linspace(-2, 2, 20)])
        y = np.array([0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1])
        w = np.linspace(.2, 1., len(x))
        model = WeightedContextModel("wickets", CONFIG).fit(x, y, w, ["intercept", "x"])
        p, _ = model.predict(x)
        gradient = model.transform(x).T @ (w * (p - y)) + np.array([0., 100.]) * model.coef
        self.assertLessEqual(np.max(np.abs(gradient)) / w.sum(), CONFIG["logistic_gradient_tolerance"])
        self.assertTrue(((p > 0) & (p < 1)).all())
        np.testing.assert_array_equal(sigmoid(np.array([-1000., 0., 1000.])), [0., .5, 1.])

    def test_constant_training_column_is_disabled_without_evaluation_statistics(self):
        x = np.column_stack([np.ones(4), [0., 1., 2., 3.], np.zeros(4)])
        model = WeightedContextModel("runs", CONFIG).fit(x, [1., 2., 3., 4.], np.ones(4), ["intercept", "x", "unused"])
        saved = copy.deepcopy(model.as_dict())
        changed = x.copy()
        changed[:, 2] = 100000.
        np.testing.assert_array_equal(model.predict(x)[0], model.predict(changed)[0])
        self.assertEqual(saved, model.as_dict())
        self.assertFalse(model.active[2])

    def test_failed_convergence_is_not_reported_as_success(self):
        config = copy.deepcopy(CONFIG)
        config["logistic_max_iterations"] = 1
        x = np.column_stack([np.ones(20), np.arange(20.)])
        with self.assertRaisesRegex(ValueError, "did not converge"):
            WeightedContextModel("wickets", config).fit(x, [0] * 10 + [1] * 10, np.ones(20), ["intercept", "x"])


class ContextFoldTests(unittest.TestCase):
    def test_evaluation_outcomes_do_not_affect_fit_predictions_or_scales(self):
        d = data()
        original, _ = fit_fold(d, 2023, 200, METHOD)
        first, models, _ = fit_context_fold(d, 2023, CONFIG, original)
        changed = d.copy()
        changed.loc[changed.year.ge(2023), ["bat_runs", "bowl_runs"]] = 50
        changed.loc[changed.year.ge(2023), ["striker_wicket", "bowler_wicket"]] = 1
        baseline, _ = fit_fold(changed, 2023, 200, METHOD)
        second, changed_models, _ = fit_context_fold(changed, 2023, CONFIG, baseline)
        self.assertEqual(models, changed_models)
        for c in ["prediction", "training_scale", "baseline_prediction"]:
            np.testing.assert_array_equal(first[c], second[c])
        self.assertFalse(first.outcome.equals(second.outcome))
        self.assertEqual(set(first.event_id), set(original.event_id))
        with self.assertRaisesRegex(ValueError, "development years only"):
            fit_context_fold(d, 2026, CONFIG, original)

    def test_metrics_keep_penalty_distinct_from_old_prior_count(self):
        d = data()
        original, _ = fit_fold(d, 2023, 200, METHOD)
        p, _, _ = fit_context_fold(d, 2023, CONFIG, original)
        annual = candidate_metrics(p, VALIDATION)
        pooled = candidate_pooled(annual)
        self.assertNotIn("prior_events", annual)
        self.assertTrue(annual.ridge_penalty.eq(100).all())
        self.assertIn("context_v2", set(pooled.model))

    def test_remaining_alert_blocks_promotion_even_with_loss_improvement(self):
        rows = []
        for year in [2023, 2024, 2025]:
            for target in TARGETS:
                for model in ["context_v2", "global", "family"]:
                    rows.append(dict(ridge_penalty=100, year=year, target=target, model=model, events=100,
                        primary_loss=1. if model == "context_v2" else 2., mae=1., log_loss=1., mean_bias=0., observed_mean=1., predicted_mean=1.))
        annual = pd.DataFrame(rows)
        paired = pd.DataFrame({"target": list(TARGETS), "primary_loss_delta": [-.1] * 4})
        gate = candidate_gate(annual, candidate_pooled(annual), pd.DataFrame({"material_alert": [True]}), paired, VALIDATION, CONFIG)
        self.assertTrue(gate["benchmark_gate_passed"])
        self.assertFalse(gate["ready_for_reserved_evaluation"])
        self.assertEqual(gate["cumulative_model_bundles"], 18)


class ContextArtifactTests(unittest.TestCase):
    def test_private_run_hashes_cohort_and_budget(self):
        out = ROOT / "reports/context_baseline_v2_2026-11-01"
        if not (out / "manifest.json").exists():
            self.skipTest("Private contextual run unavailable")
        m = json.loads((out / "manifest.json").read_text())
        self.assertEqual(m["candidate_config_sha256"], sha256(ROOT / "configs/context_baseline_v2.json"))
        self.assertEqual(m["validation_config_sha256"], sha256(ROOT / "configs/baseline_validation_v1.json"))
        self.assertEqual(m["cumulative_model_bundles"], 18)
        self.assertFalse(m["reserved_outcome_metrics_computed"] or m["player_scores_created"])
        for name, digest in m["output_sha256"].items():
            self.assertEqual(sha256(out / name), digest, name)
        p = pd.read_parquet(out / "development_predictions.parquet")
        old = pd.read_parquet(ROOT / "reports/baseline_development_2026-11-01/default_development_predictions.parquet")
        self.assertEqual(set(zip(p.event_id, p.target)), set(zip(old.event_id, old.target)))
        self.assertTrue(p.training_last_date.lt(p.match_date).all())
        self.assertEqual(set(p.year), {2023, 2024, 2025})


if __name__ == "__main__":
    unittest.main()
