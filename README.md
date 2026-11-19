# The Pressure Index

A Next.js dashboard and reproducible analytical pipeline for SupeRR Selector Season 2, Round 1. The deliverable is two ranked top-ten lists with an evidence-backed methodology for performance under pressure.

[Dashboard](https://supe-rr-manav.vercel.app) · [Submission checklist](docs/SUBMISSION_CHECKLIST.md) · [Run and deploy](dashboard/DEPLOYMENT.md)

## Method and scope

The approved [descriptive method](DESCRIPTIVE_METHOD_V2.md) orders observed pressure production against supported other-player outcomes, using frozen development scales and 1,000 whole-match bootstrap resamples. The scoring window ends on **1 November 2026**. The [final evaluation protocol](FINAL_WINDOW_PROTOCOL.md) was committed before reserved performance access; ranks, scores, counts and analytical configurations remain frozen.

The primary outcome mix is **runs 60 : wickets 40**. Executed sensitivities are **runs 50 : wickets 50** and **runs 70 : wickets 30**. Conditional **level 70 : change 30 (withheld, not executed)** and **level 50 : change 50 (withheld, not executed)** require reliable usual-performance comparisons, which are absent. Failed predictive reference models remain documented and are not used for selection.

The index is descriptive. It does not establish improvement over usual performance, fully adjusted ability, auction availability or an IPL 2027 forecast. Every late-over delivery is pressure by rule; role context and uncertainty matter alongside rank. Seven selections pass every standalone 2026 gate; eleven are limited; two have none retained.

## Published content

The public app contains 69 aggregate player-role profiles: names, ranks, P10 scores, retained/peer-supported match counts, pressure opportunities, recent-evidence labels, role labels and eligibility. It contains no match-level cases or player photos. A shared initials tile uses only the display name. Raw competition files, reconciliation ledgers and detailed analytical reports remain private and ignored by Git.

The [aggregate-only PDF](dashboard/public/reports/pressure-index-report.pdf) matches the report page and carries public deep links. Hash and source-fingerprint checks reject a changed or stale PDF. The old PPTX and slide PDF are retired; rebuilding the presentation is separate work. Existing Git history and earlier deployments are retained; removing files from the current tree does not erase them.

The participant must confirm the competition's exact publication rule and decide whether the remaining public material is permitted. `noindex` is retained for search engines and does not restrict access.

## Run and validate

Use Node 22.x in `dashboard/`:

```sh
rtk proxy npm ci
rtk proxy npm test
rtk proxy npm run build
rtk proxy npm run start -- --port 3100
```

With the production preview running, use a second terminal in `dashboard/`:

```sh
rtk proxy env DASHBOARD_URL=http://127.0.0.1:3100 npm run test:browser
```

Build checks enforce the public field contract, shared copy, numeric provenance, privacy and PDF freshness. See the [deployment guide](dashboard/DEPLOYMENT.md) for Vercel, report regeneration and route/screenshot verification.

The Python workspace uses Python 3.12 and pinned `uv.lock` dependencies. Source datasets and private review inputs are required for analytical reproduction; they are deliberately not shipped. The publication exporter has independent parity checks:

```sh
rtk proxy .venv/bin/python -m unittest discover -s tests -p test_dashboard_export.py -v
```

External reconciliation uses [Cricsheet](https://cricsheet.org/) and its [People Register](https://cricsheet.org/register/), under the [Open Data Commons Attribution License 1.0](https://opendatacommons.org/licenses/by/1-0/). Source coverage and retained-data limitations are disclosed in the dashboard and method documents.

## Authorship and AI use

The pipeline, site and copy were built with AI coding assistance. Selections, interpretation and final review are the participant's responsibility. Technical tests do not substitute for that review.

- [ ] I have reviewed and own the final selection arguments and limitations.
- [ ] I have checked the competition's AI-use and publication rules.
- [ ] I have completed the [submission checklist](docs/SUBMISSION_CHECKLIST.md), including dropdown names and the uploaded report.

## Project records

Agents and contributors should read [working instructions](docs/process/AGENTS.md) and [current progress](docs/process/progress.md) before substantive work. Historical milestones and internal handoff notes live under `docs/process/`. The [original implementation plan](IMPLEMENTATION_PLAN.md) is historical where superseded by the approved descriptive specification.
