"""Outcome-free feasibility of contemporary, whole-match-excluded references."""

import hashlib
import json

import numpy as np
import pandas as pd

from .data import fingerprints, save_json, sha256, unique
from .pilot_report import markdown_table


CONTEXT = ["year", "family", "innings", "phase", "wicket_band"]
INPUTS = ["event_id", "match_id", "match_date", *CONTEXT,
          "pressure_full", "batting_opportunity"]


def validate_exposures(data, config):
    if set(data.columns) != set(INPUTS) or data.isna().any().any():
        raise ValueError("Exposure allowlist or missing-data violation")
    unique(data, ["event_id"], "reference audit events")
    matches = data[["match_id", "match_date", "year", "family"]].drop_duplicates()
    unique(matches, ["match_id"], "reference audit matches")
    if data.empty or not data.year.isin(config["development_years"]).all():
        raise ValueError("Development exposures only")
    dates = pd.to_datetime(data.match_date, format="%Y-%m-%d", errors="raise")
    if not dates.dt.year.eq(data.year).all() or dates.gt(config["cutoff_inclusive"]).any():
        raise ValueError("Date/year or cutoff violation")
    if not data.family.isin(["IPL", "T20I"]).all():
        raise ValueError("Unexpected competition family")
    for column in ["pressure_full", "batting_opportunity"]:
        if data[column].dtype != bool:
            raise ValueError("Exposure flags must be Boolean")


def match_partitions(data, config):
    """Balanced fixed hash partition, independent of event order and outcomes."""
    validate_exposures(data, config)
    if config["folds"] != 2:
        raise ValueError("Only the frozen two-fold procedure is permitted")
    matches = data[["match_id", "match_date", "year", "family"]].drop_duplicates().copy()
    matches["partition_hash"] = matches.match_id.map(lambda value: hashlib.sha256(
        (config["partition_salt"] + ":" + str(value)).encode()).hexdigest())
    matches = matches.sort_values(["year", "family", "partition_hash", "match_id"])
    matches["evaluation_fold"] = matches.groupby(["year", "family"]).cumcount() % 2
    return matches.reset_index(drop=True)


def peer_counts(data, keys, scheme):
    """Count other-match peers, never targets; exclude both innings at all levels."""
    blocks = data.groupby(keys + ["match_id", "evaluation_fold"], observed=True).size().rename("events").reset_index()
    if scheme == "leave_match_out":
        table = blocks.groupby(keys, observed=True).agg(
            all_events=("events", "sum"), all_matches=("match_id", "size")).reset_index()
        counts = blocks.merge(table, on=keys, validate="many_to_one")
        counts["peer_events"] = counts.all_events - counts.events
        counts["peer_matches"] = counts.all_matches - 1
        counts = counts[keys + ["match_id", "peer_events", "peer_matches"]]
        return data[keys + ["match_id"]].merge(counts, on=keys + ["match_id"],
            how="left", validate="many_to_one")[["peer_events", "peer_matches"]]
    if scheme != "two_fold":
        raise ValueError("Unknown reference scheme")
    table = blocks.groupby(keys + ["evaluation_fold"], observed=True).agg(
        peer_events=("events", "sum"), peer_matches=("match_id", "size")).reset_index()
    table["evaluation_fold"] = 1 - table.evaluation_fold
    return data[keys + ["evaluation_fold"]].merge(table, on=keys + ["evaluation_fold"],
        how="left", validate="many_to_one")[["peer_events", "peer_matches"]].fillna(0).astype(int)


def audit_exposures(data, config):
    partitions = match_partitions(data, config)
    data = data.merge(partitions[["match_id", "evaluation_fold"]], on="match_id", validate="many_to_one")
    rows = []
    for role in ["batting", "bowling"]:
        d = (data.loc[data.batting_opportunity] if role == "batting" else data).reset_index(drop=True)
        for scheme in ["leave_match_out", "two_fold"]:
            finest = peer_counts(d, CONTEXT, scheme)
            parent = peer_counts(d, ["year", "family"], scheme)
            supported = ((finest.peer_events >= config["minimum_peer_events"]) &
                         (finest.peer_matches >= config["minimum_peer_matches"]))
            parent_ok = ((parent.peer_events >= config["minimum_peer_events"]) &
                         (parent.peer_matches >= config["minimum_peer_matches"]))
            annotated = d.assign(peer_events=finest.peer_events, peer_matches=finest.peer_matches,
                                 supported=supported, parent_supported=parent_ok)
            for (year, family), group in annotated.groupby(["year", "family"], sort=True):
                for exposure in ["all", "pressure"]:
                    part = group.loc[group.pressure_full] if exposure == "pressure" else group
                    rows.append(dict(scheme=scheme, role=role, year=int(year), family=family, exposure=exposure,
                        events=len(part), matches=part.match_id.nunique(), supported_events=int(part.supported.sum()),
                        supported_fraction=float(part.supported.mean()) if len(part) else np.nan,
                        parent_unsupported_events=int((~part.parent_supported).sum()),
                        zero_peer_events=int(part.peer_events.eq(0).sum()),
                        minimum_peer_matches=int(part.peer_matches.min()) if len(part) else 0,
                        median_peer_events=float(part.peer_events.median()) if len(part) else 0))
    return partitions, pd.DataFrame(rows)


def load_exposures(root, config):
    """Do not open targets.parquet or the verified outcomes, even for development."""
    source = root / "reports/supported_method_2026-11-01"
    manifest = json.loads((source / "manifest.json").read_text())
    if manifest["source_sha256"] != fingerprints(root / "6af3166e7b922_data_pack"):
        raise ValueError("Raw sources changed")
    for key, filename in [("config_sha256", "supported_method_v1.json"),
                          ("analysis_config_sha256", "analysis_preregistration.json")]:
        if manifest[key] != sha256(root / "configs" / filename):
            raise ValueError("Frozen upstream configuration changed")
    for name in ["features.parquet", "identities_and_exposures.parquet"]:
        if manifest["output_sha256"][name] != sha256(source / name):
            raise ValueError("Exposure artifact changed: " + name)
    identities = pd.read_parquet(source / "identities_and_exposures.parquet",
        columns=["event_id", "match_id", "match_date", "year", "pressure_full", "batting_opportunity"],
        filters=[("year", "in", config["development_years"])])
    features = pd.read_parquet(source / "features.parquet", columns=["event_id", *CONTEXT[1:]],
        filters=[("event_id", "in", identities.event_id.tolist())])
    if set(features.event_id) != set(identities.event_id):
        raise ValueError("Incomplete exposure inputs")
    data = identities.merge(features, on="event_id", validate="one_to_one")[INPUTS]
    validate_exposures(data, config)
    return data


def run_reference_audit(root):
    config_path = root / "configs/retrospective_reference_v1.json"
    config = json.loads(config_path.read_text())
    data = load_exposures(root, config)
    partitions, support = audit_exposures(data, config)
    candidate = support.loc[support.scheme.eq("two_fold")]
    feasible = bool(candidate.supported_fraction.ge(config["minimum_finest_support_fraction"]).all()
                    and candidate.parent_unsupported_events.eq(0).all())
    out = root / "reports/reference_audit_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    frozen = out / "frozen_reference_config.json"
    if frozen.exists() and json.loads(frozen.read_text()) != config:
        raise ValueError("Reference specification changed; version the amendment")
    save_json(frozen, config)
    partitions.to_csv(out / "match_partitions.csv", index=False)
    support.to_csv(out / "peer_support.csv", index=False)
    gate = dict(outcomes_read=False, new_model_bundles_used=0, historical_bundles_used=18,
                peer_support_feasible=feasible, development_fitting_permitted=feasible,
                reserved_outcomes_permitted=False, reference_promoted=False, player_scores_created=False,
                minimum_finest_support_fraction=float(candidate.supported_fraction.min()),
                decision="Implement the frozen two-fold development reference next." if feasible else
                         "Stop before fitting; peer support fails the frozen feasibility screen.")
    save_json(out / "feasibility_gate.json", gate)
    summary = support.groupby(["scheme", "role", "exposure"]).agg(
        events=("events", "sum"), supported_events=("supported_events", "sum"),
        minimum_stratum_fraction=("supported_fraction", "min"),
        parent_unsupported_events=("parent_unsupported_events", "sum")).reset_index()
    summary["supported_fraction"] = summary.supported_events / summary.events
    report = ["# Retrospective reference feasibility audit", "",
        "Cricket question: can we compare a player's performance with contemporary peers in the same innings phase and wicket state, without using the evaluated match to set its own reference?", "",
        f"Development only: {data.match_id.nunique():,} matches, {len(data):,} delivery events. No target file opened; no model fitted or player score computed.", "",
        markdown_table(summary), "",
        "Leave-match-out counts are an upper-information comparison only, not fitted models. The recommended two-fold design excludes the entire evaluated partition, including both innings of every evaluated match. Counts include pressure and ordinary peer events; these are level-reference support counts, not supported-change eligibility.", "",
        f"Feasibility screen passed: **{feasible}**. The minimum all/pressure year × family × role supported fraction is {candidate.supported_fraction.min():.4%}. This establishes peer availability, not calibration or prediction quality.", "",
        "The same-season reference can use matches later than the evaluated match, within the frozen cutoff. It is retrospective. A player's other matches can enter the opposite partition; this is not leave-player-out validation. Exact dates, strength of opposition and venue differences remain unadjusted within a season.", "",
        "Budget: this audit spends zero fits. Historical total remains 18. The documented candidate reserves two development and two reserved bundles (four targets each), with an explicit maximum of 22 instead of 20. There is one setting, one partition salt and no full-data refit. Exact leave-one-match-out fitting is rejected: it would require 402 development reference fits per target rather than two.", "",
        "Next: implement the frozen reference, test complete-match and partition isolation, and run development validation. The original failed forecast gates stay failed. 2026 outcome access and final rankings remain blocked at this milestone.", ""]
    (out / "REPORT.md").write_text("\n".join(report))
    save_json(out / "manifest.json", dict(config_sha256=sha256(config_path),
        preflight_manifest_sha256=sha256(root / "reports/supported_method_2026-11-01/manifest.json"),
        code_sha256=sha256(root / "src/rr_pressure/reference_audit.py"),
        outcome_files_opened=[], models_fitted=False, player_scores_created=False,
        matches=data.match_id.nunique(), events=len(data),
        output_sha256={p.name: sha256(p) for p in sorted(out.iterdir()) if p.name != "manifest.json"}))
    print(json.dumps(gate, indent=2))
    print(f"Report: {out / 'REPORT.md'}")
