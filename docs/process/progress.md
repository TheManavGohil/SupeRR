# Current project progress

Updated 19 November 2026 (IST). This is the current handoff. [Historical milestones](progress-history.md) are archived separately and contain superseded presentation states.

## Goal and frozen decisions

Round 1 needs two ordered top-ten lists plus an evidence-backed methodology. The [approved descriptive method](../../DESCRIPTIVE_METHOD_V2.md), [configuration](../../configs/descriptive_rating_v2.json) and [final-window protocol](../../FINAL_WINDOW_PROTOCOL.md) govern the completed analytical evaluation. The match-date cutoff is 1 November 2026 inclusive. Do not change analytical code/configuration, ranks, P10 values, retained counts, the pressure rule or the ordered lists during publication cleanup. No automatic model experiments, scoring reruns, submission or organiser contact are authorized by this work.

The method ranks observed pressure production against supported peers with 1,000 whole-match resamples. It does not estimate reliable pressure-versus-usual change or predict IPL 2027 performance. Primary outcome mix: runs 60 : wickets 40. Executed sensitivities: runs 50 : wickets 50 and runs 70 : wickets 30. Conditional level 70 : change 30 and level 50 : change 50 are withheld, not executed. Seven selections pass every standalone 2026 gate; eleven are limited; two have none retained.

Pressure is 35.30%: 43,029 of 121,891 final-window delivery events. The full verified corpus share is 35.12%: 54,721 of 155,799 events. Both exceed the diagnostic 20–30% range because the unchanged rule includes all late-over deliveries plus collapse/chase contexts. These thresholds were not tuned to players.

## Publication cleanup status

| Phase | Completed implementation and actual checks | Commit |
| --- | --- | --- |
| A: aggregate-only publication | Strict nested export contract; all 69 identities, ranks, scores and retained counts match frozen sources. Four independent Python export tests; production build, Node/browser checks and 76 local routes pass. | `dc0d43a` |
| B: initials tiles | Twenty PNGs, image manifest and portrait component removed; shared name-only tile across overview/rankings/profiles. Originals archived outside repo. Build, seven browser tests and 76 routes pass. | `4d9a5c5` |
| C: shared copy and labels | One copy source; explicit weights, denominators, recent evidence, retained/peer-supported labels and public canonicals. Export/build/Node/browser checks and 76 routes pass. | `f23bf82` |
| D: score scope and guards | Scope on overview/methodology/report; strict copy/numeric bindings; encoded privacy scans and deliberate-failure tests. Eleven Node/eight browser tests pass locally. Vercel failed on the checker's HTML-file-count assumption. | `b4de4ca` |
| E: clean PDF and route-check correction | Nine-page aggregate PDF, 240,277 bytes; source/byte fingerprint prevents stale downloads. Twelve Node and nine browser tests, 76 routes and page previews pass. Corrected checker serves all 76 routes in addition to static scans. Local and isolated `CI=1 VERCEL=1` builds pass. Vercel still reports failure; latest authenticated build log requested. | `85267fe` |
| F: repository hygiene | Process records moved here; README/deployment/architecture docs current; one blank participant checklist. All local links resolve; all twenty names/order match export. Four Python, twelve Node and nine browser tests pass; production build and all 76 local routes pass, with refreshed 390/1440 screenshots. All 40 analytical baseline hashes unchanged. | `b1f1ced` |
| G: final production verification | Portable verifier implemented; corrected missing profile canonicals. Thirteen Node/nine browser tests, lint/format, production build and clean install with `CI=1 VERCEL=1` build pass. Local verifier passes 76 routes, 10 scripts, 22 retired assets, PDF hash and eight screenshots; all 69 frozen identities/ranks/P10s/counts and 40 analytical hashes match. Production verifier correctly rejects older live content. Final Vercel success and production browser/route verification remain blocked on its latest build log. | This milestone; production incomplete |

A, B and C production statuses succeeded. D failed with the user-supplied `Expected all application HTML pages` error. E's new failure is not yet diagnosed; F also fails with the same unchanged application build script. E deployment is `GWhe3vGSnC4dbKyog9P2nM5Y6N2A`; F deployment is `A5FpLFGqeUbRToqrFa8EQ9XpBpc9`. Their logs require the participant's Vercel login. The stable production URL can still serve an older release. No final production success is claimed.

All local phase screenshots/route receipts are private under `reports/publication_cleanup_2026-11-18/`. D's earlier `d-production` route receipt only establishes privacy/HTTP behavior of an older release, not successful D deployment. The latest isolated clean-install/deployment-style build is `/tmp/rr-dashboard-clean-cqvn7y08` (temporary verification workspace). Final local receipts are under `reports/publication_cleanup_2026-11-18/g-local/`; production rejection receipts have `passed: false`.

## Artifacts and privacy

- Current app: [dashboard](../../dashboard/DEPLOYMENT.md); public base `https://supe-rr-manav.vercel.app`.
- Current upload: [aggregate-only PDF](../../dashboard/public/reports/pressure-index-report.pdf), linked only while its manifest validates. Sources are the report route, generated JSON and shared copy. Old PPTX and slide PDF remain removed; a future presentation rebuild is outside this cleanup.
- Current public contract: 69 aggregate player-role entries, no per-match records or player images. All browser-delivered content is public; `noindex` is not access control.
- Original assets and retired artifacts are archived outside the repository at `/home/manav/Documents/Projects/RR-private-archive/2026-11-18-publication-cleanup/`. Its receipt also pins every analytical source/configuration and the final protocol. Compare these again at the final milestone.
- Detailed analytical reports, review ledgers and reconciliation evidence remain local/ignored. The organiser clarification is a local ignored draft in this directory and has not been sent.
- Ordinary commits on `main` only. Commit/push at coherent milestones; no branches, history rewrite or force push. Earlier commits/deployments retain old records/assets; cleanup does not erase public history.

## Exact next work

1. Read the latest Vercel failure log when supplied. The first D count assumption has been corrected, but a distinct subsequent failure remains unknown. Do not guess another fix or weaken privacy/provenance gates.
2. Correct the deployment issue, run the affected checks, commit/push on `main`, and confirm Vercel success for that exact commit. The portable command is `rtk proxy npm run verify:deployment` in `dashboard/`; run the nine browser tests against the public URL as well. It verifies current content, not Git commit identity; both content and deployment status are required.
3. Inspect the final live 390/1440 screenshots and matching PDF, then record actual production results. Technical implementation is complete locally; production acceptance remains incomplete.
4. Keep participant gates in [one checklist](../SUBMISSION_CHECKLIST.md): nineteen dropdown labels lack earlier authenticated evidence, all twenty final confirmations remain blank; exact publication-rule wording/visibility decision, final authorship review, PDF and form review remain open. Recheck the live submission deadline and rules; dated November 14 evidence is not current permission to submit.

The final recommendation package is not submission-ready until those manual gates and production verification are complete. Technical implementation does not establish qualification.
