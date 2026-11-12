"""Coverage and comparison-support diagnostics. No predictive model is fitted."""

import json

import numpy as np
import pandas as pd

from .data import fingerprints, save_json, sha256
from .external import CUTOFF
from .pilot_report import markdown_table
from .state import BOWLER_WICKETS


def context_support(events, keys, minimum_events, minimum_matches):
    """Empirical common support at an explicit coarse resolution, not causal overlap."""
    grouped = events.groupby(keys + ["pressure_full"], observed=True, dropna=False).agg(
        events=("event_id", "size"), matches=("match_id", "nunique"))
    counts = grouped["events"].unstack("pressure_full", fill_value=0).reindex(columns=[False, True], fill_value=0)
    matches = grouped["matches"].unstack("pressure_full", fill_value=0).reindex(columns=[False, True], fill_value=0)
    out = counts.rename(columns={False: "ordinary_events", True: "pressure_events"})
    out["ordinary_matches"] = matches[False]
    out["pressure_matches"] = matches[True]
    out["has_both_groups"] = (counts > 0).all(axis=1)
    out["supported"] = (counts >= minimum_events).all(axis=1) & (matches >= minimum_matches).all(axis=1)
    out["pressure_without_ordinary"] = counts[True].gt(0) & counts[False].eq(0)
    return out.reset_index()


def bootstrap_comparisons(events, support, keys, replicates, seed):
    """Resample whole matches jointly; recompute pressure-stratum weights per draw.

    Supported-cell definition is fixed for this descriptive diagnostic. A cell
    absent in a replicate is omitted from that replicate and weights renormalize.
    Report this loss; these intervals are not uncertainty for a player ranking.
    """
    cells = support[keys + ["supported"]].copy().reset_index(drop=True)
    cells["cell"] = np.arange(len(cells))
    d = events.merge(cells, on=keys, validate="many_to_one")
    d["bat_opportunity"] = d.extras_wides.eq(0).astype(int)
    d["bat_runs"] = d.batter_runs * d.bat_opportunity
    d["bowler_wicket"] = d.is_wicket & d.dismissal_type.isin(BOWLER_WICKETS)
    ids = sorted(d.match_id.unique())
    lookup = {mid: i for i, mid in enumerate(ids)}
    blocks = d.groupby(["match_id", "cell", "pressure_full"]).agg(
        attempts=("event_id", "size"), opportunities=("bat_opportunity", "sum"),
        runs=("bat_runs", "sum"), wickets=("bowler_wicket", "sum")).reset_index()
    array = np.zeros((len(ids), len(cells), 2, 4), dtype=float)
    for row in blocks.itertuples(index=False):
        array[lookup[row.match_id], row.cell, int(row.pressure_full)] = [row.attempts, row.opportunities, row.runs, row.wickets]
    eligible = cells.supported.to_numpy(dtype=bool)

    def estimates(totals, numerator, denominator):
        summed = totals.sum(axis=0)
        raw = 100 * (summed[1, numerator] / summed[1, denominator] - summed[0, numerator] / summed[0, denominator])
        valid = eligible & (totals[:, :, denominator] > 0).all(axis=1)
        if not valid.any():
            return raw, np.nan, np.nan, 0
        t = totals[valid]
        shared = t.sum(axis=0)
        restricted_raw = 100 * (shared[1, numerator] / shared[1, denominator] - shared[0, numerator] / shared[0, denominator])
        weights = t[:, 1, denominator] / t[:, 1, denominator].sum()
        difference = 100 * np.sum(weights * (t[:, 1, numerator] / t[:, 1, denominator] - t[:, 0, numerator] / t[:, 0, denominator]))
        return raw, restricted_raw, difference, int(valid.sum())

    rng = np.random.default_rng(seed)
    specifications = [("batter_runs_per_100_nonwide", 2, 1), ("bowler_wickets_per_100_events", 3, 0)]
    draws = {name: [] for name, _, _ in specifications}
    for _ in range(replicates):
        weights = rng.multinomial(len(ids), np.full(len(ids), 1 / len(ids)))
        totals = np.einsum("m,mcgo->cgo", weights, array)
        for name, numerator, denominator in specifications:
            draws[name].append(estimates(totals, numerator, denominator))
    rows = []
    for name, numerator, denominator in specifications:
        points = estimates(array.sum(axis=0), numerator, denominator)
        values = np.asarray(draws[name])
        for i, comparison in enumerate(("raw_pressure_minus_ordinary", "raw_difference_on_supported_cells", "supported_context_standardized_difference")):
            finite = values[:, i][np.isfinite(values[:, i])]
            rows.append(dict(metric=name, comparison=comparison, estimate=points[i],
                p10=np.quantile(finite, .1) if len(finite) else np.nan,
                p90=np.quantile(finite, .9) if len(finite) else np.nan,
                replicates=replicates, finite_replicates=len(finite), unit="whole_match",
                original_supported_cells=points[3], minimum_cells_in_draw=int(values[:, 3].min()),
                population="2022-2025 verified matches", interpretation="descriptive association; different support populations"))
    return pd.DataFrame(rows)


def player_coverage(raw, verified, config):
    rows = []
    for role, identity, name, total_min, pressure_min in (
        ("batting", "striker_id", "striker_name", 300, 75), ("bowling", "bowler_id", "bowler_name", 240, 60)):
        source = raw.loc[raw.extras_type.ne("wide")] if role == "batting" else raw
        kept = verified.loc[verified.extras_wides.eq(0)].copy() if role == "batting" else verified.copy()
        source_groups = source.groupby(identity).agg(player_name=(name, "first"), source_opportunities=("event_id", "size"), source_matches=("match_id", "nunique"))
        kept["ordinary"] = ~kept.pressure_full
        kept["weight"] = np.exp2(-(pd.Timestamp(CUTOFF) - pd.to_datetime(kept.match_date)).dt.days / 730)
        kept["weight_squared"] = kept.weight ** 2
        grouped = kept.groupby(identity).agg(retained_opportunities=("event_id", "size"), retained_matches=("match_id", "nunique"),
            pressure_opportunities=("pressure_full", "sum"), ordinary_opportunities=("ordinary", "sum"),
            weight_sum=("weight", "sum"), weight_square_sum=("weight_squared", "sum"))
        for label, part in [("pressure", kept.loc[kept.pressure_full]), ("ordinary", kept.loc[~kept.pressure_full])]:
            grouped[label + "_matches"] = part.groupby(identity).match_id.nunique()
        result = source_groups.join(grouped).fillna(0).reset_index().rename(columns={identity: "player_id"})
        result["role"] = role
        result["retained_percent"] = 100 * result.retained_opportunities / result.source_opportunities
        result["effective_opportunities"] = (result.weight_sum ** 2 / result.weight_square_sum.replace(0, np.nan)).fillna(0)
        result["meets_sample_thresholds"] = ((result.retained_opportunities >= total_min) & (result.pressure_opportunities >= pressure_min) &
            (result.pressure_matches >= 8) & (result.ordinary_opportunities >= 100) & (result.ordinary_matches >= 5) & (result.effective_opportunities >= 40))
        kept["player_id"] = kept[identity]
        support = context_support(kept, config["player_context"], config["player_minimum_events_per_group_per_cell"],
                                  config["player_minimum_matches_per_group_per_cell"])
        support["supported_pressure_events"] = support.pressure_events.where(support.supported, 0)
        totals = support.groupby("player_id")[["pressure_events", "supported_pressure_events"]].sum()
        totals["own_context_pressure_supported_percent"] = 100 * totals.supported_pressure_events / totals.pressure_events.replace(0, np.nan)
        result = result.merge(totals[["own_context_pressure_supported_percent"]], on="player_id", how="left", validate="one_to_one")
        rows.append(result)
    return pd.concat(rows, ignore_index=True).sort_values(["role", "player_id"])


def validate_pressure(root):
    source = root / "reports/full_reconciliation_2026-11-01"
    manifest = json.loads((source / "manifest.json").read_text())
    for name in ("verified_events.parquet", "matches.csv"):
        if sha256(source / name) != manifest["output_sha256"][name]:
            raise ValueError("Reconciliation artifacts changed")
    raw_hashes = fingerprints(root / "6af3166e7b922_data_pack")
    if raw_hashes != manifest["source_sha256"]:
        raise ValueError("Source corpus changed")
    config_path = root / "configs/pressure_validation.json"
    config = json.loads(config_path.read_text())
    d = pd.read_parquet(source / "verified_events.parquet")
    d["phase"] = np.select([d.overid <= 6, d.overid <= 15], ["01-06", "07-15"], default="16-20")
    d["wicket_band"] = pd.cut(d.wickets_before, [-1, 2, 5, 10], labels=["0-2", "3-5", "6-9"]).astype(str)
    d["period"] = np.where(d.match_date <= config["development_last_date"], "development_2022_2025", "reserved_2026")
    out = root / "reports/pressure_validation_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    frames = {}
    pressure_rows, support_rows = [], []
    for period, group in [("all", d), *list(d.groupby("period"))]:
        for denominator, population in [("delivery_events", group), ("legal_balls", group.loc[group.legal_delivery_verified])]:
            pressure_rows.append(dict(period=period, denominator=denominator, events=len(population), matches=population.match_id.nunique(),
                **{f"{k}_percent": 100 * population[k].mean() for k in ("late", "collapse", "tight_chase", "pressure_proxy", "pressure_full")}))
        for resolution in ("coarse_context", "finer_context"):
            support = context_support(group, config[resolution], config["minimum_events_per_group_per_cell"], config["minimum_matches_per_group_per_cell"])
            frames[f"{resolution}_{period}"] = support
            support_rows.append(dict(period=period, resolution=resolution, cells=len(support), supported_cells=int(support.supported.sum()),
                pressure_events=int(support.pressure_events.sum()), supported_pressure_events=int(support.loc[support.supported, "pressure_events"].sum()),
                pressure_supported_percent=100 * support.loc[support.supported, "pressure_events"].sum() / support.pressure_events.sum(),
                pressure_without_any_ordinary_percent=100 * support.loc[support.pressure_without_ordinary, "pressure_events"].sum() / support.pressure_events.sum()))
    frames["pressure_coverage"] = pd.DataFrame(pressure_rows)
    frames["context_support_summary"] = pd.DataFrame(support_rows)
    frames["pressure_by_year_family"] = d.groupby(["year", "family"]).agg(events=("event_id", "size"),
        matches=("match_id", "nunique"), pressure_events=("pressure_full", "sum"), pressure_fraction=("pressure_full", "mean")).reset_index()
    balance = d.groupby(["period", "phase", "pressure_full"]).size().rename("events").reset_index()
    balance["group_percent"] = 100 * balance.events / balance.groupby(["period", "pressure_full"]).events.transform("sum")
    frames["phase_balance"] = balance
    dev = d.loc[d.period.eq("development_2022_2025")]
    print(f"Computing whole-match diagnostic bootstrap on {dev.match_id.nunique()} development matches", flush=True)
    frames["descriptive_comparisons"] = bootstrap_comparisons(dev, frames["finer_context_development_2022_2025"],
        config["finer_context"], config["bootstrap_replicates"], config["seed"])
    raw = pd.read_csv(root / "6af3166e7b922_data_pack/ball_by_ball.csv", dtype=str, keep_default_na=False,
        usecols=["match_id", "innings", "innings_ball_num", "striker_id", "striker_name", "bowler_id", "bowler_name", "extras_type"])
    m = pd.read_csv(source / "matches.csv", dtype={"match_id": str})
    raw = raw.loc[raw.match_id.isin(m.loc[m.primary_scope, "match_id"]) & raw.innings.isin(["1", "2"])].copy()
    raw["event_id"] = raw.match_id + ":" + raw.innings + ":" + raw.innings_ball_num
    frames["player_coverage"] = player_coverage(raw, d, config)
    frames["player_coverage_summary"] = frames["player_coverage"].groupby("role").agg(
        supplied_players=("player_id", "size"), retained_players=("retained_opportunities", lambda x: x.gt(0).sum()),
        eligible_players=("meets_sample_thresholds", "sum"), median_retained_percent=("retained_percent", "median"),
        players_below_80_percent_retention=("retained_percent", lambda x: x.lt(80).sum())).reset_index()
    # Outcome-independent overlap gate, evaluated on development only.
    fine = frames["finer_context_development_2022_2025"]
    support_share = fine.loc[fine.supported, "pressure_events"].sum() / fine.pressure_events.sum()
    structural_zero = bool((dev.overid >= 16).any() and dev.loc[dev.overid >= 16, "pressure_full"].all())
    gate = {"global_pressure_change_comparison_ready": bool(support_share >= config["minimum_pressure_support_share_for_global_change"] and not structural_zero),
        "development_supported_pressure_fraction": support_share, "late_phase_has_no_ordinary_controls": structural_zero,
        "pressure_rule_changed": False, "models_fitted": False, "player_rankings_created": False,
        "context_cells_do_not_establish_causal_identification": True,
        "decision": "Hold global 70/30 and 50/50 rankings until change estimand/support policy is revised; context-baseline ML not fitted in this task."}
    save_json(out / "model_gate.json", gate)
    for name, frame in frames.items():
        frame.to_csv(out / f"{name}.csv", index=False)
    from .validation_figures import make_validation_figures
    make_validation_figures(frames, m, out)
    (out / "REPORT.md").write_text("\n".join([
        "# Pressure comparison validation before ML", "",
        "[Standalone figures (PDF)](VALIDATION_CHARTS.pdf)", "",
        "The full late OR collapse OR tight_chase rule is unchanged. Scores come only from completely reconciled matches. This diagnostic measures support and descriptive associations, not causal pressure effects or player rankings.", "",
        "## Verified coverage", "", markdown_table(frames["pressure_coverage"].round(3)), "",
        "The target band is 20–30%, diagnostic only. Late overs label every event in overs 16–20; collapse and tight-chase clauses enlarge the union. Component shares overlap and cannot be added. Coverage is conditional on retained matches, not an estimate for excluded matches.", "",
        "## Comparable contexts", "", markdown_table(frames["context_support_summary"].round(3)), "",
        "Coarse cells: family, year, innings, phase. Finer cells also condition on pre-ball wickets (0–2, 3–5, 6–9). A supported cell has at least 20 events and 3 distinct matches in each pressure group. These thresholds were frozen before comparison inspection, without using player outcomes. Since pressure is deterministic from the full state, apparent coarse-cell overlap is not causal identification.", "",
        f"Development pressure support in finer cells: {100 * support_share:.2f}%. Late-phase structural zero ordinary support: {structural_zero}. "
        f"Global pressure-change comparison ready: {gate['global_pressure_change_comparison_ready']}.", "",
        "Every late-phase observation is pressure=True. A phase-adjusted model cannot manufacture within-phase ordinary evidence there. Using ordinary observations from other phases for a global change score would require extrapolation and should not be presented as an observed like-for-like difference.", "",
        "## Development-only descriptive comparison", "", markdown_table(frames["descriptive_comparisons"].round(4)), "",
        "Intervals are 10th–90th percentiles from 1,000 whole-match resamples; both innings and pressure groups stay together. Context-standardized differences use only supported finer cells, weighted to their pressure exposure. Each bootstrap draw recomputes weights; cells with a missing group in that draw are omitted and weights renormalized (minimum retained-cell counts shown). Raw and standardized estimates therefore describe different populations; their difference is not a causal adjustment estimate. No 2026 outcomes enter these comparison estimates.", "",
        "## Player evidence and coverage", "", markdown_table(frames["player_coverage_summary"].round(2)), "",
        "Player denominators are all supplied primary normal-innings opportunities: nonwide batting events and all bowling events. Eligibility retains the registered sample requirements (batting 300/75, bowling 240/60 total/pressure; 8 pressure matches; 100 ordinary opportunities across 5 matches; effective recency count >=40). Eligibility alone does not establish comparable contexts. Player-level support uses role/player, family, innings and phase, requiring 10 observations and 2 matches in each group; this pools years only for an exposure diagnostic. Player tables are ID-sorted, not performance rankings.", "",
        "## Decision and next implementation", "",
        "Do not fit final clutch rankings with the global pressure-minus-ordinary term. Preserve the 70/30 default and 50/50 registered variant as unexecuted designs. A defensible next design would estimate context-adjusted pressure performance level, and report a separate change estimate only on supported contexts, with explicit coverage and uncertainty. Any revised blended score needs its estimand and support requirements frozen before model fitting.", "",
        "Keep missing-source/rain/conflict cohorts visible; resolve material remaining player-coverage gaps before final eligibility. Use only pre-2026 development to choose an amended pressure/change methodology. Aggregate 2026 EDA has been seen, so it is reserved model evaluation, not pristine unseen data. Freeze target/score features before nuisance models, enforce chronological/match-group cross-fitting, and retain the whole-match bootstrap. The optional explorer stays deferred and the organiser draft stays unsent.", ""]))
    if fingerprints(root / "6af3166e7b922_data_pack") != raw_hashes:
        raise ValueError("Raw data changed")
    save_json(out / "manifest.json", {"cutoff": CUTOFF, "source_sha256": raw_hashes,
        "reconciliation_manifest_sha256": sha256(source / "manifest.json"), "config_sha256": sha256(config_path),
        "analysis_config_sha256": sha256(root / "configs/analysis_preregistration.json"),
        "code_sha256": {str(p.relative_to(root)): sha256(p) for p in sorted((root / "src").rglob("*.py"))},
        "output_sha256": {p.name: sha256(p) for p in sorted(out.iterdir()) if p.name != "manifest.json"},
        "models_fitted": False, "bootstrap_unit": "whole_match", "bootstrap_replicates": config["bootstrap_replicates"]})
    print(json.dumps(gate, indent=2))
    return frames
