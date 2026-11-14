# Player evidence dossiers: implementation plan

Status: updated 14 November 2026. Initial development evidence tables and descriptive uncertainty are implemented, executed and reconciled. The checkpoint recommendation is in [RATING_METHOD_DECISION.md](RATING_METHOD_DECISION.md); its substantive amendment is not activated. Full dossier rendering and rating execution remain pending. The active scoring specification has not changed.

## Purpose and immediate decision

The selector's question is: **which players repeatedly perform their cricket task under pressure, what evidence challenges that judgement, and how defensibly can we order them?** The deliverable remains two ranked top-ten lists and an evidence-backed methodology. Dossiers are the next step toward those decisions.

Stop automatic model experimentation now. Keep the saved models as diagnostic evidence, preserve their failed promotion gates, and spend no further fit bundles on this work. Twenty bundles have been used; the two reserved bundles are not spare search capacity. No new partition search, error correction from evaluation outcomes, pressure-threshold tuning, explorer or auction simulator is included.

The review found 68 separate-fold alerts across 38 target/context combinations. All 38 have opposing fold-bias signs; 46 alerts remain above the point tolerance after removing any single evaluation match. Contexts flagged in either fold contain 45.52% of development batting pressure opportunities and 45.52% of bowling pressure attempts. These findings justify withholding model-adjusted player ratings; they do not establish that the observed player outcomes are wrong.

Build observed development evidence while preparing one explicit rating-method decision. Do not wait for another model to build the dossiers. Do not turn descriptive rates into an approved composite score by changing their label.

## Scope and boundaries

- Development dossiers use verified **2023–2025** events only, referenced to 31 December 2025. The final cutoff remains **1 November 2026 inclusive**; 2022 contributes no player-selection evidence.
- Reuse frozen pressure flags, opportunity definitions, source exclusions, support rules and the 730-day recency half-life. Display ordinary and pressure denominators separately.
- Keep 1,000 whole-match bootstrap draws, stratified by competition family/year and shared across players and roles. Do not resample deliveries independently.
- [SUPPORTED_METHOD.md](SUPPORTED_METHOD.md) and [its configuration](configs/supported_method_v1.json) remain the active rating method. Their 70/30 level/change default and 50/50 variant are unchanged unless explicitly amended. No approved expectation reference currently exists.
- Dossier rates and intervals are descriptive. They are not contextual residuals, a causal pressure effect, forecasts of IPL 2027 performance, or selection scores. Failed-reference exposure is an uncertainty annotation, not a performance deduction.
- Keep detailed player outputs private under `reports/`. Commit code, tests, specifications and aggregate progress at coherent milestones.

## Work packages and acceptance criteria

| Package | Cricket decision supported | Concrete output | Done when |
| --- | --- | --- | --- |
| D0. Freeze the dossier contract | Ensure the same evidence is collected for every player. | Versioned `configs/player_evidence_v1.json`; input manifest; date/role/metric contracts; stable dossier schema. | Definitions and case-selection rules are fixed before inspecting named performance tables; reserved-outcome access is blocked. |
| D1. Build the evidence ledger | Establish what each player actually did and in which situations. | Event-to-player ledger, match summaries, role/context profiles, coverage and eligibility register. | Counts reconcile with the existing development preflight; every reported outcome traces to a verified event and match. |
| D2. Measure repeatability and comparisons | Separate repeated performance from one exceptional match and reveal whether usual-performance comparisons exist. | Season tables, shared match-bootstrap intervals, leave-one-match-out ranges, supported pressure/ordinary tables. | Unsupported comparisons stay missing; uncertainty, sample size and sensitivity are shown together. |
| D3. Produce dossiers and challenge the evidence | Make positive evidence, weaknesses and credible counterexamples inspectable. | One dossier per level-sample-eligible player/role, full match appendix, comparison-availability register and selector review ledger. | Every dossier contains role, observed performance, repeatability, limitations and source-linked cases; all eligible players are accounted for. |
| D4. Resolve and freeze the rating method | Decide how evidence becomes an ordering, including specialists without ordinary controls. | `RATING_METHOD_DECISION.md` plus a versioned executable specification if amended. | Exact formula/order, cohort, missingness, uncertainty, sensitivity and final evaluation gates are explicit; no silent promotion or method replacement. |
| D5. Apply the frozen decision to the final window | Check whether the conclusions survive the reserved period and current evidence. | Separate 2026 diagnostics and refreshed 2023–1 November 2026 dossiers, followed by permitted ratings. | D4 is resolved before reserved outcomes are read; any failed check is reported without automatic retuning. |
| D6. Select and package | Defend the two ordered lists against credible alternatives. | Ten batting selections, ten bowling selections, alternative/counterexample review, methodology and dropdown mapping. | Ordering and report agree; each selection has evidence and limitations; exact submission names are checked. |

D0–D1 and the initial analytical tables are the immediate implementation scope. **User-confirmed sequence: validate those tables, then complete D4 before rendering or polishing the full D2–D3 dossier pack.** Initial observed uncertainty/comparison tables may support the decision; full cards and narrative review follow it. D5–D6 depend on the accepted method decision; they are not authorized by a dossier being generated successfully.

## D0–D1: inputs, access and cohort

Use the existing artifacts rather than building a second ingestion or reconciliation pipeline:

1. `reports/supported_method_2026-11-01/`: development player/peer-cell files, identities/exposures, features, targets and existing configuration/provenance.
2. `reports/full_reconciliation_2026-11-01/verified_events.parquet`: verified score components, pressure reasons, pre-ball states and names, projected to the required columns and development dates only.
3. `reports/reference_instability_review_2026-11-01/player_exposure_only.csv`: exposure to unstable reference contexts, used only as a limitation annotation.
4. Supplied match metadata: team, opposition, competition and venue labels for evidence traceability. Validate team attribution against innings team IDs; do not invent opposition-strength adjustments.

Start from development event IDs. Apply Parquet predicates before materializing mixed-year outcome data; if a target table lacks dates, filter by the allowlisted development event IDs. Assert the returned year range and join cardinality. Hash the relevant input files and record the exact event/column selection. File hashing is provenance, not permission to load reserved outcomes.

Join on stable IDs, never player names. A player can have independent batting and bowling dossiers. Surface name collisions or aliases; do not guess identity merges. Reuse preflight cells and eligibility rather than recalculating them with a new definition.

The development reconciliation targets are **402 matches, 95,945 delivery events, 92,259 batting opportunities, 32,329 batting pressure opportunities and 33,920 bowling pressure attempts**. Treat these as assertions for this frozen artifact version, not universal constants.

Generate full dossiers for all **73 batting and 122 bowling player-role entries** that pass the existing development level sample checks. Of these, 62 batting and 90 bowling entries also pass the 80% source-retention check. Keep the others visible with coverage restrictions. These are development evidence cohorts, not final shortlists or necessarily 195 distinct people.

Create a separate register for every other observed player/role showing exposure and exact sample/coverage failure reasons. Missing or excluded source evidence must remain visible. Do not remove a credible specialist because supported ordinary comparisons are absent, or promote a low-sample player to meet a list size. The current development blended-plus-coverage cohort is only six batters and twelve bowlers; this is an explicit method-decision issue.

## D1–D3: exact dossier content

Each dossier has a concise front page and machine-readable appendices. No performance ranking or composite score appears in this development export; its index is ordered by player name and stable ID.

### 1. Role evidence and exposure

Show opportunities and distinct matches by family, season, innings and the existing phases (1–6, 7–15, 16–20), plus pre-ball wicket bands. Display exposure shares so a reader can distinguish an occasional finishing appearance from a sustained late-over workload.

Use context labels, not invented tactical assignments:

| Evidence label | Observable definition |
| --- | --- |
| Powerplay batting/bowling | Existing phase 1–6. |
| Middle-over batting/control | Existing phase 7–15. |
| Late-over batting/bowling | Existing phase 16–20. |
| Batting during a collapse | Frozen pre-ball `collapse` flag. It is evidence of the situation, not proof the player was assigned to rebuild. |
| Tight-chase batting/defence | Second innings and frozen pre-ball `tight_chase` flag, attributed to striker/bowler respectively. |
| Late-chase batting/defence | Second innings and late phase. Do not describe every late chase as tight. |

Retain multi-role profiles; no forced single-role classification or squad quota. Pressure-reason views overlap, so show overlap counts and never sum them as distinct opportunities. A context label documents exposure, not success. Batting order, pace/spin or handedness can be additional descriptive fields only after completeness and attribution checks; they are not necessary to finish this milestone.

### 2. Observed pressure performance

Report integer totals, opportunities, matches and rates together, both unweighted and with the fixed recency weights. A zero denominator is unavailable, not zero performance.

| Role | Primary outcomes | Companion evidence and interpretation |
| --- | --- | --- |
| Batting | Batter runs per 100 non-wide striker opportunities; bowler-attributable striker dismissals per 100 of those opportunities. | Runs, attributed dismissals, boundaries and zero-batter-run opportunities; interpret scoring tempo alongside dismissal risk. No-balls remain in the analytical opportunity denominator. |
| Bowling | Batter runs + wides + no-balls conceded per 100 delivery attempts; bowler-credited wickets per 100 attempts. | Concessions, wickets, wide/no-ball runs and zero-concession attempts; interpret control alongside wicket-taking. Byes, leg-byes and penalties are excluded from concession. |

Do not call these official strike rate, batting average or economy. Derive boundaries from verified batter runs and cross-check supplied four/six flags; label any unresolved discrepancy. Keep run-outs, retirements and other excluded dismissals in a separate event annotation so the main wicket definition is not mistaken for all dismissals. Show runs and wickets separately; do not apply the registered 60/40 contribution mix to raw quantities with incompatible units.

Break out pressure performance by family, season, innings and role context. Use opponent/venue labels to describe where evidence occurred. Do not infer opponent difficulty, pitch quality, injury, availability or future franchise role from those labels.

### 3. Usual performance and comparison limits

Show three different views with explicit labels:

1. All observed pressure outcomes: covers the player's pressure workload, including late overs.
2. All observed ordinary outcomes: background description only; these can come from very different situations.
3. Supported same-player comparisons: use the frozen family × year × innings × phase × wicket-band cells and existing peer/player support minima. For each primary metric, report pressure and ordinary rates standardized to the player's supported pressure-cell weights, plus their difference.

For the third view, use `q_cell` from the existing recency-weighted supported pressure exposures. The descriptive difference is `sum(q_cell * (pressure_rate_cell - ordinary_rate_cell))`. Display its sign literally: more batting dismissals or bowling concessions is adverse. It is an observed supported difference, **not** the model-residual change term in the active rating method and not a causal effect.

Report supported pressure counts, matches and share of all pressure evidence on the same page. Apply existing change sample requirements before treating a player-level supported difference as established evidence; otherwise retain cell tables as small-sample diagnostics and withhold the headline comparison. Late-over ordinary comparisons remain unavailable. Never fill missing change with zero or substitute a different season.

### 4. Repeatability and uncertainty

- Show every available season and match, including poor performances. Report where evidence is concentrated by family, season and match; a missing season is not a zero.
- Use the frozen 730-day recency weights for the primary descriptive rates; show unweighted rates beside them. Do not search for a recency setting that improves particular players.
- Generate 1,000 shared complete-match draws with seed 1729, stratified by family/year. Report 10th–90th percentile intervals for the primary pressure rates and supported differences, with finite-draw fractions. Intervals describe match sampling conditional on the retained data; they do not cover missing matches or unmeasured contextual differences.
- Keep original support and eligibility fixed. If a draw loses either group in any originally supported player cell, that supported difference is unavailable in that draw. If a player's pressure denominator disappears, their pressure rate is unavailable. Below 95% finite draws, mark the interval unreliable and do not use it for a selection claim.
- Compute leave-one-match-out minimum/maximum rates for every primary metric, with the influential match IDs. This captures dependence on either an exceptional or a poor match without selecting an arbitrary composite "best match".
- Show leave-one-season-out estimates at the same reference date and fixed half-life. For these explicitly different time populations, use only original supported cells from the retained years and recompute their pressure-exposure weights; do not discover new support. Re-evaluate sample adequacy, publish remaining exposure and label unavailable comparisons.
- Do not reduce consistency to a count of matches above a player's own mean, or treat narrow intervals as proof of superior cricket ability. No additional model fits are needed for these checks.

### 5. Supporting cases, weaknesses and counterexamples

Publish the complete pressure match ledger first, so every case is auditable. Freeze the following display protocol in D0 before named performance inspection:

- For a headline case, require at least ten batting pressure opportunities or six bowling pressure attempts in that match. These are proposed case-display minima only; they do not alter pressure, eligibility or scoring thresholds. Include all smaller samples in the appendix.
- Nominate highest and lowest pressure run-rate matches and highest and lowest pressure wicket/dismissal-rate matches independently. Also nominate a typical run-rate match nearest the exposure-weighted median match rate. Break ties by greater pressure exposure, then date, then match ID; deduplicate matches. Display all nominated cases, at most five.
- If no match meets the display minimum, show the highest-exposure match as an explicitly small-sample illustration. Do not call it a representative performance.
- Each case contains date, competition, opposition, innings/phase, the relevant pre-ball states, pressure reasons, opportunities and both primary outcomes. An attractive run rate with adverse dismissal evidence must show both facts. Match result, if independently checked, is narrative context only, not individual credit.
- Add a short factual weakness/counterexample statement and its supporting ledger rows. A sparse context means "not established", not "weak in that context". If the available evidence contains no supported weakness claim, say so and state the limitation rather than inventing one.

For an eventual selection, review the full ledger and at least one adverse case as well as supporting cases. The automatic examples are extrema/typical observations, not a definition of match-winning performance.

### 6. Selector assessment and alternatives

Use a fixed assessment template: observed task; positive evidence; tempo/wicket tradeoff; repeatability; adverse evidence; coverage/comparison limits; questions still unresolved. Every factual assertion links to an aggregate row or match/event ID.

Review comparable workloads together using exposure profiles, not reputation. The comparison table places both primary outcomes and uncertainty beside each other; it does not quietly sort by one outcome. Record why an apparent advantage may be context mix or insufficient exposure. Keep all level-eligible entries in the review ledger, including coverage-limited and level-only specialists; do not create an undisclosed nomination cutoff.

Once D4 permits a provisional ordering, review at least three plausible alternatives per list and explicitly defend the tenth selection against the nearest exclusions. A player may appear in both lists if their evidence supports both. There are no nationality, squad-balance, price or availability quotas.

## D4: bounded rating-method decision

Complete this decision immediately after the first validated aggregate tables, **before rendering or polishing the full dossier pack**, final ordering or reserved outcome access. The user confirmed this checkpoint on 14 November 2026. It is not another open-ended model workstream.

Prepare one decision note comparing these two paths against the actual evidence:

1. **Retain the active residual-based method.** The 70/30 default, 50/50 variant and current eligibility continue to apply. The failed reference gate blocks execution; dossier completion cannot remove that block. Document the unresolved reference and specialist-exclusion issues without requesting another automatic experiment.
2. **Explicitly amend to a transparent descriptive selection method.** Recommended for consideration because it can use the verified outcomes directly. A possible structure is a common pressure-performance ordering, with supported usual-performance differences reported separately so specialists remain visible. This would change the registered blend and must be an explicit user-approved amendment, not an implementation shortcut. Raw rates alone do not solve cross-context comparability; the proposed specification must explain how role/family/year mix and unequal coverage affect ordering and what remains unadjusted.

This plan does not select a replacement formula or approve dropping the 70/30 and 50/50 variants. Until an amendment is accepted, both remain registered and final scoring remains blocked. The decision note must give a concrete recommended formula or ordering rule, rather than offer "selector judgement" as an unspecified algorithm.

Before D5, record all of the following in the accepted version:

- What is being estimated and why it answers the Round 1 pressure/usual-performance question.
- Exact metric orientation, scale/normalization, weighting and tie-breaks; any departure from the 60/40 outcome mix or registered level/change variants.
- Which cohort can enter a common list; treatment of level-only specialists, unsupported change, low retention and sparse evidence.
- How context comparability is handled without reusing failed expectations as validated player adjustments.
- Match-bootstrap use, finite-draw requirements, repeatability checks and whether the lower quantile remains the ordering rule.
- The fixed development-to-final transfer procedure, reference date and treatment of 2026 outcomes; exact development-only scaling if needed.
- Predeclared sensitivity and failure checks, including coverage, valid comparison availability, run/wicket tradeoffs and whether results depend on one match or season.
- Disposition of every previously frozen rule, with reasons. Preserve all failed gates and do not describe the amendment as model validation.

Allow one prepared recommendation and one decision checkpoint, not an automatic search over formulas for favourable rankings. An amendment informed by these dossiers is a development-informed decision, not a method registered before development outcomes were seen. Justify it through the cricket question, comparability and evidence coverage, never preferred names; freeze it before reserved evaluation. If a defensible ordering is still unresolved, deliver the completed evidence pack and the precise outstanding decision; do not manufacture a top ten or reopen modeling by default.

## D5–D6: reserved evaluation and final selection

After D4 is resolved, apply the accepted specification unchanged to the final verified window and refresh eligibility at the final reference date. Evaluate 2026 separately under its frozen check plan before making final selection claims. Its prior aggregate EDA exposure must remain disclosed; it is not pristine unseen data.

If the accepted method uses no expectations, no reserved model fits are needed. If it retains expectations, its reference-validation requirements must actually be satisfied before reserved fitting. Dossier code cannot bypass either condition.

Produce the two provisional ordered lists, review boundary candidates and counterexamples, then finalize twenty selection entries with concise justifications. Report identical-cohort sensitivities where the accepted specification requires them; never compare different eligibility cohorts as a weight effect. Record disagreements between point ordering, uncertainty and sensitivity rather than selecting the most attractive variant.

The final methodology must explain pressure (including its roughly 35% event share), usual-performance comparisons, exclusions, roles, ratings, repeatability and limitations. Refresh exact platform/dropdown requirements at packaging time. Exported lists, methodology and dropdown mapping must agree one-for-one. No submission or organizer message is sent as part of this plan.

## Implementation layout and validation

Implemented code: `src/rr_pressure/player_evidence.py` for development-only loading, aggregates and initial descriptive uncertainty; `tests/test_player_evidence.py` for the analytical and access contracts; `build-player-evidence` CLI with development as its only permitted window. The full card renderer `player_evidence_report.py` remains proposed and unimplemented. Reuse existing support, weights, targets and bootstrap utilities where their contracts match; do not refactor unrelated modules.

Proposed private output directory: `reports/player_evidence_development_2026-11-01/` (the directory names the project cutoff; the manifest and every card state that the evidence window is 2023–2025):

```text
manifest.json                  # hashes, dates, contracts, no-fit/no-reserved-access assertions
cohort_register.csv            # every player/role, eligibility and exclusion reasons
player_context_summary.parquet # outcomes, denominators, exposure and support by context
player_match_ledger.parquet    # complete match evidence, including small samples
player_season_summary.csv
supported_comparisons.parquet
uncertainty_and_influence.parquet
case_index.csv                 # deterministic case IDs and nomination reasons
selector_review.csv            # assessment status, evidence references, open questions
dossiers/batting/<player_id>.md
dossiers/bowling/<player_id>.md
REPORT.md                      # aggregate completion, caveats and method-decision status
```

Meaningful checks required before interpreting the dossiers:

1. Development-only file reads, unique event/role joins and no lost/duplicated events; reconcile all frozen cohort and denominator totals.
2. Hand-calculated edge cases: wides, no-balls, byes/leg-byes, run-outs/non-striker dismissals, retirements and zero denominators. No official-rate mislabelling.
3. Pre-ball role contexts and overlapping pressure reasons; no result or later-ball information used to assign a situation.
4. Supported-cell weighting and missingness; preserve absent ordinary death controls and change eligibility.
5. Shared whole-match resampling and fixed support, finite-draw handling, season exclusions and influence calculations. Confirm deterministic results under the fixed seed.
6. Case-selection ties, small-sample fallback, traceable adverse cases, name/ID integrity and coverage annotations.
7. A stratified manual audit across both roles, both families and all phases, including sparse, coverage-limited and level-only cases. Verify printed numbers back to event rows.
8. Assert no model fit, candidate-scale promotion, player composite score or reserved performance output occurred. Existing promotion-gate hashes remain unchanged.

Use a small anonymous fixture first, then one complete development execution and a focused artifact review. Correct demonstrated bugs; do not repeatedly run experiments to make the findings look stronger. Existing tests prove software contracts, not the cricket validity of a future ranking.

## Milestones and next handoff

1. **Completed initial evidence milestone:** D0–D1 contract, safe loader, reconciled development ledger and initial uncertainty/comparison tables. Contract commit: `1dfb4e7`.
2. **Current decision milestone after validated tables:** D4 concrete recommendation is written; accept/reject its explicit amendment before rating execution or full dossier rendering/polishing.
3. **Following evidence milestone:** D2–D3 complete dossier pack, uncertainty, cases and selector review ledger, then D5 final-window evidence and checks. Publish aggregate findings in progress; detailed outputs remain private.
4. **Final milestone:** D6 two defensible ordered lists and the matching methodology, ready for the user's submission review.

The next task is resolving the explicit amendment in [RATING_METHOD_DECISION.md](RATING_METHOD_DECISION.md), followed by its fixed development implementation if accepted. Do not start the full dossier renderer, another predictive experiment or reserved evaluation while that decision remains pending. The project is complete only when both Round 1 deliverables are ready.
