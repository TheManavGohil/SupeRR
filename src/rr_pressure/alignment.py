"""Conservative event alignment: no sequence editing, fuzzy dates or guessed runs."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from zipfile import ZipFile

import pandas as pd

from .data import fingerprints, load, save_json, sha256
from .external import ATTRIBUTION, CUTOFF, freeze_pilot, index_archives, normalize, register_aliases, team_key
from .state import before_events, match_flags
from .pilot_report import make_pilot_report

KINDS = {"Caught": "caught", "Bowled": "bowled", "LBW": "lbw", "Stump": "stumped",
         "Hit Wicket": "hit wicket", "Runout": "run out", "RunOut": "run out", "Retire Out": "retired out",
         "Obstructing The Field": "obstructing the field"}
EXTRAS = {"wide": "wides", "Overstep": "noballs", "byes": "byes", "legbyes": "legbyes", "Penalty": "penalty"}


def candidates_for(match, index):
    key = "|".join(sorted(map(team_key, [match["home_team"], match["away_team"]])))
    return index.loc[index.family.eq(match["family"]) & index.date.eq(match["match_date"]) &
                     index.teams_key.eq(key)].drop_duplicates(["archive", "member"])


def name_compatible(full, abbreviated):
    a, b = normalize(full).split(), normalize(abbreviated).split()
    if not a or not b:
        return False
    if a == b or (len(a) > 1 and sorted(a) == sorted(b)):
        return True
    # Full two-token suffixes support omitted family-name prefixes. One-token
    # surname matches alone are insufficient evidence of identity.
    if min(len(a), len(b)) >= 2 and (a == b[-len(a):] or b == a[-len(b):]):
        return True
    return len(a) > 1 and len(b) > 1 and a[-1] == b[-1] and a[0][0] == b[0][0]


def player_crosswalk(events, public, match, aliases=None):
    """Unique surname/first-initial within team is a candidate identity.

    Acceptance additionally requires every actor on every event to match.
    Ambiguous candidates never receive a guessed identity.
    """
    team_names = {match["home_team_id"]: team_key(match["home_team"]),
                  match["away_team_id"]: team_key(match["away_team"])}
    roster = {team_key(k): v for k, v in public["info"]["players"].items()}
    registry = public["info"]["registry"]["people"]
    aliases = aliases or {}
    identities = defaultdict(set)
    for e in events:
        for role in ("striker", "non_striker", "bowler"):
            team = e["bowling_team_id"] if role == "bowler" else e["batting_team_id"]
            identities[(e[f"{role}_id"], team)].add(e[f"{role}_name"])
    proposed = {}
    rows = []
    for (pid, team), names in sorted(identities.items()):
        pool = roster.get(team_names.get(team), [])
        exact = [n for n in pool if any(normalize(a) in ({normalize(n)} | aliases.get(registry.get(n), set())) for a in names)]
        possible = exact or [n for n in pool if any(name_compatible(a, variant) for a in names
            for variant in ({n} | aliases.get(registry.get(n), set())))]
        chosen = possible[0] if len(possible) == 1 else None
        if chosen and chosen in registry:
            proposed[pid] = chosen
        rows.append({"match_id": match["match_id"], "player_id": pid, "team_id": team,
            "supplied_names": "|".join(sorted(names)), "candidate_names": "|".join(possible),
            "public_name": chosen, "public_person_id": registry.get(chosen),
            "identity_rule": "exact_name_or_register_alias" if exact else "unique_team_name_or_registered_variant"})
    reverse = Counter(proposed.values())
    proposed = {k: v for k, v in proposed.items() if reverse[v] == 1}
    for row in rows:
        row["identity_resolved"] = row["player_id"] in proposed
    return proposed, rows


def flatten(public):
    events = []
    for innings, frame in enumerate(public["innings"], 1):
        sequence = 0
        for over_index, over in enumerate(frame["overs"]):
            for offset, delivery in enumerate(over["deliveries"], 1):
                sequence += 1
                events.append({**delivery, "innings": innings, "overid": over["over"] + 1,
                    "over_ball_num": offset, "innings_ball_num": sequence, "team": frame["team"],
                    "source_pointer": f"/innings/{innings-1}/overs/{over_index}/deliveries/{offset-1}"})
    return events


def align_events(raw, public, identities, match, reviewed_retirements=frozenset()):
    """Return candidate corrections and all failures; callers must gate the entire match."""
    external = flatten(public)
    failures, corrections = [], []
    if len(raw) != len(external):
        return [], [{"event_id": "", "reason": "event_count_mismatch",
                     "detail": f"supplied={len(raw)} external={len(external)}"}]
    team_names = {match["home_team_id"]: team_key(match["home_team"]),
                  match["away_team_id"]: team_key(match["away_team"])}
    for r, p in zip(raw, external):
        errors = []
        for key in ("innings", "overid", "over_ball_num", "innings_ball_num"):
            if r[key] != p[key]:
                errors.append(key)
        if team_names.get(r["batting_team_id"]) != team_key(p["team"]):
            errors.append("batting_team")
        for a, b in (("striker", "batter"), ("non_striker", "non_striker"), ("bowler", "bowler")):
            if identities.get(r[f"{a}_id"]) != p[b]:
                errors.append(a)
        runs, extras = p["runs"], p.get("extras", {})
        if (set(extras) - {"wides", "noballs", "byes", "legbyes", "penalty"} or
                any(type(v) is not int or v < 0 for v in [*extras.values(), runs["batter"], runs["extras"], runs["total"]]) or
                sum(extras.values()) != runs["extras"] or runs["batter"] + runs["extras"] != runs["total"]):
            errors.append("external_run_arithmetic")
        if r["recorded_runs"] != runs["batter"]:
            errors.append("batter_runs")
        category = r["extras_type"]
        if category == "None" and extras:
            errors.append("extra_category")
        elif category in EXTRAS and not extras.get(EXTRAS[category], 0):
            errors.append("extra_category")
        elif category not in {"None", "other", *EXTRAS}:
            errors.append("unrecognized_extra_category")
        wickets = [w for w in p.get("wickets", []) if w["kind"] != "retired hurt"]
        if bool(wickets) != r["is_wicket"] or len(wickets) > 1:
            errors.append("wicket_flag")
        elif wickets:
            w = wickets[0]
            public_kind = "caught" if w["kind"] == "caught and bowled" else w["kind"]
            if KINDS.get(r["dismissal_type"]) != public_kind:
                errors.append("dismissal_kind")
            if identities.get(r["dismissed_player_id"]) != w["player_out"]:
                errors.append("dismissed_player")
        retired = [w for w in p.get("wickets", []) if w["kind"] == "retired hurt"]
        if retired:
            participants = {identities.get(r["striker_id"]), identities.get(r["non_striker_id"])}
            if (r["event_id"] not in reviewed_retirements or r["is_wicket"] or
                    len(retired) != 1 or retired[0]["player_out"] not in participants):
                errors.append("retirement_requires_review")
        for reason in errors:
            failures.append({"event_id": r["event_id"], "reason": reason, "detail": p["source_pointer"]})
        corrections.append({"event_id": r["event_id"], "match_id": r["match_id"], "innings": r["innings"],
            "innings_ball_num": r["innings_ball_num"], "source_row": r["source_row"],
            "source_pointer": p["source_pointer"], "recorded_runs": r["recorded_runs"],
            "recorded_extras_category": category, "recorded_extras_2_runs": r["extras_2_runs"],
            "batter_runs": runs["batter"], "extras_runs": runs["extras"], "team_runs": runs["total"],
            **{f"extras_{k}": extras.get(k, 0) for k in ("wides", "noballs", "byes", "legbyes", "penalty")},
            "legal_delivery_verified": not (extras.get("wides", 0) or extras.get("noballs", 0)),
            "event_alignment_pass": not errors})
    return corrections, failures


def score_checks(public, match):
    """Independent ledger arithmetic and ordinary outcome/terminal checks."""
    kind, margin, raw_adjusted = match_flags(match)
    info, innings = public["info"], public["innings"]
    reasons = []
    if info.get("balls_per_over") != 6:
        reasons.append("unsupported_balls_per_over")
    totals, counts, cumulative, legal_counts = [], [], [], []
    if (len(innings) != 2 or any(i.get("super_over") for i in innings)):
        return {"score_pass": False, "score_reason": "superover_or_missing_innings", "adjusted": raw_adjusted}
    adjusted = raw_adjusted or bool(info["outcome"].get("method")) or info.get("overs") != 20
    for i in innings:
        if [o["over"] for o in i["overs"]] != list(range(len(i["overs"]))):
            reasons.append("external_over_sequence")
        if i.get("penalty_runs") or i.get("miscounted_overs") or i.get("forfeited") or i.get("declared"):
            reasons.append("special_innings_requires_review")
        ds = [d for o in i["overs"] for d in o["deliveries"]]
        total = 0
        seq = []
        wickets = 0
        legal_total = 0
        for o in i["overs"]:
            legal = sum(not (d.get("extras", {}).get("wides", 0) or d.get("extras", {}).get("noballs", 0)) for d in o["deliveries"])
            if legal > 6 or (o != i["overs"][-1] and legal != 6):
                reasons.append("external_over_legality")
            legal_total += legal
        if legal_total > 120:
            reasons.append("external_innings_length")
        for d in ds:
            if wickets >= 10:
                reasons.append("event_after_all_out")
            total += d["runs"]["total"]
            wickets += sum(w["kind"] != "retired hurt" for w in d.get("wickets", []))
            seq.append(total)
        if wickets > 10:
            reasons.append("too_many_wickets")
        totals.append(total)
        counts.append(wickets)
        cumulative.append(seq)
        legal_counts.append(legal_total)
    outcome = info["outcome"]
    team_names = {match["home_team_id"]: team_key(match["home_team"]), match["away_team_id"]: team_key(match["away_team"])}
    if outcome.get("by", {}).get(kind) != margin or team_names.get(match["win_team_id"]) != team_key(outcome.get("winner", "")):
        reasons.append("supplied_external_result_conflict")
    target = totals[0] + 1
    if not adjusted:
        if legal_counts[0] != 120 and counts[0] != 10:
            reasons.append("incomplete_first_innings")
        if innings[1].get("target", {}).get("runs", target) != target:
            reasons.append("external_target_conflict")
        if kind == "runs":
            if legal_counts[1] != 120 and counts[1] != 10:
                reasons.append("incomplete_losing_chase")
            if totals[0] - totals[1] != margin or team_key(outcome.get("winner", "")) != team_key(innings[0]["team"]):
                reasons.append("run_margin")
        elif kind == "wickets":
            if (counts[1] != 10 - margin or not cumulative[1] or cumulative[1][-1] < target or
                    any(v >= target for v in cumulative[1][:-1]) or
                    team_key(outcome.get("winner", "")) != team_key(innings[1]["team"])):
                reasons.append("wicket_chase_terminal")
        else:
            reasons.append("non_decisive_result")
    else:
        reasons.append("adjusted_target_timing_unverified")
    return {"score_pass": not reasons, "score_reason": "|".join(sorted(set(reasons))), "adjusted": adjusted,
            "first_total": totals[0], "second_total": totals[1], "second_wickets": counts[1],
            "ordinary_target": target if not adjusted else None}


def verified_states(raw, corrections, config):
    """Only invoked after complete-match alignment AND score checks pass."""
    lookup = {e["event_id"]: e for e in raw}
    target = sum(c["team_runs"] for c in corrections if c["innings"] == 1) + 1
    states = []
    rule = config["rule_pressure"]
    for innings in (1, 2):
        subset = [c for c in corrections if c["innings"] == innings]
        # Existing wicket-window implementation gets externally verified legality.
        proxies = [{**lookup[c["event_id"]], "extras_type": "None" if c["legal_delivery_verified"] else "wide"} for c in subset]
        score = 0
        for c, proxy in zip(subset, before_events(proxies, rule)):
            remaining = proxy["balls_remaining"]
            required = target - score if innings == 2 else None
            rpb = required / remaining if innings == 2 and remaining > 0 else None
            tight = (rpb is not None and rule["chase_balls_remaining_inclusive"][0] <= remaining <= rule["chase_balls_remaining_inclusive"][1]
                     and rule["required_runs_per_ball_inclusive"][0] <= rpb <= rule["required_runs_per_ball_inclusive"][1])
            states.append({"event_id": c["event_id"], "match_id": c["match_id"], "innings": innings,
                **proxy, "score_before": score, "chase_target": target if innings == 2 else None,
                "runs_required": required, "required_run_rate": rpb * 6 if rpb is not None else None,
                "tight_chase": tight, "pressure_full": proxy["pressure_proxy"] or tight,
                "score_verified_pilot": True})
            score += c["team_runs"]
    return states


def run_pilot(root):
    selection = freeze_pilot(root)
    source = root / "6af3166e7b922_data_pack"
    before = fingerprints(source)
    config = json.loads((root / "configs/analysis_preregistration.json").read_text())
    if config["data_cutoff_inclusive"] != CUTOFF:
        raise ValueError("Cutoff changed")
    _, matches, events, _, _ = load(root, CUTOFF)
    index = index_archives(root)
    aliases = register_aliases(root)
    out = root / "reports/reconciliation_pilot_2026-11-01"
    index.to_csv(root / "data/external/cricsheet/index.csv", index=False)
    results, corrections, failures, identities, states = [], [], [], [], []
    for selected in selection.to_dict("records"):
        mid = selected["match_id"]
        match = matches.set_index("match_id", drop=False).loc[mid].to_dict()
        raw = events.loc[events.match_id.eq(mid)].sort_values(["innings", "innings_ball_num"]).to_dict("records")
        candidates = candidates_for(match, index)
        result = {"match_id": mid, "date": match["match_date"], "family": match["family"], "year": match["year"],
            "supplied_events": len(raw), "candidate_count": len(candidates), "matched": len(candidates) == 1,
            "alignment_pass": False, "score_pass": False, "accepted": False}
        if len(candidates) != 1:
            result["status"] = "missing_external_match" if candidates.empty else "ambiguous_external_match"
            results.append(result)
            continue
        candidate = candidates.iloc[0].to_dict()
        with ZipFile(root / "data/external/cricsheet" / candidate["archive"]) as archive:
            payload = archive.read(candidate["member"])
        if hashlib.sha256(payload).hexdigest() != candidate["member_sha256"]:
            raise ValueError("Source member changed")
        public = json.loads(payload)
        crosswalk, identity_rows = player_crosswalk(raw, public, match, aliases)
        identities.extend(identity_rows)
        proposed, issues = align_events(raw, public, crosswalk, match)
        checks = score_checks(public, match)
        result.update(checks)
        result.update({"member": candidate["member"], "alignment_pass": not issues,
                       "alignment_failure_count": len(issues), "accepted": not issues and checks["score_pass"]})
        result["status"] = "accepted" if result["accepted"] else "quarantined"
        results.append(result)
        failures.extend({"match_id": mid, **i} for i in issues)
        for c in proposed:
            c.update({"match_accepted": result["accepted"], "source_member": candidate["member"],
                      "source_archive": candidate["archive"], "source_sha256": candidate["member_sha256"]})
        corrections.extend(proposed)
        if result["accepted"]:
            states.extend(verified_states(raw, proposed, config))
        print(f"{mid}: {result['status']}; alignment issues={len(issues)}; {checks['score_reason']}", flush=True)
    frames = {"matches": pd.DataFrame(results), "candidate_corrections": pd.DataFrame(corrections),
        "alignment_failures": pd.DataFrame(failures), "player_crosswalk": pd.DataFrame(identities),
        "verified_preball_states": pd.DataFrame(states)}
    resolved = frames["player_crosswalk"].query("identity_resolved")
    if (resolved.groupby("player_id").public_person_id.nunique() > 1).any():
        raise ValueError("One supplied player ID maps to multiple public identities across pilot matches")
    frame = frames["candidate_corrections"]
    frames["verified_corrections"] = frame.loc[frame.match_accepted].copy() if len(frame) else frame.copy()
    summary = frames["matches"].groupby(["year", "family"], as_index=False).agg(
        selected=("match_id", "size"), matched=("matched", "sum"), aligned=("alignment_pass", "sum"),
        score_pass=("score_pass", "sum"), accepted=("accepted", "sum"), supplied_events=("supplied_events", "sum"))
    for metric in ("matched", "aligned", "score_pass", "accepted"):
        summary[f"{metric}_percent_of_selected"] = summary[metric] / summary.selected * 100
    frames["summary_by_year_family"] = summary
    for name, frame in frames.items():
        frame.to_csv(out / f"{name}.csv", index=False)
    frames["verified_corrections"].to_parquet(out / "verified_corrections.parquet", index=False)
    frames["verified_preball_states"].to_parquet(out / "verified_preball_states.parquet", index=False)
    make_pilot_report(frames, out)
    if fingerprints(source) != before:
        raise ValueError("Raw inputs changed")
    save_json(out / "manifest.json", {"source_sha256": before, "raw_inputs_unchanged": True,
        "cutoff": CUTOFF, "attribution": ATTRIBUTION, "selection_sha256": sha256(out / "selection.csv"),
        "config_sha256": sha256(root / "configs/analysis_preregistration.json"),
        "external_snapshots": {p.name: json.loads(p.read_text()) for p in sorted((root / "data/external/cricsheet").glob("*.manifest.json"))},
        "code_sha256": {str(p.relative_to(root)): sha256(p) for p in sorted((root / "src").rglob("*.py"))},
        "output_sha256": {p.name: sha256(p) for p in sorted(out.iterdir()) if p.suffix in (".csv", ".parquet", ".md")},
        "pilot_only": True, "global_mode_a_ready": False, "player_rankings_created": False})
    print(summary.to_string(index=False))
    return frames
