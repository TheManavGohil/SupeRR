# Project progress and agent handoff

Last updated: 12 November 2026 (IST).
Current stage: data and method preparation complete for the accepted cohort; development baseline fitting is next.

## Read this first

This is the current status and handoff record. Read it before continuing implementation and update it after each meaningful milestone. The detailed architecture is in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md); the active scoring specification is [SUPPORTED_METHOD.md](SUPPORTED_METHOD.md) and [its frozen configuration](configs/supported_method_v1.json). That amendment supersedes the original global pressure-change model. Current user instructions take precedence over these documents.

## Final goal and definition of done

The downloaded Round 1 brief asks for a system that compares batting and bowling under pressure with players' usual performance and identifies consistent performers. The required submission has **two components**:

1. Two ordered top-ten lists, one for batters and one for bowlers, with unique players within each list and exact Unstop dropdown selections.
2. A methodology document explaining pressure, ratings, fair comparisons, evidence for the selections, consistency and limitations. Its rankings must match the dropdown selections.

The reproducible pipeline supports those deliverables; it is not a separate required submission component. A website, auction simulator, advanced ML model and explorer are not on the critical path. Qualification is not established by implementation progress.

**Present status:** no predictive model fitted, no player scores or rankings produced, no final methodology document completed, no submission made. The project has a verified analytical foundation, not a submission-ready result.

## Completed work and why it matters

| Work | Achieved | Contribution to the final goal |
| --- | --- | --- |
| Brief and architecture | Requirements mapped; reproducible local pipeline and frozen constraints established. | Keeps the work tied to the two required deliverables. |
| Scoring audit | Tested recorded runs and one-run-per-extra hypotheses; neither was reliable enough for score reconstruction. | Prevents incorrect chase states and pressure labels. |
| EDA and state preparation | Typed ingestion, data quality checks, pre-delivery context, coverage tables and chart pack. | Explains the supplied population and builds the rating inputs. |
| External reconciliation and exception review | All 883 supplied matches accounted for; 651 complete matches and 155,799 deliveries verified. Raw files preserved; unresolved cases remain excluded. | Establishes trustworthy match states and traceable repairs. |
| Coverage assessment | Verified delivery retention: IPL 92.50%, T20I 70.24%; player coverage reported separately. | Makes selection bias and missing evidence visible. |
| Pressure validation | Full rule flags 35.12% of verified delivery events, above the diagnostic 20–30% target. Late-over labels plus collapse/chase conditions explain the excess. | Shows what the pressure definition captures without tuning it for players. |
| Comparison check | Every late-over event is pressure; ordinary controls are absent there. Only 35.35% of development pressure events pass the earlier population context-support check. | Blocks an unsupported global pressure-minus-ordinary interpretation. |
| Supported method freeze | Separate all-pressure performance level from change within supported same-player/year contexts. Preserve unavailable change as missing. | Defines what we can honestly estimate for each player. |
| Model preflight | Separate features, targets and identities; complete-match chronological folds and outcome-independent eligibility tables exported. | Makes the first baseline ready to implement without future-outcome leakage. |

Latest implementation verification: **66 tests passed** at the supported-method milestone. This documentation update does not represent a new test run.

## Main limitations and alignment risks

- **Final recommendations are still missing.** The next substantial work must produce and assess baseline expectations and player evidence, rather than expand the infrastructure.
- **Coverage is uneven.** T20I retention is materially below IPL retention. Missing-source and quarantined players cannot be interpreted as weak performers. Resolve remaining cases selectively when they materially affect plausible recommendations; do not restart exhaustive repair by default.
- **Comparison eligibility is restrictive.** In the final 2023–2026 scoring window, 93 batters / 150 bowlers pass level sample checks; only 11 / 16 also pass supported-change and 80% source-retention requirements. Development counts for those combined checks are 6 / 12. These are evidence counts, not a shortlist or performance result.
- **Ranking only the blended cohort may exclude strong specialists.** A late-over specialist can have substantial pressure performance evidence but little ordinary comparison evidence. Evaluate this selection limitation explicitly before claiming the ten best players overall. Keep level evidence visible for the wider population. Do not fill missing change with zero or relax rules to obtain preferred names.
- **Uncertainty may shrink the usable cohort further.** Bootstrap reliability has not yet been evaluated for player scores. Ten defensible selections per role are not guaranteed by the current eligibility counts.
- **Reserved 2026 has prior EDA exposure.** It remains reserved from model selection; it is not pristine unseen data.

The narrower blended cohort is a project risk to resolve through evidence and a documented method decision before final selection. It is not a reason to silently change the frozen method. The historical global-comparison failure remains recorded.

## Next stages, in order

| Stage | Concrete output | Completion condition |
| --- | --- | --- |
| **1. Development peer baseline — next task** | Historical expected batting runs, striker dismissals, bowling conceded runs and bowler wickets; predictions for 2023–2025 using earlier years only. | Train-only fitting/scaling, attribution and chronological checks pass; prediction errors, wicket calibration, sparse-context fallback and year/family/phase diagnostics are reported. Retain failed or inconclusive results honestly. |
| 2. Model freeze and reserved evaluation | Frozen model choice and development reference scales; separate 2026 evaluation artifact. | No reserved outcomes used for selection; model limitations and drift recorded. |
| 3. Player evidence and reliability | Pressure level and supported change, wider level-only evidence, 1,000 whole-match bootstrap draws, 70/30 and 50/50 comparison, stability and coverage checks. | Scores trace to verified events; missing comparisons remain explicit; assess whether eligibility excludes credible top-ten candidates and whether enough reliable candidates remain. Any necessary method amendment is versioned and justified. |
| 4. Final selections and report | Two ordered lists, evidence cards, supporting/counterexample matches, near-miss review, figures and methodology document. | Recommendations explain consistency and uncertainty; report and exported lists agree; user can review and defend them. |
| 5. Submission readiness | Exact dropdown mapping and upload checks. | Current platform requirements checked, files reconciled and final recommendations reviewed before submission. |

The baseline is a transparent historical peer model. Advanced models are optional only if development evidence demonstrates a useful improvement. The brief does not require ML complexity. Do not treat additional model families as progress by themselves.

## Constraints and working preferences

- **Selector perspective:** the user explicitly requested decisions through the lens of a professional cricket selector. Apply the cricket decision framework in [AGENTS.md](AGENTS.md): role/context, repeatability, tactical tradeoffs, counterevidence and defensible alternatives. This is a reasoning approach, not a claim of credentials. The frozen scoring method remains the active specification.
- Match-date cutoff: **1 November 2026 inclusive**. Preserve immutable supplied inputs and source hashes.
- 2022 is training warm-up only. Development predictions: 2023–2025. Reserved evaluation: 2026. Both innings of a match stay together; each annual fold trains on earlier years.
- Preserve the frozen pressure rule; do not tune thresholds for particular players.
- Keep 70/30 level/change as default and 50/50 as registered variant, with the same eligible cohort. The active amendment limits change to supported contexts.
- Use 1,000 whole-match resamples; approximately 20 model fold/setting bundles. Report uncertainty conditional on fitted models and support.
- Source data, detailed reports, player tables and review ledgers stay private and Git-ignored. Public commits contain code, configurations and documentation.
- Organiser clarification is drafted only; sending is not authorized.
- Explorer T10 remains deferred. Avoid adding a website or auction simulator to this round's deliverables.
- **Commit and push when appropriate for a coherent milestone. Do not force three commits per task.** Existing authorization to push to the project repository remains in effect.
- Shell commands use the `rtk` prefix under the workspace instructions.

## Where to resume

Implemented entry point: `rtk proxy .venv/bin/python -m rr_pressure prepare-method`.
The historical peer fitting command is **not implemented yet**; do not describe the preflight as a trained model.

Key code: [supported_method.py](src/rr_pressure/supported_method.py), [pressure_validation.py](src/rr_pressure/pressure_validation.py), [coverage.py](src/rr_pressure/coverage.py), [cli.py](src/rr_pressure/cli.py).

Local evidence, available with the private workspace:

- [Full reconciliation report](reports/full_reconciliation_2026-11-01/REPORT.md)
- [Pressure-comparison validation](reports/pressure_validation_2026-11-01/REPORT.md)
- [Supported-method preflight](reports/supported_method_2026-11-01/REPORT.md)
- [Current gate](reports/supported_method_2026-11-01/model_gate.json)

Latest analytical milestone: `426f28f`, following method freeze `59e1453` and implementation `ff6bcd9`. Record later analytical milestones here; use Git itself for the live working-tree/synchronization state.

Latest handoff update: added the selector decision framework on 12 November 2026 at the user's request. Documentation only; no model execution, score changes or new test run. Next substantive task remains the development peer baseline.

After a milestone, update the current stage, verified results, unresolved risks, exact next task and artifact links. Distinguish implemented, executed, validated and proposed work. Do not mark the project complete until both submission components are ready.
