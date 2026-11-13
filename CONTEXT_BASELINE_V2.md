# One focused amendment to historical expectations

This amendment implements the next task in [progress.md](progress.md). It changes the expectation model described in [supported method v1](SUPPORTED_METHOD.md), leaving its pressure definition, attribution, eligible populations, level/change weights and match-level uncertainty policy intact. The original configuration and failed baseline remain preserved.

## Cricket question

The annual peer baseline underpredicted scoring in several IPL phases, particularly second-innings powerplays. Crediting that unexplained difference to batters, or blaming bowlers for it, would be premature. One candidate will assess whether verified pre-ball scoring pace and chase demands, together with more recent historical evidence, provide a better reference.

The candidate uses family/innings/phase groups, exact innings progress and wickets, recent wickets, scoring pace before the ball, chase target and required runs per remaining ball. First-innings target fields are absent by design and become zero only for chase-specific predictors. Current delivery runs, extras, wickets, player identities, final results and pressure flags are forbidden predictors. The exact feature transforms are frozen in [context_baseline_v2.json](configs/context_baseline_v2.json).

## Fixed implementation

Use weighted ridge regression for run expectations and weighted logistic regression for wickets, with one fixed penalty of 100. Include group indicators and interactions with the continuous state features. Standardize using the corresponding training data only; disable features constant in training. Runs are floored at zero and wickets remain probabilities. Record floor/clipping rates, coefficient tables and convergence.

Train on complete earlier-year matches, with a 365-day expectation-model half-life relative to January 1 of the evaluation year. This changes how expectations learn from historical matches; player-rating recency stays at 730 days. No current-year outcomes enter model fitting or calibration. No additional library or parameter search is needed.

The three annual development bundles use the same eligible deliveries as the old baseline. All four targets share the candidate specification. This brings cumulative model bundles to 18; one reserved-evaluation bundle is available only after promotion, with one contingency remaining. Reproducibility reruns of an identical specification are not additional variants, but must not hide experiments with other settings.

## Acceptance and limitations

Apply the existing validation thresholds without modification. In addition, each target must have pooled primary loss no worse than the original default baseline. Report paired match-bootstrap differences, annual performance, subgroup and pressure-marginal calibration, and the change in alert counts. Preserve the full failed gate if any requirement fails. No second candidate, tuning loop or reserved-outcome analysis is authorized by this command.

Improved prediction is necessary but not sufficient to establish a fair final ranking. Conditioning on prior scoring can absorb value created earlier by the same batter; it estimates contribution given the current situation, not total innings value. A new scoring regime cannot be learned before it happens. Opposition strength and venue remain omitted. These are important selection limitations, not reasons to assume an alert can be ignored.

The 2023–2025 baseline findings informed this amendment. Describe its development results as an adaptive model revision, not an untouched validation result. Preserve 2026 for the separate model evaluation after a model and its development scales have passed the gate and been frozen.
