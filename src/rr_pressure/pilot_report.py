"""Private diagnostic report, coverage denominators and pressure decomposition."""

import pandas as pd


def markdown_table(frame):
    frame = frame.fillna("")
    return "\n".join(["| " + " | ".join(map(str, frame.columns)) + " |",
                      "| " + " | ".join(["---"] * len(frame.columns)) + " |"] +
                     ["| " + " | ".join(str(v).replace("|", "; ") for v in row) + " |" for row in frame.itertuples(index=False, name=None)])


def make_pilot_report(frames, out):
    matches = frames["matches"]
    states = frames["verified_preball_states"]
    corrections = frames["verified_corrections"]
    failures = frames["alignment_failures"]
    crosswalk = frames["player_crosswalk"]
    pressure_rows = []
    if len(states):
        data = states.merge(matches[["match_id", "year", "family"]], on="match_id", validate="many_to_one").merge(
            corrections[["event_id", "legal_delivery_verified"]], on="event_id", validate="one_to_one")
        for denominator in ("delivery_events", "legal_balls"):
            population = data if denominator == "delivery_events" else data.loc[data.legal_delivery_verified]
            for keys, group in [(('all', 'all'), population), *list(population.groupby(["year", "family"]))]:
                pressure_rows.append({"year": keys[0], "family": keys[1], "denominator": denominator,
                    "matches": group.match_id.nunique(), "balls": len(group),
                    **{f"{k}_percent": round(100 * group[k].mean(), 3) for k in ("late", "collapse", "tight_chase", "pressure_proxy", "pressure_full")}})
    pressure = pd.DataFrame(pressure_rows)
    pressure.to_csv(out / "pressure_coverage.csv", index=False)
    extras_rows = []
    if len(corrections):
        for field in ("wides", "noballs", "byes", "legbyes", "penalty"):
            values = corrections[f"extras_{field}"]
            extras_rows.append({"extra": field, "events": int(values.gt(0).sum()), "runs": int(values.sum()),
                               "multi_run_events": int(values.gt(1).sum()), "maximum": int(values.max())})
    extras = pd.DataFrame(extras_rows)
    extras.to_csv(out / "verified_extras.csv", index=False)
    accepted = matches.loc[matches.accepted]
    failures_by_reason = failures.groupby("reason").agg(events=("event_id", "size"), matches=("match_id", "nunique")).reset_index() if len(failures) else pd.DataFrame()
    unresolved = crosswalk.loc[~crosswalk.identity_resolved].drop_duplicates(["match_id", "player_id"])
    unresolved.to_csv(out / "unresolved_identities.csv", index=False)
    extra_category = corrections.groupby("recorded_extras_category", as_index=False).agg(
        events=("event_id", "size"), verified_extras=("extras_runs", "sum"),
        verified_noballs=("extras_noballs", "sum")) if len(corrections) else pd.DataFrame()
    extra_category.to_csv(out / "category_evidence.csv", index=False)
    lines = ["# External scoring reconciliation: frozen 20-match pilot", "",
        f"Exact date/team candidates: **{int(matches.matched.sum())}/20**. Complete event alignment: **{int(matches.alignment_pass.sum())}/20**. "
        f"Accepted ordinary matches after alignment and outcome checks: **{len(accepted)}/20**, covering **{len(corrections):,} deliveries**.", "",
        "This is a diagnostic stress sample, not an estimate of population accuracy. Two matches were frozen per year (2022–2026) and family (IPL/T20I), before external coverage inspection: the earliest ordinary failure under both scoring hypotheses, then the strongest risk/extras case. Unmatched and rejected matches were not replaced.", "",
        "## Acceptance and reconciliation", "",
        "Accepted matches require a unique exact date/team candidate, identical event count and order, all three actors, batting teams, batter runs, known extra labels, dismissal flags/kinds/persons, legal-over structure, complete first innings and correct result. Run victories require the exact margin; wicket victories require the target to be crossed only on the final delivery and the correct wickets remaining. Every candidate score comes from a specific JSON pointer and hashed snapshot. Unknown extra labels receive quantities only from an otherwise exact aligned event.", "",
        "Rows in candidate_corrections.csv are diagnostic proposals. Only verified_corrections.parquet and verified_preball_states.parquet contain accepted complete matches. Existing production EDA files remain unchanged; global Mode A is still gated.", "",
        markdown_table(frames["summary_by_year_family"][["year", "family", "selected", "matched", "aligned", "score_pass", "accepted"]]), "",
        "Each denominator above is the two preselected matches in that cell. `score_pass` validates the external ledger against supplied match metadata independently of event alignment; it is not sufficient for acceptance.", "",
        markdown_table(matches[["match_id", "date", "family", "status", "alignment_pass", "score_pass", "score_reason"]]), "",
        "## Verified extra quantities", "", markdown_table(extras), "",
        "Multi-run extras in accepted event ledgers are direct evidence against a universal one-run assumption. Recorded batting runs match the external batting-run field in accepted matches; this does not establish field semantics across every quarantined match. `extras1_runs` remains a category code, and `extras_2_runs` is retained unchanged for review.", "",
        markdown_table(extra_category), "",
        "## Pressure coverage without threshold changes", "", markdown_table(pressure), "",
        "Coverage is computed only on fully accepted matches, so it cannot substitute for corpus-wide coverage. The late clause labels every delivery in overs 16–20; collapse and tight chases expand that union. Individual component percentages overlap and must not be added. If full coverage exceeds the registered 20–30% band, this is reported as a definition/support issue, not a reason to adjust thresholds to favour players. Every late-over observation has pressure=True, leaving no ordinary comparison within that phase.", "",
        "The earlier corpus diagnostic had 31.67% late-or-collapse pressure even before adding tight chases; full pressure under unverified score hypotheses was about 35.5–35.8%. Those totals remain provisional until broader score repair. See the original reconciliation and EDA reports for all-year/competition denominators.", "",
        "## Quarantine and next gate", "", markdown_table(failures_by_reason), "",
        f"Unresolved identity instances: {len(unresolved)}. Detailed names and proposed candidates are in unresolved_identities.csv. Identity candidates use exact register aliases first, then unique team-scoped name variants, and must agree on every event. Ambiguity is never resolved by player performance or score fit.", "",
        "1. Review unresolved aliases with independent identity evidence; preserve an explicit crosswalk and source for each approved mapping.",
        "2. Review batting-run swaps, bye/leg-bye disagreements and retirements separately. The pilot does not silently rewrite those fields to force alignment.",
        "3. Keep rain-adjusted/shortened matches quarantined until target and allotted-ball timing can be reconstructed. An end-of-innings target alone does not establish its availability at every earlier ball.",
        "4. Apply the strict accepted path to the wider supplied corpus only after pilot review, reporting loss by year, competition and player. Missing Afghanistan coverage is systematic, so a Cricsheet-only cohort needs a coverage/sensitivity decision.",
        "5. Validate pressure support and phase overlap, then fit chronological context baselines. Preserve whole-match bootstrap, 70/30 and 50/50 weights, about 20 refit variants, and the deferred explorer.", "",
        "## Provenance and evaluation discipline", "",
        "Raw competition inputs were hash-checked and not edited. The cutoff remains 1 November 2026 inclusive. External archives may contain later matches, but only dates from 2022 through the cutoff enter the index. These are snapshots downloaded after the cutoff, not proof of what was publicly available on that date; source revisions are recorded. The initial selection serialization bug was corrected before external matching; superseded local selection files are preserved with an invalid_boolean_parse suffix.", "",
        "Aggregate 2026 EDA and reconciliation diagnostics have been inspected. Reserve 2026 from model/threshold tuning, but describe it as a reserved model-evaluation period, not a pristine unseen dataset. Final all-data rankings remain distinct from forecasting evaluation.", "",
        "External source: [Cricsheet](https://cricsheet.org/), [JSON specification](https://cricsheet.org/format/json/), [People Register](https://cricsheet.org/register/), [coverage and withheld matches](https://cricsheet.org/downloads/). Data is under the [Open Data Commons Attribution License 1.0](https://opendatacommons.org/licenses/by/1-0/). The derived correction layer adds alignment decisions and provenance to those source quantities.", "",
        "The organiser clarification remains drafted and unsent. No player rankings or predictive ML model have been created.", ""]
    if len(pressure):
        pct = pressure.loc[pressure.year.eq("all") & pressure.denominator.eq("delivery_events"), "pressure_full_percent"].iloc[0]
        lines.insert(4, f"Verified pilot full-pressure share: **{pct:.2f}%**, {'outside' if not 20 <= pct <= 30 else 'inside'} the 20–30% diagnostic band. This small selected cohort is not representative.\n")
    (out / "REPORT.md").write_text("\n".join(lines))
