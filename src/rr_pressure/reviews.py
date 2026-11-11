"""Explicit, private, versioned exceptions; never repair a new mismatch implicitly."""

from copy import deepcopy
import json

from .external import normalize


def load_reviews(root, aliases):
    path = root / "data/curated/reconciliation_reviews.json"
    review = json.loads(path.read_text()) if path.exists() else {"aliases": [], "events": []}
    enriched = {key: set(values) for key, values in aliases.items()}
    for entry in review["aliases"]:
        if not entry.get("evidence_urls") or not entry.get("rationale"):
            raise ValueError("Alias requires independent identity evidence and rationale")
        if entry["public_person_id"] not in enriched:
            raise ValueError("Reviewed alias has no registered public identity")
        enriched[entry["public_person_id"]].add(normalize(entry["supplied_name"]))
    return review, enriched


def apply_reviews(raw, member_sha256, entries):
    patched = deepcopy(raw)
    by_id = {row["event_id"]: row for row in patched}
    applied, retirements = [], set()
    seen = set()
    for entry in entries:
        if entry["event_id"] not in by_id:
            continue
        if entry["source_member_sha256"] != member_sha256:
            raise ValueError("Reviewed event source has changed; re-review required")
        if not entry.get("rationale"):
            raise ValueError("Missing review rationale")
        field = entry["field"]
        key = (entry["event_id"], field)
        if key in seen:
            raise ValueError("Duplicate review for event/field")
        seen.add(key)
        event = by_id[entry["event_id"]]
        if field == "retirement":
            if event["is_wicket"]:
                raise ValueError("Cannot suppress an actual wicket as retired hurt")
            retirements.add(entry["event_id"])
        else:
            if field not in {"recorded_runs", "extras_type"} or event[field] != entry["old_value"]:
                raise ValueError("Reviewed original value/field no longer matches")
            event[field] = entry["new_value"]
        applied.append(dict(entry))
    return patched, applied, retirements
