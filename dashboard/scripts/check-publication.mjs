import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
export const root = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
export const read = (name) =>
  JSON.parse(fs.readFileSync(path.join(root, name), "utf8"));
const contract = read("content/public-contract.json");
const terms = read("tests/fixtures/prohibited-public-terms.json");
const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const opponent = new RegExp(`\\b(?:${terms.map(escape).join("|")})\\b`, "i");
const forbidden =
  /\b(?:match_id|match_date|event_id|source_pointer|case_reasons|case_index)\b|your-dashboard\.vercel\.app|PLACEHOLDER|Before uploading/;
const retired = /AI-generated|concept portrait/;
export function decode(text) {
  return text
    .replace(/\\u([0-9a-f]{4})/gi, (_, n) =>
      String.fromCharCode(parseInt(n, 16)),
    )
    .replace(/\\x([0-9a-f]{2})/gi, (_, n) =>
      String.fromCharCode(parseInt(n, 16)),
    )
    .replace(/&#(?:x([0-9a-f]+)|(\d+));/gi, (_, h, d) =>
      String.fromCharCode(parseInt(h ?? d, h ? 16 : 10)),
    )
    .replace(/\\"/g, '"')
    .replace(
      /&(?:amp|quot|apos|lt|gt);/g,
      (s) =>
        ({
          "&amp;": "&",
          "&quot;": '"',
          "&apos;": "'",
          "&lt;": "<",
          "&gt;": ">",
        })[s],
    );
}
export function inspectText(text, label = "content", phase = "final") {
  const decoded = decode(text);
  assert(
    !forbidden.test(decoded),
    `Prohibited publication content in ${label}: ${decoded.match(forbidden)?.[0]}`,
  );
  assert(
    !opponent.test(decoded),
    `Case opponent in ${label}: ${decoded.match(opponent)?.[0]}`,
  );
  if (phase !== "a")
    assert(!retired.test(decoded), `Retired image wording in ${label}`);
}
export function inspectPlayer(p) {
  const exact = (obj, keys, label) =>
    assert.deepEqual(
      Object.keys(obj).sort(),
      [...keys].sort(),
      `Public key allowlist: ${label}`,
    );
  exact(p, contract.player, "player");
  for (const k of ["rating", "exposure", "recent", "eligibility"])
    exact(p[k], contract[k], k);
  assert.equal(typeof p.id, "string");
  assert.equal(typeof p.name, "string");
  assert.equal(typeof p.task, "string");
  assert(["batting", "bowling"].includes(p.role));
  assert(
    ["adequate", "limited", "no_retained_pressure"].includes(p.recent.status),
  );
  assert.equal(typeof p.selected, "boolean");
  assert.equal(typeof p.eligibility.primary, "boolean");
  assert(Number.isInteger(p.rank) && p.rank > 0);
  for (const n of [p.rating.low, ...Object.values(p.exposure)])
    assert(Number.isFinite(n));
  assert(Object.values(p.exposure).every((n) => Number.isInteger(n) && n >= 0));
  assert(p.exposure.peerSupportedMatches <= p.exposure.pressureMatches);
  inspectText(JSON.stringify(p), "player");
}
export function walk(dir) {
  return fs.existsSync(dir)
    ? fs
        .readdirSync(dir, { withFileTypes: true })
        .flatMap((e) =>
          e.isDirectory()
            ? walk(path.join(dir, e.name))
            : [path.join(dir, e.name)],
        )
    : [];
}
export function checkPublication({ built = false, phase = "final" } = {}) {
  const players = read("content/generated/players.json");
  players.forEach(inspectPlayer);
  const generated = walk(path.join(root, "content/generated"));
  assert.deepEqual(generated.map((f) => path.basename(f)).sort(), [
    "players.json",
    "release.json",
    "report.json",
    "site.json",
  ]);
  for (const f of generated) inspectText(fs.readFileSync(f, "utf8"), f, phase);
  if (phase !== "a") {
    assert(
      !fs.existsSync(path.join(root, "content/player-assets.json")),
      "Retired image manifest",
    );
    for (const f of walk(path.join(root, "public")))
      assert(
        !/\.(png|jpe?g|webp|avif)$/i.test(f),
        `Player raster asset forbidden: ${f}`,
      );
  }
  for (const f of walk(path.join(root, "public"))) {
    assert(
      !/\.(csv|parquet|zip|sql|env|pptx)$/i.test(f),
      `Private/retired public file: ${f}`,
    );
    if (/\.(json|txt|md|html|js|svg)$/i.test(f))
      inspectText(fs.readFileSync(f, "utf8"), f, phase);
  }
  if (built) {
    assert(
      fs.existsSync(path.join(root, ".next/BUILD_ID")),
      "Production build missing",
    );
    for (const dir of [".next/server/app", ".next/static/chunks"])
      for (const f of walk(path.join(root, dir)))
        if (/\.(html|rsc|js|json|txt)$/.test(f))
          inspectText(fs.readFileSync(f, "utf8"), f, phase);
  }
  return players.length;
}
if (process.argv[1] === fileURLToPath(import.meta.url))
  console.log(
    `Publication checks passed: ${checkPublication({ built: process.argv.includes("--built"), phase: process.argv.includes("--phase-a") ? "a" : "final" })} aggregate-only profiles.`,
  );
