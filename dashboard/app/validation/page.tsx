import { DataValue, CopyText } from "@/components/data-value";

import Link from "next/link";
import { players, playerUrl } from "@/lib/data";
import {
  PageIntro,
  RecentBadge,
  Notice,
  SectionHeading,
} from "@/components/ui";
export const metadata = {
  title: "Validation and limitations",
  alternates: { canonical: "/validation" },
};
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
          <CopyText name="validationIntro" />
        </p>
      </PageIntro>
      <Notice title="Recent evidence">
        <p>
          <CopyText name="eligibility" />
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
                <td>
                  <DataValue
                    source="release.developmentMatches"
                    format="text"
                  />
                </td>
                <td>
                  <DataValue
                    source="release.developmentBattingEligible"
                    format="text"
                  />
                </td>
                <td>
                  <DataValue
                    source="release.developmentBowlingEligible"
                    format="text"
                  />
                </td>
              </tr>
              <tr>
                <th>Reserved</th>
                <td>
                  <DataValue source="release.reservedMatches" format="text" />
                </td>
                <td>
                  <DataValue
                    source="release.reservedBattingEligible"
                    format="text"
                  />
                </td>
                <td>
                  <DataValue
                    source="release.reservedBowlingEligible"
                    format="text"
                  />
                </td>
              </tr>
              <tr>
                <th>Final</th>
                <td>
                  <DataValue source="release.matches" format="text" />
                </td>
                <td>
                  <DataValue source="release.battingEligible" format="text" />
                </td>
                <td>
                  <DataValue source="release.bowlingEligible" format="text" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p>
          <CopyText name="retrospective" />
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
                    <Link href={playerUrl(p)}>
                      <DataValue
                        source={`players.${p.role}.${p.id}.name`}
                        format="text"
                      />
                    </Link>
                  </th>
                  <td>
                    {p.role} /{" "}
                    <DataValue
                      source={`players.${p.role}.${p.id}.rank`}
                      format="text"
                    />
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
                <CopyText name="weightEqual" />:{" "}
                <DataValue
                  source={`release.weightOverlap.${role}.runs_wickets_50_50`}
                />{" "}
                / <DataValue source="release.topCount" format="text" />
              </p>
              <p>
                <CopyText name="weightRuns" />:{" "}
                <DataValue
                  source={`release.weightOverlap.${role}.runs_wickets_70_30`}
                />{" "}
                / <DataValue source="release.topCount" format="text" />
              </p>
            </div>
          ))}
        </div>
        <p>
          <CopyText name="companions" />
        </p>
      </section>
      <Notice title="Interpretation limits">
        <p>
          <CopyText name="sourceGaps" />
        </p>
      </Notice>
    </div>
  );
}
