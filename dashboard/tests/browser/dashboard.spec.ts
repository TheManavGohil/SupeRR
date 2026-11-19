import { copy } from "../../content/copy";
import site from "../../content/generated/site.json" with { type: "json" };
import reportManifest from "../../content/generated/report.json" with { type: "json" };
import portraits from "../../content/player-assets.json" with { type: "json" };
import { createHash } from "node:crypto";
import { validateDocument } from "../../scripts/check-built-content.mjs";
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import path from "node:path";
const report = reportManifest as { available: boolean; sha256?: string };

test("report download follows the verified manifest and retired files stay absent", async ({
  page,
  request,
}) => {
  await page.goto("/report");
  const link = page.getByRole("link", { name: "Download PDF", exact: true });
  await expect(link).toHaveCount(report.available ? 1 : 0);
  const pdf = await request.get("/reports/pressure-index-report.pdf");
  expect(pdf.status()).toBe(report.available ? 200 : 404);
  if (report.available) {
    expect(pdf.headers()["content-type"]).toContain("application/pdf");
    expect(
      createHash("sha256")
        .update(await pdf.body())
        .digest("hex"),
    ).toBe(report.sha256);
  }
  for (const route of [
    "/reports/pressure-index-submission.pptx",
    "/reports/pressure-index-slides.pdf",
  ])
    expect((await request.get(route)).status()).toBe(404);
});

test("all supplied portraits load on their profiles and retain the reviewed crop", async ({
  page,
  request,
}) => {
  const players = JSON.parse(
    fs.readFileSync(path.resolve("content/generated/players.json"), "utf8"),
  ) as { id: string; name: string; role: string; selected: boolean }[];
  for (const player of players.filter((p) => p.selected)) {
    const asset = portraits[player.id as keyof typeof portraits];
    const original = await request.get(asset.src);
    expect(original.status(), player.name).toBe(200);
    expect(
      createHash("sha256")
        .update(await original.body())
        .digest("hex"),
      player.name,
    ).toBe(asset.sha256);
    await page.goto(`/players/${player.role}/${player.id}`);
    const image = page.locator(".profile-portrait img");
    await expect(image).toHaveAttribute(
      "alt",
      `${player.name} — supplied RR-kit illustration`,
    );
    await expect
      .poll(
        () => image.evaluate((img) => (img as HTMLImageElement).naturalWidth),
        { message: player.name },
      )
      .toBeGreaterThan(0);
    const frame = page.locator(".profile-portrait .player-portrait-frame");
    const box = await frame.boundingBox();
    expect(box!.width / box!.height).toBeCloseTo(4 / 5, 2);
  }
  await page.goto("/players/batting/1077");
  await expect(
    page.locator(".profile-portrait .player-initials"),
  ).toBeVisible();
});

test("scope, canonical links and JSON-backed values remain valid after interaction", async ({
  page,
}) => {
  for (const route of [
    "/",
    "/methodology",
    "/validation",
    "/report",
    "/rankings/batting",
    "/compare",
  ]) {
    await page.goto(route);
    validateDocument(await page.content(), route);
    const canonical = await page
      .locator('link[rel="canonical"]')
      .getAttribute("href");
    expect(new URL(canonical!).href).toBe(
      new URL(route, site.publicBaseUrl).href,
    );
    if (route === "/" || route === "/methodology") {
      const scope = page.getByRole("region", { name: copy.scoreScopeTitle });
      await expect(scope).toContainText(copy.scoreScopeProduction);
      await expect(scope).toContainText(copy.scoreScopeRole);
    }
  }
  await page.goto("/rankings/batting");
  await page
    .getByRole("checkbox", { name: copy.recentFilter, exact: true })
    .check();
  validateDocument(await page.content(), "filtered rankings");
  await page.goto("/compare?role=bowling&players=781,2933,23");
  validateDocument(await page.content(), "bowling comparison");
});

test("overview, fixed ranking filters, layout switch and comparison selection", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /WHEN THE GAME GETS TIGHT/ }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Explore the selections" }).click();
  await expect(
    page.getByRole("heading", { name: "Ten batters. Every pick explained." }),
  ).toBeVisible();
  await page
    .getByRole("checkbox", { name: "Adequate 2026 sample", exact: true })
    .check();
  await expect(page.locator(".player-card")).toHaveCount(3);
  await expect(
    page.getByRole("heading", { name: "Namboori Tilak Varma" }),
  ).toBeVisible();
  await expect(page.getByText("RANK 08", { exact: true })).toBeVisible();
  await page
    .getByRole("checkbox", { name: "Adequate 2026 sample", exact: true })
    .uncheck();
  for (const name of ["Tim David", "Suryakumar Yadav", "Nicholas Pooran"])
    await page
      .getByRole("checkbox", { name: `Compare ${name}`, exact: true })
      .check();
  await expect(
    page.getByRole("checkbox", { name: "Compare Shashank Singh", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("link", { name: "Compare evidence", exact: true })
    .click();
  await expect(page.locator(".compare-card")).toHaveCount(3);
  await expect(
    page.getByRole("heading", { name: "The same questions. Side by side." }),
  ).toBeVisible();
  await page.goto("/rankings/bowling");
  await page.getByRole("button", { name: "Table view" }).click();
  await expect(page.locator(".rankings-table tbody tr")).toHaveCount(10);
  await page
    .getByRole("searchbox", { name: "Search player names" })
    .fill("nobody");
  await expect(
    page.getByRole("heading", { name: "No matching selections" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Reset filters" }).click();
  await expect(page.locator(".rankings-table tbody tr")).toHaveCount(10);
  expect(errors).toEqual([]);
});

test("all 69 direct profiles render and selected dossiers retain essential evidence", async ({
  page,
  request,
}) => {
  const players = JSON.parse(
    fs.readFileSync(path.resolve("content/generated/players.json"), "utf8"),
  ) as { role: string; id: string; name: string; selected: boolean }[];
  for (const p of players) {
    const r = await request.get(`/players/${p.role}/${p.id}`);
    expect(r.status(), p.name).toBe(200);
    expect(await r.text()).toContain(p.name);
  }
  await page.goto("/players/batting/1318");
  await expect(
    page.getByText("No retained 2026 pressure evidence", { exact: true }),
  ).toBeVisible();
  for (const id of ["task", "performance", "usual", "alternatives"])
    await expect(page.locator(`#${id}`)).toBeAttached();
  await expect(
    page.getByText("Reliable change estimate: unavailable.", { exact: true }),
  ).toBeVisible();
  await page.goto("/players/bowling/35318");
  await expect(
    page.getByText("2026 sample adequate", { exact: true }),
  ).toBeVisible();
  expect((await request.get("/players/batting/does-not-exist")).status()).toBe(
    404,
  );
  expect((await request.get("/rankings/unknown")).status()).toBe(404);
});

test("compare URL sanitises roles, duplicates, invalid IDs and maximum three entries", async ({
  page,
}) => {
  await page.goto("/compare?role=batting&players=6396,6396,781,1699,3125,2756");
  await expect(page.locator(".compare-card")).toHaveCount(3);
  await expect(
    page.getByRole("heading", { name: "Sunil Narine", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText("Some URL entries were unavailable", { exact: true }),
  ).toBeVisible();
  await page.goto("/compare?role=bowling&players=invalid");
  await expect(
    page.getByRole("heading", { name: "Choose players to compare" }),
  ).toBeVisible();
});

test("phone layout, keyboard navigation, reduced motion and no page overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to content" }),
  ).toBeFocused();
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Method", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "From the ball. To the shortlist." }),
  ).toBeVisible();
  for (const width of [360, 390, 768, 1280, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of [
      "/",
      "/rankings/batting",
      "/players/batting/6396",
      "/compare",
      "/methodology",
      "/validation",
      "/report",
    ]) {
      await page.goto(route);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth + 1,
        ),
        `${route} at ${width}px`,
      ).toBe(true);
    }
  }
});

test("key pages pass automated WCAG A/AA accessibility checks", async ({
  page,
}) => {
  for (const route of [
    "/",
    "/rankings/batting",
    "/players/batting/6396",
    "/compare",
    "/methodology",
    "/validation",
    "/report",
  ]) {
    await page.goto(route);
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(
      result.violations.map((v) => ({
        id: v.id,
        description: v.description,
        nodes: v.nodes.map((n) => n.target),
      })),
      route,
    ).toEqual([]);
  }
});

test("report includes both exact ordered lists and required method sections", async ({
  page,
}) => {
  await page.goto("/report");
  const tables = page.locator(".report-document table");
  await expect(tables).toHaveCount(2);
  await expect(tables.nth(0).locator("tbody tr")).toHaveCount(10);
  await expect(tables.nth(1).locator("tbody tr")).toHaveCount(10);
  await expect(tables.nth(0).locator("tbody tr").first()).toContainText(
    "Tim David",
  );
  await expect(tables.nth(1).locator("tbody tr").last()).toContainText(
    "Piyush Chawla",
  );
  await expect(page.locator(".report-player")).toHaveCount(20);
  await expect(
    page.getByRole("heading", {
      name: copy.reportReliability,
    }),
  ).toBeVisible();
});

test("rankings and dossiers remain readable without JavaScript", async ({
  browser,
  baseURL,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(`${baseURL}/rankings/batting`);
  await expect(
    page.getByRole("heading", { name: "Tim David", exact: true }),
  ).toBeVisible();
  await page.goto(`${baseURL}/players/bowling/2933`);
  await expect(
    page.getByRole("heading", { name: "Jasprit Bumrah", exact: true }),
  ).toBeVisible();
  await expect(page.locator("#usual")).toContainText(
    "Reliable change estimate: unavailable.",
  );
  await context.close();
});
