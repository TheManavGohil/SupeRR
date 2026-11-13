# Project progress and agent handoff

Last updated: 13 November 2026 (IST).
Current stage: the fixed retrospective reference is implemented and evaluated on development. Loss benchmarks and peer support pass, but 68 separate-fold calibration alerts fail the preregistered gate despite zero pooled alerts. No reference is promoted. Next review the failed contexts and partition instability before a documented player-evidence decision; no further automatic fits, reserved outcome evaluation or player scoring.

## Read this first

This is the current status and handoff record. Read it before continuing implementation and update it after each meaningful milestone. The detailed architecture is in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md); the active scoring specification is [SUPPORTED_METHOD.md](SUPPORTED_METHOD.md) and [its frozen configuration](configs/supported_method_v1.json). That amendment supersedes the original global pressure-change model. Current user instructions take precedence over these documents.

## Final goal and definition of done

The downloaded Round 1 brief asks for a system that compares batting and bowling under pressure with players' usual performance and identifies consistent performers. The required submission has **two components**:

1. Two ordered top-ten lists, one for batters and one for bowlers, with unique players within each list and exact Unstop dropdown selections.
2. A methodology document explaining pressure, ratings, fair comparisons, evidence for the selections, consistency and limitations. Its rankings must match the dropdown selections.

The reproducible pipeline supports those deliverables; it is not a separate required submission component. A website, auction simulator, advanced ML model and explorer are not on the critical path. Qualification is not established by implementation progress.

**Present status:** historical, contextual and retrospective peer models have been evaluated on 2023–2025; all fail their required calibration gates. No player scores or rankings have been produced, no final methodology document is completed, and no submission has been made. Reserved 2026 outcome evaluation has not been performed. Prediction validation is implemented, but no reference is approved for final ratings.

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
| Supported method freeze | Separate all-pressure performance level from change within supported same-player/year contexts. Preserve unavailable change as missing. | Defines what we can honestly estimate for each player. |sortt
| Model preflight | Separate features, targets and identities; complete-match chronological folds and outcome-independent eligibility tables exported. | Makes the first baseline ready to implement without future-outcome leakage. |
| Development baseline | Historical peer models evaluated across 402 matches / 95,945 delivery events in 2023–2025, using earlier-year training. Four targets, five registered prior settings, 15 fold/setting bundles. | Produces out-of-time expected runs and wicket probabilities, plus transparent historical comparators. |
| Baseline validation | Default improves pooled primary loss for all four targets against global and family means, and against global means in all three years. Found 29 overlapping material calibration alerts. | Shows the baseline is informative, but could misattribute scoring-context differences to players if promoted now. |
| One contextual revision | Fixed ridge/logistic models add verified pre-ball pace, wickets/progress and chase context, with 365-day expectation recency. Three development bundles; 18 cumulative. | Tests whether more precise cricket context reduces unfair attribution of scoring conditions. |
| Revision assessment | Batting/bowling run loss improves 1.74%/1.61% against v1; wicket gains are inconclusive. Alerts fall to 18; unchanged promotion gate fails. | Preserves a better predictive benchmark without claiming it is ready to select players. |
| Retrospective reference decision and support audit | Compared exact match exclusion with two fixed match partitions using development exposures only. Two-fold pressure peer support is 99.12% batting / 99.12% bowling; weakest year/family/role/exposure group 95.83%. | Supports testing contemporary peers for retrospective selection without evaluating a match against its own outcomes. Availability is established; accuracy remains untested. |
| Retrospective reference implementation and validation | Two fixed development bundles / eight target models; 402 matches / 95,945 events. All targets beat global/family benchmarks; zero pooled but 68 separate-fold calibration alerts. | Exposes substantial opposite-direction reference errors hidden by aggregate centering; blocks unsupported player credit or blame. |

Latest implementation verification: **88 tests passed** after contextual revision execution, covering pre-ball target validity, forbidden predictors, training-only scaling, numerical convergence, unchanged validation gates, cohort agreement and provenance, in addition to earlier checks. The first contextual run took approximately 35 seconds locally. Inspected the comparison figure. A repeat execution of the identical frozen candidate verifies the final provenance checks; it is not a new model setting.

Latest verification: **96 tests passed** across the full suite, including eight new reference-audit tests for whole-match peer exclusion at parent/child levels, opposite-partition isolation, fixed balanced assignment, sparse cells, role denominators, development-only exposure access and artifact provenance. The audit opened no target files and fitted no models. `git diff --check` also passed.

Latest implementation verification: **107 tests passed** across the full suite after the retrospective execution. New checks cover hand-calculated recursive means and same-year comparators, complete-partition outcome mutation, forbidden predictors, unseen contexts, role exposure, frozen assignment, development-only target access, budget enforcement, historical cohort/target agreement, fold alerts vetoing pooled success, and output provenance. The single real development execution took 52.64 seconds. Generated the three-page chart pack and inspected the calibration-alert figure. `git diff --check` passed. No new candidate, parameter sweep or reserved fit was run.

## Original baseline findings

- The default remains 200 prior events. Loss reductions against the training global mean are 0.74% for batting runs, 0.69% for bowling concessions, 0.44% for striker dismissals and 0.39% for bowler wickets. These are modest predictive gains, not player performance improvements. All paired whole-match 10th–90th percentile loss-difference intervals favour the context model.
- Calibration screening was specified before the first fit in [baseline_validation_v1.json](configs/baseline_validation_v1.json). Material thresholds are 0.10 runs or 0.01 wickets per opportunity, at least 500 events and ten matches, and a match-bootstrap interval excluding zero. These are project screening choices, not universal standards.
- There are 29 overlapping alerts: 27 for run expectations and two for wicket expectations. Most run alerts involve underpredicted IPL scoring. For example, 2024 IPL second-innings powerplay batting runs exceed expectations by 28.16 per 100 non-wide opportunities. The cause could involve changing scoring conditions or player mix; the diagnostic does not establish a cause.
- Overall ordinary batting opportunities average +11.03 runs per 100 above expectations, while pressure opportunities average −2.84. Those populations differ; this is not a player-change or causal estimate. It flags a potential distortion to investigate before judging players against the reference.
- No development observation required an unseen-context fallback. Sparse-context handling is tested, but absent cells do not explain the observed live bias.
- **Decision:** preserve this baseline as the benchmark; do not promote it to reserved evaluation or final player scoring yet. Development reference scales are exported as candidates, not frozen final scales. All frozen pressure/weight/cutoff rules remain intact.

## Latest contextual revision findings and decision

- The fixed candidate was committed before fitting as `018af8f`; specification: [CONTEXT_BASELINE_V2.md](CONTEXT_BASELINE_V2.md) and [configuration](configs/context_baseline_v2.json). No second candidate or parameter search was run.
- All four targets pass the pooled point-loss comparison with v1 and the original global/family benchmark screen. Batting run MSE improves 1.74%, bowling concession MSE 1.61%; their paired whole-match intervals favour v2. Wicket Brier improvements are tiny and their intervals include no improvement, so do not claim a reliable wicket-prediction gain.
- Material alerts change from 27 run / two wicket alerts in v1 to **13 run / five wicket alerts in v2**. The remaining total is **18 overlapping alerts**. The threshold and match-bootstrap screen were not relaxed.
- Ordinary batting mean bias falls from +11.03 to +4.84 runs per 100 opportunities; pressure batting bias changes from −2.84 to +2.21. These are different exposure populations, not player-change or causal effects.
- The 2024 IPL second-innings powerplay batting bias falls from +28.16 to +16.96 runs per 100 opportunities, still above the threshold. Remaining concerns include IPL powerplays and T20I second-innings late wickets.
- All logistic fits converge. A small number of negative run predictions are floored at zero and extreme required rates are clipped as registered; counts are disclosed. Player-rating recency remains 730 days; only expectation training uses the amended 365-day weighting.
- **Decision:** v2 is not promoted. Its reference scales remain candidates; 2026 outcomes and player rankings remain unevaluated. Preserve both failed gates. At that milestone two bundles remained under the internal maximum of 20; the retrospective decision below explicitly amends that budget. No automatic search is permitted.

## Main limitations and alignment risks

- **Final recommendations are still missing.** The specified retrospective development candidate is now evaluated and fails promotion. Next perform a bounded review of failed contexts/reference instability and document a player-evidence decision; do not add more candidates or infrastructure automatically.
- **A predictive improvement is not sufficient contextual fairness.** Both expectation candidates fail the calibration screen. Do not silently promote v2, relax the screen, or subtract evaluation-group means using those same outcomes and call that independent validation.
- **Contemporary reference fails partition calibration.** [The reference decision](RETROSPECTIVE_REFERENCE.md) and models are implemented. Other matches later in the season inform the reference. Zero pooled alerts conceal 68 separate-fold alerts (39 run / 29 wicket alerts), all in year/family/innings/phase groups. For 2023 T20I second-innings middle-over batting, the biases are −18.87 and +17.39 runs per 100 opportunities in the two folds, with both intervals excluding zero. Match-count balance does not ensure comparable scoring conditions or player/opposition mix; the cause is not established. The unchanged gate blocks promotion and reserved fitting.
- **Coverage is uneven.** T20I retention is materially below IPL retention. Missing-source and quarantined players cannot be interpreted as weak performers. Resolve remaining cases selectively when they materially affect plausible recommendations; do not restart exhaustive repair by default.
- **Comparison eligibility is restrictive.** In the final 2023–2026 scoring window, 93 batters / 150 bowlers pass level sample checks; only 11 / 16 also pass supported-change and 80% source-retention requirements. Development counts for those combined checks are 6 / 12. These are evidence counts, not a shortlist or performance result.
- **Ranking only the blended cohort may exclude strong specialists.** A late-over specialist can have substantial pressure performance evidence but little ordinary comparison evidence. Evaluate this selection limitation explicitly before claiming the ten best players overall. Keep level evidence visible for the wider population. Do not fill missing change with zero or relax rules to obtain preferred names.
- **Uncertainty may shrink the usable cohort further.** Bootstrap reliability has not yet been evaluated for player scores. Ten defensible selections per role are not guaranteed by the current eligibility counts.
- **Reserved 2026 has prior EDA exposure.** It remains reserved from model selection; it is not pristine unseen data.

The narrower blended cohort is a project risk to resolve through evidence and a documented method decision before final selection. It is not a reason to silently change the frozen method. The historical global-comparison failure remains recorded.

## Next stages, in order

| Stage | Concrete output | Completion condition |
| --- | --- | --- |
| 1. Development peer baseline — completed | Historical expected runs and wickets, annual/pooled losses, calibration, fallback, sensitivity, whole-match uncertainty and chart pack. | Executed with 77 passing tests; benchmark screen passes, calibration screen fails. Preserve the failed gate and its evidence. |
| 1b. Focused baseline amendment — completed | One fixed contextual revision, paired comparisons, calibration report, convergence checks and chart pack. | Executed with 88 passing tests; run prediction improves but the unchanged calibration gate fails. No promotion or further automatic candidate fits. |
| 1c. Rating-reference decision — completed | Outcome-free support audit and frozen two-fold same-season reference specification; rejected hundreds of exact leave-match-out fits. | Audit passes; no targets opened. Explicit budget maximum amended to 22 for two development and two reserved bundles. No new fits spent. |
| 1d. Retrospective development reference — completed, gate failed | Two registered bundles, models/membership, held-out predictions, losses, pooled and separate-fold calibration, comparisons and chart pack. | 107 tests pass; benchmarks/support pass; zero pooled / 68 separate-fold alerts. Candidate scales stay unfrozen; cumulative usage 20 of 22. |
| **1e. Reference-instability review — next task** | Bounded review of failed contexts and their match/role exposure, using existing predictions; documented decision on defensible player evidence. | Preserve failed gates. No new candidate or partition search, threshold relaxation, reserved outcome access or player scores by default. Resolve the reference limitation explicitly before resuming rating stages. |
| 2. Model freeze and reserved evaluation | Frozen model choice and development reference scales; separate two-fold 2026 evaluation artifact. | No reserved outcomes used for method selection. Other-fold 2026 outcomes may set a match-excluded reference after freeze; label retrospective procedure evaluation, not outcome-free forecasting. Preserve limitations and failed gates. |
| 3. Player evidence and reliability | Pressure level and supported change, wider level-only evidence, 1,000 whole-match bootstrap draws, 70/30 and 50/50 comparison, stability and coverage checks. | Scores trace to verified events; missing comparisons remain explicit; assess whether eligibility excludes credible top-ten candidates and whether enough reliable candidates remain. Any necessary method amendment is versioned and justified. |
| 4. Final selections and report | Two ordered lists, evidence cards, supporting/counterexample matches, near-miss review, figures and methodology document. | Recommendations explain consistency and uncertainty; report and exported lists agree; user can review and defend them. |
| 5. Submission readiness | Exact dropdown mapping and upload checks. | Current platform requirements checked, files reconciled and final recommendations reviewed before submission. |

The baseline is a transparent historical peer model. Advanced models are optional only if development evidence demonstrates a useful improvement. The brief does not require ML complexity. Do not treat additional model families as progress by themselves.

## Constraints and working preferences

- **Selector perspective:** the user explicitly requested decisions through the lens of a professional cricket selector. Apply the cricket decision framework in [AGENTS.md](AGENTS.md): role/context, repeatability, tactical tradeoffs, counterevidence and defensible alternatives. This is a reasoning approach, not a claim of credentials. The frozen scoring method remains the active specification.
- Match-date cutoff: **1 November 2026 inclusive**. Preserve immutable supplied inputs and source hashes.
- 2022 contributes no player scoring evidence. Historical v1/v2 annual folds trained on earlier years. The specified retrospective candidate instead uses two complete-match development partitions across 2023–2025, with year in the hierarchy; no 2022 data enters that candidate. Both innings stay together. The 2026 procedure remains reserved from method selection.
- Preserve the frozen pressure rule; do not tune thresholds for particular players.
- Keep 70/30 level/change as default and 50/50 as registered variant, with the same eligible cohort. The active amendment limits change to supported contexts.
- Use 1,000 whole-match resamples; approximately 20 model fold/setting bundles. Historical v1 used 15, contextual v2 three, retrospective development two: **20 used of amended maximum 22**. The two reserved bundles remain unused because development failed. One fixed setting and partition salt; no hidden leave-match-out fits or full-data refit. Do not repurpose reserved capacity for another automatic search. Report uncertainty conditional on fitted models and support.
- Source data, detailed reports, player tables and review ledgers stay private and Git-ignored. Public commits contain code, configurations and documentation.
- Organiser clarification is drafted only; sending is not authorized.
- Explorer T10 remains deferred. Avoid adding a website or auction simulator to this round's deliverables.
- **Commit and push when appropriate for a coherent milestone. Do not force three commits per task.** Existing authorization to push to the project repository remains in effect.
- Shell commands use the `rtk` prefix under the workspace instructions.

## Where to resume

Implemented commands: `rtk proxy .venv/bin/python -m rr_pressure prepare-method` and `rtk proxy .venv/bin/python -m rr_pressure fit-baseline`.
`fit-baseline` executes development folds only. It deliberately refuses 2026 fitting in this stage and exports a failed promotion gate when material bias remains. The preflight artifacts retain their original no-model status as historical inputs; use the newer baseline gate for current model readiness.

Contextual revision: `rtk proxy env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m rr_pressure fit-context-baseline`. This executes development only and preserves the original artifacts. Its failed gate remains a historical result alongside v1; the retrospective gate is now the latest decision.

Key code: [baseline.py](src/rr_pressure/baseline.py), [baseline_figures.py](src/rr_pressure/baseline_figures.py), [supported_method.py](src/rr_pressure/supported_method.py), [pressure_validation.py](src/rr_pressure/pressure_validation.py), [coverage.py](src/rr_pressure/coverage.py), [cli.py](src/rr_pressure/cli.py).

Revision code: [context_baseline.py](src/rr_pressure/context_baseline.py), [context_figures.py](src/rr_pressure/context_figures.py).

Reference audit: `rtk proxy .venv/bin/python -m rr_pressure audit-reference`. Code: [reference_audit.py](src/rr_pressure/reference_audit.py). This command consumes development exposure/context files only. [RETROSPECTIVE_REFERENCE.md](RETROSPECTIVE_REFERENCE.md) and [retrospective_reference_v1.json](configs/retrospective_reference_v1.json) govern the implemented candidate, including explicit budget and temporal-boundary amendments; supported-change and ranking rules remain in `SUPPORTED_METHOD.md`.

Reference development: `rtk proxy env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m rr_pressure fit-retrospective-reference`. Code: [retrospective_reference.py](src/rr_pressure/retrospective_reference.py), [retrospective_figures.py](src/rr_pressure/retrospective_figures.py). It reads only development targets, reuses frozen match assignments, produces two four-target bundles and exports the failed gate. Do not rerun it as a new experiment or open reserved outcomes automatically. Review the saved predictions and diagnostics next.

Local evidence, available with the private workspace:

- [Full reconciliation report](reports/full_reconciliation_2026-11-01/REPORT.md)
- [Pressure-comparison validation](reports/pressure_validation_2026-11-01/REPORT.md)
- [Supported-method preflight](reports/supported_method_2026-11-01/REPORT.md)
- [Historical preflight gate](reports/supported_method_2026-11-01/model_gate.json)
- [Development baseline report](reports/baseline_development_2026-11-01/REPORT.md)
- [Baseline diagnostic chart pack](reports/baseline_development_2026-11-01/BASELINE_CHARTS.pdf)
- [Original baseline promotion gate](reports/baseline_development_2026-11-01/model_gate.json)
- [Contextual revision report](reports/context_baseline_v2_2026-11-01/REPORT.md)
- [Contextual comparison chart pack](reports/context_baseline_v2_2026-11-01/CONTEXT_CHARTS.pdf)
- [Contextual promotion gate — historical failed result](reports/context_baseline_v2_2026-11-01/model_gate.json)
- [Retrospective reference feasibility report](reports/reference_audit_2026-11-01/REPORT.md)
- [Reference feasibility gate — not a promotion gate](reports/reference_audit_2026-11-01/feasibility_gate.json)
- [Fixed development match partitions](reports/reference_audit_2026-11-01/match_partitions.csv)
- [Retrospective development report](reports/retrospective_reference_development_2026-11-01/REPORT.md)
- [Latest promotion gate — failed](reports/retrospective_reference_development_2026-11-01/model_gate.json)
- [Retrospective chart pack](reports/retrospective_reference_development_2026-11-01/REFERENCE_CHARTS.pdf)
- [Separate-fold calibration](reports/retrospective_reference_development_2026-11-01/fold_calibration.csv)

Latest analytical milestone: retrospective development reference, executed 13 November 2026 under specification commit `b81d01a`, with input/config/code/output provenance. Previous model milestone: contextual revision, specified as `018af8f` and pushed as `f50e72a`. Original baseline: `6b065d2`; preparation: `426f28f`. Use Git itself for live synchronization state.

Latest handoff update: implemented/evaluated the fixed retrospective reference, recorded 107 passing tests and the separate-fold failure, and stopped at 20 used bundles. Existing forecast failures remain unchanged. Next review saved failed contexts/reference instability and document the player-evidence decision; do not equate pooled centering with valid selection scores or start another search.

After a milestone, update the current stage, verified results, unresolved risks, exact next task and artifact links. Distinguish implemented, executed, validated and proposed work. Do not mark the project complete until both submission components are ready.
