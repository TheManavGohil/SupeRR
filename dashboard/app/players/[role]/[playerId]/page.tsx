import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ArrowUpRight } from "lucide-react";
import {
  players,
  findPlayer,
  compareUrl,
  num,
  score,
  variantLabel,
} from "@/lib/data";
import type { Player } from "@/lib/types";
import { Portrait } from "@/components/portrait";
import {
  Eyebrow,
  Notice,
  RecentBadge,
  SectionHeading,
  ActionLink,
} from "@/components/ui";
import { IntervalChart, PhaseBars, SeasonChart } from "@/components/charts";

export const dynamicParams = false;
export function generateStaticParams() {
  return players.map((p) => ({ role: p.role, playerId: p.id }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ role: string; playerId: string }>;
}) {
  const { role, playerId } = await params;
  const p = findPlayer(role, playerId);
  return {
    title: p
      ? `${p.name} — ${p.selected ? "Selection evidence" : "Comparison candidate"}`
      : "Player not found",
  };
}
function CaseCard({
  c,
  player,
}: {
  c: Player["cases"][number];
  player: Player;
}) {
  const reasons = c.case_reasons.split(";").join(" / ").replaceAll("_", " ");
  const adverse =
    player.role === "batting"
      ? /minimum_run|maximum_wicket/.test(c.case_reasons)
      : /maximum_run|minimum_wicket/.test(c.case_reasons);
  return (
    <article className="case-card">
      <span className="case-kind">
        {adverse
          ? "Counterevidence / tradeoff"
          : "Supporting / typical evidence"}
      </span>
      <h3>vs {c.opposition}</h3>
      <p className="case-date">
        {c.match_date} · {c.family} · pressure segment
      </p>
      <div className="case-stats">
        <div>
          <strong>{c.runs}</strong>
          <span>
            {player.role === "batting" ? "BATTER RUNS" : "RUNS CONCEDED"}
          </span>
        </div>
        <div>
          <strong>{c.opportunities}</strong>
          <span>OPPORTUNITIES</span>
        </div>
        <div>
          <strong>{c.wickets}</strong>
          <span>
            {player.role === "batting"
              ? "ATTRIBUTED DISMISSALS"
              : "BOWLER WICKETS"}
          </span>
        </div>
      </div>
      <p>
        Display reason: {reasons}.{" "}
        {c.small_sample
          ? "Small-sample illustration; interpret cautiously."
          : "Meets the fixed case-display exposure minimum."}
      </p>
      <p className="case-state">
        First pressure state: over {c.first_over}, {c.score_before}/
        {c.wickets_before}, {c.balls_remaining} legal balls remaining
        {c.runs_required != null ? `; ${c.runs_required} required` : ""}. These
        are segment contributions, not complete match figures.
      </p>
    </article>
  );
}

export default async function PlayerPage({
  params,
}: {
  params: Promise<{ role: string; playerId: string }>;
}) {
  const { role, playerId } = await params;
  const p = findPlayer(role, playerId);
  if (!p) notFound();
  const alternatives = p.alternatives
    .map((a) => findPlayer(p.role, a.id))
    .filter((x): x is Player => !!x);
  return (
    <div className="page-wrap">
      <Link href={`/rankings/${p.role}`} className="back-link">
        <ArrowLeft size={13} />
        Back to {p.role} selections
      </Link>
      <section className="profile-hero">
        <div>
          <Eyebrow>
            {p.selected
              ? `FINAL ${p.role.toUpperCase()} SELECTION · RANK ${String(p.rank).padStart(2, "0")}`
              : `COMPARISON CANDIDATE · COHORT RANK ${p.rank}`}
          </Eyebrow>
          <h1>{p.name}</h1>
          <p className="task-label">{p.task}</p>
          <RecentBadge player={p} />
          <p className="profile-decision">
            {p.editorial?.why ??
              "A retained comparison candidate. Inspect the same pressure contribution, source coverage and sample evidence used for the selected players."}
          </p>
          {p.editorial && (
            <p className="profile-caution">
              <strong>The strongest qualification</strong>
              {p.editorial.caution}
            </p>
          )}
          <div className="profile-actions">
            <ActionLink
              href={compareUrl(p.role, [
                p.id,
                ...alternatives.slice(0, 2).map((x) => x.id),
              ])}
            >
              Compare this evidence
            </ActionLink>
          </div>
        </div>
        <div className="profile-portrait">
          <Portrait player={p} variant="profile" />
        </div>
      </section>
      <div className="profile-summary">
        <div className="metric">
          <span>Conservative score</span>
          <strong>{score(p.rating.low)}</strong>
          <small>10th percentile · native units</small>
        </div>
        <div className="metric">
          <span>Pressure matches</span>
          <strong>{p.exposure.pressureMatches}</strong>
          <small>{p.exposure.pressureEvents} pressure opportunities</small>
        </div>
        <div className="metric">
          <span>Source retention</span>
          <strong>{num(p.exposure.sourceRetention * 100)}%</strong>
          <small>
            {p.exposure.retainedEvents} / {p.exposure.sourceEvents}{" "}
            opportunities
          </small>
        </div>
        <div className="metric">
          <span>2026 pressure exposure</span>
          <strong>{p.recent.events}</strong>
          <small>{p.recent.matches} pressure matches</small>
        </div>
      </div>
      <nav className="profile-nav" aria-label="Player evidence sections">
        {[
          ["task", "Observed task"],
          ["performance", "Performance"],
          ["repeatability", "Repeatability"],
          ["cases", "Counterexamples"],
          ["usual", "Usual performance"],
          ["alternatives", "Alternatives"],
        ].map(([id, label]) => (
          <a key={id} href={`#${id}`}>
            {label}
          </a>
        ))}
      </nav>
      <section className="evidence-section" id="task">
        <SectionHeading
          index="01"
          title="The task behind the numbers."
          detail="Overall workload and the pressure subset are different views of the same player."
        />
        <div className="two-col">
          <div className="panel">
            <h3>All observed opportunities</h3>
            <p>
              Where the player actually contributed across the retained
              evidence.
            </p>
            <PhaseBars player={p} />
          </div>
          <div className="panel">
            <h3>Pressure opportunities only</h3>
            <p>
              The workload underlying the pressure index, without inferring a
              tactical assignment.
            </p>
            <PhaseBars player={p} pressure />
          </div>
        </div>
      </section>
      <section className="evidence-section" id="performance">
        <SectionHeading
          index="02"
          title="Performance, with the tradeoff."
          detail="Runs and wickets are evaluated together. All rates below use analytical opportunities."
        />
        <IntervalChart players={[p]} />
        <div className="two-col" style={{ marginTop: 24 }}>
          <div className="panel">
            <h3>
              {p.role === "batting"
                ? "Scoring contribution"
                : "Concession control"}
            </h3>
            <div className="metric">
              <span>
                {p.role === "batting" ? "Batter runs" : "Conceded runs"} per 100
                pressure opportunities
              </span>
              <strong>{num(p.pressure.runs_per_100)}</strong>
              <small>
                {p.pressure.runs} runs across {p.exposure.pressureEvents}{" "}
                opportunities
              </small>
            </div>
            <p>
              {p.role === "batting"
                ? "Higher scoring is favourable, interpreted alongside dismissal risk."
                : "Lower concessions are favourable, interpreted alongside wicket contribution."}
            </p>
          </div>
          <div className="panel">
            <h3>
              {p.role === "batting"
                ? "Wicket preservation"
                : "Wicket contribution"}
            </h3>
            <div className="metric">
              <span>
                {p.role === "batting"
                  ? "Attributed dismissals"
                  : "Bowler wickets"}{" "}
                per 100 pressure opportunities
              </span>
              <strong>{num(p.pressure.wickets_per_100)}</strong>
              <small>{p.pressure.wickets} credited outcomes</small>
            </div>
            <p>
              {p.role === "batting"
                ? "Bowler-attributable striker dismissals; run-outs and other excluded dismissals are not counted in this metric."
                : "Bowler-credited wickets; run-outs are excluded. Concessions exclude byes, leg-byes and penalties."}
            </p>
          </div>
        </div>
        <Notice title="Analytical rates">
          <p>
            Batting excludes wides and includes no-balls; bowling uses every
            delivery attempt. These rates are not official strike rate or
            economy. The rating uses recency-weighted cell means and fixed
            development scales, rather than simply subtracting the rates shown
            here.
          </p>
        </Notice>
      </section>
      <section className="evidence-section" id="repeatability">
        <SectionHeading
          index="03"
          title="Does the evidence repeat?"
          detail="Season exposure, competition context and deletion checks qualify the headline."
        />
        <div className="two-col">
          <div className="panel">
            <h3>Across seasons</h3>
            <SeasonChart player={p} />
          </div>
          <div className="panel">
            <h3>When a match is removed</h3>
            <p>
              Recomputed point estimate across deletions of the player’s
              pressure matches:
            </p>
            <div className="metric">
              <strong>
                {score(p.repeatability.matchPointLow)} —{" "}
                {score(p.repeatability.matchPointHigh)}
              </strong>
              <small>Point sensitivity; not a fresh bootstrap ranking.</small>
            </div>
            <p>
              {p.repeatability.seasonsInadequate} season deletions leave
              inadequate remaining sample evidence. Unavailable robustness is
              not a performance failure.
            </p>
            <p>
              2026:{" "}
              {p.recent.status === "adequate"
                ? "all standalone rating requirements pass."
                : p.recent.status === "no_retained_pressure"
                  ? "no retained pressure observations; no current-form inference."
                  : "some pressure evidence exists, but the full standalone rating requirements are not met."}
            </p>
          </div>
        </div>
        <div className="table-scroll" style={{ marginTop: 25 }}>
          <table>
            <caption className="sr-only">
              Competition-family diagnostics
            </caption>
            <thead>
              <tr>
                <th>Family</th>
                <th>Pressure opportunities</th>
                <th>Matches</th>
                <th>Point</th>
                <th>10th–90th interval</th>
                <th>Interval reliable</th>
              </tr>
            </thead>
            <tbody>
              {p.families.map((f) => (
                <tr key={f.family}>
                  <th>{f.family}</th>
                  <td>{f.pressure_events}</td>
                  <td>{f.pressure_matches}</td>
                  <td>{score(f.point)}</td>
                  <td>
                    {score(f.p10)} to {score(f.p90)}
                  </td>
                  <td>{f.interval_reliable ? "Yes" : "Unavailable"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="filter-caption">
          Family diagnostics do not establish equivalent opposition strength or
          guaranteed IPL transfer.
        </p>
        <details>
          <summary>Season-removal point sensitivity</summary>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Season removed</th>
                  <th>Remaining point</th>
                  <th>Remaining sample</th>
                </tr>
              </thead>
              <tbody>
                {p.repeatability.seasonDeletions.map((s) => (
                  <tr key={s.removed}>
                    <th>{s.removed}</th>
                    <td>{score(s.point)}</td>
                    <td>
                      {s.remaining_sample_adequate
                        ? "Adequate"
                        : "Inadequate — qualify interpretation"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
        <details>
          <summary>Registered runs / wickets weight variants</summary>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Outcome mix</th>
                  <th>Rank</th>
                  <th>Point</th>
                  <th>Conservative score</th>
                </tr>
              </thead>
              <tbody>
                {p.variants.map((v) => (
                  <tr key={v.variant}>
                    <th>{variantLabel(v.variant)}</th>
                    <td>{v.rank}</td>
                    <td>{score(v.point)}</td>
                    <td>{score(v.p10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </section>
      <section className="evidence-section" id="cases">
        <SectionHeading
          index="04"
          title="The other side of the case."
          detail="Supporting, adverse and typical examples are nominated by the same fixed rules."
        />
        {p.cases.length ? (
          <>
            <div className="case-grid">
              {p.cases.map((c) => (
                <CaseCard key={String(c.match_id)} c={c} player={p} />
              ))}
            </div>
            <Notice title="An extreme is an illustration">
              <p>
                Cases nominate highest/lowest run and wicket rates plus an
                exposure-weighted typical run-rate match, then deduplicate.
                Minimum display exposure is ten batting opportunities or six
                bowling attempts. The same segment can support one outcome and
                challenge the other; it does not establish a general weakness or
                match-winning credit.
              </p>
            </Notice>
          </>
        ) : (
          <p className="intro-copy">
            This comparison-candidate profile contains aggregate evidence. The
            detailed nominated-case review is provided for the final twenty
            selections.
          </p>
        )}
      </section>
      <section className="evidence-section" id="usual">
        <SectionHeading
          index="05"
          title="Compared with the usual level."
          detail="Supported same-player contexts are distinct from an all-ordinary background average."
        />
        <div className="two-col">
          <div className="panel">
            <h3>Ordinary background</h3>
            {p.ordinary ? (
              <>
                <p>
                  {p.ordinary.opportunities} ordinary opportunities across{" "}
                  {p.ordinary.matches} matches.
                </p>
                <p>
                  {num(p.ordinary.runs_per_100)} runs and{" "}
                  {num(p.ordinary.wickets_per_100)}{" "}
                  {p.role === "batting" ? "attributed dismissals" : "wickets"}{" "}
                  per 100 opportunities.
                </p>
                <p>
                  Descriptive background; its context mix differs from pressure
                  exposure.
                </p>
              </>
            ) : (
              <p>No retained ordinary observations are available.</p>
            )}
          </div>
          <div className="panel">
            <h3>Supported same-player comparison</h3>
            <p>
              {num(p.usual.pressureFraction * 100)}% of pressure exposure has
              supported ordinary comparisons: {p.usual.pressureEvents} pressure
              / {p.usual.ordinaryEvents} ordinary opportunities.
            </p>
            <p>
              <strong>Reliable change estimate: unavailable.</strong> The frozen
              whole-match missing-group rules do not support a reliable change
              interval. Missing change is never filled with zero.
            </p>
          </div>
        </div>
        <Notice title="Why this does not become an improvement score">
          <p>
            Every late-over event is labelled pressure, leaving no ordinary
            death-over control. The primary pressure list preserves specialists;
            conditional 70/30 and 50/50 level/change companion orderings remain
            withheld.{" "}
            <Link href="/methodology#usual">Read the support rules.</Link>
          </p>
        </Notice>
      </section>
      <section className="evidence-section" id="alternatives">
        <SectionHeading
          index="06"
          title="Why this place in the order?"
          detail="Credible exclusions and role-similar comparisons remain visible."
        />
        {p.editorial?.review && (
          <p className="profile-decision">{p.editorial.review}</p>
        )}
        {alternatives.length ? (
          <div className="alternative-grid">
            {alternatives.map((a) => (
              <article className="alternative-card" key={a.id}>
                <span>COHORT RANK {a.rank}</span>
                <h3>{a.name}</h3>
                <p>
                  Conservative score <strong>{score(a.rating.low)}</strong>
                </p>
                <p>{a.task}</p>
                <Link href={compareUrl(p.role, [p.id, a.id])}>
                  Compare side by side <ArrowUpRight size={13} />
                </Link>
              </article>
            ))}
          </div>
        ) : (
          <p className="intro-copy">
            Use the comparison page to inspect this candidate against the
            selected players in the same role.
          </p>
        )}
        <Notice title="Ordering is a declared decision rule">
          <p>
            The 10th percentile sets the order, followed by point estimate,
            supported pressure-match count and stable ID for ties. Overlapping
            intervals and weight-sensitive boundaries qualify the precision of
            an individual place.
          </p>
        </Notice>
      </section>
      <section className="evidence-section">
        <SectionHeading index="07" title="The cricket contribution." />
        {p.editorial ? (
          <p className="profile-decision">{p.editorial.contribution}</p>
        ) : (
          <p className="profile-decision">
            Assess the observed phase workload and concession/scoring tradeoff
            against the cricket task under consideration.
          </p>
        )}
        <p className="intro-copy">
          This is a role-based contribution argument. Auction availability,
          price, actual squad vacancies and future performance are not
          established by the retained match evidence.
        </p>
        <details>
          <summary>Evidence scope and definitions</summary>
          <p>
            Stable player ID {p.id} · 2023–1 November 2026 · peer retention{" "}
            {num(p.exposure.peerRetention * 100)}% · effective pressure count{" "}
            {num(p.exposure.effectiveEvents)} · valid bootstrap draws{" "}
            {num(p.rating.finiteFraction * 100)}%. Source retention is
            opportunity-based for this role/window. Opposition strength, venue
            and exact chase difficulty remain incompletely measured. Source:
            supplied corpus reconciled against Cricsheet, with original
            exclusions retained. Release pressure-index-2026-11-01-v1.
          </p>
        </details>
      </section>
    </div>
  );
}
