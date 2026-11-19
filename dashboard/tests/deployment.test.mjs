import { test } from "node:test";
import assert from "node:assert/strict";
import { verifyRoute } from "../scripts/verify-deployment.mjs";
import { copy } from "../content/copy.ts";
import { read } from "../scripts/check-publication.mjs";

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
