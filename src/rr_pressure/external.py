"""Frozen diagnostic sample and locally cached, attributed Cricsheet snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unicodedata
import urllib.request
from zipfile import ZipFile

import pandas as pd

from .data import fingerprints, save_json, sha256

CUTOFF = "2026-11-01"
ARCHIVES = {"IPL": "https://cricsheet.org/downloads/ipl_json.zip",
            "T20I": "https://cricsheet.org/downloads/t20s_male_json.zip"}
ATTRIBUTION = {"provider": "Cricsheet", "website": "https://cricsheet.org/",
               "license": "Open Data Commons Attribution License 1.0",
               "license_url": "https://opendatacommons.org/licenses/by/1-0/",
               "coverage_caveat": "Provider withholds Afghanistan matches; coverage is not random."}


def select_pilot(audit):
    """Two matches per year/family, chosen without inspecting external coverage.

    First: earliest ordinary decisive match failing both score hypotheses.
    Second: most distinct risk flags, then extras exposure, then stable hash.
    This is a diagnostic stress sample, never a population accuracy estimate.
    """
    audit = audit.copy()
    # CSV columns containing blanks are strings, not Boolean columns.
    for column in ["two_innings_present", "wicket_margin_pass"] + [
            f"{metric}_{h}" for metric in ("run_margin_pass", "chase_combined") for h in ("a", "b")]:
        audit[column] = audit[column].map({True: True, False: False, "True": True, "False": False, "": None})
    rows = []
    for year in range(2022, 2027):
        for family in ("IPL", "T20I"):
            pool = audit.loc[(audit.year == year) & (audit.family == family) &
                             audit.two_innings_present.eq(True) & (audit.date <= CUTOFF)].copy()
            if len(pool) < 2:
                raise ValueError(f"Insufficient sample for {year}/{family}")
            ordinary = pool.loc[pool.cohort.eq("ordinary") & pool.kind.isin(["runs", "wickets"])].copy()
            passed = pd.Series(False, index=ordinary.index)
            for h in ("a", "b"):
                passed |= ordinary[f"run_margin_pass_{h}"].eq(True) | ordinary[f"chase_combined_{h}"].eq(True)
            failing = ordinary.loc[~passed].sort_values(["date", "match_id"])
            if failing.empty:
                raise ValueError("No failing ordinary match: review sample design explicitly")
            first = failing.iloc[0].copy()
            first["selection_reason"] = "earliest_ordinary_failure_under_both_hypotheses"
            rows.append(first)
            pool = pool.loc[pool.match_id != first.match_id].copy()
            pool["risk_flags"] = (pool.cohort.ne("ordinary").astype(int) +
                (pool.innings1_unknown_extra_events + pool.innings2_unknown_extra_events).gt(0).astype(int) +
                (pool.kind.eq("wickets") & pool.wicket_margin_pass.eq(False)).astype(int))
            pool["extras_exposure"] = pool.innings1_unit_extra_events + pool.innings2_unit_extra_events
            pool["stable_tie"] = pool.match_id.map(lambda x: hashlib.sha256(f"1729:{x}".encode()).hexdigest())
            second = pool.sort_values(["risk_flags", "extras_exposure", "stable_tie"], ascending=[False, False, True]).iloc[0].copy()
            second["selection_reason"] = "maximum_risk_flags_then_extras_exposure"
            rows.append(second)
    return pd.DataFrame(rows).reset_index(drop=True)


def freeze_pilot(root):
    audit = root / "artifacts/reconciliation_2026-11-01/matches.csv"
    out = root / "reports/reconciliation_pilot_2026-11-01"
    out.mkdir(parents=True, exist_ok=True)
    selection = select_pilot(pd.read_csv(audit, dtype={"match_id": str}, keep_default_na=False))
    path = out / "selection.csv"
    payload = selection.to_csv(index=False)
    manifest_path = out / "selection_manifest.json"
    source_hashes = fingerprints(root / "6af3166e7b922_data_pack")
    if path.exists():
        old = json.loads(manifest_path.read_text())
        if path.read_text() != payload or old["source_sha256"] != source_hashes or old["audit_sha256"] != sha256(audit):
            raise ValueError("Frozen sample/input changed; explicit new pilot version required")
    else:
        path.write_text(payload)
        save_json(manifest_path, {"frozen_at_utc": datetime.now(timezone.utc).isoformat(),
            "selection_sha256": sha256(path), "audit_sha256": sha256(audit), "source_sha256": source_hashes,
            "cutoff": CUTOFF, "design": "2 per year/family: earliest failure + risk/extras stress",
            "replacement_for_missing_coverage": False, "population_representative": False})
    print(selection[["match_id", "date", "family", "selection_reason"]].to_string(index=False))
    return selection


def fetch(root):
    """Cache once; no implicit refresh and no archive extraction to disk."""
    freeze_pilot(root)
    dest = root / "data/external/cricsheet"
    dest.mkdir(parents=True, exist_ok=True)
    for family, url in ARCHIVES.items():
        path = dest / Path(url).name
        receipt = path.with_suffix(".manifest.json")
        if path.exists():
            if not receipt.exists() or json.loads(receipt.read_text())["sha256"] != sha256(path):
                raise ValueError(f"Unverified cache: {path}")
            continue
        temporary = path.with_suffix(".part")
        request = urllib.request.Request(url, headers={"User-Agent": "RR-reconciliation-research/0.1"})
        print(f"Fetching {url}", flush=True)
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
        with ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError("Corrupt archive")
        temporary.rename(path)
        save_json(receipt, {**ATTRIBUTION, "family": family, "url": url, "sha256": sha256(path),
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "bytes": path.stat().st_size,
            "cutoff_policy": "Match dates <= 2026-11-01; snapshot acquired later, not an as-of publication archive."})


def normalize(value):
    return " ".join("".join(c.lower() if c.isalnum() else " " for c in
        unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)).split())


def team_key(value):
    normalized = normalize(value)
    return {"royal challengers bangalore": "royal challengers bengaluru",
            "kings xi punjab": "punjab kings"}.get(normalized, normalized)


def index_archives(root):
    records = []
    for family, url in ARCHIVES.items():
        path = root / "data/external/cricsheet" / Path(url).name
        receipt = json.loads(path.with_suffix(".manifest.json").read_text())
        if receipt["sha256"] != sha256(path):
            raise ValueError("Archive hash mismatch")
        with ZipFile(path) as archive:
            for member in sorted(archive.namelist()):
                if not member.endswith(".json"):
                    continue
                raw = archive.read(member)
                info = json.loads(raw)["info"]
                if (info.get("gender") != "male" or info.get("match_type") != "T20" or
                        max(info["dates"]) > CUTOFF or min(info["dates"]) < "2022-01-01"):
                    continue
                for date in info["dates"]:
                    records.append({"family": family, "date": date,
                        "teams_key": "|".join(sorted(map(team_key, info["teams"]))),
                        "archive": path.name, "member": member,
                        "member_sha256": hashlib.sha256(raw).hexdigest(),
                        "source_created": json.loads(raw)["meta"]["created"],
                        "source_revision": json.loads(raw)["meta"]["revision"]})
    return pd.DataFrame(records)
