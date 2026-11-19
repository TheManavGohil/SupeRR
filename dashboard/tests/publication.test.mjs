import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {
  inspectPlayer,
  inspectText,
  read,
  checkPublication,
  inspectImageAsset,
  root,
} from "../scripts/check-publication.mjs";
import { duplicatedCopy, checkCopy } from "../scripts/check-copy.mjs";
import { validateDocument } from "../scripts/check-built-content.mjs";
import { publicText } from "../lib/public-numbers.ts";
import { copy } from "../content/copy.ts";
import { validateReportState, sha256 } from "../scripts/report-state.mjs";

test("report gate rejects stale sources and changed PDF bytes", () => {
  const bytes = Buffer.from("%PDF-verified-test-fixture");
  const manifest = {
    available: true,
    bytes: bytes.length,
    sha256: sha256(bytes),
    sourceFingerprint: "current",
  };
  assert.doesNotThrow(() => validateReportState(manifest, bytes, "current"));
  assert.throws(() => validateReportState(manifest, bytes, "stale"));
  assert.throws(() =>
    validateReportState(
      manifest,
      Buffer.concat([bytes, Buffer.from("match_id")]),
      "current",
    ),
  );
});
test("public contract rejects unknown and nested match records", () => {
  const p = structuredClone(read("content/generated/players.json")[0]);
  assert.throws(() => inspectPlayer({ ...p, cases: [] }));
  assert.throws(() =>
    inspectPlayer({ ...p, exposure: { ...p.exposure, match_id: 123 } }),
  );
});
test("supplied image whitelist rejects wrong files and unsafe paths", () => {
  const asset = Object.values(read("content/player-assets.json"))[0];
  const bytes = fs.readFileSync(path.join(root, "public", asset.src));
  assert.doesNotThrow(() => inspectImageAsset(asset, bytes));
  assert.throws(() =>
    inspectImageAsset({ ...asset, src: "/player_image/../private.png" }, bytes),
  );
  assert.throws(() => inspectImageAsset({ ...asset, sha256: "wrong" }, bytes));
  assert.throws(() =>
    inspectImageAsset({ ...asset, crop: { ...asset.crop, height: 1 } }, bytes),
  );
  assert.doesNotThrow(() => inspectText(copy.portraitDisclosure));
});
test("publication gate rejects encoded fields, case opponents and retired downloads", () => {
  for (const bad of [
    "match_id",
    String.raw`match\u005fdate`,
    ...read("tests/fixtures/prohibited-public-terms.json"),
    "PLACEHOLDER",
    "Before uploading",
    "https://your-dashboard.vercel.app",
  ])
    assert.throws(() => inspectText(bad));
});
test("shared sentences cannot be hard-coded in another component", () => {
  assert.deepEqual(duplicatedCopy(`<p>${copy.scoreScopeProduction}</p>`), [
    copy.scoreScopeProduction,
  ]);
  assert.deepEqual(duplicatedCopy("<p>{copy.scoreScopeProduction}</p>"), []);
});
test("numeric provenance rejects invented and existing-but-unbound values", () => {
  assert.throws(() => validateDocument("<p>999999</p>"));
  assert.throws(() =>
    validateDocument(
      `<p>${read("content/generated/release.json").matches}</p>`,
    ),
  );
  assert.throws(() =>
    validateDocument('<span data-json-source="release.matches">999999</span>'),
  );
  assert.throws(() =>
    validateDocument('<button aria-label="Count 999999">Count</button>'),
  );
});
test("numeric provenance accepts exact JSON formatting and rejects wrong fields", () => {
  assert.doesNotThrow(() =>
    validateDocument(
      `<span data-json-source="players.batting.6396.rating.low" data-json-format="score">${publicText("players.batting.6396.rating.low", "score")}</span>`,
    ),
  );
  assert.throws(() =>
    validateDocument('<span data-json-source="release.events">511</span>'),
  );
});
test("copy binding rejects a share without its numerator and denominator", () => {
  assert.throws(() =>
    validateDocument('<p data-copy-key="pressureShare">35.30%</p>'),
  );
  assert.doesNotThrow(() =>
    validateDocument(
      `<p data-copy-key="pressureShare">${copy.pressureShare}</p>`,
    ),
  );
});
test("publication and shared-copy source gates pass", () => {
  assert.equal(checkPublication(), 69);
  assert(checkCopy() > 0);
});
