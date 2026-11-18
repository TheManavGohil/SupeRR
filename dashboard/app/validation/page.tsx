import Link from "next/link";
import { players, release, playerUrl } from "@/lib/data";
import {
  PageIntro,
  RecentBadge,
  Notice,
  SectionHeading,
} from "@/components/ui";
export const metadata = { title: "Validation and limitations" };
export default function Validation() {
  const picks = players
    .filter((p) => p.selected)
    .sort((a, b) => a.role.localeCompare(b.role) || a.rank - b.rank);
  return (
    <div className="page-wrap">
      <PageIntro
        kicker="RELIABILITY & LIMITATIONS"
        title="A selection should survive scrutiny."
      >
        <p>
          Keep sample adequacy, observed production and future availability
          distinct.
        </p>
      </PageIntro>
      <Notice title="Recent evidence">
        <p>
          Seven pass every standalone 2026 gate; eleven are limited; two have
          none retained.
        </p>
      </Notice>
      <section className="section">
        <SectionHeading
          index="WINDOWS"
          title="Different windows. Different questions."
        />
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Window</th>
                <th>Matches</th>
                <th>Batting rankable</th>
                <th>Bowling rankable</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th>Development</th>
                <td>{release.developmentMatches}</td>
                <td>{release.developmentBattingEligible}</td>
                <td>{release.developmentBowlingEligible}</td>
              </tr>
              <tr>
                <th>Reserved</th>
                <td>{release.reservedMatches}</td>
                <td>{release.reservedBattingEligible}</td>
                <td>{release.reservedBowlingEligible}</td>
              </tr>
              <tr>
                <th>Final</th>
                <td>{release.matches}</td>
                <td>{release.battingEligible}</td>
                <td>{release.bowlingEligible}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p>
          Prior aggregate recent-year EDA was seen. The reserved evaluation is
          retrospective; historical predictive models failed calibration gates.
        </p>
      </section>
      <section className="section">
        <SectionHeading
          index="RECENCY"
          title="Recent evidence, player by player."
        />
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Selection</th>
                <th>Role / rank</th>
                <th>Standalone evidence</th>
              </tr>
            </thead>
            <tbody>
              {picks.map((p) => (
                <tr key={p.id}>
                  <th>
                    <Link href={playerUrl(p)}>{p.name}</Link>
                  </th>
                  <td>
                    {p.role} / {p.rank}
                  </td>
                  <td>
                    <RecentBadge player={p} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="section">
        <SectionHeading
          index="WEIGHTS"
          title="What changes when preferences change?"
        />
        <div className="two-col">
          {(["batting", "bowling"] as const).map((role) => (
            <div className="panel" key={role}>
              <h3>{role} top-ten overlap</h3>
              <p>
                50 / 50 runs / wickets:{" "}
                {release.weightOverlap[role].runs_wickets_50_50} /{" "}
                {release.topCount}
              </p>
              <p>
                70 / 30 runs / wickets:{" "}
                {release.weightOverlap[role].runs_wickets_70_30} /{" "}
                {release.topCount}
              </p>
            </div>
          ))}
        </div>
        <p>
          The level/change companions remain withheld because their change
          component is unreliable.
        </p>
      </section>
      <Notice title="Interpretation limits">
        <p>
          Source gaps, broad context definitions and incomplete venue/opposition
          adjustment qualify the ordering. Match-sampling uncertainty cannot
          account for missing-source bias.
        </p>
      </Notice>
    </div>
  );
}
