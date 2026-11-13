# Retrospective peer-reference decision

Decision recorded 13 November 2026, before fitting this candidate or computing player scores. Executable specification: [retrospective_reference_v1.json](configs/retrospective_reference_v1.json). Outcome-free feasibility command: `rtk proxy .venv/bin/python -m rr_pressure audit-reference`.

## Cricket question and decision

Did a batter or bowler deliver strong pressure performances relative to the scoring conditions faced by contemporary peers in the same phase and wicket state? A selector reviewing completed seasons needs that comparison. Predicting the following season's scoring environment is a different task. The competition brief requires retrospective pressure ratings; it does not require annual forecasts.

**Implement one fixed, same-season, two-fold peer reference for development evaluation next.** Divide complete matches into two partitions, fit on one and evaluate the other, then reverse. Every event receives an expectation from a model that saw neither innings of its match. This is an amendment to the expectation reference, not permission to rank players or a claim that either historical model passed. The original 29-alert and contextual 18-alert forecast gates remain failed and preserved.

Exact leave-one-match-out fitting would preserve more peer information, but entails 402 distinct development training sets per target. Computing means through subtraction would reduce execution time, not turn those into independent validation or make the statistical reference fits disappear. Reject that design under the small experiment budget. Two whole-match partitions give us held-out predictions for all development events using eight target-model fits in total.

## Evidence available before fitting

The audit opens only development exposure and context columns from the hashed preflight artifacts. It does not open targets, read player names or compute performance. All counts use verified 2023–2025 matches: 402 matches, 95,945 delivery events; batting uses 92,259 non-wide opportunities. No 2026 observations enter the audit.

At the finest year × family × innings × phase × wicket-band context, the reference needs at least 20 role opportunities in three other matches. These thresholds reuse the existing peer-support minima, without requiring an ordinary group for a level reference. The feasibility screen, specified before running the audit, requires 95% support in every year/family/role, separately for all and pressure opportunities, and same-year/family parent support for every opportunity.

| Reference scheme | Batting opportunities supported | Batting pressure supported | Bowling attempts supported | Bowling pressure supported |
| --- | ---: | ---: | ---: | ---: |
| Exclude evaluated match only — counts, not fits | 100% | 100% | 100% | 100% |
| Exclude evaluated half of matches — selected design | 99.59% | 99.12% | 99.59% | 99.12% |

The weakest year/family/role/exposure group has 95.83% support. All events have supported same-year/family parents. The screen passes. Finest-cell sparse events remain included and disclosed; hierarchical shrinkage supplies their reference. These counts do **not** show calibrated expectations, adequate individual-player comparisons, or causal identification. No support or pressure threshold was tuned to a player.

## Fixed procedure

1. Sort matches within each family/year by SHA256 of the fixed salt and match ID; alternate evaluation folds 0 and 1. The salt is `rr-retrospective-peers-v1`. Export and freeze the resulting assignment. Do not try another seed or balance folds using results, player identities or scores. Both innings remain together.
2. Each development training partition pools 2023–2025 and produces four target models. Use equal role-opportunity weights and the existing recursive mean formula `(sum + 200 * parent) / (count + 200)`. The root is the training-partition mean, followed by year, year/family, year/family/innings, year/family/innings/phase, then wicket band. Retain 200 prior events, with no new prior sweep. Unseen cells fall back; low-count cells shrink. Export support, shrinkage and fallback evidence.
3. Keep the established targets and role denominators. Never include player identities, pressure flag, current-ball outcomes, results or future tactical assignments as predictors. Year is deliberately permitted for this retrospective reference. Other development seasons can enter the root prior; the strongest reference is the same-year cell. All priors exclude the evaluated partition.
4. Validate each opposite partition without correcting its predictions using its outcomes. Retain the original loss metrics, 0.10-run/0.01-wicket material-bias tolerances, 500-event/ten-match diagnostic minima and 1,000 whole-match resamples. Compare against opposite-partition same-year global and same-year/family means. Require no worse pooled loss for each target, no worse annual global loss in at least two of three years, and no material calibration alerts in pooled or separately reported evaluation-fold screens. Sparse groups remain uncertain. Report pressure and ordinary marginal diagnostics without treating them as player-change estimates.
5. Compare with historical v1/v2 predictions on identical event/target cohorts. Those comparisons are diagnostics, not evidence that a retrospective model is a better match-date forecaster. Check run MSE/MAE, wicket Brier/log loss, calibration, unseen and sparse contexts, match concentration and fold imbalance. Do not reduce this decision to aggregate calibration alone: peer-reference centering can make aggregate bias small mechanically.
6. Only if development passes, freeze the four development residual SDs and model choice. Then run the identical two-fold procedure within 2026 up to **1 November 2026 inclusive**. Other-fold 2026 outcomes set reference means, but never the evaluated match's own expectation. This is **reserved-procedure retrospective cross-validation**, not an outcome-free forecast of 2026 and not a pristine holdout (prior EDA is already disclosed). Reserved outcomes never choose the method, partition, scale, weights or thresholds. Preserve any reserved failures; no automatic retuning or ranking approval.

For model-validation scale displays, use the corresponding training partition's outcome SD. Final contributions use the frozen development residual SDs with the existing floors. A mutation of every outcome in an evaluation partition must leave its predictions, training statistics and comparators unchanged. Development residual scales necessarily use development evaluation outcomes and are frozen only afterward; do not confuse those two contracts.

## Explicit budget amendment

The user requested **about 20** model-refit variants. Our earlier implementation imposed an internal maximum of 20 annual fold/setting bundles. Eighteen have been used. Two remaining bundles would cover development cross-fitting but leave no capacity for the required two reserved partitions. Increase that internal maximum to **22**, expressly for this one retrospective candidate:

| Stage | Four-target training/evaluation bundles | Cumulative |
| --- | ---: | ---: |
| Historical v1, five settings × three years | 15 | 15 |
| Contextual v2, one setting × three years | 3 | 18 |
| Retrospective development, two partitions pooled across three years | 2 | 20 |
| Reserved retrospective evaluation, two partitions | 2 | 22 |

A bundle still means one training set and one setting producing four target models. The new development models include year as a categorical hierarchy level; they are **not** six separate year-by-partition fits being relabelled as two. The maximum is 16 additional target-model fits, one prior strength, one salt, and no full-data refit. This audit spends zero bundles. If development fails, stop at 20 used; do not spend reserved fits searching for another model. The historical configurations remain unchanged as provenance; this new configuration records the amended future budget.

## Selection safeguards and practical limits

Match exclusion does not exclude the player's other matches. The benchmark measures conditional performance against the observed peer mix, not intrinsic talent or a causal pressure response. It does not adjust venue, opposition strength, tournament differences within T20Is, or precise within-season drift. Year and coarse wicket/phase cells cannot fully describe chase difficulty. These are checks for the next evaluation and limitations to retain on evidence cards, not reasons to invent adjustments.

The method still separates all-pressure level from supported same-player pressure-versus-ordinary change. The new reference does not supply ordinary death-over controls or enlarge the supported-change cohort by itself. Keep strong specialists visible in level-only evidence; do not fill missing change with zero or claim the narrower blended list identifies the ten best players overall without the specialist review.

Pressure labels, 730-day rating recency, warm-up exclusion, source-retention requirements, contribution weights, 70/30 and 50/50 level/change variants, eligibility, whole-match bootstrap and finite-draw gates remain unchanged. Bootstrap uncertainty is conditional on the fitted references and support; cross-fold training creates dependence not represented by treating delivery residuals as independent. No new bootstrap refitting is authorized here.

## Next implementation milestone

Implement the exact two-partition hierarchical reference and development runner. Test match/partition outcome isolation at every hierarchy level, missing cells, year boundaries, role exposure, numerical domains, frozen assignment, source hashes and budget accounting. Run the fixed development evaluation once and export losses, both fold screens, support/fallback tables, comparisons, candidate scales and a promotion gate. Only a passing gate permits the separately frozen reserved procedure. No player selection is authorized by a feasibility pass alone.
