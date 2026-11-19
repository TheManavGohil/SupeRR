# Verified Round 1 submission format

Checked 14 November 2026 against the downloaded problem statement, the [official public competition metadata](https://unstop.com/api/public/competition/1792758), its publicly served submission client, and the user's logged-in form text/screenshots. This is a read-only check; no form was filled or submitted.

## Required fields

| Fields | Requirement |
| --- | --- |
| `Batsman 1` through `Batsman 10` | Ten mandatory selections in rank order, highest first. |
| `Bowler 1` through `Bowler 10` | Ten mandatory selections in rank order, highest first. |
| `Upload Your Report` | Mandatory file; accepted extensions are **pdf,pptx**. The client limit is **50 × 1024 × 1024 bytes** (52,428,800; displayed as 50 MB). |

The twenty player fields reference the same `/api/submission-dropdown-options` catalogue. The client displays and stores the option's `name`, rather than the analytical player ID. The brief prohibits repetition within each list and requires report/dropdown agreement. Do not infer auction availability or a batting/bowling eligibility filter from this shared catalogue.

The authenticated option labels still require evidence. The user screenshot verifies one selected label; the other nineteen remain pending in the private mapping register. The catalogue returns `Unauthenticated.` to a normal unauthenticated JSON request. Do not treat dataset labels, likely aliases or a shared endpoint as proof of exact dropdown labels.

## Optional fields and report content

| Field | Requirement |
| --- | --- |
| `Please upload your dashboard link (if any).` | Optional text; the user's live form displays a 500-character limit. |
| `Share Your Journey` | Optional link. The form supports YouTube, Instagram, X/Twitter, LinkedIn and Google Drive/Docs links. The brief states this does not affect evaluation. |

A dashboard link alone does not satisfy the required file field in the checked form, despite the general listing's broader wording. The approved current upload artifact is the regenerated aggregate-only **PDF**; the former PPTX and slide PDF are retired. A presentation rebuild is separate work. `.ppt` is absent from the Round 1 accepted-extension list. No Round 1 page/slide limit appears in the checked brief or schema. The separate `5-slider Detailed Submission` field belongs to **Round 2**, not Round 1.

The report must explain pressure, metrics/baselines/ratings, eligibility and context fairness, evidence for both ordered lists, consistency and limitations. The upload remark additionally asks how the selected players could strengthen Rajasthan Royals. Interpret that through supported cricket roles and disclose unmeasured availability; it does not authorize changing the frozen lists or inventing squad/auction assumptions.

## Dates and official rules

Round 1 closes **18 November 2026 at 11:59 PM IST** in the metadata checked on 14 November 2026. Registration closes **16 November 2026 at 11:59 PM IST**. Recheck the live form before the user submits.

The [official listing](https://api.unstop.com/hackathons/superr-selector-season-2-help-shape-rajasthan-royals-ipl-2027-auction-strategy-rajasthan-royals-1792758) permits AI assistance but requires the participant's own final insights, picks and recommendations; copied or wholly AI-generated submissions may be disqualified. The participant must review and own the final selection argument before submission. It also prohibits publication of the competition data pack and allows one submission per participant. The technical `allow_multiple_submissions` flag is not permission to disregard that written rule.

## Evidence and outstanding work

Detailed snapshots, source hashes, field IDs and exact-name mapping remain private in `reports/submission_verification_2026-11-14/`. The current official brief PDF is byte-identical to the original. The current archive changes extra-run quantities and a non-selected player's name labels; the original frozen inputs remain preserved. All 121,891 final retained events have extra totals agreeing with the revised archive. Two recorded batter-run differences remain covered by the existing verified repair; no ratings or source exclusions were changed during this check.

The old deck, slide proof and detailed PDF were withdrawn during the approved publication cleanup. The regenerated [aggregate-only PDF](dashboard/public/reports/pressure-index-report.pdf) is nine pages and 240,277 bytes; its download is enabled only when its manifest is verified. Source-fingerprint and byte-hash checks reject stale or changed reports. A future presentation rebuild is outside this cleanup.

Use the single [participant checklist](docs/SUBMISSION_CHECKLIST.md): nineteen labels still lack prior authenticated evidence, and all twenty final confirmation cells are intentionally blank. The participant must confirm the exact data-publication rule, decide on repository visibility if needed, review and own the analysis, and inspect the production site/PDF before submission. Technical checks and dated rule evidence do not complete these manual gates. No submission or organiser contact is included.
