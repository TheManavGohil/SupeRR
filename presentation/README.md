# Pressure Index submission deck

The 25-slide, widescreen presentation contains the frozen two top tens,
methodology, audit results, uncertainty, role-based RR options, close exclusions,
and supporting/adverse pressure examples for all twenty selected players.
Every player has a supplied RR concept portrait. Text, panels, tables and the
interval comparison are native editable PowerPoint objects; photos are embedded
originals with native crop viewports from the dashboard manifest.

## Deliverables

- [PowerPoint upload](../dashboard/public/reports/pressure-index-submission.pptx)
- [Matching PDF slide proof](../dashboard/public/reports/pressure-index-slides.pdf)
- [Existing detailed written report](../dashboard/public/reports/pressure-index-report.pdf)

The slide proof and PPTX are generated from one layout. The PDF is **not** a
render from PowerPoint or LibreOffice: those renderers were unavailable here.
Open the PPTX in the intended presentation application for a final visual check.
Arial is used without embedding proprietary font files. Supplied portraits are
AI-generated illustrative RR jersey concepts; this is disclosed in the slides.

## Replace the placeholder and regenerate

The current public URL is `https://your-dashboard.vercel.app`, visibly labelled
as a placeholder. Replace it after deployment, before the participant uploads
the file. There is no invented participant/team identity.

From the repository root, with Python 3.10+ and Arial installed:

```sh
rtk proxy python3 -m venv /tmp/rr-slides-venv
rtk proxy /tmp/rr-slides-venv/bin/pip install -r presentation/requirements.txt
rtk proxy /tmp/rr-slides-venv/bin/python presentation/build_deck.py --dashboard-url https://YOUR-PUBLIC-DOMAIN.vercel.app
```

The script reads `dashboard/content/generated/{players,release}.json` and
`dashboard/content/player-assets.json`; it never fits a model, changes ratings
or alters original photos. The system Arial path is defined near the start of
`build_deck.py` if regeneration on another operating system requires a change.

## Slide map

| Slides | Purpose |
| --- | --- |
| 1–3 | Recommendation, selection standard and evidence flow |
| 4–7 | Data trust, pressure, peer index, bootstrap and material limits |
| 8–9 | Exact batting and bowling top tens |
| 10–12 | Stability, recent evidence, boundary intervals and RR role options |
| 13–17 | All ten batting dossiers, two per slide |
| 18–22 | All ten bowling dossiers, two per slide |
| 23 | Distinctive choices and dashboard link |
| 24–25 | Technical rules, provenance, scope and source links |

Dossier case statistics are **pressure segments**, not complete innings/spells.
Opponent abbreviations are printed beside each example. Speaker notes retain
the complete source case records, dates, match IDs, context and editorial review.

## Verification

Generation checks every text box against measured Arial line widths/heights,
checks shape bounds, verifies both ranking tables and displayed scores against
the frozen export, requires all twenty portraits and notes on all slides, checks
ZIP integrity and the 50 MiB limit, and rejects private paths/localhost/draft
tokens in slide text. It writes a private validation record under
`reports/presentation_2026-11-18/` (ignored by Git).

The PDF proof was rendered to 25 PNG pages for visual inspection, including
individual inspection of the cover, both tables, the interval chart and dense
dossier slides. PDF text extraction is also checked for the twenty names and
matching rank/score strings. These are presentation checks, not new validation
of a predictive model or a claim of submission readiness. Exact dropdown mapping,
participant review, deployment and public-link checks remain pending.
