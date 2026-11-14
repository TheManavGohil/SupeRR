"""Approved descriptive rating algebra and joint peer/player uncertainty."""

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from rr_pressure.data import sha256
from rr_pressure.descriptive_rating import (cell_blocks, change_components, load_development, mix,
    multiply, order_ratings, outcome_scales, pressure_components, primary_eligibility,
    summarize_draws, validate_config, evaluate_development)
from rr_pressure.player_evidence import CONTEXT, pressure_peer_support


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/descriptive_rating_v2.json").read_text())
BASE = json.loads((ROOT / "configs/supported_method_v1.json").read_text())


def events():
    rows = []
    for player, outcomes in [("p", [(4, 0), (2, 1)]), ("q", [(1, 1), (1, 0)])]:
        for i, (runs, wickets) in enumerate(outcomes):
            rows.append(dict(event_id=f"{player}:{i}", match_id=f"m{i}", role="batting", player_id=player,
                family="IPL", year=2025, innings=1, phase="16-20", wicket_band="0-2", pressure_full=True,
                weight=1., weight_squared=1., runs=runs, wickets=wickets, weighted_runs=float(runs), weighted_wickets=float(wickets)))
    return pd.DataFrame(rows)


def components(d, multiplicities=None, role="batting", pseudo=2.):
    matches = pd.DataFrame({"match_id": ["m0", "m1"]})
    cells = d[CONTEXT].drop_duplicates().reset_index(drop=True)
    copies = np.ones((1, 2)) if multiplicities is None else np.array(multiplicities, dtype=float)
    total = multiply(cell_blocks(d, matches, cells), copies)
    own = multiply(cell_blocks(d.loc[d.player_id.eq("p")], matches, cells), copies)
    result = pressure_components(own, total, {"runs": 1., "wickets": 1.}, CONFIG["orientation"][role], pseudo)
    return result, own, total


class DescriptiveAlgebraTests(unittest.TestCase):
    def test_hand_calculated_leave_player_out_score_and_direction(self):
        result, _, _ = components(events())
        self.assertAlmostEqual(result["runs_raw"][0], 2.)
        self.assertAlmostEqual(result["runs"][0], 1.)
        self.assertAlmostEqual(result["wickets_raw"][0], 0.)
        self.assertAlmostEqual(mix(result, (.6, .4))[0], .6)
        bowling, _, _ = components(events(), role="bowling")
        self.assertAlmostEqual(mix(bowling, (.6, .4))[0], -.6)

    def test_own_outcome_changes_do_not_change_own_peer_benchmark(self):
        d = events()
        before, own, total = components(d)
        d.loc[d.player_id.eq("p"), "weighted_runs"] += 3
        after, own2, total2 = components(d)
        np.testing.assert_allclose(total2["runs"] - own2["runs"], total["runs"] - own["runs"])
        self.assertGreater(after["runs"][0], before["runs"][0])
        d = events()
        d.loc[d.player_id.eq("p"), "weighted_wickets"] += .25
        changed, _, _ = components(d)
        self.assertLess(changed["wickets"][0], before["wickets"][0])

    def test_resampling_recomputes_peer_means_and_linear_square_weights(self):
        d = events()
        d.loc[d.player_id.eq("p"), "weighted_runs"] = [4., 4.]
        d.loc[d.player_id.eq("q"), "weighted_runs"] = [0., 6.]
        result, _, _ = components(d, [[1, 1], [2, 0], [0, 2]])
        np.testing.assert_allclose(result["runs_raw"], [1., 4., -2.])
        # Two resampled observations, not four squared copies or independent balls.
        np.testing.assert_allclose(result["effective_events"], [2., 2., 2.])
        np.testing.assert_allclose(result["runs"], [.5, 2., -1.])

    def test_recency_weighted_mean_and_effective_count(self):
        d = events()
        d.loc[d.match_id.eq("m1"), "weight"] = .5
        d["weight_squared"] = d.weight ** 2
        d["weighted_runs"] = d.runs * d.weight
        d["weighted_wickets"] = d.wickets * d.weight
        result, _, _ = components(d)
        self.assertAlmostEqual(result["runs_raw"][0], 5 / 1.5 - 1)
        self.assertAlmostEqual(result["effective_events"][0], 1.8)

    def test_zero_peer_mass_invalidates_positive_own_cell(self):
        d = events()
        d.loc[d.player_id.eq("q"), "match_id"] = "m1"
        result, _, _ = components(d, [[2, 0], [0, 2]])
        self.assertFalse(result["valid"][0])
        self.assertTrue(np.isnan(result["runs"][0]))
        self.assertTrue(result["valid"][1])

    def test_zero_own_cell_can_have_zero_weight_without_invalidating_level(self):
        d = events()
        d.loc[d.match_id.eq("m1"), "wicket_band"] = "3-5"
        result, _, _ = components(d, [[2, 0]])
        self.assertTrue(result["valid"][0])
        self.assertAlmostEqual(result["runs_raw"][0], 3.)
        # Same missing cell makes an ordinary-change comparison invalid.
        _, own, _ = components(d, [[2, 0]])
        change = change_components(own, own, {"runs": 1., "wickets": 1.}, CONFIG["orientation"]["batting"], 2.)
        self.assertFalse(change["valid"][0])

    def test_invalid_multiplicity_and_incomplete_match_universe_fail(self):
        d = events()
        matches = pd.DataFrame({"match_id": ["m0", "m1"]})
        cells = d[CONTEXT].drop_duplicates()
        blocks = cell_blocks(d, matches, cells)
        for invalid in [np.array([[.5, 1.]]), np.array([[-1., 1.]])]:
            with self.assertRaisesRegex(ValueError, "integers"):
                multiply(blocks, invalid)
        with self.assertRaisesRegex(ValueError, "match universe"):
            cell_blocks(d, matches.iloc[:1], cells)

    def test_supported_change_algebra_and_lost_group(self):
        pressure = {"mass": np.array([[4., 2.], [4., 2.]]), "squared": np.array([[4., 2.], [4., 2.]]),
            "runs": np.array([[12., 16.], [12., 16.]]), "wickets": np.zeros((2, 2))}
        ordinary = {"mass": np.array([[2., 4.], [0., 4.]]), "squared": np.array([[2., 4.], [0., 4.]]),
            "runs": np.array([[2., 16.], [0., 16.]]), "wickets": np.zeros((2, 2))}
        change = change_components(pressure, ordinary, {"runs": 1., "wickets": 1.}, CONFIG["orientation"]["batting"], 2.)
        self.assertAlmostEqual(change["runs_raw"][0], 2 / 3 * 2 + 1 / 3 * 4)
        self.assertAlmostEqual(change["paired_effective_events"][0], 2.4)
        self.assertAlmostEqual(change["runs"][0], change["runs_raw"][0] * 2.4 / 4.4)
        self.assertTrue(np.isnan(change["runs"][1]))

    def test_weighted_outcome_scales_use_population_variance_and_floors(self):
        d = events()
        scale = outcome_scales(d, CONFIG)
        self.assertAlmostEqual(scale["batting"]["runs"], np.std([4., 2., 1., 1.]))
        self.assertAlmostEqual(scale["batting"]["wickets"], .5)
        d["wickets"] = 0
        self.assertEqual(outcome_scales(d, CONFIG)["batting"]["wickets"], .01)

    def test_draw_reliability_and_prespecified_ties(self):
        row = summarize_draws(1., np.array([1.] * 94 + [np.nan] * 6), CONFIG)
        self.assertFalse(row["interval_reliable"])
        self.assertTrue(np.isnan(row["p10"]))
        table = pd.DataFrame([dict(role="batting", player_id=p, variant="default_60_40", point=1., p10=0., interval_reliable=True) for p in ["c", "a", "b"]])
        eligible = table[["role", "player_id"]].assign(primary_sample_ready=True, peer_pressure_matches=[8, 8, 9])
        result = order_ratings(table, eligible).sort_values("rank")
        self.assertEqual(result.player_id.tolist(), ["b", "a", "c"])
        eligible.loc[eligible.player_id.eq("b"), "primary_sample_ready"] = False
        result = order_ratings(table, eligible)
        self.assertTrue(result.loc[result.player_id.eq("b"), "selection_score"].isna().all())

    def test_activation_rejects_threshold_changes_or_reserved_execution(self):
        validate_config(ROOT, CONFIG)
        for change in [{"reserved_outcomes_permitted": True}, {"execution_window": "final"},
            {"outcome_weights": {"default": [.9, .1]}}]:
            altered = copy.deepcopy(CONFIG)
            altered.update(change)
            with self.assertRaises(ValueError):
                validate_config(ROOT, altered)

    def test_complete_synthetic_execution_keeps_variants_on_the_same_cohort(self):
        d = events()
        d["supported"] = False
        c = pd.DataFrame([dict(role="batting", player_id=p, level_sample_eligible=True, coverage_ready=True,
            pressure_events=2, pressure_weight_sum=2., change_sample_eligible=False) for p in ["p", "q"]])
        base = copy.deepcopy(BASE)
        base.update(peer_minimum_events_per_group=2, peer_minimum_matches_per_group=2,
            minimum_pressure_matches=1, minimum_effective_pressure_events=1)
        base["roles"]["batting"].update(minimum_total_events=1, minimum_pressure_events=1)
        audit = pressure_peer_support(d, base)
        result = evaluate_development(d, c, audit, CONFIG, base, {"batting": {"runs": 1., "wickets": 1.}})
        self.assertEqual(len(result["ratings"]), 6)
        self.assertTrue(result["ratings"].selection_ready.all())
        self.assertTrue(result["eligibility"].primary_sample_ready.all())
        self.assertEqual(len(result["influence"]), 6)
        self.assertEqual(set(result["ratings"].variant), {"default_60_40", "runs_wickets_50_50", "runs_wickets_70_30"})
        self.assertEqual(result["draws"].shape, (1000, 2))


class DevelopmentArtifactTests(unittest.TestCase):
    def test_loader_uses_only_validated_development_ledger(self):
        if not (ROOT / "reports/player_evidence_development_2026-11-01/manifest.json").exists():
            self.skipTest("Private evidence unavailable")
        original = pd.read_parquet
        reads = []
        def guarded(path, **kwargs):
            self.assertEqual(path.name, "event_role_ledger.parquet")
            self.assertEqual(kwargs["filters"], [("year", "in", [2023, 2024, 2025])])
            result = original(path, **kwargs)
            self.assertFalse(result.year.eq(2026).any())
            reads.append(path)
            return result
        with patch("rr_pressure.descriptive_rating.pd.read_parquet", side_effect=guarded):
            ledger, cohort, base, receipt = load_development(ROOT, CONFIG)
        self.assertEqual(len(reads), 1)
        self.assertEqual(ledger.match_id.nunique(), 402)


if __name__ == "__main__":
    unittest.main()
