"""Peer support must exclude complete matches without consuming outcomes."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from rr_pressure.data import sha256
from rr_pressure.reference_audit import (CONTEXT, INPUTS, audit_exposures,
    load_exposures, match_partitions, peer_counts)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/retrospective_reference_v1.json").read_text())


def exposures():
    rows = []
    for year in [2023, 2024, 2025]:
        for family in ["IPL", "T20I"]:
            for match in range(4):
                match_id = f"{year}:{family}:{match}"
                for innings in [1, 2]:
                    for ball in range(2):
                        rows.append(dict(event_id=f"{match_id}:{innings}:{ball}", match_id=match_id,
                            match_date=f"{year}-05-01", year=year, family=family, innings=innings,
                            phase="01-06", wicket_band="0-2", pressure_full=ball == 1,
                            batting_opportunity=ball == 0))
    return pd.DataFrame(rows)[INPUTS]


class ReferenceAuditTests(unittest.TestCase):
    def test_partitions_balanced_and_independent_of_row_order(self):
        d = exposures()
        first = match_partitions(d, CONFIG)
        second = match_partitions(d.sample(frac=1, random_state=15), CONFIG)
        pd.testing.assert_frame_equal(first, second)
        self.assertFalse(first.match_id.duplicated().any())
        self.assertTrue(first.groupby(["year", "family", "evaluation_fold"]).size().eq(2).all())

    def test_counts_exclude_both_innings_at_parent_and_child(self):
        d = exposures()
        partitions = match_partitions(d, CONFIG)
        d = d.merge(partitions[["match_id", "evaluation_fold"]], on="match_id")
        for scheme, child_n, parent_n, n_matches in [
                ("leave_match_out", 6, 12, 3), ("two_fold", 4, 8, 2)]:
            child = peer_counts(d, CONTEXT, scheme)
            parent = peer_counts(d, ["year", "family"], scheme)
            self.assertTrue(child.peer_events.eq(child_n).all())
            self.assertTrue(parent.peer_events.eq(parent_n).all())
            self.assertTrue(child.peer_matches.eq(n_matches).all())
            self.assertTrue(parent.peer_matches.eq(n_matches).all())

    def test_evaluated_partition_exposure_does_not_enter_its_reference(self):
        d = exposures()
        d = d.merge(match_partitions(d, CONFIG)[["match_id", "evaluation_fold"]], on="match_id")
        before = peer_counts(d, CONTEXT, "two_fold")
        extra = d.loc[d.evaluation_fold.eq(0)].copy()
        extra.event_id += ":extra"
        after = peer_counts(pd.concat([d, extra], ignore_index=True), CONTEXT, "two_fold")
        pd.testing.assert_frame_equal(before.loc[d.evaluation_fold.eq(0)],
                                      after.iloc[:len(d)].loc[d.evaluation_fold.eq(0)])
        self.assertTrue(after.iloc[:len(d)].loc[d.evaluation_fold.eq(1), "peer_events"].eq(8).all())

    def test_nonwide_batting_and_all_attempt_bowling_denominators(self):
        d = exposures()
        _, table = audit_exposures(d, CONFIG)
        rows = table.loc[table.scheme.eq("two_fold") & table.exposure.eq("all")]
        self.assertEqual(rows.loc[rows.role.eq("batting"), "events"].sum(), int(d.batting_opportunity.sum()))
        self.assertEqual(rows.loc[rows.role.eq("bowling"), "events"].sum(), len(d))
        self.assertTrue(rows.loc[rows.role.eq("batting"), "median_peer_events"].eq(2).all())
        self.assertTrue(rows.loc[rows.role.eq("bowling"), "median_peer_events"].eq(4).all())

    def test_absent_opposite_fold_cell_reports_zero(self):
        d = exposures()
        d = d.merge(match_partitions(d, CONFIG)[["match_id", "evaluation_fold"]], on="match_id")
        d.loc[d.evaluation_fold.eq(0), "wicket_band"] = "6-9"
        self.assertTrue(peer_counts(d, CONTEXT, "two_fold").peer_events.eq(0).all())
        self.assertTrue(peer_counts(d, CONTEXT, "two_fold").peer_matches.eq(0).all())

    def test_rejects_targets_reserved_year_and_conflicting_match_metadata(self):
        d = exposures()
        with self.assertRaisesRegex(ValueError, "allowlist"):
            match_partitions(d.assign(bat_runs=0), CONFIG)
        reserved = d.copy()
        reserved["year"] = 2026
        with self.assertRaisesRegex(ValueError, "Development exposures only"):
            match_partitions(reserved, CONFIG)
        d.loc[0, "match_date"] = "2023-05-02"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            match_partitions(d, CONFIG)

    def test_loader_reads_only_development_exposure_columns(self):
        if not (ROOT / "reports/supported_method_2026-11-01/manifest.json").exists():
            self.skipTest("Private inputs unavailable")
        original = pd.read_parquet
        reads = []

        def guarded(path, **kwargs):
            self.assertIn(path.name, ["features.parquet", "identities_and_exposures.parquet"])
            self.assertNotIn("striker_id", kwargs["columns"])
            self.assertNotIn("bowler_id", kwargs["columns"])
            self.assertTrue(kwargs["filters"])
            reads.append(path.name)
            return original(path, **kwargs)

        with patch("rr_pressure.reference_audit.pd.read_parquet", side_effect=guarded):
            d = load_exposures(ROOT, CONFIG)
        self.assertEqual(len(reads), 2)
        self.assertEqual(set(d.year), {2023, 2024, 2025})
        self.assertEqual(set(d.columns), set(INPUTS))

    def test_artifact_claims_match_provenance_and_remain_exposure_only(self):
        out = ROOT / "reports/reference_audit_2026-11-01"
        if not (out / "manifest.json").exists():
            self.skipTest("Private audit unavailable")
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertFalse(manifest["models_fitted"] or manifest["player_scores_created"])
        self.assertEqual(manifest["outcome_files_opened"], [])
        self.assertEqual(manifest["config_sha256"], sha256(ROOT / "configs/retrospective_reference_v1.json"))
        for name, digest in manifest["output_sha256"].items():
            self.assertEqual(digest, sha256(out / name), name)
        partitions = pd.read_csv(out / "match_partitions.csv")
        self.assertEqual(set(partitions.year), {2023, 2024, 2025})
        self.assertFalse(partitions.match_id.duplicated().any())


if __name__ == "__main__":
    unittest.main()
