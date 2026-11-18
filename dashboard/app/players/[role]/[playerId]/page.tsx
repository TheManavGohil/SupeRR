import Link from "next/link";
import { notFound } from "next/navigation";
import { players, findPlayer, playerUrl, score } from "@/lib/data";
import { PlayerInitials } from "@/components/player-initials";
import { Notice, RecentBadge, SectionHeading } from "@/components/ui";
export const dynamicParams = false;
export function generateStaticParams() {
  return players.map((p) => ({ role: p.role, playerId: p.id }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ role: string; playerId: string }>;
}) {
  const { role, playerId } = await params;
  const p = findPlayer(role, playerId);
  return { title: p ? `${p.name} — Aggregate evidence` : "Player unavailable" };
}
export default async function Profile({
  params,
}: {
  params: Promise<{ role: string; playerId: string }>;
}) {
  const { role, playerId } = await params;
  const p = findPlayer(role, playerId);
  if (!p) notFound();
  const alternatives = players
    .filter((q) => q.role === p.role && q.id !== p.id)
    .sort((a, b) => Math.abs(a.rank - p.rank) - Math.abs(b.rank - p.rank))
    .slice(0, 3);
  return (
    <div className="page-wrap">
      <Link href={`/rankings/${p.role}`} className="back-link">
        ← Back to {p.role} selections
      </Link>
      <section className="profile-hero">
        <div>
          <p className="eyebrow">
            {p.selected ? "FINAL SELECTION" : "COMPARISON CANDIDATE"} · RANK{" "}
            {p.rank}
          </p>
          <h1>{p.name}</h1>
          <p className="task-label">{p.task}</p>
          <p className="profile-lede">
            The frozen ordering balances scoring and wicket outcomes against
            supported peers. Read the observed task and evidence status
            alongside the rank.
          </p>
          <RecentBadge player={p} />
        </div>
        <div className="profile-portrait">
          <PlayerInitials name={p.name} />
        </div>
      </section>
      <div className="profile-summary">
        <div className="metric">
          <span>Conservative score</span>
          <strong>{score(p.rating.low)}</strong>
        </div>
        <div className="metric">
          <span>Retained matches</span>
          <strong>{p.exposure.pressureMatches}</strong>
          <small>
            {p.exposure.peerSupportedMatches !== p.exposure.pressureMatches
              ? `${p.exposure.peerSupportedMatches} peer-supported`
              : null}
          </small>
        </div>
        <div className="metric">
          <span>Pressure opportunities</span>
          <strong>{p.exposure.pressureEvents}</strong>
        </div>
      </div>
      <section className="evidence-section" id="task">
        <SectionHeading index="TASK" title="Read the task before the rank." />
        <p>
          {p.task}. This is an observed workload label; squad fit and
          availability need separate review.
        </p>
      </section>
      <section className="evidence-section" id="performance">
        <SectionHeading
          index="EVIDENCE"
          title="Aggregate evidence, with a clear boundary."
        />
        <p>
          The score describes retained production relative to supported peers.
          Sample size and the recent-evidence label qualify its interpretation.
        </p>
        <p>Examples are available on request.</p>
      </section>
      <section className="evidence-section" id="usual">
        <SectionHeading
          index="SCOPE"
          title="The usual-performance comparison."
        />
        <Notice title="Reliable change estimate: unavailable.">
          <p>
            Ordinary and pressure contexts do not provide reliable matched
            comparisons for the final selections. Missing change is not a
            negative performance score.
          </p>
        </Notice>
      </section>
      <section className="evidence-section" id="alternatives">
        <SectionHeading
          index="COMPARE"
          title="Read the neighbouring decisions."
          detail="Adjacent frozen ranks are navigation aids, rather than claims of tactical similarity."
        />
        <div className="two-col">
          {alternatives.map((q) => (
            <Link key={q.id} className="panel" href={playerUrl(q)}>
              #{q.rank} {q.name} · {q.task}
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
