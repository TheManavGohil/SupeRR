import Link from "next/link";
import {
  ArrowDown,
  ArrowUpRight,
  Crosshair,
  Layers3,
  ShieldCheck,
} from "lucide-react";
import { selected, release, score, playerUrl } from "@/lib/data";
import { Portrait } from "@/components/portrait";
import {
  ActionLink,
  Eyebrow,
  Notice,
  PlayerCard,
  SectionHeading,
  TextLink,
} from "@/components/ui";

export default function Home() {
  const batters = selected("batting"),
    bowlers = selected("bowling");
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <Eyebrow>SUPERR SELECTOR SEASON 2 · ROUND 1</Eyebrow>
          <h1>
            WHEN THE
            <br />
            GAME GETS
            <br />
            <span>TIGHT.</span>
          </h1>
          <p className="hero-deck">
            Ten batters. Ten bowlers.
            <br />
            <strong>The evidence behind every pick.</strong>
          </p>
          <div className="hero-actions">
            <ActionLink href="/rankings/batting">
              Explore the selections
            </ActionLink>
            <TextLink href="/methodology">See the method</TextLink>
          </div>
          <div className="hero-footnote">
            <span className="live-dot" />
            FROZEN AT 01 NOV 2026 <span> / </span> RETROSPECTIVE ANALYSIS
          </div>
        </div>
        <div className="hero-art">
          <span className="hero-art-label">PERFORMANCE / UNDER PRESSURE</span>
          <span className="hero-big-type" aria-hidden="true">
            01
          </span>
          <div className="hero-portrait">
            <Portrait player={batters[0]} hero />
          </div>
          <Link href={playerUrl(batters[0])} className="hero-player-caption">
            <div>
              <span>BATTING RANK 01</span>
              <h2>TIM DAVID</h2>
              <p>Late-over scoring · 66 pressure matches</p>
            </div>
            <ArrowUpRight />
          </Link>
          <div className="floating-score">
            <span>CONSERVATIVE SCORE</span>
            <strong>{score(batters[0].rating.low)}</strong>
            <small>10th-percentile selection statistic</small>
          </div>
          <div className="hero-index" aria-hidden="true">
            EVIDENCE
            <br />
            OVER INSTINCT.
          </div>
        </div>
      </section>
      <div className="scope-strip">
        <div>
          <strong>{release.matches}</strong>
          <span>verified matches</span>
        </div>
        <div>
          <strong>121,891</strong>
          <span>delivery events</span>
        </div>
        <div>
          <strong>20</strong>
          <span>selected player-role entries</span>
        </div>
        <div>
          <strong>1,000</strong>
          <span>whole-match resamples</span>
        </div>
        <a href="#selections" aria-label="Scroll to selections">
          <ArrowDown />
        </a>
      </div>
      <section id="selections" className="section">
        <div className="heading-with-action">
          <SectionHeading
            index="01"
            title="The players. The proof."
            detail="Two ranked lists, with every selection open to scrutiny."
          />
          <Link href="/rankings/batting" className="text-link">
            All batting selections <ArrowUpRight size={16} />
          </Link>
        </div>
        <div className="selection-strip">
          <h3>
            Batting <span>TOP 03 / 10</span>
          </h3>
          <TextLink href="/rankings/batting">See all ten</TextLink>
        </div>
        <div className="player-grid">
          {batters.slice(0, 3).map((p) => (
            <PlayerCard key={p.id} player={p} />
          ))}
        </div>
        <div className="selection-strip">
          <h3>
            Bowling <span>TOP 03 / 10</span>
          </h3>
          <TextLink href="/rankings/bowling">See all ten</TextLink>
        </div>
        <div className="player-grid">
          {bowlers.slice(0, 3).map((p) => (
            <PlayerCard key={p.id} player={p} />
          ))}
        </div>
      </section>
      <section className="method-preview section">
        <div>
          <Eyebrow>THE SELECTION LOGIC</Eyebrow>
          <h2>
            Great moments
            <br />
            need <em>strong evidence.</em>
          </h2>
          <p>
            Pressure is defined before the ball. Performance is compared with
            other players in similar measured contexts. Consistency and
            counterexamples travel with every recommendation.
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
              copy: "Late overs, a wicket collapse or a tight chase. One frozen rule for batting and bowling.",
            },
            {
              icon: Layers3,
              title: "Compare the contribution",
              copy: "Scoring and dismissal risk. Concessions and wickets. Contemporaneous peers with the player left out.",
            },
            {
              icon: ShieldCheck,
              title: "Challenge the selection",
              copy: "Whole-match uncertainty, season checks, close alternatives and the matches that tell the other side.",
            },
          ].map((x, i) => (
            <div className="process-card" key={x.title}>
              <span className="process-number">0{i + 1}</span>
              <x.icon size={23} />
              <h3>{x.title}</h3>
              <p>{x.copy}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="section reality-section">
        <SectionHeading
          index="02"
          title="The qualification matters."
          detail="A multi-year record and current form answer different questions."
        />
        <div className="reality-grid">
          <div className="reality-number">
            07<span>/ 20</span>
          </div>
          <div>
            <h3>
              Seven selected entries meet every standalone 2026 rating
              requirement.
            </h3>
            <p>
              Two have no retained 2026 pressure observations. Every profile
              shows what the recent evidence can support, alongside the longer
              record.
            </p>
            <TextLink href="/validation">Inspect temporal evidence</TextLink>
          </div>
        </div>
        <Notice title="A transparent pressure index">
          <p>
            These are descriptive rankings of retained IPL and T20I evidence.
            Venue, opposition strength and fine chase difficulty remain
            incompletely measured. Current availability and IPL 2027 performance
            are separate questions.
          </p>
        </Notice>
      </section>
      <section className="closing-cta">
        <Eyebrow>EVERY PICK HAS A CASE</Eyebrow>
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
