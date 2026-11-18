"""Read-only, allowlisted publication export of the frozen final analysis.

Run from the project root with .venv/bin/python scripts/export_dashboard.py.
Does not fit, repair, resample, or rerank anything. Original artifacts stay private.
"""
from pathlib import Path
import hashlib
import json
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "reports/final_window_evaluation_2026-11-01"
DATA = FINAL / "final_2023_2026"
CARDS = DATA / "player_dossiers"
OUT = ROOT / "dashboard/content/generated"

# Editorial interpretations supplement the frozen numerical evidence, never ordering.
EDITORIAL = {
    "6396": ("Late-over scoring", "Sustained finishing output", "His strong late-over scoring is supported by 66 pressure matches and first place in every registered outcome mix.", "His retained 2026 exposure does not satisfy every standalone-year eligibility gate.", "A finishing option when rapid scoring must be weighed against dismissal risk."),
    "1699": ("Middle-over scoring", "Tempo through the middle", "A long pressure history combines scoring tempo with adequate standalone 2026 evidence.", "A slow, unbeaten New Zealand segment challenges the assumption that preservation alone is enough.", "Middle-over scoring with evidence of taking pressure opportunities beyond simple survival."),
    "3125": ("Middle / late-over scoring", "Finishing range", "Middle-over overall workload and late-heavy pressure exposure support his scoring and preservation tradeoff.", "Only 33 retained 2026 pressure opportunities support the current-year view; the final rank is multi-year evidence.", "Flexible scoring through the middle and closing overs, subject to the available role evidence."),
    "2756": ("Late-over scoring", "IPL specialist evidence", "Thirty-three pressure matches and a strong Kolkata segment support his scoring contribution.", "The evidence is IPL-only and two season deletions leave inadequate samples.", "A specialist scoring option whose pressure contribution can complement a middle-to-late innings task."),
    "23311": ("Middle-over scoring", "Promising, shorter history", "His positive pressure contribution holds ranks five to six across registered outcome mixes.", "Fourteen pressure matches and three inadequate season-removal samples limit repeatability claims.", "A developing scoring option to review with explicit acknowledgement of the short evidence history."),
    "1318": ("Late-over scoring", "High-impact closing overs", "A late-heavy workload across 39 pressure matches combines strong scoring with visible dismissal risk.", "No retained 2026 pressure observations exist; the narrow lead over the next entry does not establish current form.", "A historical finishing profile for tasks where acceleration matters, with availability assessed separately."),
    "6726": ("Late-over scoring", "Finishing upside and downside", "Late-heavy exposure across 46 pressure matches includes strong Delhi finishing evidence.", "A 2026 Mumbai counterexample and incomplete season-deletion evidence qualify that upside.", "Late-innings scoring capacity with the risk of low-output pressure segments kept visible."),
    "7897": ("Middle / late-over scoring", "Preservation with tempo", "Seventy-one pressure matches and adequate 2026 evidence support a low-dismissal scoring profile.", "Ranks five to fifteen across outcome mixes show how strongly the run/wicket preference matters.", "A middle-to-late innings option that brings preservation evidence alongside scoring."),
    "3647": ("Middle-over scoring", "A stable weight comparison", "Forty-three retained pressure matches (42 peer-supported), adequate 2026 evidence and ninth place under all outcome mixes support his position.", "Cases challenge both scoring tempo and preservation; weight stability does not remove overlapping intervals.", "A middle-over scoring option assessed through tempo and wicket preservation together."),
    "4391": ("Middle / late-over scoring", "A close tenth-place call", "Middle-over total workload and a late-heavy pressure subset support a positive multi-year contribution.", "Only eleven retained 2026 pressure opportunities exist and the lower interval narrowly leads the next candidate.", "A flexible scoring profile whose inclusion remains a close, uncertainty-qualified boundary decision."),
    "781": ("Middle-over control", "Control over a sustained sample", "Forty IPL pressure matches, adequate 2026 evidence and first place under all outcome mixes support the control case.", "There is no T20I corroboration here; a wicketless segment must be interpreted alongside runs conceded.", "Middle-over control supported by retained IPL evidence, with wicket-taking examined alongside concessions."),
    "2933": ("Powerplay / death bowling", "Control and wickets together", "Fifty-one pressure matches and adequate 2026 evidence support both concession control and wicket contribution.", "A recent New Zealand segment provides adverse evidence; the index rank is not a universal ability judgement.", "A pressure-bowling option spanning the opening and closing tasks observed in the data."),
    "4373": ("Late-over bowling", "Closing-over contribution", "Late-heavy pressure workload across 42 matches supports the concession/wicket balance.", "Only nineteen retained 2026 pressure attempts exist, and an expensive Lucknow case challenges control.", "A closing-over option supported primarily by the multi-year evidence."),
    "5837": ("Middle-over bowling", "A context-dependent control case", "Twenty-three T20I pressure matches support a positive middle-over relative contribution.", "No IPL corroboration exists; thirty retained 2026 pressure attempts are insufficient for the full one-year rules.", "A middle-over profile for further cricket review, without assuming T20I performance transfers directly to IPL."),
    "6354": ("Powerplay / late-over bowling", "A positive, shorter sample", "Powerplay-heavy total workload and late-heavy pressure exposure produce a favourable contribution across sixteen pressure matches.", "An expensive West Indies case and an inadequate season deletion limit the repeatability claim.", "An opening-to-closing bowling option whose shorter pressure history warrants care."),
    "35318": ("Pressure bowling", "Recent evidence, short history", "The retained IPL history passes the standalone 2026 rules and includes strong concession-control evidence.", "Ten pressure matches sit near the minimum; one qualifying season is not long-term repeatability.", "A recent pressure-bowling option for further evaluation with a short-history qualification."),
    "6256": ("Middle-over bowling", "Breadth of pressure evidence", "Sixty-eight pressure matches, both competition families and adequate 2026 evidence support the case.", "The best UAE control example does not measure opposition strength; an expensive Hyderabad segment is counterevidence.", "A middle-over option supported by a broad pressure history, with context limitations retained."),
    "7327": ("Middle / late-over bowling", "Wickets with concession risk", "Seventeen pressure matches provide evidence of wicket contribution alongside an observed middle-to-late workload.", "The rank varies from four to eleven; 108 retained 2026 attempts do not satisfy every standalone gate.", "A wicket-contributing pressure option whose conceded runs must be considered in the same decision."),
    "6284": ("Middle-over bowling", "A short-history specialist", "The IPL middle-over evidence supports a positive contribution within the frozen combined-window rules.", "Eleven pressure matches, two inadequate season deletions and 47 retained 2026 attempts limit confidence in repeatability.", "A specialist middle-over control profile with clearly bounded evidence."),
    "23": ("Middle-over bowling", "A qualified historical selection", "Eighteen IPL pressure matches support a positive historical control contribution.", "No retained 2026 pressure evidence exists; the narrow lead over the next candidate overlaps substantially in uncertainty.", "A historical middle-over control profile; current form and future availability remain separate questions."),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        value = value.item()
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return None
    return value


def records(frame, columns):
    return clean(frame[columns].to_dict("records"))


def run():
    protocol = json.loads((ROOT / "configs/final_window_v1.json").read_text())
    for name, sha in protocol["frozen_sha256"].items():
        assert digest(ROOT / name) == sha, f"Frozen dependency changed: {name}"
    receipt = json.loads((FINAL / "manifest.json").read_text())
    for name, sha in receipt["output_sha256"].items():
        path = ROOT / name if (ROOT / name).exists() else FINAL / name
        assert digest(path) == sha, f"Final evidence changed: {name}"

    def csv(name):
        return pd.read_csv(CARDS / name, dtype={"player_id": str, "alternative_id": str})

    top = pd.read_csv(FINAL / "two_top_ten_lists.csv", dtype={"player_id": str})
    alternatives = csv("alternatives.csv")
    selected = set(zip(top.role, top.player_id))
    keys = selected | set(zip(alternatives.role, alternatives.alternative_id))
    assert len(selected) == 20 and len(keys) == 69
    eligibility = pd.read_parquet(DATA / "eligibility.parquet")
    ratings = pd.read_parquet(DATA / "ratings.parquet")
    families = pd.read_parquet(DATA / "family_diagnostics.parquet")
    influence = pd.read_parquet(DATA / "influence.parquet")
    reserved_elig = pd.read_parquet(FINAL / "reserved_2026/eligibility.parquet")
    reserved_ratings = pd.read_parquet(FINAL / "reserved_2026/ratings.parquet")
    review = csv("counterexample_review.csv")
    observed = csv("observed_summary.csv")
    phases = csv("role_context_profiles.csv")
    seasons = csv("season_summary.csv")
    support = csv("supported_comparisons.csv")
    cases = csv("case_index.csv")
    expert = (FINAL / "FINAL_AGENT_REVIEW.md").read_text()

    def part(table, role, pid):
        return table.loc[table.role.eq(role) & table.player_id.eq(pid)]

    players = []
    for role, pid in sorted(keys):
        e = part(eligibility, role, pid).iloc[0]
        r = part(ratings, role, pid)
        primary = r.loc[r.variant.eq("default_60_40")].iloc[0]
        rv = part(review, role, pid).iloc[0]
        obs = part(observed, role, pid)
        inf = part(influence, role, pid)
        match_inf = inf.loc[inf.deletion.eq("match") & inf.own_pressure_match.eq(True)]
        reserved_entry = part(reserved_elig, role, pid)
        rr = part(reserved_ratings, role, pid)
        rr = rr.loc[rr.variant.eq("default_60_40")]
        recent_events = int(reserved_entry.iloc[0].pressure_events) if len(reserved_entry) else 0
        recent_matches = int(reserved_entry.iloc[0].pressure_matches) if len(reserved_entry) else 0
        adequate = bool(len(rr) and rr.iloc[0].selection_ready)
        recent = "adequate" if adequate else "no_retained_pressure" if not recent_events else "limited"
        s = part(support, role, pid).iloc[0]
        phase_data = part(phases, role, pid)
        workload = phase_data.groupby("phase", as_index=False).opportunities.sum()
        workload["share"] = workload.opportunities / workload.opportunities.sum() * 100
        pressure_phases = phase_data.loc[phase_data.pressure_full.eq(True)].copy()
        pressure_phases["share"] = pressure_phases.opportunities / pressure_phases.opportunities.sum() * 100
        player_cases = part(cases, role, pid)
        # Case aggregates only; no delivery rows, source pointers or event IDs.
        case_columns = ["match_id", "match_date", "family", "opposition", "phases", "opportunities", "runs", "wickets", "runs_per_100", "wickets_per_100", "case_reasons", "small_sample", "first_over", "score_before", "wickets_before", "balls_remaining", "runs_required", "required_run_rate"]
        full_review = None
        match = re.search(r"^\d+\. \*\*" + re.escape(e.player_name) + r":\*\* (.+)$", expert, re.M)
        if match:
            full_review = match.group(1)
            if pid == "3647":
                full_review = full_review.replace("with 42 pressure matches", "with 43 retained pressure matches (42 peer-supported)")
        editorial = EDITORIAL.get(pid) if (role, pid) in selected else None
        pressure = obs.loc[obs.pressure_full.eq(True)].iloc[0]
        ordinary = obs.loc[obs.pressure_full.eq(False)]
        player = {
            "id": pid, "role": role, "name": e.player_name,
            "rank": int(primary["rank"]), "selected": (role, pid) in selected,
            "task": editorial[0] if editorial else f"Observed {str(rv.dominant_workload_phase)}-over workload",
            "editorial": {"title": editorial[1], "why": editorial[2], "caution": editorial[3], "contribution": editorial[4], "review": full_review} if editorial else None,
            "rating": {"point": primary.point, "low": primary.p10, "high": primary.p90, "finiteFraction": primary.finite_fraction},
            "exposure": {"pressureEvents": e.pressure_events, "pressureMatches": e.pressure_matches, "effectiveEvents": e.pressure_effective_events, "retainedEvents": e.retained_events, "sourceEvents": e.source_events, "sourceRetention": e.retained_fraction, "peerRetention": e.peer_pressure_count_retention},
            "pressure": clean({k: pressure[k] for k in ["runs", "wickets", "runs_per_100", "wickets_per_100", "weighted_runs_per_100", "weighted_wickets_per_100"]}),
            "ordinary": clean({k: ordinary.iloc[0][k] for k in ["opportunities", "matches", "runs_per_100", "wickets_per_100"]}) if len(ordinary) else None,
            "workload": records(workload, ["phase", "opportunities", "share"]),
            "pressurePhases": records(pressure_phases, ["phase", "opportunities", "share", "runs_per_100", "wickets_per_100"]),
            "seasons": records(part(seasons, role, pid).loc[lambda x: x.pressure_full.eq(True)], ["year", "opportunities", "matches", "runs_per_100", "wickets_per_100"]),
            "families": records(part(families, role, pid), ["family", "pressure_events", "pressure_matches", "point", "p10", "p90", "interval_reliable"]),
            "repeatability": {"matchPointLow": match_inf.point.min(), "matchPointHigh": match_inf.point.max(), "seasonsInadequate": int(rv.season_deletions_inadequate), "seasonDeletions": records(inf.loc[inf.deletion.eq("season")], ["removed", "point", "remaining_sample_adequate"])},
            "usual": {"reliable": False, "sampleEligible": bool(s.change_sample_eligible), "pressureFraction": s.supported_pressure_fraction, "pressureEvents": s.supported_pressure_events, "ordinaryEvents": s.supported_ordinary_events, "observedRunsDifference": s.runs_difference_per_100, "observedWicketsDifference": s.wickets_difference_per_100},
            "recent": {"status": recent, "events": recent_events, "matches": recent_matches, "rating": float(rr.iloc[0].point) if adequate else None},
            "variants": records(r, ["variant", "rank", "point", "p10", "p90"]),
            "cases": records(player_cases, case_columns) if editorial else [],
            "alternatives": [{"id": str(a.alternative_id), "rank": int(a.alternative_rank), "boundary": bool(a.boundary_alternative), "roleSimilar": bool(a.role_similar_alternative)} for a in part(alternatives, role, pid).itertuples()],
        }
        if player["selected"]:
            assert editorial and full_review and player["cases"], f"Incomplete selected evidence: {role}/{pid}"
        players.append(clean(player))
    assert sum(p["recent"]["status"] == "adequate" for p in players if p["selected"]) == 7
    assert sum(p["recent"]["status"] == "no_retained_pressure" for p in players if p["selected"]) == 2
    for row in top.itertuples():
        player = next(p for p in players if p["role"] == row.role and p["id"] == row.player_id)
        assert player["rank"] == int(row.rank)
        assert np.isclose(player["rating"]["low"], row.selection_score, atol=1e-10)
    release = {
        "id": "pressure-index-2026-11-01-v1", "cutoff": "2026-11-01", "firstYear": 2023,
        "matches": 511, "events": 121891, "pressureEvents": 43029, "pressureShare": 43029 / 121891 * 100,
        "battingEligible": 75, "bowlingEligible": 104, "dossiers": 243, "bootstrapDraws": 1000,
        "reservedMatches": 109, "reservedBattingEligible": 6, "reservedBowlingEligible": 28,
        "selectedRecentAdequate": 7, "selectedRecentAbsent": 2, "sourceMatches": 883, "verifiedMatches": 651,
        "developmentMatches": 402, "developmentBattingEligible": 62, "developmentBowlingEligible": 90,
        "weightOverlap": {"batting": [10, 8], "bowling": [9, 9]},
        "method": "descriptive_peer_pressure_v2", "protocolCommit": "5ca8bea",
        "sourceHashes": {"topTens": digest(FINAL / "two_top_ten_lists.csv"), "method": digest(ROOT / "configs/descriptive_rating_v2.json"), "finalManifest": digest(FINAL / "manifest.json")},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in [("players.json", players), ("release.json", release)]:
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(f"Exported {len(players)} curated role entries, 20 selections; frozen files verified; no scoring executed.")


if __name__ == "__main__":
    run()
