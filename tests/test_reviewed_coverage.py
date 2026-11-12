"""Synthetic review fixtures and private full-cohort invariants."""

from copy import deepcopy
import unittest
import pandas as pd

from rr_pressure.alignment import align_events
from rr_pressure.reviews import apply_reviews, match_number_review
from rr_pressure.coverage import choose_candidate, nearby_candidates
from test_external_pilot import fixture


class ReviewTests(unittest.TestCase):
    def test_ordinal_exception_is_exact_date_and_source_specific(self):
        match = {"match_id": "fiction", "match_number": "19"}
        review = dict(match_id="fiction", field="match_number", supplied_value="19", external_value="21",
                      source_member_sha256="digest", evidence_urls=["https://example.org/fixture-change"])
        self.assertEqual(match_number_review(match, 21, "digest", [review], 0), review)
        self.assertIsNone(match_number_review(match, 21, "other", [review], 0))
        self.assertIsNone(match_number_review(match, 21, "digest", [review], 1))
        with self.assertRaises(ValueError):
            match_number_review(match, 22, "digest", [review], 0)
    def test_nearby_search_respects_cutoff_and_team_pair(self):
        match = dict(home_team="Alpha", away_team="Beta", family="T20I", match_date="2026-11-01")
        index = pd.DataFrame([dict(family="T20I", teams_key="alpha|beta", date=date, member=f"{i}.json", archive="x")
            for i, date in enumerate(["2026-10-30", "2026-10-31", "2026-11-01", "2026-11-02"])])
        result = nearby_candidates(match, index, 1)
        self.assertEqual(set(result.date), {"2026-10-31", "2026-11-01"})

    def test_exact_date_failure_does_not_override_unique_complete_ledger(self):
        exact = {"accepted": False, "label": "exact_but_wrong_actors"}
        shifted = {"accepted": True, "label": "shifted_and_complete"}
        chosen, ambiguous = choose_candidate([exact, shifted])
        self.assertEqual(chosen, shifted)
        self.assertFalse(ambiguous)
        _, ambiguous = choose_candidate([shifted, dict(shifted)])
        self.assertTrue(ambiguous)

    def test_exact_field_override_preserves_original_and_records_evidence(self):
        raw, _, _, _ = fixture()
        original = deepcopy(raw)
        entry = dict(event_id=raw[0]["event_id"], field="recorded_runs", old_value=1, new_value=2,
                     source_member_sha256="digest", rationale="Individually reviewed source pointer")
        patched, log, _ = apply_reviews(raw, "digest", [entry])
        self.assertEqual(raw, original)
        self.assertEqual(patched[0]["recorded_runs"], 2)
        self.assertEqual(log, [entry])
        with self.assertRaises(ValueError):
            apply_reviews(raw, "changed", [entry])
        entry["old_value"] = 3
        with self.assertRaises(ValueError):
            apply_reviews(raw, "digest", [entry])

    def test_review_cannot_suppress_wicket_or_modify_identity(self):
        raw, _, _, _ = fixture()
        entry = dict(event_id=raw[0]["event_id"], field="retirement", source_member_sha256="digest", rationale="Review")
        with self.assertRaises(ValueError):
            apply_reviews(raw, "digest", [entry])
        entry.update(field="striker_id", old_value=raw[0]["striker_id"], new_value="another")
        with self.assertRaises(ValueError):
            apply_reviews(raw, "digest", [entry])

    def test_only_reviewed_participant_retirement_is_allowed(self):
        raw, public, match, ids = fixture()
        event = raw[10]
        public["innings"][1]["overs"][0]["deliveries"][0]["wickets"] = [
            {"kind": "retired hurt", "player_out": event["striker_id"]}]
        self.assertIn("retirement_requires_review", {i["reason"] for i in align_events(raw, public, ids, match)[1]})
        self.assertFalse(align_events(raw, public, ids, match, {event["event_id"]})[1])
        public["innings"][1]["overs"][0]["deliveries"][0]["wickets"][0]["player_out"] = "not a participant"
        self.assertIn("retirement_requires_review", {i["reason"] for i in align_events(raw, public, ids, match, {event["event_id"]})[1]})

    def test_unlisted_event_is_never_repaired(self):
        raw, _, _, _ = fixture()
        entry = dict(event_id="unrelated", field="recorded_runs", old_value=1, new_value=2,
                     source_member_sha256="digest", rationale="Review")
        patched, log, retired = apply_reviews(raw, "digest", [entry])
        self.assertEqual(patched, raw)
        self.assertFalse(log or retired)
