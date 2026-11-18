import Link from "next/link";
import {
  ArrowDown,
  ArrowUpRight,
  Crosshair,
  Layers3,
  ShieldCheck,
} from "lucide-react";
import { selected, release, score, playerUrl } from "@/lib/data";
import site from "@/content/generated/site.json";
import { copy } from "@/content/copy";
import { PlayerInitials } from "@/components/player-initials";
import {
  ActionLink,
  Eyebrow,
  Notice,
  PlayerCard,
  SectionHeading,
  TextLink,
} from "@/components/ui";
export const metadata = { alternates: { canonical: "/" } };
export default function Home() {
  const batters = selected("batting"),
    bowlers = selected("bowling");
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <Eyebrow>{copy.homeKicker}</Eyebrow>
          <h1>
            WHEN THE
            <br />
            GAME GETS
            <br />
            <span>TIGHT.</span>
          </h1>
          <p className="hero-deck">
            {copy.homeDeck}
            <br />
            <strong>{copy.homeProof}</strong>
          </p>
          <div className="hero-actions">
            <ActionLink href="/rankings/batting">
              Explore the selections
            </ActionLink>
            <TextLink href="/methodology">See the method</TextLink>
          </div>
          <div className="hero-footnote">
            <span className="live-dot" />
            {copy.frozen}
          </div>
        </div>
        <div className="hero-art">
          <span className="hero-art-label">PERFORMANCE / UNDER PRESSURE</span>
          <div className="hero-portrait">
            <PlayerInitials name={batters[0].name} />
          </div>
          <Link href={playerUrl(batters[0])} className="hero-player-caption">
            <div>
              <span>
                {copy.heroRank} {String(batters[0].rank).padStart(2, "0")}
              </span>
              <h2>{batters[0].name}</h2>
              <p>
                {batters[0].task} · {batters[0].exposure.pressureMatches}{" "}
                {copy.retainedMatches.toLowerCase()}
              </p>
            </div>
            <ArrowUpRight />
          </Link>
          <div className="floating-score">
            <span>{copy.scoreLabel}</span>
            <strong>{score(batters[0].rating.low)}</strong>
            <small>{copy.heroMetric}</small>
          </div>
        </div>
      </section>
      <div className="scope-strip">
        <div>
          <strong>{release.matches}</strong>
          <span>{copy.scopeMatches}</span>
        </div>
        <div>
          <strong>{release.events.toLocaleString("en-GB")}</strong>
          <span>{copy.scopeEvents}</span>
        </div>
        <div>
          <strong>{release.selectedTotal}</strong>
          <span>{copy.scopeSelections}</span>
        </div>
        <div>
          <strong>{release.bootstrapDraws.toLocaleString("en-GB")}</strong>
          <span>{copy.scopeResamples}</span>
        </div>
        <a href="#selections" aria-label="Scroll to selections">
          <ArrowDown />
        </a>
      </div>
      <section id="selections" className="section">
        <div className="heading-with-action">
          <SectionHeading
            index="PICKS"
            title={copy.selectionsTitle}
            detail={copy.selectionsDetail}
          />
        </div>
        {(
          [
            ["Batting", batters, "batting"],
            ["Bowling", bowlers, "bowling"],
          ] as const
        ).map(([label, list, role]) => (
          <div key={role}>
            <div className="selection-strip">
              <h3>
                {label}
                <span>
                  TOP {site.heroPreviewCount} / {release.topCount}
                </span>
              </h3>
              <TextLink href={`/rankings/${role}`}>See all selections</TextLink>
            </div>
            <div className="player-grid">
              {list.slice(0, site.heroPreviewCount).map((p) => (
                <PlayerCard key={p.id} player={p} />
              ))}
            </div>
          </div>
        ))}
      </section>
      <section className="method-preview section">
        <div>
          <Eyebrow>THE SELECTION LOGIC</Eyebrow>
          <h2>
            Great moments
            <br />
            need <em>strong evidence.</em>
          </h2>
          <p>{copy.methodPreview}</p>
          <ActionLink href="/methodology" subtle>
            Follow the complete approach
          </ActionLink>
        </div>
        <div className="process-cards">
          {[
            {
              icon: Crosshair,
              title: "Define the situation",
              text: copy.processSituation,
            },
            {
              icon: Layers3,
              title: "Compare the contribution",
              text: copy.processContribution,
            },
            {
              icon: ShieldCheck,
              title: "Challenge the selection",
              text: copy.processChallenge,
            },
          ].map((x) => (
            <div className="process-card" key={x.title}>
              <x.icon size={23} />
              <h3>{x.title}</h3>
              <p>{x.text}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="section reality-section">
        <SectionHeading
          index="SCOPE"
          title={copy.realityTitle}
          detail={copy.realityDetail}
        />
        <div className="reality-grid">
          <div className="reality-number">
            {release.selectedRecentAdequate}
            <span>/ {release.selectedTotal}</span>
          </div>
          <div>
            <h3>{copy.eligibility}</h3>
            <p>{copy.scoreScopeFuture}</p>
            <TextLink href="/validation">Inspect temporal evidence</TextLink>
          </div>
        </div>
        <Notice title="A transparent pressure index">
          <p>{copy.sourceGaps}</p>
        </Notice>
      </section>
      <section className="closing-cta">
        <Eyebrow>READ THE EVIDENCE</Eyebrow>
        <h2>
          Read it.
          <br />
          <span>Challenge it.</span>
        </h2>
        <div>
          <ActionLink href="/compare">Compare the evidence</ActionLink>
          <ActionLink href="/report" subtle>
            Read the submission report
          </ActionLink>
        </div>
      </section>
    </>
  );
}
