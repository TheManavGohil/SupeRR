# Run and deploy The Pressure Index

The Next.js app in `dashboard/` builds from frozen player aggregates without the private Python workspace. It does not fetch live cricket data or recompute scores. The stable public base for canonicals and PDF links is `https://supe-rr-manav.vercel.app` in `content/generated/site.json`.

## Local production preview

Use Node **22.x**. Run these commands from `dashboard/`:

```sh
rtk proxy npm ci
rtk proxy npm test
rtk proxy npm run lint
rtk proxy npm run build
rtk proxy npm run start -- --port 3100
```

In another terminal, also in `dashboard/`:

```sh
rtk proxy env DASHBOARD_URL=http://127.0.0.1:3100 npm run test:browser
```

The build checks strict public keys, shared copy, PDF freshness and privacy, then validates numeric/copy provenance in static files and by serving every required route on a temporary local port. It does not assume a hosting adapter retains a particular number of HTML files.

## Vercel

1. Import the GitHub repository, using **Root Directory: `dashboard`**, **Framework: Next.js**, and **Node 22.x**.
2. Use install command `npm ci`, build command `npm run build` and the standard Next.js output configuration. No application secrets, Python runtime, database or API keys are needed.
3. Push an ordinary commit to `main` and check the Vercel status for that exact commit. A response from the stable URL alone can be an older deployment.
4. Verify all routes and download hashes against the committed aggregates. Test the production URL while logged out; judge access must not require Vercel login.

Run the portable verification command from `dashboard/`:

```sh
rtk proxy npm run verify:deployment
```

It checks all 76 routes against current copy and JSON bindings, profile identity/aggregates, scope, canonicals, noindex, delivered script privacy, all twenty removed PNGs, both retired slide files, and the PDF hash. A fresh browser context saves overview/rankings/profile screenshots at 390 and 1440 pixels under ignored `reports/`. A stale release fails even if its routes return HTTP 200. Check GitHub/Vercel success for the exact pushed commit separately; the content receipt alone does not prove the Git commit identity.

To run the same verification on a local preview:

```sh
rtk proxy env DASHBOARD_URL=http://127.0.0.1:3100 npm run verify:deployment
```

The recommended Git integration deploys only `dashboard/`. Its own `.vercelignore` excludes caches, browser-test outputs and environment files while keeping the verified public PDF. Vercel gives this project-level file precedence over the repository-level file. Root ignore rules use anchored paths for private workspace material and process notes; an unanchored `reports/` rule would also remove the public PDF. A regression check validates both policies against all required sources/assets. See [Vercel's ignore-file documentation](https://vercel.com/docs/deployments/vercel-ignore#monorepos).

All browser-delivered content is public. `noindex` remains enabled; it is not access control.

## Publication boundaries

Only the strict aggregate contract in `content/public-contract.json` is exported. Match-level cases, source pointers, raw ledgers and event data are excluded. One shared `PlayerInitials` tile receives only the display name. No player raster assets or image manifest are allowed. The original images and retired report/slide files were archived outside the repository before deletion.

The old PPTX and slide PDF must remain absent. Rebuilding the presentation is outside this cleanup. Previous Git history and deployments have not been erased.

## PDF companion

The approved upload artifact is `public/reports/pressure-index-report.pdf`, generated from `/report` and shared `content/copy.ts`. The report manifest records its byte hash and a fingerprint of the source files and fonts. A build fails if the report differs or its sources change. Report links use the stable public base.

After changing report inputs, withdraw the previous PDF before building a preview:

```sh
rtk proxy npm run report:withdraw
rtk proxy npm run build
rtk proxy npm run start -- --port 3100
```

With that matching production preview running, render from a second terminal:

```sh
rtk proxy env DASHBOARD_URL=http://127.0.0.1:3100 npm run report:pdf
```

Chrome is required locally; set `CHROME_PATH` for an installed browser if needed. The renderer validates the report page, creates a private candidate and publishes the PDF plus manifest. Inspect every PDF page, text, links, ordering and file size before committing. Rebuild to include the enabled download, restart the preview and rerun browser checks. Vercel builds verify the committed PDF; they do not need a browser to generate it.

When withdrawn, the download link is hidden. Do not copy an old PDF back or bypass fingerprint checks. Do not rerun the frozen analytical evaluation to change presentation content.

## Participant gates

Technical verification does not complete the participant's responsibilities. The single [submission checklist](../docs/SUBMISSION_CHECKLIST.md) contains all twenty exact site names with blank confirmation cells, the publication-rule decision, authorship review and final report/form checks. Current handoff and implementation history are under [docs/process](../docs/process/progress.md).
