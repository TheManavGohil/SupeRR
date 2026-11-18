import { checkReport } from "./report-state.mjs";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { checkPublication, read, root } from "./check-publication.mjs";
checkPublication({ phase: process.argv.includes("--phase-a") ? "a" : "final" });
const players = read("content/generated/players.json"),
  release = read("content/generated/release.json"),
  report = read("content/generated/report.json");
assert.equal(players.length, 69);
assert.equal(new Set(players.map((p) => `${p.role}:${p.id}`)).size, 69);
for (const role of ["batting", "bowling"]) {
  const list = players
    .filter((p) => p.selected && p.role === role)
    .sort((a, b) => a.rank - b.rank);
  assert.deepEqual(
    list.map((p) => p.rank),
    Array.from({ length: 10 }, (_, i) => i + 1),
  );
  assert(list.every((p) => p.eligibility.primary));
  for (let i = 1; i < list.length; i++)
    assert(list[i - 1].rating.low >= list[i].rating.low);
}
for (const [status, total] of [
  ["adequate", 7],
  ["limited", 11],
  ["no_retained_pressure", 2],
])
  assert.equal(
    players.filter((p) => p.selected && p.recent.status === status).length,
    total,
  );
assert.equal(release.cutoff, "2026-11-01");
assert.equal(release.events, 121891);
assert.equal(release.pressureEvents, 43029);
assert.equal(release.verifiedEvents, 155799);
assert.equal(release.verifiedPressureEvents, 54721);
const pdf = path.join(root, "public/reports/pressure-index-report.pdf");
assert.equal(fs.existsSync(pdf), report.available);
console.log(
  "Content checks passed: frozen top tens, strict aggregate contract and complete recent-status counts.",
);

checkReport();
