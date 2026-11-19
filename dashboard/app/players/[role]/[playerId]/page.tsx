import { DataValue, CopyText, KnownText } from "@/components/data-value";
import { copy, contribution } from "@/content/copy";
import Link from "next/link";
import { notFound } from "next/navigation";
import { players, findPlayer, playerUrl } from "@/lib/data";
import { PlayerPortrait } from "@/components/player-portrait";
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
  return {
    title: p ? `${p.name} — Aggregate evidence` : "Player unavailable",
    ...(p ? { alternates: { canonical: playerUrl(p) } } : {}),
  };
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
            <DataValue
              source={`players.${p.role}.${p.id}.rank`}
              format="text"
            />
          </p>
          <h1>
            <DataValue
              source={`players.${p.role}.${p.id}.name`}
              format="text"
            />
          </h1>
          <p className="task-label">
            <DataValue
              source={`players.${p.role}.${p.id}.task`}
              format="text"
            />
          </p>
          <p className="profile-lede">
            <CopyText name="profileLead" />
          </p>
          <RecentBadge player={p} />
        </div>
        <div className="profile-portrait">
          <PlayerPortrait player={p} variant="profile" />
        </div>
      </section>
      <div className="profile-summary">
        <div className="metric">
          <span>
            <CopyText name="scoreLabel" />
          </span>
          <strong>
            <DataValue
              source={`players.${p.role}.${p.id}.rating.low`}
              format="score"
            />
          </strong>
        </div>
        <div className="metric">
          <span>
            <CopyText name="retainedMatches" />
          </span>
          <strong>
            <DataValue
              source={`players.${p.role}.${p.id}.exposure.pressureMatches`}
              format="text"
            />
          </strong>
          <small>
            <>
              {p.exposure.peerSupportedMatches !==
                p.exposure.pressureMatches && (
                <>
                  <DataValue
                    source={`players.${p.role}.${p.id}.exposure.peerSupportedMatches`}
                  />{" "}
                  <CopyText name="peerSupported" />
                </>
              )}
            </>
          </small>
        </div>
        <div className="metric">
          <span>
            <CopyText name="pressureOpportunities" />
          </span>
          <strong>
            <DataValue
              source={`players.${p.role}.${p.id}.exposure.pressureEvents`}
              format="text"
            />
          </strong>
        </div>
      </div>
      <section className="evidence-section" id="task">
        <SectionHeading index="TASK" title="Read the task before the rank." />
        <p>
          <KnownText value={contribution(p.task)} />
        </p>
      </section>
      <section className="evidence-section" id="performance">
        <SectionHeading
          index="EVIDENCE"
          title="Aggregate evidence, with a clear boundary."
        />
        <p>
          <CopyText name="aggregateEvidence" />
        </p>
        <p>
          <CopyText name="examples" />
        </p>
      </section>
      <section className="evidence-section" id="usual">
        <SectionHeading
          index="SCOPE"
          title="The usual-performance comparison."
        />
        <Notice title={copy.unavailableChange}>
          <p>
            <CopyText name="missingChange" />
          </p>
        </Notice>
      </section>
      <section className="evidence-section" id="alternatives">
        <SectionHeading
          index="COMPARE"
          title="Read the neighbouring decisions."
          detail={copy.neighbourDetail}
        />
        <div className="two-col">
          {alternatives.map((q) => (
            <Link key={q.id} className="panel" href={playerUrl(q)}>
              #
              <DataValue
                source={`players.${q.role}.${q.id}.rank`}
                format="text"
              />{" "}
              <DataValue
                source={`players.${q.role}.${q.id}.name`}
                format="text"
              />{" "}
              ·{" "}
              <DataValue
                source={`players.${q.role}.${q.id}.task`}
                format="text"
              />
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
