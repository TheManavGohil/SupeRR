"use client";
import { copy } from "@/content/copy";
import site from "@/content/generated/site.json";
import { useState, type ReactNode } from "react";
import Link from "next/link";
import { Search, LayoutGrid, List, ArrowUpRight, X } from "lucide-react";
import type { CardPlayer, Role } from "@/lib/types";
import { compareUrl, playerUrl, score } from "@/lib/format";
import { PlayerCard, RecentBadge } from "./ui";

export function RankingsExplorer({
  players,
  role,
  intro,
  tabs,
}: {
  players: CardPlayer[];
  role: Role;
  intro: ReactNode;
  tabs: ReactNode;
}) {
  const [search, setSearch] = useState("");
  const [recent, setRecent] = useState(false);
  const [view, setView] = useState<"cards" | "table">("cards");
  const [ids, setIds] = useState<string[]>([]);
  const filtered = players.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) &&
      (!recent || p.recent.status === "adequate"),
  );
  const featured =
    view === "cards" && filtered.some((p) => p.id === players[0]?.id)
      ? players[0]
      : null;
  const gridPlayers = filtered.filter((p) => p.id !== featured?.id);
  const toggle = (id: string) =>
    setIds(
      ids.includes(id)
        ? ids.filter((x) => x !== id)
        : ids.length < site.compareLimit
          ? [...ids, id]
          : ids,
    );
  const selectableCard = (p: CardPlayer) => (
    <div className="selectable-card" key={p.id}>
      <PlayerCard player={p} />
      <label className="compare-checkbox">
        <input
          type="checkbox"
          checked={ids.includes(p.id)}
          disabled={ids.length === site.compareLimit && !ids.includes(p.id)}
          onChange={() => toggle(p.id)}
        />
        Compare {p.name}
      </label>
    </div>
  );
  return (
    <>
      <div className={`rankings-lead ${featured ? "has-featured" : ""}`}>
        {intro}
        {featured && (
          <section
            className="rankings-featured"
            aria-label="Top-ranked selection"
          >
            <h2 className="sr-only">Rank one</h2>
            {selectableCard(featured)}
          </section>
        )}
      </div>
      {tabs}
      <h2 className="sr-only">Ranked player evidence</h2>
      <div className="rankings-toolbar">
        <label className="search-control">
          <Search size={18} />
          <span className="sr-only">Search player names</span>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Find a player…"
          />
        </label>
        <label className="checkbox-control">
          <input
            type="checkbox"
            checked={recent}
            onChange={(e) => setRecent(e.target.checked)}
          />
          {copy.recentFilter}
        </label>
        <div className="view-switch" role="group" aria-label="Ranking layout">
          <button
            aria-label="Card view"
            aria-pressed={view === "cards"}
            onClick={() => setView("cards")}
          >
            <LayoutGrid size={18} />
          </button>
          <button
            aria-label="Table view"
            aria-pressed={view === "table"}
            onClick={() => setView("table")}
          >
            <List size={18} />
          </button>
        </div>
      </div>
      <p className="filter-caption" aria-live="polite">
        Showing {filtered.length} of {players.length} {copy.rankingFilterSuffix}
        {ids.length === site.compareLimit
          ? copy.compareLimitReached
          : copy.compareHint}
      </p>
      {filtered.length === 0 ? (
        <div className="empty-state">
          <h2>No matching selections</h2>
          <p>Try another name or reset the recent-evidence filter.</p>
          <button
            className="button"
            onClick={() => {
              setSearch("");
              setRecent(false);
            }}
          >
            Reset filters
          </button>
        </div>
      ) : view === "cards" ? (
        gridPlayers.length > 0 && (
          <div className="player-grid rankings-grid">
            {gridPlayers.map(selectableCard)}
          </div>
        )
      ) : (
        <div className="table-scroll">
          <table className="rankings-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Player / observed task</th>
                <th>Score</th>
                <th>{copy.retainedMatches}</th>
                <th>{copy.recentColumn}</th>
                <th>Compare</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id}>
                  <td className="rank-cell">
                    {String(p.rank).padStart(2, "0")}
                  </td>
                  <th>
                    <Link href={playerUrl(p)}>
                      {p.name}
                      <ArrowUpRight size={14} />
                    </Link>
                    <small>{p.task}</small>
                  </th>
                  <td>{score(p.rating.low)}</td>
                  <td>
                    {p.exposure.pressureMatches}
                    {p.exposure.peerSupportedMatches !==
                      p.exposure.pressureMatches && (
                      <small>
                        {p.exposure.peerSupportedMatches} {copy.peerSupported}
                      </small>
                    )}
                  </td>
                  <td>
                    <RecentBadge player={p} />
                  </td>
                  <td>
                    <input
                      aria-label={`Compare ${p.name}`}
                      type="checkbox"
                      checked={ids.includes(p.id)}
                      disabled={
                        ids.length === site.compareLimit && !ids.includes(p.id)
                      }
                      onChange={() => toggle(p.id)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {ids.length > 0 && (
        <aside
          className="compare-tray"
          aria-label="Selected comparison players"
        >
          <div>
            <strong>
              {ids.length} / {site.compareLimit} players
            </strong>
            <span>
              {players
                .filter((p) => ids.includes(p.id))
                .map((p) => p.name)
                .join(" · ")}
            </span>
          </div>
          <Link className="button" href={compareUrl(role, ids)}>
            Compare evidence <ArrowUpRight size={16} />
          </Link>
          <button
            className="icon-button"
            aria-label="Clear comparison"
            onClick={() => setIds([])}
          >
            <X size={18} />
          </button>
        </aside>
      )}
    </>
  );
}
