import Link from "next/link";
import { players, release, playerUrl, num } from "@/lib/data";
import {
  PageIntro,
  Notice,
  SectionHeading,
  RecentBadge,
} from "@/components/ui";
export const metadata = { title: "Validation and limitations" };
export default function Validation() {
  const picks = players
    .filter((p) => p.selected)
    .sort((a, b) => a.role.localeCompare(b.role) || a.rank - b.rank);
  return (
    <div className="page-wrap" style={{ paddingBottom: 70 }}>
      <PageIntro
        kicker="RELIABILITY & LIMITATIONS"
        title="A selection should survive scrutiny."
      >
        <p>
          What the checks establish, where the evidence is thin, and why
          uncertainty stays attached to the recommendation.
        </p>
      </PageIntro>
      <div className="validation-stats">
        <div className="validation-stat">
          <strong>07/20</strong>
          <span>Full standalone 2026 requirements met</span>
          <p>
            Multi-year eligibility does not establish current form for every
            selection.
          </p>
        </div>
        <div className="validation-stat">
          <strong>02</strong>
          <span>No retained 2026 pressure evidence</span>
          <p>
            Recent observations are absent; historical evidence remains
            distinct.
          </p>
        </div>
        <div className="validation-stat">
          <strong>0</strong>
          <span>Reliable final change intervals</span>
          <p>Conditional level/change rankings remain unavailable.</p>
        </div>
      </div>
      <section className="section">
        <SectionHeading
          index="01"
          title="Different windows. Different questions."
          detail="Development formed the method; the final window applied it without retuning."
        />
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Window</th>
                <th>Matches</th>
                <th>Batting rankable</th>
                <th>Bowling rankable</th>
                <th>Interpretation</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th>Development · 2023–2025</th>
                <td>402</td>
                <td>62</td>
                <td>90</td>
                <td>Method feasibility and review</td>
              </tr>
              <tr>
                <th>Reserved · 2026 to cutoff</th>
                <td>109</td>
                <td>6</td>
                <td>28</td>
                <td>Same-year retrospective check</td>
              </tr>
              <tr>
                <th>Final · 2023 to cutoff</th>
                <td>511</td>
                <td>75</td>
                <td>104</td>
                <td>Combined selection evidence</td>
              </tr>
            </tbody>
          </table>
        </div>
        <Notice title="The reserved check retains the original sample rules">
          <p>
            A one-year batting list of ten was not forced by lowering exposure
            requirements. 2026 had prior aggregate EDA exposure, so this is not
            pristine unseen predictive validation. The protocol was committed as{" "}
            {release.protocolCommit} before reserved performance access.
          </p>
        </Notice>
      </section>
      <section className="section" style={{ paddingTop: 0 }}>
        <SectionHeading
          index="02"
          title="Recent evidence, player by player."
          detail="Insufficient sample or coverage is an unavailable claim, not a negative performance score."
        />
        <div className="table-scroll">
          <table style={{ minWidth: 650 }}>
            <thead>
              <tr>
                <th>Selection</th>
                <th>Role / rank</th>
                <th>2026 opportunities</th>
                <th>2026 pressure matches</th>
                <th>Standalone evidence</th>
              </tr>
            </thead>
            <tbody>
              {picks.map((p) => (
                <tr key={p.role + p.id}>
                  <th>
                    <Link href={playerUrl(p)}>{p.name}</Link>
                  </th>
                  <td>
                    {p.role} / {p.rank}
                  </td>
                  <td>{p.recent.events}</td>
                  <td>{p.recent.matches}</td>
                  <td>
                    <RecentBadge player={p} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="section" style={{ paddingTop: 0 }}>
        <SectionHeading
          index="03"
          title="What changes when preferences change?"
          detail="Registered outcome-weight variants share the same eligible cohort and match draws."
        />
        <div className="two-col">
          <div className="panel">
            <h3>Batting top-ten overlap</h3>
            <div className="profile-summary">
              <div className="metric">
                <span>50 / 50 runs / wickets</span>
                <strong>10 / 10</strong>
              </div>
              <div className="metric">
                <span>70 / 30 runs / wickets</span>
                <strong>8 / 10</strong>
              </div>
            </div>
            <p>
              The declared default remains 60 / 40. Membership and exact ranks
              can depend on the cricket tradeoff.
            </p>
          </div>
          <div className="panel">
            <h3>Bowling top-ten overlap</h3>
            <div className="profile-summary">
              <div className="metric">
                <span>50 / 50 runs / wickets</span>
                <strong>9 / 10</strong>
              </div>
              <div className="metric">
                <span>70 / 30 runs / wickets</span>
                <strong>9 / 10</strong>
              </div>
            </div>
            <p>
              Profiles show every registered variant. An appealing alternative
              ordering does not replace the default.
            </p>
          </div>
        </div>
        <Notice title="Separate sensitivities from unavailable companions">
          <p>
            These weights trade runs against wickets. The 70/30 and 50/50
            pressure-level/usual-change companions are a separate concept,
            withheld because their change component is unreliable.
          </p>
        </Notice>
      </section>
      <section className="section" style={{ paddingTop: 0 }}>
        <SectionHeading index="04" title="Coverage is part of the argument." />
        <div className="two-col">
          <div className="panel">
            <h3>From source to retained evidence</h3>
            <p>
              883 supplied matches → 651 completely verified matches across
              available years → 511 verified scoring-window matches.
            </p>
            <p>
              Final dossier population: 93 batting / 150 bowling level-sample
              entries. Final sample, coverage and uncertainty gates retain 75 /
              104 for the primary ordering.
            </p>
            <p>
              The difference between 651 and 511 includes the scoring-window
              restriction, rather than a new ranking-driven exclusion.
            </p>
          </div>
          <div className="panel">
            <h3>What source gaps leave unmeasured</h3>
            <p>
              Verified delivery retention in the full source audit is 92.50% for
              IPL and 70.24% for T20I. These are full-audit rates, not the
              final-window per-player opportunity retentions.
            </p>
            <p>
              Profiles show role/window-specific source retention. Unresolved or
              missing-source evidence cannot be interpreted as weak performance.
            </p>
          </div>
        </div>
      </section>
      <section className="section" style={{ paddingTop: 0 }}>
        <SectionHeading
          index="05"
          title="Why the final estimator is descriptive."
          detail="Actual predictive experiments informed a documented decision; failed calibration gates remain failed."
        />
        <div className="timeline">
          <div>
            <h3>Historical peer baseline</h3>
            <p>
              Fifteen fold/setting bundles. Predictive loss improved over simple
              means, but 29 overlapping material calibration alerts blocked
              promotion.
            </p>
          </div>
          <div>
            <h3>One contextual revision</h3>
            <p>
              Three bundles added verified pre-ball context. Run predictions
              improved and alerts fell to 18; the unchanged calibration gate
              still failed.
            </p>
          </div>
          <div>
            <h3>Retrospective peer reference</h3>
            <p>
              Two development bundles. Zero pooled alerts concealed 68
              separate-fold alerts, including opposite-direction biases.
            </p>
          </div>
          <div>
            <h3>Observed dossiers and approved pressure index</h3>
            <p>
              Automatic experimentation stopped at 20 bundles. Validated player
              evidence supported one explicit descriptive method decision,
              frozen before reserved evaluation. No failed predictive model was
              promoted.
            </p>
          </div>
        </div>
      </section>
      <section className="section" style={{ paddingTop: 0 }}>
        <SectionHeading index="06" title="What remains uncertain." />
        <div className="prose">
          <ul>
            <li>
              Venue, opposition strength and fine chase difficulty are
              incompletely measured.
            </li>
            <li>
              Late-over ordinary controls are absent; a global
              pressure-minus-ordinary interpretation is unsupported.
            </li>
            <li>
              Small or single-season histories can qualify while remaining weak
              evidence for long-term repeatability.
            </li>
            <li>
              Bootstrap intervals condition on retained observations, frozen
              support and development scales. They do not represent
              missing-source uncertainty.
            </li>
            <li>
              Close boundary intervals overlap; exact ranks are not certain
              superiority statements.
            </li>
            <li>
              No current availability, auction price, squad vacancy or IPL 2027
              forecast follows from these rankings.
            </li>
          </ul>
          <p>
            The pressure definition flags {num(release.pressureShare, 2)}% of
            final events. Its breadth and the limits above are part of the
            selection argument.
          </p>
        </div>
      </section>
    </div>
  );
}
