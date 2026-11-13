"""Hand calculations, partition isolation and promotion-gate correctness."""

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from rr_pressure.baseline import TARGETS, metrics, pooled_metrics
from rr_pressure.data import sha256
from rr_pressure.reference_audit import CONTEXT, INPUTS, audit_exposures, match_partitions
from rr_pressure.retrospective_reference import (RetrospectivePeers, check_budget, fit_partition,
    historical_comparisons, load_reference_development, reference_gate)
from test_baseline import data as baseline_data


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/retrospective_reference_v1.json").read_text())
VALIDATION = json.loads((ROOT / "configs/baseline_validation_v1.json").read_text())


def data():
    return baseline_data().loc[lambda d: d.year.isin(CONFIG["development_years"]), INPUTS + list(TARGETS)].reset_index(drop=True)


class ReferenceModelTests(unittest.TestCase):
    def test_recursive_means_and_comparators_match_hand_calculation(self):
        config = copy.deepcopy(CONFIG)
        config["prior_events"] = 2
        x = pd.DataFrame(dict(year=[2023, 2023, 2024, 2024], family=["IPL", "T20I", "IPL", "T20I"],
            innings=[1]*4, phase=["01-06"]*4, wicket_band=["0-2"]*4))[CONTEXT]
        model = RetrospectivePeers(config, "runs").fit(x, [4, 0, 0, 0], ["a", "b", "c", "d"])
        expected = (4 + 2 * 1) / 4  # year parent, global mean 1
        for _ in range(4):  # family, innings, phase, wicket band
            expected = (4 + 2 * expected) / 3
        result = model.predict(x)
        self.assertAlmostEqual(result.prediction.iloc[0], expected)
        self.assertEqual(result.global_prediction.iloc[0], 2.)
        self.assertEqual(result.family_prediction.iloc[0], 4.)
        self.assertEqual(result.backoff_depth.iloc[0], 5)
        self.assertEqual(result.finest_peer_events.iloc[0], 1)
        self.assertAlmostEqual(result.own_cell_weight.iloc[0], 1/3)
        self.assertEqual(result.maximum_reference_match_fraction.iloc[0], 1.)

    def test_unseen_finest_cell_and_year_use_training_parents(self):
        d = data()
        model = RetrospectivePeers(CONFIG, "runs").fit(d[CONTEXT], d.bat_runs, d.match_id)
        x = d[CONTEXT].iloc[:2].copy()
        x.iloc[0, x.columns.get_loc("wicket_band")] = "6-9"
        x.iloc[1, x.columns.get_loc("year")] = 2030
        result = model.predict(x)
        self.assertEqual(result.backoff_depth.tolist(), [4, 0])
        self.assertEqual(result.finest_peer_events.tolist(), [0, 0])
        self.assertEqual(result.prediction.iloc[1], model.global_mean)
        self.assertEqual(result.global_prediction.iloc[1], model.global_mean)

    def test_forbidden_predictors_and_nonbinary_or_nonfinite_targets_fail(self):
        d = data()
        for column in ["striker_id", "pressure_full", "bat_runs"]:
            with self.assertRaisesRegex(ValueError, "allowlist"):
                RetrospectivePeers(CONFIG, "runs").fit(d[CONTEXT].assign(**{column: 1}), d.bat_runs, d.match_id)
        for values in [np.full(len(d), np.nan), np.full(len(d), -1)]:
            with self.assertRaisesRegex(ValueError, "Invalid training"):
                RetrospectivePeers(CONFIG, "runs").fit(d[CONTEXT], values, d.match_id)
        with self.assertRaisesRegex(ValueError, "Nonbinary"):
            RetrospectivePeers(CONFIG, "wickets").fit(d[CONTEXT], d.bat_runs, d.match_id)

    def test_all_evaluation_partition_outcomes_leave_every_reference_unchanged(self):
        d = data()
        partitions = match_partitions(d[INPUTS], CONFIG)
        first, models = fit_partition(d, partitions, 0, CONFIG)
        changed = d.copy()
        mask = changed.match_id.isin(partitions.loc[partitions.evaluation_fold.eq(0), "match_id"])
        changed.loc[mask, ["bat_runs", "bowl_runs"]] = 100.
        changed.loc[mask, ["striker_wicket", "bowler_wicket"]] = 1
        second, other_models = fit_partition(changed, partitions, 0, CONFIG)
        self.assertEqual(models, other_models)
        columns = ["prediction", "global_prediction", "family_prediction", "training_scale",
                   "reference_events", "reference_matches", "own_cell_weight"]
        pd.testing.assert_frame_equal(first[columns], second[columns])
        self.assertFalse(first.outcome.equals(second.outcome))
        membership = models["membership"]
        self.assertFalse(set(membership["training_match_ids"]) & set(membership["evaluation_match_ids"]))

    def test_predictions_keep_years_roles_and_complete_match_membership(self):
        d = data()
        partitions = match_partitions(d[INPUTS], CONFIG)
        all_predictions = []
        for fold in [0, 1]:
            p, models = fit_partition(d, partitions, fold, CONFIG)
            self.assertTrue(p.evaluation_fold.eq(fold).all())
            self.assertTrue(p.training_fold.eq(1-fold).all())
            self.assertEqual(set(models["targets"]), set(TARGETS))
            all_predictions.append(p)
        p = pd.concat(all_predictions)
        self.assertFalse(p.duplicated(["event_id", "target"]).any())
        for target, (role, kind) in TARGETS.items():
            expected = d.loc[d.batting_opportunity] if role == "batting" else d
            self.assertEqual(set(p.loc[p.target.eq(target), "event_id"]), set(expected.event_id))
            if kind == "wickets":
                self.assertTrue(p.loc[p.target.eq(target), "prediction"].between(0, 1).all())

    def test_tampered_partition_and_reserved_inputs_are_rejected(self):
        d = data()
        partitions = match_partitions(d[INPUTS], CONFIG)
        altered = partitions.copy()
        altered.loc[0, "evaluation_fold"] = 1 - altered.loc[0, "evaluation_fold"]
        with self.assertRaisesRegex(ValueError, "partition changed"):
            fit_partition(d, altered, 0, CONFIG)
        with self.assertRaisesRegex(ValueError, "Unregistered"):
            fit_partition(d, partitions, 2, CONFIG)
        d["year"] = 2026
        with self.assertRaisesRegex(ValueError, "Development exposures only"):
            fit_partition(d, partitions, 0, CONFIG)

    def test_budget_rejects_extra_setting_or_hidden_refits(self):
        check_budget(CONFIG, 18)
        for field, value in [("development_partition_bundles", 3), ("amended_maximum", 20),
                             ("additional_settings_or_partition_seeds", 1), ("new_target_model_fits_maximum", 20)]:
            config = copy.deepcopy(CONFIG)
            config["budget"][field] = value
            with self.assertRaisesRegex(ValueError, "budget"):
                check_budget(config, 18)

    def test_historical_comparisons_reject_changed_cohort_or_target(self):
        d = data()
        p = pd.concat([fit_partition(d, match_partitions(d[INPUTS], CONFIG), f, CONFIG)[0] for f in [0, 1]])
        old = p[["event_id", "target", "outcome", "prediction", "year"]].copy()
        with self.assertRaisesRegex(ValueError, "cohort mismatch"):
            historical_comparisons(p, {"test": old.iloc[1:]}, VALIDATION)
        old.loc[old.index[0], "outcome"] = 100
        with self.assertRaisesRegex(ValueError, "targets differ"):
            historical_comparisons(p, {"test": old}, VALIDATION)


class ReferenceGateTests(unittest.TestCase):
    def test_fold_alert_blocks_a_clean_pooled_screen(self):
        rows = [dict(prior_events=200, year=year, target=target, model=model, events=100,
            primary_loss=1. if model == "hierarchical" else 2., mae=1., log_loss=1., mean_bias=0.,
            observed_mean=1., predicted_mean=1.) for year in [2023, 2024, 2025]
            for target in TARGETS for model in ["hierarchical", "global", "family"]]
        annual = pd.DataFrame(rows)
        calibration = pd.DataFrame(dict(material_alert=[False]))
        fold_calibration = pd.DataFrame([dict(evaluation_fold=f, target=t, material_alert=f == 0 and t == "bat_runs")
                                         for f in [0, 1] for t in TARGETS])
        support = pd.DataFrame(dict(scheme=["two_fold"], supported_fraction=[1.], parent_unsupported_events=[0]))
        g = reference_gate(annual, pooled_metrics(annual), calibration, fold_calibration, support, VALIDATION, CONFIG)
        self.assertTrue(g["benchmark_gate_passed"])
        self.assertEqual(g["pooled_material_calibration_alerts"], 0)
        self.assertEqual(g["fold_material_calibration_alerts"], 1)
        self.assertFalse(g["ready_for_reserved_evaluation"] or g["reference_scales_frozen_for_final_ratings"])
        fold_calibration["material_alert"] = False
        g = reference_gate(annual, pooled_metrics(annual), calibration, fold_calibration, support, VALIDATION, CONFIG)
        self.assertTrue(g["ready_for_reserved_evaluation"])
        support["supported_fraction"] = .94
        self.assertFalse(reference_gate(annual, pooled_metrics(annual), calibration, fold_calibration,
                                       support, VALIDATION, CONFIG)["ready_for_reserved_evaluation"])


class ReferenceArtifactTests(unittest.TestCase):
    def test_loader_filters_all_performance_reads_to_development(self):
        if not (ROOT / "reports/reference_audit_2026-11-01/manifest.json").exists():
            self.skipTest("Private inputs unavailable")
        original = pd.read_parquet
        target_reads = []

        def guarded(path, **kwargs):
            if path.name == "targets.parquet":
                self.assertEqual(set(kwargs["columns"]), {"event_id", *TARGETS})
                self.assertEqual(kwargs["filters"][0][0], "event_id")
                target_reads.append(kwargs["filters"][0][2])
            return original(path, **kwargs)

        with patch("rr_pressure.retrospective_reference.pd.read_parquet", side_effect=guarded):
            d, partitions, support, originals, upstream = load_reference_development(ROOT, CONFIG)
        self.assertEqual(len(target_reads), 1)
        self.assertEqual(set(target_reads[0]), set(d.event_id))
        self.assertEqual(set(d.year), {2023, 2024, 2025})
        self.assertEqual(len(partitions), 402)

    def test_execution_contracts_and_provenance(self):
        out = ROOT / "reports/retrospective_reference_development_2026-11-01"
        if not (out / "manifest.json").exists():
            self.skipTest("Private reference artifacts unavailable")
        m = json.loads((out / "manifest.json").read_text())
        self.assertEqual(m["candidate_bundles"], 2)
        self.assertEqual(m["target_model_fits"], 8)
        self.assertEqual(m["cumulative_model_bundles"], 20)
        self.assertFalse(m["reserved_outcome_metrics_computed"] or m["player_scores_created"])
        self.assertEqual(m["reference_config_sha256"], sha256(ROOT / "configs/retrospective_reference_v1.json"))
        self.assertEqual(m["validation_config_sha256"], sha256(ROOT / "configs/baseline_validation_v1.json"))
        for name, digest in m["output_sha256"].items():
            self.assertEqual(digest, sha256(out / name), name)
        p = pd.read_parquet(out / "development_predictions.parquet")
        self.assertEqual(set(p.year), {2023, 2024, 2025})
        self.assertFalse(p.duplicated(["event_id", "target"]).any())
        self.assertTrue(p.evaluation_fold.ne(p.training_fold).all())
        for fold in [0, 1]:
            membership = json.loads((out / f"models_fold_{fold}.json").read_text())["membership"]
            self.assertFalse(set(membership["training_match_ids"]) & set(membership["evaluation_match_ids"]))
        scales = json.loads((out / "development_reference_scales.json").read_text())
        gate = json.loads((out / "model_gate.json").read_text())
        self.assertEqual(scales["status"] == "frozen", gate["ready_for_reserved_evaluation"])


if __name__ == "__main__":
    unittest.main()
