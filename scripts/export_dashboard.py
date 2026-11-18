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
TASKS = {'6396': 'Late-over scoring', '1699': 'Middle-over scoring', '3125': 'Middle / late-over scoring', '2756': 'Late-over scoring', '23311': 'Middle-over scoring', '1318': 'Late-over scoring', '6726': 'Late-over scoring', '7897': 'Middle / late-over scoring', '3647': 'Middle-over scoring', '4391': 'Middle / late-over scoring', '781': 'Middle-over control', '2933': 'Powerplay / death bowling', '4373': 'Late-over bowling', '5837': 'Middle-over bowling', '6354': 'Powerplay / late-over bowling', '35318': 'Pressure bowling', '6256': 'Middle-over bowling', '7327': 'Middle / late-over bowling', '6284': 'Middle-over bowling', '23': 'Middle-over bowling'}


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
    reserved_elig = pd.read_parquet(FINAL / "reserved_2026/eligibility.parquet")
    reserved_ratings = pd.read_parquet(FINAL / "reserved_2026/ratings.parquet")
    review = csv("counterexample_review.csv")

    def part(table, role, pid):
        return table.loc[table.role.eq(role) & table.player_id.eq(pid)]

    players = []
    for role, pid in sorted(keys):
        e = part(eligibility, role, pid).iloc[0]
        r = part(ratings, role, pid)
        primary = r.loc[r.variant.eq("default_60_40")].iloc[0]
        rv = part(review, role, pid).iloc[0]
        reserved_entry = part(reserved_elig, role, pid)
        rr = part(reserved_ratings, role, pid)
        rr = rr.loc[rr.variant.eq("default_60_40")]
        recent_events = int(reserved_entry.iloc[0].pressure_events) if len(reserved_entry) else 0
        recent_matches = int(reserved_entry.iloc[0].pressure_matches) if len(reserved_entry) else 0
        adequate = bool(len(rr) and rr.iloc[0].selection_ready)
        recent = "adequate" if adequate else "no_retained_pressure" if not recent_events else "limited"
        task = TASKS.get(pid) if (role, pid) in selected else None
        player = {
            "id": pid, "role": role, "name": e.player_name,
            "rank": int(primary["rank"]), "selected": (role, pid) in selected,
            "task": task or f"Observed {str(rv.dominant_workload_phase)}-over workload",
            "rating": {"low": primary.p10},
            "exposure": {"pressureEvents": int(e.pressure_events), "pressureMatches": int(e.pressure_matches), "peerSupportedMatches": int(primary.peer_pressure_matches)},
            "recent": {"status": recent},
            "eligibility": {"primary": bool(primary.selection_ready)},
        }
        players.append(clean(player))
    assert sum(p["recent"]["status"] == "adequate" for p in players if p["selected"]) == 7
    assert sum(p["recent"]["status"] == "no_retained_pressure" for p in players if p["selected"]) == 2
    for row in top.itertuples():
        player = next(p for p in players if p["role"] == row.role and p["id"] == row.player_id)
        assert player["rank"] == int(row.rank)
        assert np.isclose(player["rating"]["low"], row.selection_score, atol=1e-10)
    pressure = pd.read_csv(ROOT / "reports/pressure_validation_2026-11-01/pressure_by_year_family.csv")
    release = {
        "id": "pressure-index-2026-11-01-v1", "publicationSchemaVersion": 2, "cutoff": "2026-11-01", "firstYear": 2023,
        "matches": 511, "events": 121891, "pressureEvents": 43029, "pressureShare": 43029 / 121891 * 100,
        "battingEligible": 75, "bowlingEligible": 104, "dossiers": 243, "bootstrapDraws": 1000,
        "reservedMatches": 109, "reservedBattingEligible": 6, "reservedBowlingEligible": 28,
        "selectedRecentAdequate": 7, "selectedRecentAbsent": 2, "sourceMatches": 883, "verifiedMatches": 651,
        "developmentMatches": 402, "developmentBattingEligible": 62, "developmentBowlingEligible": 90,
        "weightOverlap": {"batting": {"runs_wickets_50_50": 10, "runs_wickets_70_30": 8}, "bowling": {"runs_wickets_50_50": 9, "runs_wickets_70_30": 9}},
        "verifiedEvents": int(pressure.events.sum()), "verifiedPressureEvents": int(pressure.pressure_events.sum()),
        "verifiedPressureShare": float(pressure.pressure_events.sum() / pressure.events.sum() * 100),
        "selectedTotal": len(selected), "selectedRecentLimited": 11, "topCount": 10, "profileCount": len(players),
        "developmentLastYear": 2025, "recentYear": 2026, "auctionYear": 2027, "season": 2, "round": 1,
        "method": "descriptive_peer_pressure_v2", "protocolCommit": "5ca8bea",
        "sourceHashes": {"topTens": digest(FINAL / "two_top_ten_lists.csv"), "method": digest(ROOT / "configs/descriptive_rating_v2.json"), "finalManifest": digest(FINAL / "manifest.json")},
    }
    site = {
        "publicBaseUrl": "https://supe-rr-manav.vercel.app",
        "heroPreviewCount": 3, "compareLimit": 3, "scoreDigits": 4,
        "method": {"lateStart": 16, "lateEnd": 20, "collapseWickets": 2, "collapseBalls": 12,
          "earlyWickets": 4, "earlyStart": 1, "earlyEnd": 10, "chaseInnings": 2,
          "chaseBallsMin": 1, "chaseBallsMax": 60, "chaseRateMin": .75, "chaseRateMax": 1.5,
          "pressureTargetMin": 20, "pressureTargetMax": 30, "runsWeight": 60, "wicketsWeight": 40,
          "sensitivityEqual": 50, "sensitivityRuns": 70, "sensitivityWickets": 30,
          "levelWeight": 70, "changeWeight": 30, "recencyDays": 730,
          "peerOpportunities": 20, "peerMatches": 3, "battingTotal": 300, "bowlingTotal": 240,
          "battingPressure": 75, "bowlingPressure": 60, "pressureMatches": 8,
          "effectiveCount": 40, "retentionPercent": 80, "finitePercent": 95,
          "quantilePercent": 10, "battingShrinkage": 75, "bowlingShrinkage": 60,
          "reliableChangeIntervals": 0, "seed": 1729},
        "document": {"maxBytes": 52428800},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in [("players.json", players), ("release.json", release), ("site.json", site)]:
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(f"Exported {len(players)} aggregate-only role entries, 20 selections; frozen files verified; no scoring executed.")


if __name__ == "__main__":
    run()
