# Active descriptive pressure method, version 2

The user approved the explicit primary-ordering amendment on 14 November 2026 with “yes, go ahead!” after reviewing the initial evidence and rating recommendation. [The active configuration](configs/descriptive_rating_v2.json) activates development execution of the exact formula in [RATING_METHOD_DECISION.md](RATING_METHOD_DECISION.md). The disabled proposal remains a historical record. Approval is not evidence that the implementation or development gate has passed.

This amendment supersedes the residual-based primary ordering in [SUPPORTED_METHOD.md](SUPPORTED_METHOD.md). Its opportunity definitions, original exposure/source-coverage thresholds, supported ordinary comparison rules, 730-day recency, pressure labels and 1,000 shared whole-match bootstrap remain in force except for the explicit changes below. All earlier prediction gates remain failed historical results; no predictive model is promoted.

## Approved changes

- Main ordering uses leave-player-out empirical pressure peer means within family × year × innings × phase × pre-ball wicket band. Other players need 20 opportunities across three matches; no parent or cross-year fallback. All retained other players contribute, not just eligible candidates.
- Oriented runs/wickets differences use fixed development weighted outcome SDs and the 60/40 mix, with registered 50/50 and 70/30 outcome mixes as sensitivities. Workload weights reflect the player's observed supported pressure exposure. Use `n_eff/(n_eff+k)` shrinkage, with k=75 batting / 60 bowling.
- Reapply original pressure sample minima inside pressure-peer-supported cells and require at least 80% pressure retention by both event count and weighted mass, in addition to original level/source gates. Missing ordinary comparison does not block primary ranking.
- Recompute player means, leave-player-out peer means, workload weights, effective counts and shrinkage inside each shared whole-match draw. Freeze support, original eligibility and development scale constants. A positive own cell with no peer mass invalidates the draw. A zero-own-mass cell has zero workload weight. Repeated match copies contribute linearly to squared-weight sums.
- Require at least 95% finite draws and order by the 10th percentile, then point rating, supported pressure-match count and stable player ID. There are no nationality, role-balance, price or availability quotas.
- Supported descriptive change remains separate, with the original fixed-cell missing-group rule and paired-effective-count shrinkage. The 70/30 level/change default and 50/50 variant become conditional companion comparisons on an identical adequate cohort; neither orders the broad primary list. Do not fill absent change with zero or present the descriptive change as the former residual statistic.

The full algebra, scaling units, interpretation, bootstrap invalidation and final-window transfer policy are frozen in the decision document. Exact computational validation and provenance are required before the first development score run. Support availability does not validate the proposed index.

## Execution boundary

The current authorization activates development implementation and execution on verified 2023–2025 evidence only. Freeze numerical development scales before score output. Preserve all raw sources, exclusions and failed model gates. No predictive fits or parameter/partition search are included.

Before reserved evaluation, validate development feasibility (at least ten qualifying players per role), finite-draw reliability, same-cohort outcome-weight sensitivities, family-separated evidence, match/season influence and numerical/attribution contracts. Keep the declared ordering even if a sensitivity is more attractive. If a gate fails, report it without automatically changing the method.

The final match-date cutoff remains 1 November 2026 inclusive; 2022 contributes no scoring evidence. Reserved outcomes remain disabled for this development implementation. A separate final-window execution stage must consume the frozen scales and unchanged accepted method. Aggregate 2026 EDA was previously seen; it is not pristine unseen data.

## Interpretation and remaining evidence

The rating describes observed performance relative to contemporaneous retained peers in broad contexts. It is not a causal pressure effect, fully adjusted player ability, an outcome-free forecast or an IPL 2027 prediction. Target difficulty, exact remaining balls, venue and opposition strength remain incompletely measured. Family-specific results, roles, repeatability and counterexamples must accompany selection claims.

The Round 1 deliverable remains two ordered top-ten lists with matching evidence-backed methodology. Development ratings are not the final recommendations. Detailed player tables stay private and Git-ignored. See [progress.md](progress.md) for implemented/executed/validated status and the exact next task.
