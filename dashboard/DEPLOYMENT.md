# Run and deploy The Pressure Index

The app is implemented in `dashboard/` and builds independently of the private Python workspace. It presents the frozen 2023–1 November 2026 analysis; it does not fetch live cricket data or recompute scores.

## Local production preview

Use Node **22.x** (the repository was built on 22.23.2):

```sh
cd dashboard
npm ci
npm run build
npm start
```

Open `http://localhost:3000`. For development use `npm run dev`. Local workspace shell instructions add `rtk proxy` before these commands.

## Vercel

1. Import the GitHub repository into Vercel.
2. Set **Root Directory** to `dashboard` and framework to **Next.js**.
3. Install command: `npm ci`. Build command: `npm run build`. Keep the standard Next.js output configuration.
4. Use Node 22.x. No application secrets, Python runtime, database or external API keys are required.
5. Deploy, then check `/`, both `/rankings/` pages, a player deep link, `/compare`, `/methodology`, `/validation`, `/report` and the PDF download.
6. Ensure the production URL opens for a logged-out judge without a Vercel authentication challenge. Use the stable production URL in Unstop's optional dashboard field (500 characters).

The original data pack, full ledgers and private reports are excluded from Git/deployment. Curated generated data contains only aggregate findings required for this presentation. All browser-delivered content is public. Root `.vercelignore` also excludes private workspace material if a CLI deployment is used from the repository root; the recommended Vercel project root is still `dashboard/`.

Dependency audit, 18 November 2026: `npm audit --omit=dev` reports zero production advisories. The full development tree reports 14 high findings propagated from the unpatched [picomatch advisory](https://github.com/advisories/GHSA-fc5q-39xc-vjpf) in lint/glob tooling. The affected tooling processes trusted repository patterns and is not used by a dashboard route or runtime API. There is no published patched release in the checked advisory; no speculative override or forced framework downgrade is applied. Recheck the development tooling when a fix is published. These findings are recorded separately from production exposure.

## Player tiles

Every player uses the shared `PlayerInitials` component driven only by the display name. Original photos and the retired slide artifacts are archived outside the repository. Do not add player-image assets or an image manifest.

## PDF companion

The checked report is `public/reports/pressure-index-report.pdf`; its source is `/report`. Unstop requires the file upload even when a dashboard link is provided.

With the local production server running:

```sh
npm run report:pdf
```

This uses the installed Chrome browser or Playwright Chromium. Set `CHROME_PATH` if needed, or install the browser with `npx playwright install chromium`.

After the public URL exists, regenerate from the same local report with public deep links:

```sh
PUBLIC_DASHBOARD_URL=https://your-project.vercel.app npm run report:pdf
```

The default renderer removes local navigation links so the PDF never embeds localhost as a judge-facing destination. External source-attribution links remain. Update the PDF asset in Git and redeploy if it changes. Keep the frozen ranks and release ID identical.

## Checks

```sh
npm run check:content
npm test
npm run typecheck
npm run lint
npm run build
# Start production server in another terminal before browser checks:
npm run test:browser
```

Browser tests use installed Chrome when available, otherwise Playwright Chromium. They cover all 69 profile routes, filters, fixed ranks, compare input handling, mobile overflow, keyboard navigation, report parity and automated accessibility. `npm test` checks the curated publication contracts independently of the UI. The Python workspace additionally tests export parity against the private frozen artifacts.

The read-only data export can be reproduced from the private workspace via `.venv/bin/python scripts/export_dashboard.py`. This verifies source hashes and writes `content/generated/`; Vercel never runs it and needs no access to private artifacts. Changes to editorial text must retain factual denominators and do not authorize rerating players.

## Submission checks still requiring the participant

- Verify the remaining nineteen exact Unstop option labels. The original source labels remain in the app; no speculative aliases are substituted.
- Review and own the final analytical argument. The competition permits AI assistance but requires the participant's own final insights and recommendations.
- Recheck current deadline/form, populate the exact two lists, upload the PDF and enter the stable URL. Deployment and Unstop submission are performed by the user.

The aggregate-only dashboard and shared initials tiles are implemented; final dropdown evidence, production URL and participant review are tracked separately in `progress.md`.
