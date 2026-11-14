"""Final access is gated by a committed protocol; metrics and cutoffs stay fixed."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch
import subprocess

import pandas as pd
import numpy as np

from rr_pressure.data import sha256
from rr_pressure.final_window import validate_dates, validate_protocol, load_window, temporal_review


ROOT = Path(__file__).resolve().parents[1]


def exposure_expectations(prefix):
    folder = ROOT / "reports/supported_method_2026-11-01"
    pop = pd.read_csv(folder / "population_windows.csv").set_index("window").loc[prefix]
    result = dict(events=int(pop.verified_events), matches=int(pop.verified_matches))
    for role in ["batting", "bowling"]:
        d = pd.read_csv(folder / f"{prefix}_{role}_players.csv")
        result.update({role + "_opportunities": int(d.retained_events.sum()),
            role + "_pressure_opportunities": int(d.pressure_events.sum()),
            role + "_level_eligible": int(d.level_sample_eligible.sum()),
            role + "_level_coverage_ready": int((d.level_sample_eligible & d.coverage_ready).sum()),
            role + "_blend_coverage_ready": int(d.unqualified_shortlist_evidence_ready.sum())})
    return result


class FinalWindowTests(unittest.TestCase):
    def test_cutoff_is_inclusive_and_warmup_future_or_conflicting_years_fail(self):
        window = dict(first_date="2023-01-01", last_date="2026-11-01")
        ids = pd.DataFrame(dict(match_id=["a", "b"], match_date=["2023-01-01", "2026-11-01"], year=[2023, 2026]))
        validate_dates(ids, window)
        for date, year in [("2026-11-02", 2026), ("2022-12-31", 2022), ("2026-11-01", 2025)]:
            changed = ids.copy()
            changed.loc[1, ["match_date", "year"]] = [date, year]
            with self.assertRaises(ValueError):
                validate_dates(changed, window)

    def test_uncommitted_protocol_prevents_any_parquet_outcome_read(self):
        fake = subprocess.CompletedProcess([], 128, stdout="", stderr="missing")
        with patch("rr_pressure.final_window.subprocess.run", return_value=fake), patch("rr_pressure.final_window.pd.read_parquet") as read:
            with self.assertRaisesRegex(ValueError, "committed unchanged"):
                validate_protocol(ROOT, {})
            read.assert_not_called()

    def test_new_loader_reproduces_development_without_opening_reserved_targets(self):
        source = ROOT / "reports/supported_method_2026-11-01"
        if not (source / "manifest.json").exists():
            self.skipTest("Private source artifacts unavailable")
        window = dict(first_date="2023-01-01", last_date="2025-12-31", reference_date="2025-12-31",
            exposure_prefix="development", expected=exposure_expectations("development"))
        base = json.loads((ROOT / "configs/supported_method_v1.json").read_text())
        original = pd.read_parquet
        reads = []
        def guarded(path, **kwargs):
            self.assertTrue(kwargs.get("filters"))
            result = original(path, **kwargs)
            if "year" in result:
                self.assertTrue(result.year.isin([2023, 2024, 2025]).all())
            reads.append(path.name)
            return result
        with patch("rr_pressure.final_window.pd.read_parquet", side_effect=guarded):
            ledger, cohort = load_window(ROOT, window, base, {}, {})
        self.assertEqual(len(reads), 4)
        self.assertEqual(len(ledger), 188204)
        self.assertEqual(ledger.match_id.nunique(), 402)

    def test_temporal_missing_evidence_is_not_zero_performance(self):
        development = pd.DataFrame([dict(role="batting", player_id="p", variant="default_60_40", selection_ready=True, rank=1., point=.2)])
        reserved = pd.DataFrame(columns=["role", "player_id", "variant", "point", "selection_ready", "finite_fraction"])
        final = development.copy()
        cohort = pd.DataFrame([dict(role="batting", player_id="p", pressure_events=0, pressure_matches=0, retained_fraction=0.)])
        ledger = pd.DataFrame(columns=["role", "player_id", "pressure_full", "event_id", "match_id", "runs", "wickets", "four_or_six_run_event",
            "boundary_flag_disagrees", "zero_runs", "wide_noball_runs", "excluded_dismissal_event", "own_noncredited_dismissal",
            "weight", "weight_squared", "weighted_runs", "weighted_wickets"])
        ledger["pressure_full"] = ledger.pressure_full.astype(bool)
        result = temporal_review(development, reserved, final, cohort, ledger)
        self.assertTrue(result.reserved_point.isna().all())
        self.assertEqual(result.reserved_evidence_status.iloc[0], "no_retained_pressure_evidence")


class FinalArtifactTests(unittest.TestCase):
    def test_final_hashes_cutoff_and_top_tens(self):
        out = ROOT / "reports/final_window_evaluation_2026-11-01"
        if not (out / "manifest.json").exists():
            self.skipTest("Frozen final evaluation has not run")
        manifest = json.loads((out / "manifest.json").read_text())
        for name, digest in manifest["output_sha256"].items():
            self.assertEqual(sha256(out / name), digest, name)
        for name, digest in manifest["frozen_dependencies"].items():
            self.assertEqual(sha256(ROOT / name), digest, name)
        self.assertTrue(manifest["reserved_outcomes_read"])
        self.assertEqual(manifest["predictive_fits"], 0)
        top = pd.read_csv(out / "two_top_ten_lists.csv", dtype={"player_id": str})
        self.assertEqual(top.groupby("role").size().to_dict(), {"batting": 10, "bowling": 10})
        self.assertFalse(top.duplicated(["role", "player_id"]).any())
        for label in ["reserved_2026", "final_2023_2026"]:
            ledger = pd.read_parquet(out / label / "event_role_ledger.parquet")
            self.assertTrue(ledger.match_date.le("2026-11-01").all())
            self.assertFalse(ledger.year.eq(2022).any())
        final = pd.read_parquet(out / "final_2023_2026/ratings.parquet")
        for _, group in final.groupby(["role", "player_id"]):
            self.assertEqual(group.selection_ready.nunique(), 1)
        gate = json.loads((out / "evaluation_gate.json").read_text())
        self.assertFalse(gate["submission_ready"] or gate["dropdown_mapping_verified"])


if __name__ == "__main__":
    unittest.main()
