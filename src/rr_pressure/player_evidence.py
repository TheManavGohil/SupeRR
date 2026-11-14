"""Development-only observed evidence; no expectation fits or composite ratings."""

import json
import time

import numpy as np
import pandas as pd

from .baseline import match_draws
from .data import fingerprints, save_json, sha256, unique
from .supported_method import delivery_tables


TARGETS = ["bat_runs", "striker_wicket", "bowl_runs", "bowler_wicket"]
KEY = ["role", "player_id"]
CONTEXT = ["family", "year", "innings", "phase", "wicket_band"]
DETAILS = ["event_id", "match_id", "match_date", "year", "family", "innings", "overid",
    "wickets_before", "striker_id", "striker_name", "bowler_id", "bowler_name",
    "batter_runs", "extras_wides", "extras_noballs", "extras_byes", "extras_legbyes",
    "is_wicket", "dismissal_type", "dismissed_player_id", "is_four", "is_six",
    "late", "collapse", "tight_chase", "pressure_full", "batting_team_id", "bowling_team_id",
    "score_before", "balls_remaining", "runs_required", "required_run_rate",
    "source_pointer", "source_member", "match_accepted", "score_verified", "event_alignment_pass"]


def validate_contract(config, method):
    if (config["window"] != "development" or config["years"] != [2023, 2024, 2025] or
            config["years"] != method["development_prediction_years"] or
            config["reference_date"] != method["development_reference_date"] or
            config["project_cutoff_inclusive"] != method["cutoff_inclusive"] or
            config["recency_half_life_days"] != method["recency_half_life_days"] or
            config["supported_context_keys"] != method["context_keys"] or
            config["rate_multiplier"] != 100 or
            any(config[k] for k in ["model_fits_permitted", "composite_ratings_permitted",
                "reserved_outcomes_permitted", "full_dossier_rendering_permitted"])):
        raise ValueError("Evidence contract violates the development decision checkpoint")
    b, m = config["bootstrap"], method["bootstrap"]
    if any(b[k] != m[k] for k in ["unit", "replicates", "seed", "strata", "minimum_finite_fraction"]):
        raise ValueError("Evidence bootstrap differs from the frozen method")


def _verified_hash(path, manifest):
    if sha256(path) != manifest["output_sha256"][path.name]:
        raise ValueError("Changed upstream evidence artifact: " + path.name)


def load_evidence(root, config, method):
    """Predicates restrict mixed-year files before outcome materialization."""
    validate_contract(config, method)
    preflight = root / "reports/supported_method_2026-11-01"
    reconciled = root / "reports/full_reconciliation_2026-11-01"
    upstream = json.loads((preflight / "manifest.json").read_text())
    receipt = json.loads((reconciled / "manifest.json").read_text())
    if (upstream["config_sha256"] != sha256(root / config["method_config"]) or
            upstream["analysis_config_sha256"] != sha256(root / "configs/analysis_preregistration.json") or
            upstream["reconciliation_manifest_sha256"] != sha256(reconciled / "manifest.json") or
            upstream["source_sha256"] != fingerprints(root / "6af3166e7b922_data_pack")):
        raise ValueError("Evidence lineage differs from the frozen preflight")
    for name in ["identities_and_exposures.parquet", "features.parquet", "targets.parquet"]:
        _verified_hash(preflight / name, upstream)
    _verified_hash(reconciled / "verified_events.parquet", receipt)
    ids = pd.read_parquet(preflight / "identities_and_exposures.parquet",
        filters=[("year", "in", config["years"])])
    if ids.empty or not ids.year.isin(config["years"]).all():
        raise ValueError("Non-development identity or empty evidence window")
    event_ids = ids.event_id.tolist()
    filters = [("event_id", "in", event_ids)]
    features = pd.read_parquet(preflight / "features.parquet", filters=filters)
    targets = pd.read_parquet(preflight / "targets.parquet", columns=["event_id", *TARGETS], filters=filters)
    details = pd.read_parquet(reconciled / "verified_events.parquet", columns=DETAILS,
        filters=[("year", "in", config["years"]), ("event_id", "in", event_ids)])
    for table in [ids, features, targets, details]:
        unique(table, ["event_id"], "development evidence input")
        if set(table.event_id) != set(event_ids):
            raise ValueError("Incomplete development evidence join")
    if not (details.match_accepted & details.score_verified & details.event_alignment_pass).all():
        raise ValueError("Unverified evidence event")
    if not pd.to_datetime(ids.match_date).dt.year.eq(ids.year).all():
        raise ValueError("Evidence date/year conflict")
    if ids.match_date.gt(config["reference_date"]).any():
        raise ValueError("Future event in development evidence")
    # Independent source-to-target reproduction, rather than assuming saved targets are right.
    reproduced_features, reproduced_ids, reproduced_targets = delivery_tables(details)
    for observed, expected in [(features, reproduced_features), (ids, reproduced_ids), (targets, reproduced_targets)]:
        cols = observed.columns.tolist()
        pd.testing.assert_frame_equal(observed.sort_values("event_id").reset_index(drop=True),
            expected[cols].sort_values("event_id").reset_index(drop=True), check_dtype=False)
    extras = details.drop(columns=[c for c in details if c != "event_id" and (c in ids or c in features or c in targets)])
    data = ids.merge(features, on="event_id", validate="one_to_one").merge(
        targets, on="event_id", validate="one_to_one").merge(extras, on="event_id", validate="one_to_one")
    eligibility, cells = [], []
    for role in ["batting", "bowling"]:
        files = [f"development_{role}_players.csv", f"development_{role}_player_cells.csv"]
        for name in files:
            _verified_hash(preflight / name, upstream)
        eligibility.append(pd.read_csv(preflight / files[0], dtype={"player_id": str}))
        cells.append(pd.read_csv(preflight / files[1], dtype={"player_id": str}).assign(role=role))
    return data, pd.concat(eligibility, ignore_index=True), pd.concat(cells, ignore_index=True), upstream


def role_ledger(data, cells, config):
    rows = []
    for role, identity, name, run, wicket in [
        ("batting", "striker_id", "striker_name", "bat_runs", "striker_wicket"),
        ("bowling", "bowler_id", "bowler_name", "bowl_runs", "bowler_wicket")]:
        g = data.loc[data.batting_opportunity].copy() if role == "batting" else data.copy()
        g["role"], g["player_id"], g["player_name"] = role, g[identity], g[name]
        g["runs"], g["wickets"] = g[run], g[wicket]
        age = (pd.Timestamp(config["reference_date"]) - pd.to_datetime(g.match_date)).dt.days
        if age.lt(0).any():
            raise ValueError("Future role evidence")
        g["weight"] = np.exp2(-age / config["recency_half_life_days"])
        g["four_or_six_run_event"] = g.batter_runs.isin([4, 6]).astype(int)
        g["boundary_flag_disagrees"] = ((g.batter_runs.eq(4) != g.is_four) | (g.batter_runs.eq(6) != g.is_six)).astype(int)
        g["zero_runs"] = g.runs.eq(0).astype(int)
        g["wide_noball_runs"] = g.extras_wides + g.extras_noballs
        g["excluded_dismissal_event"] = (g.is_wicket & g.bowler_wicket.eq(0)).astype(int)
        g["own_noncredited_dismissal"] = (g.is_wicket & g.bowler_wicket.eq(0) & g.dismissed_player_id.eq(g.player_id)).astype(int)
        rows.append(g)
    result = pd.concat(rows, ignore_index=True)
    unique(result, ["event_id", "role"], "role evidence ledger")
    support = cells[KEY + CONTEXT + ["supported"]]
    unique(support, KEY + CONTEXT, "frozen evidence cells")
    result = result.merge(support, on=KEY + CONTEXT, how="left", validate="many_to_one")
    if result[KEY + ["player_name", "supported"]].isna().any().any() or result.player_id.eq("").any():
        raise ValueError("Missing evidence identity or support")
    result["weight_squared"] = result.weight ** 2
    for metric in ["runs", "wickets"]:
        result["weighted_" + metric] = result.weight * result[metric]
    return result


def summarize(ledger, keys):
    g = ledger.groupby(keys, observed=True, dropna=False, sort=True)
    result = g.agg(opportunities=("event_id", "size"), matches=("match_id", "nunique"),
        runs=("runs", "sum"), wickets=("wickets", "sum"), four_or_six_run_events=("four_or_six_run_event", "sum"),
        boundary_flag_disagreements=("boundary_flag_disagrees", "sum"),
        zero_run_opportunities=("zero_runs", "sum"), wide_noball_runs=("wide_noball_runs", "sum"),
        excluded_dismissal_events=("excluded_dismissal_event", "sum"),
        own_noncredited_dismissals=("own_noncredited_dismissal", "sum"),
        weight_sum=("weight", "sum"), weight_squared_sum=("weight_squared", "sum"),
        weighted_runs=("weighted_runs", "sum"), weighted_wickets=("weighted_wickets", "sum")).reset_index()
    result["effective_opportunities"] = result.weight_sum ** 2 / result.weight_squared_sum
    for metric in ["runs", "wickets"]:
        result[metric + "_per_100"] = 100 * result[metric] / result.opportunities
        result["weighted_" + metric + "_per_100"] = 100 * result["weighted_" + metric] / result.weight_sum
    return result


def supported_comparisons(contexts, cohort):
    """Observed within-cell differences; not approved residual-based change ratings."""
    d = contexts.loc[contexts.supported].copy()
    cols = KEY + CONTEXT
    metrics = ["opportunities", "weight_sum", "weighted_runs_per_100", "weighted_wickets_per_100"]
    p = d.loc[d.pressure_full, cols + metrics]
    o = d.loc[~d.pressure_full, cols + metrics]
    paired = p.merge(o, on=cols, how="outer", suffixes=("_pressure", "_ordinary"), validate="one_to_one", indicator=True)
    if paired._merge.ne("both").any():
        raise ValueError("Frozen supported cell lost a comparison group")
    rows = []
    for key, group in paired.groupby(KEY, sort=True):
        q = group.weight_sum_pressure / group.weight_sum_pressure.sum()
        row = dict(zip(KEY, key))
        row["supported_cells"] = len(group)
        for metric in ["runs", "wickets"]:
            for label in ["pressure", "ordinary"]:
                row[f"{metric}_{label}_per_100"] = float((q * group[f"weighted_{metric}_per_100_{label}"]).sum())
            row[f"{metric}_difference_per_100"] = row[f"{metric}_pressure_per_100"] - row[f"{metric}_ordinary_per_100"]
        rows.append(row)
    result = cohort[KEY + ["change_sample_eligible", "supported_pressure_events", "supported_pressure_matches",
        "supported_ordinary_events", "supported_ordinary_matches", "supported_pressure_fraction"]].merge(
            pd.DataFrame(rows, columns=KEY + ["supported_cells"] + [f"{m}_{label}_per_100" for m in ["runs", "wickets"]
                for label in ["pressure", "ordinary", "difference"]]), on=KEY, how="left", validate="one_to_one")
    for metric in ["runs", "wickets"]:
        result[f"headline_{metric}_difference_per_100"] = result[f"{metric}_difference_per_100"].where(result.change_sample_eligible)
    return result, paired.drop(columns="_merge")


def rate_draws(group, matches, draws):
    blocks = group.groupby("match_id")[["weight", "weighted_runs", "weighted_wickets"]].sum().reindex(matches.match_id, fill_value=0)
    den = draws @ blocks.weight.to_numpy(float)
    return {metric: np.divide(100 * (draws @ blocks["weighted_" + metric].to_numpy(float)), den,
        out=np.full(len(draws), np.nan), where=den > 0) for metric in ["runs", "wickets"]}, den


def uncertainty(ledger, cohort, config):
    """Shared whole-match descriptive intervals for sample-eligible player/roles."""
    b = config["bootstrap"]
    matches, draws = match_draws(ledger, dict(bootstrap_seed=b["seed"], bootstrap_replicates=b["replicates"], bootstrap_strata=b["strata"]))
    ready = cohort.loc[cohort.level_sample_eligible, KEY + ["change_sample_eligible"]]
    d = ledger.merge(ready, on=KEY, validate="many_to_one")
    rows = []
    for key, group in d.groupby(KEY, sort=True):
        p = group.loc[group.pressure_full]
        samples, _ = rate_draws(p, matches, draws)
        for metric, values in samples.items():
            rows.append(_interval_row(key, "pressure_rate", metric, values, b))
        if not group.change_sample_eligible.iloc[0]:
            continue
        pairs = group.loc[group.supported]
        num = {metric: np.zeros(len(draws)) for metric in samples}
        total = np.zeros(len(draws))
        valid = np.ones(len(draws), dtype=bool)
        for _, cell in pairs.groupby(CONTEXT, observed=True, sort=True):
            pressure, mass = rate_draws(cell.loc[cell.pressure_full], matches, draws)
            ordinary, ordinary_mass = rate_draws(cell.loc[~cell.pressure_full], matches, draws)
            valid &= (mass > 0) & (ordinary_mass > 0)
            total += mass
            for metric in samples:
                num[metric] += mass * np.nan_to_num(pressure[metric] - ordinary[metric])
        for metric in samples:
            values = np.divide(num[metric], total, out=np.full(len(draws), np.nan), where=valid & (total > 0))
            rows.append(_interval_row(key, "supported_difference", metric, values, b))
    return pd.DataFrame(rows), matches, draws


def _interval_row(key, estimand, metric, values, bootstrap):
    finite = values[np.isfinite(values)]
    fraction = len(finite) / len(values)
    reliable = fraction >= bootstrap["minimum_finite_fraction"]
    lo, hi = np.quantile(finite, bootstrap["interval_quantiles"]) if reliable else (np.nan, np.nan)
    return dict(zip(KEY, key), estimand=estimand, metric=metric, p10=lo, p90=hi,
        finite_fraction=fraction, interval_reliable=reliable, composite_selection_score=False)


def validate_tables(data, ledger, cohort, contexts, config):
    counts = dict(events=len(data), matches=data.match_id.nunique())
    for role, g in ledger.groupby("role"):
        counts[role + "_opportunities"] = len(g)
        counts[role + "_pressure_opportunities"] = int(g.pressure_full.sum())
        c = cohort.loc[cohort.role.eq(role)].set_index("player_id")
        for flag, label in [(c.level_sample_eligible, "level_eligible"),
            (c.level_sample_eligible & c.coverage_ready, "level_coverage_ready"),
            (c.unqualified_shortlist_evidence_ready, "blend_coverage_ready")]:
            counts[role + "_" + label] = int(flag.sum())
        for prefix, part in [("retained_", g), ("pressure_", g.loc[g.pressure_full]),
            ("supported_pressure_", g.loc[g.pressure_full & g.supported]),
            ("supported_ordinary_", g.loc[~g.pressure_full & g.supported])]:
            actual = part.groupby("player_id").agg(events=("event_id", "size"), matches=("match_id", "nunique"), weight_sum=("weight", "sum"))
            for metric in actual.columns:
                if not np.allclose(actual[metric].reindex(c.index, fill_value=0), c[prefix + metric], atol=1e-9, rtol=1e-12):
                    raise ValueError("Dossier/preflight cohort mismatch: " + role + " " + prefix + metric)
    if counts != config["expected"]:
        raise ValueError("Frozen evidence count mismatch: " + str(counts))
    if int(contexts.opportunities.sum()) != len(ledger):
        raise ValueError("Context aggregation lost opportunities")
    if not ledger.pressure_full.eq(ledger.late | ledger.collapse | ledger.tight_chase).all():
        raise ValueError("Pressure reasons disagree with frozen flag")
    if ((contexts.phase.eq("16-20")) & ~contexts.pressure_full).any():
        raise ValueError("Unexpected ordinary late-over controls")
    return counts


def pressure_peer_support(ledger, method):
    """Outcome-free feasibility of a proposed descriptive leave-player-out benchmark."""
    rows = []
    for key, g in ledger.loc[ledger.pressure_full].groupby(["role"] + CONTEXT, observed=True, sort=True):
        for player, own in g.groupby("player_id", sort=True):
            other = g.loc[g.player_id.ne(player)]
            rows.append(dict(zip(["role"] + CONTEXT, key), player_id=player,
                pressure_events=len(own), pressure_weight=own.weight.sum(),
                other_player_events=len(other), other_player_matches=other.match_id.nunique()))
    result = pd.DataFrame(rows)
    result["peer_supported"] = (result.other_player_events.ge(method["peer_minimum_events_per_group"]) &
        result.other_player_matches.ge(method["peer_minimum_matches_per_group"]))
    return result


def decision_summary(cohort, intervals, peer_support):
    rows = []
    for role, players in cohort.groupby("role", sort=True):
        eligible = players.loc[players.level_sample_eligible]
        ready = eligible.loc[eligible.coverage_ready]
        change = intervals.loc[intervals.role.eq(role) & intervals.estimand.eq("supported_difference")].drop_duplicates("player_id")
        pressure = intervals.loc[intervals.role.eq(role) & intervals.estimand.eq("pressure_rate")].drop_duplicates("player_id")
        audit = peer_support.loc[peer_support.role.eq(role)].copy()
        audit["supported_events"] = audit.pressure_events.where(audit.peer_supported, 0)
        retention = audit.groupby("player_id").agg(total=("pressure_events", "sum"), supported=("supported_events", "sum"))
        retention["fraction"] = retention.supported / retention.total
        retention = retention.reindex(ready.player_id)
        rows.append(dict(role=role, level_sample_eligible=len(eligible), level_and_coverage_ready=len(ready),
            blend_and_coverage_ready=int(players.unqualified_shortlist_evidence_ready.sum()),
            change_sample_eligible=int(players.change_sample_eligible.sum()),
            change_interval_reliable=int(change.interval_reliable.sum()),
            change_finite_fraction_min=float(change.finite_fraction.min()),
            change_finite_fraction_median=float(change.finite_fraction.median()),
            change_finite_fraction_max=float(change.finite_fraction.max()),
            pressure_interval_reliable=int(pressure.interval_reliable.sum()),
            median_supported_ordinary_comparison_fraction=float(eligible.supported_pressure_fraction.median()),
            no_supported_ordinary_comparison=int(eligible.supported_pressure_events.eq(0).sum()),
            pressure_peer_coverage_min=float(retention.fraction.min()),
            pressure_peer_coverage_atleast_80_percent=int(retention.fraction.ge(.8).sum())))
    return rows


def build_player_evidence(root):
    start = time.monotonic()
    config_path = root / "configs/player_evidence_v1.json"
    config = json.loads(config_path.read_text())
    method = json.loads((root / config["method_config"]).read_text())
    gates = [root / "reports" / directory / "model_gate.json" for directory in [
        "baseline_development_2026-11-01", "context_baseline_v2_2026-11-01", "retrospective_reference_development_2026-11-01"]]
    gate_hashes = {str(p.relative_to(root)): sha256(p) for p in gates}
    data, cohort, cells, upstream = load_evidence(root, config, method)
    ledger = role_ledger(data, cells, config)
    contexts = summarize(ledger, KEY + CONTEXT + ["pressure_full", "supported"])
    counts = validate_tables(data, ledger, cohort, contexts, config)
    comparison, paired = supported_comparisons(contexts, cohort)
    intervals, matches, draws = uncertainty(ledger, cohort, config)
    peer_support = pressure_peer_support(ledger, method)
    decision = decision_summary(cohort, intervals, peer_support)
    out = root / "reports/player_evidence_development_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    # Names are labels only; expose aliases instead of merging people by name.
    labels = ledger[KEY + ["player_name"]].drop_duplicates().sort_values(KEY + ["player_name"])
    labels.to_csv(out / "name_aliases.csv", index=False)
    collisions = labels.groupby(["role", "player_name"]).player_id.nunique().rename("distinct_player_ids").reset_index()
    labels.merge(collisions.loc[collisions.distinct_player_ids.gt(1)], on=["role", "player_name"], validate="many_to_one").to_csv(
        out / "name_label_collisions.csv", index=False)
    labels = labels.groupby(KEY).agg(player_name=("player_name", "first"), name_alias_count=("player_name", "nunique")).reset_index()
    cohort = cohort.merge(labels, on=KEY, how="left", validate="one_to_one")
    cohort.to_csv(out / "cohort_register.csv", index=False)
    comparison.to_parquet(out / "supported_comparisons.parquet", index=False)
    paired.to_parquet(out / "supported_cell_comparisons.parquet", index=False)
    contexts.to_parquet(out / "player_context_summary.parquet", index=False)
    summarize(ledger, KEY + ["pressure_full"]).to_csv(out / "player_observed_summary.csv", index=False)
    summarize(ledger, KEY + ["year", "family", "pressure_full"]).to_csv(out / "player_season_summary.csv", index=False)
    summarize(ledger, KEY + ["match_id", "match_date", "family", "year", "innings", "pressure_full"]).to_parquet(out / "player_match_ledger.parquet", index=False)
    ledger.to_parquet(out / "event_role_ledger.parquet", index=False)
    intervals.to_parquet(out / "observed_uncertainty.parquet", index=False)
    peer_support.to_csv(out / "pressure_peer_support.csv", index=False)
    save_json(out / "decision_evidence_summary.json", decision)
    issues = data.loc[(data.batter_runs.eq(4) != data.is_four) | (data.batter_runs.eq(6) != data.is_six),
        ["event_id", "match_id", "match_date", "batter_runs", "is_four", "is_six", "source_pointer"]]
    issues.to_csv(out / "boundary_annotation_disagreements.csv", index=False)
    matches.to_csv(out / "bootstrap_matches.csv", index=False)
    np.save(out / "bootstrap_multiplicities.npy", draws, allow_pickle=False)
    summary = dict(counts, validated_initial_tables=True, decision_checkpoint_reached=True,
        models_fitted=False, player_composite_scores_created=False, reserved_outcomes_read=False,
        dossier_cards_created=False, rating_method_amended=False)
    save_json(out / "validation.json", summary)
    (out / "REPORT.md").write_text("\n".join(["# Initial observed player evidence tables", "",
        "Window: 2023–2025 only. Reference date: 31 December 2025. Project cutoff: 1 November 2026.", "",
        "Development event counts, per-player exposure, pressure/support and recency sums reproduce the frozen preflight.",
        "Saved targets independently reproduce verified source attribution. Rates are per 100 analytical opportunities, not official economy or strike rate.",
        "Runs and wickets remain separate. Ordinary comparisons use original supported same-year cells; unavailable headline change stays missing.",
        "Four/six-run events are not labelled verified boundaries. Supplied boundary-flag discrepancies and shared name labels have separate audit files; identities are not merged by name.",
        "Intervals use 1,000 shared whole-match draws, conditional on retained matches and fixed support; they do not cover missing data or contextual confounding.", "",
        "**Checkpoint reached: make the rating-method recommendation before rendering the full dossier pack.**", "",
        "See `decision_evidence_summary.json` for anonymous cohort/uncertainty findings and `pressure_peer_support.csv` for outcome-free feasibility of a proposed peer benchmark. Feasibility does not validate ratings.", "",
        "No model fits, composite ratings, reserved outcome evaluation, dossier cards or rating amendment were created.", ""]))
    if gate_hashes != {str(p.relative_to(root)): sha256(p) for p in gates}:
        raise ValueError("Evidence generation changed an existing model gate")
    save_json(out / "manifest.json", dict(evidence_id=config["evidence_id"], config_sha256=sha256(config_path),
        method_config_sha256=sha256(root / config["method_config"]),
        preflight_manifest_sha256=sha256(root / "reports/supported_method_2026-11-01/manifest.json"),
        source_sha256=upstream["source_sha256"], development_years=config["years"],
        reference_date=config["reference_date"], models_fitted=False, new_model_bundles=0,
        player_composite_scores_created=False, reserved_outcomes_read=False, dossier_cards_created=False,
        preserved_gate_sha256=gate_hashes,
        code_sha256={str(p.relative_to(root)): sha256(p) for p in [root / "src/rr_pressure" / name for name in
            ["player_evidence.py", "baseline.py", "supported_method.py", "data.py", "cli.py"]]},
        output_sha256={p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "manifest.json"},
        elapsed_seconds=round(time.monotonic() - start, 2)))
    print(json.dumps(summary, indent=2))
