# Rating decision after the first validated evidence tables

14 November 2026. Status: **user-approved amendment**. The user accepted this exact primary-ordering change with “yes, go ahead!” after the concrete recommendation was presented. [DESCRIPTIVE_METHOD_V2.md](DESCRIPTIVE_METHOD_V2.md) and [the activated development configuration](configs/descriptive_rating_v2.json) govern implementation. Approval does not imply that development validation has passed; see [progress.md](progress.md) for current execution status. The rationale and proposed algebra below are retained as the pre-execution specification.

## Decision and cricket question

Recommend **one descriptive peer-relative pressure-performance ordering for every qualifying player**, with supported usual-performance differences alongside it. Do not make availability of an ordinary comparison a requirement for the main list. Do not use any failed predictive reference for player credit.

The selection question becomes: **how much better or worse did the player perform than other observed players facing the same broad pressure context, and how repeatable was that evidence?** A death specialist can answer that question through other death-over players even when no ordinary death-over observations exist. Whether the player improved relative to their usual performance remains a separate, explicitly restricted question.

This is a retrospective description of the retained corpus. It does not estimate an individual causal pressure effect, forecast IPL 2027, establish equal IPL/T20I opposition strength, or demonstrate that earlier models passed calibration. The empirical peer mean below is still an estimated benchmark; its sampling uncertainty must be recomputed in the match bootstrap. Merely renaming a failed prediction model would not resolve the problem.

## Evidence supporting the decision

The development-only execution uses 402 matches / 95,945 verified deliveries in 2023–2025. Saved targets independently reproduce verified event attribution. Per-player counts, pressure/support membership and weighted exposure sums reproduce the existing frozen preflight. The first execution followed contract commit `1dfb4e7`; later regeneration adds annotation and exposure-only decision audits, not a different scoring candidate.

| Development evidence | Batting | Bowling |
| --- | ---: | ---: |
| Level sample eligible | 73 | 122 |
| Level sample + source retention at least 80% | 62 | 90 |
| Supported-change sample eligible | 8 | 15 |
| Supported-change sample + source retention at least 80% | 6 | 12 |
| Eligible pressure-rate intervals passing the 95% finite-draw rule | 73 / 73 | 122 / 122 |
| Eligible supported-change intervals passing that rule | **0 / 8** | **0 / 15** |
| Supported-change finite-draw fraction: minimum / median / maximum | 53.0% / 59.8% / 74.5% | 45.6% / 59.6% / 79.7% |
| Median share of pressure events with supported ordinary comparisons, among level-eligible entries | 15.08% | 5.47% |
| Level-eligible entries with no supported ordinary pressure comparisons | 9 | 52 |

These are observed-rate uncertainty results, not residual-rating results. The absence of reliable change intervals is a separate sample-support barrier: fixed supported cells frequently lose one comparison group under whole-match resampling. Changing a reference model cannot create those missing match groups. Do not drop invalid draws, remove cells selectively, or relax the 95% rule to obtain ten names.

These findings apply to development. They do not establish that the combined 2023–2026 change intervals will fail; that analysis has not been performed. The method decision must be made before seeing those reserved outcomes.

Raw pressure rates also differ materially by cricket situation. For example, pooled IPL batting pressure outcomes are 123.87 runs and 3.54 attributed dismissals per 100 middle-over opportunities, versus 169.77 runs and 7.54 dismissals at the death. Thus a plain pooled run-rate ranking would reward a different workload and conceal the dismissal tradeoff. These aggregate differences are descriptive, not effects caused by the phase.

An outcome-free feasibility audit excludes every event of the evaluated player from their same-context pressure peer population and requires 20 peer opportunities across three matches. **Every pressure opportunity of all 62 batting / 90 bowling level-plus-coverage entries has that peer support in development.** This establishes availability only; no peer means, composite ratings, ordering or bootstrap reliability for the proposed index have been evaluated. Ten final selections are not guaranteed by these counts.

Reproducible private evidence: `reports/player_evidence_development_2026-11-01/validation.json`, `decision_evidence_summary.json`, `observed_uncertainty.parquet`, `pressure_peer_support.csv` and the manifest. No named performance ordering was inspected to choose this recommendation.

## Exact proposed primary rating

### Contexts, opportunities and comparison population

Keep the frozen pressure rule and role denominators. Batting uses non-wide striker opportunities including no-balls, batter runs and bowler-attributable striker dismissals. Bowling uses all attempts, batter runs + wides + no-balls conceded, and bowler-credited wickets. Show other dismissals separately. Rates are analytical, not official economy or strike rate.

For each role separately, define a pressure comparison cell:

```text
competition family × calendar year × innings × phase × pre-ball wicket band
```

Only pressure opportunities enter this primary comparison. The peer population includes all other observed players with verified pressure opportunities in that cell, not just shortlisted or level-eligible players. Exclude **all** observations of the evaluated player in that role from the peer means and support counts. Weight peer and player observations with the unchanged 730-day half-life at the analysis reference date.

Use only cells with at least 20 other-player opportunities across at least three distinct matches. There is no fallback to another year, phase, broader context or predictive model. Freeze the player's supported pressure-cell set before resampling. Ordinary support is a different set and must not be conflated with this pressure-peer support.

These cells control only the measured dimensions above. They do not fully match target difficulty, recent wickets, venue, opposition strength or exact remaining balls. Report that limitation; the descriptor is "relative to observed peers in broad matching contexts", not "fully context-adjusted ability".

### Contribution scale and formula

Freeze two scale constants per role from **all verified 2023–2025 pressure opportunities**, using recency weights at 31 December 2025:

```text
s_runs    = max(weighted population SD of run outcome per opportunity, 0.05)
s_wickets = max(weighted population SD of attributed wicket outcome per opportunity, 0.01)
```

These are development outcome scales, not the unapproved residual scales of a failed model. Freeze their numerical values and hashes before any 2026 outcome access. Keep them fixed when resampling: intervals are conditional on these chosen normalization constants. Do not set them to make runs or wickets favour particular players.

Let `r_pc` and `d_pc` be the player's recency-weighted mean runs and wickets per opportunity in cell `c`. Let `r_other_pc`, `d_other_pc` be the corresponding leave-player-out peer means. The default cell contribution is:

```text
batting:  U_pc = 0.60 * (r_pc - r_other_pc) / s_runs
                - 0.40 * (d_pc - d_other_pc) / s_wickets

bowling:  U_pc = -0.60 * (r_pc - r_other_pc) / s_runs
                + 0.40 * (d_pc - d_other_pc) / s_wickets

q_pc      = player's recency-weighted pressure mass in c
            / their total mass in pressure-peer-supported cells
L_raw_p   = sum_c(q_pc * U_pc)
n_eff_p   = sum(w)^2 / sum(w^2), over those player opportunities
L_p       = L_raw_p * n_eff_p / (n_eff_p + k_role)
k_batting = 75; k_bowling = 60
```

Positive contribution means more favourable observed outcomes than the corresponding retained peer means under the declared run/wicket tradeoff. A weighted average over the player's own workload is intentional: the method measures performance in their observed task, not performance under an invented common role assignment. It does not prove that dominance over a weaker T20I opposition transfers to IPL. Report IPL and T20I results separately alongside the combined number.

Keep the registered 50/50 and 70/30 **run/wicket** mixes as sensitivity checks on the identical eligible cohort and shared draws. They are distinct from the level/change weight variants. No new mix is selected after viewing rankings.

### Eligibility and coverage

Retain the original source-retention threshold and level sample requirements. Also apply the pressure-event, pressure-match and effective-pressure minima **inside the pressure-peer-supported set**. Require at least 80% of both the player's pressure event count and recency-weighted pressure mass to remain in that set. The latter is a proposed evidence-coverage safeguard, not a pressure-label change.

Thus the primary list requires: original total exposure; source retention at least 80%; at least 75 batting / 60 bowling supported pressure opportunities; eight supported pressure matches; effective supported pressure count at least 40; pressure-peer retention at least 80% by count and weight; and sufficient finite bootstrap draws. Publish all attrition reasons. Coverage-limited or unsupported players keep diagnostic evidence; do not assign poor-performance scores or silently override their exclusions.

No ordinary observations are required for the primary pressure rating. Do not claim this gate has passed numerically just because the exposure-only feasibility audit passes. The proposed score and its uncertainty are unimplemented.

### Bootstrap and ordering

Use 1,000 shared complete-match draws stratified by family/year, seed 1729. Both innings and all player roles move together. Freeze eligibility, supported pressure cells and scale constants; recompute player means, **leave-player-out peer means**, workload weights, effective counts and shrinkage in every draw. Repeated match copies count linearly in `sum(w²)`, not as squared multiplicities.

If a draw contains positive own pressure mass in an originally supported cell but zero peer mass there, the player's rating is unavailable in that draw. Do not drop that cell or substitute a parent mean. An originally supported cell with zero own mass has zero workload weight in that resample; it is not an ordinary comparison that must retain both groups. If all own mass disappears, the rating is unavailable.

Require at least 95% finite draws. Otherwise withhold a primary selection score. For eligible players, order by the **10th percentile of `L_p`**, then point `L_p`, supported pressure-match count and ascending stable player ID. Publish raw/shrunk points, 10th–90th intervals, finite fraction and support retention. This is a conservative decision index, not a posterior probability of being the best player.

Recomputing descriptive aggregates in each bootstrap includes peer-benchmark sampling variation. It is not another setting/partition search or an assertion that the previous prediction models now pass validation. The original 20 predictive fit bundles and every failed gate remain unchanged.

## Usual performance and the 70/30–50/50 issue

Continue reporting the three existing views: all-pressure observed performance, all-ordinary observed performance as background, and supported same-player/year context comparisons. Preserve the original support minima, cell weighting, sample requirements and missing-group bootstrap rule. Change is never filled with zero.

For an optional descriptive companion index, orient and scale the supported observed run/wicket differences using the same declared outcome scales and 60/40 mix, then apply the original paired-effective-count shrinkage. Use each difference per opportunity (divide the initial-table differences per 100 by 100). If `D_runs` and `D_wickets` are the pressure-cell-weighted same-player pressure-minus-ordinary differences, use `0.60*D_runs/s_runs - 0.40*D_wickets/s_wickets` for batting, and its opposite for bowling. Multiply by `n_pair/(n_pair+k_role)`, with the original `n_pair = 1/sum_c(q_c²*(1/n_eff_pressure_c + 1/n_eff_ordinary_c))`. Call this `C_descriptive`; it is **not** the original residual-based change statistic. Recompute the cell weights and paired count in every draw, retaining the original missing-group invalidation rule. It remains unavailable for decision use below 95% finite draws.

Where both components and uncertainty are adequate, report `0.70*L + 0.30*C_descriptive` and `0.50*L + 0.50*C_descriptive` on the identical comparison-eligible cohort and shared draws. Do not order the broad primary list by either companion and do not compare its shortlist with a different eligibility cohort as a weight effect. In the current development evidence, none qualifies for a reliable supported-change interval, so no such companion ordering can be claimed.

**This amendment changes the original mandatory 70/30 level/change primary ranking into a pressure primary ranking plus conditional companion comparisons.** It also replaces predictive residual scales/expectations with an explicitly descriptive empirical comparison. The user's subsequent explicit approval activates these changes under version 2; the earlier timing instruction alone did not authorize them. [SUPPORTED_METHOD.md](SUPPORTED_METHOD.md), its original weights and all failed gates remain in the historical audit record.

## What remains before any score or reserved evaluation

1. **Completed:** the user explicitly accepted the amendment and its changed primary ordering. No further approval is needed for this accepted formula.
2. Version the active method/config and implement **this one fixed estimator**, not another family of predictive candidates. Verify hand-calculated scores, monotonic metric direction, leave-player-out benchmark isolation, shared resampling, peer-loss invalidation and denominator handling. Activation and focused numerical checks are complete; use progress for the subsequent execution status.
3. Execute development ratings once. Verify exposure/support, reference recomputation, finite-draw reliability and that at least ten candidates per role actually qualify. Publish limitations and cohort attrition. This is feasibility of a descriptive selection procedure, not predictive calibration or evidence of qualification.
4. Produce fixed run/wicket sensitivities, leave-one-match and leave-one-season influence, family-separated results and counterexamples. Keep the declared primary ordering even when a variant is more appealing. Sensitivity findings can qualify a selection claim; they do not authorize automatic retuning or reputation overrides.
5. Freeze development scales, code/config hashes and the final transfer/check protocol, then evaluate 2026 separately. Recompute the accepted same-year descriptive peers using 2026 outcomes as expressly retrospective evidence; never claim an outcome-free forecast. Prior aggregate 2026 EDA remains disclosed.
6. For the final 2023–1 November 2026 window, use the final reference date and unchanged half-life, formula, gates and ordering. Report 2026-only and combined-window evidence, exclusions and sensitivity. Do not change the method in response to reserved rankings.
7. Complete the full dossiers and review the two ordered lists against credible alternatives. Require a factual role rationale, repeatability, weaknesses and adverse evidence for each selection. Exact source ID-to-dropdown mapping remains a packaging requirement.

If fewer than ten valid candidates remain in either development or final evidence, report that failure and the precise reason; do not fill places by relaxing rules or silently switching back to a failed model. This procedure offers an explicit route to the two lists, not a guarantee that the data support ten unqualified claims.

## Checkpoint disposition

Completed: initial development tables and descriptive uncertainty; aggregate decision evidence; outcome-free pressure-peer availability audit; concrete recommendation before full dossier polishing; explicit user approval; active versioned specification and fixed estimator implementation with focused numerical checks.

Pending at the activation checkpoint: complete development execution and empirical peer-inclusive uncertainty validation; numerical scale freeze; reserved evaluation; full dossiers; final selections and methodology. See progress for later completed checks. No final player ability claims follow from the initial tables alone.
