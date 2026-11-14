"""Frozen reserved-year and final-window descriptive evaluation; no method search."""

import argparse
import json
from pathlib import Path
import subprocess
import time

import numpy as np
import pandas as pd

from .data import fingerprints, save_json, sha256, unique
from .descriptive_rating import evaluate_development, validate_config, MIXES
from .player_dossiers import build_dossiers, markdown_table
from .player_evidence import (DETAILS, TARGETS, KEY, pressure_peer_support, role_ledger,
    summarize, uncertainty, validate_tables)
from .supported_method import delivery_tables


def verify_outputs(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    for name, digest in manifest["output_sha256"].items():
        if sha256(directory / name) != digest:
            raise ValueError("Frozen input changed: " + str(directory / name))
    return manifest


def validate_protocol(root, protocol):
    """No outcome read is permitted until the reviewed protocol is in Git."""
    path = root / "configs/final_window_v1.json"
    recorded = subprocess.run(["rtk", "proxy", "git", "show", "HEAD:configs/final_window_v1.json"],
        cwd=root, text=True, capture_output=True, check=False)
    if recorded.returncode or recorded.stdout != path.read_text():
        raise ValueError("Final-window protocol must be committed unchanged before reserved outcome access")
    if (protocol["cutoff_inclusive"] != "2026-11-01" or protocol["method_changes_permitted"] or
            protocol["predictive_fits_permitted"] or not protocol["user_authorized_final_evaluation"] or
            protocol["window_order"] != ["reserved_2026", "final_2023_2026"]):
        raise ValueError("Invalid frozen final-window execution boundary")
    for name, digest in protocol["frozen_sha256"].items():
        if sha256(root / name) != digest:
            raise ValueError("Frozen final-window dependency changed: " + name)
    config = json.loads((root / "configs/descriptive_rating_v2.json").read_text())
    base = validate_config(root, config)
    development = root / "reports/descriptive_rating_development_2026-11-01"
    verify_outputs(development)
    if not json.loads((development / "development_gate.json").read_text())["development_feasible"]:
        raise ValueError("Development feasibility has not passed")
    dossier = root / "reports/player_dossiers_development_2026-11-01"
    review = verify_outputs(dossier)
    if not review.get("priority_agent_review_completed_before_reserved_outcomes"):
        raise ValueError("Development counterexample interpretation is incomplete")
    frozen = json.loads((development / "frozen_scales.json").read_text())
    if frozen["reserved_outcomes_used"] or frozen["development_years"] != [2023, 2024, 2025]:
        raise ValueError("Normalization is not frozen development-only evidence")
    return config, base, frozen["outcome_scales"]


def validate_dates(ids, window):
    if ids.empty:
        raise ValueError("Empty final-window evidence")
    dates = pd.to_datetime(ids.match_date, format="%Y-%m-%d", errors="raise")
    if (not dates.dt.year.eq(ids.year).all() or not ids.match_date.between(window["first_date"], window["last_date"]).all() or
            ids.year.lt(2023).any() or ids.match_date.gt("2026-11-01").any()):
        raise ValueError("Event outside frozen final-window dates or year attribution")
    unique(ids[["match_id", "match_date", "year"]].drop_duplicates(), ["match_id"], "final match chronology")


def load_window(root, window, base, upstream, reconciliation):
    """Project outcomes only after date-filtered IDs and independently reproduce targets."""
    source = root / "reports/supported_method_2026-11-01"
    ids = pd.read_parquet(source / "identities_and_exposures.parquet",
        filters=[("match_date", ">=", window["first_date"]), ("match_date", "<=", window["last_date"])])
    validate_dates(ids, window)
    selected = ids.event_id.tolist()
    filters = [("event_id", "in", selected)]
    features = pd.read_parquet(source / "features.parquet", filters=filters)
    targets = pd.read_parquet(source / "targets.parquet", columns=["event_id", *TARGETS], filters=filters)
    details = pd.read_parquet(root / "reports/full_reconciliation_2026-11-01/verified_events.parquet",
        columns=DETAILS, filters=filters)
    for table in [ids, features, targets, details]:
        unique(table, ["event_id"], "final-window input")
        if set(table.event_id) != set(selected):
            raise ValueError("Incomplete final-window input")
    if not (details.match_accepted & details.score_verified & details.event_alignment_pass).all():
        raise ValueError("Unverified final event")
    reproduced = delivery_tables(details)
    for observed, expected in zip([features, ids, targets], reproduced):
        pd.testing.assert_frame_equal(observed.sort_values("event_id").reset_index(drop=True),
            expected[observed.columns].sort_values("event_id").reset_index(drop=True), check_dtype=False)
    extra = details.drop(columns=[c for c in details if c != "event_id" and (c in ids or c in features or c in targets)])
    data = ids.merge(features, on="event_id", validate="one_to_one").merge(targets, on="event_id", validate="one_to_one").merge(
        extra, on="event_id", validate="one_to_one")
    players, cells = [], []
    for role in ["batting", "bowling"]:
        prefix = window["exposure_prefix"] + "_" + role
        players.append(pd.read_csv(source / (prefix + "_players.csv"), dtype={"player_id": str}))
        cells.append(pd.read_csv(source / (prefix + "_player_cells.csv"), dtype={"player_id": str}).assign(role=role))
    cohort = pd.concat(players, ignore_index=True)
    ledger = role_ledger(data, pd.concat(cells, ignore_index=True), dict(reference_date=window["reference_date"],
        recency_half_life_days=base["recency_half_life_days"]))
    names = ledger[KEY + ["player_name"]].drop_duplicates().sort_values(KEY + ["player_name"])
    labels = names.groupby(KEY).agg(player_name=("player_name", "first"), name_alias_count=("player_name", "nunique")).reset_index()
    cohort = cohort.merge(labels, on=KEY, how="left", validate="one_to_one")
    contexts = summarize(ledger, KEY + ["family", "year", "innings", "phase", "wicket_band", "pressure_full", "supported"])
    validate_tables(data, ledger, cohort, contexts, {"expected": window["expected"]})
    return ledger, cohort


def evaluation_summary(results):
    rows, stability = [], []
    for role in ["batting", "bowling"]:
        ratings = results["ratings"]
        default = ratings.loc[ratings.role.eq(role) & ratings.variant.eq("default_60_40")]
        qualified = default.loc[default.selection_ready].sort_values("rank")
        rows.append(dict(role=role, level_sample_eligible=len(default), primary_rankable=len(qualified),
            minimum_finite_fraction=float(default.finite_fraction.min()), enough_for_ten=len(qualified) >= 10))
        for variant in MIXES:
            other = ratings.loc[ratings.role.eq(role) & ratings.variant.eq(variant) & ratings.selection_ready].sort_values("rank")
            if set(other.player_id) != set(qualified.player_id):
                raise ValueError("Final outcome variants changed eligible cohort")
            stability.append(dict(role=role, variant=variant, eligible=len(other),
                top_ten_overlap=len(set(other.head(10).player_id) & set(qualified.head(10).player_id))))
    return rows, pd.DataFrame(stability)


def temporal_review(development, reserved, final, reserved_cohort, reserved_ledger):
    keys = KEY
    dev = development.loc[development.variant.eq("default_60_40") & development.selection_ready,
        keys + ["rank", "point"]].rename(columns={"rank": "development_rank", "point": "development_point"})
    r = reserved.loc[reserved.variant.eq("default_60_40"), keys + ["point", "selection_ready", "finite_fraction"]].rename(
        columns={"point": "reserved_point", "selection_ready": "adequate_reserved_rating", "finite_fraction": "reserved_finite_fraction"})
    f = final.loc[final.variant.eq("default_60_40"), keys + ["rank", "selection_ready"]].rename(
        columns={"rank": "final_rank", "selection_ready": "final_selection_ready"})
    result = dev.merge(reserved_cohort[keys + ["pressure_events", "pressure_matches", "retained_fraction"]], on=keys, how="left", validate="one_to_one").merge(
        r, on=keys, how="left", validate="one_to_one").merge(f, on=keys, how="left", validate="one_to_one")
    observed = summarize(reserved_ledger.loc[reserved_ledger.pressure_full], keys)
    result = result.merge(observed[keys + ["runs_per_100", "wickets_per_100"]], on=keys, how="left", validate="one_to_one")
    result["reserved_evidence_status"] = np.select([result.pressure_events.isna() | result.pressure_events.eq(0),
        result.adequate_reserved_rating.eq(True)], ["no_retained_pressure_evidence", "adequate_reserved_rating"], default="insufficient_reserved_sample_or_coverage")
    return result


def run(root):
    start = time.monotonic()
    protocol_path = root / "configs/final_window_v1.json"
    protocol = json.loads(protocol_path.read_text())
    config, base, scales = validate_protocol(root, protocol)
    preflight = root / "reports/supported_method_2026-11-01"
    upstream = json.loads((preflight / "manifest.json").read_text())
    source = root / "reports/full_reconciliation_2026-11-01"
    reconciliation = json.loads((source / "manifest.json").read_text())
    if upstream["source_sha256"] != fingerprints(root / "6af3166e7b922_data_pack"):
        raise ValueError("Frozen raw source corpus changed")
    for name in ["identities_and_exposures.parquet", "features.parquet", "targets.parquet"]:
        if sha256(preflight / name) != upstream["output_sha256"][name]:
            raise ValueError("Frozen final-window preflight changed")
    if sha256(source / "verified_events.parquet") != reconciliation["output_sha256"]["verified_events.parquet"]:
        raise ValueError("Reconciled event corpus changed")
    for window in protocol["windows"].values():
        for role in ["batting", "bowling"]:
            for suffix in ["players", "player_cells"]:
                name = f"{window['exposure_prefix']}_{role}_{suffix}.csv"
                if sha256(preflight / name) != upstream["output_sha256"][name]:
                    raise ValueError("Frozen final exposure/support table changed")
    out = root / "reports/final_window_evaluation_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    collected = {}
    for label in protocol["window_order"]:
        window = protocol["windows"][label]
        ledger, cohort = load_window(root, window, base, upstream, reconciliation)
        audit = pressure_peer_support(ledger, base)
        results = evaluate_development(ledger, cohort, audit, config, base, scales)
        # Observed metric intervals complement the peer-relative rating interval.
        evidence_config = json.loads((root / "configs/player_evidence_v1.json").read_text())
        observed_ci, _, _ = uncertainty(ledger, cohort, evidence_config)
        results["observed_uncertainty"] = observed_ci
        summary, stability = evaluation_summary(results)
        if label == "final_2023_2026" and not all(row["enough_for_ten"] for row in summary):
            raise ValueError("Fewer than ten qualifying final candidates: do not relax frozen gates")
        directory = out / label
        directory.mkdir(parents=True, exist_ok=True)
        for name in ["eligibility", "ratings", "family_diagnostics", "influence", "supported_change", "companions", "observed_uncertainty"]:
            results[name].to_parquet(directory / (name + ".parquet"), index=False)
        ledger.to_parquet(directory / "event_role_ledger.parquet", index=False)
        cohort.to_csv(directory / "cohort_register.csv", index=False)
        results["matches"].to_csv(directory / "bootstrap_matches.csv", index=False)
        np.save(directory / "bootstrap_multiplicities.npy", results["draws"], allow_pickle=False)
        stability.to_csv(directory / "outcome_weight_stability.csv", index=False)
        save_json(directory / "summary.json", summary)
        # Reserved-year sample requirements are deliberately not relaxed to fill ten places.
        ranked = results["ratings"].loc[results["ratings"].variant.eq("default_60_40") & results["ratings"].selection_ready].merge(
            cohort[KEY + ["player_name"]], on=KEY, validate="one_to_one").sort_values(["role", "rank"])
        ranked.to_csv(directory / "ranked_diagnostics.csv", index=False)
        if label == "final_2023_2026":
            frames = build_dossiers(root, ledger, cohort, results, directory / "player_dossiers", "2023–1 November 2026 final window",
                {"protocol_sha256": sha256(protocol_path), "frozen_scales_sha256": protocol["frozen_sha256"]["reports/descriptive_rating_development_2026-11-01/frozen_scales.json"]})
            for role in ["batting", "bowling"]:
                ranked.loc[ranked.role.eq(role)].to_csv(directory / f"ranked_{role}.csv", index=False)
            top = ranked.loc[ranked["rank"].le(10)]
            if len(top) != 20 or top.duplicated(KEY).any():
                raise ValueError("Final analytical lists do not contain ten unique IDs per role")
            top.to_csv(out / "two_top_ten_lists.csv", index=False)
        collected[label] = (results, cohort, ledger, summary)
        print(json.dumps({"window": label, "summary": summary}), flush=True)
    development = pd.read_parquet(root / "reports/descriptive_rating_development_2026-11-01/ratings.parquet")
    reserved, rc, rl, rs = collected["reserved_2026"]
    final, fc, fl, fs = collected["final_2023_2026"]
    temporal = temporal_review(development, reserved["ratings"], final["ratings"], rc, rl)
    temporal.to_csv(out / "temporal_review.csv", index=False)
    final_top = pd.read_csv(out / "two_top_ten_lists.csv", dtype={"player_id": str})
    gate = dict(protocol_id=protocol["protocol_id"], method_unchanged=True, development_scales_unchanged=True,
        source_and_exposure_reconciliation_passed=True, reserved_year_evaluated=True,
        final_window_evaluated=True, enough_final_candidates=True, analytical_top_tens_created=True,
        submission_ready=False, dropdown_mapping_verified=False, predictive_calibration_claim=False,
        prior_2026_aggregate_EDA_disclosed=True)
    save_json(out / "evaluation_gate.json", gate)
    lines = ["# Frozen final-window evaluation", "",
        "Protocol was committed before reserved outcome access. Same approved method, pressure thresholds, coverage/support gates, 730-day recency, frozen development scales and 1,000 joint whole-match draws. No predictive fit or method tuning.", "",
        "2026 is a retrospective reserved-period check with prior aggregate EDA exposure; it is not pristine unseen forecast validation.", "",
        "## Window feasibility", "", markdown_table(pd.DataFrame([dict(window=label, **row) for label, (_, _, _, rows) in collected.items() for row in rows])), "",
        "One-year reserved diagnostics keep the multi-year sample minima. Missing/insufficient reserved evidence is unavailable, not poor performance; ten reserved-year batting qualifiers are not required.", "",
        "## Two analytical top-ten lists", "", markdown_table(final_top[["role", "rank", "player_id", "player_name", "selection_score", "point", "p90", "finite_fraction"]].round(5)), "",
        "The ordered lists are analytical recommendations for the retained corpus. Evidence cards, role profiles, supporting/adverse cases and alternatives are in `final_2023_2026/player_dossiers/`. Current platform dropdown matching and final submission packaging are not verified.", "",
        "## Temporal and robustness review", "",
        "`temporal_review.csv` tracks every development-qualified player into 2026-only and combined evidence. Rank changes involve additional data, recency and eligibility changes; they are not a paired forecast accuracy or causal year effect.",
        "Outcome-weight sensitivity remains on an identical cohort within each window. Family, match and season diagnostics are unchanged descriptive checks. Close intervals, sparse phases, source coverage and unmeasured opposition/venue context must qualify the selection rationale.", "",
        "No unavailable change is filled with zero; conditional level/change companion orderings cannot rescue unreliable required components. Preserve all historical failed prediction gates.", ""]
    (out / "REPORT.md").write_text("\n".join(lines))
    for name, digest in protocol["frozen_sha256"].items():
        if sha256(root / name) != digest:
            raise ValueError("Frozen dependency changed during final evaluation")
    save_json(out / "manifest.json", dict(protocol_sha256=sha256(protocol_path), method_config_sha256=sha256(root / "configs/descriptive_rating_v2.json"),
        frozen_dependencies=protocol["frozen_sha256"], reserved_outcomes_read=True, predictive_fits=0,
        method_or_threshold_changes=False, final_cutoff_inclusive="2026-11-01",
        output_sha256={str(p.relative_to(out)): sha256(p) for p in sorted(out.rglob("*")) if p.is_file() and p != out / "manifest.json"},
        elapsed_seconds=round(time.monotonic() - start, 2)))
    print(json.dumps({"gate": gate, "elapsed_seconds": round(time.monotonic() - start, 2)}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    run(parser.parse_args().root.resolve())
