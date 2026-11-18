import { DataValue, CopyText, KnownText } from "@/components/data-value";
import { copy } from "@/content/copy";
import Link from "next/link";
import { ArrowUpRight, ArrowRight } from "lucide-react";
import { playerUrl, recentLabel } from "@/lib/format";
import { PlayerInitials } from "./player-initials";
import type { Player, CardPlayer } from "@/lib/types";

export function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="eyebrow">
      <span />
      {children}
    </p>
  );
}
export function PageIntro({
  kicker,
  title,
  children,
}: {
  kicker: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="page-intro">
      <Eyebrow>{kicker}</Eyebrow>
      <h1>
        <KnownText value={title} />
      </h1>
      <div className="intro-copy">{children}</div>
    </section>
  );
}
export function SectionHeading({
  index,
  title,
  detail,
}: {
  index: string;
  title: string;
  detail?: string;
}) {
  return (
    <div className="section-heading">
      <span className="section-index">{index}</span>
      <div>
        <h2>
          <KnownText value={title} />
        </h2>
        {detail && (
          <p>
            <KnownText value={detail} />
          </p>
        )}
      </div>
    </div>
  );
}
export function ActionLink({
  href,
  children,
  subtle = false,
}: {
  href: string;
  children: React.ReactNode;
  subtle?: boolean;
}) {
  return (
    <Link className={`button ${subtle ? "button-secondary" : ""}`} href={href}>
      {children}
      <ArrowUpRight size={17} />
    </Link>
  );
}
export function RecentBadge({ player }: { player: Pick<Player, "recent"> }) {
  return (
    <span
      className={`status ${player.recent.status === "adequate" ? "status-good" : "status-limited"}`}
    >
      <span />
      <KnownText value={recentLabel(player)} />
    </span>
  );
}
export function PlayerCard({ player }: { player: CardPlayer }) {
  return (
    <article className="player-card">
      <Link href={playerUrl(player)}>
        <PlayerInitials name={player.name} />
        <div className="player-card-details">
          <div className="player-card-content">
            <div className="card-kicker">
              <span>
                RANK{" "}
                <DataValue
                  source={`players.${player.role}.${player.id}.rank`}
                  format="rank"
                />
              </span>
              <ArrowUpRight size={20} />
            </div>
            <h3>
              <DataValue
                source={`players.${player.role}.${player.id}.name`}
                format="text"
              />
            </h3>
            <p className="task-label">
              <DataValue
                source={`players.${player.role}.${player.id}.task`}
                format="text"
              />
            </p>
            <div className="card-stat">
              <span>
                <CopyText name="scoreLabel" />
              </span>
              <strong>
                <DataValue
                  source={`players.${player.role}.${player.id}.rating.low`}
                  format="score"
                />
              </strong>
            </div>
            <div className="card-meta">
              <span>
                <DataValue
                  source={`players.${player.role}.${player.id}.exposure.pressureMatches`}
                  format="text"
                />{" "}
                {copy.retainedMatches.toLowerCase()}
              </span>
              <span>
                <DataValue
                  source={`players.${player.role}.${player.id}.exposure.pressureEvents`}
                  format="text"
                />{" "}
                opportunities
              </span>
            </div>
          </div>
          <div className="card-badge">
            <RecentBadge player={player} />
          </div>
        </div>
      </Link>
    </article>
  );
}
export function Notice({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <aside className="notice">
      <span className="notice-symbol" aria-hidden="true">
        i
      </span>
      <div>
        <strong>
          <KnownText value={title} />
        </strong>
        <div>{children}</div>
      </div>
    </aside>
  );
}
export function TextLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link className="text-link" href={href}>
      {children}
      <ArrowRight size={16} />
    </Link>
  );
}
