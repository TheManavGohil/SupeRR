import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "scripts" / "reconcile_and_pressure.py"
SPEC = importlib.util.spec_from_file_location("audit", PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def ball(runs=0, extras="None", innings="2", over=1, wicket=False):
    return {"runs": str(runs), "extras_type": extras, "extras1_runs": "6", "extras_2_runs": "4",
            "innings": innings, "overid": str(over), "is_wicket": str(wicket).lower()}


class AuditTests(unittest.TestCase):
    def test_result_spellings_and_tie_precedence(self):
        for text in ["X Won by 6 Wkts", "X Won 6 wickets", "X won by 6Wickets(D/L Method)"]:
            self.assertEqual(audit.parse_result(text), ("wickets", 6))
        self.assertEqual(audit.parse_result("X Won 36  Runs"), ("runs", 36))
        self.assertEqual(audit.parse_result("X Tied (X Won the Super Over by 2 wickets)"), ("tie", None))
        self.assertEqual(audit.parse_result("X Won the one over Eliminator"), ("tie", None))

    def test_two_hypotheses_do_not_add_category_code_or_secondary_field(self):
        self.assertEqual(audit.event_runs(ball(4), "a"), 4)
        self.assertEqual(audit.event_runs(ball(4), "b"), 4)
        for extra in audit.ONE_EXTRA:
            self.assertEqual(audit.event_runs(ball(0, extra), "b"), 1)
        self.assertEqual(audit.event_runs(ball(0, "other"), "b"), 0)

    def test_chase_early_crossing_and_final_boundary(self):
        self.assertEqual(audit.chase_check([ball(4), ball(1)], 4, "a"), (True, False))
        self.assertEqual(audit.chase_check([ball(1), ball(6)], 5, "a"), (True, True))
        self.assertEqual(audit.chase_check([ball(1)], 5, "a"), (False, False))

    def test_over_count_ignores_wide_and_rejects_unknown(self):
        rows = [ball(over=1) for _ in range(6)] + [ball(extras="wide", over=1), ball(over=2)]
        self.assertTrue(audit.legal_structure(rows)[0])
        self.assertFalse(audit.legal_structure(rows + [ball(extras="other", over=2)])[0])
        self.assertFalse(audit.legal_structure([ball(over=1)] * 7)[0])

    def test_current_outcome_cannot_change_its_pressure(self):
        before = [ball(0, innings="1", wicket=True), ball(0, innings="1", wicket=True)]
        a = list(audit.pressure_events(before + [ball(0, innings="1")], {"a": 100, "b": 100}))
        b = list(audit.pressure_events(before + [ball(6, innings="1", wicket=True)], {"a": 100, "b": 100}))
        self.assertEqual(a[-1], b[-1])
        self.assertTrue(a[-1]["collapse"])

    def test_wide_does_not_advance_tight_chase_window(self):
        # Before 60 legal balls, 61 remain; tight_chase must still be false.
        events = [ball(over=i // 6 + 1) for i in range(59)] + [ball(extras="wide", over=10), ball(over=10), ball(over=11)]
        flags = list(audit.pressure_events(events, {"a": 60, "b": 60}))
        self.assertFalse(flags[60]["tight_a"])
        self.assertTrue(flags[61]["tight_a"])

    def test_collapse_window_expires_and_early_clause_not_latched(self):
        events = [ball(innings="1", wicket=True), ball(innings="1", wicket=True)]
        events += [ball(innings="1") for _ in range(13)]
        flags = list(audit.pressure_events(events, {"a": None, "b": None}))
        self.assertTrue(flags[2]["collapse"])
        self.assertFalse(flags[-1]["collapse"])
        events = [ball(innings="1", wicket=True) for _ in range(4)] + [ball(innings="1") for _ in range(14)] + [ball(innings="1", over=11)]
        flags = list(audit.pressure_events(events, {"a": None, "b": None}))
        self.assertTrue(flags[-2]["collapse"])
        self.assertFalse(flags[-1]["collapse"])

    def test_adjusted_match_detection(self):
        base = {"result": "X Won by 2 runs", "first_inn_revised_overs": "", "second_inn_revised_overs": "", "revised_target": ""}
        self.assertFalse(audit.rain_flag(base))
        self.assertTrue(audit.rain_flag(base | {"result": "X Won by 2 runs (DLS Method)"}))
        self.assertTrue(audit.rain_flag(base | {"revised_target": "100"}))

    def test_unknown_target_has_bounds_without_invented_chase(self):
        events = [ball(over=i // 6 + 1) for i in range(61)]
        flags = list(audit.pressure_events(events, {"a": None, "b": None}))[-1]
        self.assertFalse(flags["tight_a"])
        self.assertFalse(flags["lower"])
        self.assertTrue(flags["upper"])

    def test_missing_same_extras_in_both_innings_can_hide_bad_totals(self):
        # An exact margin is insufficient evidence to accept either reconstructed total.
        supplied_first, supplied_second = [ball(6)], [ball(1)]
        raw_difference = sum(audit.event_runs(e, "a") for e in supplied_first) - sum(audit.event_runs(e, "a") for e in supplied_second)
        independently_correct_first, independently_correct_second = 10, 5
        self.assertEqual(raw_difference, independently_correct_first - independently_correct_second)
        self.assertNotEqual(sum(audit.event_runs(e, "a") for e in supplied_first), independently_correct_first)


if __name__ == "__main__":
    unittest.main()
