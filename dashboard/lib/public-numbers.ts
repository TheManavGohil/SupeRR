import players from "../content/generated/players.json" with { type: "json" };
import release from "../content/generated/release.json" with { type: "json" };
import site from "../content/generated/site.json" with { type: "json" };
export type ValueFormat =
  "text" | "integer" | "rank" | "score" | "player-option";
export function resolvePublicValue(source: string): unknown {
  const parts = source.split(".");
  let value: unknown;
  if (parts[0] === "players") {
    const [, role, id] = parts;
    value = players.find((p) => p.role === role && p.id === id);
    parts.splice(0, 3);
  } else {
    value =
      parts[0] === "release" ? release : parts[0] === "site" ? site : undefined;
    parts.shift();
  }
  for (const key of parts) {
    if (["__proto__", "prototype", "constructor"].includes(key))
      throw Error("Invalid public reference");
    value = (value as Record<string, unknown> | undefined)?.[key];
  }
  if (value === undefined || value === null)
    throw Error(`Unknown public JSON reference: ${source}`);
  return value;
}
export function publicText(
  source: string,
  format: ValueFormat = "text",
): string {
  const value = resolvePublicValue(source);
  if (format === "player-option") {
    const p = value as (typeof players)[number];
    if (typeof p.rank !== "number" || typeof p.name !== "string")
      throw Error("Invalid player option reference");
    return `#${p.rank} ${p.name}${p.selected ? " · selected" : ""}`;
  }
  if (format === "text") {
    if (typeof value !== "number" && typeof value !== "string")
      throw Error("Expected a scalar public value");
    return String(value);
  }
  if (typeof value !== "number" || !Number.isFinite(value))
    throw Error(`Expected numeric public value: ${source}`);
  if (format === "rank") return String(value).padStart(2, "0");
  if (format === "integer")
    return value.toLocaleString("en-GB", { maximumFractionDigits: 0 });
  if (format === "score")
    return value.toLocaleString("en-GB", {
      minimumFractionDigits: site.scoreDigits,
      maximumFractionDigits: site.scoreDigits,
    });
  throw Error(`Unknown public formatter: ${format}`);
}
