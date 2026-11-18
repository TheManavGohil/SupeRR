import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { parse } from "parse5";
import { copy } from "../content/copy.ts";
import { publicText } from "../lib/public-numbers.ts";
import { root, walk, inspectText } from "./check-publication.mjs";
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
export function checkBuiltContent() {
  // Next's generated emergency shell is framework output, not an authored route.
  // Its technical status text is excluded here; the privacy scanner still checks it.
  const files = walk(path.join(root, ".next/server/app")).filter(
    (f) => f.endsWith(".html") && path.basename(f) !== "_global-error.html",
  );
  assert(files.length >= 76, "Expected all application HTML pages");
  let bindings = 0;
  for (const f of files)
    bindings += validateDocument(
      fs.readFileSync(f, "utf8"),
      path.relative(root, f),
    );
  return { pages: files.length, bindings };
}
if (process.argv[1] === fileURLToPath(import.meta.url))
  console.log("Built numeric/copy provenance passed:", checkBuiltContent());
