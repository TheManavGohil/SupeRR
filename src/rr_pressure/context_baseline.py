"""Single preregistered ridge/logistic candidate using verified pre-ball state."""

import itertools
import json
import time

import numpy as np
import pandas as pd

from .baseline import TARGETS, _interval, diagnostic_tables, load_development, match_draws, metrics, pooled_metrics
from .data import fingerprints, save_json, sha256, unique
from .pilot_report import markdown_table


def context_basis(frame, config):
    """Explicit state allowlist: no outcomes, identities, dates or pressure flag."""
    columns = config["context_groups"] + config["required_states"]
    if frame.columns.tolist() != columns:
        raise ValueError("Context predictor allowlist violation")
    d = frame.reset_index(drop=True)
    if not d.family.isin(["IPL", "T20I"]).all() or not d.innings.isin([1, 2]).all() or not d.phase.isin(["01-06", "07-15", "16-20"]).all():
        raise ValueError("Unsupported context group")
    numeric = ["score_before", "legal_balls_before", "balls_remaining", "wickets_before", "recent_wickets"]
    if not np.isfinite(d[numeric].to_numpy()).all() or (d[numeric] < 0).any().any():
        raise ValueError("Invalid pre-ball state")
    if (not d.legal_balls_before.between(0, 119).all() or not d.balls_remaining.between(1, 120).all() or
        not (d.legal_balls_before + d.balls_remaining).eq(120).all() or not d.wickets_before.between(0, 9).all() or
        not d.recent_wickets.between(0, 10).all()):
        raise ValueError("Invalid legal-ball/wicket state")
    chase = d.innings.eq(2)
    if not d.loc[~chase, ["chase_target", "runs_required"]].isna().all().all():
        raise ValueError("First-innings target must not be populated")
    c = d.loc[chase]
    if (not np.isfinite(c[["chase_target", "runs_required"]].to_numpy()).all() or
        c.chase_target.le(0).any() or c.runs_required.le(0).any() or
        not np.allclose(c.chase_target - c.score_before, c.runs_required, rtol=0, atol=1e-9)):
        raise ValueError("Missing or inconsistent known chase target")
    progress = d.legal_balls_before.to_numpy(dtype=float) / 120
    wickets = d.wickets_before.to_numpy(dtype=float) / 10
    pace_raw = d.score_before.to_numpy(dtype=float) / (d.legal_balls_before.to_numpy() + 12)
    target_raw = d.chase_target.fillna(0).to_numpy() / 120
    required_raw = d.runs_required.fillna(0).to_numpy() / d.balls_remaining.to_numpy()
    required = np.clip(required_raw, 0, 6)
    continuous = np.column_stack([progress, progress ** 2, wickets, wickets ** 2,
        d.recent_wickets.to_numpy(dtype=float) / 10, np.clip(pace_raw, 0, 6), np.clip(target_raw, 0, 6),
        required, np.maximum(required - 1, 0), np.maximum(required - 1.5, 0), np.maximum(required - 2, 0)])
    groups, group_names = [], []
    for family, innings, phase in itertools.product(["IPL", "T20I"], [1, 2], ["01-06", "07-15", "16-20"]):
        groups.append((d.family.eq(family) & d.innings.eq(innings) & d.phase.eq(phase)).to_numpy(dtype=float))
        group_names.append(f"{family}:innings{innings}:{phase}")
    indicators = np.column_stack(groups)
    interactions = (indicators[:, :, None] * continuous[:, None, :]).reshape(len(d), -1)
    names = ["intercept", *group_names, *config["continuous_features"],
        *[f"{g}*{name}" for g in group_names for name in config["continuous_features"]]]
    matrix = np.column_stack([np.ones(len(d)), indicators, continuous, interactions])
    if matrix.shape[1] != len(names) or not np.isfinite(matrix).all():
        raise ValueError("Invalid model basis")
    clipping = dict(events=len(d), scoring_pace_clipped=int((pace_raw > 6).sum()),
        target_rate_clipped=int((target_raw > 6).sum()), required_rate_clipped=int((required_raw > 6).sum()))
    return matrix, names, clipping


def sigmoid(z):
    return np.exp(-np.logaddexp(0, -np.asarray(z)))


class WeightedContextModel:
    """Fixed-penalty convex models with training-only feature standardization."""

    def __init__(self, kind, config):
        if kind not in ("runs", "wickets"):
            raise ValueError("Unknown target kind")
        self.kind, self.config = kind, config

    def fit(self, basis, y, weights, names):
        y, weights = np.asarray(y, dtype=float), np.asarray(weights, dtype=float)
        if (len(basis) != len(y) or len(y) != len(weights) or not len(y) or
            not np.isfinite(basis).all() or not np.isfinite(y).all() or not np.isfinite(weights).all() or
            (weights <= 0).any() or (y < 0).any() or not np.all(basis[:, 0] == 1) or len(names) != basis.shape[1]):
            raise ValueError("Invalid training inputs")
        if self.kind == "wickets" and set(np.unique(y)) != {0, 1}:
            raise ValueError("Logistic training requires both binary outcomes")
        self.names = list(names)
        self.mean = np.average(basis, weights=weights, axis=0)
        self.sd = np.sqrt(np.average((basis - self.mean) ** 2, weights=weights, axis=0))
        self.active = self.sd > self.config["minimum_feature_sd"]
        self.mean[0], self.sd[0], self.active[0] = 0., 1., True
        self.sd[~self.active] = 1.
        x = self.transform(basis)
        penalty = np.full(x.shape[1], self.config["ridge_penalty"], dtype=float)
        penalty[0] = 0.
        self.training_mean = float(np.average(y, weights=weights))
        self.training_sd = float(np.sqrt(np.average((y - self.training_mean) ** 2, weights=weights)))
        self.effective_weight_sum = float(weights.sum())
        self.iterations = 1
        if self.kind == "runs":
            h = x.T @ (weights[:, None] * x) + np.diag(penalty)
            self.coef = np.linalg.solve(h, x.T @ (weights * y))
            gradient = h @ self.coef - x.T @ (weights * y)
            self.gradient_norm = float(np.max(np.abs(gradient)) / weights.sum())
        else:
            beta = np.zeros(x.shape[1])
            beta[0] = np.log(self.training_mean / (1 - self.training_mean))

            def objective(b):
                z = x @ b
                return float(np.dot(weights, np.logaddexp(0, z) - y * z) + .5 * np.dot(penalty, b * b))

            for iteration in range(self.config["logistic_max_iterations"]):
                p = sigmoid(x @ beta)
                gradient = x.T @ (weights * (p - y)) + penalty * beta
                self.gradient_norm = float(np.max(np.abs(gradient)) / weights.sum())
                self.iterations = iteration + 1
                if self.gradient_norm <= self.config["logistic_gradient_tolerance"]:
                    break
                h = x.T @ ((weights * p * (1 - p))[:, None] * x) + np.diag(penalty)
                direction = np.linalg.solve(h, gradient)
                before = objective(beta)
                step = 1.
                for _ in range(40):
                    proposal = beta - step * direction
                    if objective(proposal) <= before - 1e-4 * step * np.dot(gradient, direction):
                        beta = proposal
                        break
                    step *= .5
                else:
                    raise ValueError("Logistic line search failed")
            else:
                raise ValueError("Logistic model did not converge")
            self.coef = beta
        if not np.isfinite(self.coef).all():
            raise ValueError("Nonfinite coefficients")
        return self

    def transform(self, basis):
        if basis.shape[1] != len(self.names) or not np.isfinite(basis).all():
            raise ValueError("Prediction basis mismatch")
        return ((basis - self.mean) / self.sd)[:, self.active]

    def predict(self, basis):
        linear = self.transform(basis) @ self.coef
        return (np.maximum(linear, 0), int((linear < 0).sum())) if self.kind == "runs" else (sigmoid(linear), 0)

    def as_dict(self):
        return dict(kind=self.kind, ridge_penalty=self.config["ridge_penalty"], feature_names=self.names,
            active_feature_names=[n for n, a in zip(self.names, self.active) if a],
            training_feature_mean=self.mean.tolist(), training_feature_sd=self.sd.tolist(),
            active=self.active.tolist(), coefficients=self.coef.tolist(), training_outcome_mean=self.training_mean,
            training_outcome_sd=self.training_sd, weight_sum=self.effective_weight_sum,
            iterations=self.iterations, normalized_gradient_max=self.gradient_norm)


def fit_context_fold(data, year, config, baseline_predictions):
    if year not in config["development_years"]:
        raise ValueError("Candidate command permits development years only")
    matches = data[["match_id", "match_date", "year"]].drop_duplicates()
    unique(matches, ["match_id"], "context chronology")
    if not pd.to_datetime(matches.match_date).dt.year.eq(matches.year).all():
        raise ValueError("Year/date disagreement")
    train = data.loc[data.match_date.lt(f"{year}-01-01")]
    ev = data.loc[data.year.eq(year)]
    if train.empty or ev.empty or train.match_date.max() >= ev.match_date.min() or set(train.match_id) & set(ev.match_id):
        raise ValueError("Invalid chronological training split")
    base = baseline_predictions.loc[baseline_predictions.year.eq(year)]
    unique(base, ["event_id", "target"], "original predictions")
    columns = config["context_groups"] + config["required_states"]
    predictions, models, diagnostics = [], {}, []
    for role in ["batting", "bowling"]:
        tr = train.loc[train.batting_opportunity] if role == "batting" else train
        test = ev.loc[ev.batting_opportunity] if role == "batting" else ev
        raw_train, names, _ = context_basis(tr[columns], config)
        raw_test, test_names, clipping = context_basis(test[columns], config)
        if names != test_names:
            raise ValueError("Training and evaluation bases differ")
        age = (pd.Timestamp(f"{year}-01-01") - pd.to_datetime(tr.match_date)).dt.days.to_numpy()
        if (age <= 0).any():
            raise ValueError("Future training age")
        weights = np.exp2(-age / config["expectation_recency_half_life_days"])
        for target, (target_role, kind) in TARGETS.items():
            if target_role != role:
                continue
            model = WeightedContextModel(kind, config).fit(raw_train, tr[target], weights, names)
            estimates, floored = model.predict(raw_test)
            records = base.loc[base.target.eq(target)].drop(columns=["prior_events", "backoff_depth", "reference_events"]).copy()
            expected = test[["event_id", target]].rename(columns={target: "expected_outcome"})
            expected["candidate_prediction"] = estimates
            records = records.merge(expected, on="event_id", validate="one_to_one")
            if len(records) != len(test) or set(records.event_id) != set(test.event_id) or not records.outcome.eq(records.expected_outcome).all():
                raise ValueError("Candidate cohort/targets differ from baseline")
            records["baseline_prediction"] = records.prediction
            records["prediction"] = records.pop("candidate_prediction")
            records = records.drop(columns="expected_outcome")
            records["ridge_penalty"] = config["ridge_penalty"]
            records["candidate_id"] = config["candidate_id"]
            records["training_scale"] = max(model.training_sd, .01 if kind == "wickets" else .05)
            records["residual"] = records.outcome - records.prediction
            records["forecast_standardized_residual"] = records.residual / records.training_scale
            records["training_last_date"] = train.match_date.max()
            if not np.isfinite(records.prediction).all():
                raise ValueError("Nonfinite candidate prediction")
            predictions.append(records)
            models[target] = model.as_dict()
            diagnostics.append(dict(year=year, target=target, **clipping, run_predictions_floored=floored,
                inactive_training_features=int((~model.active).sum()), model_iterations=model.iterations,
                normalized_gradient_max=model.gradient_norm))
    return pd.concat(predictions, ignore_index=True), models, pd.DataFrame(diagnostics)


def candidate_metrics(predictions, validation):
    # Reuse metric arithmetic without mislabelling the new penalty as prior events.
    result = metrics(predictions.rename(columns={"ridge_penalty": "prior_events"}), validation)
    result = result.rename(columns={"prior_events": "ridge_penalty"})
    result["model"] = result.model.replace({"hierarchical": "context_v2"})
    return result


def candidate_pooled(annual):
    result = pooled_metrics(annual.rename(columns={"ridge_penalty": "prior_events"}))
    return result.rename(columns={"prior_events": "ridge_penalty"})


def candidate_gate(annual, pooled, calibration, paired, validation, config):
    checks = []
    for target in TARGETS:
        p = pooled.loc[pooled.target.eq(target)].set_index("model")
        yearly = annual.loc[annual.target.eq(target)].pivot(index="year", columns="model", values="primary_loss")
        passing_years = int(yearly.context_v2.le(yearly["global"]).sum())
        checks.append(dict(target=target,
            pooled_beats_global=bool(p.loc["context_v2", "primary_loss"] <= p.loc["global", "primary_loss"]),
            pooled_beats_family=bool(p.loc["context_v2", "primary_loss"] <= p.loc["family", "primary_loss"]),
            pooled_no_worse_than_v1=bool(paired.loc[paired.target.eq(target), "primary_loss_delta"].iloc[0] <= 0),
            years_no_worse_than_global=passing_years, annual_gate=passing_years >= validation["minimum_passing_years"]))
    passes = all(c["pooled_beats_global"] and c["pooled_beats_family"] and c["pooled_no_worse_than_v1"] and c["annual_gate"] for c in checks)
    alerts = int(calibration.material_alert.sum())
    ready = passes and alerts == 0
    return dict(candidate_id=config["candidate_id"], benchmark_checks=checks, benchmark_gate_passed=passes,
        material_calibration_alerts=alerts, ready_for_reserved_evaluation=ready,
        reference_scales_frozen_for_final_ratings=ready, models_fitted=True,
        cumulative_model_bundles=config["budget"]["cumulative_after_development"],
        player_scores_created=False, reserved_outcome_metrics_computed=False, final_rankings_permitted=False,
        pressure_rule_changed=False, global_pressure_change_comparison_ready=False,
        decision="Candidate passes the unchanged screen; freeze it and development scales before separate reserved evaluation." if ready else
            "Candidate is not promoted. Preserve the failed gate and both baselines; no further automatic candidate fits or reserved evaluation.")


def load_context_development(root, config, method):
    data, preflight = load_development(root, method)
    full = root / "reports/full_reconciliation_2026-11-01"
    baseline = root / "reports/baseline_development_2026-11-01"
    baseline_manifest = json.loads((baseline / "manifest.json").read_text())
    full_manifest = json.loads((full / "manifest.json").read_text())
    if (preflight["reconciliation_manifest_sha256"] != sha256(full / "manifest.json") or
        baseline_manifest["preflight_manifest_sha256"] != sha256(root / "reports/supported_method_2026-11-01/manifest.json") or
        baseline_manifest["validation_config_sha256"] != sha256(root / "configs/baseline_validation_v1.json")):
        raise ValueError("Upstream source or validation mismatch")
    for directory, manifest, name in [(full, full_manifest, "verified_events.parquet"),
        (baseline, baseline_manifest, "default_development_predictions.parquet"),
        (baseline, baseline_manifest, "model_gate.json"), (baseline, baseline_manifest, "calibration.csv")]:
        if sha256(directory / name) != manifest["output_sha256"][name]:
            raise ValueError("Changed upstream artifact: " + name)
    if baseline_manifest["model_fold_setting_bundles"] != config["budget"]["previous_bundles"]:
        raise ValueError("Model budget does not match previous execution")
    states = pd.read_parquet(full / "verified_events.parquet", columns=["event_id"] + config["required_states"],
        filters=[("event_id", "in", data.event_id.tolist())])
    unique(states, ["event_id"], "verified context")
    if set(states.event_id) != set(data.event_id):
        raise ValueError("Incomplete verified context")
    data = data.merge(states, on="event_id", validate="one_to_one")
    original = pd.read_parquet(baseline / "default_development_predictions.parquet")
    if not original.year.isin(config["development_years"]).all():
        raise ValueError("Reserved outcomes in baseline predictions")
    return data, original, preflight


def run_context_baseline(root):
    start = time.perf_counter()
    config_path = root / "configs/context_baseline_v2.json"
    config = json.loads(config_path.read_text())
    method_path = root / "configs/supported_method_v1.json"
    validation_path = root / "configs/baseline_validation_v1.json"
    method = json.loads(method_path.read_text())
    validation = json.loads(validation_path.read_text())
    budget = config["budget"]
    if (budget["maximum_bundles"] != method["expectation_model"]["maximum_fold_setting_bundles"] or
        len(config["development_years"]) != budget["candidate_development_bundles"] or
        budget["previous_bundles"] + len(config["development_years"]) != budget["cumulative_after_development"] or
        budget["cumulative_after_development"] + budget["reserved_bundles_if_promoted"] + budget["unused_contingency"] > budget["maximum_bundles"]):
        raise ValueError("Candidate exceeds registered model budget")
    if config["development_years"] != method["development_prediction_years"]:
        raise ValueError("Development years changed")
    if config["parent_method"] != method["method_id"]:
        raise ValueError("Candidate amends a different method")
    out = root / "reports/context_baseline_v2_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    frozen = out / "frozen_candidate.json"
    if frozen.exists() and json.loads(frozen.read_text()) != config:
        raise ValueError("Frozen candidate changed; do not retune silently")
    save_json(frozen, config)
    save_json(out / "frozen_validation.json", validation)
    data, original, preflight = load_context_development(root, config, method)
    predictions, diagnostics = [], []
    for year in config["development_years"]:
        p, models, diag = fit_context_fold(data, year, config, original)
        p.to_parquet(out / f"predictions_{year}.parquet", index=False)
        save_json(out / f"models_{year}.json", models)
        predictions.append(p)
        diagnostics.append(diag)
        print(f"Completed contextual candidate {year}: one fixed bundle, four targets.", flush=True)
    predictions = pd.concat(predictions, ignore_index=True)
    annual = candidate_metrics(predictions, validation)
    pooled = candidate_pooled(annual)
    tables = diagnostic_tables(predictions, validation, include_backoff=False)
    tables.pop("backoff")
    matches, draws = match_draws(predictions, validation)
    comparisons = []
    for target, group in predictions.groupby("target"):
        delta = (group.outcome - group.prediction) ** 2 - (group.outcome - group.baseline_prediction) ** 2
        low, high, finite = _interval(group, delta, matches, draws)
        loss = float(np.mean((group.outcome - group.baseline_prediction) ** 2))
        comparisons.append(dict(target=target, primary_loss_delta=float(delta.mean()),
            relative_improvement_percent=float(-100 * delta.mean() / loss), p10=low, p90=high, finite_replicates=finite))
    paired = pd.DataFrame(comparisons)
    tables.update(annual_metrics=annual, pooled_metrics=pooled, paired_against_v1=paired,
        feature_diagnostics=pd.concat(diagnostics, ignore_index=True))
    old_calibration = pd.read_csv(root / "reports/baseline_development_2026-11-01/calibration.csv")
    tables["alert_counts"] = pd.concat([old_calibration.assign(candidate="historical_v1"),
        tables["calibration"].assign(candidate="context_v2")], ignore_index=True).groupby(["candidate", "target"]).material_alert.sum().reset_index()
    for name, table in tables.items():
        table.to_csv(out / f"{name}.csv", index=False)
    predictions.to_parquet(out / "development_predictions.parquet", index=False)
    gate = candidate_gate(annual, pooled, tables["calibration"], paired, validation, config)
    save_json(out / "model_gate.json", gate)
    scales = {target: dict(residual_sd=max(float(g.residual.std(ddof=0)), .01 if TARGETS[target][1] == "wickets" else .05),
        residual_mean=float(g.residual.mean()), events=len(g)) for target, g in predictions.groupby("target")}
    save_json(out / "development_reference_scales.json", dict(candidate_id=config["candidate_id"],
        status="frozen" if gate["ready_for_reserved_evaluation"] else "candidate_only_gate_failed",
        reserved_outcomes_used=False, targets=scales))
    from .context_figures import make_context_figures
    make_context_figures(tables, old_calibration, out)
    (out / "REPORT.md").write_text("\n".join([
        "# Contextual baseline revision — development only", "", "[Standalone comparison charts](CONTEXT_CHARTS.pdf)", "",
        "One fixed candidate uses verified pre-ball scoring pace, exact progress/wickets and chase requirements, plus historical recency weighting. Runs use ridge regression and wickets use logistic regression. Training uses earlier years only. All four targets and role opportunities match the original default baseline exactly.", "",
        f"Evaluated {predictions.match_id.nunique()} development matches, with three candidate bundles and {budget['cumulative_after_development']} cumulative bundles. No second candidate or tuning search was run. No 2026 outcome was included. The penalty and feature specification were committed before fitting.", "",
        "## Paired prediction comparison with the original default", "", markdown_table(paired.round(6)), "",
        "Negative loss differences favour the candidate. Intervals are 10th–90th percentiles from 1,000 shared whole-match resamples stratified by family/year, conditional on fitted models. Raw losses are MSE for runs and Brier for wickets. The original v1 findings informed this amendment, so these development results are adaptive evidence, not an independent holdout result.", "",
        "## Calibration alerts under the unchanged screen", "", markdown_table(tables["alert_counts"]), "",
        markdown_table(tables["calibration"].loc[tables["calibration"].material_alert].round(5)), "",
        "The screen still requires at least 500 events and ten matches, a mean bias above 0.10 runs or 0.01 wickets per opportunity, and a match-bootstrap interval excluding zero. Alerts overlap and have no multiplicity correction. Lower alert counts alone do not pass the gate. Sparse groups remain uncertain.", "",
        "## Numerical and feature diagnostics", "", markdown_table(tables["feature_diagnostics"].round(8)), "",
        "Feature means, SDs, coefficients, inactive training columns and numerical convergence are saved for each model. Global/family comparators are copied from the original earlier-year baseline. The model weight half-life is 365 days; the player-rating policy remains 730 days. No evaluation outcomes are used to adjust predictions or scales during fitting.", "",
        "## Selector interpretation and decision", "", gate["decision"], "",
        f"Benchmark gate passed: **{gate['benchmark_gate_passed']}**. Calibration alerts: **{gate['material_calibration_alerts']}**. Ready for reserved evaluation: **{gate['ready_for_reserved_evaluation']}**.", "",
        "The practical question is whether runs and wickets are being credited fairly given the situation. Conditioning on existing scoring pace can absorb some earlier value created by the same player; these residuals are conditional contributions, not total innings value. Venue and opposition strength remain omitted. Historical recency cannot anticipate every new scoring environment. No player scores or rankings are generated by this stage.", "",
        "Pressure thresholds, supported comparison eligibility, cutoff, 70/30 and 50/50 weights, and match-bootstrap policy are unchanged. If the candidate fails, preserve both models and the failed gate; do not automatically spend the remaining budget on another candidate or inspect reserved outcomes.", ""]))
    if fingerprints(root / "6af3166e7b922_data_pack") != preflight["source_sha256"]:
        raise ValueError("Raw data changed")
    save_json(out / "manifest.json", dict(candidate_id=config["candidate_id"], source_sha256=preflight["source_sha256"],
        candidate_config_sha256=sha256(config_path), method_config_sha256=sha256(method_path), validation_config_sha256=sha256(validation_path),
        parent_baseline_manifest_sha256=sha256(root / "reports/baseline_development_2026-11-01/manifest.json"),
        code_sha256={str(p.relative_to(root)): sha256(p) for p in sorted((root / "src").rglob("*.py"))},
        lockfile_sha256=sha256(root / "uv.lock"), candidate_bundles=3, cumulative_model_bundles=budget["cumulative_after_development"],
        reserved_outcome_metrics_computed=False, player_scores_created=False,
        output_sha256={p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "manifest.json"},
        elapsed_seconds=round(time.perf_counter() - start, 2)))
    print(json.dumps(gate, indent=2))
    print(f"Report: {out / 'REPORT.md'}")
    return gate
