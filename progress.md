# Project progress and agent handoff

Last updated: 14 November 2026 (IST).
Current stage: role-based dossiers, counterexample review and the frozen final-window evaluation are complete. Protocol/code were committed as `5ca8bea` before reserved performance access. The unchanged method qualifies 75 batting / 104 bowling entries; 243 final cards, two analytical top tens and a matching methodology are available privately. Exact dropdown mapping and submission packaging remain outstanding. No new predictive models, method tuning or submissions were performed.

## Read this first

This is the current status and handoff record. Read it before continuing implementation and update it after each meaningful milestone. The original architecture is in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md); the work sequence is [PLAYER_EVIDENCE_PLAN.md](PLAYER_EVIDENCE_PLAN.md). The active scoring specification is [DESCRIPTIVE_METHOD_V2.md](DESCRIPTIVE_METHOD_V2.md) and [its approved configuration](configs/descriptive_rating_v2.json), with exact algebra in [RATING_METHOD_DECISION.md](RATING_METHOD_DECISION.md). [SUPPORTED_METHOD.md](SUPPORTED_METHOD.md) is historical and supplies only explicitly inherited exposure/ordinary-support rules. Current user instructions take precedence.

## Final goal and definition of done

The downloaded Round 1 brief asks for a system that compares batting and bowling under pressure with players' usual performance and identifies consistent performers. The required submission has **two components**:

1. Two ordered top-ten lists, one for batters and one for bowlers, with unique players within each list and exact Unstop dropdown selections.
2. A methodology document explaining pressure, ratings, fair comparisons, evidence for the selections, consistency and limitations. Its rankings must match the dropdown selections.

The reproducible pipeline supports those deliverables; it is not a separate required submission component. A website, auction simulator, advanced ML model and explorer are not on the critical path. Qualification is not established by implementation progress.

**Present status:** historical, contextual and retrospective predictive models remain failed calibration results. The explicitly approved descriptive v2 replacement has completed development, reserved 2026 and combined-window evaluation. Two analytical top-ten lists, matching methodology and final player review exist, with 75 batting / 104 bowling entries passing combined-window primary gates. Submission readiness remains false until exact dropdown mapping and upload-format checks are complete; nothing has been submitted.

The approved descriptive ordering compares observed other-player outcomes and recomputes their uncertainty. Its successful development feasibility does not promote a predictive model, establish fully adjusted player ability or validate IPL 2027 forecasts.

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
| Reference-instability review | Reviewed saved predictions only: 38 alerted target/context combinations all have opposing fold-bias signs; 46 of 68 alerts stay above the point tolerance after any single evaluation-match deletion. About 45.52% of development pressure exposure lies in contexts flagged in either fold. | Shows the problem is too broad to ignore in ratings and is not generally explained by one exceptional match; supports moving to observed player evidence while preserving the failed gate. |
| Player evidence implementation plan | Wrote D0–D6 inputs, cohort, dossier metrics, repeatability, case-selection protocol, checks and a bounded rating-method decision. Subsequent execution is recorded below. | Keeps the work concrete and the two ordered lists central. |
| Initial evidence tables — implemented and executed | Frozen [player_evidence_v1.json](configs/player_evidence_v1.json) under `1dfb4e7` before named performance tables. Development-only loader, independently reproduced targets, reconciled context/match/season tables, supported comparisons and shared bootstrap intervals. | Provides concrete performance and support evidence for the rating decision before full dossier rendering. |
| Initial-table rating checkpoint — completed | Reliable descriptive pressure intervals for all 73 batting / 122 bowling level-eligible entries; zero reliable supported-change intervals among eight / fifteen sample-eligible entries. Outcome-free pressure peer audit covers all pressure events of the 62 / 90 level-plus-coverage entries. | Supported the explicit recommendation before full dossier polishing; the user subsequently approved it. |
| Descriptive amendment — approved, executed and validated on development | Versioned under `54be28b` before scoring. Peer-inclusive bootstrap, identical-cohort outcome variants, ordinary companions, family and match/season diagnostics; frozen scales. All 62 / 90 primary sample-plus-coverage entries pass uncertainty. | Produces inspectable development pressure ratings without promoting a failed predictive model or excluding specialists for missing ordinary controls. |
| Development dossiers and counterexample review — completed | 195 level-eligible player-role cards with total/pressure workload, rates and intervals, supported usual comparisons, season/family/match influence, frozen case nominations and source pointers. Reviewed 27 priority entries and boundary/role-similar alternatives. | Turns numerical ratings into cricket evidence; distinguishes adverse examples from unsupported player-wide weakness claims. |
| Final-window protocol — frozen and executed | [Protocol](FINAL_WINDOW_PROTOCOL.md), [configuration](configs/final_window_v1.json) and code committed as `5ca8bea` before access; dependency/source hashes pass before and after execution. Reserved evaluation precedes combined evaluation. | Prevents selection of method/scales from 2026 outcomes. |
| Final evidence and selection review — completed analytically | 243 final cards (93 batting / 150 bowling), source-traceable cases, repeatability, alternatives, temporal evidence, two ordered top tens and matching methodology. Primary gates retain 75 / 104 entries. | Supplies both analytical deliverables; exact dropdown mapping and submission packaging remain. |

Latest implementation verification: **88 tests passed** after contextual revision execution, covering pre-ball target validity, forbidden predictors, training-only scaling, numerical convergence, unchanged validation gates, cohort agreement and provenance, in addition to earlier checks. The first contextual run took approximately 35 seconds locally. Inspected the comparison figure. A repeat execution of the identical frozen candidate verifies the final provenance checks; it is not a new model setting.

Latest verification: **96 tests passed** across the full suite, including eight new reference-audit tests for whole-match peer exclusion at parent/child levels, opposite-partition isolation, fixed balanced assignment, sparse cells, role denominators, development-only exposure access and artifact provenance. The audit opened no target files and fitted no models. `git diff --check` also passed.

Latest implementation verification: **107 tests passed** across the full suite after the retrospective execution. New checks cover hand-calculated recursive means and same-year comparators, complete-partition outcome mutation, forbidden predictors, unseen contexts, role exposure, frozen assignment, development-only target access, budget enforcement, historical cohort/target agreement, fold alerts vetoing pooled success, and output provenance. The single real development execution took 52.64 seconds. Generated the three-page chart pack and inspected the calibration-alert figure. `git diff --check` passed. No new candidate, parameter sweep or reserved fit was run.

Reference-review verification: **115 tests passed** across the full suite after review implementation. Eight review tests cover whole-match deletion, shared resampling, exposure unions, identity integrity, saved-prediction-only loading, provenance and preservation of the failed gate. The review was rerun after a chart-legend layout correction (15.04 seconds); this was diagnostic regeneration, not a new fit. The final eight focused review tests passed again at the planning closeout, and the corrected exposure figure was inspected. Documentation links and `git diff --check` passed. No reserved outcomes, player performance scores or new models were created.

Initial evidence verification: **127 tests passed** across the final full suite (46.91 seconds), including twelve evidence tests covering temporal reads, attribution, supported comparisons, complete-match draws, missing groups, peer exclusion, annotation integrity and provenance. Documentation links, proposal JSON and `git diff --check` passed. Initial execution took 9.35 seconds; final diagnostic regeneration took 18.45 seconds. Targets reproduce verified runs/wicket attribution independently; per-player exposure, support and recency sums reproduce the frozen preflight. Fourteen supplied boundary-flag disagreements and one shared-name label across two player IDs are explicitly exported; do not call all four/six-run events verified boundaries or merge players by name. No new predictive fits, composite ratings or reserved outcome evaluation occurred.

Descriptive implementation verification before score execution: **140 full-suite tests passed** (29.27 seconds), including thirteen new tests for hand-calculated leave-player-out contributions, metric directions, isolation of own outcomes from own peer benchmark, peer-mean recomputation in resamples, linear squared-weight multiplicities, recency/effective counts, peer loss, zero own-cell mass, original change-group invalidation, development-only reads, fixed activation constraints and a complete anonymous synthetic execution. `git diff --check` passed. No live descriptive scores or reserved outcomes were evaluated at this verification checkpoint.

Descriptive execution verification: **143 tests passed** across the final full suite (38.58 seconds). The single fixed development run completed in **28.82 seconds**. Sixteen focused descriptive tests pass, including all-score reproduction by an independent grouped formula, provenance/frozen-scale/gate integrity and inclusion of peers outside the candidate cohort. Documentation links, active configuration and `git diff --check` pass. No predictive fit, reserved outcome evaluation or final ranking was run; the 20-bundle historical fit count is unchanged.

Dossier/final-stage verification before reserved access: **153 tests run, 152 passed and one expected final-artifact skip** (43.28 seconds). Added case deduplication/extrema/ties/small-sample tests, role-similar/boundary alternative checks, complete 195-card/source-event reconciliation, cutoff and year checks, uncommitted-protocol access rejection, missing-temporal-evidence handling and new-loader reproduction of development. Fixed only report formatting/workload presentation during development dossier generation; no score, pressure rule or ordering changed. Agent review of named priority evidence is recorded privately as `EXPERT_REVIEW.md` and hashed before final access.

## Frozen final-window results

Final implementation verification: **154 tests passed** across the full suite (84.31 seconds), with no skips. Tests include independent grouped reproduction of every reserved/final level point score, unchanged protocol/scales and output hashes, exact ten unique entries per role, identical sensitivity cohorts, methodology/list agreement, source-event reconciliation, and access/cutoff contracts. A separate check verified all 18 frozen dependencies, 292 final output hashes and 1,072 local links across 250 Markdown files; `git diff --check` passed. No new computational changes followed the frozen execution.

- A single fixed execution completed in **85.62 seconds**. Reserved 2026 contains 109 matches / 25,946 events; six batting / 28 bowling entries satisfy the unchanged primary gates. The combined 2023–1 November 2026 window contains 511 matches / 121,891 events, with 75 batting / 104 bowling qualifying entries. No forced ten-player reserved-year list is produced.
- All final sample-plus-coverage entries pass the 95% finite-draw gate. Minimum finite fractions across all original level-eligible diagnostics are 98.6% batting / 96.8% bowling. Fixed development scales, shared stratified whole-match draws, peer recomputation, support and source exclusions are unchanged. Every reserved/final point score reproduces a separate grouped calculation.
- Final dossiers retain all 93 batting / 150 bowling level-sample-eligible entries, including coverage-limited players. Reviewed the selected twenty, boundary alternatives and adverse cases in the private final interpretation. Observed rates and total workload remain distinct from pressure-only exposure and the primary index.
- On the identical final primary cohort, 50/50 and 70/30 **runs/wickets** sensitivities retain ten / eight of the default batting top ten and nine / nine bowling entries. These are declared tradeoff sensitivities; the 60/40 primary order is unchanged. Close boundary intervals overlap, so exact places do not imply certain superiority.
- **Temporal qualification:** only seven of the final twenty satisfy the full standalone 2026 rating requirements; two have no retained 2026 pressure observations. Multi-year eligibility does not establish current form or availability. Six batting / five bowling development top-ten entries remain in their final top tens. Do not tune inactivity rules or the method after seeing these results.
- No supported-change interval is reliable in either reserved or combined evidence. Conditional 70/30 and 50/50 level/change companions remain unavailable; absent change is not zero. Final pressure share is **35.30%** of delivery events, above the 20–30% diagnostic target; unchanged late-over, collapse and tight-chase rules explain its breadth.
- Analytical top-ten creation passes; submission readiness and dropdown verification remain false. Detailed lists, methodology, final review and provenance are private under `reports/final_window_evaluation_2026-11-01/`. There are no new predictive fits; the historical fit count remains 20.

## Approved descriptive development results

- Primary sample, source coverage and pressure-peer coverage gates retain **62 batting / 90 bowling entries**. All pass the at-least-95%-finite uncertainty rule. The minimum finite fractions across all original level-eligible diagnostic entries are 98.5% batting / 96.9% bowling. Every point uses leave-player-out other-player outcomes, with peer means recomputed in each shared match draw.
- Ordinary supported-change validity reproduces the initial evidence exactly. Zero eligible development change intervals are reliable, so both level/change companion orderings remain withheld. No missing comparison is filled with zero.
- On the identical primary cohort, changing the **runs/wickets** mix from 60/40 to 50/50 or 70/30 retains nine of the default batting top ten. Bowling retains eight / nine respectively. Maximum absolute shifts anywhere in the eligible ranking are eight / ten places for batting and eleven / fifteen for bowling. These are tradeoff sensitivities, not predictive validation failures; keep the declared default and review boundary candidates.
- All-match and season deletions recompute both player and peer point contributions under the original support. They are sensitivity estimates, not fresh bootstrap rankings. Among the development top ten, five of thirty batting season deletions and four of thirty bowling season deletions leave inadequate remaining sample evidence. Do not treat those unavailable robustness claims as player failure.
- Nine of the development batting top ten and eight bowling entries have evidence in both families. Family diagnostics remain descriptive: 19/19 corresponding batting intervals and 17/18 bowling intervals meet finite-draw requirements. Unequal family exposure and unmeasured opposition strength still require selector review.
- Numerical scales were frozen in the private `frozen_scales.json` before scores. The historical development gate passes feasibility but itself withholds final-ranking readiness and makes no full-context-comparability or forecasting claim. The separate final-stage results above now supply combined-window analytical readiness.

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

## Reference review findings and current decision

- Reviewed the saved development predictions and model tables across 402 matches / 95,945 events. There are 38 alerted target/context combinations spanning 15 of 36 year/family/innings/phase contexts. All 38 have opposite fold-bias signs; median cancellation of their weighted absolute fold bias is 92.04%. Aggregate centering therefore does not establish accurate contextual player credit.
- In all 68 alerts, the absolute within-cell outcome gap between partitions exceeds the absolute registered shrinkage component. This decomposition does not establish a causal explanation. Forty-six alerts remain above the point threshold after any single evaluation-match deletion; this is a fixed-prediction sensitivity, not a refit or a new calibration gate.
- Joint match-bootstrap raw fold-mean gap intervals exclude zero in 21 of 38 alerted target contexts. These raw-mean diagnostics answer a different question from conditional prediction calibration and do not replace its failed screen.
- Contexts flagged in either fold contain **45.52% of batting pressure opportunities and 45.52% of bowling pressure attempts**. For T20I late-over pressure, the corresponding shares are 74.87% and 74.90%. These are affected exposure shares, not player-performance deductions. All 73 development level-eligible batting entries and 121 of 122 bowling entries have some affected exposure.
- **Decision at that checkpoint:** stop automatic model experimentation and preserve 20 used bundles and every failed promotion gate. Subsequent dossier work, explicit method approval and frozen final evaluation are recorded separately above; the failed reference was never promoted.

## Main limitations and alignment risks

- **Submission packaging remains incomplete.** Analytical recommendations, methodology and role/counterexample review are complete. Verify exact dropdown identities and upload format; do not add candidates or infrastructure automatically.
- **A predictive improvement is not sufficient contextual fairness.** Both expectation candidates fail the calibration screen. Do not silently promote v2, relax the screen, or subtract evaluation-group means using those same outcomes and call that independent validation.
- **Contemporary reference fails partition calibration.** [The reference decision](RETROSPECTIVE_REFERENCE.md) and models are implemented. Other matches later in the season inform the reference. Zero pooled alerts conceal 68 separate-fold alerts (39 run / 29 wicket alerts), all in year/family/innings/phase groups. For 2023 T20I second-innings middle-over batting, the biases are −18.87 and +17.39 runs per 100 opportunities in the two folds, with both intervals excluding zero. Match-count balance does not ensure comparable scoring conditions or player/opposition mix; the cause is not established. The unchanged gate blocks promotion and reserved fitting.
- **Coverage is uneven.** T20I retention is materially below IPL retention. Missing-source and quarantined players cannot be interpreted as weak performers. Resolve remaining cases selectively when they materially affect plausible recommendations; do not restart exhaustive repair by default.
- **Comparison eligibility is restrictive.** In the final 2023–2026 scoring window, 93 batters / 150 bowlers pass level sample checks; only 11 / 16 also pass supported-change and 80% source-retention requirements. Development counts for those combined checks are 6 / 12. These are evidence counts, not a shortlist or performance result.
- **Ranking only the blended cohort may exclude strong specialists.** A late-over specialist can have substantial pressure performance evidence but little ordinary comparison evidence. Evaluate this selection limitation explicitly before claiming the ten best players overall. Keep level evidence visible for the wider population. Do not fill missing change with zero or relax rules to obtain preferred names.
- **Recent evidence is uneven.** Only seven selected entries meet all standalone 2026 rating requirements; two have no retained 2026 pressure observations. The fixed method does not impose availability or inactivity filters. Avoid claims that all twenty are currently in form or available.
- **Supported-change uncertainty is inadequate.** No change interval passes the frozen 95% finite-draw threshold in development, reserved or final evaluation. Keep supported comparisons visible with limitations and both conditional blend variants unavailable; pressure-rate intervals alone do not validate change or fully adjusted ability.
- **The descriptive amendment passes computational and sample feasibility, not full contextual fairness.** It replaces mandatory primary 70/30 level/change ordering with one empirical peer-relative pressure ordering; keeps supported usual-performance evidence and conditional companions; recomputes peer uncertainty. It remains a descriptive retained-data index, not causal ability or an IPL transfer forecast. Venue, opposition strength and fine chase difficulty remain incompletely measured.
- **Reserved 2026 has prior EDA exposure.** It remains reserved from model selection; it is not pristine unseen data.

The narrower blended cohort and unreliable change intervals were addressed through the explicitly approved primary-method amendment. They remain interpretation limits, not permission to silently change the frozen method. The historical global-comparison failure remains recorded.

## Next stages, in order

| Stage | Concrete output | Completion condition |
| --- | --- | --- |
| 1. Development peer baseline — completed | Historical expected runs and wickets, annual/pooled losses, calibration, fallback, sensitivity, whole-match uncertainty and chart pack. | Executed with 77 passing tests; benchmark screen passes, calibration screen fails. Preserve the failed gate and its evidence. |
| 1b. Focused baseline amendment — completed | One fixed contextual revision, paired comparisons, calibration report, convergence checks and chart pack. | Executed with 88 passing tests; run prediction improves but the unchanged calibration gate fails. No promotion or further automatic candidate fits. |
| 1c. Rating-reference decision — completed | Outcome-free support audit and frozen two-fold same-season reference specification; rejected hundreds of exact leave-match-out fits. | Audit passes; no targets opened. Explicit budget maximum amended to 22 for two development and two reserved bundles. No new fits spent. |
| 1d. Retrospective development reference — completed, gate failed | Two registered bundles, models/membership, held-out predictions, losses, pooled and separate-fold calibration, comparisons and chart pack. | 107 tests pass; benchmarks/support pass; zero pooled / 68 separate-fold alerts. Candidate scales stay unfrozen; cumulative usage 20 of 22. |
| 1e. Reference-instability review — completed | Saved-prediction decomposition, fold comparisons, match influence, role/player exposure and chart pack. | 115 full-suite tests passed; no new fits or reserved outcomes; failed gate preserved. Automatic model search is stopped. |
| D0–D1. Dossier contract and development ledger — completed | Versioned dossier contract, development-only loader, role/match/context summaries, coverage and cohort register. | Frozen counts and per-player denominators reconcile; all 73 batting / 122 bowling level-eligible player-role entries retained, with exclusion reasons for others. No composite scores. |
| D2–D3. Development dossiers and review — completed | 195 cards, rate intervals, usual-comparison availability, workload profiles, deterministic supporting/adverse cases, source traces and alternative review. | All level-eligible entries retained; 27 priority entries interpreted before reserved access. Total workload is separate from the pressure subset; all candidate ordering remains frozen. |
| D4. Rating-method decision — approved and development validated | [Active v2 specification](DESCRIPTIVE_METHOD_V2.md), [configuration](configs/descriptive_rating_v2.json), [decision algebra](RATING_METHOD_DECISION.md) and descriptive engine. | Committed as `54be28b` before the single fixed run; 62 / 90 primary entries rankable. Scales frozen; all-score independent arithmetic and uncertainty/gate checks pass. No automatic search or final ranking claims. |
| **D5. Frozen final-window evaluation — completed** | Separate 2026 diagnostics, combined-window evidence, 243 refreshed cards, temporal review and two analytical top tens. | Protocol/dependencies committed before access at `5ca8bea`; fixed scales and all gates retained; no forced ten-player reserved-year list or method tuning. |
| D6. Final selections and report — analytical package complete; mapping pending | Two ordered lists, selection cards, alternatives, matching methodology and final interpretation exist privately. | Exact dropdown identities and upload format still need verification. Analytical outputs do not certify submission readiness; nothing submitted. |

The brief does not require ML complexity. Automatic model experimentation is stopped. The next milestone is exact-name mapping and submission packaging of the completed analytical deliverables. Keep the fixed ordering and its uncertainty visible.

## Constraints and working preferences

- **Selector perspective:** the user explicitly requested decisions through the lens of a professional cricket selector. Apply the cricket decision framework in [AGENTS.md](AGENTS.md): role/context, repeatability, tactical tradeoffs, counterevidence and defensible alternatives. This is a reasoning approach, not a claim of credentials. The frozen scoring method remains the active specification.
- Match-date cutoff: **1 November 2026 inclusive**. Preserve immutable supplied inputs and source hashes.
- 2022 contributes no player scoring evidence. Historical v1/v2 annual folds trained on earlier years. The specified retrospective candidate instead uses two complete-match development partitions across 2023–2025, with year in the hierarchy; no 2022 data enters that candidate. Both innings stay together. The 2026 procedure remains reserved from method selection.
- Preserve the frozen pressure rule; do not tune thresholds for particular players.
- Under the user-approved v2 amendment, primary ordering uses pressure performance. Keep 70/30 level/change as default and 50/50 as registered **conditional companion** variants on the identical adequate cohort; never fill missing change. Preserve the original supported-context comparison rules and disclose that the descriptive change differs from the former residual statistic. Runs/wickets remain 60/40 by default, with 50/50 and 70/30 outcome sensitivities on the common primary cohort.
- Use 1,000 whole-match resamples. Historical v1 used 15 predictive fold/setting bundles, contextual v2 three and retrospective development two: **20 used of amended maximum 22**. The two predictive reserved bundles remain unused because those model gates failed. Do not repurpose them for another automatic search. V2 descriptive aggregate recomputation adds no predictive fits; its uncertainty is conditional on retained data, frozen scales, support and eligibility, with player and peer means recomputed in each draw. Keep prior fixed-model uncertainty limitations for the historical prediction reports.
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

Reference development: `rtk proxy env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m rr_pressure fit-retrospective-reference`. Code: [retrospective_reference.py](src/rr_pressure/retrospective_reference.py), [retrospective_figures.py](src/rr_pressure/retrospective_figures.py). It reads only development targets, reuses frozen match assignments, produces two four-target bundles and exports the failed gate. Do not rerun it as a new experiment or open reserved outcomes automatically. Its saved predictions have now been reviewed.

Reference review: `rtk proxy env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m rr_pressure review-reference`. Code: [reference_review.py](src/rr_pressure/reference_review.py), [reference_review_figures.py](src/rr_pressure/reference_review_figures.py). Implemented and executed; uses existing predictions only, preserves the gate, and produces exposure diagnostics without performance scores.

Initial evidence command: `rtk proxy env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m rr_pressure build-player-evidence`. Implemented and executed; exports initial development tables, descriptive intervals and exposure-only feasibility. Do not rerun as an experiment or interpret the rates as approved ratings.

Descriptive development command: `rtk proxy env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m rr_pressure.descriptive_rating`. Implemented and executed once under `54be28b`; do not rerun as an experiment. It consumes only development evidence, freezes scales before score output and computes peer-inclusive uncertainty. The original disabled proposal stays historical. The formula was fixed before numerical pressure ratings were inspected; reserved outcomes remain disabled in this command.

Development dossiers: `rtk proxy env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m rr_pressure.player_dossiers`. Implemented/executed; private `EXPERT_REVIEW.md` records the named-priority interpretation separately from automated card checks. Do not rerun as a selection experiment.

**Frozen final evaluation is implemented and executed:** `rtk proxy env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m rr_pressure.final_window`. Protocol/code were committed under `5ca8bea` before reserved access; all pinned hashes passed. Reserved 2026 preceded the combined window, using frozen development scales. Do not rerun as a new experiment or change the accepted method. **Resume with final methodology/list review, exact dropdown mapping and upload-format checks.** No submission or organizer contact is authorized here.

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
- [Reference-instability review](reports/reference_instability_review_2026-11-01/REPORT.md)
- [Instability chart pack](reports/reference_instability_review_2026-11-01/INSTABILITY_REVIEW.pdf)
- [Pressure exposure to flagged contexts](reports/reference_instability_review_2026-11-01/pressure_exposure.csv)
- [Review provenance](reports/reference_instability_review_2026-11-01/manifest.json)
- [Initial observed evidence report](reports/player_evidence_development_2026-11-01/REPORT.md)
- [Initial evidence reconciliation](reports/player_evidence_development_2026-11-01/validation.json)
- [Anonymous rating-decision evidence](reports/player_evidence_development_2026-11-01/decision_evidence_summary.json)
- [Observed pressure and supported-change uncertainty](reports/player_evidence_development_2026-11-01/observed_uncertainty.parquet)
- [Exposure-only pressure-peer support](reports/player_evidence_development_2026-11-01/pressure_peer_support.csv)
- [Initial evidence provenance](reports/player_evidence_development_2026-11-01/manifest.json)
- [Descriptive development report](reports/descriptive_rating_development_2026-11-01/REPORT.md)
- [Descriptive development feasibility gate](reports/descriptive_rating_development_2026-11-01/development_gate.json)
- [Frozen development normalization](reports/descriptive_rating_development_2026-11-01/frozen_scales.json)
- [Outcome-weight stability](reports/descriptive_rating_development_2026-11-01/outcome_weight_stability.csv)
- [Descriptive development provenance](reports/descriptive_rating_development_2026-11-01/manifest.json)
- [Development dossier index](reports/player_dossiers_development_2026-11-01/index.csv)
- [Development selector review](reports/player_dossiers_development_2026-11-01/SELECTOR_REVIEW.md)
- [Agent priority interpretation before reserved access](reports/player_dossiers_development_2026-11-01/EXPERT_REVIEW.md)
- [Dossier/source trace provenance](reports/player_dossiers_development_2026-11-01/manifest.json)
- [Frozen final evaluation report](reports/final_window_evaluation_2026-11-01/REPORT.md)
- [Two ordered analytical top tens](reports/final_window_evaluation_2026-11-01/two_top_ten_lists.csv)
- [Matching final methodology](reports/final_window_evaluation_2026-11-01/METHODOLOGY.md)
- [Final selection/counterexample interpretation](reports/final_window_evaluation_2026-11-01/FINAL_AGENT_REVIEW.md)
- [Final dossier index](reports/final_window_evaluation_2026-11-01/final_2023_2026/player_dossiers/index.csv)
- [Development/reserved/final temporal review](reports/final_window_evaluation_2026-11-01/temporal_review.csv)
- [Final analytical gate — mapping/submission incomplete](reports/final_window_evaluation_2026-11-01/evaluation_gate.json)
- [Final output provenance](reports/final_window_evaluation_2026-11-01/manifest.json)

Latest analytical milestone: dossiers, counterexample review and frozen final evaluation under protocol/code commit `5ca8bea`, producing two analytical lists and matching methodology. Approved descriptive specification/implementation: `54be28b`; initial observed evidence contract: `1dfb4e7`; rating recommendation: `6bdee1d`; no-fit reference review: `65be28c`. Latest predictive model milestone remains `a0c295d` under specification `b81d01a`; it is still failed. Use Git itself for live synchronization state.

Latest handoff update: the requested implementation and execution are complete. Final role/counterexample interpretation and matching methodology were added after computation without changing any protocol, scale or ordered list; their hashes are included in the private final manifest. Next finish exact dropdown mapping and submission packaging. Preserve the two-list goal, cutoff, pressure rules, shared match bootstrap, source exclusions, failed model gates and explicit temporal limitations.

After a milestone, update the current stage, verified results, unresolved risks, exact next task and artifact links. Distinguish implemented, executed, validated and proposed work. Do not mark the project complete until both submission components are ready.
