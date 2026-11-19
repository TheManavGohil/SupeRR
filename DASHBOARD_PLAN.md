# Dashboard architecture and publication contract

Implemented 17–18 November 2026; updated for the approved publication cleanup. Current status and next task: [process progress](docs/process/progress.md). This presentation layer does not change the approved analytical method or rerun evaluation.

## Judge journey

The overview introduces both frozen lists and their score scope. Batting and bowling rankings expose the exact top tens, retained exposure and recent-evidence labels. Player profiles explain the observed role, aggregate evidence, usual-comparison limits and the possible RR contribution supported by that role. Comparisons show the same aggregates for up to three entries in the same discipline. Methodology, validation and a matching printable report make the reasoning inspectable.

The index orders observed pressure production against supported peers. It does not establish pressure-versus-usual improvement, fully adjusted ability, 2027 availability or future form. These limits appear together on overview, methodology and report. Private detailed examples are available on request, subject to competition rules.

## Data boundary

`scripts/export_dashboard.py` is a read-only publication exporter. It verifies frozen analytical artifacts and emits an explicit aggregate contract for 69 existing player-role entries, including the twenty selections. Allowed player fields are identity/name, discipline, rank, selection, observed-role label, P10 score, retained and peer-supported match counts, pressure opportunities, recent status and eligibility. Unknown fields fail export/content checks.

The four generated JSON files contain players, release totals, site/method constants and report availability/hash metadata. No match-level cases, opponent narratives, source pointers, per-match splits or raw event data are published. The exporter tests compare against the private frozen source without recomputing scores.

## Application structure

| Concern | Implementation |
| --- | --- |
| Framework | Next.js App Router, TypeScript, React; Node 22.x; Vercel root `dashboard/`. |
| Routes | Overview, two rankings, comparison, methodology, validation, report and 69 static profiles. |
| Shared copy | `dashboard/content/copy.ts`; pages, components and PDF renderer import the same phrases. |
| Numeric provenance | Generated JSON bindings and validated shared copy; built HTML and served routes are checked. |
| Player presentation | `PlayerInitials`, driven only by display name, on overview/rankings/profiles. No player images. |
| Interaction | Search, fixed evidence filters, table/card view and URL-backed same-role comparison. |
| Visuals | White/blush RR-inspired palette, consistent initials tiles, clear typographic hierarchy and responsive spacing. |
| Publication checks | Exact nested field contract, encoded-text privacy scanning, shared-copy guard, numeric bindings and PDF freshness. |
| Accessibility | Keyboard and reduced-motion behavior, readable without JavaScript, automated WCAG A/AA checks and phone overflow checks. |

The primary contribution mix is runs 60 : wickets 40. Executed sensitivities are runs 50 : wickets 50 and runs 70 : wickets 30. Conditional level 70 : change 30 and level 50 : change 50 remain withheld, not executed. Missing usual-comparison evidence is unavailable, never a zero score.

## Report and deployment

The detailed PDF is rendered from the report route using the shared copy and aggregate tables. Public profile links use `https://supe-rr-manav.vercel.app`. The download stays hidden while withdrawn, and a source fingerprint plus byte hash prevents stale files from passing a build. Retired PPTX and slide PDF remain removed; rebuilding them is outside this plan.

Each publication milestone uses an ordinary commit on `main`. Build/content/browser checks, privacy scans, all-route HTTP checks and 390/1440 screenshots verify the change. A stable live URL can serve an older deployment, so final verification must establish the deployed commit and compare its published content/downloads to the current release. See the [deployment guide](dashboard/DEPLOYMENT.md).

## Manual completion

Exact dropdown names, current publication-rule wording, participant ownership and final submission review remain in the single [submission checklist](docs/SUBMISSION_CHECKLIST.md). Noindex is preserved and does not restrict public access. Earlier commits and deployments retain their old contents; current-tree cleanup does not erase history. No auction simulator, squad quotas, price assumptions, model search or Unstop submission is added.
