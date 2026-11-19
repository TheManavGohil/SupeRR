import { ScoreScope } from "@/components/score-scope";
import { DataValue, CopyText } from "@/components/data-value";
import Link from "next/link";
import {
  ArrowDown,
  ArrowUpRight,
  Crosshair,
  Layers3,
  ShieldCheck,
} from "lucide-react";
import { selected, playerUrl } from "@/lib/data";
import site from "@/content/generated/site.json";
import { copy } from "@/content/copy";
import { PlayerPortrait } from "@/components/player-portrait";
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
          <Eyebrow>
            <CopyText name="homeKicker" />
          </Eyebrow>
          <h1>
            WHEN THE
            <br />
            GAME GETS
            <br />
            <span>TIGHT.</span>
          </h1>
          <p className="hero-deck">
            <CopyText name="homeDeck" />
            <br />
            <strong>
              <CopyText name="homeProof" />
            </strong>
          </p>
          <div className="hero-actions">
            <ActionLink href="/rankings/batting">
              Explore the selections
            </ActionLink>
            <TextLink href="/methodology">See the method</TextLink>
          </div>
          <div className="hero-footnote">
            <span className="live-dot" />
            <CopyText name="frozen" />
          </div>
        </div>
        <div className="hero-art">
          <span className="hero-art-label">PERFORMANCE / UNDER PRESSURE</span>
          <div className="hero-portrait">
            <PlayerPortrait player={batters[0]} variant="hero" />
          </div>
          <Link href={playerUrl(batters[0])} className="hero-player-caption">
            <div>
              <span>
                <CopyText name="heroRank" />{" "}
                <DataValue
                  source={`players.${batters[0].role}.${batters[0].id}.rank`}
                  format="rank"
                />
              </span>
              <h2>
                <DataValue
                  source={`players.${batters[0].role}.${batters[0].id}.name`}
                  format="text"
                />
              </h2>
              <p>
                <DataValue
                  source={`players.${batters[0].role}.${batters[0].id}.task`}
                  format="text"
                />{" "}
                ·{" "}
                <DataValue
                  source={`players.${batters[0].role}.${batters[0].id}.exposure.pressureMatches`}
                  format="text"
                />{" "}
                {copy.retainedMatches.toLowerCase()}
              </p>
            </div>
            <ArrowUpRight />
          </Link>
          <div className="floating-score">
            <span>
              <CopyText name="scoreLabel" />
            </span>
            <strong>
              <DataValue
                source={`players.${batters[0].role}.${batters[0].id}.rating.low`}
                format="score"
              />
            </strong>
            <small>
              <CopyText name="heroMetric" />
            </small>
          </div>
        </div>
      </section>
      <div className="scope-strip">
        <div>
          <strong>
            <DataValue source="release.matches" format="text" />
          </strong>
          <span>
            <CopyText name="scopeMatches" />
          </span>
        </div>
        <div>
          <strong>
            <DataValue source="release.events" format="integer" />
          </strong>
          <span>
            <CopyText name="scopeEvents" />
          </span>
        </div>
        <div>
          <strong>
            <DataValue source="release.selectedTotal" format="text" />
          </strong>
          <span>
            <CopyText name="scopeSelections" />
          </span>
        </div>
        <div>
          <strong>
            <DataValue source="release.bootstrapDraws" format="integer" />
          </strong>
          <span>
            <CopyText name="scopeResamples" />
          </span>
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
                  TOP <DataValue source="site.heroPreviewCount" format="text" />{" "}
                  / <DataValue source="release.topCount" format="text" />
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
      <ScoreScope />
      <section className="method-preview section">
        <div>
          <Eyebrow>THE SELECTION LOGIC</Eyebrow>
          <h2>
            Great moments
            <br />
            need <em>strong evidence.</em>
          </h2>
          <p>
            <CopyText name="methodPreview" />
          </p>
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
            <DataValue source="release.selectedRecentAdequate" format="text" />
            <span>
              / <DataValue source="release.selectedTotal" format="text" />
            </span>
          </div>
          <div>
            <h3>
              <CopyText name="eligibility" />
            </h3>
            <p>
              <CopyText name="scoreScopeFuture" />
            </p>
            <TextLink href="/validation">Inspect temporal evidence</TextLink>
          </div>
        </div>
        <Notice title="A transparent pressure index">
          <p>
            <CopyText name="sourceGaps" />
          </p>
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
