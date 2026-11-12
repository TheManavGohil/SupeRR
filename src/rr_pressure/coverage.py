"""Full supplied-corpus coverage with explicit exception review and rejection ledgers."""

from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from .alignment import align_events, candidates_for, player_crosswalk, score_checks, verified_states
from .data import fingerprints, load, save_json, sha256
from .external import ARCHIVES, ATTRIBUTION, CUTOFF, index_archives, register_aliases, team_key
from .pilot_report import markdown_table
from .reviews import apply_reviews, load_reviews, match_number_review


def coverage_summary(matches, keys):
    result = matches.groupby(keys, dropna=False).agg(
        supplied_matches=("match_id", "size"), matches_with_deliveries=("has_deliveries", "sum"),
        source_events=("supplied_events", "sum"), primary_normal_events=("primary_normal_events", "sum"),
        external_matches=("matched", "sum"), aligned_matches=("alignment_pass", "sum"),
        accepted_matches=("accepted", "sum"), accepted_events=("accepted_events", "sum")).reset_index()
    result["match_retention_percent"] = 100 * result.accepted_matches / result.matches_with_deliveries.replace(0, float("nan"))
    result["event_retention_percent"] = 100 * result.accepted_events / result.source_events.replace(0, float("nan"))
    return result


def write_manifest(root, out, raw_hashes, extra=None):
    save_json(out / "manifest.json", {"cutoff": CUTOFF, "source_sha256": raw_hashes,
        "raw_inputs_unchanged": True, "attribution": ATTRIBUTION,
        "config_sha256": sha256(root / "configs/analysis_preregistration.json"),
        "policy_sha256": sha256(root / "configs/reconciliation_policy.json"),
        "review_sha256": sha256(root / "data/curated/reconciliation_reviews.json") if (root / "data/curated/reconciliation_reviews.json").exists() else None,
        "code_sha256": {str(p.relative_to(root)): sha256(p) for p in sorted((root / "src").rglob("*.py"))},
        "external_snapshots": {p.name: json.loads(p.read_text()) for p in sorted((root / "data/external/cricsheet").glob("*.manifest.json"))},
        "output_sha256": {p.name: sha256(p) for p in sorted(out.iterdir()) if p.suffix in (".csv", ".parquet", ".md")},
        "models_fitted": False, **(extra or {})})


def nearby_candidates(match, index, tolerance):
    key = "|".join(sorted(map(team_key, [match["home_team"], match["away_team"]])))
    pool = index.loc[index.family.eq(match["family"]) & index.teams_key.eq(key)].copy()
    pool["date_offset_days"] = (pd.to_datetime(pool.date) - pd.Timestamp(match["match_date"])).dt.days
    pool = pool.loc[pool.date_offset_days.abs().le(tolerance) & pool.date.le(CUTOFF)]
    pool["absolute_offset"] = pool.date_offset_days.abs()
    return pool.sort_values(["absolute_offset", "date", "member"]).drop_duplicates(["archive", "member"])


def evaluate_candidate(raw, match, candidate, payload, aliases, reviews):
    digest = hashlib.sha256(payload).hexdigest()
    if digest != candidate["member_sha256"]:
        raise ValueError("Source member changed")
    public = json.loads(payload)
    # Reviews are tied to a specific source, so never apply one to a different nearby game.
    relevant = [r for r in reviews["events"] if r["source_member_sha256"] == digest]
    patched, used, retired = apply_reviews(raw, digest, relevant)
    crosswalk, rows = player_crosswalk(patched, public, match, aliases)
    proposed, issues = align_events(patched, public, crosswalk, match, retired)
    checks = score_checks(public, match)
    number = public["info"].get("event", {}).get("match_number")
    ordinal_review = None
    if number is not None and match.get("match_number") and str(number) != str(match["match_number"]):
        ordinal_review = match_number_review(match, number, digest, reviews.get("matches", []), candidate["date_offset_days"])
        if ordinal_review is None:
            issues.append({"event_id": "", "reason": "match_number_conflict", "detail": f"supplied={match['match_number']} external={number}"})
    return {"candidate": candidate, "patched": patched, "used": used, "retired": retired,
            "identities": rows, "proposed": proposed, "issues": issues, "checks": checks,
            "accepted": not issues and checks["score_pass"], "ordinal_review": ordinal_review}


def choose_candidate(evaluated):
    accepted = [e for e in evaluated if e["accepted"]]
    if len(accepted) == 1:
        return accepted[0], False
    # Rejected candidates remain diagnostic only. Choosing the closest to display
    # is not acceptance; retain every alternative in candidate_audit.csv.
    return evaluated[0], len(accepted) > 1


def run_full(root):
    source = root / "6af3166e7b922_data_pack"
    original = fingerprints(source)
    config = json.loads((root / "configs/analysis_preregistration.json").read_text())
    policy = json.loads((root / "configs/reconciliation_policy.json").read_text())
    if config["data_cutoff_inclusive"] != CUTOFF:
        raise ValueError("Cutoff changed")
    _, matches, events, _, _ = load(root, CUTOFF)
    out = root / "reports/full_reconciliation_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    index = index_archives(root)
    reviews, aliases = load_reviews(root, register_aliases(root))
    groups = {mid: group.sort_values(["innings", "innings_ball_num"]).to_dict("records") for mid, group in events.groupby("match_id")}
    results, corrections, failures, identities, states, applied, candidate_audit, ordinal_reviews = [], [], [], [], [], [], [], []
    with ExitStack() as stack:
        archives = {Path(url).name: stack.enter_context(ZipFile(root / "data/external/cricsheet" / Path(url).name)) for url in ARCHIVES.values()}
        for ordinal, match in enumerate(matches.to_dict("records"), 1):
            mid = match["match_id"]
            raw = groups.get(mid, [])
            primary = match["family"] in ("IPL", "T20I")
            result = {k: match[k] for k in ("match_id", "match_date", "year", "family", "comp_id", "comp_name", "home_team", "away_team")}
            result.update(supplied_events=len(raw), primary_normal_events=sum(r["innings"] <= 2 for r in raw) if primary else 0,
                has_deliveries=bool(raw), primary_scope=primary, matched=False, alignment_pass=False, score_pass=False,
                accepted=False, accepted_events=0, score_reason="", member="", candidate_count=0)
            if not raw or not primary:
                result["status"] = "no_supplied_deliveries" if not raw else "outside_primary_scope"
                results.append(result)
                continue
            candidates = nearby_candidates(match, index, policy["match_date_candidate_tolerance_days"])
            exact = candidates.loc[candidates.date_offset_days.eq(0)]
            result.update(candidate_count=len(candidates), exact_date_candidates=len(exact), matched=not candidates.empty)
            if candidates.empty:
                result["status"] = "missing_external_match"
                results.append(result)
                continue
            evaluated = []
            for candidate in candidates.to_dict("records"):
                evaluation = evaluate_candidate(raw, match, candidate,
                    archives[candidate["archive"]].read(candidate["member"]), aliases, reviews)
                evaluated.append(evaluation)
                candidate_audit.append({"match_id": mid, "member": candidate["member"], "external_date": candidate["date"],
                    "date_offset_days": candidate["date_offset_days"], "source_sha256": candidate["member_sha256"],
                    "alignment_failure_count": len(evaluation["issues"]), "candidate_pass": evaluation["accepted"],
                    "score_reason": evaluation["checks"]["score_reason"],
                    "alignment_reasons": "|".join(sorted({i["reason"] for i in evaluation["issues"]}))})
            selected, ambiguous = choose_candidate(evaluated)
            if selected["ordinal_review"] is not None:
                ordinal_reviews.append(selected["ordinal_review"])
            candidate = selected["candidate"]
            patched, used, retired = selected["patched"], selected["used"], selected["retired"]
            digest = candidate["member_sha256"]
            applied.extend({"match_id": mid, **entry} for entry in used)
            identities.extend(selected["identities"])
            proposed, issues, checks = selected["proposed"], selected["issues"], selected["checks"]
            result.update(checks)
            result.update(member=candidate["member"], source_member_sha256=digest,
                external_date=candidate["date"], date_offset_days=candidate["date_offset_days"],
                alignment_pass=not issues, alignment_failure_count=len(issues),
                accepted=selected["accepted"] and not ambiguous, reviewed_events=len(used))
            result["status"] = "ambiguous_external_match" if ambiguous else ("accepted" if result["accepted"] else "quarantined")
            result["accepted_events"] = len(raw) if result["accepted"] else 0
            results.append(result)
            failures.extend({"match_id": mid, **issue} for issue in issues)
            raw_lookup = {r["event_id"]: r for r in raw}
            for c in proposed:
                prior = raw_lookup[c["event_id"]]
                c.update(alignment_input_runs=c["recorded_runs"], alignment_input_extras=c["recorded_extras_category"],
                    recorded_runs=prior["recorded_runs"], recorded_extras_category=prior["extras_type"],
                    match_accepted=result["accepted"], source_member=candidate["member"],
                    source_archive=candidate["archive"], source_sha256=digest,
                    reviewed_retirement=c["event_id"] in retired)
            corrections.extend(proposed)
            if result["accepted"]:
                states.extend(verified_states(patched, proposed, config))
            if ordinal % 100 == 0:
                print(f"Checked {ordinal}/{len(matches)} matches", flush=True)
    result_frame = pd.DataFrame(results)
    duplicate_members = result_frame.loc[result_frame.accepted, "member"].value_counts().loc[lambda s: s > 1].index
    result_frame.loc[result_frame.member.isin(duplicate_members), ["accepted", "accepted_events", "status"]] = [False, 0, "duplicate_external_match"]
    identity_frame = pd.DataFrame(identities)
    resolved = identity_frame.loc[identity_frame.identity_resolved]
    bad_ids = resolved.groupby("player_id").public_person_id.nunique().loc[lambda s: s > 1].index
    # A duplicated supplied identity for one person also requires entity resolution.
    bad_people = resolved.groupby("public_person_id").player_id.nunique().loc[lambda s: s > 1].index
    conflicts = resolved.loc[resolved.player_id.isin(bad_ids) | resolved.public_person_id.isin(bad_people)]
    conflict_matches = set(conflicts.match_id)
    affected = result_frame.match_id.isin(conflict_matches)
    result_frame.loc[affected, ["accepted", "accepted_events", "status"]] = [False, 0, "global_identity_conflict"]
    accepted_ids = set(result_frame.loc[result_frame.accepted, "match_id"])
    correction_frame = pd.DataFrame(corrections)
    correction_frame["match_accepted"] = correction_frame.match_id.isin(accepted_ids)
    verified = correction_frame.loc[correction_frame.match_accepted].copy()
    state_frame = pd.DataFrame(states)
    state_frame = state_frame.loc[state_frame.match_id.isin(accepted_ids)].rename(columns={"score_verified_pilot": "score_verified"})
    frames = {"matches": result_frame, "alignment_failures": pd.DataFrame(failures), "candidate_audit": pd.DataFrame(candidate_audit),
        "player_crosswalk": identity_frame, "global_identity_conflicts": conflicts,
        "applied_reviews": pd.DataFrame(applied), "reviewed_match_ordinals": pd.DataFrame(ordinal_reviews),
        "unresolved_identities": identity_frame.loc[~identity_frame.identity_resolved],
        "coverage_by_year_family": coverage_summary(result_frame, ["year", "family"]),
        "coverage_by_competition": coverage_summary(result_frame, ["year", "family", "comp_id", "comp_name"])}
    # Preserve pilot history and record every selected match's new disposition.
    pilot = pd.read_csv(root / "reports/reconciliation_pilot_2026-11-01/matches.csv", dtype={"match_id": str})
    frames["pilot_review_dispositions"] = pilot[["match_id", "status", "accepted"]].rename(
        columns={"status": "original_status", "accepted": "original_accepted"}).merge(
        result_frame[["match_id", "status", "accepted", "alignment_pass", "score_reason"]], on="match_id", validate="one_to_one")
    for name, frame in frames.items():
        frame.to_csv(out / f"{name}.csv", index=False)
    correction_frame.to_parquet(out / "candidate_corrections.parquet", index=False)
    verified.to_parquet(out / "verified_corrections.parquet", index=False)
    state_frame.to_parquet(out / "verified_preball_states.parquet", index=False)
    # Complete verified event table for diagnostics; current outcomes are kept out of feature allowlists.
    joined = events.merge(verified.drop(columns=["recorded_runs", "source_row", "innings", "innings_ball_num"]),
                          on=["event_id", "match_id"], validate="one_to_one", how="inner")
    joined = joined.merge(state_frame.drop(columns=["innings"]), on=["event_id", "match_id"], validate="one_to_one")
    joined.to_parquet(out / "verified_events.parquet", index=False)
    primary = result_frame.loc[result_frame.primary_scope]
    reasons = result_frame.groupby(["family", "status"], as_index=False).agg(matches=("match_id", "size"), events=("supplied_events", "sum"))
    reasons.to_csv(out / "dispositions.csv", index=False)
    text = ["# Full-dataset reconciliation and exception dispositions", "",
        f"Audited {len(result_frame)} supplied matches and {len(events):,} events through {CUTOFF}. "
        f"Primary IPL/T20I: {len(primary)} matches, {primary.supplied_events.sum():,} events. "
        f"Accepted: {len(accepted_ids)} complete matches, {len(verified):,} events.", "",
        "All supplied matches are accounted for, including abandoned matches without deliveries and Other T20 outside the registered primary scope. Match retention uses matches with deliveries; event retention uses all supplied events in each row. Super-over rows remain in the denominator and are excluded from verified ordinary innings.", "",
        "Candidate search includes the exact date and one day either side, with both supplied and public dates respecting the cutoff. A shifted date requires exactly one candidate passing complete delivery, actor, result and available match-number checks. No supplied date is rewritten. All candidates, including misleading exact-date candidates, are recorded in candidate_audit.csv; accepted source members must be unique across supplied matches.", "",
        f"Reviewed numbering-convention differences: {len(ordinal_reviews)}. These are explicit source-hashed exceptions for exact-date IPL 2025 matches with agreeing full ledgers. Official IPL announcements preserve original fixture numbers after rescheduling while source ordinals can follow chronology. Both labels are retained; no raw date, result or model feature is modified. Details: reviewed_match_ordinals.csv.", "",
        markdown_table(frames["coverage_by_year_family"].round(2)), "", markdown_table(reasons), "",
        "## Pilot exceptions", "", markdown_table(frames["pilot_review_dispositions"]), "",
        f"Loaded {len(reviews['aliases'])} reviewed identity aliases and applied {len(applied)} event reviews. The private review ledger records original/adopted values, rationales, evidence URLs and source hashes. Retired-hurt exceptions preserve zero wickets only when the event names a verified participant and the complete sequence agrees. These are source-adjudicated repairs, not claims that two independent ball feeds agree.", "",
        "Rain/shortened matches retain their exclusion because target/allotted-ball timing is unverified. Missing external matches remain a coverage limitation; no guessed extras or replacement samples are used. New full-corpus disagreements are listed individually and not automatically repaired using pilot exceptions.", "",
        "## Identity consistency", "",
        f"{len(conflicts)} identity observations across {len(conflict_matches)} matches require global identity review. Any supplied ID linked to multiple external people, or public person linked to multiple supplied IDs, quarantines all involved matches. No player is merged silently.", "",
        "## Next diagnostic", "",
        "Run pressure-validate to measure player retention, pressure coverage, context overlap and whole-match uncertainty. No predictive models or player rankings are fitted here. Pilot and EDA outputs remain unchanged. All raw inputs are fingerprinted; source snapshots were retrieved after the match-date cutoff and are not publication-time archives.", "",
        "Data attribution: [Cricsheet](https://cricsheet.org/), [People Register](https://cricsheet.org/register/), [ODC Attribution License 1.0](https://opendatacommons.org/licenses/by/1-0/). Review evidence is linked in data/curated/reconciliation_reviews.json. All data and reports stay outside the public repository.", ""]
    (out / "REPORT.md").write_text("\n".join(text))
    if fingerprints(source) != original:
        raise ValueError("Raw inputs changed")
    write_manifest(root, out, original, {"primary_match_count": len(primary), "accepted_matches": len(accepted_ids),
        "accepted_events": len(verified), "global_mode_a_ready": False, "review_required_before_modeling": True})
    print(json.dumps({"supplied_matches": len(matches), "accepted_matches": len(accepted_ids),
        "accepted_events": len(verified), "identity_conflict_matches": len(conflict_matches)}, indent=2))
    return out
