import { test } from "node:test";
import assert from "node:assert/strict";
import {
  inspectPlayer,
  inspectText,
  read,
  checkPublication,
} from "../scripts/check-publication.mjs";
import { duplicatedCopy, checkCopy } from "../scripts/check-copy.mjs";
import { validateDocument } from "../scripts/check-built-content.mjs";
import { publicText } from "../lib/public-numbers.ts";
import { copy } from "../content/copy.ts";
test("public contract rejects unknown and nested match records", () => {
  const p = structuredClone(read("content/generated/players.json")[0]);
  assert.throws(() => inspectPlayer({ ...p, cases: [] }));
  assert.throws(() =>
    inspectPlayer({ ...p, exposure: { ...p.exposure, match_id: 123 } }),
  );
});
test("publication gate rejects encoded fields, case opponents and retired wording", () => {
  for (const bad of [
    "match_id",
    String.raw`match\u005fdate`,
    ...read("tests/fixtures/prohibited-public-terms.json"),
    "PLACEHOLDER",
    "AI-generated",
    "concept portrait",
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
