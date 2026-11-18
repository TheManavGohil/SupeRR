import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { copy } from "../content/copy.ts";
import site from "../content/generated/site.json" with { type: "json" };
import { validateDocument } from "./check-built-content.mjs";
import { reportFingerprint, publishReport } from "./report-state.mjs";
const base = process.env.DASHBOARD_URL ?? "http://127.0.0.1:3100";
assert(
  ["localhost", "127.0.0.1"].includes(new URL(base).hostname),
  "Render the matching local production build",
);
const output = path.resolve(
  "../reports/publication_cleanup_2026-11-18/e/candidate.pdf",
);
const fingerprint = reportFingerprint();
const browser = await chromium.launch({
  executablePath:
    process.env.CHROME_PATH ??
    (fs.existsSync("/usr/bin/google-chrome")
      ? "/usr/bin/google-chrome"
      : undefined),
  args: ["--no-sandbox"],
});
try {
  const page = await browser.newPage();
  const response = await page.goto(`${base}/report`, {
    waitUntil: "networkidle",
  });
  assert.equal(response.status(), 200);
  await page.evaluate(() => document.fonts.ready);
  validateDocument(await page.content(), "PDF source page");
  await page.evaluate((publicBase) => {
    for (const a of document.querySelectorAll(".report-document a")) {
      const href = a.getAttribute("href");
      if (href?.startsWith("/"))
        a.setAttribute("href", new URL(href, publicBase).href);
    }
  }, site.publicBaseUrl);
  const links = await page
    .locator(".report-document a")
    .evaluateAll((items) => items.map((a) => a.href));
  assert(
    !links.some((href) => /localhost|127\.0\.0\.1|your-dashboard/.test(href)),
  );
  fs.mkdirSync(path.dirname(output), { recursive: true });
  await page.pdf({
    path: output,
    format: "A4",
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: "<span></span>",
    footerTemplate: `<div style="font-size:8px;width:100%;padding:0 45px;color:#536071;font-family:Arial;display:flex;justify-content:space-between"><span>${copy.footer}</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`,
  });
  assert(
    fs.statSync(output).size < site.document.maxBytes,
    "Report exceeds upload limit",
  );
  const manifest = publishReport(output, fingerprint);
  fs.writeFileSync(
    path.join(path.dirname(output), "render.json"),
    JSON.stringify({ manifest, links, sourcePageValidated: true }, null, 2) +
      "\n",
  );
  console.log(
    `Aggregate-only PDF generated and fingerprinted: ${manifest.bytes} bytes. Inspect the candidate before committing.`,
  );
} finally {
  await browser.close();
}
