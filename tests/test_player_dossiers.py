"""Fixed examples and dossier traceability must not change selection ordering."""

import json
from pathlib import Path
import unittest

import pandas as pd

from rr_pressure.data import sha256
from rr_pressure.player_dossiers import choose_cases, alternatives


ROOT = Path(__file__).resolve().parents[1]


class DossierProtocolTests(unittest.TestCase):
    def test_extremes_show_both_metrics_and_deduplicate_cases(self):
        matches = pd.DataFrame(dict(match_id=["a", "b", "c", "d", "e", "f"],
            match_date=["2025-01-01"] * 6, opportunities=[10, 20, 10, 10, 10, 1],
            runs_per_100=[100, 200, 300, 150, 180, 999], wickets_per_100=[0, 5, 10, 0, 3, 100]))
        result = choose_cases(matches, 10)
        self.assertLessEqual(len(result), 5)
        self.assertFalse(result.match_id.eq("f").any())
        maximum = result.loc[result.match_id.eq("c")].iloc[0]
        self.assertIn("maximum_run_rate", maximum.case_reasons)
        self.assertIn("maximum_wicket_rate", maximum.case_reasons)
        self.assertFalse(result.small_sample.any())
        self.assertIn("typical_run_rate", ";".join(result.case_reasons))

    def test_ties_use_exposure_then_date_then_id(self):
        matches = pd.DataFrame(dict(match_id=["b", "a", "c"], match_date=["2025-01-01"] * 3,
            opportunities=[20, 20, 10], runs_per_100=[100, 100, 100], wickets_per_100=[0, 0, 0]))
        result = choose_cases(matches, 10)
        self.assertEqual(result.match_id.tolist(), ["a"])

    def test_all_small_samples_use_explicit_highest_exposure_fallback(self):
        matches = pd.DataFrame(dict(match_id=["a", "b"], match_date=["2025-01-01"] * 2,
            opportunities=[1, 2], runs_per_100=[600, 0], wickets_per_100=[0, 50]))
        result = choose_cases(matches, 10)
        self.assertEqual(result.match_id.tolist(), ["b"])
        self.assertTrue(result.small_sample.all())
        self.assertEqual(result.case_reasons.iloc[0], "highest_exposure_small_sample")

    def test_alternatives_include_boundary_and_similar_roles_without_reordering(self):
        default = pd.DataFrame([dict(role="batting", player_id=str(i), rank=i, selection_ready=True) for i in range(1, 16)])
        profiles = pd.DataFrame([dict(role="batting", player_id=str(i), phase=p, pressure_full=True,
            opportunities=100 if (p == "16-20") == (i == 1 or i == 15) else 1)
            for i in range(1, 16) for p in ["01-06", "07-15", "16-20"]])
        original = default.copy(deep=True)
        alt = alternatives(default, profiles)
        first = alt.loc[alt.player_id.eq("1")]
        self.assertTrue({"11", "12", "13", "15"}.issubset(set(first.alternative_id)))
        self.assertTrue(first.loc[first.alternative_id.eq("15"), "role_similar_alternative"].iloc[0])
        pd.testing.assert_frame_equal(default, original)


class DossierArtifactTests(unittest.TestCase):
    def test_complete_population_case_counts_and_source_traceability(self):
        out = ROOT / "reports/player_dossiers_development_2026-11-01"
        if not (out / "manifest.json").exists():
            self.skipTest("Private development dossiers not generated")
        manifest = json.loads((out / "manifest.json").read_text())
        for name, digest in manifest["output_sha256"].items():
            self.assertEqual(sha256(out / name), digest, name)
        index = pd.read_csv(out / "index.csv", dtype={"player_id": str})
        self.assertEqual(len(index), 195)
        self.assertEqual(index.groupby("role").size().to_dict(), {"batting": 73, "bowling": 122})
        cases = pd.read_csv(out / "case_index.csv", dtype={"player_id": str, "match_id": str})
        self.assertTrue(cases.groupby(["role", "player_id"]).size().le(5).all())
        self.assertFalse(cases.duplicated(["role", "player_id", "match_id"]).any())
        events = pd.read_csv(out / "case_events.csv", dtype={"player_id": str, "match_id": str})
        self.assertFalse(events.source_pointer.isna().any())
        counts = events.groupby(["role", "player_id", "match_id"]).size().rename("events").reset_index()
        checked = cases.merge(counts, on=["role", "player_id", "match_id"], validate="one_to_one")
        self.assertTrue(checked.opportunities.eq(checked.events).all())
        for row in index.itertuples():
            content = (out / row.dossier).read_text()
            for section in ["Observed task", "Repeatability", "Usual-performance", "counterexamples", "alternatives"]:
                self.assertIn(section, content)


if __name__ == "__main__":
    unittest.main()
