"""Fixed contemporary peer expectations with complete-match cross-fitting."""

import json
import time

import numpy as np
import pandas as pd

from .baseline import (TARGETS, _interval, _lookup, development_gate, diagnostic_tables,
                       match_draws, metrics, pooled_metrics)
from .data import fingerprints, save_json, sha256, unique
from .pilot_report import markdown_table
from .reference_audit import (CONTEXT, INPUTS, audit_exposures, load_exposures,
                              match_partitions, validate_exposures)


class RetrospectivePeers:
    """Recursive means; every statistic comes from one training partition."""

    def __init__(self, config, kind):
        self.config, self.kind = config, kind
        self.hierarchy = config["hierarchy"]
        expected = [CONTEXT[:i] for i in range(len(CONTEXT) + 1)]
        if self.hierarchy != expected or kind not in ["runs", "wickets"]:
            raise ValueError("Unexpected retrospective hierarchy or target kind")
        self.prior = config["prior_events"]
        if not np.isfinite(self.prior) or self.prior <= 0:
            raise ValueError("Invalid prior strength")

    @staticmethod
    def _validate(x):
        if x.columns.tolist() != CONTEXT or x.isna().any().any():
            raise ValueError("Predictor allowlist or missing-context violation")

    def fit(self, x, y, match_ids):
        self._validate(x)
        values, ids = np.asarray(y, dtype=float), np.asarray(match_ids)
        if (not len(x) or len(x) != len(values) or len(x) != len(ids) or
                not np.isfinite(values).all() or (values < 0).any() or pd.isna(ids).any()):
            raise ValueError("Invalid training targets or match identities")
        if self.kind == "wickets" and not np.isin(values, [0, 1]).all():
            raise ValueError("Nonbinary wicket target")
        d = x.reset_index(drop=True).assign(outcome=values, match_id=ids)
        self.global_mean, self.training_sd = float(values.mean()), float(values.std(ddof=0))
        self.training_events, self.training_matches = len(d), d.match_id.nunique()
        self.global_max_match_fraction = float(d.groupby("match_id").size().max() / len(d))
        self.tables = []
        for keys in self.hierarchy[1:]:
            table = d.groupby(keys, observed=True).agg(total=("outcome", "sum"),
                count=("outcome", "size"), matches=("match_id", "nunique")).reset_index()
            largest = d.groupby(keys + ["match_id"], observed=True).size().groupby(level=keys).max()
            table = table.merge(largest.rename("largest_match_events").reset_index(), on=keys,
                                validate="one_to_one")
            parent = self._predict(table)["prediction"].to_numpy()
            table["parent_mean"] = parent
            table["own_weight"] = table["count"] / (table["count"] + self.prior)
            table["expectation"] = (table.total + self.prior * parent) / (table["count"] + self.prior)
            table["maximum_match_fraction"] = table.largest_match_events / table["count"]
            self.tables.append((keys, table))
        return self

    def _predict(self, x):
        result = pd.DataFrame(dict(prediction=np.full(len(x), self.global_mean),
            backoff_depth=np.zeros(len(x), dtype=int), reference_events=self.training_events,
            reference_matches=self.training_matches, own_cell_weight=1.,
            maximum_reference_match_fraction=self.global_max_match_fraction))
        for depth, (keys, table) in enumerate(self.tables, start=1):
            values = _lookup(x, table, keys, "expectation")
            seen = np.isfinite(values)
            result.loc[seen, "prediction"] = values[seen]
            result.loc[seen, "backoff_depth"] = depth
            for source, dest in [("count", "reference_events"), ("matches", "reference_matches"),
                                 ("own_weight", "own_cell_weight"),
                                 ("maximum_match_fraction", "maximum_reference_match_fraction")]:
                result.loc[seen, dest] = _lookup(x, table, keys, source)[seen]
        return result

    def predict(self, x):
        self._validate(x)
        result = self._predict(x)
        # Unshrunk same-year comparators also exclude the complete evaluation fold.
        for depth, column in [(0, "global_prediction"), (1, "family_prediction")]:
            keys, table = self.tables[depth]
            raw = table.assign(raw_mean=table.total / table["count"])
            value = _lookup(x, raw, keys, "raw_mean")
            fallback = self.global_mean if depth == 0 else result.global_prediction.to_numpy()
            result[column] = np.where(np.isfinite(value), value, fallback)
        for depth, prefix in [(1, "parent"), (4, "finest")]:
            keys, table = self.tables[depth]
            for source, dest in [("count", "events"), ("matches", "matches")]:
                values = _lookup(x, table, keys, source)
                result[f"{prefix}_peer_{dest}"] = np.nan_to_num(values, nan=0).astype(int)
            result[f"{prefix}_supported"] = (
                result[f"{prefix}_peer_events"].ge(self.config["minimum_peer_events"]) &
                result[f"{prefix}_peer_matches"].ge(self.config["minimum_peer_matches"]))
        return result

    def as_dict(self):
        return dict(kind=self.kind, prior_events=self.prior, training_events=self.training_events,
            training_matches=self.training_matches, training_mean=self.global_mean,
            training_outcome_sd=self.training_sd, maximum_match_fraction=self.global_max_match_fraction,
            levels=[dict(keys=keys, cells=table.to_dict("records")) for keys, table in self.tables])


def validate_partitions(data, partitions, config):
    if set(data.columns) != set(INPUTS + list(TARGETS)):
        raise ValueError("Unexpected development input columns")
    validate_exposures(data[INPUTS], config)
    expected = match_partitions(data[INPUTS], config)
    try:
        pd.testing.assert_frame_equal(expected, partitions.reset_index(drop=True), check_dtype=False)
    except AssertionError as error:
        raise ValueError("Frozen match partition changed") from error
    if set(data.year) != set(config["development_years"]):
        raise ValueError("Incomplete development years")


def fit_partition(data, partitions, evaluation_fold, config):
    validate_partitions(data, partitions, config)
    if evaluation_fold not in range(config["folds"]):
        raise ValueError("Unregistered evaluation partition")
    d = data.merge(partitions[["match_id", "evaluation_fold"]], on="match_id", validate="many_to_one")
    train, evaluate = d.loc[d.evaluation_fold.ne(evaluation_fold)], d.loc[d.evaluation_fold.eq(evaluation_fold)]
    if train.empty or evaluate.empty or set(train.match_id) & set(evaluate.match_id):
        raise ValueError("Invalid complete-match split")
    rows, models = [], {}
    for target, (role, kind) in TARGETS.items():
        tr = train.loc[train.batting_opportunity] if role == "batting" else train
        ev = evaluate.loc[evaluate.batting_opportunity] if role == "batting" else evaluate
        if ev.empty or tr.empty:
            raise ValueError("Missing role exposure")
        y = ev[target].to_numpy(dtype=float)
        if not np.isfinite(y).all() or (y < 0).any() or (kind == "wickets" and not np.isin(y, [0, 1]).all()):
            raise ValueError("Invalid evaluation targets")
        model = RetrospectivePeers(config, kind).fit(tr[CONTEXT], tr[target], tr.match_id)
        records = pd.concat([ev[INPUTS].reset_index(drop=True), model.predict(ev[CONTEXT])], axis=1)
        records["evaluation_fold"], records["training_fold"] = evaluation_fold, 1 - evaluation_fold
        records["target"], records["role"], records["kind"] = target, role, kind
        records["outcome"], records["prior_events"] = y, config["prior_events"]
        records["training_scale"] = max(model.training_sd, .01 if kind == "wickets" else .05)
        records["residual"] = records.outcome - records.prediction
        records["partition_standardized_residual"] = records.residual / records.training_scale
        records["training_first_date"], records["training_last_date"] = tr.match_date.min(), tr.match_date.max()
        if (not np.isfinite(records[["prediction", "global_prediction", "family_prediction", "training_scale"]]).all().all()
                or records.prediction.lt(0).any() or (kind == "wickets" and not records.prediction.between(0, 1).all())):
            raise ValueError("Prediction domain violation")
        rows.append(records)
        models[target] = model.as_dict()
    membership = dict(evaluation_fold=evaluation_fold, training_fold=1 - evaluation_fold,
        training_match_ids=sorted(train.match_id.unique()), evaluation_match_ids=sorted(evaluate.match_id.unique()))
    return pd.concat(rows, ignore_index=True), dict(membership=membership, targets=models)


def check_budget(config, historical):
    b = config["budget"]
    if (historical != b["historical_bundles_used"] or config["folds"] != 2 or
            b["development_partition_bundles"] != 2 or b["reserved_partition_bundles"] != 2 or
            b["targets_per_bundle"] != len(TARGETS) or b["additional_settings_or_partition_seeds"] != 0 or
            b["new_target_model_fits_maximum"] != 4 * len(TARGETS) or
            historical + 4 > b["amended_maximum"]):
        raise ValueError("Registered reference budget mismatch")


def load_reference_development(root, config):
    """Verify the frozen audit before opening only development targets."""
    audit = root / "reports/reference_audit_2026-11-01"
    manifest = json.loads((audit / "manifest.json").read_text())
    preflight = root / "reports/supported_method_2026-11-01"
    if (manifest["config_sha256"] != sha256(root / "configs/retrospective_reference_v1.json") or
            manifest["preflight_manifest_sha256"] != sha256(preflight / "manifest.json")):
        raise ValueError("Reference audit provenance changed")
    for name, digest in manifest["output_sha256"].items():
        if sha256(audit / name) != digest:
            raise ValueError("Reference audit artifact changed: " + name)
    if not json.loads((audit / "feasibility_gate.json").read_text())["development_fitting_permitted"]:
        raise ValueError("Reference support audit failed")
    data = load_exposures(root, config)
    partitions, support = audit_exposures(data, config)
    recorded = pd.read_csv(audit / "match_partitions.csv", dtype={"match_id": str})
    pd.testing.assert_frame_equal(partitions, recorded, check_dtype=False)
    pd.testing.assert_frame_equal(support, pd.read_csv(audit / "peer_support.csv"), check_dtype=False)
    upstream = json.loads((preflight / "manifest.json").read_text())
    if sha256(preflight / "targets.parquet") != upstream["output_sha256"]["targets.parquet"]:
        raise ValueError("Target artifact changed")
    targets = pd.read_parquet(preflight / "targets.parquet", columns=["event_id", *TARGETS],
        filters=[("event_id", "in", data.event_id.tolist())])
    if set(targets.event_id) != set(data.event_id):
        raise ValueError("Incomplete development targets")
    data = data.merge(targets, on="event_id", validate="one_to_one")
    originals, histories = {}, []
    for label, directory, filename in [
        ("historical_v1", "baseline_development_2026-11-01", "default_development_predictions.parquet"),
        ("context_v2", "context_baseline_v2_2026-11-01", "development_predictions.parquet")]:
        source = root / "reports" / directory
        m = json.loads((source / "manifest.json").read_text())
        if (m["source_sha256"] != upstream["source_sha256"] or
                m["validation_config_sha256"] != sha256(root / "configs/baseline_validation_v1.json")):
            raise ValueError("Historical reference lineage changed")
        for name in [filename, "model_gate.json"]:
            if sha256(source / name) != m["output_sha256"][name]:
                raise ValueError("Historical artifact changed: " + name)
        originals[label] = pd.read_parquet(source / filename, columns=["event_id", "target", "outcome", "prediction", "year"])
        if not originals[label].year.isin(config["development_years"]).all():
            raise ValueError("Reserved outcomes in historical predictions")
        histories.append(m["model_fold_setting_bundles"] if label == "historical_v1" else m["candidate_bundles"])
    check_budget(config, sum(histories))
    validate_partitions(data, partitions, config)
    return data, partitions, support, originals, upstream


def historical_comparisons(predictions, originals, validation):
    matches, draws = match_draws(predictions, validation)
    result = []
    for label, old in originals.items():
        unique(old, ["event_id", "target"], "historical prediction keys")
        if set(zip(old.event_id, old.target)) != set(zip(predictions.event_id, predictions.target)):
            raise ValueError("Historical comparison cohort mismatch")
        paired = predictions.merge(old[["event_id", "target", "outcome", "prediction"]],
            on=["event_id", "target"], suffixes=("", "_old"), validate="one_to_one")
        if not paired.outcome.eq(paired.outcome_old).all():
            raise ValueError("Historical comparison targets differ")
        for target, g in paired.groupby("target"):
            delta = (g.outcome - g.prediction) ** 2 - (g.outcome - g.prediction_old) ** 2
            low, high, finite = _interval(g, delta, matches, draws)
            loss = float(np.mean((g.outcome - g.prediction_old) ** 2))
            result.append(dict(target=target, comparator=label, primary_loss_delta=float(delta.mean()),
                relative_improvement_percent=float(-100 * delta.mean() / loss) if loss else np.nan,
                p10=low, p90=high, finite_replicates=finite))
    return pd.DataFrame(result)


def reference_gate(annual, pooled, calibration, fold_calibration, support, validation, config):
    base = development_gate(annual, pooled, calibration, validation)
    if set(fold_calibration.evaluation_fold) != {0, 1} or set(fold_calibration.target) != set(TARGETS):
        raise ValueError("Incomplete partition calibration screen")
    candidate = support.loc[support.scheme.eq("two_fold")]
    support_ok = bool(not candidate.empty and candidate.supported_fraction.ge(
        config["minimum_finest_support_fraction"]).all() and candidate.parent_unsupported_events.eq(0).all())
    fold_alerts = int(fold_calibration.material_alert.sum())
    ready = bool(base["ready_for_reserved_evaluation"] and fold_alerts == 0 and support_ok)
    base.update(candidate_id=config["candidate_id"], pooled_material_calibration_alerts=base["material_calibration_alerts"],
        fold_material_calibration_alerts=fold_alerts, peer_support_gate_passed=support_ok,
        ready_for_reserved_evaluation=ready, reference_scales_frozen_for_final_ratings=ready,
        cumulative_model_bundles=config["budget"]["historical_bundles_used"] + config["folds"],
        interpretation="Retrospective opposite-partition expectations; not match-date forecasts.",
        decision="Development passes; freeze the procedure and scales before separate reserved evaluation." if ready else
            "Reference is not promoted. Preserve failed development screens; no reserved outcomes, player scores or further candidate fits.")
    return base


def support_diagnostics(predictions):
    rows = []
    for (fold, year, family, target), g in predictions.groupby(["evaluation_fold", "year", "family", "target"]):
        rows.append(dict(evaluation_fold=fold, year=year, family=family, target=target, events=len(g),
            matches=g.match_id.nunique(), unseen_finest_events=int(g.backoff_depth.lt(5).sum()),
            finest_supported_fraction=float(g.finest_supported.mean()),
            parent_unsupported_events=int((~g.parent_supported).sum()),
            median_finest_peer_events=float(g.finest_peer_events.median()),
            median_own_cell_weight=float(g.own_cell_weight.median()),
            maximum_reference_match_fraction=float(g.maximum_reference_match_fraction.max())))
    return pd.DataFrame(rows)


def run_retrospective_reference(root):
    start = time.perf_counter()
    config_path = root / "configs/retrospective_reference_v1.json"
    validation_path = root / "configs/baseline_validation_v1.json"
    config, validation = json.loads(config_path.read_text()), json.loads(validation_path.read_text())
    if config["prior_events"] != validation["default_prior_events"]:
        raise ValueError("Registered default prior changed")
    data, partitions, support, originals, upstream = load_reference_development(root, config)
    out = root / "reports/retrospective_reference_development_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    for name, value in [("frozen_reference.json", config), ("frozen_validation.json", validation)]:
        path = out / name
        if path.exists() and json.loads(path.read_text()) != value:
            raise ValueError("Frozen reference specification changed")
        save_json(path, value)
    predictions, ledger = [], []
    for fold in range(config["folds"]):
        p, models = fit_partition(data, partitions, fold, config)
        p.to_parquet(out / f"predictions_fold_{fold}.parquet", index=False)
        save_json(out / f"models_fold_{fold}.json", models)
        predictions.append(p)
        ledger.append(dict(evaluation_fold=fold, training_fold=1-fold, targets=len(models["targets"]),
            training_matches=len(models["membership"]["training_match_ids"]),
            evaluation_matches=len(models["membership"]["evaluation_match_ids"]), prediction_rows=len(p)))
        print(f"Completed evaluation partition {fold}: one bundle, four target models.", flush=True)
    predictions = pd.concat(predictions, ignore_index=True)
    unique(predictions, ["event_id", "target"], "retrospective predictions")
    annual = metrics(predictions, validation)
    pooled = pooled_metrics(annual)
    tables = diagnostic_tables(predictions, validation, include_backoff=False)
    tables.pop("backoff")
    fold_calibration, fold_metrics = [], []
    for fold, p in predictions.groupby("evaluation_fold"):
        diag = diagnostic_tables(p, validation, include_backoff=False)
        fold_calibration.append(diag["calibration"].assign(evaluation_fold=fold))
        fold_metrics.append(metrics(p, validation).assign(evaluation_fold=fold))
    tables.update(annual_metrics=annual, pooled_metrics=pooled,
        fold_calibration=pd.concat(fold_calibration, ignore_index=True),
        fold_metrics=pd.concat(fold_metrics, ignore_index=True),
        historical_comparisons=historical_comparisons(predictions, originals, validation),
        support_diagnostics=support_diagnostics(predictions), fit_ledger=pd.DataFrame(ledger))
    gate = reference_gate(annual, pooled, tables["calibration"], tables["fold_calibration"], support, validation, config)
    tables["alert_counts"] = pd.concat([tables["calibration"].assign(screen="pooled"),
        tables["fold_calibration"].assign(screen=lambda d: "fold_" + d.evaluation_fold.astype(str))]
        ).groupby(["screen", "target"]).agg(alerts=("material_alert", "sum"),
            supported_groups=("enough_evidence", "sum"), screened_groups=("material_alert", "size")).reset_index()
    for name, table in tables.items():
        table.to_csv(out / f"{name}.csv", index=False)
    predictions.to_parquet(out / "development_predictions.parquet", index=False)
    save_json(out / "model_gate.json", gate)
    save_json(out / "development_reference_scales.json", dict(candidate_id=config["candidate_id"],
        status="frozen" if gate["ready_for_reserved_evaluation"] else "candidate_only_gate_failed",
        reserved_outcomes_used=False, targets={target: dict(events=len(g), residual_mean=float(g.residual.mean()),
            residual_sd=max(float(g.residual.std(ddof=0)), .01 if TARGETS[target][1] == "wickets" else .05))
            for target, g in predictions.groupby("target")}))
    from .retrospective_figures import make_retrospective_figures
    make_retrospective_figures(tables, out)
    alerts = pd.concat([tables["calibration"].assign(screen="pooled"),
        tables["fold_calibration"].assign(screen=lambda d: "fold_" + d.evaluation_fold.astype(str))])
    (out / "REPORT.md").write_text("\n".join([
        "# Contemporary peer reference — development evaluation", "", "[Standalone chart pack](REFERENCE_CHARTS.pdf)", "",
        "Cricket question: are pressure runs and wickets being compared with an adequate contemporary innings-phase and wicket-state reference?", "",
        f"Evaluated {data.match_id.nunique():,} verified development matches / {len(data):,} delivery events (2023–2025). Two fixed complete-match partitions produce eight target models, bringing the cumulative budget to 20 of 22 bundles. The prior stays 200; no new seed, setting or full-data refit was used. No 2026 targets or player scores were accessed.", "",
        "## Prediction losses", "", markdown_table(pooled.round(6)), "",
        "The hierarchical model includes year. Global/family comparators are unshrunk opposite-partition same-year and same-year/family means. Run loss is MSE; wicket loss is Brier. Annual and partition metrics are exported separately.", "",
        "## Comparison with historical forecasts", "", markdown_table(tables["historical_comparisons"].round(6)), "",
        "Negative loss differences favour the contemporary reference. This retrospective procedure can use later matches in the same season and, through the root prior, other development seasons. These are identical-cohort descriptive comparisons, not claims of improved match-date forecasting. All intervals use 1,000 whole-match draws within family/year, conditional on fitted references. The original forecast failures remain preserved.", "",
        "## Calibration screens", "", markdown_table(tables["alert_counts"]), "",
        markdown_table(alerts.loc[alerts.material_alert].round(5)), "",
        "The predeclared tolerances remain 0.10 runs or 0.01 wickets per opportunity, with at least 500 events and ten matches and a 10th–90th percentile interval excluding zero. Pooled and both evaluation-fold screens must pass. Alerts overlap; there is no multiplicity correction. Sparse groups remain uncertain. Combined aggregate centering can be mechanical and cannot substitute for these diagnostics.", "",
        "## Peer support and concentration", "", markdown_table(tables["support_diagnostics"].round(4)), "",
        "Counts and concentration refer to the deepest available training cell; finest-cell support is also exported independently. Sparse cells are retained and shrunk toward their parent. Match concentration describes the local cell, not the full recursive influence through all priors. Training membership and each level's counts, parent means, weights and expectations are in the private model files.", "",
        "## Decision", "", gate["decision"], "",
        f"Benchmark pass: **{gate['benchmark_gate_passed']}**; pooled alerts: **{gate['pooled_material_calibration_alerts']}**; separate-fold alerts: **{gate['fold_material_calibration_alerts']}**; support pass: **{gate['peer_support_gate_passed']}**; reserved readiness: **{gate['ready_for_reserved_evaluation']}**.", "",
        "The reference excludes both innings of every evaluated match from all means, comparators and validation scales. The player's other matches may enter the reference. Venue, opposition strength, precise chase difficulty and within-season drift remain unadjusted. These residuals are contextual descriptions, not intrinsic talent or causal pressure effects. Bootstrap intervals condition on references and omit refitting uncertainty and cross-fold training dependence.", "",
        "Pressure rules, 730-day rating recency, supported-change evidence, 70/30 and 50/50 blends, coverage and eligibility remain frozen. This reference cannot supply missing ordinary death-over controls or enlarge the narrow change cohort by itself. A failed gate blocks reserved evaluation and player scoring; it does not authorize another candidate search.", ""]))
    if fingerprints(root / "6af3166e7b922_data_pack") != upstream["source_sha256"]:
        raise ValueError("Raw sources changed")
    save_json(out / "manifest.json", dict(candidate_id=config["candidate_id"], source_sha256=upstream["source_sha256"],
        reference_config_sha256=sha256(config_path), validation_config_sha256=sha256(validation_path),
        audit_manifest_sha256=sha256(root / "reports/reference_audit_2026-11-01/manifest.json"),
        preflight_manifest_sha256=sha256(root / "reports/supported_method_2026-11-01/manifest.json"),
        historical_manifest_sha256={label: sha256(root / "reports" / directory / "manifest.json") for label, directory in
            [("historical_v1", "baseline_development_2026-11-01"), ("context_v2", "context_baseline_v2_2026-11-01")]},
        code_sha256={str(p.relative_to(root)): sha256(p) for p in sorted((root / "src").rglob("*.py"))},
        lockfile_sha256=sha256(root / "uv.lock"), candidate_bundles=2, target_model_fits=8, cumulative_model_bundles=20,
        reserved_outcome_metrics_computed=False, player_scores_created=False,
        output_sha256={p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "manifest.json"},
        elapsed_seconds=round(time.perf_counter() - start, 2)))
    print(json.dumps(gate, indent=2))
    print(f"Report: {out / 'REPORT.md'}")
    return gate
