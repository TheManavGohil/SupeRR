# Publication cleanup record

The participant approved phases A–G on `main`, ordinary commits only, preserving frozen analysis. Current execution status is in [progress](progress.md). This file records publication decisions and verification limits; it is not a submission narrative.

## Fixed publication decisions

- Publish only the aggregate contract: 69 existing player-role entries and twenty unchanged selections. Remove all per-match cases and narrative opponents from generated content, routes and report.
- Remove all twenty player PNGs and the image manifest. Use one shared name-only initials tile; originals are archived outside the repository.
- Keep shared copy in `dashboard/content/copy.ts`. Generate numeric statements from JSON, qualify pressure share with numerator/denominator, and distinguish retained from peer-supported matches.
- Present the scope on overview, methodology and report. Late-over exposure is automatic under the pressure rule; a high rank still depends on outcomes, peers and uncertainty. The participant's suggested “rank high by design” wording was made precise to avoid implying automatic high scores.
- Regenerate the aggregate PDF; retain its source/byte freshness gates. Withdraw the old PPTX and slide PDF, with no deck rebuild here.
- Preserve noindex. It expresses the existing indexing preference, provides no access control and does not decide compliance with the publication rule.
- Move process/handoff records here. The ignored organiser clarification remains local, drafted only. Use one participant checklist with blank confirmations.

## Wording inventory and frozen exception

Explicit runs/wickets and level/change labels replace ambiguous shorthand in README, dashboard plan/copy, descriptive specification, historical supported/reference specifications, rating decision, player evidence plan, original implementation plan and process history. Executed outcomes use runs 50 : wickets 50 and runs 70 : wickets 30; primary is runs 60 : wickets 40. Conditional level 70 : change 30 and level 50 : change 50 remain withheld, not executed.

**Exception:** `FINAL_WINDOW_PROTOCOL.md` lines 25 and 28 retain their historical shorthand because that exact file is pinned by the frozen evaluation. Editing it would conflict with preserving the evaluation provenance. Its outcome mixes mean runs/wickets; its level/change companions are conditional and remain withheld. This is a documentation exception, not a scoring change.

Both recorded pressure percentages carry denominators in current and historical process notes: 43,029 of 121,891 final-window events, and 54,721 of 155,799 full-verified events. The complete recent gate sentence is shared across the application. Shreyas's 43 retained matches remain unchanged; the exported peer-supported count is 42.

## Checks and deployment distinction

Publication checks reject unknown nested fields, encoded prohibited records/opponents, retired wording/assets and stale PDFs. Copy checks reject hard-coded shared phrases outside the single source. Rendered numeric/copy bindings must exactly match their JSON or shared-copy source. Next's framework emergency shell is excluded only from numeric validation, not privacy scans.

The initial D file-count assumption passed locally but failed in Vercel. E replaces it by serving every required route during the build, keeping static scans as well. Both local and isolated Vercel-flag builds pass; the subsequent Vercel failure still requires its authenticated log. Do not claim a successful deployment based only on HTTP 200 from the stable URL: it can serve the older C release. The earlier `d-production` receipt is such a limited HTTP/privacy observation.

Local route receipts and 390/1440 screenshots are kept privately under `reports/publication_cleanup_2026-11-18/`. Four Python export tests independently reproduce frozen values; the archive receipt pins every analytical source/configuration and the final protocol. Technical checks do not fill participant confirmation cells.

Final local G results: all 76 routes, 10 delivered script assets, 22 removed-asset paths, the PDF hash and eight screenshots pass. Thirteen Node and nine browser tests, lint/format and a clean installation/deployment-style build pass. All 69 archived identities/ranks/P10s/retained counts and all 40 analytical baseline hashes remain equal. PDF extraction confirms the twenty names/P10s, privacy scan, exactly one authorship line and no localhost. The production verifier rejects the older live pages for missing numeric bindings, as intended. Production acceptance is incomplete until the current Vercel build succeeds and live checks pass.

## Retained risks and rollback

Earlier public commits and deployments retain the old images/records/artifacts. No history rewrite, force push or deployment-history deletion is authorized here. The participant decides on visibility after confirming the exact competition rule; current-tree cleanup does not erase previous copies.

An ordinary `git revert` on `main` is the mechanical rollback for a phase. Reverting A/B/E would republish retired content, so any rollback must preserve the aggregate boundary, image removal and clean PDF or withdraw the download. Prefer a forward correction when those conditions would be violated.

Exact dropdown labels, rule wording, participant ownership and final submission review stay open in the [participant checklist](../SUBMISSION_CHECKLIST.md). Nothing has been submitted or sent to organisers.
