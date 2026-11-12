"""Frozen supported-context estimands and outcome-independent model preflight.

No expectation model is fitted here. The estimator is exercised on synthetic
contributions in tests; live outputs contain exposure/support, never scores.
"""

import json

import numpy as np
import pandas as pd

from .data import fingerprints, load, save_json, sha256, unique
from .pilot_report import markdown_table
from .pressure_validation import context_support
from .state import BOWLER_WICKETS


FEATURES = ["family", "innings", "phase", "wicket_band"]
IDENTITIES = ["event_id", "match_id", "match_date", "year", "striker_id", "bowler_id", "pressure_full"]


def delivery_tables(events):
    """Allowlist features; attribution and outcome-based role filters stay separate."""
    d = events.copy()
    unique(d, ["event_id"], "method events")
    if not d.innings.isin([1, 2]).all() or not d.wickets_before.between(0, 9).all():
        raise ValueError("Unsupported innings or pre-ball wicket state")
    if not d.overid.between(1, 20).all():
        raise ValueError("Invalid over")
    d["phase"] = np.select([d.overid <= 6, d.overid <= 15], ["01-06", "07-15"], default="16-20")
    d["wicket_band"] = pd.cut(d.wickets_before, [-1, 2, 5, 9], labels=["0-2", "3-5", "6-9"]).astype(str)
    features = d[["event_id"] + FEATURES].copy()
    if features.isna().any().any():
        raise ValueError("Missing model context")
    identities = d[IDENTITIES].copy()
    identities["batting_opportunity"] = d.extras_wides.eq(0)
    credited = d.is_wicket & d.dismissal_type.isin(BOWLER_WICKETS)
    targets = pd.DataFrame({"event_id": d.event_id, "bat_runs": d.batter_runs,
        "striker_wicket": (credited & d.dismissed_player_id.eq(d.striker_id)).astype(int),
        "bowl_runs": d.batter_runs + d.extras_wides + d.extras_noballs,
        "bowler_wicket": credited.astype(int)})
    if targets.drop(columns="event_id").isna().any().any() or (targets.drop(columns="event_id") < 0).any().any():
        raise ValueError("Invalid target")
    return features, identities, targets


def chronological_folds(identities, config):
    """Calendar folds with complete matches and strictly earlier training dates."""
    matches = identities[["match_id", "match_date", "year"]].drop_duplicates()
    unique(matches, ["match_id"], "match chronology")
    dates = pd.to_datetime(matches.match_date, format="%Y-%m-%d", errors="raise")
    if not dates.dt.year.eq(matches.year).all():
        raise ValueError("Match year disagrees with date")
    years = [config["warmup_year"], *config["development_prediction_years"], config["reserved_prediction_year"]]
    if not matches.year.isin(years).all() or dates.gt(pd.Timestamp(config["cutoff_inclusive"])).any():
        raise ValueError("Match outside frozen date window")
    rows, summaries = [], []
    for year in years[1:]:
        boundary = f"{year}-01-01"
        train = matches.loc[matches.match_date < boundary].copy()
        evaluation = matches.loc[matches.year.eq(year)].copy()
        if train.empty or evaluation.empty:
            raise ValueError(f"Empty chronological partition for {year}")
        if set(train.match_id) & set(evaluation.match_id) or train.match_date.max() >= evaluation.match_date.min():
            raise ValueError("Chronological leakage")
        for partition, part in [("train", train), ("evaluate", evaluation)]:
            part["fold_year"] = year
            part["partition"] = partition
            part["evaluation_use"] = "reserved" if year == config["reserved_prediction_year"] else "development"
            rows.append(part)
        summaries.append(dict(fold_year=year, train_matches=len(train), evaluation_matches=len(evaluation),
            train_last_date=train.match_date.max(), evaluation_first_date=evaluation.match_date.min(),
            evaluation_last_date=evaluation.match_date.max()))
    return pd.concat(rows, ignore_index=True), pd.DataFrame(summaries)


def _support(events, keys, minimum_events, minimum_matches):
    if events.empty:
        return pd.DataFrame(columns=keys + ["ordinary_events", "pressure_events", "ordinary_matches",
            "pressure_matches", "has_both_groups", "supported", "pressure_without_ordinary"])
    return context_support(events, keys, minimum_events, minimum_matches)


def _counts(events, prefix):
    result = events.groupby("player_id").agg(**{
        prefix + "events": ("event_id", "size"), prefix + "matches": ("match_id", "nunique"),
        prefix + "weight_sum": ("weight", "sum"), prefix + "weight_squared_sum": ("weight_squared", "sum")})
    result[prefix + "effective_events"] = result[prefix + "weight_sum"] ** 2 / result[prefix + "weight_squared_sum"]
    return result


def eligibility(exposures, source, config, role, reference_date):
    """Uses identities, dates, pressure labels and exposure only, never targets."""
    identity = "striker_id" if role == "batting" else "bowler_id"
    kept = exposures.loc[exposures.batting_opportunity].copy() if role == "batting" else exposures.copy()
    raw = source.loc[source.extras_type.ne("wide")] if role == "batting" else source
    unique(kept, ["event_id"], "retained role opportunities")
    unique(raw, ["event_id"], "source role opportunities")
    if not set(kept.event_id).issubset(set(raw.event_id)):
        raise ValueError("Retained opportunity outside source denominator")
    kept["player_id"] = kept[identity]
    age = (pd.Timestamp(reference_date) - pd.to_datetime(kept.match_date)).dt.days
    if age.lt(0).any():
        raise ValueError("Future opportunity in recency window")
    kept["weight"] = np.exp2(-age / config["recency_half_life_days"])
    kept["weight_squared"] = kept.weight ** 2
    keys = config["context_keys"]
    peers = _support(kept, keys, config["peer_minimum_events_per_group"], config["peer_minimum_matches_per_group"])
    own = _support(kept, ["player_id"] + keys, config["player_minimum_events_per_group"], config["player_minimum_matches_per_group"])
    cells = own.rename(columns={"supported": "player_supported"}).merge(
        peers[keys + ["supported"]].rename(columns={"supported": "peer_supported"}), on=keys, validate="many_to_one")
    cells["supported"] = cells.player_supported.astype(bool) & cells.peer_supported.astype(bool)
    kept = kept.merge(cells[["player_id"] + keys + ["supported"]], on=["player_id"] + keys, validate="many_to_one")
    supported = kept.loc[kept.supported].copy()
    result = raw.groupby(identity).agg(source_events=("event_id", "size"), source_matches=("match_id", "nunique"))
    result.index.name = "player_id"
    for part, prefix in [(kept, "retained_"), (kept.loc[kept.pressure_full], "pressure_"),
                         (supported.loc[supported.pressure_full], "supported_pressure_"),
                         (supported.loc[~supported.pressure_full], "supported_ordinary_")]:
        result = result.join(_counts(part, prefix))
    result = result.fillna(0)
    if (result.retained_events > result.source_events).any() or not set(kept.player_id).issubset(result.index):
        raise ValueError("Role/source exposure mismatch")
    result["retained_fraction"] = result.retained_events / result.source_events
    result["supported_pressure_fraction"] = result.supported_pressure_events / result.pressure_events.replace(0, np.nan)
    result["supported_pressure_weight_fraction"] = result.supported_pressure_weight_sum / result.pressure_weight_sum.replace(0, np.nan)
    limits = config["roles"][role]
    result["level_sample_eligible"] = ((result.retained_events >= limits["minimum_total_events"]) &
        (result.pressure_events >= limits["minimum_pressure_events"]) &
        (result.pressure_matches >= config["minimum_pressure_matches"]) &
        (result.pressure_effective_events >= config["minimum_effective_pressure_events"]))
    result["change_sample_eligible"] = ((result.supported_pressure_events >= limits["minimum_pressure_events"]) &
        (result.supported_pressure_matches >= config["minimum_pressure_matches"]) &
        (result.supported_pressure_effective_events >= config["minimum_effective_pressure_events"]) &
        (result.supported_ordinary_events >= config["minimum_ordinary_events_for_change"]) &
        (result.supported_ordinary_matches >= config["minimum_ordinary_matches_for_change"]))
    result["coverage_ready"] = result.retained_fraction >= config["minimum_retained_fraction_for_unqualified_shortlist"]
    result["blend_sample_eligible"] = result.level_sample_eligible & result.change_sample_eligible
    result["unqualified_shortlist_evidence_ready"] = result.blend_sample_eligible & result.coverage_ready
    result["role"] = role
    result = result.reset_index()
    result["blocked_reasons"] = result.apply(lambda r: ";".join(label for flag, label in (
        (r.level_sample_eligible, "insufficient_level_exposure"), (r.change_sample_eligible, "insufficient_supported_change_exposure"),
        (r.coverage_ready, "source_retention_below_80_percent")) if not flag), axis=1)
    return result.sort_values("player_id"), cells, peers


def estimate_components(events, frozen_cells, keys, pseudo_events, multiplicities=None):
    """One player's synthetic or cross-fitted contributions, with fixed support.

    Multiplicity counts replicate observations, so sum(w^2) uses multiplicity,
    not multiplicity squared. A lost comparison group invalidates change.
    Caller applies eligibility and common match draws outside this function.
    """
    d = events.copy()
    if pseudo_events <= 0 or not np.isfinite(d[["weight", "contribution"]].to_numpy()).all() or d.weight.le(0).any():
        raise ValueError("Invalid contributions, weights or regularizer")
    copies = pd.Series(1.0, index=d.index) if multiplicities is None else d.match_id.map(multiplicities).fillna(0)
    if not np.isfinite(copies).all() or copies.lt(0).any() or copies.ne(np.floor(copies)).any():
        raise ValueError("Bootstrap multiplicities must be nonnegative integers")
    d["weighted_sum"] = d.weight * copies
    d["square_sum"] = d.weight ** 2 * copies
    d["contribution_sum"] = d.weighted_sum * d.contribution
    p = d.loc[d.pressure_full]
    mass = p.weighted_sum.sum()
    n_eff = mass ** 2 / p.square_sum.sum() if mass else 0.0
    level_raw = p.contribution_sum.sum() / mass if mass else np.nan
    result = dict(level_raw=level_raw, level=level_raw * n_eff / (n_eff + pseudo_events),
        pressure_effective_events=n_eff, change_raw=np.nan, change=np.nan, paired_effective_events=np.nan,
        change_available=False)
    if frozen_cells.empty:
        return result
    unique(frozen_cells, keys, "frozen player support")
    base = frozen_cells[keys].copy()
    grouped = d.groupby(keys + ["pressure_full"], observed=True, dropna=False)[["weighted_sum", "square_sum", "contribution_sum"]].sum().reset_index()
    for flag, prefix in [(True, "p_"), (False, "o_")]:
        group = grouped.loc[grouped.pressure_full.eq(flag)].drop(columns="pressure_full")
        group = group.rename(columns={c: prefix + c for c in ["weighted_sum", "square_sum", "contribution_sum"]})
        base = base.merge(group, on=keys, how="left", validate="one_to_one")
    if base[["p_weighted_sum", "o_weighted_sum"]].isna().any().any() or (base[["p_weighted_sum", "o_weighted_sum"]] <= 0).any().any():
        return result
    q = base.p_weighted_sum / base.p_weighted_sum.sum()
    delta = (q * (base.p_contribution_sum / base.p_weighted_sum - base.o_contribution_sum / base.o_weighted_sum)).sum()
    inverse_n = (q ** 2 * (base.p_square_sum / base.p_weighted_sum ** 2 + base.o_square_sum / base.o_weighted_sum ** 2)).sum()
    paired = 1 / inverse_n
    result.update(change_raw=float(delta), change=float(delta * paired / (paired + pseudo_events)),
        paired_effective_events=float(paired), change_available=True)
    return result


def blend_components(level, change, config, eligible):
    if not eligible or not np.isfinite([level, change]).all():
        return {name: np.nan for name in config["level_change_weights"]}
    return {name: weights["level"] * level + weights["change"] * change
            for name, weights in config["level_change_weights"].items()}


def selection_interval(draws, config):
    """Never hide a material invalid-draw fraction behind conditional quantiles."""
    values = np.asarray(draws, dtype=float)
    finite = values[np.isfinite(values)]
    fraction = len(finite) / len(values) if len(values) else 0.0
    ready = fraction >= config["bootstrap"]["minimum_finite_fraction"]
    return dict(finite_fraction=fraction, selection_score=float(np.quantile(finite, config["bootstrap"]["selection_quantile"])) if ready else np.nan,
        p90=float(np.quantile(finite, .9)) if ready else np.nan)


def prepare_method(root):
    """Materialize the frozen contract and exposure gates without fitting models."""
    config_path = root / "configs/supported_method_v1.json"
    config = json.loads(config_path.read_text())
    original_path = root / "configs/analysis_preregistration.json"
    original = json.loads(original_path.read_text())
    if (config["cutoff_inclusive"] != "2026-11-01" or config["cutoff_inclusive"] != original["data_cutoff_inclusive"] or
        config["level_change_weights"] != original["level_change_weights"] or config["bootstrap"]["unit"] != "whole_match" or
        config["bootstrap"]["replicates"] != original["bootstrap"]["final_replicates"]):
        raise ValueError("Method violates approved frozen constraints")
    source = root / "reports/full_reconciliation_2026-11-01"
    validation = root / "reports/pressure_validation_2026-11-01"
    receipt = json.loads((source / "manifest.json").read_text())
    pressure_receipt = json.loads((validation / "manifest.json").read_text())
    if pressure_receipt["reconciliation_manifest_sha256"] != sha256(source / "manifest.json"):
        raise ValueError("Pressure validation belongs to a different reconciliation")
    if pressure_receipt["analysis_config_sha256"] != sha256(original_path):
        raise ValueError("Original pressure configuration changed")
    for directory, manifest, names in [(source, receipt, ["verified_events.parquet"]),
        (validation, pressure_receipt, ["model_gate.json"])]:
        for name in names:
            if sha256(directory / name) != manifest["output_sha256"][name]:
                raise ValueError("Upstream artifact changed: " + name)
    raw_hashes = fingerprints(root / "6af3166e7b922_data_pack")
    if raw_hashes != receipt["source_sha256"]:
        raise ValueError("Source corpus changed")
    out = root / "reports/supported_method_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    freeze_path = out / "frozen_method.json"
    if freeze_path.exists() and json.loads(freeze_path.read_text()) != config:
        raise ValueError("Frozen method changed; create a versioned amendment")
    save_json(freeze_path, config)
    d = pd.read_parquet(source / "verified_events.parquet")
    if not (d.match_accepted & d.score_verified & d.event_alignment_pass).all():
        raise ValueError("Unverified events supplied to method preflight")
    features, identities, targets = delivery_tables(d)
    folds, fold_summary = chronological_folds(identities, config)
    exposures = identities.merge(features, on="event_id", validate="one_to_one")
    _, _, raw, _, _ = load(root, config["cutoff_inclusive"])
    raw = raw.loc[raw.family.isin(["IPL", "T20I"]) & raw.innings.isin([1, 2])]
    for name, table in [("features", features), ("identities_and_exposures", identities), ("targets", targets)]:
        table.to_parquet(out / f"{name}.parquet", index=False)
    folds.to_csv(out / "match_folds.csv", index=False)
    fold_summary.to_csv(out / "fold_summary.csv", index=False)
    summaries, populations = [], []
    start = f"{config['development_prediction_years'][0]}-01-01"
    windows = [("development", start, config["development_reference_date"]),
        ("reserved_exposure_only", f"{config['reserved_prediction_year']}-01-01", config["final_reference_date"]),
        ("final_retrospective_exposure_only", start, config["final_reference_date"])]
    for window, first, last in windows:
        e = exposures.loc[exposures.match_date.between(first, last)].copy()
        r = raw.loc[raw.match_date.between(first, last)]
        populations.append(dict(window=window, first_date=first, last_date=last, verified_events=len(e),
            verified_matches=e.match_id.nunique(), source_events=len(r), source_matches=r.match_id.nunique()))
        for role in config["roles"]:
            players, cells, peers = eligibility(e, r, config, role, last)
            for name, table in [("players", players), ("player_cells", cells), ("peer_cells", peers)]:
                table.to_csv(out / f"{window}_{role}_{name}.csv", index=False)
            summaries.append(dict(window=window, role=role, supplied_players=len(players),
                retained_players=int(players.retained_events.gt(0).sum()), level_sample_eligible=int(players.level_sample_eligible.sum()),
                change_sample_eligible=int(players.change_sample_eligible.sum()), blend_sample_eligible=int(players.blend_sample_eligible.sum()),
                coverage_ready_blend=int(players.unqualified_shortlist_evidence_ready.sum()),
                supported_pressure_percent=100 * players.supported_pressure_events.sum() / players.pressure_events.sum()))
    summary = pd.DataFrame(summaries)
    summary.to_csv(out / "eligibility_summary.csv", index=False)
    population = pd.DataFrame(populations)
    population.to_csv(out / "population_windows.csv", index=False)
    old_gate = json.loads((validation / "model_gate.json").read_text())
    gate = {"method_id": config["method_id"], "method_config_sha256": sha256(config_path),
        "preflight_passed": True, "development_peer_baseline_permitted": True,
        "global_pressure_change_comparison_ready": old_gate["global_pressure_change_comparison_ready"],
        "restricted_change_requires_player_support": True, "final_rankings_permitted": False,
        "models_fitted": False, "player_scores_created": False, "reserved_outcome_metrics_computed": False,
        "note": "Eligibility is exposure only. Fit and validate development expectations next; do not infer model or ranking readiness from preflight."}
    save_json(out / "model_gate.json", gate)
    save_json(out / "feature_contract.json", {"predictors": FEATURES, "join_key_not_a_predictor": "event_id",
        "targets_file": "targets.parquet", "identity_pressure_and_role_filters_file": "identities_and_exposures.parquet",
        "support_keys_not_all_predictors": config["context_keys"], "current_outcome_features_allowed": False,
        "reserved_targets_exported_but_not_analyzed": True, "warmup_used_for_player_scores": False})
    (out / "REPORT.md").write_text("\n".join([
        "# Supported method preflight", "", f"Frozen method: `{config['method_id']}`; SHA-256 `{sha256(config_path)}`.", "",
        "No expectation model, player score or ranking was computed. These are outcome-independent evidence gates. The old global-change gate remains failed; the amendment permits a separate all-pressure level and change confined to supported same-player/year contexts.", "",
        "## Chronological folds", "", markdown_table(fold_summary), "",
        f"2022 is training warm-up only: {int(d.year.eq(2022).sum()):,} verified deliveries are excluded from scoring evidence. Each fold uses complete earlier-year matches; no evaluation match enters its training set. Reserved 2026 targets are exported separately, but no reserved outcome metric is computed.", "",
        "## Exposure windows", "", markdown_table(population), "", "## Player support", "", markdown_table(summary.round(3)), "",
        "Level eligibility uses total/pressure exposure and pressure-match/effective-count gates. Change independently repeats pressure gates within peer-and-player-supported cells plus ordinary evidence requirements. Cells include family, year, innings, phase and wicket band. Bowling counts all attempts; batting excludes wides. Supported pressure percentages here require same-player evidence and therefore differ from the earlier population-wide overlap statistic.", "",
        "The coverage_ready_blend count also requires at least 80% source-opportunity retention in the same window. Passing does not certify model quality, bootstrap stability or a final top-ten list. Low coverage or unavailable change is not a poor-performance finding. No names or outcomes were used to relax thresholds. Reserved-year-only eligibility is descriptive; the full multi-year minima can leave no eligible blends in one year. Evaluate reserved prediction accuracy on all applicable events, but do not claim a validated reserved-year top-ten change ranking without the required evidence.", "",
        "## Interpretation and next execution", "",
        "Keep 70/30 and 50/50 on one common eligible cohort. Missing change remains null. Level-only evidence stays separate. Within-cell change is an adjusted descriptive association, not a causal effect; it does not extend to unsupported late overs. Freeze support during match resampling; a lost group invalidates the draw instead of silently changing its population. Selection requires at least 95% finite draws.", "",
        "Next fit the registered hierarchical historical peer baseline on 2023–2025 development folds; validate target attribution, calibration, backoff and out-of-time residuals. Freeze model choice and development residual scales before reserved model evaluation. Keep the 20 fold/setting budget, 1,000 whole-match resamples and unchanged pressure thresholds. The optional explorer remains deferred and the organiser clarification unsent.", ""]))
    if fingerprints(root / "6af3166e7b922_data_pack") != raw_hashes:
        raise ValueError("Source changed during preflight")
    save_json(out / "manifest.json", {"method_id": config["method_id"], "cutoff": config["cutoff_inclusive"],
        "source_sha256": raw_hashes, "config_sha256": sha256(config_path), "analysis_config_sha256": sha256(original_path),
        "reconciliation_manifest_sha256": sha256(source / "manifest.json"),
        "pressure_validation_manifest_sha256": sha256(validation / "manifest.json"),
        "code_sha256": {str(p.relative_to(root)): sha256(p) for p in sorted((root / "src").rglob("*.py"))},
        "lockfile_sha256": sha256(root / "uv.lock"),
        "output_sha256": {p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "manifest.json"},
        "models_fitted": False, "player_scores_created": False, "reserved_outcome_metrics_computed": False})
    print(summary.to_string(index=False))
    print(f"Report: {out / 'REPORT.md'}")
    return gate
