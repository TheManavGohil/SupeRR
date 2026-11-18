import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const players = JSON.parse(
  fs.readFileSync(path.join(root, "content/generated/players.json")),
);
const release = JSON.parse(
  fs.readFileSync(path.join(root, "content/generated/release.json")),
);
const assets = JSON.parse(
  fs.readFileSync(path.join(root, "content/player-assets.json")),
);
assert.equal(players.length, 69);
assert.equal(new Set(players.map((p) => `${p.role}:${p.id}`)).size, 69);
for (const role of ["batting", "bowling"]) {
  const selected = players
    .filter((p) => p.role === role && p.selected)
    .sort((a, b) => a.rank - b.rank);
  assert.deepEqual(
    selected.map((p) => p.rank),
    Array.from({ length: 10 }, (_, i) => i + 1),
  );
  for (const p of selected) {
    assert(
      p.editorial?.why &&
        p.editorial?.caution &&
        p.editorial?.contribution &&
        p.editorial?.review,
    );
    assert(p.cases.length > 0 && p.cases.length <= 5);
    assert(p.rating.finiteFraction >= 0.95);
    assert.equal(
      p.rating.low,
      p.variants.find((v) => v.variant === "default_60_40").p10,
    );
    assert.equal(p.usual.reliable, false);
    assert.equal(p.variants.length, 3);
  }
}
assert.equal(
  players.filter((p) => p.selected && p.recent.status === "adequate").length,
  7,
);
assert.equal(
  players.filter(
    (p) => p.selected && p.recent.status === "no_retained_pressure",
  ).length,
  2,
);
assert.equal(release.matches, 511);
assert.equal(release.cutoff, "2026-11-01");
const forbiddenKeys = new Set([
  "event_id",
  "first_event_id",
  "source_pointer",
  "source_row",
  "source_member",
  "source_archive",
  "source_sha256",
  "delivery_ist_time",
  "innings_ball_num",
]);
function inspect(value) {
  if (Array.isArray(value)) return value.forEach(inspect);
  if (value && typeof value === "object")
    for (const [key, v] of Object.entries(value)) {
      assert(!forbiddenKeys.has(key), `Forbidden publication key: ${key}`);
      inspect(v);
    }
  if (typeof value === "number") assert(Number.isFinite(value));
  if (typeof value === "string")
    assert(
      !/\/home\/|\/tmp\/|\.parquet|(?:Bearer\s|AWS_SECRET_ACCESS_KEY)/.test(
        value,
      ),
      "Private path or credential-like content",
    );
}
inspect(players);
inspect(release);
for (const p of players) {
  assert.equal(typeof p.id, "string");
  for (const a of p.alternatives)
    assert(players.some((q) => q.id === a.id && q.role === p.role));
  assert(
    p.workload.reduce((s, x) => s + x.opportunities, 0) ===
      p.exposure.retainedEvents,
  );
  assert(
    p.pressurePhases.reduce((s, x) => s + x.opportunities, 0) ===
      p.exposure.pressureEvents,
  );
  assert(Math.abs(p.workload.reduce((s, x) => s + x.share, 0) - 100) < 1e-7);
}
for (const [id, a] of Object.entries(assets)) {
  assert(
    players.some((p) => p.id === id),
    `Unknown portrait ID ${id}`,
  );
  assert(/^\/(?:players|player_image)\/[\w-]+\.(?:png|webp|avif)$/.test(a.src));
  assert(a.alt && a.alt.length > 3);
  assert(
    fs.existsSync(path.join(root, "public", a.src)),
    `Missing portrait ${a.src}`,
  );
  assert(Number.isInteger(a.width) && a.width > 0);
  assert(Number.isInteger(a.height) && a.height > 0);
  assert(Object.values(a.crop).every(Number.isFinite));
  assert(a.crop.width > 0 && a.crop.height > 0);
  assert(Math.abs(a.crop.width / a.crop.height - 0.8) < 1e-8);
  assert(a.crop.x < a.width && a.crop.x + a.crop.width > 0);
  assert(a.crop.y < a.height && a.crop.y + a.crop.height > 0);
  assert.equal(a.trim.length, 4);
  assert(a.trim.every((n) => Number.isInteger(n) && n >= 0));
  assert(a.trim[0] + a.trim[2] < a.height);
  assert(a.trim[1] + a.trim[3] < a.width);
  if (a.src.endsWith(".png")) {
    const file = fs.readFileSync(path.join(root, "public", a.src));
    assert.equal(file.subarray(1, 4).toString(), "PNG");
    assert.equal(file.readUInt32BE(16), a.width, a.src);
    assert.equal(file.readUInt32BE(20), a.height, a.src);
  }
}
function walk(dir) {
  return fs.existsSync(dir)
    ? fs
        .readdirSync(dir, { withFileTypes: true })
        .flatMap((x) =>
          x.isDirectory()
            ? walk(path.join(dir, x.name))
            : [path.join(dir, x.name)],
        )
    : [];
}
for (const file of walk(path.join(root, "public"))) {
  assert(
    !/\.(?:csv|parquet|zip|sql|env)$/i.test(file),
    `Private file type in public assets: ${file}`,
  );
}
console.log(
  `Content checks passed: 20 exact ordered selections, 69 curated entries, 7 adequate recent entries, 2 absent, ${Object.keys(assets).length} portraits. No forbidden data keys.`,
);
