"""Historical peer expectations and strictly out-of-time development validation."""

import json
import time

import numpy as np
import pandas as pd

from .data import fingerprints, save_json, sha256, unique
from .pilot_report import markdown_table
from .supported_method import FEATURES, chronological_folds


TARGETS = {"bat_runs": ("batting", "runs"), "striker_wicket": ("batting", "wickets"),
           "bowl_runs": ("bowling", "runs"), "bowler_wicket": ("bowling", "wickets")}


def _lookup(frame, table, keys, column):
    return frame[keys].merge(table[keys + [column]], on=keys, how="left", sort=False,
        validate="many_to_one")[column].to_numpy(dtype=float)


class HistoricalPeers:
    """Recursive count-weighted means; unseen contexts back off to their parent."""

    def __init__(self, hierarchy, prior_events):
        self.hierarchy = list(reversed(hierarchy))
        if self.hierarchy[0] != [] or self.hierarchy[-1] != FEATURES:
            raise ValueError("Unexpected predictor hierarchy")
        if any(child[:len(parent)] != parent for parent, child in zip(self.hierarchy, self.hierarchy[1:])):
            raise ValueError("Hierarchy must be nested")
        if not np.isfinite(prior_events) or prior_events <= 0:
            raise ValueError("Invalid prior strength")
        self.prior_events = prior_events

    @staticmethod
    def _validate_features(x):
        if x.columns.tolist() != FEATURES or x.isna().any().any():
            raise ValueError("Predictor allowlist or missing-context violation")

    def fit(self, x, y):
        self._validate_features(x)
        values = np.asarray(y, dtype=float)
        if len(x) != len(values) or not len(x) or not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("Invalid training targets")
        self.global_mean = float(values.mean())
        self.training_sd = float(values.std(ddof=0))
        self.training_events = len(x)
        self.tables = []
        d = x.reset_index(drop=True).assign(outcome=values)
        self.family_means = d.groupby("family", observed=True).outcome.mean().rename("family_mean").reset_index()
        for keys in self.hierarchy[1:]:
            table = d.groupby(keys, observed=True, dropna=False).outcome.agg(["sum", "count"]).reset_index()
            parent, _, _ = self._predict(table)
            table["expectation"] = (table["sum"] + self.prior_events * parent) / (table["count"] + self.prior_events)
            self.tables.append((keys, table))
        return self

    def _predict(self, x):
        means = np.full(len(x), self.global_mean)
        depth = np.zeros(len(x), dtype=int)
        counts = np.full(len(x), self.training_events, dtype=int)
        for i, (keys, table) in enumerate(self.tables, start=1):
            value = _lookup(x, table, keys, "expectation")
            count = _lookup(x, table, keys, "count")
            seen = np.isfinite(value)
            means[seen], depth[seen], counts[seen] = value[seen], i, count[seen].astype(int)
        return means, depth, counts

    def predict(self, x):
        self._validate_features(x)
        means, depth, counts = self._predict(x)
        family = _lookup(x, self.family_means, ["family"], "family_mean")
        family = np.where(np.isfinite(family), family, self.global_mean)
        return pd.DataFrame({"prediction": means, "backoff_depth": depth, "reference_events": counts,
            "global_prediction": self.global_mean, "family_prediction": family})

    def as_dict(self):
        return {"prior_events": self.prior_events, "training_events": self.training_events,
            "global_mean": self.global_mean, "training_outcome_sd": self.training_sd,
            "family_means": self.family_means.to_dict("records"),
            "levels": [{"keys": keys, "cells": table.to_dict("records")} for keys, table in self.tables]}


def fit_fold(data, year, prior, method):
    """Fold masks are defined by match dates, before any outcome is consumed."""
    if year not in method["development_prediction_years"]:
        raise ValueError("This command fits development years only")
    matches = data[["match_id", "match_date", "year"]].drop_duplicates()
    unique(matches, ["match_id"], "baseline chronology")
    if not pd.to_datetime(matches.match_date).dt.year.eq(matches.year).all():
        raise ValueError("Date/year mismatch")
    train = data.loc[data.match_date < f"{year}-01-01"]
    evaluate = data.loc[data.year.eq(year)]
    if train.empty or evaluate.empty or train.match_date.max() >= evaluate.match_date.min():
        raise ValueError("Invalid chronological split")
    if set(train.match_id) & set(evaluate.match_id):
        raise ValueError("Match leakage")
    rows, models = [], {}
    for target, (role, kind) in TARGETS.items():
        tr = train.loc[train.batting_opportunity] if role == "batting" else train
        ev = evaluate.loc[evaluate.batting_opportunity] if role == "batting" else evaluate
        if kind == "wickets" and not tr[target].isin([0, 1]).all():
            raise ValueError("Nonbinary wicket target")
        model = HistoricalPeers(method["expectation_model"]["hierarchy"], prior).fit(tr[FEATURES], tr[target])
        prediction = model.predict(ev[FEATURES])
        records = ev[["event_id", "match_id", "match_date", "year", *FEATURES, "pressure_full"]].reset_index(drop=True)
        records = pd.concat([records, prediction], axis=1)
        records["target"], records["role"], records["kind"] = target, role, kind
        records["outcome"] = ev[target].to_numpy(dtype=float)
        records["prior_events"] = prior
        records["training_scale"] = max(model.training_sd, .01 if kind == "wickets" else .05)
        records["residual"] = records.outcome - records.prediction
        records["forecast_standardized_residual"] = records.residual / records.training_scale
        records["training_last_date"] = train.match_date.max()
        if not np.isfinite(records[["prediction", "outcome", "training_scale"]].to_numpy()).all():
            raise ValueError("Nonfinite output")
        if records.prediction.lt(0).any() or (kind == "wickets" and not records.prediction.between(0, 1).all()):
            raise ValueError("Prediction domain violation")
        rows.append(records)
        models[target] = model.as_dict()
    return pd.concat(rows, ignore_index=True), models


def metrics(predictions, config):
    rows = []
    for (prior, year, target), group in predictions.groupby(["prior_events", "year", "target"], sort=True):
        y = group.outcome.to_numpy()
        for label, col in [("hierarchical", "prediction"), ("global", "global_prediction"), ("family", "family_prediction")]:
            p = group[col].to_numpy()
            binary = TARGETS[target][1] == "wickets"
            clipped = np.clip(p, config["log_loss_probability_clip"], 1 - config["log_loss_probability_clip"])
            rows.append(dict(prior_events=prior, year=year, target=target, model=label, events=len(group),
                primary_loss=float(np.mean((y - p) ** 2)), primary_loss_name="Brier" if binary else "MSE",
                mae=float(np.mean(np.abs(y - p))) if not binary else np.nan,
                log_loss=float(np.mean(-y * np.log(clipped) - (1 - y) * np.log1p(-clipped))) if binary else np.nan,
                mean_bias=float(np.mean(y - p)), observed_mean=float(y.mean()), predicted_mean=float(p.mean())))
    return pd.DataFrame(rows)


def pooled_metrics(annual):
    values = ["primary_loss", "mae", "log_loss", "mean_bias", "observed_mean", "predicted_mean"]
    rows = []
    for (prior, target, model), group in annual.groupby(["prior_events", "target", "model"]):
        row = dict(prior_events=prior, target=target, model=model, events=int(group.events.sum()))
        row.update({c: float(np.average(group[c], weights=group.events)) for c in values})
        rows.append(row)
    return pd.DataFrame(rows)


def match_draws(predictions, config):
    """One common match-multiplicity matrix for every target and subgroup."""
    matches = predictions[["match_id", "family", "year"]].drop_duplicates().sort_values("match_id").reset_index(drop=True)
    unique(matches, ["match_id"], "bootstrap match strata")
    rng = np.random.default_rng(config["bootstrap_seed"])
    weights = np.zeros((config["bootstrap_replicates"], len(matches)), dtype=np.int16)
    for _, group in matches.groupby(config["bootstrap_strata"], sort=True):
        positions = group.index.to_numpy()
        weights[:, positions] = rng.multinomial(len(positions), np.full(len(positions), 1 / len(positions)), size=len(weights))
    return matches, weights


def _interval(group, value, matches, weights):
    blocks = group.assign(_value=np.asarray(value)).groupby("match_id").agg(n=("event_id", "size"), total=("_value", "sum"))
    blocks = blocks.reindex(matches.match_id, fill_value=0)
    denominator = weights @ blocks.n.to_numpy(dtype=float)
    numerator = weights @ blocks.total.to_numpy(dtype=float)
    draws = np.divide(numerator, denominator, out=np.full(len(weights), np.nan), where=denominator > 0)
    finite = draws[np.isfinite(draws)]
    return (float(np.quantile(finite, .1)), float(np.quantile(finite, .9)), len(finite)) if len(finite) else (np.nan, np.nan, 0)


def diagnostic_tables(default, config):
    matches, weights = match_draws(default, config)
    comparisons, calibration, reliability, backoff = [], [], [], []
    for target, group in default.groupby("target"):
        for comparator, column in [("global", "global_prediction"), ("family", "family_prediction")]:
            delta = (group.outcome - group.prediction) ** 2 - (group.outcome - group[column]) ** 2
            low, high, finite = _interval(group, delta, matches, weights)
            base = float(np.mean((group.outcome - group[column]) ** 2))
            comparisons.append(dict(target=target, comparator=comparator, primary_loss_delta=float(delta.mean()),
                relative_improvement_percent=float(-100 * delta.mean() / base) if base else np.nan,
                p10=low, p90=high, finite_replicates=finite, bootstrap_unit="whole_match"))
        backoff.append(dict(target=target, events=len(group), unseen_finest_context_events=int(group.backoff_depth.lt(4).sum()),
            global_fallback_events=int(group.backoff_depth.eq(0).sum()),
            minimum_reference_events=int(group.reference_events.min())))
        if TARGETS[target][1] == "wickets":
            binned = group.assign(probability_bin=pd.cut(group.prediction, config["reliability_bin_edges"], include_lowest=True))
            for bucket, part in binned.groupby("probability_bin", observed=True):
                reliability.append(dict(target=target, probability_bin=str(bucket), events=len(part), matches=part.match_id.nunique(),
                    predicted=float(part.prediction.mean()), observed=float(part.outcome.mean())))
        # Role-relevant marginal pressure diagnostics are descriptive, not causal.
        for resolution, keys in [("overall", []), ("year_family_innings_phase", config["calibration_groups"]),
                                  ("pressure", ["pressure_full"])]:
            groups = [((), group)] if not keys else group.groupby(keys, observed=True, dropna=False)
            for key, part in groups:
                if not isinstance(key, tuple):
                    key = (key,)
                low, high, finite = _interval(part, part.residual, matches, weights)
                supported = len(part) >= config["minimum_calibration_events"] and part.match_id.nunique() >= config["minimum_calibration_matches"]
                threshold = config["material_mean_bias"][TARGETS[target][1]]
                bias = float(part.residual.mean())
                alert = supported and abs(bias) > threshold and (low > 0 or high < 0)
                calibration.append(dict(target=target, resolution=resolution, **dict(zip(keys, key)),
                    events=len(part), matches=part.match_id.nunique(), predicted_mean=float(part.prediction.mean()),
                    observed_mean=float(part.outcome.mean()), mean_bias=bias, p10=low, p90=high,
                    finite_replicates=finite, enough_evidence=supported, material_alert=alert))
    return {"paired_loss_comparisons": pd.DataFrame(comparisons), "calibration": pd.DataFrame(calibration),
        "reliability": pd.DataFrame(reliability), "backoff": pd.DataFrame(backoff)}


def development_gate(annual, pooled, calibration, config):
    checks = []
    prior = config["default_prior_events"]
    for target in TARGETS:
        p = pooled.loc[pooled.prior_events.eq(prior) & pooled.target.eq(target)].set_index("model")
        y = annual.loc[annual.prior_events.eq(prior) & annual.target.eq(target)].pivot(index="year", columns="model", values="primary_loss")
        passing = int((y.hierarchical <= y["global"]).sum())
        checks.append(dict(target=target, pooled_beats_global=bool(p.loc["hierarchical", "primary_loss"] <= p.loc["global", "primary_loss"]),
            pooled_beats_family=bool(p.loc["hierarchical", "primary_loss"] <= p.loc["family", "primary_loss"]),
            years_no_worse_than_global=passing, annual_gate=passing >= config["minimum_passing_years"]))
    benchmark_pass = all(x["pooled_beats_global"] and x["pooled_beats_family"] and x["annual_gate"] for x in checks)
    alerts = int(calibration.material_alert.sum())
    return {"models_fitted": True, "default_prior_events": prior, "default_changed": False,
        "benchmark_checks": checks, "benchmark_gate_passed": benchmark_pass, "material_calibration_alerts": alerts,
        "development_prediction_contracts_passed": True, "ready_for_reserved_evaluation": benchmark_pass and alerts == 0,
        "reference_scales_frozen_for_final_ratings": benchmark_pass and alerts == 0,
        "reserved_outcome_metrics_computed": False, "player_scores_created": False, "final_rankings_permitted": False,
        "global_pressure_change_comparison_ready": False,
        "decision": "Freeze default and development reference scales for reserved evaluation." if benchmark_pass and alerts == 0 else
            "Retain baseline as a development benchmark. Review bias/benchmark failures before reserved evaluation; no automatic retuning or final rankings."}


def load_development(root, method):
    source = root / "reports/supported_method_2026-11-01"
    manifest = json.loads((source / "manifest.json").read_text())
    if manifest["config_sha256"] != sha256(root / "configs/supported_method_v1.json"):
        raise ValueError("Method configuration differs from frozen inputs")
    if manifest["analysis_config_sha256"] != sha256(root / "configs/analysis_preregistration.json"):
        raise ValueError("Original pressure configuration changed")
    if manifest["source_sha256"] != fingerprints(root / "6af3166e7b922_data_pack"):
        raise ValueError("Raw sources changed")
    for name in ["features.parquet", "identities_and_exposures.parquet", "targets.parquet", "match_folds.csv", "model_gate.json"]:
        if sha256(source / name) != manifest["output_sha256"][name]:
            raise ValueError("Preflight artifact changed: " + name)
    if not json.loads((source / "model_gate.json").read_text())["development_peer_baseline_permitted"]:
        raise ValueError("Development model fitting not permitted by preflight")
    identities = pd.read_parquet(source / "identities_and_exposures.parquet")
    folds, _ = chronological_folds(identities, method)
    recorded = pd.read_csv(source / "match_folds.csv", dtype={"match_id": str})
    sort = ["fold_year", "partition", "match_id"]
    pd.testing.assert_frame_equal(folds.sort_values(sort).reset_index(drop=True), recorded[folds.columns].sort_values(sort).reset_index(drop=True), check_dtype=False)
    # Read only warm-up and development targets. Reserved identifiers/dates above
    # are used solely to verify fold boundaries; their outcomes never enter fit.
    identities = identities.loc[identities.year.le(max(method["development_prediction_years"]))].copy()
    ids = identities.event_id.tolist()
    features = pd.read_parquet(source / "features.parquet", filters=[("event_id", "in", ids)])
    targets = pd.read_parquet(source / "targets.parquet", filters=[("event_id", "in", ids)])
    if features.columns.tolist() != ["event_id"] + FEATURES:
        raise ValueError("Feature contract changed")
    for frame in (identities, features, targets):
        unique(frame, ["event_id"], "development input")
        if set(frame.event_id) != set(ids):
            raise ValueError("Incomplete development input")
    # Focal player identities are not needed for expectation validation.
    data = identities.drop(columns=["striker_id", "bowler_id"]).merge(features, on="event_id", validate="one_to_one").merge(targets, on="event_id", validate="one_to_one")
    return data, manifest


def run_baseline(root):
    start = time.perf_counter()
    method_path = root / "configs/supported_method_v1.json"
    validation_path = root / "configs/baseline_validation_v1.json"
    method = json.loads(method_path.read_text())
    config = json.loads(validation_path.read_text())
    settings = method["expectation_model"]["prior_events_variants"]
    years = method["development_prediction_years"]
    if config["default_prior_events"] != method["expectation_model"]["prior_events_default"]:
        raise ValueError("Default must match registered method")
    if len(settings) * (len(years) + 1) > method["expectation_model"]["maximum_fold_setting_bundles"]:
        raise ValueError("Model budget exceeded")
    out = root / "reports/baseline_development_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    for filename, content in [("frozen_validation.json", config), ("frozen_method.json", method)]:
        path = out / filename
        if path.exists() and json.loads(path.read_text()) != content:
            raise ValueError("Configuration changed; version the analytical amendment")
        save_json(path, content)
    data, upstream = load_development(root, method)
    annual, defaults, fits = [], [], []
    for year in years:
        for prior in settings:
            predictions, models = fit_fold(data, year, prior, method)
            predictions.to_parquet(out / f"predictions_{year}_prior_{prior}.parquet", index=False)
            save_json(out / f"models_{year}_prior_{prior}.json", models)
            annual.append(metrics(predictions, config))
            if prior == config["default_prior_events"]:
                defaults.append(predictions)
            fits.append(dict(year=year, prior_events=prior, targets=len(TARGETS),
                training_matches=data.loc[data.match_date.lt(f"{year}-01-01"), "match_id"].nunique(),
                evaluation_matches=predictions.match_id.nunique(), prediction_rows=len(predictions)))
        print(f"Completed {year}: five registered settings, four targets each.", flush=True)
    annual = pd.concat(annual, ignore_index=True)
    pooled = pooled_metrics(annual)
    default = pd.concat(defaults, ignore_index=True)
    tables = diagnostic_tables(default, config)
    tables.update(annual_metrics=annual, pooled_metrics=pooled, fits=pd.DataFrame(fits))
    for name, frame in tables.items():
        frame.to_csv(out / f"{name}.csv", index=False)
    default.to_parquet(out / "default_development_predictions.parquet", index=False)
    gate = development_gate(annual, pooled, tables["calibration"], config)
    save_json(out / "model_gate.json", gate)
    scales = {target: {"residual_sd": max(float(group.residual.std(ddof=0)), .01 if TARGETS[target][1] == "wickets" else .05),
        "residual_mean": float(group.residual.mean()), "events": len(group)} for target, group in default.groupby("target")}
    save_json(out / "development_reference_scales.json", {"status": "frozen" if gate["reference_scales_frozen_for_final_ratings"] else "candidate_only_gate_failed",
        "prior_events": config["default_prior_events"], "years": years, "reserved_outcomes_used": False,
        "scale_definition": "Population SD (ddof=0) of out-of-time residuals, with registered floors; mean bias is reported, not subtracted from outcomes.", "targets": scales})
    from .baseline_figures import make_baseline_figures
    make_baseline_figures(tables, config, out)
    alerts = tables["calibration"].loc[tables["calibration"].material_alert]
    report_metrics = pooled.loc[pooled.prior_events.eq(config["default_prior_events"])]
    (out / "REPORT.md").write_text("\n".join([
        "# Development historical peer baseline", "", "[Diagnostic chart pack](BASELINE_CHARTS.pdf)", "",
        "The model asks what an average historical peer would produce in the same competition family, innings, phase and wicket band. Expectations use earlier-year matches only. This provides a reference for pressure performance; it does not identify a causal response to pressure or establish a top-ten list.", "",
        f"Evaluated {default.match_id.nunique()} complete development matches across 2023–2025. Ran {len(fits)} of the maximum 20 fold/setting bundles, each predicting four targets. The registered default remains 200 prior events; other settings are sensitivities, not an automatic model search. 2026 outcomes were not loaded into the development table or evaluated.", "",
        "## Default compared with historical references", "", markdown_table(report_metrics.round(6)), "",
        "Runs use MSE and MAE per role opportunity; wicket primary loss is Brier, with natural-log loss also reported. Batting excludes wides; bowling uses every attempt. Comparators are training-only global and unshrunk family means. Pooled metrics weight delivery opportunities; annual metrics preserve the year breakdown.", "",
        markdown_table(tables["paired_loss_comparisons"].round(6)), "",
        "Negative loss differences favour the context model. Intervals are 10th–90th percentiles from 1,000 shared whole-match resamples stratified by family/year, conditional on the fitted annual models. These comparisons are not player-rating intervals or upstream model-refit uncertainty.", "",
        "## Calibration and cricket interpretation", "", markdown_table(alerts.round(5)) if len(alerts) else "No supported-group material calibration alerts under the predeclared screen.", "",
        "Bias is observed minus expected. A positive run bias would reward a batter merely for playing in an underpredicted scoring environment and penalise a bowler facing that environment. A wicket bias can similarly distort survival or wicket-taking credit. This is why phase and competition diagnostics matter before player selection.", "",
        "Screening tolerances were set before fitting: 0.10 runs or 0.01 wickets per opportunity, at least 500 events and ten matches, and a match-bootstrap interval excluding zero. They are project diagnostics, not universal calibration standards. Alerts span overall, family/year/innings/phase and pressure marginals; overlapping alerts are not independent and have no multiple-testing correction. Sparse groups are reported as uncertain. Coarse peer context does not adjust opposition, venue, required rate, exact remaining balls or tactical role; no claims of complete contextual fairness are justified.", "",
        "## Sparse-context fallback", "", markdown_table(tables["backoff"]), "",
        "Unseen finest cells fall back through phase/innings/family to the training global mean. Seen but small cells are shrunk recursively. The number of reference events is exposure, not independent match evidence. Reliability bins and all subgroup/annual metrics are available as CSVs.", "",
        "## Decision", "", gate["decision"], "",
        f"Benchmark screen passed: **{gate['benchmark_gate_passed']}**. Material calibration alerts: **{gate['material_calibration_alerts']}**. Ready for reserved evaluation: **{gate['ready_for_reserved_evaluation']}**.", "",
        "Development residual scales are exported with an explicit frozen/candidate status. No player aggregates, scores or rankings have been produced. The pressure rule, supported-change population, 70/30 and 50/50 weights, source cutoff and exception exclusions are unchanged. The restrictive blended candidate pool remains a separate selection risk.", ""]))
    if fingerprints(root / "6af3166e7b922_data_pack") != upstream["source_sha256"]:
        raise ValueError("Raw data changed during fitting")
    save_json(out / "manifest.json", {"milestone": "development_peer_baseline", "source_sha256": upstream["source_sha256"],
        "method_config_sha256": sha256(method_path), "validation_config_sha256": sha256(validation_path),
        "preflight_manifest_sha256": sha256(root / "reports/supported_method_2026-11-01/manifest.json"),
        "code_sha256": {str(p.relative_to(root)): sha256(p) for p in sorted((root / "src").rglob("*.py"))},
        "lockfile_sha256": sha256(root / "uv.lock"), "models_fitted": True, "model_fold_setting_bundles": len(fits),
        "reserved_outcome_metrics_computed": False, "player_scores_created": False, "development_matches": int(default.match_id.nunique()),
        "output_sha256": {p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "manifest.json"},
        "elapsed_seconds": round(time.perf_counter() - start, 2)})
    print(json.dumps(gate, indent=2))
    print(f"Report: {out / 'REPORT.md'}")
    return gate
