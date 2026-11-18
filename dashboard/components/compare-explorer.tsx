"use client";
import { publicText } from "@/lib/public-numbers";
import { DataValue, CopyText, KnownText } from "@/components/data-value";
import { copy } from "@/content/copy";
import site from "@/content/generated/site.json";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import type { ComparePlayer, Role } from "@/lib/types";
import { compareUrl, score, playerUrl, recentLabel } from "@/lib/format";
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
  const ids = rawIds
    .filter((id) => list.some((p) => p.id === id))
    .slice(0, site.compareLimit);
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
    { label: copy.scoreLabel, value: (p) => score(p.rating.low) },
    { label: copy.retainedMatches, value: (p) => p.exposure.pressureMatches },
    {
      label: copy.pressureOpportunities,
      value: (p) => p.exposure.pressureEvents,
    },
    { label: "Observed task", value: (p) => p.task },
    { label: "Recent evidence", value: (p) => recentLabel(p) },
    {
      label: "Eligibility",
      value: (p) => (p.eligibility.primary ? copy.eligible : copy.ineligible),
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
            Player <DataValue source={`site.uiCounts.${i + 1}`} />
            <select
              aria-label={`Comparison player ${(site.numberWords as Record<string, string>)[String(i + 1)]}`}
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
                  data-json-source={`players.${p.role}.${p.id}`}
                  data-json-format="player-option"
                >
                  {publicText(`players.${p.role}.${p.id}`, "player-option")}
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
                  <DataValue
                    source={`players.${p.role}.${p.id}.rank`}
                    format="text"
                  />
                </span>
                <h2>
                  <DataValue
                    source={`players.${p.role}.${p.id}.name`}
                    format="text"
                  />
                </h2>
                <p>
                  <DataValue
                    source={`players.${p.role}.${p.id}.task`}
                    format="text"
                  />
                </p>
                <strong className="score-big">
                  <DataValue
                    source={`players.${p.role}.${p.id}.rating.low`}
                    format="score"
                  />
                </strong>
                <RecentBadge player={p} />
                <p>
                  <CopyText name="comparisonCandidate" />
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
                      <th key={p.id}>
                        <DataValue
                          source={`players.${p.role}.${p.id}.name`}
                          format="text"
                        />
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.label}>
                      <th>
                        <KnownText value={row.label} />
                      </th>
                      {chosen.map((p) => (
                        <td key={p.id}>
                          {row.label === copy.scoreLabel ? (
                            <DataValue
                              source={`players.${p.role}.${p.id}.rating.low`}
                              format="score"
                            />
                          ) : row.label === copy.retainedMatches ? (
                            <DataValue
                              source={`players.${p.role}.${p.id}.exposure.pressureMatches`}
                            />
                          ) : row.label === copy.pressureOpportunities ? (
                            <DataValue
                              source={`players.${p.role}.${p.id}.exposure.pressureEvents`}
                            />
                          ) : row.label === "Observed task" ? (
                            <DataValue
                              source={`players.${p.role}.${p.id}.task`}
                            />
                          ) : (
                            <KnownText value={String(row.value(p))} />
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <Notice title="Read the tradeoff, preserve the ordering">
            <p>
              <CopyText name="comparisonScope" />
            </p>
          </Notice>
        </>
      ) : (
        <div className="empty-state">
          <h2>Choose players to compare</h2>
          <p>
            <CopyText name="comparisonIntro" />
          </p>
        </div>
      )}
    </>
  );
}
