"use client";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import type { ComparePlayer, Role } from "@/lib/types";
import {
  compareUrl,
  num,
  score,
  playerUrl,
  recentLabel,
  phaseName,
} from "@/lib/format";
import { IntervalChart } from "./charts";
import { Notice, RecentBadge } from "./ui";

export function CompareExplorer({ players }: { players: ComparePlayer[] }) {
  const query = useSearchParams();
  const router = useRouter();
  const role: Role = query.get("role") === "bowling" ? "bowling" : "batting";
  const list = players
    .filter((p) => p.role === role)
    .sort((a, b) => a.rank - b.rank);
  const rawIds = [
    ...new Set((query.get("players") ?? "").split(",").filter(Boolean)),
  ];
  const ids = rawIds.filter((id) => list.some((p) => p.id === id)).slice(0, 3);
  const effectiveIds = query.has("players")
    ? ids
    : list.slice(0, 2).map((p) => p.id);
  const chosen = effectiveIds.map((id) => list.find((p) => p.id === id)!);
  const update = (position: number, id: string) => {
    const next = [...effectiveIds];
    if (id) next[position] = id;
    else next.splice(position, 1);
    router.replace(compareUrl(role, [...new Set(next.filter(Boolean))]), {
      scroll: false,
    });
  };
  const rows: {
    label: string;
    value: (p: ComparePlayer) => React.ReactNode;
  }[] = [
    { label: "Conservative score", value: (p) => score(p.rating.low) },
    {
      label: "10th–90th interval",
      value: (p) => `${score(p.rating.low)} to ${score(p.rating.high)}`,
    },
    {
      label: "Pressure matches / opportunities",
      value: (p) =>
        `${p.exposure.pressureMatches} / ${p.exposure.pressureEvents}`,
    },
    {
      label: role === "batting" ? "Batter runs / 100" : "Concessions / 100",
      value: (p) => num(p.pressure.runs_per_100),
    },
    {
      label:
        role === "batting" ? "Attributed dismissals / 100" : "Wickets / 100",
      value: (p) => num(p.pressure.wickets_per_100),
    },
    {
      label: "Source retention",
      value: (p) => `${num(p.exposure.sourceRetention * 100)}%`,
    },
    {
      label: "Dominant pressure phase",
      value: (p) =>
        phaseName(
          [...p.pressurePhases].sort((a, b) => b.share - a.share)[0]?.phase ??
            "Unavailable",
        ),
    },
    { label: "2026 status", value: (p) => recentLabel(p) },
    { label: "2026 pressure opportunities", value: (p) => p.recent.events },
    { label: "Reliable usual-performance change", value: () => "Unavailable" },
    {
      label: "Inadequate season-deletion samples",
      value: (p) => p.repeatability.seasonsInadequate,
    },
    {
      label: "Strongest qualification",
      value: (p) =>
        p.editorial?.caution ??
        "Inspect sample, source retention and context evidence; no selected-player narrative is attached.",
    },
  ];
  return (
    <>
      <nav className="role-tabs" aria-label="Comparison role">
        <Link
          href={compareUrl(
            "batting",
            players
              .filter((p) => p.role === "batting" && p.selected)
              .sort((a, b) => a.rank - b.rank)
              .slice(0, 2)
              .map((p) => p.id),
          )}
          aria-current={role === "batting" ? "page" : undefined}
        >
          Batting
        </Link>
        <Link
          href={compareUrl(
            "bowling",
            players
              .filter((p) => p.role === "bowling" && p.selected)
              .sort((a, b) => a.rank - b.rank)
              .slice(0, 2)
              .map((p) => p.id),
          )}
          aria-current={role === "bowling" ? "page" : undefined}
        >
          Bowling
        </Link>
      </nav>
      <div className="compare-controls">
        {[0, 1, 2].map((i) => (
          <label key={i}>
            Player {i + 1}
            <select
              aria-label={`Comparison player ${i + 1}`}
              value={effectiveIds[i] ?? ""}
              onChange={(e) => update(i, e.target.value)}
            >
              <option value="">Choose a player</option>
              {list.map((p) => (
                <option
                  key={p.id}
                  value={p.id}
                  disabled={
                    effectiveIds.includes(p.id) && effectiveIds[i] !== p.id
                  }
                >
                  #{p.rank} {p.name}
                  {p.selected ? " · selected" : ""}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
      {rawIds.some((id) => !list.some((p) => p.id === id)) && (
        <Notice title="Some URL entries were unavailable">
          <p>
            Only valid candidates from the selected role are shown. Choose
            players below to complete the comparison.
          </p>
        </Notice>
      )}
      {chosen.length ? (
        <>
          <div className="compare-cards">
            {chosen.map((p) => (
              <article className="compare-card" key={p.id}>
                <span className="compare-card-rank">
                  {p.selected ? "SELECTED" : "COMPARISON CANDIDATE"} · RANK{" "}
                  {p.rank}
                </span>
                <h2>{p.name}</h2>
                <p>{p.task}</p>
                <strong className="score-big">{score(p.rating.low)}</strong>
                <RecentBadge player={p} />
                <p>
                  {p.editorial?.why ??
                    "Compare this candidate on the same frozen evidence and sample rules."}
                </p>
                <Link className="text-link" href={playerUrl(p)}>
                  Full evidence <ArrowUpRight size={15} />
                </Link>
              </article>
            ))}
          </div>
          <section className="section">
            <h2 style={{ marginBottom: 25 }}>
              The same questions. Side by side.
            </h2>
            <div className="table-scroll">
              <table className="comparison-table">
                <thead>
                  <tr>
                    <th>Evidence</th>
                    {chosen.map((p) => (
                      <th key={p.id}>{p.name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.label}>
                      <th>{row.label}</th>
                      {chosen.map((p) => (
                        <td key={p.id}>{row.value(p)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <IntervalChart players={chosen} />
          <Notice title="Read the tradeoff, preserve the ordering">
            <p>
              Raw rates reflect different observed workloads. The primary index
              compares broad measured contexts, with incomplete venue/opposition
              adjustment. These intervals are not paired superiority tests. The
              frozen rank follows the conservative statistic, even when the
              uncertainty overlaps.
            </p>
          </Notice>
        </>
      ) : (
        <div className="empty-state">
          <h2>Choose players to compare</h2>
          <p>
            Select up to three players from one role. Missing or invalid URL
            values do not become zero-performance comparisons.
          </p>
        </div>
      )}
    </>
  );
}
