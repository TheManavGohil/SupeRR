"""Synthetic review fixtures and private full-cohort invariants."""

from copy import deepcopy
import unittest

from rr_pressure.alignment import align_events
from rr_pressure.reviews import apply_reviews
from test_external_pilot import fixture


class ReviewTests(unittest.TestCase):
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
