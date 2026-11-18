import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { createServer } from "node:http";
import next from "next";
import { parse } from "parse5";
import { copy } from "../content/copy.ts";
import { publicText } from "../lib/public-numbers.ts";
import { root, walk, inspectText, read } from "./check-publication.mjs";
const normal = (s) => s.replace(/\s+/g, " ").trim();
const text = (n) =>
  n.nodeName === "#text" ? n.value : (n.childNodes ?? []).map(text).join("");
export function validateDocument(html, label = "document") {
  inspectText(html, label);
  const document = parse(html);
  const errors = [];
  let bindings = 0;
  function visit(n) {
    if (["script", "style", "svg"].includes(n.tagName)) return;
    const attrs = Object.fromEntries(
      (n.attrs ?? []).map((a) => [a.name, a.value]),
    );
    if (attrs["data-copy-key"]) {
      const expected = copy[attrs["data-copy-key"]];
      if (expected === undefined || normal(text(n)) !== normal(expected))
        errors.push(`Shared copy mismatch: ${attrs["data-copy-key"]}`);
      bindings++;
      return;
    }
    if (attrs["data-json-source"]) {
      try {
        assert.equal(
          normal(text(n)),
          normal(
            publicText(
              attrs["data-json-source"],
              attrs["data-json-format"] ?? "text",
            ),
          ),
        );
      } catch (e) {
        errors.push(`JSON binding ${attrs["data-json-source"]}: ${e.message}`);
      }
      bindings++;
      return;
    }
    if (
      n.tagName === "meta" &&
      attrs.name === "description" &&
      attrs.content !== copy.metadataDescription
    )
      errors.push("Metadata description differs from generated copy");
    for (const key of ["aria-label", "alt", "title", "placeholder"])
      if (attrs[key] && /\d/.test(attrs[key]))
        errors.push(`Unbound numeric ${key}: ${attrs[key]}`);
    if (n.nodeName === "#text" && /\d/.test(n.value))
      errors.push(`Unbound numeric text: ${normal(n.value).slice(0, 140)}`);
    for (const child of n.childNodes ?? []) visit(child);
  }
  visit(document);
  assert.deepEqual(errors, [], `${label}: numeric/copy provenance failed`);
  return bindings;
}
export async function checkBuiltContent() {
  // Next's generated emergency shell is framework output, not an authored route.
  // Its technical status text is excluded here; the privacy scanner still checks it.
  const files = walk(path.join(root, ".next/server/app")).filter(
    (f) => f.endsWith(".html") && path.basename(f) !== "_global-error.html",
  );
  let bindings = 0;
  for (const f of files)
    bindings += validateDocument(
      fs.readFileSync(f, "utf8"),
      path.relative(root, f),
    );
  // Hosting adapters can change which prerendered files remain on disk. Verify
  // every application route through Next as well, rather than trusting a count.
  const routes = [
    "/",
    "/rankings/batting",
    "/rankings/bowling",
    "/compare",
    "/methodology",
    "/validation",
    "/report",
    ...read("content/generated/players.json").map(
      (player) => `/players/${player.role}/${player.id}`,
    ),
  ];
  const app = next({ dev: false, dir: root, quiet: true });
  let server;
  try {
    await app.prepare();
    server = createServer(app.getRequestHandler());
    await new Promise((resolve, reject) => {
      server.once("error", reject);
      server.listen(0, "127.0.0.1", resolve);
    });
    const base = `http://127.0.0.1:${server.address().port}`;
    for (const route of routes) {
      const response = await fetch(base + route, {
        signal: AbortSignal.timeout(30000),
      });
      assert.equal(response.status, 200, `${route}: expected HTTP 200`);
      bindings += validateDocument(await response.text(), route);
    }
  } finally {
    if (server?.listening) {
      server.closeAllConnections();
      await new Promise((resolve, reject) =>
        server.close((error) => (error ? reject(error) : resolve())),
      );
    }
    await app.close();
  }
  return { staticPages: files.length, servedRoutes: routes.length, bindings };
}
if (process.argv[1] === fileURLToPath(import.meta.url))
  console.log(
    "Built numeric/copy provenance passed:",
    await checkBuiltContent(),
  );
