import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import ignore from "ignore";
import { verifyRoute } from "../scripts/verify-deployment.mjs";
import { copy } from "../content/copy.ts";
import { read, root, walk } from "../scripts/check-publication.mjs";
import { reportInputs } from "../scripts/report-state.mjs";

test("deployment filters keep required sources and the PDF while excluding private outputs", () => {
  const pdf = "public/reports/pressure-index-report.pdf";
  // Reproduce the inherited rule that caused the deployment-only failure.
  assert(ignore().add("reports/").ignores(pdf));
  const project = ignore().add(
    fs.readFileSync(path.join(root, ".vercelignore"), "utf8"),
  );
  const repository = ignore().add(
    fs.readFileSync(path.resolve(root, "../.vercelignore"), "utf8"),
  );
  const required = new Set([
    pdf,
    "package.json",
    "package-lock.json",
    "next.config.ts",
    "tsconfig.json",
    ...reportInputs,
    ...["app", "components", "content", "lib", "scripts", "tests", "public"]
      .flatMap((dir) => walk(path.join(root, dir)))
      .map((file) => path.relative(root, file).split(path.sep).join("/")),
  ]);
  for (const file of required) {
    assert(
      !project.ignores(file),
      `Required dashboard input excluded: ${file}`,
    );
    assert(
      !repository.ignores(`dashboard/${file}`),
      `Required root deployment input excluded: ${file}`,
    );
  }
  for (const file of [
    ".next/server/app/index.html",
    "node_modules/next/package.json",
    "test-results/trace.zip",
    "playwright-report/index.html",
    ".env.local",
  ])
    assert(
      project.ignores(file),
      `Private/generated dashboard output included: ${file}`,
    );
  for (const file of [
    "reports/private.pdf",
    "data/private.json",
    "artifacts/private.json",
    "docs/process/progress.md",
  ])
    assert(repository.ignores(file), `Private root output included: ${file}`);
});

test("deployment verification rejects stale scope and wrong canonical URLs", () => {
  const site = read("content/generated/site.json");
  const route = "/methodology";
  const canonical = new URL(route, site.publicBaseUrl).href;
  const scope = [
    "scoreScopeTitle",
    "scoreScopeProduction",
    "scoreScopeRole",
    "scoreScopeAdjustment",
    "scoreScopeFuture",
  ]
    .map((key) => `<p data-copy-key="${key}">${copy[key]}</p>`)
    .join("");
  const html = `<link rel="canonical" href="${canonical}"><meta name="robots" content="noindex, nofollow">${scope}`;
  assert.doesNotThrow(() => verifyRoute(html, route, [], site.publicBaseUrl));
  assert.throws(() =>
    verifyRoute(html.replace(scope, ""), route, [], site.publicBaseUrl),
  );
  assert.throws(() =>
    verifyRoute(
      html.replace(canonical, site.publicBaseUrl),
      route,
      [],
      site.publicBaseUrl,
    ),
  );
  assert.throws(() =>
    verifyRoute(
      html.replace("noindex, nofollow", "index, follow"),
      route,
      [],
      site.publicBaseUrl,
    ),
  );
});
