import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const players = JSON.parse(
  fs.readFileSync(
    new URL("../content/generated/players.json", import.meta.url),
  ),
);
const release = JSON.parse(
  fs.readFileSync(
    new URL("../content/generated/release.json", import.meta.url),
  ),
);
test("published ranking order matches the frozen two lists", () => {
  const expected = {
    batting: [
      "6396",
      "1699",
      "3125",
      "2756",
      "23311",
      "1318",
      "6726",
      "7897",
      "3647",
      "4391",
    ],
    bowling: [
      "781",
      "2933",
      "4373",
      "5837",
      "6354",
      "35318",
      "6256",
      "7327",
      "6284",
      "23",
    ],
  };
  for (const role of Object.keys(expected))
    assert.deepEqual(
      players
        .filter((p) => p.role === role && p.selected)
        .sort((a, b) => a.rank - b.rank)
        .map((p) => p.id),
      expected[role],
    );
});
test("missing recent evidence remains unavailable rather than zero rating", () => {
  for (const id of ["1318", "23"])
    assert.equal(
      players.find((p) => p.selected && p.id === id).recent.status,
      "no_retained_pressure",
    );
});
test("uncertainty ordering and alternatives retain factual evidence", () => {
  for (const role of ["batting", "bowling"]) {
    const list = players
      .filter((p) => p.role === role && p.selected)
      .sort((a, b) => a.rank - b.rank);
    for (let i = 1; i < list.length; i++)
      assert(list[i - 1].rating.low >= list[i].rating.low);
  }
});
test("unreliable ordinary change is not promoted to a ranking", () => {
  for (const p of players) assert(p.eligibility.primary);
  assert.equal(release.bootstrapDraws, 1000);
  assert.equal(release.selectedRecentAdequate, 7);
});
