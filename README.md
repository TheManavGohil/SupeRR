# RR pressure analysis

Private implementation for SupeRR Selector Season 2. The first milestone is complete: typed ingestion, score-independent pre-delivery states, EDA tables, player sample coverage, whole-match descriptive uncertainty, and an eight-page chart pack.

Read the [implementation plan](IMPLEMENTATION_PLAN.md). The EDA report, chart pack, detailed tables, and scoring reconciliation are generated locally and excluded from the public repository because they contain competition-derived results.

## Reproduce

Python 3.12 is used; exact dependencies are in `uv.lock`. In this workspace every shell command uses RTK.

```sh
rtk proxy uv --cache-dir /tmp/rr-uv-cache sync --frozen --python /usr/bin/python3
rtk proxy .venv/bin/python -m rr_pressure eda
rtk proxy .venv/bin/python -m unittest discover -s tests -v
```

The original standard-library audit remains runnable independently:

```sh
rtk proxy python3 scripts/reconcile_and_pressure.py
```

## Current artifacts

| Location | Contents |
|---|---|
| `reports/eda_2026-11-01/REPORT.md` | Interpretation, cohort definitions, caveats and figures. |
| `reports/eda_2026-11-01/EDA_CHARTS.pdf` | Eight standalone chart pages. |
| `reports/eda_2026-11-01/tables/` | Phase/innings/over patterns, outcome-based chase shares, player evidence and exclusions. |
| `reports/eda_2026-11-01/audit/` | Schemas/missingness, conflicting lineup keys, player aliases, feature contract and settings. |
| `data/processed/score_independent_states.parquet` | Every supplied event with typed columns, quality flags and accepted pre-event proxy states. |
| `data/processed/preball_features.parquet` | Allowlisted accepted pre-event features, separated from outcomes. |
| `data/processed/delivery_outcomes.parquet` | Recorded outcomes keyed by event ID. |
| `data/processed/player_match_metrics.parquet` | Player/match/context blocks for later uncertainty analysis. |
| `reports/eda_2026-11-01/manifest.json` | Input, code, config and output hashes, dependency versions and counts. |

The cutoff remains 1 November 2026 inclusive. The production EDA still uses the registered `late OR collapse` proxy, with exact score/target/required-rate fields null. A separate diagnostic pilot now produces verified scores and full rule pressure only for completely accepted matches. No player ratings or final rankings have been created.

## External reconciliation pilot

Run the scoring audit first, then freeze the diagnostic sample before downloading sources:

```sh
rtk proxy .venv/bin/python -m rr_pressure select-pilot
rtk proxy .venv/bin/python -m rr_pressure fetch-cricsheet
rtk proxy .venv/bin/python -m rr_pressure reconcile-pilot
```

The 20-match sample contains two matches per year/family (2022–2026, IPL/T20I), selected by scoring failure and risk/extras exposure. Unavailable matches are not replaced. Archives and player registers are downloaded once into ignored `data/external/cricsheet/`; cached hashes are verified on reuse. Source match dates after the cutoff are excluded. Snapshot retrieval after the cutoff is disclosed separately from match eligibility.

Read `reports/reconciliation_pilot_2026-11-01/REPORT.md` locally. It reports year/family availability, alignment, acceptance, extra quantities, pressure shares and unresolved cases. `candidate_corrections.csv` includes rejected proposals for diagnosis. Only `verified_corrections.parquet` and `verified_preball_states.parquet` contain completely accepted matches; they are isolated from production EDA outputs. Each correction has its raw event ID/source row, source member/hash and JSON pointer. Source inputs are never rewritten.

Match acceptance requires exact event order and participants, batting runs, known extra labels, wickets, complete innings and the correct result/terminal chase. Adjusted targets and unresolved discrepancies stay quarantined. The pilot is a stress sample, so its acceptance rate and pressure share are not population estimates. The next step is exception review and full-cohort coverage assessment before model fitting.

External data is provided by [Cricsheet](https://cricsheet.org/), using its [JSON format](https://cricsheet.org/format/json/) and [People Register](https://cricsheet.org/register/), under the [Open Data Commons Attribution License 1.0](https://opendatacommons.org/licenses/by/1-0/). Derived outputs add alignment decisions and provenance. See [coverage caveats](https://cricsheet.org/downloads/), including withheld Afghanistan matches. All downloaded data and derived competition artifacts remain excluded from this repository.

Next steps are to address material remaining coverage gaps, freeze a supported definition of performance change, then fit context baselines and run the chronological evaluation. The registered ranking design keeps 1,000 whole-match bootstrap replicates, about 20 upstream-model variants and the 70/30 versus 50/50 level/change comparison, subject to the support gate below. The optional explorer is deferred. The organiser clarification is drafted and unsent.

## Full coverage and pressure-comparison validation

```sh
rtk proxy .venv/bin/python -m rr_pressure reconcile-full
rtk proxy .venv/bin/python -m rr_pressure pressure-validate
rtk proxy .venv/bin/python -m unittest discover -s tests -q
```

Private reviewed exceptions live in `data/curated/reconciliation_reviews.json`: identity aliases with evidence links, specific event-field decisions tied to source hashes and original values, reviewed retired-hurt events, and exact-date match-ordinal convention differences. Keep that private input with the source data for exact reproduction. Without it, the code performs strict reconciliation with fewer accepted matches. It never guesses new corrections or edits supplied files.

Full-corpus matching evaluates exact and adjacent dates, but a shifted match needs a unique complete event/result match; both dates respect the cutoff. Every candidate is logged, and one external match cannot be counted twice. [The matching policy](configs/reconciliation_policy.json) and [pressure-support checks](configs/pressure_validation.json) are versioned separately from the unchanged pressure rule.

Local outputs:

| Location | Contents |
|---|---|
| `reports/full_reconciliation_2026-11-01/REPORT.md` | Every supplied match, year/family/competition retention, pilot dispositions and remaining exclusions. |
| `reports/full_reconciliation_2026-11-01/candidate_audit.csv` | All date candidates and individual alignment/result failures. |
| `reports/full_reconciliation_2026-11-01/verified_events.parquet` | Complete accepted matches with original values, adopted scores, provenance and pre-ball states. Contains outcomes; do not feed all columns into a model. |
| `reports/pressure_validation_2026-11-01/REPORT.md` | Pressure shares, context overlap, player coverage and development-only descriptive comparisons. |
| `reports/pressure_validation_2026-11-01/VALIDATION_CHARTS.pdf` | Standalone coverage and comparison-support figures. |
| `reports/pressure_validation_2026-11-01/model_gate.json` | Explicit readiness decision; no predictive model has been fitted. |

The global pressure-change ranking gate currently fails: all late-phase deliveries are labelled pressure, leaving no ordinary comparison in that phase. The 70/30 default and 50/50 variant remain registered but unexecuted. [Supported method v1](SUPPORTED_METHOD.md) now freezes context-adjusted pressure level separately from change on supported contexts, eligibility, combination and missing-evidence rules. Do not change pressure thresholds to improve particular players' results.

Uncertainty diagnostics use 1,000 whole-match resamples, not ball resampling. Raw and supported-context contrasts describe different populations; a third contrast reports the raw difference on the supported population. Context support is a descriptive condition and does not establish a causal pressure effect. All detailed reports, exception evidence and downloaded data remain ignored by Git.

Aggregate 2026 EDA has already been inspected. Keep 2026 reserved from model and threshold tuning, and describe this exposure honestly in the evaluation report.

## Frozen supported-context method

```sh
rtk proxy .venv/bin/python -m rr_pressure prepare-method
rtk proxy .venv/bin/python -m unittest discover -s tests -q
```

This preflight fits no model and computes no player performance scores. The [versioned configuration](configs/supported_method_v1.json) is frozen before the new eligibility diagnostics. It splits all-pressure level from same-player, same-year supported-context change; missing change remains null and cannot enter either blend. The old failed global-change gate stays intact.

`reports/supported_method_2026-11-01/` contains the local report, frozen configuration, source/config/output hashes, model gate, exposure windows, player support tables, and match fold membership. `features.parquet` contains only the event join key and four allowlisted context predictors. Outcomes live in `targets.parquet`; player identities, pressure labels and role filters live in `identities_and_exposures.parquet`. Never feed those latter tables wholesale into a predictor. The exported 2026 targets are not analyzed by this command.

2022 supplies training warm-up only; scoring evidence begins in 2023. Train each annual fold on complete earlier-year matches. Development, reserved-year exposure and final retrospective exposure are audited separately. Both the population and the player need ordinary and pressure observations within the comparison cell. Under-80% source retention blocks an unqualified shortlist; insufficient comparisons do not imply poor performance.

The next implementation is the registered historical peer baseline on development folds, followed by residual/calibration checks and a frozen model choice before reserved evaluation. The live preflight does not execute the component estimators; those are checked using synthetic contributions. They preserve a fixed support population during match resampling and withhold selection scores when too many draws lack comparison groups. Further dependencies are model validation, the complete bootstrap/ranking runner, sensitivity analysis and evidence review.

The source data, generated artifacts, detailed data audit, and organiser clarification are private competition materials. They are excluded from version control by default. Running the pipeline overwrites its generated EDA artifacts; raw source files are fingerprinted and never edited.
