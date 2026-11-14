"""Role evidence, deterministic match examples and explicit counterexample review."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import save_json, sha256, unique
from .player_evidence import KEY, summarize, supported_comparisons


PHASES = ["01-06", "07-15", "16-20"]


def markdown_table(frame):
    def cell(value):
        return "" if pd.isna(value) else str(value).replace("|", ";")
    return "\n".join(["| " + " | ".join(map(str, frame.columns)) + " |",
        "| " + " | ".join(["---"] * len(frame.columns)) + " |"] +
        ["| " + " | ".join(cell(value) for value in row) + " |" for row in frame.itertuples(index=False, name=None)])


def fmt(value, digits=3):
    return "unavailable" if pd.isna(value) else f"{value:.{digits}f}"


def attach_opposition(root, ledger):
    columns = ["match_id", "home_team_id", "home_team", "away_team_id", "away_team", "venue_country"]
    matches = pd.read_csv(root / "6af3166e7b922_data_pack/matches.csv", usecols=columns, dtype=str, keep_default_na=False)
    unique(matches, ["match_id"], "dossier match metadata")
    result = ledger.merge(matches, on="match_id", how="left", validate="many_to_one")
    own_id = np.where(result.role.eq("batting"), result.batting_team_id, result.bowling_team_id)
    other_id = np.where(result.role.eq("batting"), result.bowling_team_id, result.batting_team_id)
    for ids in [own_id, other_id]:
        if not ((ids == result.home_team_id) | (ids == result.away_team_id)).all():
            raise ValueError("Dossier team identity does not match supplied match metadata")
    result["opposition"] = np.where(other_id == result.home_team_id, result.home_team, result.away_team)
    return result.drop(columns=["home_team_id", "home_team", "away_team_id", "away_team"])


def choose_cases(matches, minimum):
    """Frozen extreme/typical protocol. No composite or reputation selection."""
    if matches.empty:
        return matches.assign(case_reasons=pd.Series(dtype=str), small_sample=pd.Series(dtype=bool))
    candidates = matches.loc[matches.opportunities.ge(minimum)].copy()
    if candidates.empty:
        result = matches.sort_values(["opportunities", "match_date", "match_id"], ascending=[False, True, True]).head(1).copy()
        return result.assign(case_reasons="highest_exposure_small_sample", small_sample=True)
    reasons = {}
    for column, label in [("runs_per_100", "run_rate"), ("wickets_per_100", "wicket_rate")]:
        for ascending, name in [(False, "maximum_"), (True, "minimum_")]:
            row = candidates.sort_values([column, "opportunities", "match_date", "match_id"], ascending=[ascending, False, True, True]).iloc[0]
            reasons.setdefault(row.match_id, []).append(name + label)
    ordered = candidates.sort_values(["runs_per_100", "match_date", "match_id"])
    median = ordered.loc[ordered.opportunities.cumsum().ge(ordered.opportunities.sum() / 2)].iloc[0].runs_per_100
    typical = candidates.assign(_distance=(candidates.runs_per_100 - median).abs()).sort_values(
        ["_distance", "opportunities", "match_date", "match_id"], ascending=[True, False, True, True]).iloc[0]
    reasons.setdefault(typical.match_id, []).append("typical_run_rate")
    result = candidates.loc[candidates.match_id.isin(reasons)].copy()
    result["case_reasons"] = result.match_id.map(lambda match: ";".join(reasons[match]))
    return result.assign(small_sample=False).sort_values(["match_date", "match_id"])


def case_details(events, cases):
    rows, traces = [], []
    for row in cases.itertuples():
        g = events.loc[events.match_id.eq(row.match_id)].copy()
        g["_ordinal"] = g.event_id.str.rsplit(":", n=1).str[-1].astype(int)
        g = g.sort_values(["innings", "_ordinal"])
        first = g.iloc[0]
        record = row._asdict()
        record.pop("Index", None)
        record.update(opposition=first.opposition, phases="/".join(sorted(g.phase.unique())),
            pressure_reasons="/".join(flag for flag in ["late", "collapse", "tight_chase"] if g[flag].any()),
            first_event_id=first.event_id, first_over=int(first.overid), score_before=int(first.score_before),
            wickets_before=int(first.wickets_before), balls_remaining=int(first.balls_remaining),
            runs_required=first.runs_required, required_run_rate=first.required_run_rate)
        rows.append(record)
        traces.append(g[["role", "player_id", "match_id", "event_id", "source_pointer", "source_member", "runs", "wickets",
            "phase", "score_before", "wickets_before", "balls_remaining", "runs_required", "required_run_rate",
            "late", "collapse", "tight_chase"]])
    return pd.DataFrame(rows), pd.concat(traces, ignore_index=True) if traces else pd.DataFrame()


def alternatives(default, phase_profiles):
    rows = []
    for role, pool in default.loc[default.selection_ready].groupby("role", sort=True):
        outside = pool.loc[pool["rank"].gt(10)].sort_values("rank")
        profiles = phase_profiles.loc[phase_profiles.role.eq(role) & phase_profiles.pressure_full].pivot(
            index="player_id", columns="phase", values="opportunities").reindex(columns=PHASES, fill_value=0).fillna(0)
        profiles = profiles.div(profiles.sum(axis=1), axis=0)
        for player in pool.loc[pool["rank"].le(10)].player_id:
            distance = (profiles.reindex(outside.player_id) - profiles.loc[player]).abs().sum(axis=1)
            similar = outside.assign(role_distance=outside.player_id.map(distance)).sort_values(["role_distance", "rank", "player_id"]).head(3)
            nominated = set(outside.head(3).player_id) | set(similar.player_id)
            for other in outside.loc[outside.player_id.isin(nominated)].itertuples():
                rows.append(dict(role=role, player_id=player, alternative_id=other.player_id,
                    alternative_rank=int(other.rank), role_distance=float(distance.loc[other.player_id]),
                    boundary_alternative=other.player_id in set(outside.head(3).player_id),
                    role_similar_alternative=other.player_id in set(similar.player_id)))
    return pd.DataFrame(rows, columns=KEY + ["alternative_id", "alternative_rank", "role_distance", "boundary_alternative", "role_similar_alternative"])


def build_dossiers(root, ledger, cohort, results, out, label, provenance):
    out.mkdir(parents=True, exist_ok=True)
    policy = json.loads((root / "configs/player_evidence_v1.json").read_text())["case_display"]
    ledger = attach_opposition(root, ledger)
    default = results["ratings"].loc[results["ratings"].variant.eq("default_60_40")].copy()
    profiles = summarize(ledger, KEY + ["phase", "pressure_full"])
    observed = summarize(ledger, KEY + ["pressure_full"])
    seasons = summarize(ledger, KEY + ["year", "pressure_full"])
    context = summarize(ledger, KEY + ["family", "year", "innings", "phase", "wicket_band", "pressure_full", "supported"])
    comparisons, _ = supported_comparisons(context, cohort)
    match_ledger = summarize(ledger, KEY + ["match_id", "match_date", "family", "year", "innings", "pressure_full"])
    matchup = alternatives(default, profiles)
    names = cohort.set_index(KEY).player_name.to_dict()
    grouped = {key: g for key, g in ledger.groupby(KEY, sort=True)}
    eligible = results["eligibility"].loc[results["eligibility"].level_sample_eligible].copy()
    cards, case_rows, event_rows, review_rows = [], [], [], []
    for actor in eligible.sort_values(["role", "player_name", "player_id"]).itertuples():
        key = (actor.role, actor.player_id)
        g = grouped[key]
        p = g.loc[g.pressure_full]
        rank = default.loc[default.role.eq(actor.role) & default.player_id.eq(actor.player_id)].iloc[0]
        own_matches = match_ledger.loc[match_ledger.role.eq(actor.role) & match_ledger.player_id.eq(actor.player_id) & match_ledger.pressure_full]
        minimum = policy["batting_minimum_pressure_opportunities" if actor.role == "batting" else "bowling_minimum_pressure_attempts"]
        selected = choose_cases(own_matches, minimum)
        examples, traces = case_details(p, selected)
        case_rows.append(examples)
        event_rows.append(traces)
        prof = profiles.loc[profiles.role.eq(actor.role) & profiles.player_id.eq(actor.player_id)]
        phase = prof.loc[prof.pressure_full].copy()
        phase["pressure_share_percent"] = 100 * phase.opportunities / phase.opportunities.sum()
        main = phase.sort_values(["opportunities", "phase"], ascending=[False, True]).iloc[0]
        workload = prof.groupby("phase", as_index=False).opportunities.sum()
        workload["share_percent"] = 100 * workload.opportunities / workload.opportunities.sum()
        usual_role = workload.sort_values(["opportunities", "phase"], ascending=[False, True]).iloc[0]
        own_observed = observed.loc[observed.role.eq(actor.role) & observed.player_id.eq(actor.player_id)]
        observed_ci = results.get("observed_uncertainty", pd.DataFrame())
        if len(observed_ci):
            observed_ci = observed_ci.loc[observed_ci.role.eq(actor.role) & observed_ci.player_id.eq(actor.player_id)]
        season = seasons.loc[seasons.role.eq(actor.role) & seasons.player_id.eq(actor.player_id) & seasons.pressure_full]
        family = results["family_diagnostics"].loc[results["family_diagnostics"].role.eq(actor.role) & results["family_diagnostics"].player_id.eq(actor.player_id)]
        influence = results["influence"].loc[results["influence"].role.eq(actor.role) & results["influence"].player_id.eq(actor.player_id)]
        deleted = influence.loc[influence.deletion.eq("match") & influence.own_pressure_match].copy()
        worst_removed = deleted.sort_values(["point", "removed"]).head(1)
        season_drop = influence.loc[influence.deletion.eq("season")]
        change = results["supported_change"]
        change = change.loc[change.role.eq(actor.role) & change.player_id.eq(actor.player_id)] if len(change) else change
        reliable_change = bool(len(change) and change.interval_reliable.iloc[0])
        comp = comparisons.loc[comparisons.role.eq(actor.role) & comparisons.player_id.eq(actor.player_id)].iloc[0]
        variants = results["ratings"].loc[results["ratings"].role.eq(actor.role) & results["ratings"].player_id.eq(actor.player_id)]
        bad_run_reason = "minimum_run_rate" if actor.role == "batting" else "maximum_run_rate"
        bad_wicket_reason = "maximum_wicket_rate" if actor.role == "batting" else "minimum_wicket_rate"
        bad_run = examples.loc[examples.case_reasons.str.contains(bad_run_reason)]
        bad_wicket = examples.loc[examples.case_reasons.str.contains(bad_wicket_reason)]
        review = dict(role=actor.role, player_id=actor.player_id, player_name=actor.player_name,
            primary_rank=rank["rank"], selection_ready=bool(rank.selection_ready), dominant_pressure_phase=main.phase,
            dominant_workload_phase=usual_role.phase, dominant_workload_share=float(usual_role.share_percent),
            dominant_phase_share=float(main.pressure_share_percent), source_retention=float(actor.retained_fraction),
            reliable_usual_comparison=reliable_change, family_count=int(family.family.nunique()),
            adverse_run_match=bad_run.match_id.iloc[0] if len(bad_run) else "",
            adverse_wicket_match=bad_wicket.match_id.iloc[0] if len(bad_wicket) else "",
            adequate_case_display=bool(len(examples) and not examples.small_sample.any()),
            season_deletions_inadequate=int(season_drop.remaining_sample_adequate.eq(False).sum()),
            variant_rank_min=float(variants["rank"].min()), variant_rank_max=float(variants["rank"].max()),
            evidence_check_status="automated_traceable_counterexample_review",
            priority_review=bool(rank.selection_ready and ((rank["rank"] <= 13) or variants["rank"].le(10).any())))
        review_rows.append(review)
        lines = [f"# {actor.player_name} — {actor.role}", "", f"Stable player ID: `{actor.player_id}`. Evidence window: **{label}**.", "",
            f"Primary ordering position: {int(rank['rank']) if rank.selection_ready else 'withheld'}; selection statistic {fmt(rank.selection_score)}; point {fmt(rank.point)}; 10th–90th interval [{fmt(rank.p10)}, {fmt(rank.p90)}]; valid draws {rank.finite_fraction:.1%}.",
            f"Source retention {actor.retained_fraction:.1%} ({int(actor.retained_events)}/{int(actor.source_events)} opportunities). Pressure: {len(p)} opportunities / {p.match_id.nunique()} matches; effective count {actor.pressure_effective_events:.1f}. Pressure-peer retention {actor.peer_pressure_count_retention:.1%} by count / {actor.peer_pressure_weight_retention:.1%} by mass.",
            f"Primary blocked reasons: {actor.primary_blocked_reasons or 'none'}. Shared names/aliases are labels; stable IDs remain separate.", "",
            "## Observed task and performance", "",
            f"Largest overall workload: overs {usual_role.phase}, {usual_role.share_percent:.1f}% of all opportunities. The pressure subset can have a different phase mix; neither is a claim of an assigned tactical role.", "",
            markdown_table(workload.round(3)), "",
            f"Largest observed pressure workload: overs {main.phase}, {main.pressure_share_percent:.1f}% of pressure opportunities. This describes exposure; it is not an invented tactical assignment.", "",
            markdown_table(own_observed[["pressure_full", "opportunities", "matches", "runs", "wickets", "runs_per_100", "wickets_per_100", "weighted_runs_per_100", "weighted_wickets_per_100"]].round(3)), "",
            "Rates are per 100 analytical opportunities. Batting excludes wides and includes no-balls; wickets are attributed striker dismissals. Bowling uses every attempt and excludes byes/leg-byes/penalties from concession. More batting runs/fewer dismissals and fewer bowling runs/more wickets are favourable; interpret both outcomes together.", "",
            markdown_table(observed_ci[["estimand", "metric", "p10", "p90", "finite_fraction", "interval_reliable"]].round(4)) if len(observed_ci) else "Observed rate intervals are unavailable in this view.", "",
            markdown_table(phase[["phase", "opportunities", "matches", "pressure_share_percent", "weighted_runs_per_100", "weighted_wickets_per_100"]].round(3)), "",
            "Pressure reasons overlap: " + "; ".join(f"{flag} {int(p[flag].sum())}" for flag in ["late", "collapse", "tight_chase"]) + ". These counts must not be added.", "",
            "## Repeatability and context", "",
            markdown_table(season[["year", "opportunities", "matches", "runs", "wickets", "weighted_runs_per_100", "weighted_wickets_per_100"]].round(3)), "",
            markdown_table(family[["family", "pressure_events", "pressure_matches", "point", "p10", "p90", "finite_fraction", "interval_reliable"]].round(4)), "",
            "Family estimates are diagnostics, not proof that T20I dominance transfers to IPL. Opposition strength, venue and fine chase difficulty remain incompletely measured.", "",
            f"After deleting any one own pressure match, point estimate ranges from {fmt(deleted.point.min())} to {fmt(deleted.point.max())}. The lowest remaining point removes match `{worst_removed.removed.iloc[0] if len(worst_removed) else 'unavailable'}`. These are point sensitivities, not fresh bootstrap selection scores.", "",
            markdown_table(season_drop[["removed", "point", "remaining_effective_events", "remaining_sample_adequate"]].round(4)), "",
            "## Usual-performance evidence", "",
            f"Supported ordinary comparison covers {comp.supported_pressure_fraction:.1%} of pressure opportunities ({int(comp.supported_pressure_events)} pressure / {int(comp.supported_ordinary_events)} ordinary). Same-player/year cells are fixed; ordinary late-over controls are absent.",
            f"Change sample eligible: {bool(comp.change_sample_eligible)}; reliable change interval: {reliable_change}. Unsupported/unreliable change stays unavailable for decision ordering. All-ordinary rates above are background, not a causal pressure comparison.", "",
            markdown_table(pd.DataFrame([dict(runs_difference_per_100=comp.runs_difference_per_100,
                wickets_difference_per_100=comp.wickets_difference_per_100, reliable_for_decisions=reliable_change)]).round(4)), "",
            "## Supporting cases and counterexamples", "",
            "Cases follow the frozen high/low run rate, high/low wicket rate and typical-run-rate protocol. Small samples are labelled; selected extrema do not establish a player-wide weakness or match-winning credit.", "",
            markdown_table(examples[["match_id", "match_date", "family", "opposition", "phases", "opportunities", "runs", "wickets", "runs_per_100", "wickets_per_100", "case_reasons", "small_sample"]].round(3)), "",
            f"Adverse run-rate illustration: `{review['adverse_run_match'] or 'not established from adequate match cases'}`. Adverse wicket-rate illustration: `{review['adverse_wicket_match'] or 'not established from adequate match cases'}`. Read both metrics: the same match can support scoring tempo and challenge preservation, or support control and challenge wicket-taking.",
            "First observed pressure state for each case (pre-ball, not the match result):", "",
            markdown_table(examples[["match_id", "first_event_id", "first_over", "score_before", "wickets_before", "balls_remaining", "runs_required", "required_run_rate", "pressure_reasons"]].round(3)), "",
            "## Ordering, alternatives and limitations", "",
            markdown_table(variants[["variant", "rank", "point", "selection_score", "finite_fraction"]].round(4)), "",
            "The primary order uses the registered 60/40 runs/wickets lower-quantile rule. Weight variants are disclosed; reputation and narratives do not override it."]
        alt = matchup.loc[matchup.role.eq(actor.role) & matchup.player_id.eq(actor.player_id)].copy()
        if len(alt):
            alt["alternative_name"] = alt.alternative_id.map(lambda x: names.get((actor.role, x), x))
            lines += ["", markdown_table(alt[["alternative_id", "alternative_name", "alternative_rank", "role_distance", "boundary_alternative", "role_similar_alternative"]].round(3)), "",
                "Alternatives include the first three excluded ranks and the three closest observed phase profiles. The declared conservative score determines the ordering; role distance is a review aid, not a selection quota or score adjustment."]
        lines += ["", "Evidence limitations: missing source matches are not evidence of weakness; sparse contexts are not established weaknesses; four/six-run events are not automatically verified boundaries. Check exposure, family differences and adverse cases before any selection claim.", "",
            "Traceability: [complete match ledger](../../player_match_ledger.csv), [case event/source pointers](../../case_events.csv), [review register](../../counterexample_review.csv), [phase profiles](../../role_context_profiles.csv). No scout observation or human approval is claimed by the automated review status.", ""]
        path = out / "dossiers" / actor.role / f"{actor.player_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines))
        cards.append(dict(role=actor.role, player_id=actor.player_id, player_name=actor.player_name,
            primary_rank=rank["rank"], selection_ready=rank.selection_ready, dossier=str(path.relative_to(out))))
    frames = dict(index=pd.DataFrame(cards), counterexample_review=pd.DataFrame(review_rows),
        case_index=pd.concat(case_rows, ignore_index=True), case_events=pd.concat(event_rows, ignore_index=True),
        player_match_ledger=match_ledger, role_context_profiles=profiles, observed_summary=observed,
        season_summary=seasons, supported_comparisons=comparisons, alternatives=matchup)
    for name, frame in frames.items():
        frame.to_csv(out / f"{name}.csv", index=False)
    review = frames["counterexample_review"]
    # Priority affects review order only, never player eligibility or ranking.
    boundary = review.loc[review.priority_review].sort_values(["role", "primary_rank", "player_id"])
    (out / "SELECTOR_REVIEW.md").write_text("\n".join([f"# Role and counterexample review — {label}", "",
        "Every level-sample-eligible player/role has a dossier, including coverage-limited entries. Priority review includes ranks 1–13 and any registered outcome variant's top ten; this does not restrict the selection population.", "",
        markdown_table(boundary[["role", "player_id", "player_name", "primary_rank", "dominant_workload_phase", "dominant_pressure_phase", "adverse_run_match", "adverse_wicket_match", "family_count", "season_deletions_inadequate", "variant_rank_min", "variant_rank_max"]].round(3)), "",
        "Counterexample fields are factual nominated observations, not causal weakness diagnoses. Review both outcomes and complete match/season evidence. Unavailable ordinary comparison remains missing; uncertainty or source loss is not poor performance.", "",
        "The tenth-versus-exclusions question is addressed by `alternatives.csv`: boundary ranks 11–13 plus role-similar outside candidates. Fixed primary scores determine ordering; overlapping intervals mean close order should not be described as certain.", ""]))
    (out / "REPORT.md").write_text("\n".join([f"# Player evidence dossiers — {label}", "",
        f"Created {len(cards)} player-role dossiers; {int(review.selection_ready.sum())} pass the primary ranking rules. {int(review.priority_review.sum())} entries have priority for boundary/variant review.", "",
        "Every dossier includes workload context, observed pressure and ordinary outcomes, season/family/match sensitivity, supported comparison availability, balanced match examples, pre-ball state and source-event traceability.",
        "Automated evidence checks are not a claim of private scouting or a manual review. No method, threshold, weight or ordering is changed by the cases.", "",
        "Read `SELECTOR_REVIEW.md`, `index.csv` and the individual cards. Detailed player information remains private.", ""]))
    save_json(out / "manifest.json", dict(window=label, input_provenance=provenance,
        case_policy_sha256=sha256(root / "configs/player_evidence_v1.json"),
        code_sha256={"src/rr_pressure/player_dossiers.py": sha256(root / "src/rr_pressure/player_dossiers.py")},
        cards=len(cards), counterexample_protocol_executed=True, method_or_order_changed=False,
        output_sha256={str(p.relative_to(out)): sha256(p) for p in sorted(out.rglob("*")) if p.is_file() and p.name != "manifest.json"}))
    return frames


def run_development(root):
    evidence = root / "reports/player_evidence_development_2026-11-01"
    rating = root / "reports/descriptive_rating_development_2026-11-01"
    for directory in [evidence, rating]:
        manifest = json.loads((directory / "manifest.json").read_text())
        for name, digest in manifest["output_sha256"].items():
            if sha256(directory / name) != digest:
                raise ValueError("Changed development dossier input: " + name)
    ledger = pd.read_parquet(evidence / "event_role_ledger.parquet", filters=[("year", "in", [2023, 2024, 2025])])
    if not ledger.year.isin([2023, 2024, 2025]).all():
        raise ValueError("Reserved event in development dossier")
    cohort = pd.read_csv(evidence / "cohort_register.csv", dtype={"player_id": str})
    results = {name: pd.read_parquet(rating / f"{name}.parquet") for name in ["eligibility", "ratings", "family_diagnostics", "influence", "supported_change"]}
    results["observed_uncertainty"] = pd.read_parquet(evidence / "observed_uncertainty.parquet")
    return build_dossiers(root, ledger, cohort, results, root / "reports/player_dossiers_development_2026-11-01", "2023–2025 development",
        {"evidence_manifest_sha256": sha256(evidence / "manifest.json"), "rating_manifest_sha256": sha256(rating / "manifest.json")})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    run_development(parser.parse_args().root.resolve())
