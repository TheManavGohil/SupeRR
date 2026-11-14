# Supported pressure comparisons, version 1

This amendment replaces the unsupported global change term in sections 9.5–9.6 of the original plan. It is frozen in [the executable configuration](configs/supported_method_v1.json) before model fitting or player scores. The earlier failed global-comparison gate remains part of the audit trail. This is a pre-model specification, not evidence that a model or ranking has passed validation.

Implementation status: the historical expectation baseline and [one contextual revision](CONTEXT_BASELINE_V2.md) have now been evaluated. Both fail the calibration promotion screen; neither is approved for final ratings. The contextual candidate amends expectation features and training recency only. Its results do not change the supported-change or ranking rules below. See [progress.md](progress.md) for the current decision and remaining work.

Latest expectation candidate: [the retrospective reference decision](RETROSPECTIVE_REFERENCE.md) specifies two whole-match partitions and contemporary peers, with an explicit internal budget amendment from 20 to 22 bundles. It is implemented and evaluated on development: peer support and loss benchmarks pass, but 68 separate-fold calibration alerts block promotion despite zero pooled alerts. Twenty bundles have now been used. For that candidate only, the new specification replaces the annual forecasting boundary below. Contribution, supported-change, eligibility and ranking rules here remain unchanged. No expectation candidate is approved for final scoring; 2026 outcomes remain reserved.

Initial observed development evidence is now implemented and reconciled. None of its eight batting / fifteen bowling sample-eligible supported-change entries reaches 95% finite bootstrap draws; this is descriptive support evidence, not a residual-model validation. [The rating decision](RATING_METHOD_DECISION.md) recommends a substantive descriptive amendment after those first tables and before full dossier polishing. That proposal is not activated and does not supersede this specification until accepted. Automatic predictive experimentation is stopped.

## What the two components mean

**Pressure level** measures a player's recency-weighted contribution against historical peer expectations on all verified pressure opportunities, including late overs. Peers in late overs can themselves be under pressure: estimating an expected outcome there does not require ordinary observations. This estimates performance relative to peers, not improvement caused by pressure.

**Supported change** compares the same player's pressure and ordinary residual contributions within family × year × innings × phase × pre-ball wicket-band cells. Both the peer population and the player must have observations in both groups. Peer cells require 20 opportunities and three distinct matches per group; player cells require ten opportunities and two matches per group. Support is computed separately for batting and bowling exposures and separately for each analysis window. Including year prevents ordinary evidence from a different season becoming the player's comparison.

For player `p`, let `q_pc` be the share of their recency-weighted supported pressure opportunities in cell `c`. Then:

```text
level_raw_p  = weighted_mean(contribution | player p, pressure)
change_raw_p = sum_c q_pc * (weighted_mean(contribution | p,c,pressure)
                           - weighted_mean(contribution | p,c,ordinary))
n_eff       = sum(weights)^2 / sum(weights^2)
n_pair      = 1 / sum_c q_pc^2 * (1/n_eff_pressure_pc + 1/n_eff_ordinary_pc)
```

The denominator in the last expression is the entire sum. Multiply level by `n_eff_pressure / (n_eff_pressure + k)` and change by `n_pair / (n_pair + k)`, where `k=75` for batting and `k=60` for bowling. These fixed regularizers equal one registered minimum pressure sample; they are not fitted empirical-Bayes parameters. Whole-match resampling, not opportunity independence, supplies uncertainty. Report raw and shrunk estimates together.

The default decision index remains `0.70*level + 0.30*change`; the registered variant remains `0.50*level + 0.50*change`, on exactly the same eligible players and resamples. The two components target different populations, disclosed on every evidence card. Unsupported change is missing, never zero. Level-only evidence has its own table and cannot silently enter a blended ranking. A strong late-over specialist without ordinary comparisons is an insufficient-comparison case, not a weak player.

## Eligibility before scores

Pressure level requires 300 total and 75 pressure batting opportunities, or 240 total and 60 pressure bowling opportunities, eight pressure matches and effective pressure sample size of at least 40. Ordinary opportunities are not required for a level estimate. This deliberately separates the old combined eligibility rule into level and change gates.

Supported change must independently satisfy the same pressure minimum, eight pressure matches and effective pressure sample of 40 **inside the supported cells**, plus 100 ordinary opportunities across five matches there. Its fraction of all pressure opportunities is always reported. The old 80% global-overlap gate is not relaxed: this amendment targets only supported contexts and makes no global change claim.

Source retention is measured in the same role and date window. Below 80% retention, diagnostics remain visible but an unqualified shortlist is blocked pending a documented coverage review. Never fill a ten-player list by relaxing thresholds after seeing names. Development, reserved-year diagnostics and final retrospective eligibility are separate outputs.

The one-year reserved exposure diagnostic applies the same multi-year minima and may produce no eligible blends. That does not prevent evaluation of expected-outcome predictions on reserved events, but it does prevent claiming a validated reserved-year player-change ranking without enough evidence.

## Chronology and model boundary

2022 is training warm-up only; it contributes no player residuals. For each of 2023, 2024, 2025 and 2026, train on complete verified matches strictly before that calendar year. All events from a match stay in the same partition. No same-day or future match can enter training. Evaluate development on 2023–2025; 2026 remains reserved from method selection. Prior aggregate 2026 EDA exposure is explicitly disclosed.

The first baseline will estimate four targets using hierarchically shrunk historical peer means. The hierarchy is family/innings/phase/wicket-band → family/innings/phase → family/innings → family → global. Every mean uses training outcomes only. Player IDs, current-ball extras/outcomes, current-ball legality, result, future batting order and the pressure label are excluded from predictors. Role exposure filters and target attribution are kept outside the feature matrix. More detailed score/target features and advanced ML are deferred until this transparent baseline has been validated.

For batting, use non-wide striker opportunities, bat runs and bowler-attributable striker dismissal. For bowling, use all attempts, bat runs plus wides plus no-balls, and bowler-credited wickets. Byes, leg-byes and penalties do not enter bowler concession. Run-outs are not charged to a striker who was not dismissed. These are analytical opportunity rates, not official economy/strike-rate claims.

The contribution mix stays 60/40 runs/wickets, with 50/50 and 70/30 registered sensitivities. Forecast evaluation scales come only from the corresponding training data; retrospective contributions share a frozen development out-of-time residual scale. Model-setting comparisons use development only. Five registered prior strengths across four chronological folds cap the budget at 20 fold/setting bundles, each producing all four target predictions. No hyperparameter search or advanced model is included in this milestone.

## Uncertainty and ranking gate

Use 1,000 complete-match resamples stratified by family/year, with the same draw for every player and both roles. Keep the original support set and eligibility fixed. Recompute exposure weights, weighted means and shrinkage in each draw. If any supported cell loses either group, mark that player's change/blend unavailable in that draw; do not change the comparison population by dropping that cell. Publish the finite-draw fraction and withhold a selection score below 95%. Otherwise use the 10th percentile as the selection score, with the pre-registered tie order.

Intervals are conditional on fitted expectations, support and eligibility. Registered model settings, best-match removal and year sensitivity address other instability separately. Global change remains prohibited. This amendment can permit a transparent level baseline and restricted-change diagnostics; it does not by itself approve final rankings or erase reconciliation/coverage exclusions.

## Implementation sequence

1. Freeze this version and its hash; export separate features, targets, identities and match folds.
2. Run outcome-independent support/eligibility preflight for development and final exposure windows; report attrition from dropping warm-up scoring evidence.
3. Fit the historical peer baseline on development folds, validate calibration/backoff and leakage, then inspect anonymous residual diagnostics.
4. Freeze model selection and development reference scales before reserved model evaluation.
5. Generate level/change evidence, conditional match-bootstrap intervals and registered sensitivities. Keep coverage and comparison failures visible before proposing final lists.
