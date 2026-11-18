import fs from "node:fs";
const dir = new URL("../tests/", import.meta.url);
for (const file of fs
  .readdirSync(dir)
  .filter((f) => f.endsWith(".test.mjs"))
  .sort())
  await import(new URL(file, dir));
