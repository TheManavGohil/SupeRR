"""Pre-event score-independent state. Unverified scores remain null."""

from __future__ import annotations

from collections import Counter, deque
import re

import pandas as pd

KNOWN = {"None", "wide", "Overstep", "byes", "legbyes"}
ILLEGAL = {"wide", "Overstep"}
BOWLER_WICKETS = {"Caught", "Bowled", "LBW", "Stump", "Hit Wicket"}


def parse_result(result):
    lower = result.lower()
    if any(t in lower for t in ("tied", "super over", "superover", "one over eliminator")):
        return "tie", None
    if "abandon" in lower:
        return "abandoned", None
    if "no result" in lower:
        return "no_result", None
    found = re.search(r"\bwon\s+(?:by\s+)?(\d+)\s*(runs?|wickets?|wkts?)\b", lower)
    return (("runs" if found[2].startswith("run") else "wickets"), int(found[1])) if found else ("unparsed", None)


def match_flags(match):
    kind, margin = parse_result(match["result"])
    rain = bool(re.search(r"\bd\s*/?\s*ls?\b|duckworth", match["result"], re.I)) or any(
        match[k] for k in ("first_inn_revised_overs", "second_inn_revised_overs", "revised_target"))
    return kind, margin, rain


def innings_quality(events, match):
    """Whole-innings exclusions stop uncertain state propagating into accepted rows."""
    if not events:
        return "missing_innings"
    if events[0]["innings"] not in (1, 2):
        return "super_over"
    kind, margin, rain = match_flags(match)
    if rain:
        return "adjusted_or_rain"
    if kind not in ("runs", "wickets", "tie"):
        return kind
    if any(e["extras_type"] not in KNOWN for e in events):
        return "unknown_extra_category"
    if [e["innings_ball_num"] for e in events] != list(range(1, len(events) + 1)):
        return "event_sequence_gap"
    overs = Counter()
    for event in events:
        overs[event["overid"]] += event["extras_type"] not in ILLEGAL
    last = max(overs)
    if not (1 <= last <= 20 and all(overs[o] == 6 for o in range(1, last)) and 0 <= overs[last] <= 6):
        return "over_legality_mismatch"
    wickets = sum(e["is_wicket"] for e in events)
    if wickets > 10:
        return "too_many_wickets"
    if kind == "wickets" and events[0]["innings"] == 2 and wickets != 10 - margin:
        return "wicket_margin_conflict"
    return "accepted_proxy"


def before_events(events, config):
    """All outputs depend only on earlier events and the current known over label."""
    legal_before = wickets_before = 0
    recent = deque()
    window = config["recent_legal_ball_window"]
    for event in events:
        while recent and recent[0][0] < legal_before - window:
            recent.popleft()
        recent_wickets = sum(value for _, value in recent)
        over = event["overid"]
        late = config["late_overs_inclusive"][0] <= over <= config["late_overs_inclusive"][1]
        collapse_recent = recent_wickets >= config["recent_wickets_minimum"]
        collapse_early = over <= config["early_over_maximum_inclusive"] and wickets_before >= config["early_wickets_minimum"]
        collapse = collapse_recent or collapse_early
        yield {"legal_balls_before": legal_before, "balls_remaining": 120 - legal_before,
               "wickets_before": wickets_before, "recent_wickets": recent_wickets,
               "late": late, "collapse_recent": collapse_recent, "collapse_early": collapse_early,
               "collapse": collapse, "pressure_proxy": late or collapse}
        recent.append((legal_before, int(event["is_wicket"])))
        legal_before += event["extras_type"] not in ILLEGAL
        wickets_before += event["is_wicket"]


def build_states(events, matches, config):
    result = events.sort_values(["match_id", "innings", "innings_ball_num"]).reset_index(drop=True).copy()
    lookup = matches.set_index("match_id").to_dict("index")
    records = []
    ledger = []
    for (match_id, innings), group in result.groupby(["match_id", "innings"], sort=False):
        raw = group.to_dict("records")
        match = lookup[match_id]
        quality = innings_quality(raw, match)
        primary = match["family"] in ("IPL", "T20I")
        accepted = quality == "accepted_proxy"
        ledger.append({"match_id": match_id, "innings": innings, "year": match["year"], "family": match["family"],
                       "events": len(group), "quality": quality, "primary_scope": primary,
                       "eligible_proxy": accepted and primary})
        states = before_events(raw, config["rule_pressure"]) if accepted else [None] * len(raw)
        for event, state in zip(raw, states):
            record = {"event_id": event["event_id"], "quality": quality,
                      "primary_scope": primary, "eligible_proxy": accepted and primary}
            record.update(state or {k: None for k in ("legal_balls_before", "balls_remaining", "wickets_before", "recent_wickets",
                                                      "late", "collapse_recent", "collapse_early", "collapse", "pressure_proxy")})
            records.append(record)
    states = pd.DataFrame(records)
    result = result.merge(states, on="event_id", how="left", validate="one_to_one")
    for col in ("legal_balls_before", "balls_remaining", "wickets_before", "recent_wickets"):
        result[col] = result[col].astype("Int16")
    for col in ("late", "collapse_recent", "collapse_early", "collapse", "pressure_proxy"):
        result[col] = result[col].astype("boolean")
    result["legal_delivery"] = result["extras_type"].map({k: k not in ILLEGAL for k in KNOWN}).astype("boolean")
    result["bowler_credited_wicket"] = result["is_wicket"] & result["dismissal_type"].isin(BOWLER_WICKETS)
    result["striker_bowler_dismissal"] = result["bowler_credited_wicket"] & result["dismissed_player_id"].eq(result["striker_id"])
    result["phase"] = result["overid"].map(lambda o: "01–06" if o <= 6 else "07–15" if o <= 15 else "16–20")
    result["boundary_flag"] = result["is_four"] | result["is_six"]
    result["recorded_zero"] = result["recorded_runs"].eq(0)
    result["illegal_delivery"] = result["extras_type"].isin(ILLEGAL)
    result["score_before"] = pd.Series(pd.NA, index=result.index, dtype="Int32")
    result["chase_target"] = pd.Series(pd.NA, index=result.index, dtype="Int32")
    result["required_run_rate"] = pd.Series(pd.NA, index=result.index, dtype="Float64")
    result["tight_chase"] = pd.Series(pd.NA, index=result.index, dtype="boolean")
    result["pressure_full"] = pd.Series(pd.NA, index=result.index, dtype="boolean")
    result["mode_a_ready"] = False
    if result["eligible_proxy"].sum() == 0:
        raise ValueError("No usable primary proxy cohort")
    return result, pd.DataFrame(ledger)
