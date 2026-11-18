import "server-only";
import raw from "@/content/generated/players.json";
import release from "@/content/generated/release.json";
import type { Player, Role } from "./types";
export const players = raw as Player[];
export { release };
export const roles: Role[] = ["batting", "bowling"];
export * from "./format";
export const selected = (role: Role) =>
  players
    .filter((p) => p.selected && p.role === role)
    .sort((a, b) => a.rank - b.rank);
export const findPlayer = (role: string, id: string) =>
  players.find((p) => p.role === role && p.id === id);
