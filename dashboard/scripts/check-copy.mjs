import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import ts from "typescript";
import { fileURLToPath } from "node:url";
import { copy, roleContribution } from "../content/copy.ts";
import { root, walk } from "./check-publication.mjs";
const normalize = (s) => s.replace(/\s+/g, " ").trim();
const phrases = new Set(
  [...Object.values(copy), ...Object.values(roleContribution)]
    .filter((s) => s.length >= 24)
    .map(normalize),
);
export function duplicatedCopy(source, name = "candidate.tsx") {
  const file = ts.createSourceFile(
    name,
    source,
    ts.ScriptTarget.Latest,
    true,
    name.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
  );
  const errors = [];
  function visit(n) {
    if (
      ts.isStringLiteral(n) ||
      ts.isNoSubstitutionTemplateLiteral(n) ||
      ts.isJsxText(n)
    ) {
      const value = normalize(n.text);
      if (phrases.has(value)) errors.push(value);
    }
    ts.forEachChild(n, visit);
  }
  visit(file);
  return errors;
}
export function checkCopy() {
  for (const dir of ["app", "components", "lib", "content", "scripts"])
    for (const f of walk(path.join(root, dir)))
      if (
        /\.(ts|tsx|mjs)$/.test(f) &&
        path.relative(root, f) !== "content/copy.ts"
      )
        assert.deepEqual(
          duplicatedCopy(fs.readFileSync(f, "utf8"), f),
          [],
          `Shared copy hard-coded outside copy.ts: ${path.relative(root, f)}`,
        );
  return phrases.size;
}
if (process.argv[1] === fileURLToPath(import.meta.url))
  console.log(`Shared copy checks passed: ${checkCopy()} protected phrases.`);
