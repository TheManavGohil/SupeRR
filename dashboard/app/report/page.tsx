import { copy, contribution } from "@/content/copy";
import Link from "next/link";
import { selected, release, score, playerUrl } from "@/lib/data";
import { methodSections } from "@/content/method";
import { PageIntro, RecentBadge } from "@/components/ui";
import { ReportActions } from "@/components/report-actions";
import type { Player } from "@/lib/types";
export const metadata = {
  title: "Complete submission report",
  alternates: { canonical: "/report" },
};
function RankTable({ picks }: { picks: Player[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Player</th>
          <th>{copy.scoreLabel}</th>
          <th>{copy.retainedMatches}</th>
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
                <small>
                  {p.exposure.peerSupportedMatches} {copy.peerSupported}
                </small>
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
      <PageIntro kicker="THE SUBMISSION DOCUMENT" title={copy.reportTitle}>
        <p>{copy.reportIntro}</p>
      </PageIntro>
      <ReportActions />
      <article className="report-document">
        <p className="report-kicker">{copy.reportKicker}</p>
        <h1>
          The Pressure Index.
          <br />
          Evidence behind every pick.
        </h1>
        <p className="report-meta">
          {copy.reportMeta} Release: {release.id}.
        </p>
        <h2>Final ordered lists</h2>
        <h3>Top ten batters</h3>
        <RankTable picks={selected("batting")} />
        <h3>Top ten bowlers</h3>
        <RankTable picks={selected("bowling")} />
        <div className="report-limits">
          <p>{copy.eligibility}</p>
          <p>{copy.scoreScopeProduction}</p>
        </div>
        <h2 className="report-new-page">How the ratings were constructed</h2>
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
        <h2 className="report-new-page">Why each batter is selected</h2>
        {selected("batting").map((p) => (
          <Selection key={p.id} player={p} />
        ))}
        <h2 className="report-new-page">Why each bowler is selected</h2>
        {selected("bowling").map((p) => (
          <Selection key={p.id} player={p} />
        ))}
        <h2 className="report-new-page">{copy.reportReliability}</h2>
        <p>{copy.reportMethod}</p>
        <p>
          {copy.scoreScopeAdjustment} {copy.examples}
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
        <p>{copy.authorship}</p>
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
        {copy.scoreLabel} {score(p.rating.low)} · {p.exposure.pressureMatches}{" "}
        retained matches · {p.exposure.pressureEvents} pressure opportunities.
      </p>
      <p>{contribution(p.task)}</p>
      <p>
        {p.eligibility.primary ? copy.eligible : copy.ineligible}{" "}
        <RecentBadge player={p} />
      </p>
      <p>
        <Link href={playerUrl(p)}>Interactive aggregate evidence</Link>.
      </p>
    </section>
  );
}
