import { copy } from "../content/copy";
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
export const recentLabel = (p: Pick<Player, "recent">) =>
  p.recent.status === "adequate"
    ? copy.recentAdequate
    : p.recent.status === "no_retained_pressure"
      ? copy.recentAbsent
      : copy.recentLimited;
export const variantLabel = (s: string) =>
  s.includes("50_50")
    ? copy.weightEqual
    : s.includes("70_30")
      ? copy.weightRuns
      : copy.weightPrimary;
