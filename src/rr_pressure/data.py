"""Typed ingestion, cardinality checks and source provenance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

FILES = ("competitions", "matches", "teams", "competition_team_player_mapping", "playing_eleven", "ball_by_ball")
KEYS = {"competitions": ["comp_id"], "matches": ["match_id"], "teams": ["comp_id", "team_id"],
        "competition_team_player_mapping": ["comp_id", "team_id", "player_id"],
        "playing_eleven": ["match_id", "team_id", "player_id"],
        "ball_by_ball": ["match_id", "innings", "innings_ball_num"]}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprints(source):
    return {p.name: sha256(p) for p in sorted(source.iterdir()) if p.is_file()}


def unique(frame, keys, label):
    if frame.duplicated(keys).any():
        raise ValueError(f"{label}: duplicate keys {keys}")


def checked_merge(left, right, on, label):
    unique(right, on, label)
    result = left.merge(right, on=on, how="left", validate="many_to_one", indicator="_join")
    if len(result) != len(left) or result["_join"].ne("both").any():
        raise ValueError(f"{label}: missing parent or multiplied event rows")
    return result.drop(columns="_join")


def load(root, cutoff):
    source = root / "6af3166e7b922_data_pack"
    frames = {name: pd.read_csv(source / f"{name}.csv", dtype=str, keep_default_na=False) for name in FILES}
    inventory = []
    nulls = []
    duplicates = []
    for name, frame in frames.items():
        dup = frame.duplicated(KEYS[name], keep=False)
        inventory.append({"file": f"{name}.csv", "rows": len(frame), "columns": len(frame.columns),
                          "duplicate_key_surplus": int(frame.duplicated(KEYS[name]).sum()),
                          "duplicate_key_rows": int(dup.sum())})
        if name != "playing_eleven":
            unique(frame, KEYS[name], name)
        elif dup.any():
            duplicates = frame.loc[dup].to_dict("records")
        for column in frame:
            nulls.append({"file": name, "column": column, "blank_count": int(frame[column].eq("").sum()),
                          "literal_None_count": int(frame[column].eq("None").sum())})
    match = frames["matches"].copy()
    pd.to_datetime(match["match_date"], format="%Y-%m-%d", errors="raise")
    match = match.loc[match["match_date"] <= cutoff].copy()
    match = checked_merge(match, frames["competitions"], ["comp_id"], "match competition")
    match["family"] = "Other T20"
    match.loc[match["match_format"].eq("T20I"), "family"] = "T20I"
    match.loc[match["comp_name"].str.startswith("IPL "), "family"] = "IPL"
    match["year"] = match["match_date"].str[:4].astype("int16")
    events = frames["ball_by_ball"].copy()
    all_match_ids = set(frames["matches"]["match_id"])
    if not set(events["match_id"]).issubset(all_match_ids):
        raise ValueError("Delivery has no match parent")
    events = events.loc[events["match_id"].isin(match["match_id"])].copy()
    events["source_row"] = events.index + 2  # CSV line including header
    meta = ["match_id", "comp_id", "comp_name", "family", "match_date", "year", "venue_id", "venue_country", "stage"]
    events = checked_merge(events, match[meta], ["match_id"], "event match")
    for column in ["innings", "overid", "over_ball_num", "innings_ball_num", "batting_order", "runs"]:
        events[column] = pd.to_numeric(events[column], errors="raise").astype("int16")
    for column in ["is_wicket", "is_four", "is_six"]:
        if not events[column].isin(["true", "false"]).all():
            raise ValueError(f"Invalid Boolean in {column}")
        events[column] = events[column].eq("true")
    events = events.rename(columns={"runs": "recorded_runs"})
    if (events["recorded_runs"] < 0).any():
        raise ValueError("Negative recorded runs")
    events["event_id"] = (events["match_id"] + ":" + events["innings"].astype(str) + ":" +
                          events["innings_ball_num"].astype(str))
    unique(events, ["event_id"], "canonical events")
    # Create a player dimension without joining the many-row competition mapping to balls.
    names = frames["competition_team_player_mapping"][["player_id", "player_name"]].copy()
    for role in ("striker", "non_striker", "bowler"):
        names = pd.concat([names, events[[f"{role}_id", f"{role}_name"]].rename(
            columns={f"{role}_id": "player_id", f"{role}_name": "player_name"})], ignore_index=True)
    aliases = names.drop_duplicates().sort_values(["player_id", "player_name"])
    players = aliases.drop_duplicates("player_id", keep="first")
    unique(players, ["player_id"], "player dimension")
    audit = {"inventory": pd.DataFrame(inventory), "field_missingness": pd.DataFrame(nulls),
             "lineup_duplicate_rows": pd.DataFrame(duplicates), "player_aliases": aliases}
    return frames, match, events, players, audit


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, default=str) + "\n")
