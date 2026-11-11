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

The cutoff remains 1 November 2026 inclusive. No corrected scores, full pressure ratings or final player rankings have been created. Exact score/target/required-rate fields remain null until their event-level inputs are verified. The current pressure proxy is the registered `late OR collapse` part of the baseline.

Future steps are event-level score repair and coverage validation, pressure-definition validation, context-adjusted baselines, and the frozen chronological evaluation. The final ranking stage keeps 1,000 whole-match bootstrap replicates, about 20 upstream-model variants and the 70/30 versus 50/50 level/change comparison. The optional explorer is deferred. The organiser clarification is drafted and unsent.

The source data, generated artifacts, detailed data audit, and organiser clarification are private competition materials. They are excluded from version control by default. Running the pipeline overwrites its generated EDA artifacts; raw source files are fingerprinted and never edited.
