"""Observed evidence attribution, supported comparisons and temporal boundary."""

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from rr_pressure.data import sha256
from rr_pressure.player_evidence import (KEY, CONTEXT, load_evidence, rate_draws, role_ledger,
    summarize, supported_comparisons, uncertainty, validate_contract)
from rr_pressure.supported_method import delivery_tables


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/player_evidence_v1.json").read_text())
METHOD = json.loads((ROOT / "configs/supported_method_v1.json").read_text())


def fixture():
    rows = []
    for i, (pressure, runs, wicket) in enumerate([(True, 4, False), (True, 2, True), (False, 1, False), (False, 0, False)]):
        rows.append(dict(event_id=str(i), match_id="a" if i % 2 == 0 else "b", match_date="2025-12-31",
            year=2025, family="IPL", innings=1, overid=8, wickets_before=2, striker_id="bat",
            bowler_id="bowl", striker_name="Batter", bowler_name="Bowler", pressure_full=pressure,
            late=False, collapse=pressure, tight_chase=False, extras_wides=0, extras_noballs=0,
            extras_byes=0, extras_legbyes=0, batter_runs=runs, is_wicket=wicket,
            is_four=runs == 4, is_six=runs == 6,
            dismissal_type="Caught" if wicket else "", dismissed_player_id="bat" if wicket else ""))
    d = pd.DataFrame(rows)
    features, ids, targets = delivery_tables(d)
    for col in features:
        if col not in d:
            d[col] = features[col]
    for col in targets:
        if col not in d:
            d[col] = targets[col]
    d["batting_opportunity"] = ids.batting_opportunity
    cells = pd.DataFrame([dict(role=role, player_id=player, family="IPL", year=2025,
        innings=1, phase="07-15", wicket_band="0-2", supported=True)
        for role, player in [("batting", "bat"), ("bowling", "bowl")]])
    return d, cells


def cohort():
    return pd.DataFrame([dict(role=role, player_id=player, level_sample_eligible=True,
        change_sample_eligible=True, supported_pressure_events=2, supported_pressure_matches=2,
        supported_ordinary_events=2, supported_ordinary_matches=2, supported_pressure_fraction=1.)
        for role, player in [("batting", "bat"), ("bowling", "bowl")]])


class PlayerEvidenceTests(unittest.TestCase):
    def test_contract_rejects_reserved_scope_and_score_permissions(self):
        validate_contract(CONFIG, METHOD)
        for key, value in [("years", [2023, 2024, 2025, 2026]), ("reference_date", "2026-11-01"),
            ("model_fits_permitted", True), ("composite_ratings_permitted", True),
            ("full_dossier_rendering_permitted", True)]:
            changed = copy.deepcopy(CONFIG)
            changed[key] = value
            with self.assertRaises(ValueError):
                validate_contract(changed, METHOD)

    def test_batting_and_bowling_exposures_wides_noballs_byes_runout(self):
        d, cells = fixture()
        d.loc[0, ["extras_wides", "extras_noballs", "extras_byes", "is_wicket", "dismissal_type", "dismissed_player_id"]] = [2, 1, 4, True, "Run Out", "other"]
        _, ids, targets = delivery_tables(d)
        d["batting_opportunity"] = ids.batting_opportunity
        d[TARGET_COLUMNS] = targets[TARGET_COLUMNS]
        ledger = role_ledger(d, cells, CONFIG)
        self.assertEqual(len(ledger.loc[ledger.role.eq("batting")]), 3)
        bowling = ledger.loc[ledger.role.eq("bowling") & ledger.event_id.eq("0")].iloc[0]
        self.assertEqual(bowling.runs, 7)  # batter 4 + wides 2 + no-ball 1; byes excluded
        self.assertEqual(bowling.wickets, 0)
        self.assertEqual(bowling.excluded_dismissal_event, 1)
        self.assertEqual(bowling.own_noncredited_dismissal, 0)
        self.assertFalse(ledger.loc[ledger.event_id.eq("0"), "role"].eq("batting").any())

    def test_summaries_and_supported_difference_are_hand_calculated(self):
        d, cells = fixture()
        ledger = role_ledger(d, cells, CONFIG)
        contexts = summarize(ledger, KEY + CONTEXT + ["pressure_full", "supported"])
        result, paired = supported_comparisons(contexts, cohort())
        self.assertEqual(len(paired), 2)
        for _, row in result.iterrows():
            self.assertAlmostEqual(row.runs_pressure_per_100, 300.)
            self.assertAlmostEqual(row.runs_ordinary_per_100, 50.)
            self.assertAlmostEqual(row.headline_runs_difference_per_100, 250.)
            self.assertAlmostEqual(row.headline_wickets_difference_per_100, 50.)
        summary = summarize(ledger, KEY + ["pressure_full"])
        self.assertEqual(summary.opportunities.sum(), len(ledger))
        self.assertTrue(summary.effective_opportunities.eq(2).all())

    def test_missing_change_never_becomes_zero_or_headline(self):
        d, cells = fixture()
        cells["supported"] = False
        contexts = summarize(role_ledger(d, cells, CONFIG), KEY + CONTEXT + ["pressure_full", "supported"])
        c = cohort()
        c["change_sample_eligible"] = False
        result, paired = supported_comparisons(contexts, c)
        self.assertTrue(paired.empty)
        self.assertTrue(result.headline_runs_difference_per_100.isna().all())
        self.assertTrue(result.runs_difference_per_100.isna().all())

    def test_insufficient_change_sample_hides_headline_only(self):
        d, cells = fixture()
        c = cohort()
        c["change_sample_eligible"] = False
        contexts = summarize(role_ledger(d, cells, CONFIG), KEY + CONTEXT + ["pressure_full", "supported"])
        result, _ = supported_comparisons(contexts, c)
        self.assertTrue(result.headline_runs_difference_per_100.isna().all())
        self.assertTrue(result.runs_difference_per_100.eq(250.).all())

    def test_complete_match_resampling_and_zero_denominator(self):
        d, cells = fixture()
        ledger = role_ledger(d, cells, CONFIG)
        p = ledger.loc[ledger.role.eq("batting") & ledger.pressure_full]
        matches = pd.DataFrame(dict(match_id=["a", "b", "c"]))
        draws = np.array([[1, 1, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2]])
        rates, den = rate_draws(p, matches, draws)
        np.testing.assert_allclose(rates["runs"][:3], [300., 400., 200.])
        np.testing.assert_allclose(rates["wickets"][:3], [50., 0., 100.])
        self.assertTrue(np.isnan(rates["runs"][3]))
        self.assertEqual(den[3], 0)

    def test_lost_supported_group_invalidates_draw_instead_of_changing_population(self):
        d, cells = fixture()
        # One ordinary match: bootstrap loses it often, invalidating supported difference.
        d.loc[~d.pressure_full, "match_id"] = "a"
        ledger = role_ledger(d, cells, CONFIG)
        result, _, draws = uncertainty(ledger, cohort(), CONFIG)
        change = result.loc[result.estimand.eq("supported_difference")]
        self.assertTrue(change.finite_fraction.lt(.95).all())
        self.assertTrue(change.p10.isna().all())
        pressure = result.loc[result.estimand.eq("pressure_rate")]
        self.assertTrue(pressure.interval_reliable.all())
        self.assertTrue(draws.sum(axis=1).astype(int).tolist() == [2] * 1000)

    def test_missing_support_and_duplicate_cells_fail_closed(self):
        d, cells = fixture()
        with self.assertRaisesRegex(ValueError, "Missing evidence identity or support"):
            role_ledger(d, cells.iloc[:1], CONFIG)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            role_ledger(d, pd.concat([cells, cells]), CONFIG)


TARGET_COLUMNS = ["bat_runs", "striker_wicket", "bowl_runs", "bowler_wicket"]


class PlayerEvidenceArtifactTests(unittest.TestCase):
    def test_loader_filters_every_mixed_year_outcome_read_before_materialization(self):
        if not (ROOT / "reports/supported_method_2026-11-01/manifest.json").exists():
            self.skipTest("Private source artifacts unavailable")
        original = pd.read_parquet
        reads = []
        def guarded(path, **kwargs):
            self.assertTrue(kwargs.get("filters"), path)
            self.assertIn(path.name, ["identities_and_exposures.parquet", "features.parquet", "targets.parquet", "verified_events.parquet"])
            result = original(path, **kwargs)
            if "year" in result:
                self.assertTrue(result.year.isin([2023, 2024, 2025]).all())
            reads.append(path.name)
            return result
        with patch("rr_pressure.player_evidence.pd.read_parquet", side_effect=guarded):
            data, players, cells, upstream = load_evidence(ROOT, CONFIG, METHOD)
        self.assertEqual(len(reads), 4)
        self.assertEqual(len(data), 95945)
        self.assertEqual(data.match_id.nunique(), 402)
        self.assertFalse(data.year.eq(2026).any())

    def test_output_provenance_counts_shared_bootstrap_and_checkpoint(self):
        out = ROOT / "reports/player_evidence_development_2026-11-01"
        if not (out / "manifest.json").exists():
            self.skipTest("Evidence tables not generated yet")
        manifest = json.loads((out / "manifest.json").read_text())
        for name, digest in manifest["output_sha256"].items():
            self.assertEqual(sha256(out / name), digest, name)
        self.assertEqual(manifest["config_sha256"], sha256(ROOT / "configs/player_evidence_v1.json"))
        self.assertFalse(manifest["models_fitted"] or manifest["reserved_outcomes_read"] or
            manifest["player_composite_scores_created"] or manifest["dossier_cards_created"])
        for name, digest in manifest["preserved_gate_sha256"].items():
            self.assertEqual(sha256(ROOT / name), digest)
        validation = json.loads((out / "validation.json").read_text())
        self.assertTrue(validation["validated_initial_tables"] and validation["decision_checkpoint_reached"])
        for name, value in CONFIG["expected"].items():
            self.assertEqual(validation[name], value)
        matches = pd.read_csv(out / "bootstrap_matches.csv", dtype={"match_id": str})
        draws = np.load(out / "bootstrap_multiplicities.npy", allow_pickle=False)
        self.assertEqual(draws.shape, (1000, 402))
        for _, group in matches.groupby(["family", "year"]):
            self.assertTrue((draws[:, group.index].sum(axis=1) == len(group)).all())


if __name__ == "__main__":
    unittest.main()
