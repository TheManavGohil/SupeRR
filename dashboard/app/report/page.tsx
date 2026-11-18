import Link from "next/link";
import { selected, release, score, playerUrl } from "@/lib/data";
import { methodSections } from "@/content/method";
import { PageIntro, RecentBadge } from "@/components/ui";
import { ReportActions } from "@/components/report-actions";
import type { Player } from "@/lib/types";
export const metadata = { title: "Complete submission report" };
function RankTable({ picks }: { picks: Player[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Player</th>
          <th>P10 score</th>
          <th>Retained matches</th>
        </tr>
      </thead>
      <tbody>
        {picks.map((p) => (
          <tr key={p.id}>
            <td>{p.rank}</td>
            <th>{p.name}</th>
            <td>{score(p.rating.low)}</td>
            <td>
              {p.exposure.pressureMatches}
              {p.exposure.peerSupportedMatches !==
                p.exposure.pressureMatches && (
                <small>{p.exposure.peerSupportedMatches} peer-supported</small>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
export default function Report() {
  return (
    <div className="page-wrap">
      <PageIntro
        kicker="THE SUBMISSION DOCUMENT"
        title="The complete selection argument."
      >
        <p>The ordered selections, shared method and aggregate evidence.</p>
      </PageIntro>
      <ReportActions />
      <article className="report-document">
        <p className="report-kicker">INDEPENDENT SUPERR SELECTOR SUBMISSION</p>
        <h1>
          The Pressure Index.
          <br />
          Evidence behind every pick.
        </h1>
        <p className="report-meta">
          Scoring window: {release.firstYear} to {release.cutoff} ·{" "}
          {release.matches} verified matches ·{" "}
          {release.events.toLocaleString("en-GB")} events. Release: {release.id}
          .
        </p>
        <h2>1. Final ordered lists</h2>
        <h3>Top ten batters</h3>
        <RankTable picks={selected("batting")} />
        <h3>Top ten bowlers</h3>
        <RankTable picks={selected("bowling")} />
        <div className="report-limits">
          <p>
            Seven pass every standalone 2026 gate; eleven are limited; two have
            none retained.
          </p>
          <p>
            Reliable pressure-versus-usual change remains unavailable. The list
            describes observed peer-relative production.
          </p>
        </div>
        <h2 className="report-new-page">2. How the ratings were constructed</h2>
        {methodSections.map((s) => (
          <section key={s.id}>
            <h3>{s.title}</h3>
            <p>{s.intro}</p>
            <ul>
              {s.points.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          </section>
        ))}
        <h2 className="report-new-page">3. Why each batter is selected</h2>
        {selected("batting").map((p) => (
          <Selection key={p.id} player={p} />
        ))}
        <h2 className="report-new-page">4. Why each bowler is selected</h2>
        {selected("bowling").map((p) => (
          <Selection key={p.id} player={p} />
        ))}
        <h2 className="report-new-page">
          5. Reliability, limitations and reproduction
        </h2>
        <p>
          The primary index uses frozen peer comparisons, sample-size shrinkage
          and whole-match resampling. Exact ranks are decisions under this
          method; they do not establish certain superiority, future form or
          availability.
        </p>
        <p>
          Venue, opposition strength and fine chase difficulty remain
          incompletely adjusted. Examples are available on request.
        </p>
        <h3>Sources and analytical scope</h3>
        <p>
          Supplied competition data was reconciled against{" "}
          <a href="https://cricsheet.org/">Cricsheet</a> records, attributed
          under the{" "}
          <a href="https://opendatacommons.org/licenses/by/1-0/">
            Open Data Commons Attribution Licence
          </a>
          . This publication contains approved aggregates.
        </p>
        <p>
          Read the <Link href="/methodology">methodology</Link> and{" "}
          <Link href="/validation">validation overview</Link>.
        </p>
      </article>
    </div>
  );
}
function Selection({ player: p }: { player: Player }) {
  return (
    <section className="report-player">
      <h3>
        {p.rank}. {p.name} — {p.task}
      </h3>
      <p>
        P10 {score(p.rating.low)} · {p.exposure.pressureMatches} retained
        matches · {p.exposure.pressureEvents} pressure opportunities.
      </p>
      <p>
        Observed workload: {p.task}. Evaluate the role alongside retained
        exposure and eligibility; this is an option for cricket review, without
        an availability claim.
      </p>
      <p>
        {p.eligibility.primary
          ? "Meets the frozen primary eligibility rules."
          : "Primary eligibility is unavailable."}{" "}
        <RecentBadge player={p} />
      </p>
      <p>
        <Link href={playerUrl(p)}>Interactive aggregate evidence</Link>.
      </p>
    </section>
  );
}
