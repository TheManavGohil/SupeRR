import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";
import { parse } from "parse5";
import { copy } from "../content/copy.ts";
import { validateDocument } from "./check-built-content.mjs";
import { root, read, inspectText } from "./check-publication.mjs";
import { checkReport, sha256 } from "./report-state.mjs";

const normal = (value) => value.replace(/\s+/g, " ").trim();
const portraits = read("content/player-assets.json");
function imageSource(src) {
  const url = new URL(src, "https://local.invalid");
  return url.pathname === "/_next/image"
    ? url.searchParams.get("url")
    : url.pathname;
}
const text = (node) =>
  node.nodeName === "#text"
    ? node.value
    : (node.childNodes ?? []).map(text).join("");
function elements(html) {
  const nodes = [];
  function visit(node) {
    if (node.tagName)
      nodes.push({
        tag: node.tagName,
        attrs: Object.fromEntries(
          (node.attrs ?? []).map((a) => [a.name, a.value]),
        ),
        text: normal(text(node)),
      });
    for (const child of node.childNodes ?? []) visit(child);
  }
  visit(parse(html));
  return nodes;
}

// This validates release content. Check the GitHub/Vercel status of the exact
// pushed commit separately; HTTP 200 alone does not establish deployment identity.
export function verifyRoute(html, route, players, publicBase) {
  const bindings = validateDocument(html, route);
  assert(bindings > 0, `${route}: missing publication bindings`);
  const nodes = elements(html);
  const canonical = nodes.find(
    (n) => n.tag === "link" && n.attrs.rel === "canonical",
  );
  assert(canonical?.attrs.href, `${route}: missing canonical URL`);
  assert.equal(
    new URL(canonical.attrs.href).href,
    new URL(route, publicBase).href,
  );
  const robots = nodes.find(
    (n) => n.tag === "meta" && n.attrs.name === "robots",
  );
  assert(
    robots?.attrs.content.includes("noindex"),
    `${route}: noindex changed`,
  );
  assert(
    robots?.attrs.content.includes("nofollow"),
    `${route}: nofollow changed`,
  );
  const images = nodes.filter((n) => n.tag === "img");
  for (const image of images)
    assert(
      Object.values(portraits).some(
        (asset) => asset.src === imageSource(image.attrs.src),
      ),
      `${route}: unapproved image`,
    );
  if (images.length)
    assert(
      nodes.some((n) => n.attrs["data-copy-key"] === "portraitDisclosure"),
      `${route}: missing portrait disclosure`,
    );
  if (["/", "/methodology", "/report"].includes(route)) {
    for (const key of [
      "scoreScopeTitle",
      "scoreScopeProduction",
      "scoreScopeRole",
      "scoreScopeAdjustment",
      "scoreScopeFuture",
    ])
      assert(
        nodes.some(
          (n) =>
            n.attrs["data-copy-key"] === key && n.text === normal(copy[key]),
        ),
        `${route}: missing scope ${key}`,
      );
  }
  const player = players.find((p) => route === `/players/${p.role}/${p.id}`);
  if (player) {
    assert(
      nodes.some((n) => n.tag === "h1" && n.text === player.name),
      `${route}: wrong player`,
    );
    for (const key of [
      "rank",
      "rating.low",
      "exposure.pressureMatches",
      "exposure.pressureEvents",
    ])
      assert(
        nodes.some(
          (n) =>
            n.attrs["data-json-source"] ===
            `players.${player.role}.${player.id}.${key}`,
        ),
        `${route}: missing player aggregate ${key}`,
      );
    if (portraits[player.id])
      assert(
        images.some(
          (image) => imageSource(image.attrs.src) === portraits[player.id].src,
        ),
        `${route}: missing player portrait`,
      );
  }
  if (route.startsWith("/rankings/"))
    for (const selected of players.filter(
      (p) => p.selected && route === `/rankings/${p.role}`,
    ))
      assert(
        images.some(
          (image) =>
            imageSource(image.attrs.src) === portraits[selected.id].src,
        ),
        `${route}: missing ${selected.name} portrait`,
      );
  if (route === "/")
    assert(
      images.some(
        (image) =>
          imageSource(image.attrs.src) ===
          portraits[
            players.find(
              (p) => p.selected && p.role === "batting" && p.rank === 1,
            ).id
          ].src,
      ),
      "Missing hero portrait",
    );
  return {
    bindings,
    scripts: nodes
      .filter((n) => n.tag === "script" && n.attrs.src)
      .map((n) => n.attrs.src),
  };
}

export async function verifyDeployment() {
  checkReport();
  const site = read("content/generated/site.json");
  const players = read("content/generated/players.json");
  const report = read("content/generated/report.json");
  const base = new URL(process.env.DASHBOARD_URL ?? site.publicBaseUrl);
  assert(["https:", "http:"].includes(base.protocol));
  assert(
    !base.username &&
      !base.password &&
      base.pathname === "/" &&
      !base.search &&
      !base.hash,
  );
  assert(
    base.protocol === "https:" ||
      ["localhost", "127.0.0.1"].includes(base.hostname),
  );
  const out = process.env.VERIFY_OUTPUT_DIR
    ? path.resolve(process.env.VERIFY_OUTPUT_DIR)
    : path.resolve(
        root,
        "../reports/publication_cleanup_2026-11-18",
        `g-${Date.now()}`,
      );
  assert(
    out.startsWith(path.resolve(root, "../reports") + path.sep),
    "Verification receipts must stay in the ignored reports directory",
  );
  fs.mkdirSync(out, { recursive: true });
  const receipt = {
    base: base.origin,
    checkedAt: new Date().toISOString(),
    expectedAggregateSha256: sha256(
      fs.readFileSync(path.join(root, "content/generated/players.json")),
    ),
    expectedReportSha256: report.sha256 ?? null,
    routes: [],
    scripts: [],
    retired: [],
    images: [],
    screenshots: [],
    passed: false,
  };
  let browser;
  try {
    browser = await chromium.launch({
      executablePath:
        process.env.CHROME_PATH ??
        (fs.existsSync("/usr/bin/google-chrome")
          ? "/usr/bin/google-chrome"
          : undefined),
      args: ["--no-sandbox"],
    });
    // Fresh context: no login/session is inherited from the participant.
    const context = await browser.newContext();
    const routes = [
      "/",
      "/rankings/batting",
      "/rankings/bowling",
      "/compare",
      "/methodology",
      "/validation",
      "/report",
      ...players.map((p) => `/players/${p.role}/${p.id}`),
    ];
    const scripts = new Set();
    for (let i = 0; i < routes.length; i += 5) {
      await Promise.all(
        routes.slice(i, i + 5).map(async (route) => {
          const response = await context.request.get(new URL(route, base).href);
          assert.equal(response.status(), 200, `${route}: expected HTTP 200`);
          const result = verifyRoute(
            await response.text(),
            route,
            players,
            site.publicBaseUrl,
          );
          result.scripts.forEach((src) => scripts.add(src));
          receipt.routes.push({
            route,
            status: response.status(),
            bindings: result.bindings,
          });
        }),
      );
    }
    for (const src of scripts) {
      const url = new URL(src, base);
      assert.equal(
        url.origin,
        base.origin,
        "Unexpected external application script",
      );
      const response = await context.request.get(url.href);
      assert.equal(response.status(), 200, `Script ${src}`);
      inspectText(await response.text(), src);
      receipt.scripts.push(src);
    }
    for (const route of read("tests/fixtures/retired-public-paths.json")) {
      const response = await context.request.get(new URL(route, base).href);
      assert(
        [404, 410].includes(response.status()),
        `${route}: retired asset still available`,
      );
      receipt.retired.push({ route, status: response.status() });
    }
    for (const asset of Object.values(portraits)) {
      const response = await context.request.get(new URL(asset.src, base).href);
      assert.equal(
        response.status(),
        200,
        `${asset.src}: missing supplied image`,
      );
      assert(response.headers()["content-type"]?.includes("image/png"));
      assert.equal(
        sha256(await response.body()),
        asset.sha256,
        `${asset.src}: image differs from supplied original`,
      );
      receipt.images.push({
        route: asset.src,
        status: response.status(),
        sha256: asset.sha256,
      });
    }
    const pdf = await context.request.get(
      new URL("/reports/pressure-index-report.pdf", base).href,
    );
    assert.equal(pdf.status(), report.available ? 200 : 404);
    if (report.available) {
      assert(pdf.headers()["content-type"]?.includes("application/pdf"));
      const bytes = await pdf.body();
      assert.equal(bytes.length, report.bytes);
      assert.equal(
        sha256(bytes),
        report.sha256,
        "Live PDF differs from the verified artifact",
      );
      receipt.download = { bytes: bytes.length, sha256: sha256(bytes) };
    }
    const page = await context.newPage();
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      for (const [label, route] of [
        ["overview", "/"],
        ["batting", "/rankings/batting"],
        ["bowling", "/rankings/bowling"],
        ["profile", "/players/batting/6396"],
      ]) {
        await page.goto(new URL(route, base).href, {
          waitUntil: "networkidle",
        });
        await page.evaluate(() => document.fonts.ready);
        await page.evaluate(async () => {
          for (const image of document.images) image.loading = "eager";
          await Promise.all(
            [...document.images].map((image) => image.decode()),
          );
        });
        verifyRoute(await page.content(), route, players, site.publicBaseUrl);
        assert(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth + 1,
          ),
          `${route}: overflow at ${width}px`,
        );
        const filename = `${label}-${width}.png`;
        await page.screenshot({
          path: path.join(out, filename),
          fullPage: true,
        });
        receipt.screenshots.push(filename);
      }
    }
    receipt.passed = true;
    console.log(
      `Verified ${receipt.routes.length} routes, ${receipt.scripts.length} script assets, ${receipt.images.length} supplied images, ${receipt.retired.length} retired assets, ${report.available ? "matching PDF" : "withdrawn PDF"} and ${receipt.screenshots.length} screenshots. Receipt: ${out}`,
    );
    return receipt;
  } catch (error) {
    receipt.error = error.message;
    throw error;
  } finally {
    fs.writeFileSync(
      path.join(out, "verification.json"),
      JSON.stringify(receipt, null, 2) + "\n",
    );
    await browser?.close();
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    await verifyDeployment();
  } catch (error) {
    console.error(
      `Deployment verification failed: ${error.message.split("\n")[0]}`,
    );
    process.exitCode = 1;
  }
}
