"""Exploratory review of saved reference errors; no model fitting or scoring."""

import json
import time

import numpy as np
import pandas as pd

from .baseline import TARGETS, match_draws
from .data import fingerprints, save_json, sha256, unique
from .pilot_report import markdown_table
from .reference_audit import CONTEXT


CELL = ["year", "family", "innings", "phase"]
GROUP = ["evaluation_fold", *CELL, "target"]


def distribution_distance(group, column):
    """Opportunity-weighted total variation; descriptive, without a pass cutoff."""
    shares = []
    for fold in [0, 1]:
        x = group.loc[group.evaluation_fold.eq(fold), column]
        shares.append(x.value_counts(normalize=True, dropna=False))
    if any(x.empty for x in shares):
        return np.nan
    index = shares[0].index.union(shares[1].index)
    return float((shares[0].reindex(index, fill_value=0) - shares[1].reindex(index, fill_value=0)).abs().sum() / 2)


def match_influence(group, tolerance):
    """Remove each evaluation match from a mean, keeping all predictions fixed."""
    blocks = group.groupby("match_id").agg(events=("residual", "size"), total=("residual", "sum"))
    n, total = len(group), float(group.residual.sum())
    bias = total / n
    remaining = n - blocks.events.to_numpy()
    deleted = np.divide(total - blocks.total.to_numpy(), remaining,
        out=np.full(len(blocks), np.nan), where=remaining > 0)
    finite = deleted[np.isfinite(deleted)]
    abs_total = float(blocks.total.abs().sum())
    sign = np.sign(bias)
    return dict(matches=len(blocks), largest_match_exposure_fraction=float(blocks.events.max() / n),
        largest_match_absolute_residual_share=float(blocks.total.abs().max() / abs_total) if abs_total else 0.,
        matches_with_same_bias_sign_fraction=float(np.mean(np.sign(blocks.total) == sign)),
        deleted_match_min_bias=float(finite.min()) if len(finite) else np.nan,
        deleted_match_max_bias=float(finite.max()) if len(finite) else np.nan,
        all_match_deletions_keep_sign=bool(len(finite) == len(blocks) and (finite * sign > 0).all()),
        all_match_deletions_above_tolerance=bool(len(finite) == len(blocks) and (finite * sign > tolerance).all()))


def attach_reference_components(predictions, models):
    """Read raw cell means from saved model tables, without producing new forecasts."""
    pieces = []
    for (fold, target), group in predictions.groupby(["evaluation_fold", "target"], sort=True):
        table = pd.DataFrame(models[int(fold)]["targets"][target]["levels"][-1]["cells"])
        unique(table, CONTEXT, "saved finest reference cells")
        table["saved_raw_cell_mean"] = table.total / table["count"]
        d = group.merge(table[CONTEXT + ["saved_raw_cell_mean", "expectation"]],
            on=CONTEXT, how="left", validate="many_to_one")
        if d.saved_raw_cell_mean.isna().any() or not np.allclose(d.expectation, d.prediction, atol=1e-12, rtol=0):
            raise ValueError("Saved finest reference does not match evaluated predictions")
        d["within_cell_partition_gap"] = d.outcome - d.saved_raw_cell_mean
        d["registered_shrinkage_component"] = d.saved_raw_cell_mean - d.prediction
        if not np.allclose(d.within_cell_partition_gap + d.registered_shrinkage_component,
                           d.residual, atol=1e-12, rtol=0):
            raise ValueError("Reference-error decomposition does not reconcile")
        pieces.append(d.drop(columns="expectation"))
    return pd.concat(pieces, ignore_index=True)


def context_diagnostics(predictions, calibration, validation):
    rows = []
    flags = calibration.loc[calibration.resolution.eq("year_family_innings_phase"),
        GROUP + ["material_alert", "enough_evidence", "mean_bias", "p10", "p90"]].copy()
    unique(flags, GROUP, "saved context calibration")
    for key, g in predictions.groupby(GROUP, observed=True, sort=True):
        target = key[-1]
        rows.append(dict(zip(GROUP, key)) | dict(events=len(g), pressure_events=int(g.pressure_full.sum()),
            observed_mean=float(g.outcome.mean()), predicted_mean=float(g.prediction.mean()),
            reproduced_bias=float(g.residual.mean()),
            within_cell_partition_gap=float(g.within_cell_partition_gap.mean()),
            registered_shrinkage_component=float(g.registered_shrinkage_component.mean()),
            finest_supported_fraction=float(g.finest_supported.mean()),
            median_own_cell_weight=float(g.own_cell_weight.median()),
            reference_majority_one_match_events=int(g.maximum_reference_match_fraction.gt(.5).sum()),
            **match_influence(g, validation["material_mean_bias"][TARGETS[target][1]])))
    result = pd.DataFrame(rows).merge(flags, on=GROUP, how="outer", validate="one_to_one", indicator=True)
    if result._merge.ne("both").any() or not np.allclose(result.reproduced_bias, result.mean_bias, atol=1e-12, rtol=0):
        raise ValueError("Saved calibration cohort or mean differs")
    return result.drop(columns="_merge")


def bootstrap_means(group, matches, weights):
    blocks = group.groupby("match_id").agg(events=("outcome", "size"), total=("outcome", "sum"))
    blocks = blocks.reindex(matches.match_id, fill_value=0)
    den = weights @ blocks.events.to_numpy(dtype=float)
    num = weights @ blocks.total.to_numpy(dtype=float)
    return np.divide(num, den, out=np.full(len(weights), np.nan), where=den > 0)


def paired_contexts(predictions, diagnostics, validation):
    """Both-partition uncertainty concerns raw means, not a replacement gate."""
    matches, weights = match_draws(predictions, validation)
    first = diagnostics.loc[diagnostics.evaluation_fold.eq(0)].drop(columns="evaluation_fold")
    second = diagnostics.loc[diagnostics.evaluation_fold.eq(1)].drop(columns="evaluation_fold")
    pairs = first.merge(second, on=CELL + ["target"], suffixes=("_0", "_1"), validate="one_to_one")
    if len(pairs) * 2 != len(diagnostics):
        raise ValueError("A context lacks a complete evaluation partition")
    pairs["any_alert"] = pairs.material_alert_0 | pairs.material_alert_1
    pairs["both_alert"] = pairs.material_alert_0 & pairs.material_alert_1
    pairs["opposite_bias_signs"] = pairs.mean_bias_0 * pairs.mean_bias_1 < 0
    den = pairs.events_0 + pairs.events_1
    pairs["pooled_bias"] = (pairs.events_0 * pairs.mean_bias_0 + pairs.events_1 * pairs.mean_bias_1) / den
    absolute = (pairs.events_0 * pairs.mean_bias_0.abs() + pairs.events_1 * pairs.mean_bias_1.abs()) / den
    pairs["cancellation_fraction"] = 1 - np.divide(pairs.pooled_bias.abs(), absolute,
        out=np.full(len(pairs), np.nan), where=absolute > 0)
    rows = []
    for key, g in predictions.groupby(CELL + ["target"], observed=True, sort=True):
        zero, one = g.loc[g.evaluation_fold.eq(0)], g.loc[g.evaluation_fold.eq(1)]
        delta = bootstrap_means(zero, matches, weights) - bootstrap_means(one, matches, weights)
        finite = delta[np.isfinite(delta)]
        p10, p90 = np.quantile(finite, [.1, .9]) if len(finite) else (np.nan, np.nan)
        teams = pd.concat([g[["evaluation_fold", "home_team_id"]].rename(columns={"home_team_id": "team_id"}),
                           g[["evaluation_fold", "away_team_id"]].rename(columns={"away_team_id": "team_id"})])
        rows.append(dict(zip(CELL + ["target"], key)) | dict(
            raw_partition_mean_gap=float(zero.outcome.mean() - one.outcome.mean()),
            raw_gap_joint_p10=float(p10), raw_gap_joint_p90=float(p90), raw_gap_finite_draws=len(finite),
            raw_gap_joint_interval_excludes_zero=bool(p10 > 0 or p90 < 0),
            wicket_band_distribution_distance=distribution_distance(g, "wicket_band"),
            venue_country_distribution_distance=distribution_distance(g, "venue_country"),
            month_distribution_distance=distribution_distance(g, "month"),
            team_involvement_distribution_distance=distribution_distance(teams, "team_id")))
    return pairs.merge(pd.DataFrame(rows), on=CELL + ["target"], validate="one_to_one")


def exposure_flags(predictions, diagnostics):
    """Role unions prevent the same delivery's run/wicket alert being counted twice."""
    flags = diagnostics[GROUP + ["material_alert"]]
    both = flags.groupby(CELL + ["target"], observed=True).material_alert.max().rename("either_fold_alert").reset_index()
    d = predictions.merge(flags, on=GROUP, validate="many_to_one").merge(both,
        on=CELL + ["target"], validate="many_to_one")
    id_keys = ["event_id", "match_id", "match_date", "year", "family", "innings", "phase", "evaluation_fold", "role", "pressure_full"]
    return d.groupby(id_keys, observed=True, dropna=False).agg(
        own_fold_alert=("material_alert", "max"), either_fold_alert=("either_fold_alert", "max")).reset_index()


def exposure_tables(events, identities, eligibility):
    summary = []
    for resolution, keys in [("overall", ["role"]), ("family_phase", ["role", "family", "phase"]),
                             ("year_family", ["role", "year", "family"])]:
        for key, g in events.groupby(keys, sort=True):
            key = key if isinstance(key, tuple) else (key,)
            for exposure in ["all", "pressure"]:
                part = g.loc[g.pressure_full] if exposure == "pressure" else g
                summary.append(dict(resolution=resolution, **dict(zip(keys, key)), exposure=exposure,
                    events=len(part), own_fold_alert_events=int(part.own_fold_alert.sum()),
                    either_fold_alert_events=int(part.either_fold_alert.sum()),
                    own_fold_alert_fraction=float(part.own_fold_alert.mean()) if len(part) else np.nan,
                    either_fold_alert_fraction=float(part.either_fold_alert.mean()) if len(part) else np.nan))
    player_rows, cohort_rows = [], []
    for role, column in [("batting", "striker_id"), ("bowling", "bowler_id")]:
        d = events.loc[events.role.eq(role) & events.pressure_full].merge(
            identities[["event_id", column]].rename(columns={column: "player_id"}), on="event_id", how="left", validate="one_to_one")
        if d.player_id.isna().any():
            raise ValueError("Missing pressure-exposure identity")
        players = d.groupby("player_id").agg(pressure_events=("event_id", "size"),
            own_fold_alert_events=("own_fold_alert", "sum"), either_fold_alert_events=("either_fold_alert", "sum")).reset_index()
        players["own_fold_alert_fraction"] = players.own_fold_alert_events / players.pressure_events
        players["either_fold_alert_fraction"] = players.either_fold_alert_events / players.pressure_events
        eligible = eligibility[role]
        unique(eligible, ["player_id"], "development exposure eligibility")
        players = players.merge(eligible[["player_id", "level_sample_eligible", "coverage_ready", "unqualified_shortlist_evidence_ready"]],
                                on="player_id", how="left", validate="one_to_one")
        if players.level_sample_eligible.isna().any():
            raise ValueError("Missing eligibility mapping")
        players["role"] = role
        player_rows.append(players)
        for label, mask in [("level_sample", players.level_sample_eligible),
                            ("level_and_coverage", players.level_sample_eligible & players.coverage_ready),
                            ("blend_and_coverage", players.unqualified_shortlist_evidence_ready)]:
            g = players.loc[mask]
            cohort_rows.append(dict(role=role, cohort=label, players=len(g),
                players_with_any_own_fold_alert=int(g.own_fold_alert_events.gt(0).sum()),
                players_with_any_either_fold_alert=int(g.either_fold_alert_events.gt(0).sum()),
                median_own_fold_alert_fraction=float(g.own_fold_alert_fraction.median()) if len(g) else np.nan,
                median_either_fold_alert_fraction=float(g.either_fold_alert_fraction.median()) if len(g) else np.nan,
                minimum_either_fold_alert_fraction=float(g.either_fold_alert_fraction.min()) if len(g) else np.nan))
    return pd.DataFrame(summary), pd.concat(player_rows, ignore_index=True), pd.DataFrame(cohort_rows)


def load_review(root):
    source = root / "reports/retrospective_reference_development_2026-11-01"
    m = json.loads((source / "manifest.json").read_text())
    config = root / "configs/retrospective_reference_v1.json"
    validation = root / "configs/baseline_validation_v1.json"
    preflight = root / "reports/supported_method_2026-11-01"
    if (m["reference_config_sha256"] != sha256(config) or m["validation_config_sha256"] != sha256(validation) or
            m["preflight_manifest_sha256"] != sha256(preflight / "manifest.json") or
            m["source_sha256"] != fingerprints(root / "6af3166e7b922_data_pack")):
        raise ValueError("Review input lineage changed")
    for name in ["development_predictions.parquet", "fold_calibration.csv", "model_gate.json", "models_fold_0.json", "models_fold_1.json"]:
        if m["output_sha256"][name] != sha256(source / name):
            raise ValueError("Saved reference artifact changed: " + name)
    predictions = pd.read_parquet(source / "development_predictions.parquet")
    if not predictions.year.isin([2023, 2024, 2025]).all() or not predictions.evaluation_fold.ne(predictions.training_fold).all():
        raise ValueError("Nondevelopment or same-partition predictions")
    unique(predictions, ["event_id", "target"], "review predictions")
    models = {f: json.loads((source / f"models_fold_{f}.json").read_text()) for f in [0, 1]}
    calibration = pd.read_csv(source / "fold_calibration.csv")
    p = json.loads((preflight / "manifest.json").read_text())
    names = ["identities_and_exposures.parquet", "development_batting_players.csv", "development_bowling_players.csv"]
    for name in names:
        if p["output_sha256"][name] != sha256(preflight / name):
            raise ValueError("Exposure artifact changed: " + name)
    ids = sorted(predictions.event_id.unique())
    identities = pd.read_parquet(preflight / names[0], columns=["event_id", "striker_id", "bowler_id"],
        filters=[("event_id", "in", ids)])
    unique(identities, ["event_id"], "review exposure identities")
    if set(identities.event_id) != set(ids):
        raise ValueError("Incomplete exposure identities")
    eligibility = {role: pd.read_csv(preflight / f"development_{role}_players.csv", dtype={"player_id": str})
                   for role in ["batting", "bowling"]}
    # Metadata only: result, player-of-match and revised targets are not read.
    meta = pd.read_csv(root / "6af3166e7b922_data_pack/matches.csv", dtype=str,
        usecols=["match_id", "venue_country", "home_team_id", "away_team_id"], keep_default_na=False)
    meta = meta.loc[meta.match_id.isin(predictions.match_id)]
    unique(meta, ["match_id"], "review match metadata")
    predictions = predictions.merge(meta, on="match_id", how="left", validate="many_to_one")
    if predictions.venue_country.isna().any():
        raise ValueError("Missing match metadata")
    predictions["month"] = predictions.match_date.str[:7]
    return predictions, calibration, models, identities, eligibility, json.loads(validation.read_text()), m


def run_reference_review(root):
    start = time.perf_counter()
    predictions, calibration, models, identities, eligibility, validation, upstream = load_review(root)
    d = attach_reference_components(predictions, models)
    diagnostics = context_diagnostics(d, calibration, validation)
    pairs = paired_contexts(d, diagnostics, validation)
    events = exposure_flags(d, diagnostics)
    exposure, players, cohorts = exposure_tables(events, identities, eligibility)
    alerts = diagnostics.loc[diagnostics.material_alert]
    alert_pairs = pairs.loc[pairs.any_alert]
    summary = dict(development_matches=predictions.match_id.nunique(), delivery_events=predictions.event_id.nunique(),
        saved_fold_alerts=len(alerts), alerted_target_contexts=len(alert_pairs),
        alerted_physical_contexts=len(alert_pairs[CELL].drop_duplicates()),
        total_physical_contexts=len(pairs[CELL].drop_duplicates()),
        both_folds_alert_target_contexts=int(alert_pairs.both_alert.sum()),
        alerted_target_contexts_with_opposite_bias_signs=int(alert_pairs.opposite_bias_signs.sum()),
        median_cancellation_fraction=float(alert_pairs.cancellation_fraction.median()),
        alerts_persistent_above_tolerance_after_any_single_match_deletion=int(alerts.all_match_deletions_above_tolerance.sum()),
        alerts_within_cell_gap_larger_than_shrinkage=int((alerts.within_cell_partition_gap.abs() > alerts.registered_shrinkage_component.abs()).sum()),
        alerted_target_contexts_joint_raw_gap_interval_excludes_zero=int(alert_pairs.raw_gap_joint_interval_excludes_zero.sum()),
        minimum_joint_raw_gap_finite_draws=int(pairs.raw_gap_finite_draws.min()),
        new_model_bundles_used=0, cumulative_model_bundles=upstream["cumulative_model_bundles"],
        reserved_outcomes_read=False, player_performance_scores_created=False, promotion_gate_changed=False,
        reference_promoted=False)
    out = root / "reports/reference_instability_review_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    for name, table in dict(context_diagnostics=diagnostics, paired_contexts=pairs,
        pressure_exposure=exposure, player_exposure_only=players, eligible_cohort_exposure=cohorts).items():
        table.to_csv(out / f"{name}.csv", index=False)
    save_json(out / "review_summary.json", summary)
    from .reference_review_figures import make_review_figures
    make_review_figures(pairs, exposure, out)
    biggest = alert_pairs.assign(absolute_gap=lambda x: (x.mean_bias_0-x.mean_bias_1).abs()).sort_values("absolute_gap", ascending=False)
    cols = CELL + ["target", "mean_bias_0", "mean_bias_1", "pooled_bias", "raw_gap_joint_p10", "raw_gap_joint_p90"]
    (out / "REPORT.md").write_text("\n".join([
        "# Saved-reference instability review", "", "[Standalone review charts](INSTABILITY_REVIEW.pdf)", "",
        "Cricket question: how much pressure-selection evidence is exposed to a reference that changes with the peer matches, and is that weakness confined to isolated performances?", "",
        "This is a post hoc, development-only diagnostic review of existing predictions and saved model tables. No reference is fitted, corrected or rescored. Alert membership, thresholds, eligibility, match assignments and the failed promotion gate are preserved. All detailed player identifiers remain private; the player table contains exposure counts only, not performance, scores or rankings.", "",
        "## Scope and main findings", "", markdown_table(pd.DataFrame([summary]).T.reset_index().rename(columns={"index":"measure",0:"value"})), "",
        "A physical context is year × family × innings × phase; target contexts additionally distinguish the four outcomes. Both-fold and run/wicket alerts overlap. The 68 original alert rows must not be interpreted as 68 separate cricket situations.", "",
        "## Largest opposing reference errors", "", markdown_table(biggest[cols].head(12).round(6)), "",
        "Bias is observed minus predicted per opportunity. Pooled bias is weighted by actual evaluation opportunities. Cancellation is one minus absolute pooled bias divided by the weighted mean absolute fold bias; a value near one means strong cancellation. It is a description, not an approval threshold.", "",
        "## Pressure evidence affected", "", markdown_table(exposure.loc[exposure.resolution.eq("overall")].round(5)), "",
        markdown_table(exposure.loc[exposure.resolution.eq("family_phase") & exposure.exposure.eq("pressure")].round(5)), "",
        "Own-fold exposure counts events whose actual evaluation fold/target cell had an alert. Either-fold exposure counts events in a target context alerted in at least one fold. A role event is counted once when either its run or wicket target is affected. The broader measure indicates comparison instability, not an estimate of individual error. Neither measure may be used to drop adverse observations or construct a passed subset.", "",
        "## Existing eligibility cohorts", "", markdown_table(cohorts.round(5)), "",
        "Cohorts use the original development exposure and coverage gates, before performance scores. Fractions describe pressure exposure to affected contexts, not a player quality rating. They do not establish that an individual player's bias equals the group's mean bias. No final-window or 2026 inference is made.", "",
        "## Outlier and shrinkage checks", "",
        f"Of {len(alerts)} alerts, {summary['alerts_persistent_above_tolerance_after_any_single_match_deletion']} retain their sign and exceed the original material point-bias tolerance after removing any one evaluation match. Predictions stay fixed; this is neither reference refitting nor a re-run of the bootstrap calibration gate. The full min/max deletion biases and match concentration appear in context_diagnostics.csv.", "",
        f"In {summary['alerts_within_cell_gap_larger_than_shrinkage']} alerts, the absolute within-wicket-band partition gap exceeds the absolute registered-shrinkage component. The exact identity is mean(outcome − prediction) = mean(outcome − saved training-cell raw mean) + mean(saved training-cell raw mean − prediction). This arithmetic uses saved model tables, not an alternative prediction model. It distinguishes a peer-sample gap from the registered shrinkage contribution; neither term identifies a causal mechanism.", "",
        "## Peer composition and two-sided sampling uncertainty", "",
        "paired_contexts.csv records opportunity-weighted total-variation distances for wicket band, venue country, calendar month and teams involved in each fixture. Team involvement includes both teams equally and does not infer batting order or opposition strength. These descriptive distances have no pass cutoff and are not fitted adjustments. Differences can involve conditions, players, opponents and random sampling; the review cannot assign a causal explanation.", "",
        f"Across {len(alert_pairs)} alerted target contexts, {summary['alerted_target_contexts_joint_raw_gap_interval_excludes_zero']} have raw observed partition-mean differences whose joint 10th–90th percentile interval excludes zero. These use 1,000 shared whole-match draws within family/year with both partition means recalculated, and at least {summary['minimum_joint_raw_gap_finite_draws']} finite draws. This checks uncertainty on the raw two-sample gap. It does not reproduce the wicket-conditioned prediction-bias statistic, quantify full reference uncertainty, replace the conditional calibration screen, or permit promotion. All pairs, including unalerted contexts, are exported to prevent selective reporting.", "",
        "## Decision and next step", "",
        "Keep the failed promotion gate and all 20 used bundles unchanged. A clean pooled average cannot validate a player's contextual contribution when the reference halves disagree. Do not search for a favourable split, discard alerted phases, subtract evaluation-group errors, repurpose reserved fits or produce performance scores from this reference.", "",
        "Use the review to close the automatic model-search stage. The next concrete deliverable should be a development-only cricket evidence dossier using verified observed runs, wickets, tempo, pressure/ordinary context, match and season repeatability, source coverage and supporting/counterexample matches. It can describe performance and missing comparisons without a model-based ranking. Before final numeric ratings or 2026 outcome access, make an explicit versioned method decision: either establish a defensible reference-uncertainty procedure or adopt a transparent descriptive selection method with its limitations. This review alone authorizes neither amendment nor final selections.", ""]))
    save_json(out / "manifest.json", dict(upstream_manifest_sha256=sha256(root / "reports/retrospective_reference_development_2026-11-01/manifest.json"),
        preflight_manifest_sha256=sha256(root / "reports/supported_method_2026-11-01/manifest.json"),
        validation_config_sha256=sha256(root / "configs/baseline_validation_v1.json"),
        code_sha256={name:sha256(root / name) for name in ["src/rr_pressure/reference_review.py", "src/rr_pressure/reference_review_figures.py"]},
        models_fitted=False, player_performance_scores_created=False, reserved_outcomes_read=False,
        output_sha256={p.name:sha256(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!="manifest.json"},
        elapsed_seconds=round(time.perf_counter()-start,2)))
    print(json.dumps(summary, indent=2))
    print(f"Report: {out / 'REPORT.md'}")
    return summary
