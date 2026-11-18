import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const reportInputs = [
  "content/generated/players.json",
  "content/generated/release.json",
  "content/generated/site.json",
  "content/copy.ts",
  "content/method.ts",
  "app/report/page.tsx",
  "app/layout.tsx",
  "app/globals.css",
  "components/ui.tsx",
  "components/data-value.tsx",
  "components/score-scope.tsx",
  "lib/public-numbers.ts",
  "scripts/render-report.mjs",
  "scripts/report-state.mjs",
  "public/fonts/barlow-condensed-latin-500-normal.woff2",
  "public/fonts/barlow-condensed-latin-600-normal.woff2",
  "public/fonts/manrope-latin-wght-normal.woff2",
];
export const sha256 = (data) =>
  crypto.createHash("sha256").update(data).digest("hex");
export function reportFingerprint() {
  const hash = crypto.createHash("sha256");
  for (const name of reportInputs) {
    hash.update(name);
    hash.update("\0");
    hash.update(fs.readFileSync(path.join(root, name)));
  }
  return hash.digest("hex");
}
export function validateReportState(manifest, buffer, fingerprint) {
  assert(manifest.available);
  assert.equal(
    manifest.sourceFingerprint,
    fingerprint,
    "PDF is stale: regenerate from current report sources",
  );
  assert.equal(
    manifest.sha256,
    sha256(buffer),
    "PDF differs from the verified artifact",
  );
  assert.equal(manifest.bytes, buffer.length);
  assert.equal(buffer.subarray(0, 5).toString(), "%PDF-");
}
export function checkReport() {
  const manifest = JSON.parse(
    fs.readFileSync(path.join(root, "content/generated/report.json")),
  );
  const file = path.join(root, "public/reports/pressure-index-report.pdf");
  assert.equal(
    fs.existsSync(file),
    manifest.available,
    "Report visibility and file availability disagree",
  );
  if (manifest.available)
    validateReportState(manifest, fs.readFileSync(file), reportFingerprint());
}
export function publishReport(candidate, fingerprint) {
  assert.equal(
    reportFingerprint(),
    fingerprint,
    "Report sources changed during rendering",
  );
  const bytes = fs.readFileSync(candidate);
  const manifest = {
    available: true,
    file: "pressure-index-report.pdf",
    bytes: bytes.length,
    sha256: sha256(bytes),
    sourceFingerprint: fingerprint,
  };
  validateReportState(manifest, bytes, fingerprint);
  fs.copyFileSync(
    candidate,
    path.join(root, "public/reports/pressure-index-report.pdf"),
  );
  fs.writeFileSync(
    path.join(root, "content/generated/report.json"),
    JSON.stringify(manifest, null, 2) + "\n",
  );
  return manifest;
}
if (
  process.argv[1] === fileURLToPath(import.meta.url) &&
  process.argv.includes("--withdraw")
) {
  const file = path.join(root, "public/reports/pressure-index-report.pdf");
  if (fs.existsSync(file)) {
    const archive = path.resolve(
      root,
      "../reports/publication_cleanup_2026-11-18/withdrawn",
    );
    fs.mkdirSync(archive, { recursive: true });
    fs.renameSync(
      file,
      path.join(archive, sha256(fs.readFileSync(file)) + ".pdf"),
    );
  }
  fs.writeFileSync(
    path.join(root, "content/generated/report.json"),
    JSON.stringify({ available: false }, null, 2) + "\n",
  );
  console.log("Report withdrawn; download remains hidden until regeneration.");
}
