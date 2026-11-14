"""Approved retrospective descriptive index; development execution only.

Empirical peer means are statistics of observed other-player outcomes, not
promoted forecasts. Match draws recompute both player and peer evidence.
"""

import argparse
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from .baseline import match_draws
from .data import fingerprints, save_json, sha256, unique
from .player_evidence import CONTEXT, KEY, pressure_peer_support


STATS = {"count": None, "mass": "weight", "squared": "weight_squared",
    "runs": "weighted_runs", "wickets": "weighted_wickets"}
MIXES = {"default_60_40": (.6, .4), "runs_wickets_50_50": (.5, .5), "runs_wickets_70_30": (.7, .3)}


def validate_config(root, config):
    proposal_path = root / "configs/descriptive_rating_v2_proposal.json"
    proposal = json.loads(proposal_path.read_text())
    overridden = {"method_id", "status", "player_score_outputs_permitted"}
    if (config["approved_proposal_sha256"] != sha256(proposal_path) or
            any(config[k] != v for k, v in proposal.items() if k not in overridden) or
            config["method_id"] != "descriptive_peer_pressure_v2" or
            config["status"] != "user_approved_for_development_execution" or
            not config["development_execution_permitted"] or not config["player_score_outputs_permitted"] or
            config["execution_window"] != "development_only" or config["reserved_outcomes_permitted"] or
            config["base_method_config_sha256"] != sha256(root / config["base_method_config"])):
        raise ValueError("Active rating config differs from the explicitly approved development amendment")
    return json.loads((root / config["base_method_config"]).read_text())


def load_development(root, config):
    base = validate_config(root, config)
    directory = root / "reports/player_evidence_development_2026-11-01"
    manifest = json.loads((directory / "manifest.json").read_text())
    if (manifest["development_years"] != config["development_years"] or
            manifest["reference_date"] != config["development_reference_date"] or
            manifest["method_config_sha256"] != config["base_method_config_sha256"] or
            manifest["reserved_outcomes_read"]):
        raise ValueError("Evidence does not belong to the approved development window")
    if (manifest["source_sha256"] != fingerprints(root / "6af3166e7b922_data_pack") or
            manifest["preflight_manifest_sha256"] != sha256(root / "reports/supported_method_2026-11-01/manifest.json")):
        raise ValueError("Frozen raw inputs or preflight lineage changed")
    for name, digest in manifest["preserved_gate_sha256"].items():
        if sha256(root / name) != digest:
            raise ValueError("A historical prediction gate changed")
    names = ["event_role_ledger.parquet", "cohort_register.csv", "validation.json", "observed_uncertainty.parquet"]
    for name in names:
        if sha256(directory / name) != manifest["output_sha256"][name]:
            raise ValueError("Changed initial evidence: " + name)
    if not json.loads((directory / "validation.json").read_text())["validated_initial_tables"]:
        raise ValueError("Initial tables have not passed reconciliation")
    # The evidence artifact contains development only; predicate is an extra boundary.
    ledger = pd.read_parquet(directory / "event_role_ledger.parquet",
        filters=[("year", "in", config["development_years"])])
    cohort = pd.read_csv(directory / "cohort_register.csv", dtype={"player_id": str})
    unique(ledger, ["role", "event_id"], "rating event/role")
    unique(cohort, KEY, "rating cohort")
    if (len(ledger) != 188204 or ledger.event_id.nunique() != 95945 or ledger.match_id.nunique() != 402 or
            not ledger.year.isin(config["development_years"]).all() or
            not pd.to_datetime(ledger.match_date).dt.year.eq(ledger.year).all() or
            ledger.match_date.gt(config["development_reference_date"]).any()):
        raise ValueError("Incomplete or non-development rating evidence")
    if not np.isfinite(ledger[["weight", "weight_squared", "runs", "wickets"]].to_numpy(float)).all():
        raise ValueError("Nonfinite rating input")
    expected = np.exp2(-(pd.Timestamp(config["development_reference_date"]) - pd.to_datetime(ledger.match_date)).dt.days /
        config["recency_half_life_days"])
    if not (np.allclose(ledger.weight, expected, atol=1e-14, rtol=0) and
            np.allclose(ledger.weight_squared, ledger.weight ** 2, atol=1e-14, rtol=0)):
        raise ValueError("Rating recency differs from frozen evidence")
    return ledger, cohort, base, manifest


def outcome_scales(ledger, config):
    result = {}
    for role, group in ledger.loc[ledger.pressure_full].groupby("role", sort=True):
        result[role] = {}
        for metric in ["runs", "wickets"]:
            mean = np.average(group[metric], weights=group.weight)
            variance = np.average((group[metric] - mean) ** 2, weights=group.weight)
            result[role][metric] = max(float(np.sqrt(variance)), config["outcome_scales"]["floors"][metric])
    return result


def cell_blocks(events, matches, cells):
    """Complete-match sufficient statistics, aligned to a fixed context set."""
    shape = (len(matches), len(cells))
    blocks = {name: np.zeros(shape, dtype=float) for name in STATS}
    if events.empty or cells.empty:
        return blocks
    labels = cells[CONTEXT].reset_index(drop=True).assign(_cell=np.arange(len(cells)))
    unique(labels, CONTEXT, "rating cells")
    d = events.merge(labels, on=CONTEXT, how="inner", validate="many_to_one")
    positions = pd.Series(np.arange(len(matches)), index=matches.match_id)
    mi = d.match_id.map(positions)
    if mi.isna().any():
        raise ValueError("Event outside shared bootstrap match universe")
    index = (mi.to_numpy(int), d._cell.to_numpy(int))
    for name, column in STATS.items():
        np.add.at(blocks[name], index, 1. if column is None else d[column].to_numpy(float))
    return blocks


def multiply(blocks, multiplicities):
    if not np.isfinite(multiplicities).all() or (multiplicities < 0).any() or (multiplicities != np.floor(multiplicities)).any():
        raise ValueError("Match multiplicities must be nonnegative integers")
    return {name: multiplicities @ values for name, values in blocks.items()}


def _ratio(a, b):
    return np.divide(a, b, out=np.zeros(np.broadcast_shapes(np.shape(a), np.shape(b))), where=b > 0)


def pressure_components(own, total, scales, orientation, pseudo_events):
    """Compute oriented standardized run/wicket components in every draw.

    Squared-weight sums already count copies linearly in multiply(). Unweighted
    event counts identify actual peer loss without floating-point ghost mass.
    """
    count = total["count"] - own["count"]
    if (count < 0).any():
        raise ValueError("Evaluated player exceeds complete peer population")
    peer_mass = np.maximum(total["mass"] - own["mass"], 0.)
    mass = own["mass"].sum(axis=1)
    invalid = ((own["count"] > 0) & (count == 0)).any(axis=1) | (mass <= 0)
    neff = _ratio(mass ** 2, own["squared"].sum(axis=1))
    shrink = _ratio(neff, neff + pseudo_events)
    result = dict(effective_events=neff, mass=mass, valid=~invalid)
    for metric in ["runs", "wickets"]:
        other_mean = _ratio(total[metric] - own[metric], peer_mass)
        raw = orientation[metric] * _ratio((own[metric] - own["mass"] * other_mean).sum(axis=1), mass) / scales[metric]
        raw[invalid] = np.nan
        result[metric + "_raw"] = raw
        result[metric] = raw * shrink
    return result


def change_components(pressure, ordinary, scales, orientation, pseudo_events):
    """Same-player observed change; all original comparison groups must survive."""
    pm, om = pressure["mass"], ordinary["mass"]
    valid = ((pm > 0) & (om > 0)).all(axis=1) & (pm.sum(axis=1) > 0)
    q = _ratio(pm, pm.sum(axis=1)[:, None])
    inverse_n = (q ** 2 * (_ratio(pressure["squared"], pm ** 2) + _ratio(ordinary["squared"], om ** 2))).sum(axis=1)
    paired = _ratio(1., inverse_n)
    shrink = _ratio(paired, paired + pseudo_events)
    result = dict(paired_effective_events=paired, valid=valid)
    for metric in ["runs", "wickets"]:
        delta = (_ratio(pressure[metric], pm) - _ratio(ordinary[metric], om))
        raw = orientation[metric] * (q * delta).sum(axis=1) / scales[metric]
        raw[~valid] = np.nan
        result[metric + "_raw"] = raw
        result[metric] = raw * shrink
    return result


def mix(components, weights, raw=False):
    suffix = "_raw" if raw else ""
    return weights[0] * components["runs" + suffix] + weights[1] * components["wickets" + suffix]


def summarize_draws(point, values, config):
    finite = values[np.isfinite(values)]
    fraction = len(finite) / len(values) if len(values) else 0.
    ready = fraction >= config["bootstrap"]["minimum_finite_fraction"]
    lo, hi = np.quantile(finite, [.1, .9]) if ready else (np.nan, np.nan)
    return dict(point=float(point), p10=float(lo), p90=float(hi), finite_fraction=fraction, interval_reliable=ready)


def primary_eligibility(ledger, cohort, audit, config, base):
    keys = KEY + CONTEXT
    kept = ledger.loc[ledger.pressure_full].merge(audit.loc[audit.peer_supported, keys], on=keys, validate="many_to_one")
    stats = kept.groupby(KEY).agg(peer_pressure_events=("event_id", "size"), peer_pressure_matches=("match_id", "nunique"),
        peer_pressure_mass=("weight", "sum"), peer_pressure_squared=("weight_squared", "sum")).reset_index()
    result = cohort.merge(stats, on=KEY, how="left", validate="one_to_one")
    cols = ["peer_pressure_events", "peer_pressure_matches", "peer_pressure_mass", "peer_pressure_squared"]
    result[cols] = result[cols].fillna(0)
    result["peer_pressure_effective"] = _ratio(result.peer_pressure_mass.to_numpy() ** 2, result.peer_pressure_squared.to_numpy())
    result["peer_pressure_count_retention"] = _ratio(result.peer_pressure_events.to_numpy(), result.pressure_events.to_numpy())
    result["peer_pressure_weight_retention"] = _ratio(result.peer_pressure_mass.to_numpy(), result.pressure_weight_sum.to_numpy())
    reasons = []
    for _, row in result.iterrows():
        limits = base["roles"][row.role]
        gates = [(row.level_sample_eligible, "original_level_sample"), (row.coverage_ready, "source_coverage"),
            (row.peer_pressure_events >= limits["minimum_pressure_events"], "peer_supported_pressure_events"),
            (row.peer_pressure_matches >= base["minimum_pressure_matches"], "peer_supported_pressure_matches"),
            (row.peer_pressure_effective >= base["minimum_effective_pressure_events"], "peer_supported_effective_count"),
            (min(row.peer_pressure_count_retention, row.peer_pressure_weight_retention) >=
                config["comparison"]["minimum_pressure_retention_count_and_weight"], "peer_pressure_retention")]
        reasons.append(";".join(label for passed, label in gates if not passed))
    result["primary_blocked_reasons"] = reasons
    result["primary_sample_ready"] = result.primary_blocked_reasons.eq("")
    return result


def order_ratings(table, eligible):
    """Same sample cohort across outcome mixes; no unreliable draw quantiles."""
    result = table.merge(eligible[KEY + ["primary_sample_ready", "peer_pressure_matches"]], on=KEY, validate="many_to_one")
    result["selection_ready"] = result.primary_sample_ready & result.interval_reliable
    result["selection_score"] = result.p10.where(result.selection_ready)
    result["rank"] = np.nan
    for _, group in result.loc[result.selection_ready].groupby(["role", "variant"], sort=True):
        ordered = group.sort_values(["selection_score", "point", "peer_pressure_matches", "player_id"], ascending=[False, False, False, True])
        result.loc[ordered.index, "rank"] = np.arange(1, len(ordered) + 1)
    return result


def evaluate_development(ledger, cohort, audit, config, base, scales):
    b = config["bootstrap"]
    matches, draws = match_draws(ledger, dict(bootstrap_seed=b["seed"], bootstrap_replicates=b["replicates"], bootstrap_strata=b["strata"]))
    count = len(matches)
    # Point, registered bootstrap, every whole-match deletion and each season deletion.
    deletes = np.ones((count, count)) - np.eye(count)
    years = sorted(ledger.year.unique())
    seasons = np.array([matches.year.ne(year).to_numpy(float) for year in years])
    multipliers = np.vstack([np.ones(count), draws, deletes, seasons])
    intervals, families, influences, changes, companions = [], [], [], [], []
    eligibility = primary_eligibility(ledger, cohort, audit, config, base)
    boot_slice = slice(1, 1 + len(draws))
    delete_start = 1 + len(draws)
    for role, pressure in ledger.loc[ledger.pressure_full].groupby("role", sort=True):
        cells = pressure[CONTEXT].drop_duplicates().sort_values(CONTEXT).reset_index(drop=True)
        indexed = cells.assign(_index=np.arange(len(cells)))
        totals = multiply(cell_blocks(pressure, matches, cells), multipliers)
        actors = eligibility.loc[eligibility.role.eq(role) & eligibility.level_sample_eligible]
        for actor in actors.itertuples():
            player = actor.player_id
            own = pressure.loc[pressure.player_id.eq(player)]
            frozen = audit.loc[audit.role.eq(role) & audit.player_id.eq(player) & audit.peer_supported, CONTEXT]
            positions = frozen.merge(indexed, on=CONTEXT, validate="one_to_one")._index.to_numpy(int)
            own_values = multiply(cell_blocks(own, matches, frozen), multipliers)
            other_values = {name: array[:, positions] for name, array in totals.items()}
            components = pressure_components(own_values, other_values, scales[role], config["orientation"][role], config["role_pseudo_events"][role])
            for variant, weights in MIXES.items():
                values = mix(components, weights)
                row = dict(role=role, player_id=player, variant=variant,
                    raw_point=float(mix(components, weights, raw=True)[0]),
                    **summarize_draws(values[0], values[boot_slice], config))
                intervals.append(row)
            default = mix(components, MIXES["default_60_40"])
            own_matches = set(own.match_id)
            for i, match in enumerate(matches.itertuples()):
                influences.append(dict(role=role, player_id=player, deletion="match", removed=str(match.match_id),
                    own_pressure_match=match.match_id in own_matches, point=float(default[delete_start + i]),
                    original_point=float(default[0]), remaining_effective_events=float(components["effective_events"][delete_start + i])))
            for i, year in enumerate(years):
                remain = ledger.loc[ledger.role.eq(role) & ledger.player_id.eq(player) & ledger.year.ne(year)]
                kept = remain.loc[remain.pressure_full].merge(frozen, on=CONTEXT, validate="many_to_one")
                neff = components["effective_events"][-len(years) + i]
                limits = base["roles"][role]
                adequate = (len(remain) >= limits["minimum_total_events"] and len(kept) >= limits["minimum_pressure_events"] and
                    kept.match_id.nunique() >= base["minimum_pressure_matches"] and neff >= base["minimum_effective_pressure_events"])
                influences.append(dict(role=role, player_id=player, deletion="season", removed=str(year), own_pressure_match=False,
                    point=float(default[-len(years) + i]), original_point=float(default[0]), remaining_effective_events=float(neff),
                    remaining_sample_adequate=adequate))
            for family in sorted(frozen.family.unique()):
                mask = frozen.family.eq(family).to_numpy()
                comp = pressure_components({k: v[:, mask] for k, v in own_values.items()},
                    {k: v[:, mask] for k, v in other_values.items()}, scales[role], config["orientation"][role], config["role_pseudo_events"][role])
                values = mix(comp, MIXES["default_60_40"])
                families.append(dict(role=role, player_id=player, family=family, pressure_events=int(own.family.eq(family).sum()),
                    pressure_matches=own.loc[own.family.eq(family), "match_id"].nunique(),
                    diagnostic_only=True, **summarize_draws(values[0], values[boot_slice], config)))
            if actor.change_sample_eligible:
                all_own = ledger.loc[ledger.role.eq(role) & ledger.player_id.eq(player) & ledger.supported]
                ordinary_cells = all_own[CONTEXT].drop_duplicates().sort_values(CONTEXT).reset_index(drop=True)
                pm = multiply(cell_blocks(all_own.loc[all_own.pressure_full], matches, ordinary_cells), multipliers[:delete_start])
                om = multiply(cell_blocks(all_own.loc[~all_own.pressure_full], matches, ordinary_cells), multipliers[:delete_start])
                comp = change_components(pm, om, scales[role], config["orientation"][role], config["role_pseudo_events"][role])
                values = mix(comp, MIXES["default_60_40"])
                change_summary = summarize_draws(values[0], values[boot_slice], config)
                changes.append(dict(role=role, player_id=player, **change_summary))
                for label, weights in config["companion_level_change_weights"].items():
                    blended = weights[0] * default[:delete_start] + weights[1] * values
                    summary = summarize_draws(blended[0], blended[boot_slice], config)
                    # A combined interval cannot rescue an unreliable required component.
                    summary["interval_reliable"] &= change_summary["interval_reliable"]
                    if not summary["interval_reliable"]:
                        summary["p10"] = summary["p90"] = np.nan
                    companions.append(dict(role=role, player_id=player, variant=label, **summary))
    ratings = order_ratings(pd.DataFrame(intervals), eligibility)
    return dict(eligibility=eligibility, ratings=ratings, family_diagnostics=pd.DataFrame(families),
        influence=pd.DataFrame(influences), supported_change=pd.DataFrame(changes), companions=pd.DataFrame(companions),
        matches=matches, draws=draws)


def run_development(root):
    start = time.monotonic()
    config_path = root / "configs/descriptive_rating_v2.json"
    config = json.loads(config_path.read_text())
    ledger, cohort, base, evidence = load_development(root, config)
    out = root / "reports/descriptive_rating_development_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    scales = outcome_scales(ledger, config)
    frozen = dict(method_id=config["method_id"], config_sha256=sha256(config_path),
        evidence_manifest_sha256=sha256(root / "reports/player_evidence_development_2026-11-01/manifest.json"),
        reference_date=config["development_reference_date"], development_years=config["development_years"],
        outcome_scales=scales, reserved_outcomes_used=False)
    scale_path = out / "frozen_scales.json"
    if scale_path.exists() and json.loads(scale_path.read_text()) != frozen:
        raise ValueError("Frozen descriptive scales changed; do not overwrite or retune")
    save_json(scale_path, frozen)
    audit = pressure_peer_support(ledger, base)
    results = evaluate_development(ledger, cohort, audit, config, base, scales)
    ratings = results["ratings"]
    # Missingness and sample membership must be identical across outcome weights.
    for _, group in ratings.groupby(KEY, sort=True):
        if len(group) != 3 or group.selection_ready.nunique() != 1 or group.finite_fraction.nunique() != 1:
            raise ValueError("Outcome-weight variants differ in eligibility or finite-draw membership")
    changes = results["supported_change"]
    initial_change = pd.read_parquet(root / "reports/player_evidence_development_2026-11-01/observed_uncertainty.parquet")
    initial_change = initial_change.loc[initial_change.estimand.eq("supported_difference")].drop_duplicates(KEY)
    compare = changes.merge(initial_change[KEY + ["finite_fraction"]], on=KEY, how="outer", suffixes=("", "_initial"), indicator=True, validate="one_to_one")
    if compare._merge.ne("both").any() or not np.allclose(compare.finite_fraction, compare.finite_fraction_initial, atol=0, rtol=0):
        raise ValueError("Supported-change draw validity differs from validated initial evidence")
    rankable = ratings.loc[ratings.variant.eq("default_60_40") & ratings.selection_ready]
    summary, stability = [], []
    for role, eligible in results["eligibility"].groupby("role", sort=True):
        primary = ratings.loc[ratings.role.eq(role) & ratings.variant.eq("default_60_40")]
        ranked = rankable.loc[rankable.role.eq(role)].sort_values("rank")
        top = set(ranked.head(10).player_id)
        cv = changes.loc[changes.role.eq(role)]
        summary.append(dict(role=role, original_level_sample=int(eligible.level_sample_eligible.sum()),
            pressure_sample_and_coverage_ready=int(eligible.primary_sample_ready.sum()),
            primary_rankable=len(ranked), minimum_finite_fraction=float(primary.finite_fraction.min()),
            reliable_change_entries=int(cv.interval_reliable.sum()), development_has_ten=len(ranked) >= 10))
        for variant in MIXES:
            alt = ratings.loc[ratings.role.eq(role) & ratings.variant.eq(variant) & ratings.selection_ready].sort_values("rank")
            rank_delta = alt[["player_id", "rank"]].merge(ranked[["player_id", "rank"]], on="player_id", suffixes=("", "_default"), validate="one_to_one")
            stability.append(dict(role=role, variant=variant, eligible=len(alt), top_ten_overlap=len(top & set(alt.head(10).player_id)),
                maximum_absolute_rank_shift=float((rank_delta["rank"] - rank_delta.rank_default).abs().max())))
    for name in ["eligibility", "ratings", "family_diagnostics", "influence", "supported_change", "companions"]:
        results[name].to_parquet(out / f"{name}.parquet", index=False)
    audit.to_csv(out / "pressure_peer_support.csv", index=False)
    results["matches"].to_csv(out / "bootstrap_matches.csv", index=False)
    np.save(out / "bootstrap_multiplicities.npy", results["draws"], allow_pickle=False)
    pd.DataFrame(stability).to_csv(out / "outcome_weight_stability.csv", index=False)
    # Every table stays private; top-ten output is labelled development, not final selection.
    rankable.loc[rankable["rank"].le(10)].merge(cohort[KEY + ["player_name"]], on=KEY, validate="one_to_one").to_csv(
        out / "development_top_ten_diagnostic.csv", index=False)
    feasible = all(row["development_has_ten"] for row in summary)
    gate = dict(method_id=config["method_id"], approved_method_implemented=True,
        development_execution_completed=True, development_feasible=feasible,
        development_only=True, context_comparability_fully_established=False,
        predictive_calibration_claim=False, final_rankings_permitted=False,
        reserved_outcomes_evaluated=False, full_dossiers_produced=False,
        next_stage="Review development sensitivity and counterexamples, then freeze the separate reserved evaluation stage." if feasible else
            "Report insufficient development candidates; do not relax gates or start automatic experiments.")
    save_json(out / "development_gate.json", gate)
    save_json(out / "summary.json", summary)
    lines = ["# Descriptive pressure rating: development validation", "",
        "Window: verified 2023–2025 only; reference date 31 December 2025. These are development diagnostics, not the final lists.", "",
        "Approved method: `descriptive_peer_pressure_v2`. No predictive model fitted or promoted; historical failed gates are preserved.",
        "The peer benchmark excludes all role observations of the evaluated player. All player/peer means are recomputed in 1,000 shared whole-match draws.",
        "Scale constants are frozen development outcome SDs. Uncertainty remains conditional on retained data, fixed support/eligibility and these constants.", "",
        "| Role | Original level sample | Primary sample + coverage | Rankable after uncertainty | Minimum finite fraction | Reliable supported change |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in summary:
        lines.append(f"| {row['role']} | {row['original_level_sample']} | {row['pressure_sample_and_coverage_ready']} | {row['primary_rankable']} | {row['minimum_finite_fraction']:.3f} | {row['reliable_change_entries']} |")
    lines.extend(["", "See `outcome_weight_stability.csv` for identical-cohort 60/40, 50/50 and 70/30 runs/wickets sensitivity.",
        "`influence.parquet` recomputes player and peer contributions after removing every match or season. Match-deletion results are point sensitivities, not new bootstrap rankings; remaining season sample adequacy is reported separately.",
        "`family_diagnostics.parquet` gives IPL/T20I evidence separately; it is not a family-specific eligible selection list.",
        "Supported ordinary change and both companion weightings remain withheld from decision ordering when their required component has unreliable draws.", "",
        "## Selection limitations", "",
        "Broad context matching does not fully measure target difficulty, exact ball state, venue or opposition strength. Relative T20I performance is not proof of IPL transfer.",
        "Source retention is unequal. Excluded players are insufficient-evidence cases, not poor performers. The main pressure ordering does not require ordinary controls.",
        "Sensitivity, role evidence, adverse cases and credible alternatives must accompany selections. No rule is retuned to favour a variant or preferred player.", "",
        "## Next stage", "", gate["next_stage"],
        "Reserved 2026 outcomes were not read by this command; full dossiers and final rankings remain unfinished.", ""])
    (out / "REPORT.md").write_text("\n".join(lines))
    for path, digest in evidence["preserved_gate_sha256"].items():
        if sha256(root / path) != digest:
            raise ValueError("A historical prediction gate changed during descriptive scoring")
    if json.loads(scale_path.read_text()) != frozen:
        raise ValueError("Frozen scales changed during execution")
    code = ["descriptive_rating.py", "player_evidence.py", "baseline.py", "data.py"]
    save_json(out / "manifest.json", dict(method_id=config["method_id"],
        config_sha256=sha256(config_path), evidence_manifest_sha256=frozen["evidence_manifest_sha256"],
        frozen_scales_sha256=sha256(scale_path), development_years=config["development_years"],
        reference_date=config["development_reference_date"], reserved_outcomes_read=False,
        predictive_models_fitted=False, new_predictive_bundles=0, cumulative_predictive_bundles=20,
        final_rankings_created=False, full_dossiers_created=False,
        preserved_gate_sha256=evidence["preserved_gate_sha256"],
        code_sha256={"src/rr_pressure/" + name: sha256(root / "src/rr_pressure" / name) for name in code},
        output_sha256={p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "manifest.json"},
        elapsed_seconds=round(time.monotonic() - start, 2)))
    print(json.dumps(dict(summary=summary, gate=gate, elapsed_seconds=round(time.monotonic() - start, 2)), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    run_development(args.root.resolve())


if __name__ == "__main__":
    main()
