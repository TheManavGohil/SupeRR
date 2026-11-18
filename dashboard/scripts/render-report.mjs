import { copy } from "../content/copy.ts";
import site from "../content/generated/site.json" with { type: "json" };
import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
const base = process.env.DASHBOARD_URL ?? "http://127.0.0.1:3000";
const output = path.resolve("public/reports/pressure-index-report.pdf");
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
  await page.goto(`${base}/report`, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  // Relative links would otherwise embed localhost in the exported submission.
  // Keep external attribution; strip local navigation URLs unless a public base is supplied.
  await page.evaluate((publicBase) => {
    for (const a of document.querySelectorAll(".report-document a")) {
      const href = a.getAttribute("href");
      if (href?.startsWith("/")) {
        if (publicBase) a.setAttribute("href", new URL(href, publicBase).href);
        else a.removeAttribute("href");
      }
    }
  }, site.publicBaseUrl);
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
  const size = fs.statSync(output).size;
  if (size > site.document.maxBytes)
    throw new Error("Report exceeds official upload limit");
  console.log(
    `PDF rendered: ${output}; ${size.toLocaleString()} bytes. Public deep links included.`,
  );
} finally {
  await browser.close();
}
