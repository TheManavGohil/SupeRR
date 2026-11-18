import Link from "next/link";
import { selected, release, score, num, playerUrl } from "@/lib/data";
import { methodSections } from "@/content/method";
import { PageIntro } from "@/components/ui";
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
          <th>10th percentile</th>
          <th>Point</th>
          <th>90th percentile</th>
          <th>Pressure matches</th>
        </tr>
      </thead>
      <tbody>
        {picks.map((p) => (
          <tr key={p.id}>
            <td>{p.rank}</td>
            <th>{p.name}</th>
            <td>{score(p.rating.low)}</td>
            <td>{score(p.rating.point)}</td>
            <td>{score(p.rating.high)}</td>
            <td>{p.exposure.pressureMatches}</td>
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
        <p>
          Both ordered lists, their method, supporting evidence and
          qualifications. The PDF and website share one analytical release.
        </p>
      </PageIntro>
      <ReportActions />
      <article className="report-document">
        <p className="report-kicker">
          INDEPENDENT SUPERR SELECTOR SEASON 2 SUBMISSION · ROUND 1
        </p>
        <h1>
          The Pressure Index.
          <br />
          Evidence behind every pick.
        </h1>
        <p>
          A data-driven assessment of batting and bowling under pressure, using
          the supplied IPL/T20I corpus and verified match context.
        </p>
        <div className="report-meta">
          Scoring window: 2023–1 November 2026 inclusive · 511 verified matches
          · 121,891 delivery events
          <br />
          Release: {release.id} · descriptive peer-relative method v2 · 1,000
          whole-match resamples
        </div>
        <h2>1. Final ordered lists</h2>
        <p>
          The order follows the 10th percentile of the shrunk pressure
          contribution, with declared tie-breakers. Native scores are not
          probabilities or a score out of 100.
        </p>
        <h3 style={{ marginTop: 20, marginBottom: 12 }}>Top ten batters</h3>
        <RankTable picks={selected("batting")} />
        <h3 style={{ marginTop: 25, marginBottom: 12 }}>Top ten bowlers</h3>
        <RankTable picks={selected("bowling")} />
        <div className="report-limits">
          <p>
            <strong>Material qualification:</strong> only seven selected entries
            meet all standalone 2026 rating requirements; two have no retained
            2026 pressure observations. No final supported-change interval is
            reliable. Multi-year eligibility does not establish current form or
            availability.
          </p>
        </div>
        <h2 className="report-new-page">2. How the ratings were constructed</h2>
        {methodSections.map((s, i) => (
          <section key={s.id} style={{ marginTop: 22 }}>
            <h3>
              2.{i + 1} {s.title}
            </h3>
            <p style={{ marginTop: 8 }}>{s.intro}</p>
            <ul>
              {s.points.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </section>
        ))}
        <p>
          Batting cell contribution = 0.60 × (own runs − other-player runs) /
          frozen run SD − 0.40 × (own dismissals − other-player dismissals) /
          frozen wicket SD. Bowling reverses the signs. Average by the player’s
          supported pressure mass and shrink by n_eff / (n_eff + k). Normative
          weights and regularizers are fixed, not learned ability priors.
        </p>
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
          Final primary cohorts contain 75 batting and 104 bowling entries. All
          pass the frozen 95% finite-draw rule. Complete dossiers cover all 243
          level-sample entries, including coverage-limited players. Registered
          outcome sensitivities retain 10/10 and 8/10 batting top-ten members,
          and 9/10 bowling members under both alternatives. The declared 60/40
          primary order is retained.
        </p>
        <p style={{ marginTop: 12 }}>
          No reliable supported-change companion ordering is claimed. Rates and
          selected examples do not substitute for supported comparisons.
          Match/season deletion checks are point sensitivities, not new
          bootstrap rankings. Family diagnostics do not establish
          competition-strength equivalence.
        </p>
        <p style={{ marginTop: 12 }}>
          Coverage is uneven. Venue, opposition strength and fine chase
          difficulty remain incompletely measured. Conditional match-sampling
          intervals do not include missing-source uncertainty. Close boundary
          intervals overlap, and exact places should not be read as certain
          superiority.
        </p>
        <p style={{ marginTop: 12 }}>
          Reproduction sequence: preserve input hashes; verify accepted score
          states and exclusions; apply pre-delivery pressure flags; construct
          analytical role opportunities; apply fixed eligibility/support;
          calculate leave-player-out cell contributions with development-only
          scales; recompute own and peer means in shared stratified whole-match
          draws; apply the finite-draw gate and declared ordering; generate
          fixed sensitivities and source-traceable dossiers. Protocol was frozen
          under commit {release.protocolCommit} before reserved performance
          access.
        </p>
        <h3 style={{ marginTop: 25 }}>Sources and analytical scope</h3>
        <p>
          Supplied RR competition data, reconciled against Cricsheet match
          records. <a href="https://cricsheet.org/">Cricsheet</a> data is
          attributed under the{" "}
          <a href="https://opendatacommons.org/licenses/by/1-0/">
            Open Data Commons Attribution Licence 1.0
          </a>
          . The supplied data pack and delivery ledgers are not distributed with
          this report. The match-date cutoff is distinct from an as-of
          publication archive; later-acquired reconciliation snapshots were
          used. Availability and auction strategy require separate evidence.
        </p>
        <p style={{ marginTop: 12 }}>
          The <Link href="/methodology">methodology</Link>,{" "}
          <Link href="/validation">validation overview</Link> and each linked
          player profile contain the corresponding interactive evidence.
          Analytical release {release.id}.
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
        <strong>Selection rationale:</strong> {p.editorial?.why}
      </p>
      <p>
        <strong>Counterevidence and interpretation:</strong>{" "}
        {p.editorial?.review}
      </p>
      <p>
        <strong>Qualification:</strong> {p.editorial?.caution}
      </p>
      <p>
        <strong>Potential cricket contribution:</strong>{" "}
        {p.editorial?.contribution}
      </p>
      <p>
        <strong>Exposure:</strong> {p.exposure.pressureEvents} pressure
        opportunities / {p.exposure.pressureMatches} matches; source retention{" "}
        {num(p.exposure.sourceRetention * 100)}%; {p.recent.events} retained
        2026 pressure opportunities. Conservative score {score(p.rating.low)};
        point {score(p.rating.point)}; 90th percentile {score(p.rating.high)}.{" "}
        <Link href={playerUrl(p)}>Interactive evidence</Link>.
      </p>
    </section>
  );
}
