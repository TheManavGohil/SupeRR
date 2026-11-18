import { ScoreScope } from "@/components/score-scope";
import { DataValue, CopyText, KnownText } from "@/components/data-value";
import { copy, contribution } from "@/content/copy";
import Link from "next/link";
import { selected, playerUrl } from "@/lib/data";
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
          <th>
            <CopyText name="scoreLabel" />
          </th>
          <th>
            <CopyText name="retainedMatches" />
          </th>
        </tr>
      </thead>
      <tbody>
        {picks.map((p) => (
          <tr key={p.id}>
            <td>
              <DataValue
                source={`players.${p.role}.${p.id}.rank`}
                format="text"
              />
            </td>
            <th>
              <DataValue
                source={`players.${p.role}.${p.id}.name`}
                format="text"
              />
            </th>
            <td>
              <DataValue
                source={`players.${p.role}.${p.id}.rating.low`}
                format="score"
              />
            </td>
            <td>
              <DataValue
                source={`players.${p.role}.${p.id}.exposure.pressureMatches`}
                format="text"
              />
              {p.exposure.peerSupportedMatches !==
                p.exposure.pressureMatches && (
                <small>
                  <DataValue
                    source={`players.${p.role}.${p.id}.exposure.peerSupportedMatches`}
                    format="text"
                  />{" "}
                  <CopyText name="peerSupported" />
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
        <p>
          <CopyText name="reportIntro" />
        </p>
      </PageIntro>
      <ReportActions />
      <article className="report-document">
        <p className="report-kicker">
          <CopyText name="reportKicker" />
        </p>
        <h1>
          The Pressure Index.
          <br />
          Evidence behind every pick.
        </h1>
        <p className="report-meta">
          <CopyText name="reportMeta" /> Release:{" "}
          <DataValue source="release.id" format="text" />.
        </p>
        <h2>Final ordered lists</h2>
        <h3>
          <CopyText name="battingListTitle" />
        </h3>
        <RankTable picks={selected("batting")} />
        <h3>
          <CopyText name="bowlingListTitle" />
        </h3>
        <RankTable picks={selected("bowling")} />
        <div className="report-limits">
          <p>
            <CopyText name="eligibility" />
          </p>
        </div>
        <ScoreScope />
        <h2 className="report-new-page">How the ratings were constructed</h2>
        {methodSections.map((s) => (
          <section key={s.id}>
            <h3>
              <KnownText value={s.title} />
            </h3>
            <p>
              <KnownText value={s.intro} />
            </p>
            <ul>
              {s.points.map((t) => (
                <li key={t}>
                  <KnownText value={t} />
                </li>
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
        <h2 className="report-new-page">
          <CopyText name="reportReliability" />
        </h2>
        <p>
          <CopyText name="reportMethod" />
        </p>
        <p>
          <CopyText name="scoreScopeAdjustment" /> <CopyText name="examples" />
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
        <p className="print-only">
          <CopyText name="authorship" />
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
        <DataValue source={`players.${p.role}.${p.id}.rank`} format="text" />.{" "}
        <DataValue source={`players.${p.role}.${p.id}.name`} format="text" /> —{" "}
        <DataValue source={`players.${p.role}.${p.id}.task`} format="text" />
      </h3>
      <p>
        <CopyText name="scoreLabel" />{" "}
        <DataValue
          source={`players.${p.role}.${p.id}.rating.low`}
          format="score"
        />{" "}
        ·{" "}
        <DataValue
          source={`players.${p.role}.${p.id}.exposure.pressureMatches`}
          format="text"
        />{" "}
        retained matches ·{" "}
        <DataValue
          source={`players.${p.role}.${p.id}.exposure.pressureEvents`}
          format="text"
        />{" "}
        pressure opportunities.
      </p>
      <p>
        <KnownText value={contribution(p.task)} />
      </p>
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
