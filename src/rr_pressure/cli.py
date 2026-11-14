from __future__ import annotations

import argparse
import importlib.metadata
from pathlib import Path
import json
import time

import pandas as pd

from .data import fingerprints, load, save_json, sha256
from .eda import build_tables
from .report import make_figures, make_report
from .state import build_states

FEATURES = ["event_id", "match_id", "innings", "innings_ball_num", "striker_id", "bowler_id",
            "comp_id", "family", "match_date", "year", "venue_id", "venue_country", "phase", "overid",
            "legal_balls_before", "balls_remaining", "wickets_before", "recent_wickets", "late",
            "collapse_recent", "collapse_early", "collapse", "pressure_proxy", "batting_type", "bowling_type"]


def run_eda(root):
    start = time.perf_counter()
    config_path = root / "configs/analysis_preregistration.json"
    config = json.loads(config_path.read_text())
    if config["data_cutoff_inclusive"] != "2026-11-01":
        raise ValueError("Approved cutoff must remain 2026-11-01")
    source = root / "6af3166e7b922_data_pack"
    before = fingerprints(source)
    out = root / "reports" / "eda_2026-11-01"
    processed = root / "data" / "processed"
    for directory in (out, out / "tables", out / "audit", processed):
        directory.mkdir(parents=True, exist_ok=True)
    _, matches, deliveries, players, audit = load(root, config["data_cutoff_inclusive"])
    print(f"Loaded {len(deliveries):,} events; dimension joins preserved rows.", flush=True)
    events, ledger = build_states(deliveries, matches, config)
    print(f"Built {int(events.eligible_proxy.sum()):,} accepted proxy states; exact scores remain unverified.", flush=True)
    events.to_parquet(processed / "score_independent_states.parquet", index=False)
    matches.to_parquet(processed / "matches.parquet", index=False)
    players.to_parquet(processed / "players.parquet", index=False)
    accepted = events.loc[events.eligible_proxy]
    accepted[FEATURES].to_parquet(processed / "preball_features.parquet", index=False)
    accepted[["event_id", "recorded_runs", "is_wicket", "dismissed_player_id", "bowler_credited_wicket",
              "striker_bowler_dismissal", "extras_type", "boundary_flag", "legal_delivery"]].to_parquet(
                  processed / "delivery_outcomes.parquet", index=False)
    tables = build_tables(matches, events, ledger, config)
    for name, frame in tables.items():
        frame.to_csv(out / "tables" / f"{name}.csv", index=False, float_format="%.6f")
    tables["player_match_metrics"].to_parquet(processed / "player_match_metrics.parquet", index=False)
    for name, frame in audit.items():
        frame.to_csv(out / "audit" / f"{name}.csv", index=False)
    save_json(out / "audit" / "feature_contract.json", {
        "features": FEATURES, "score_fields_available": False, "pressure_definition": "late OR collapse proxy",
        "not_available": ["score_before", "chase_target", "required_run_rate", "tight_chase", "pressure_full"],
        "outcomes_stored_separately": True, "current_batting_order_excluded_from_features": True,
    })
    save_json(out / "audit" / "preregistered_settings.json", config)
    print("Computed phase metrics, chasing outcomes and player sample coverage; rendering charts.", flush=True)
    figures = make_figures(tables, events, out)
    make_report(tables, events, ledger, audit, out, figures, config)
    if fingerprints(source) != before:
        raise ValueError("Source files changed during analysis")
    # Compare the independently implemented proxy against the prior verified audit population.
    reference_path = root / "artifacts/reconciliation_2026-11-01/pressure_included_innings.csv"
    regression = None
    if reference_path.exists():
        reference = pd.read_csv(reference_path, dtype={"match_id": str})
        reference = reference[reference.family.isin(["IPL", "T20I"])]
        old_keys = set(zip(reference.match_id, reference.innings))
        new_keys = set(zip(ledger[ledger.eligible_proxy].match_id, ledger[ledger.eligible_proxy].innings))
        regression = old_keys == new_keys and int(reference.events.sum()) == len(accepted)
        if not regression:
            raise ValueError("Proxy cohort differs from the approved reconciliation; review required")
        prior_counts = pd.read_csv(reference_path.parent / "pressure_detail.csv")
        prior_counts = prior_counts[prior_counts.family.isin(["IPL", "T20I"]) & prior_counts.denominator.eq("delivery_events")]
        if int(prior_counts.base.sum()) != int(accepted.pressure_proxy.sum()):
            raise ValueError("Pressure flags differ from the approved reconciliation")
    outputs = {str(p.relative_to(root)): sha256(p) for directory in (out, processed) for p in sorted(directory.rglob("*"))
               if p.is_file() and p.name != "manifest.json"}
    manifest = {
        "milestone": "score-independent EDA", "cutoff_inclusive": config["data_cutoff_inclusive"],
        "source_sha256": before, "raw_inputs_unchanged": True, "config_sha256": sha256(config_path),
        "code_sha256": {str(p.relative_to(root)): sha256(p) for p in sorted((root / "src").rglob("*.py"))},
        "lockfile_sha256": sha256(root / "uv.lock"),
        "versions": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "pyarrow", "matplotlib"]},
        "output_sha256": outputs, "random_seed": 1729, "eda_match_bootstrap_replicates": config["bootstrap"]["debug_replicates"],
        "rows": len(events), "accepted_proxy_rows": len(accepted), "proxy_pressure_rows": int(accepted.pressure_proxy.sum()),
        "reconciliation_regression_pass": regression, "mode_a_ready": False,
        "external_data_used": False, "player_rankings_created": False, "elapsed_seconds": round(time.perf_counter() - start, 2),
    }
    save_json(out / "manifest.json", manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k in ["rows", "accepted_proxy_rows", "proxy_pressure_rows", "elapsed_seconds", "reconciliation_regression_pass"]}, indent=2))
    print(f"Report: {out / 'REPORT.md'}")


def main():
    parser = argparse.ArgumentParser(description="Private RR analysis pipeline")
    parser.add_argument("command", choices=["eda", "select-pilot", "fetch-cricsheet", "reconcile-pilot", "reconcile-full", "pressure-validate", "prepare-method", "fit-baseline", "fit-context-baseline", "audit-reference", "fit-retrospective-reference", "review-reference", "build-player-evidence"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    if args.command == "eda":
        run_eda(args.root.resolve())
    elif args.command == "build-player-evidence":
        from .player_evidence import build_player_evidence
        build_player_evidence(args.root.resolve())
    elif args.command == "review-reference":
        from .reference_review import run_reference_review
        run_reference_review(args.root.resolve())
    elif args.command == "fit-retrospective-reference":
        from .retrospective_reference import run_retrospective_reference
        run_retrospective_reference(args.root.resolve())
    elif args.command == "audit-reference":
        from .reference_audit import run_reference_audit
        run_reference_audit(args.root.resolve())
    elif args.command == "fit-context-baseline":
        from .context_baseline import run_context_baseline
        run_context_baseline(args.root.resolve())
    elif args.command == "fit-baseline":
        from .baseline import run_baseline
        run_baseline(args.root.resolve())
    elif args.command == "prepare-method":
        from .supported_method import prepare_method
        prepare_method(args.root.resolve())
    elif args.command == "pressure-validate":
        from .pressure_validation import validate_pressure
        validate_pressure(args.root.resolve())
    elif args.command == "reconcile-full":
        from .coverage import run_full
        run_full(args.root.resolve())
    elif args.command == "reconcile-pilot":
        from .alignment import run_pilot
        run_pilot(args.root.resolve())
    else:
        from .external import fetch, freeze_pilot
        {"select-pilot": freeze_pilot, "fetch-cricsheet": fetch}[args.command](args.root.resolve())


if __name__ == "__main__":
    main()
