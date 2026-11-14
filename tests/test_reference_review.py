"""Saved-reference diagnostics must preserve the failed gate and role counts."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from rr_pressure.baseline import TARGETS
from rr_pressure.data import sha256
from rr_pressure.reference_review import (CELL, GROUP, attach_reference_components, bootstrap_means,
    context_diagnostics, distribution_distance, exposure_flags, exposure_tables, load_review, match_influence)


ROOT = Path(__file__).resolve().parents[1]


class ReviewDiagnosticTests(unittest.TestCase):
    def test_fixed_prediction_match_deletion_matches_hand_calculation(self):
        g=pd.DataFrame(dict(match_id=["a","a","b","b","c","c"], residual=[1.,1.,2.,2.,3.,3.]))
        r=match_influence(g,1.)
        self.assertAlmostEqual(r["deleted_match_min_bias"],1.5)
        self.assertAlmostEqual(r["deleted_match_max_bias"],2.5)
        self.assertAlmostEqual(r["largest_match_exposure_fraction"],1/3)
        self.assertAlmostEqual(r["largest_match_absolute_residual_share"],.5)
        self.assertTrue(r["all_match_deletions_above_tolerance"])
        g.residual=[8.,8.,0.,0.,0.,0.]
        self.assertFalse(match_influence(g,1.)["all_match_deletions_above_tolerance"])

    def test_single_match_group_cannot_claim_deletion_robustness(self):
        result=match_influence(pd.DataFrame(dict(match_id=["a","a"],residual=[1.,1.])),.1)
        self.assertFalse(result["all_match_deletions_keep_sign"])
        self.assertTrue(np.isnan(result["deleted_match_min_bias"]))

    def test_total_variation_is_opportunity_weighted(self):
        g=pd.DataFrame(dict(evaluation_fold=[0,0,0,0,1,1],country=["A","A","A","B","A","B"]))
        self.assertAlmostEqual(distribution_distance(g,"country"),.25)
        g.loc[g.evaluation_fold.eq(1),"country"]="C"
        self.assertEqual(distribution_distance(g,"country"),1.)

    def test_bootstrap_means_move_whole_match_opportunities_together(self):
        g=pd.DataFrame(dict(match_id=["a","a","b"],outcome=[0.,2.,4.]))
        matches=pd.DataFrame(dict(match_id=["a","b","c"]))
        weights=np.array([[1,1,0],[2,0,0],[0,2,0],[0,0,2]])
        result=bootstrap_means(g,matches,weights)
        np.testing.assert_allclose(result[:3],[2.,1.,4.])
        self.assertTrue(np.isnan(result[3]))

    def test_role_union_counts_overlapping_run_and_wicket_alert_once(self):
        rows=[]
        for fold in [0,1]:
            for target in TARGETS:
                rows.append(dict(event_id=f"e{fold}",match_id=f"m{fold}",match_date="2023-05-01",year=2023,
                    family="IPL",innings=2,phase="16-20",evaluation_fold=fold,role=TARGETS[target][0],
                    pressure_full=True,target=target,material_alert=fold==0))
        p=pd.DataFrame(rows)
        flags=p[GROUP+["material_alert"]]
        events=exposure_flags(p.drop(columns="material_alert"),flags)
        self.assertEqual(len(events),4)
        self.assertEqual(events.own_fold_alert.sum(),2)
        self.assertEqual(events.either_fold_alert.sum(),4)
        identities=pd.DataFrame(dict(event_id=["e0","e1"],striker_id=["bat","bat"],bowler_id=["bowl","bowl"]))
        eligibility={role:pd.DataFrame(dict(player_id=[player],level_sample_eligible=[True],coverage_ready=[True],
            unqualified_shortlist_evidence_ready=[False])) for role,player in [("batting","bat"),("bowling","bowl")]}
        summary,players,cohorts=exposure_tables(events,identities,eligibility)
        self.assertTrue(players.pressure_events.eq(2).all())
        self.assertTrue(players.own_fold_alert_fraction.eq(.5).all())
        self.assertTrue(players.either_fold_alert_fraction.eq(1.).all())
        self.assertTrue(summary.either_fold_alert_fraction.eq(1.).all())
        self.assertFalse(any("residual" in x or "score" in x for x in players.columns))

    def test_missing_identity_cannot_silently_reduce_player_exposure(self):
        events=pd.DataFrame(dict(event_id=["e"],role=["batting"],pressure_full=[True],own_fold_alert=[True],
            either_fold_alert=[True],family=["IPL"],phase=["16-20"],year=[2023]))
        identities=pd.DataFrame(dict(event_id=["different"],striker_id=["p"],bowler_id=["b"]))
        with self.assertRaisesRegex(ValueError,"Missing pressure-exposure identity"):
            exposure_tables(events,identities,{})


class ReviewArtifactTests(unittest.TestCase):
    def test_loader_reads_saved_predictions_and_development_identity_columns_only(self):
        if not (ROOT/"reports/retrospective_reference_development_2026-11-01/manifest.json").exists():
            self.skipTest("Private development artifacts unavailable")
        original=pd.read_parquet
        reads=[]
        def guarded(path,**kwargs):
            self.assertIn(path.name,["development_predictions.parquet","identities_and_exposures.parquet"])
            if path.name=="identities_and_exposures.parquet":
                self.assertEqual(kwargs["columns"],["event_id","striker_id","bowler_id"])
                self.assertTrue(kwargs["filters"])
            result=original(path,**kwargs)
            if "year" in result:
                self.assertTrue(result.year.isin([2023,2024,2025]).all())
            reads.append(path.name)
            return result
        with patch("rr_pressure.reference_review.pd.read_parquet",side_effect=guarded):
            p,calibration,models,identities,eligibility,validation,m=load_review(ROOT)
        self.assertEqual(len(reads),2)
        self.assertEqual(p.match_id.nunique(),402)
        self.assertEqual(m["cumulative_model_bundles"],20)
        enriched=attach_reference_components(p,models)
        np.testing.assert_allclose(enriched.within_cell_partition_gap+enriched.registered_shrinkage_component,
                                   enriched.residual,atol=1e-12,rtol=0)
        diagnostics=context_diagnostics(enriched,calibration,validation)
        self.assertEqual(int(diagnostics.material_alert.sum()),68)

    def test_review_provenance_exposure_denominators_and_failed_gate_preserved(self):
        out=ROOT/"reports/reference_instability_review_2026-11-01"
        if not (out/"manifest.json").exists():
            self.skipTest("Private review artifacts unavailable")
        manifest=json.loads((out/"manifest.json").read_text())
        self.assertFalse(manifest["models_fitted"] or manifest["player_performance_scores_created"] or manifest["reserved_outcomes_read"])
        for name,digest in manifest["output_sha256"].items():
            self.assertEqual(digest,sha256(out/name),name)
        summary=json.loads((out/"review_summary.json").read_text())
        self.assertEqual(summary["saved_fold_alerts"],68)
        self.assertEqual(summary["new_model_bundles_used"],0)
        self.assertEqual(summary["cumulative_model_bundles"],20)
        self.assertFalse(summary["promotion_gate_changed"] or summary["reference_promoted"])
        exposure=pd.read_csv(out/"pressure_exposure.csv")
        pressure=exposure.loc[exposure.resolution.eq("overall") & exposure.exposure.eq("pressure")].set_index("role")
        self.assertEqual(pressure.loc["batting","events"],32329)
        self.assertEqual(pressure.loc["bowling","events"],33920)
        self.assertTrue(exposure.own_fold_alert_events.le(exposure.either_fold_alert_events).all())
        self.assertTrue(exposure.either_fold_alert_events.le(exposure.events).all())
        gate=json.loads((ROOT/"reports/retrospective_reference_development_2026-11-01/model_gate.json").read_text())
        self.assertFalse(gate["ready_for_reserved_evaluation"])


if __name__=="__main__":
    unittest.main()
