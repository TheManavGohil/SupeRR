import Link from "next/link";
import { ArrowUpRight, ArrowRight } from "lucide-react";
import { playerUrl, recentLabel, score } from "@/lib/format";
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
      <h1>{title}</h1>
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
        <h2>{title}</h2>
        {detail && <p>{detail}</p>}
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
      {recentLabel(player)}
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
              <span>RANK {String(player.rank).padStart(2, "0")}</span>
              <ArrowUpRight size={20} />
            </div>
            <h3>{player.name}</h3>
            <p className="task-label">{player.task}</p>
            <div className="card-stat">
              <span>Conservative score</span>
              <strong>{score(player.rating.low)}</strong>
            </div>
            <div className="card-meta">
              <span>{player.exposure.pressureMatches} pressure matches</span>
              <span>{player.exposure.pressureEvents} opportunities</span>
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
        <strong>{title}</strong>
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
