"""Descriptive tables and whole-match uncertainty; no player performance ranking."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .state import match_flags


def metrics(events, keys):
    d = events.copy()
    d["opportunity"] = d["extras_type"].ne("wide").astype(int)
    d["opportunity_runs"] = d["recorded_runs"] * d["opportunity"]
    d["opportunity_boundary"] = d["boundary_flag"] & d["opportunity"].astype(bool)
    d["opportunity_zero"] = d["recorded_zero"] & d["opportunity"].astype(bool)
    out = d.groupby(keys, observed=True, dropna=False).agg(
        delivery_events=("event_id", "size"), matches=("match_id", "nunique"),
        batting_opportunities=("opportunity", "sum"), recorded_runs=("opportunity_runs", "sum"),
        boundary_events=("opportunity_boundary", "sum"), zero_recorded_run_events=("opportunity_zero", "sum"),
        legal_deliveries=("legal_delivery", "sum"), bowler_credited_wickets=("bowler_credited_wicket", "sum"),
        team_wicket_events=("is_wicket", "sum"), illegal_events=("illegal_delivery", "sum"),
        proxy_pressure_events=("pressure_proxy", "sum")).reset_index()
    for target, numerator, denominator in [
        ("recorded_runs_per_100_opportunities", "recorded_runs", "batting_opportunities"),
        ("boundary_pct", "boundary_events", "batting_opportunities"),
        ("zero_recorded_runs_pct", "zero_recorded_run_events", "batting_opportunities"),
        ("bowler_wickets_per_100_attempts", "bowler_credited_wickets", "delivery_events"),
        ("illegal_delivery_pct", "illegal_events", "delivery_events"),
        ("pressure_proxy_pct", "proxy_pressure_events", "delivery_events"),
    ]:
        out[target] = 100 * out[numerator] / out[denominator].replace(0, np.nan)
    return out


def player_exposure(events, cutoff):
    primary = events.loc[events["primary_scope"] & events["innings"].isin([1, 2])]
    accepted = primary.loc[primary["eligible_proxy"]]
    outputs = []
    match_outputs = []
    for role, identity, name, minimum, pressure_minimum in [
        ("batting", "striker_id", "striker_name", 300, 75),
        ("bowling", "bowler_id", "bowler_name", 240, 60),
    ]:
        raw = primary.loc[primary["extras_type"].ne("wide")] if role == "batting" else primary
        d = accepted.loc[accepted["extras_type"].ne("wide")].copy() if role == "batting" else accepted.copy()
        d["recency_weight"] = np.exp2(-(pd.Timestamp(cutoff) - pd.to_datetime(d["match_date"])).dt.days / 730)
        d["weight_squared"] = d["recency_weight"] ** 2
        d["is_pressure"] = d["pressure_proxy"].astype(bool)
        d["is_ordinary"] = ~d["is_pressure"]
        named = raw.groupby(identity).agg(player_name=(name, "first"), source_opportunities=("event_id", "size"),
                                         source_matches=("match_id", "nunique"))
        result = d.groupby(identity).agg(
            opportunities=("event_id", "size"), matches=("match_id", "nunique"),
            pressure_opportunities=("is_pressure", "sum"), ordinary_opportunities=("is_ordinary", "sum"),
            years=("year", "nunique"), weight_sum=("recency_weight", "sum"), weight_square_sum=("weight_squared", "sum"))
        for label, subset in [("pressure", d[d["is_pressure"]]), ("ordinary", d[d["is_ordinary"]]),
                              ("ipl", d[d["family"].eq("IPL")]), ("t20i", d[d["family"].eq("T20I")])]:
            result[label + "_matches"] = subset.groupby(identity)["match_id"].nunique()
        result = named.join(result, how="left").fillna(0).reset_index().rename(columns={identity: "player_id"})
        result["role"] = role
        result["retained_pct"] = 100 * result["opportunities"] / result["source_opportunities"]
        result["effective_opportunities"] = result["weight_sum"] ** 2 / result["weight_square_sum"].replace(0, np.nan)
        result["effective_opportunities"] = result["effective_opportunities"].fillna(0)
        result["passes_total"] = result["opportunities"] >= minimum
        result["passes_pressure_count"] = result["pressure_opportunities"] >= pressure_minimum
        result["passes_pressure_matches"] = result["pressure_matches"] >= 8
        result["passes_ordinary"] = (result["ordinary_matches"] >= 5) & (result["ordinary_opportunities"] >= 100)
        result["passes_effective_count"] = result["effective_opportunities"] >= 40
        checks = ["passes_total", "passes_pressure_count", "passes_pressure_matches", "passes_ordinary", "passes_effective_count"]
        result["meets_initial_sample_thresholds"] = result[checks].all(axis=1)
        result["weak_coverage_under_80pct"] = result["retained_pct"] < 80
        outputs.append(result.sort_values("player_id"))
        # Retain complete match blocks for future player resampling; avoid ball bootstrap.
        block = metrics(d, [identity, "match_id", "family", "year", "phase", "pressure_proxy"])
        block = block.rename(columns={identity: "player_id"})
        block["role"] = role
        match_outputs.append(block)
    return pd.concat(outputs, ignore_index=True), pd.concat(match_outputs, ignore_index=True)


def exposure_funnel(exposure):
    rows = []
    for role, part in exposure.groupby("role"):
        remaining = pd.Series(True, index=part.index)
        rows.append({"role": role, "stage": "Any supplied primary opportunity", "players": len(part)})
        for label, check in [
            ("Minimum retained opportunities", "passes_total"),
            ("Minimum pressure opportunities", "passes_pressure_count"),
            ("Pressure in at least 8 matches", "passes_pressure_matches"),
            ("Ordinary baseline evidence", "passes_ordinary"),
            ("Effective weighted count >= 40", "passes_effective_count"),
        ]:
            remaining &= part[check]
            rows.append({"role": role, "stage": label, "players": int(remaining.sum())})
    return pd.DataFrame(rows)


def chase_outcomes(matches, events):
    second_team = events.loc[events["innings"].eq(2)].groupby("match_id")["batting_team_id"].first().to_dict()
    rows = []
    for match in matches.to_dict("records"):
        kind, _, rain = match_flags(match)
        if match["family"] not in ("IPL", "T20I") or rain or kind not in ("runs", "wickets"):
            continue
        team = second_team.get(match["match_id"])
        if team is None or not match["win_team_id"]:
            continue
        rows.append({"match_id": match["match_id"], "year": match["year"], "family": match["family"],
                     "chase_win": int(team == match["win_team_id"])})
    return pd.DataFrame(rows)


def match_bootstrap(events, replicates, seed=1729):
    """Aggregate EDA means; resample each entire match jointly across pressure groups."""
    d = events.copy()
    d["opportunity"] = d["extras_type"].ne("wide").astype(int)
    d["opportunity_runs"] = d["recorded_runs"] * d["opportunity"]
    blocks = d.groupby(["match_id", "pressure_proxy"]).agg(
        n=("opportunity", "sum"), runs=("opportunity_runs", "sum"), attempts=("event_id", "size"),
        wickets=("bowler_credited_wicket", "sum"))
    ids = sorted(d["match_id"].unique())
    matrices = []
    for pressure in (False, True):
        sub = blocks.xs(pressure, level="pressure_proxy").reindex(ids, fill_value=0)
        matrices.append(sub[["n", "runs", "attempts", "wickets"]].to_numpy(dtype=float))
    array = np.stack(matrices, axis=1)
    rng = np.random.default_rng(seed)
    sampled = np.stack([array[rng.integers(0, len(ids), size=len(ids))].sum(axis=0) for _ in range(replicates)])
    original = array.sum(axis=0)
    rows = []
    for metric, numerator, denominator in [("recorded_runs_per_100_nonwide", 1, 0), ("bowler_wickets_per_100_attempts", 3, 2)]:
        draws = 100 * sampled[:, :, numerator] / sampled[:, :, denominator]
        points = 100 * original[:, numerator] / original[:, denominator]
        for i, name in enumerate(["ordinary_proxy", "pressure_proxy"]):
            rows.append({"metric": metric, "group": name, "estimate": points[i],
                         "p10": np.quantile(draws[:, i], 0.1), "p90": np.quantile(draws[:, i], 0.9),
                         "replicates": replicates, "resampling_unit": "whole_match"})
        differences = draws[:, 1] - draws[:, 0]
        rows.append({"metric": metric, "group": "pressure_minus_ordinary_descriptive", "estimate": points[1] - points[0],
                     "p10": np.quantile(differences, 0.1), "p90": np.quantile(differences, 0.9),
                     "replicates": replicates, "resampling_unit": "whole_match"})
    return pd.DataFrame(rows)


def build_tables(matches, events, ledger, config):
    primary = events[events["primary_scope"] & events["innings"].isin([1, 2])]
    accepted = events[events["eligible_proxy"]].copy()
    tables = {}
    tables["match_coverage"] = matches.groupby(["year", "family"]).agg(matches=("match_id", "size"),
                                                                               competitions=("comp_id", "nunique")).reset_index()
    coverage = primary.groupby(["year", "family"]).agg(source_events=("event_id", "size"), source_matches=("match_id", "nunique"))
    kept = accepted.groupby(["year", "family"]).agg(retained_events=("event_id", "size"), retained_matches=("match_id", "nunique"))
    coverage = coverage.join(kept).fillna(0)
    coverage["retained_pct"] = 100 * coverage["retained_events"] / coverage["source_events"]
    tables["retention_by_year_family"] = coverage.reset_index()
    tables["exclusion_ledger"] = ledger
    tables["exclusion_summary"] = ledger.groupby(["family", "quality"], as_index=False).agg(innings=("match_id", "size"), events=("events", "sum"))
    for name, keys in {
        "phase_metrics": ["family", "innings", "phase"],
        "phase_pressure_metrics": ["family", "innings", "phase", "pressure_proxy"],
        "year_phase_metrics": ["year", "family", "phase"],
        "over_metrics": ["family", "innings", "overid"],
        "pressure_metrics": ["pressure_proxy"],
        "pressure_by_year_family": ["year", "family"],
    }.items():
        tables[name] = metrics(accepted, keys)
    reason = accepted.copy()
    reason["reason"] = np.select([reason["late"] & reason["collapse"], reason["late"], reason["collapse"]],
                                  ["late_and_collapse", "late_only", "collapse_only"], default="ordinary_proxy")
    tables["pressure_reason_counts"] = reason.groupby(["family", "reason"], as_index=False).agg(events=("event_id", "size"))
    tables["player_exposure"], tables["player_match_metrics"] = player_exposure(events, config["data_cutoff_inclusive"])
    tables["sample_eligibility_funnel"] = exposure_funnel(tables["player_exposure"])
    tables["chase_outcome_matches"] = chase_outcomes(matches, events)
    tables["chase_outcomes"] = tables["chase_outcome_matches"].groupby(["year", "family"], as_index=False).agg(
        matches=("match_id", "size"), chase_wins=("chase_win", "sum"))
    tables["chase_outcomes"]["chase_win_pct"] = 100 * tables["chase_outcomes"]["chase_wins"] / tables["chase_outcomes"]["matches"]
    tables["pressure_metric_uncertainty"] = match_bootstrap(accepted, config["bootstrap"]["debug_replicates"])
    tables["dismissal_categories"] = events.loc[events["is_wicket"]].groupby(["dismissal_type", "bowler_credited_wicket"], as_index=False).agg(events=("event_id", "size"))
    tables["annotation_missingness"] = events.groupby(["year", "family"], as_index=False).agg(
        events=("event_id", "size"), speed_zero=("bowl_speed", lambda s: s.eq("0").sum()),
        stroke_blank_or_none=("stroke", lambda s: s.isin(["", "None"]).sum()))
    tables["annotation_missingness"]["speed_zero_pct"] = 100 * tables["annotation_missingness"]["speed_zero"] / tables["annotation_missingness"]["events"]
    return tables
