"""Local-only scoring hypotheses and pre-ball pressure diagnostics; no data repair.

Run from the repository root: python3 scripts/reconcile_and_pressure.py
Only the standard library is required. Outputs contain proprietary-derived data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "6af3166e7b922_data_pack"
OUT = ROOT / "artifacts" / "reconciliation_2026-11-01"
CUTOFF = "2026-11-01"
ONE_EXTRA = {"wide", "Overstep", "byes", "legbyes"}
ILLEGAL = {"wide", "Overstep"}
KNOWN = ONE_EXTRA | {"None"}


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def parse_result(result):
    lower = result.lower()
    if any(term in lower for term in ("tied", "super over", "superover", "one over eliminator")):
        return "tie", None
    if "abandon" in lower:
        return "abandoned", None
    if "no result" in lower:
        return "no_result", None
    match = re.search(r"\bwon\s+(?:by\s+)?(\d+)\s*(runs?|wickets?|wkts?)\b", lower)
    if match:
        return ("runs" if match[2].startswith("run") else "wickets"), int(match[1])
    return "unparsed", None


def rain_flag(match):
    return bool(re.search(r"\bd\s*/?\s*ls?\b|duckworth", match["result"], re.I)) or any(
        match[k] for k in ("first_inn_revised_overs", "second_inn_revised_overs", "revised_target")
    )


def event_runs(event, mode):
    # Exactly the two requested hypotheses; extras_2_runs is NOT silently added.
    return int(event["runs"]) + int(mode == "b" and event["extras_type"] in ONE_EXTRA)


def chase_check(events, target, mode):
    """Necessary final-crossing consistency, not proof of correct intermediate scores."""
    total = 0
    crossed_early = False
    for index, event in enumerate(events):
        total += event_runs(event, mode)
        if index < len(events) - 1 and total >= target:
            crossed_early = True
    return total >= target, bool(events) and total >= target and not crossed_early


def legal_structure(events):
    if not events:
        return False, "missing_innings"
    if any(e["extras_type"] not in KNOWN for e in events):
        return False, "unknown_extra_category"
    overs = Counter()
    for event in events:
        overs[int(event["overid"])] += event["extras_type"] not in ILLEGAL
    last = max(overs)
    if not (1 <= last <= 20 and all(overs[o] == 6 for o in range(1, last)) and 0 <= overs[last] <= 6):
        return False, "over_legality_mismatch"
    return True, "known_categories_and_structural_check"


def pressure_events(events, targets):
    """Yield pre-event flags. Targets are explicitly hypothetical, not verified."""
    legal_before = wickets_before = 0
    scores = {"a": 0, "b": 0}
    recent = deque()
    for event in events:
        while recent and recent[0][0] < legal_before - 12:
            recent.popleft()
        over = int(event["overid"])
        late = 16 <= over <= 20
        collapse = sum(w for _, w in recent) >= 2 or (over <= 10 and wickets_before >= 4)
        base = late or collapse
        second = event["innings"] == "2"
        remaining = 120 - legal_before
        chase_window = second and 0 < remaining <= 60
        flags = {
            "late": late, "collapse": collapse, "base": base,
            "lower": base, "upper": base or chase_window,
            "legal": event["extras_type"] not in ILLEGAL,
        }
        for mode in ("a", "b"):
            tight = bool(chase_window and targets[mode] is not None and
                         0.75 <= (targets[mode] - scores[mode]) / remaining <= 1.50)
            flags[f"tight_{mode}"] = tight
            flags[f"high_{mode}"] = base or tight
            flags[f"tight_only_{mode}"] = tight and not base
            flags[f"already_reached_{mode}"] = bool(second and targets[mode] is not None and
                                                       scores[mode] >= targets[mode])
        yield flags
        wicket = event["is_wicket"].lower() == "true"
        recent.append((legal_before, int(wicket)))
        wickets_before += wicket
        legal_before += flags["legal"]
        for mode in ("a", "b"):
            scores[mode] += event_runs(event, mode)


def grouped(rows, dimensions):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in dimensions)].append(row)
    return sorted(groups.items())


def reconcile(matches, balls):
    output = []
    for match in matches:
        kind, margin = parse_result(match["result"])
        first = balls.get((match["match_id"], "1"), [])
        second = balls.get((match["match_id"], "2"), [])
        complete = bool(first and second)
        adjusted = rain_flag(match)
        row = {
            "match_id": match["match_id"], "date": match["match_date"],
            "year": match["match_date"][:4], "comp_id": match["comp_id"],
            "competition": match["competition"], "family": match["family"],
            "result": match["result"], "kind": kind, "official_margin": margin,
            "cohort": "adjusted_or_rain" if adjusted else "ordinary",
            "two_innings_present": complete,
            "primary_comparison": complete and not adjusted and kind in {"runs", "wickets"},
            "innings1_events": len(first), "innings2_events": len(second),
            "innings1_unknown_extra_events": sum(e["extras_type"] not in KNOWN for e in first),
            "innings2_unknown_extra_events": sum(e["extras_type"] not in KNOWN for e in second),
            "innings1_unit_extra_events": sum(e["extras_type"] in ONE_EXTRA for e in first),
            "innings2_unit_extra_events": sum(e["extras_type"] in ONE_EXTRA for e in second),
            "revised_target": match["revised_target"],
            "first_inn_revised_overs": match["first_inn_revised_overs"],
            "second_inn_revised_overs": match["second_inn_revised_overs"],
            "innings2_wickets": sum(e["is_wicket"].lower() == "true" for e in second),
        }
        row["wicket_margin_pass"] = (row["innings2_wickets"] == 10 - margin
                                      if kind == "wickets" and complete else None)
        row["winner_side_pass"] = (
            match["win_team_id"] == (first if kind == "runs" else second)[0]["batting_team_id"]
            if kind in {"runs", "wickets"} and complete else None
        )
        for mode in ("a", "b"):
            x = sum(event_runs(e, mode) for e in first)
            y = sum(event_runs(e, mode) for e in second)
            row[f"innings1_{mode}"] = x if first else None
            row[f"innings2_{mode}"] = y if second else None
            row[f"difference_{mode}"] = x - y if complete else None
            row[f"run_margin_gap_{mode}"] = x - y - margin if complete and kind == "runs" else None
            row[f"run_margin_pass_{mode}"] = x - y == margin if complete and kind == "runs" else None
            target = x + 1
            reached, terminal = chase_check(second, target, mode) if complete else (None, None)
            row[f"chase_target_{mode}"] = target if complete and kind == "wickets" else None
            row[f"chase_reached_{mode}"] = reached if kind == "wickets" else None
            row[f"chase_terminal_{mode}"] = terminal if kind == "wickets" else None
            row[f"chase_combined_{mode}"] = (terminal and row["wicket_margin_pass"] and row["winner_side_pass"]
                                               if complete and kind == "wickets" else None)
            revised = int(match["revised_target"]) if match["revised_target"] else None
            row[f"revised_run_margin_pass_{mode}"] = (
                revised - 1 - y == margin if complete and revised and kind == "runs" else None)
            row[f"revised_chase_terminal_{mode}"] = (
                chase_check(second, revised, mode)[1] if complete and revised and kind == "wickets" else None)
        output.append(row)
    return output


def margin_summaries(rows, dimensions):
    output = []
    for key, members in grouped(rows, dimensions):
        for kind in ("runs", "wickets"):
            sample = [r for r in members if r["kind"] == kind and r["two_innings_present"]]
            if not sample:
                continue
            row = dict(zip(dimensions, key)) | {"kind": kind, "n": len(sample)}
            for mode in ("a", "b"):
                metric = "run_margin_pass" if kind == "runs" else "chase_combined"
                passes = sum(bool(r[f"{metric}_{mode}"]) for r in sample)
                row[f"pass_{mode}"] = passes
                row[f"pass_pct_{mode}"] = round(100 * passes / len(sample), 4)
                if kind == "runs":
                    row[f"mean_abs_gap_{mode}"] = round(sum(abs(r[f"run_margin_gap_{mode}"]) for r in sample) / len(sample), 4)
                else:
                    row[f"mean_abs_gap_{mode}"] = None
                row[f"target_reached_{mode}"] = sum(bool(r[f"chase_reached_{mode}"]) for r in sample) if kind == "wickets" else None
                row[f"terminal_crossing_{mode}"] = sum(bool(r[f"chase_terminal_{mode}"]) for r in sample) if kind == "wickets" else None
            row["wicket_margin_pass"] = sum(bool(r["wicket_margin_pass"]) for r in sample) if kind == "wickets" else None
            output.append(row)
    return output


def pressure_analysis(matches, balls):
    counts = defaultdict(Counter)
    exclusions = []
    included_innings = []
    for match in matches:
        kind, margin = parse_result(match["result"])
        if rain_flag(match) or kind not in {"runs", "wickets", "tie"}:
            reason = "adjusted_or_rain" if rain_flag(match) else kind
            exclusions.append({"match_id": match["match_id"], "innings": "all", "reason": reason,
                               "events": sum(len(balls.get((match["match_id"], i), [])) for i in ("1", "2"))})
            continue
        first = balls.get((match["match_id"], "1"), [])
        targets = {mode: 1 + sum(event_runs(e, mode) for e in first) if first else None for mode in ("a", "b")}
        for innings in ("1", "2"):
            events = balls.get((match["match_id"], innings), [])
            safe, reason = legal_structure(events)
            if safe and kind == "wickets" and innings == "2" and sum(e["is_wicket"].lower() == "true" for e in events) != 10 - margin:
                safe, reason = False, "wicket_margin_conflict"
            if not safe:
                exclusions.append({"match_id": match["match_id"], "innings": innings,
                                   "reason": reason, "events": len(events)})
                continue
            included_innings.append({"match_id": match["match_id"], "innings": innings,
                                     "family": match["family"], "events": len(events),
                                     "target_a": targets["a"], "target_b": targets["b"],
                                     "target_status": "unverified_hypotheses"})
            for flags in pressure_events(events, targets):
                denominators = ["delivery_events"] + (["legal_deliveries"] if flags["legal"] else [])
                for denominator in denominators:
                    counter = counts[(match["match_date"][:4], match["family"], match["comp_id"],
                                      match["competition"], innings, denominator)]
                    counter["n"] += 1
                    counter.update({k: int(v) for k, v in flags.items() if k != "legal"})
    rows = []
    for key, counter in sorted(counts.items()):
        rows.append(dict(zip(("year", "family", "comp_id", "competition", "innings", "denominator"), key)) | dict(counter))
    return rows, exclusions, included_innings


def pressure_summary(rows, dimensions):
    output = []
    for key, members in grouped(rows, dimensions):
        counter = Counter()
        for row in members:
            counter.update({k: v for k, v in row.items() if isinstance(v, int)})
        item = dict(zip(dimensions, key)) | dict(counter)
        item.update({k + "_pct": round(100 * v / counter["n"], 4) for k, v in counter.items() if k != "n"})
        output.append(item)
    return output


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] +
                     ["| " + " | ".join(str(v) for v in row) + " |" for row in rows])


def report(reconciliation, pressures, excluded, included, manifest):
    ordinary = [r for r in reconciliation if r["primary_comparison"]]
    adjusted = [r for r in reconciliation if r["cohort"] == "adjusted_or_rain"]
    summary = margin_summaries(ordinary, [])
    def fmt(row, mode):
        return f"{row['pass_' + mode]}/{row['n']} ({row['pass_pct_' + mode]:.1f}%)"
    sections = [
        "# Run-margin reconciliation and baseline pressure audit",
        "Frozen match-date cutoff: **1 November 2026 inclusive**. Local supplied data only; no Cricsheet alignment, public-data download, source correction, player ranking or threshold optimisation was performed.",
        "## Scoring hypotheses and denominators",
        "**A:** sum only `runs`. **B:** sum `runs` plus one for each event with `extras_type` in `wide`, `Overstep` (hypothesised no-ball), `byes`, or `legbyes`. `extras1_runs` is never added. Neither rule adds `extras_2_runs`, `other`, or `Penalty`: their quantities/semantics are not assumed. B is exactly the requested diagnostic hypothesis, not an accepted scoring rule.",
        "Result parsing is case-insensitive and includes `Wkts`, missing spaces, and `Won N Runs` without `by`. Ties/super overs are classified before parsing margins. Ordinary comparisons exclude every match with D/L/DLS text, a revised target, or revised-over fields. Both totals and literal differences are still exported for adjusted matches; those differences need not equal a DLS margin.",
        "For run wins, pass means first-innings hypothesis total minus second-innings hypothesis total equals the reported margin exactly. For wicket wins, the stronger combined pass requires the hypothetical target (first total + 1) to be reached on the final recorded event, never earlier, the wicket count to equal 10 minus the reported winning margin, and the winning side to be the chasing side. Also export the weaker target-reached check separately. A pass is only arithmetic consistency; offsetting missing extras can conceal incorrect totals and intermediate states.",
        "## Ordinary matches: overall",
        table(["Outcome", "Matches", "A: exact/combined pass", "B: exact/combined pass"],
              [[r["kind"], r["n"], fmt(r, "a"), fmt(r, "b")] for r in summary]),
        "## By year",
        table(["Year", "Outcome", "A", "B"],
              [[r["year"], r["kind"], fmt(r, "a"), fmt(r, "b")] for r in margin_summaries(ordinary, ["year"])]),
        "## By competition family",
        table(["Competition family", "Outcome", "A", "B"],
              [[r["family"], r["kind"], fmt(r, "a"), fmt(r, "b")] for r in margin_summaries(ordinary, ["family"])]),
        "Full competition-by-competition and year-by-competition rates, including denominators and zero passes, are in [by_competition.csv](by_competition.csv) and [by_year_competition.csv](by_year_competition.csv). [by_year_family.csv](by_year_family.csv) gives the compact cross-tab. Rain/adjusted cohorts are separately labelled in every aggregate CSV.",
        "## Wicket-win checks separately",
    ]
    chases = [r for r in ordinary if r["kind"] == "wickets"]
    sections.append(table(["Rule", "Target reached", "Crossed only at final event", "Crossing + wickets + winner"], [
        [mode.upper(), f"{sum(r[f'chase_reached_{mode}'] for r in chases)}/{len(chases)}",
         f"{sum(r[f'chase_terminal_{mode}'] for r in chases)}/{len(chases)}",
         f"{sum(r[f'chase_combined_{mode}'] for r in chases)}/{len(chases)}"] for mode in ("a", "b")]))
    sections.append(f"Wicket-margin agreement independent of run rule: {sum(r['wicket_margin_pass'] for r in chases)}/{len(chases)}. Match 20190 reports a six-wicket win but records five second-innings wicket events; this is an unresolved conflict between the result and event data, not proof of which field is wrong. Its second innings is excluded from pressure coverage. No claim that merely exceeding an inferred target verifies a chase score.")
    sections += ["## Adjusted matches and exclusions",
                 f"{len(adjusted)} metadata matches have a rain/adjustment marker. `matches.csv` retains all source matches within cutoff, including missing innings and non-margin results. `adjusted_summary.csv` shows literal-difference results separately; `revised_*` columns in the event-free match audit check the final supplied revised target where available. These are diagnostics only: DLS stoppage results and missing revision timing can invalidate ordinary terminal-crossing logic.",
                 "## Mode A repair decision",
                 "**Reject both A and B as a universal score reconstruction. Do not apply one-run extras, distribute residual runs, or select only margin-passing matches as if their delivery scores were verified.** Exact margin agreement only constrains the difference between the two innings' missing extras; it does not recover either innings total or the timing of extras.",
                 "Preferred repair: first obtain the organiser's scoring dictionary/corrected export, particularly explicit per-delivery extras and team totals. The clarification is drafted separately and remains unsent. If unavailable, a subsequent explicitly documented external event-ledger alignment may fill the missing quantities, with exact event matching, innings-total checks and coverage reporting. No external alignment has started. Preserve the RR event/player universe and store corrections separately. Mode A remains blocked pending verified per-delivery state; continue only the score-independent diagnostic/fallback meanwhile.",
                 "## Baseline pressure coverage",
                 "The rule is unchanged: `late OR collapse OR tight_chase`. Late = overs 16–20. Collapse = at least two wickets in the preceding 12 legal-ball positions (including intervening illegal events), OR at least four wickets already lost while still in overs 1–10. The early-collapse clause is not latched through the rest of the innings. Tight chase = second innings, 1–60 legal balls remaining, and pre-event runs required per ball in [0.75, 1.50]. All flags are computed before the event.",
                 "Primary scope is IPL + T20I, normal innings of completed, unadjusted matches. Tied normal innings are allowed, super-over innings are not. Within that scope, retain only innings with known extra categories and structurally consistent over lengths under wide/Overstep illegal-ball conventions; exclude a chasing innings whose wicket ledger contradicts the reported winning margin. This tests internal consistency, not independently verified scoring semantics. Other T20 results are exported separately. Unknown-extra/over-mismatch innings are excluded, not silently repaired.",
                 "Because neither scoring hypothesis is verified, **the full rule's true high-pressure share is not yet identifiable**. We report (1) the score-independent late/collapse share, (2) full-rule sensitivity under A/B, and (3) a conservative range when tight-chase state is unknown. The upper bound permits every remaining second-innings opportunity in the final 60 legal balls to qualify. A/B rates are not validated pressure labels; any events after a hypothetical target was already reached are retained and counted as another symptom of invalid score reconstruction."]
    primary = [r for r in pressures if r["family"] in {"IPL", "T20I"}]
    overall = pressure_summary(primary, ["denominator"])
    sections.append(table(["Denominator", "N", "Late", "Collapse", "Late OR collapse", "Full rule A", "Full rule B", "Unknown-score range"], [
        [r["denominator"], r["n"], f"{r['late_pct']:.2f}%", f"{r['collapse_pct']:.2f}%", f"{r['base_pct']:.2f}%",
         f"{r['high_a_pct']:.2f}%", f"{r['high_b_pct']:.2f}%", f"{r['lower_pct']:.2f}–{r['upper_pct']:.2f}%"] for r in overall]))
    for row in overall:
        if row["base_pct"] > 30:
            sections.append(f"**Outside the 20–30% target ({row['denominator']}):** late OR collapse alone already flags {row['base_pct']:.2f}%. Adding tight chases cannot reduce that share. The union of a five-over late phase and overlapping collapse windows is structurally broader than a top-quartile pressure definition. No threshold has been changed to force the target or affect player selection.")
        else:
            sections.append(f"For {row['denominator']}, the score-independent lower bound is {row['base_pct']:.2f}%; A/B full-rule rates are {row['high_a_pct']:.2f}%/{row['high_b_pct']:.2f}%. Compare these with the 20–30% target as provisional sensitivities only; the validated full share requires repaired scores.")
    primary_included = [r for r in included if r["family"] in {"IPL", "T20I"}]
    sections.append(f"Pressure diagnostic retains {len(primary_included)} primary-cohort innings from {len({r['match_id'] for r in primary_included})} distinct matches. This is an innings-level filter: some matches contribute only one innings. Hypothetical targets may use an unverified first innings, which is why full-rule A/B values remain provisional. See `pressure_included_innings.csv`, `pressure_exclusions.csv`, and `pressure_coverage.json` for exact population counts.")
    sections += ["### Pressure by year (delivery events, primary scope)",
                 table(["Year", "N", "Late OR collapse", "Full A", "Full B"], [
                     [r["year"], r["n"], f"{r['base_pct']:.2f}%", f"{r['high_a_pct']:.2f}%", f"{r['high_b_pct']:.2f}%"]
                     for r in pressure_summary([r for r in primary if r["denominator"] == "delivery_events"], ["year"])]),
                 "### Pressure by competition family (delivery events)",
                 table(["Family", "N", "Late OR collapse", "Full A", "Full B"], [
                     [r["family"], r["n"], f"{r['base_pct']:.2f}%", f"{r['high_a_pct']:.2f}%", f"{r['high_b_pct']:.2f}%"]
                     for r in pressure_summary([r for r in pressures if r["denominator"] == "delivery_events"], ["family"])]),
                 "## Reproduction and limitations",
                 "Run `rtk proxy python3 scripts/reconcile_and_pressure.py`. Hypothesis code is covered by synthetic tests in `tests/test_reconcile_and_pressure.py`. The manifest fingerprints all supplied files before and after execution and records the analysis script hash. No raw file is modified. Full CSV artifacts remain local.",
                 "This is a reconciliation audit, not completed Mode A validation. Results are based on supplied match dates, results and event data; we have not independently verified source accuracy. The margin match is an internal consistency test. Pressure subset exclusions may be nonrandom, and interval bounds do not extrapolate to excluded innings. No player-name-based analysis or threshold tuning has occurred."]
    return "\n\n".join(sections) + "\n"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    registration_path = ROOT / "configs" / "analysis_preregistration.json"
    registration = json.loads(registration_path.read_text())
    assert registration["data_cutoff_inclusive"] == CUTOFF
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.iterdir()) if p.is_file()}
    competitions = {r["comp_id"]: r for r in read_csv(SOURCE / "competitions.csv")}
    all_matches = read_csv(SOURCE / "matches.csv")
    matches = [r for r in all_matches if r["match_date"] <= CUTOFF]
    match_ids = {r["match_id"] for r in matches}
    for match in matches:
        comp = competitions[match["comp_id"]]
        match["competition"] = comp["comp_name"]
        match["family"] = "IPL" if comp["comp_name"].startswith("IPL ") else "T20I" if comp["match_format"] == "T20I" else "Other T20"
    balls = defaultdict(list)
    raw_balls = read_csv(SOURCE / "ball_by_ball.csv")
    for event in raw_balls:
        if event["match_id"] in match_ids:
            balls[event["match_id"], event["innings"]].append(event)
    for events in balls.values():
        events.sort(key=lambda r: int(r["innings_ball_num"]))
    audit = reconcile(matches, balls)
    assert not [r for r in audit if r["kind"] == "unparsed"], "Unparsed results require review"
    write_csv(OUT / "matches.csv", audit)
    for name, dimensions in {
        "overall": ["cohort"], "by_year": ["cohort", "year"],
        "by_family": ["cohort", "family"], "by_year_family": ["cohort", "year", "family"],
        "by_competition": ["cohort", "comp_id", "competition", "family"],
        "by_year_competition": ["cohort", "year", "comp_id", "competition", "family"],
    }.items():
        write_csv(OUT / f"{name}.csv", margin_summaries(audit, dimensions))
    write_csv(OUT / "adjusted_summary.csv", margin_summaries([r for r in audit if r["cohort"] == "adjusted_or_rain"], ["year", "family"]))
    pressures, excluded, included = pressure_analysis(matches, balls)
    write_csv(OUT / "pressure_detail.csv", pressures)
    write_csv(OUT / "pressure_exclusions.csv", excluded)
    write_csv(OUT / "pressure_included_innings.csv", included)
    for name, dimensions in {
        "by_year_family": ["year", "family", "denominator"],
        "by_competition": ["comp_id", "competition", "family", "denominator"],
        "by_innings": ["innings", "family", "denominator"],
    }.items():
        write_csv(OUT / f"pressure_{name}.csv", pressure_summary(pressures, dimensions))
    primary_matches = [m for m in matches if m["family"] in {"IPL", "T20I"}]
    base_matches = [m for m in primary_matches if not rain_flag(m) and parse_result(m["result"])[0] in {"runs", "wickets", "tie"}]
    primary_included = [r for r in included if r["family"] in {"IPL", "T20I"}]
    coverage = {
        "all_source_delivery_events": len(raw_balls),
        "primary_normal_innings_events_before_outcome_and_rain_filters": sum(len(balls.get((m["match_id"], i), [])) for m in primary_matches for i in ("1", "2")),
        "primary_completed_unadjusted_events_before_legality_filter": sum(len(balls.get((m["match_id"], i), [])) for m in base_matches for i in ("1", "2")),
        "primary_pressure_diagnostic_events": sum(r["events"] for r in primary_included),
        "primary_pressure_diagnostic_innings": len(primary_included),
        "primary_pressure_diagnostic_matches": len({r["match_id"] for r in primary_included}),
    }
    (OUT / "pressure_coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    hashes_after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.iterdir()) if p.is_file()}
    assert hashes == hashes_after, "Raw inputs changed"
    manifest = {"cutoff": CUTOFF, "source_sha256": hashes, "raw_inputs_unchanged": hashes == hashes_after,
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "preregistration_sha256": hashlib.sha256(registration_path.read_bytes()).hexdigest(),
                "matches_included": len(matches), "matches_after_cutoff_excluded": len(all_matches) - len(matches),
                "external_sources_used": False, "pressure_thresholds_changed": False,
                "result_kinds": dict(Counter(r["kind"] for r in audit))}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (OUT / "REPORT.md").write_text(report(audit, pressures, excluded, included, manifest))
    print(json.dumps({"reconciliation": margin_summaries([r for r in audit if r["primary_comparison"]], []),
                      "pressure": pressure_summary([r for r in pressures if r["family"] in {"IPL", "T20I"}], ["denominator"]),
                      "coverage": coverage, "report": str(OUT / "REPORT.md")}, indent=2))


if __name__ == "__main__":
    main()
