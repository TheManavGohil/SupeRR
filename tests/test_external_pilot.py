"""Synthetic fixtures only: no competition data is published with tests."""

import unittest
from copy import deepcopy
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from rr_pressure.external import select_pilot, team_key
from rr_pressure.data import fingerprints, sha256
from rr_pressure.alignment import align_events, candidates_for, flatten, player_crosswalk, score_checks, verified_states


def fixture():
    # Fictional six-ball overs: a complete 10-wicket first innings, then a short chase.
    def delivery(batter, partner, bowler, runs, out=False):
        d = {"batter": batter, "non_striker": partner, "bowler": bowler,
             "runs": {"batter": runs, "extras": 0, "total": runs}}
        if out:
            d["wickets"] = [{"kind": "bowled", "player_out": batter}]
        return d
    first = [delivery(f"A{i} Example", "Z Partner", "B Bowler", 1, True) for i in range(10)]
    second = [delivery("B Bowler", "Y Partner", "Z Partner", 4) for _ in range(3)]
    people = {n: f"person-{i}" for i, n in enumerate([*(f"A{i} Example" for i in range(10)), "Z Partner", "B Bowler", "Y Partner"])}
    public = {"info": {"overs": 20, "balls_per_over": 6, "players": {"Alpha": [*people][:11], "Beta": ["B Bowler", "Y Partner"]},
        "registry": {"people": people}, "outcome": {"winner": "Beta", "by": {"wickets": 10}}},
        "innings": [{"team": "Alpha", "overs": [{"over": 0, "deliveries": first[:6]}, {"over": 1, "deliveries": first[6:]}]},
                    {"team": "Beta", "overs": [{"over": 0, "deliveries": second}]}]}
    match = dict(match_id="fiction", home_team_id="a", away_team_id="b", home_team="Alpha", away_team="Beta",
        win_team_id="b", result="Beta won by 10 wickets", first_inn_revised_overs="", second_inn_revised_overs="", revised_target="",
        family="T20I", match_date="2025-01-01")
    raw = []
    for i, d in enumerate(flatten(public)):
        raw.append({"event_id": f"fiction:{d['innings']}:{d['innings_ball_num']}", "match_id": "fiction", "source_row": i+2,
            **{k: d[k] for k in ("innings", "overid", "over_ball_num", "innings_ball_num")},
            "batting_team_id": "a" if d["innings"] == 1 else "b", "bowling_team_id": "b" if d["innings"] == 1 else "a",
            **{f"{a}_{suffix}": d[b] for a, b in (("striker", "batter"), ("non_striker", "non_striker"), ("bowler", "bowler")) for suffix in ("id", "name")},
            "recorded_runs": d["runs"]["batter"], "extras_type": "None", "extras_2_runs": "0",
            "is_wicket": bool(d.get("wickets")), "dismissed_player_id": d["batter"] if d.get("wickets") else "",
            "dismissal_type": "Bowled" if d.get("wickets") else ""})
    return raw, public, match, {n: n for n in people}


class AlignmentTests(unittest.TestCase):
    def test_complete_match_accepts_and_preserves_source(self):
        raw, public, match, ids = fixture()
        before = deepcopy(raw)
        c, errors = align_events(raw, public, ids, match)
        self.assertFalse(errors)
        self.assertTrue(score_checks(public, match)["score_pass"])
        self.assertEqual(raw, before)
        self.assertEqual(len(c), len(raw))

    def test_missing_shifted_actor_or_batter_run_event_rejected(self):
        raw, public, match, ids = fixture()
        for change, expected in (("missing", "event_count_mismatch"), ("actor", "striker"), ("runs", "batter_runs"), ("order", "over_ball_num")):
            r = deepcopy(raw)
            if change == "missing": r.pop(0)
            if change == "actor": r[0]["striker_id"] = "unknown"
            if change == "runs": r[0]["recorded_runs"] = 2
            if change == "order": r[0]["over_ball_num"] = 2
            _, issues = align_events(r, public, ids, match)
            self.assertIn(expected, {i["reason"] for i in issues})

    def test_multi_run_extras_are_preserved_and_category_conflict_rejected(self):
        raw, public, match, ids = fixture()
        d = public["innings"][1]["overs"][0]["deliveries"][0]
        d.update(extras={"wides": 5}, runs={"batter": 0, "extras": 5, "total": 5})
        raw[10].update(recorded_runs=0, extras_type="wide")
        corrections, issues = align_events(raw, public, ids, match)
        self.assertFalse(issues)
        self.assertEqual(corrections[10]["team_runs"], 5)
        self.assertFalse(corrections[10]["legal_delivery_verified"])
        raw[10]["extras_type"] = "byes"
        self.assertIn("extra_category", {i["reason"] for i in align_events(raw, public, ids, match)[1]})

    def test_non_striker_runout_is_checked(self):
        raw, public, match, ids = fixture()
        public["innings"][0]["overs"][0]["deliveries"][0]["wickets"] = [{"kind": "run out", "player_out": "Z Partner"}]
        raw[0].update(dismissal_type="RunOut", dismissed_player_id="Z Partner")
        self.assertFalse(align_events(raw, public, ids, match)[1])
        raw[0]["dismissed_player_id"] = raw[0]["striker_id"]
        self.assertIn("dismissed_player", {i["reason"] for i in align_events(raw, public, ids, match)[1]})

    def test_early_chase_crossing_and_result_conflict_rejected(self):
        _, public, match, _ = fixture()
        public["innings"][1]["overs"][0]["deliveries"][0]["runs"].update(batter=12, total=12)
        self.assertIn("wicket_chase_terminal", score_checks(public, match)["score_reason"])
        match["result"] = "Beta won by 9 wickets"
        self.assertIn("supplied_external_result_conflict", score_checks(public, match)["score_reason"])

    def test_adjustments_superovers_and_incomplete_innings_are_not_promoted(self):
        _, public, match, _ = fixture()
        public["info"]["outcome"]["method"] = "D/L"
        self.assertFalse(score_checks(public, match)["score_pass"])
        del public["info"]["outcome"]["method"]
        public["innings"][0]["overs"][1]["deliveries"].pop()
        self.assertIn("incomplete_first_innings", score_checks(public, match)["score_reason"])
        public["innings"][0]["super_over"] = True
        self.assertIn("superover", score_checks(public, match)["score_reason"])

    def test_aliases_resolve_exactly_but_ambiguity_never_guessed(self):
        raw, public, match, _ = fixture()
        public["info"]["players"]["Alpha"].append("AX Example")
        public["info"]["registry"]["people"]["AX Example"] = "another"
        raw[0]["striker_name"] = "Alex Example"
        ids, _ = player_crosswalk(raw, public, match)
        self.assertNotIn(raw[0]["striker_id"], ids)
        aliases = {public["info"]["registry"]["people"]["A0 Example"]: {"alex example"}}
        ids, _ = player_crosswalk(raw, public, match, aliases)
        self.assertEqual(ids[raw[0]["striker_id"]], "A0 Example")

    def test_duplicate_match_candidates_remain_ambiguous(self):
        _, _, match, _ = fixture()
        index = pd.DataFrame([dict(family="T20I", date="2025-01-01", teams_key="alpha|beta", archive="x", member=m) for m in ("1.json", "2.json")])
        self.assertEqual(len(candidates_for(match, index)), 2)

    def test_current_outcome_cannot_change_its_score_or_pressure(self):
        raw, public, match, ids = fixture()
        config = json.loads((Path(__file__).resolve().parents[1] / "configs/analysis_preregistration.json").read_text())
        corrections, _ = align_events(raw, public, ids, match)
        original = verified_states(raw, corrections, config)
        corrections[-1]["team_runs"] += 5
        changed = verified_states(raw, corrections, config)
        self.assertEqual(original[-1], changed[-1])
        self.assertEqual(original[10]["score_before"], 0)
        self.assertEqual(original[10]["chase_target"], 11)

    def test_corrupt_external_extra_arithmetic_is_rejected(self):
        raw, public, match, ids = fixture()
        public["innings"][1]["overs"][0]["deliveries"][0]["runs"]["extras"] = 3
        self.assertIn("external_run_arithmetic", {i["reason"] for i in align_events(raw, public, ids, match)[1]})


class PilotArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.out = cls.root / "reports/reconciliation_pilot_2026-11-01"
        if not (cls.out / "manifest.json").exists():
            raise unittest.SkipTest("Private pilot artifacts unavailable")

    def test_raw_inputs_unchanged_and_only_complete_accepted_matches_emitted(self):
        manifest = json.loads((self.out / "manifest.json").read_text())
        self.assertEqual(manifest["source_sha256"], fingerprints(self.root / "6af3166e7b922_data_pack"))
        matches = pd.read_csv(self.out / "matches.csv", dtype={"match_id": str})
        corrections = pd.read_parquet(self.out / "verified_corrections.parquet")
        self.assertEqual(set(corrections.match_id), set(matches.loc[matches.accepted, "match_id"]))
        counts = corrections.groupby("match_id").size()
        for match in matches.loc[matches.accepted].itertuples():
            self.assertEqual(counts[match.match_id], match.supplied_events)
            self.assertTrue(match.alignment_pass and match.score_pass)
        self.assertTrue(corrections.event_alignment_pass.all())
        self.assertFalse(corrections.event_id.duplicated().any())

    def test_every_verified_quantity_has_matching_external_pointer(self):
        corrections = pd.read_parquet(self.out / "verified_corrections.parquet")
        cache = {}
        for row in corrections.itertuples():
            key = (row.source_archive, row.source_member)
            if key not in cache:
                import hashlib
                with ZipFile(self.root / "data/external/cricsheet" / row.source_archive) as z:
                    payload = z.read(row.source_member)
                self.assertEqual(hashlib.sha256(payload).hexdigest(), row.source_sha256)
                cache[key] = json.loads(payload)
            value = cache[key]
            for token in row.source_pointer.strip("/").split("/"):
                value = value[int(token)] if isinstance(value, list) else value[token]
            self.assertEqual(value["runs"]["total"], row.team_runs)
            self.assertEqual(value["runs"]["batter"], row.recorded_runs)
            self.assertEqual(value["runs"]["extras"], row.extras_runs)

    def test_preball_scores_are_shifted_and_output_hashes_match(self):
        corrections = pd.read_parquet(self.out / "verified_corrections.parquet")
        states = pd.read_parquet(self.out / "verified_preball_states.parquet")
        joined = states.merge(corrections, on=["event_id", "match_id", "innings"], validate="one_to_one")
        for _, group in joined.groupby(["match_id", "innings"], sort=False):
            expected = group.team_runs.cumsum() - group.team_runs
            self.assertEqual(group.score_before.tolist(), expected.tolist())
            self.assertTrue((group.balls_remaining > 0).all())
            self.assertTrue((group.wickets_before < 10).all())
        manifest = json.loads((self.out / "manifest.json").read_text())
        for path, digest in manifest["output_sha256"].items():
            self.assertEqual(sha256(self.out / path), digest, path)


class SelectionTests(unittest.TestCase):
    def test_stratification_string_booleans_and_no_replacement(self):
        rows = []
        for year in range(2022, 2027):
            for family in ("IPL", "T20I"):
                for day in range(1, 5):
                    rows.append(dict(match_id=f"{year}-{family}-{day}", date=f"{year}-01-0{day}",
                        year=year, family=family, two_innings_present="True", cohort="ordinary",
                        kind="runs", run_margin_pass_a="True" if day == 1 else "False",
                        run_margin_pass_b="False", chase_combined_a="", chase_combined_b="",
                        wicket_margin_pass="", innings1_unknown_extra_events=int(day == 4),
                        innings2_unknown_extra_events=0, innings1_unit_extra_events=day,
                        innings2_unit_extra_events=0))
        frame = pd.DataFrame(rows)
        chosen = select_pilot(frame)
        self.assertEqual(len(chosen), 20)
        self.assertEqual(chosen.groupby(["year", "family"]).size().tolist(), [2] * 10)
        self.assertTrue(chosen.match_id.str.endswith(("-2", "-4")).all())
        pd.testing.assert_frame_equal(chosen, select_pilot(frame.sample(frac=1, random_state=6)))

    def test_team_rename_is_explicit(self):
        self.assertEqual(team_key("Royal Challengers Bangalore"), team_key("Royal Challengers Bengaluru"))
        self.assertNotEqual(team_key("India"), team_key("India A"))


if __name__ == "__main__":
    unittest.main()
