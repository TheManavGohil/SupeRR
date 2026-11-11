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

Future steps are event-level score repair and coverage validation, pressure-definition validation, context-adjusted baselines, and the frozen chronological evaluation. The final ranking stage keeps 1,000 whole-match bootstrap replicates, about 20 upstream-model variants and the 70/30 versus 50/50 level/change comparison. The optional explorer is deferred. The organiser clarification is drafted and unsent.

Aggregate 2026 EDA has already been inspected. Keep 2026 reserved from model and threshold tuning, and describe this exposure honestly in the evaluation report.

The source data, generated artifacts, detailed data audit, and organiser clarification are private competition materials. They are excluded from version control by default. Running the pipeline overwrites its generated EDA artifacts; raw source files are fingerprinted and never edited.
