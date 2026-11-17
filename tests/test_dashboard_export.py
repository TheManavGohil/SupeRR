"""Publication boundary checks against independent frozen analysis artifacts."""
import json
from pathlib import Path
import unittest
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
class DashboardExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.players=json.loads((ROOT/'dashboard/content/generated/players.json').read_text())
        cls.final=ROOT/'reports/final_window_evaluation_2026-11-01'

    def test_all_top_twenty_ids_ranks_and_quantities_match_original(self):
        top=pd.read_csv(self.final/'two_top_ten_lists.csv',dtype={'player_id':str})
        for row in top.itertuples():
            p=next(p for p in self.players if p['role']==row.role and p['id']==row.player_id)
            self.assertTrue(p['selected']);self.assertEqual(p['rank'],int(row.rank));self.assertEqual(p['name'],row.player_name)
            np.testing.assert_allclose([p['rating']['low'],p['rating']['point'],p['rating']['high']],[row.selection_score,row.point,row.p90],atol=1e-10,rtol=0)

    def test_publication_is_the_existing_selected_alternative_union(self):
        a=pd.read_csv(self.final/'final_2023_2026/player_dossiers/alternatives.csv',dtype={'alternative_id':str})
        t=pd.read_csv(self.final/'two_top_ten_lists.csv',dtype={'player_id':str})
        expected=set(zip(t.role,t.player_id))|set(zip(a.role,a.alternative_id))
        self.assertEqual(set((p['role'],p['id']) for p in self.players),expected)
        self.assertEqual(len(expected),69)

    def test_selected_recent_status_reproduces_reserved_gate(self):
        r=pd.read_parquet(self.final/'reserved_2026/ratings.parquet')
        ready=set(zip(r.loc[r.variant.eq('default_60_40')&r.selection_ready].role,r.loc[r.variant.eq('default_60_40')&r.selection_ready].player_id))
        for p in self.players:
            self.assertEqual(p['recent']['status']=='adequate',(p['role'],p['id'])in ready)

if __name__=='__main__':unittest.main()
