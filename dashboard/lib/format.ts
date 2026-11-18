import type { Player, Role } from "./types";

// Browser-safe presentation helpers: no dataset import in this module.
export const roleLabel = (role: Role) =>
  role === "batting" ? "Batters" : "Bowlers";
export const playerUrl = (p: Pick<Player, "role" | "id">) =>
  `/players/${p.role}/${p.id}`;
export const compareUrl = (role: Role, ids: string[]) =>
  `/compare?role=${role}&players=${ids.join(",")}`;
export const num = (n: number | null | undefined, digits = 1) =>
  n == null
    ? "Unavailable"
    : n.toLocaleString("en-GB", {
        maximumFractionDigits: digits,
        minimumFractionDigits: digits,
      });
export const score = (n: number | null | undefined) => num(n, 4);
export const phaseName = (s: string) =>
  ({ "01-06": "Powerplay", "07-15": "Middle overs", "16-20": "Death overs" })[
    s
  ] ?? s;
export const recentLabel = (p: Pick<Player, "recent">) =>
  p.recent.status === "adequate"
    ? "2026 sample adequate"
    : p.recent.status === "no_retained_pressure"
      ? "No retained 2026 pressure evidence"
      : "2026 evidence limited";
export const variantLabel = (s: string) =>
  s.includes("50_50") ? "50 / 50" : s.includes("70_30") ? "70 / 30" : "60 / 40";
