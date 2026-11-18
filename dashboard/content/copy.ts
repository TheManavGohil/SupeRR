import release from "./generated/release.json" with { type: "json" };
import site from "./generated/site.json" with { type: "json" };

const m = site.method;
const number = (n: number) => n.toLocaleString("en-GB");
const words = (n: number) =>
  (site.numberWords as Record<string, string>)[String(n)] ?? number(n);
const cap = (s: string) => s.replace(/^./, (c) => c.toUpperCase());
export const cutoffText = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
}).format(new Date(release.cutoff));
export const copy = {
  authorship:
    "The pipeline, site and copy were built with AI coding assistance; selections, interpretation and final review are the participant’s responsibility.",
  footer: `An independent SupeRR Selector Season ${release.season} submission. Retrospective evidence · ${cutoffText} cutoff.`,
  footerScope:
    "Observed pressure production, retained exposure and evidence limitations.",
  scoreScopeTitle: "What this score measures",
  scoreScopeProduction:
    "It ranks observed production in high-pressure overs against supported peers in the same match context. It does not yet measure how a player's pressure performance differs from their usual performance.",
  scoreScopeRole:
    "The pressure rule flags every late-over delivery, so late-over specialists receive pressure exposure by design. Read the role label, not the rank alone.",
  scoreScopeAdjustment:
    "Venue, opposition strength and fine chase difficulty are not fully adjusted.",
  scoreScopeFuture: `IPL ${release.auctionYear} availability and current form are not measured.`,
  eligibility: `${words(release.selectedRecentAdequate).replace(/^./, (s) => s.toUpperCase())} pass every standalone ${release.recentYear} gate; ${words(release.selectedRecentLimited)} are limited; ${words(release.selectedRecentAbsent)} have none retained.`,
  weightPrimary: `runs ${m.runsWeight} : wickets ${m.wicketsWeight}`,
  weightEqual: `runs ${m.sensitivityEqual} : wickets ${m.sensitivityEqual}`,
  weightRuns: `runs ${m.sensitivityRuns} : wickets ${m.sensitivityWickets}`,
  weightLevel: `level ${m.levelWeight} : change ${m.changeWeight} (withheld, not executed)`,
  weightLevelEqual: `level ${m.sensitivityEqual} : change ${m.sensitivityEqual} (withheld, not executed)`,
  scoreLabel: `P${m.quantilePercent} score`,
  scoreDescription: `Ranked by the ${m.quantilePercent}th percentile of observed peer-relative pressure production. Read the task and retained exposure alongside the rank.`,
  retainedMatches: "RETAINED MATCHES",
  peerSupported: "peer-supported",
  pressureOpportunities: "Pressure opportunities",
  recentAdequate: `${release.recentYear} sample adequate`,
  recentLimited: `${release.recentYear} evidence limited`,
  recentAbsent: `No retained ${release.recentYear} pressure evidence`,
  recentFilter: `Adequate ${release.recentYear} sample`,
  recentColumn: `${release.recentYear} evidence`,
  eligible: "Meets the frozen primary eligibility rules.",
  ineligible: "Primary eligibility is unavailable.",
  unavailableChange: "Reliable change estimate: unavailable.",
  missingChange:
    "Ordinary and pressure contexts do not provide reliable matched comparisons for the final selections. Missing change is not a negative performance score.",
  examples: "Examples are available on request.",
  sourceGaps:
    "Source gaps, broad context definitions and incomplete adjustment qualify the ordering. Match-sampling uncertainty cannot account for missing-source bias.",
  roleScope:
    "This is an observed workload label; squad fit and availability need separate review.",
  rankingTitleBatting: `${cap(words(release.topCount))} batters. Every pick explained.`,
  rankingTitleBowling: `${cap(words(release.topCount))} bowlers. Every pick explained.`,
  homeKicker: `SUPERR SELECTOR SEASON ${release.season} · ROUND ${release.round}`,
  homeDeck: `${cap(words(release.topCount))} batters. ${cap(words(release.topCount))} bowlers.`,
  homeProof: "The evidence behind every pick.",
  frozen: `FROZEN AT ${cutoffText.toUpperCase()} / RETROSPECTIVE ANALYSIS`,
  heroRank: "BATTING RANK",
  heroMetric: `${m.quantilePercent}th-percentile selection statistic`,
  scopeMatches: "verified matches",
  scopeEvents: "delivery events",
  scopeSelections: "selected player-role entries",
  scopeResamples: "whole-match resamples",
  selectionsTitle: "The players. The proof.",
  selectionsDetail:
    "Two ranked lists, with aggregate evidence for every selection.",
  methodPreview:
    "Pressure is defined before the ball. Production is compared with supported peers in measured contexts. Retained exposure and eligibility qualify each recommendation.",
  processSituation:
    "Late overs, a wicket collapse or a tight chase. One frozen rule for batting and bowling.",
  processContribution:
    "Scoring and dismissal risk. Concessions and wickets. Contemporaneous peers with the player left out.",
  processChallenge:
    "Whole-match uncertainty, sample checks and an explicit account of what remains unmeasured.",
  realityTitle: "The qualification matters.",
  realityDetail:
    "A multi-year record and current form answer different questions.",
  rankingFilterSuffix: "selections. Original ranks are retained.",
  compareLimitReached: "Compare limit reached: remove a player to add another.",
  compareHint: "Choose players from the same role for an aggregate comparison.",
  reportSameRelease:
    "Same frozen rankings and aggregate evidence as the dashboard.",
  reportIntro: "The ordered selections, shared method and aggregate evidence.",
  reportTitle: "The complete selection argument.",
  reportKicker: "INDEPENDENT SUPERR SELECTOR SUBMISSION",
  reportMeta: `Scoring window: ${release.firstYear} to ${cutoffText} · ${number(release.matches)} verified matches · ${number(release.events)} events.`,
  reportOrdering: `The frozen order follows the ${m.quantilePercent}th bootstrap percentile, with declared tie-breakers.`,
  reportMethod:
    "The primary index uses frozen peer comparisons, sample-size shrinkage and whole-match resampling. Exact ranks are decisions under this method; they do not establish certain superiority, future form or availability.",
  reportReproduction:
    "Reproduce from the frozen outputs and approved method: verified states, pre-ball pressure labels, fixed attribution and support, peer-relative contributions, shrinkage and shared whole-match resamples. Publication exports read existing results without recomputing ratings.",
  reportReliability: "Reliability, limitations and reproduction",
  profileLead:
    "The frozen ordering balances scoring and wicket outcomes against supported peers. Read the observed task and evidence status alongside the rank.",
  aggregateEvidence:
    "The score describes retained production relative to supported peers. Sample size and the recent-evidence label qualify its interpretation.",
  neighbourDetail:
    "Adjacent frozen ranks are navigation aids, rather than claims of tactical similarity.",
  comparisonIntro: `Compare up to ${site.compareLimit} players in the same role using observed tasks, retained exposure and standalone evidence status.`,
  comparisonCandidate:
    "Compare this candidate on the same frozen evidence and sample rules.",
  comparisonScope:
    "Compare retained aggregates alongside the observed task and recent-evidence status. Context and source gaps qualify every recommendation.",
  validationIntro:
    "Keep sample adequacy, observed production and future availability distinct.",
  retrospective:
    "Prior aggregate recent-year EDA was seen. The reserved evaluation is retrospective; historical predictive models failed calibration gates.",
  companions:
    "The level/change companions remain withheld because their change component is unreliable. Missing change is never filled with zero.",
  pressureShare: `The rule flags ${release.pressureShare.toFixed(2)}%: ${number(release.pressureEvents)} of ${number(release.events)} final-window events. This is above the ${m.pressureTargetMin}–${m.pressureTargetMax}% diagnostic target; the fixed late-over rule plus collapse/chase expansion explains the breadth.`,
  verifiedPressureShare: `Across the full verified population, ${release.verifiedPressureShare.toFixed(2)}% means ${number(release.verifiedPressureEvents)} of ${number(release.verifiedEvents)} events.`,
  methodIntro:
    "A reproducible pressure definition, a task-specific comparison and a declared ranking rule. Here is how the evidence becomes the two lists.",
  methodDataTitle: "Start with a trustworthy match state.",
  methodDataIntro:
    "The supplied pack contained ambiguous extras. Score reconciliation preceded exact chase-state interpretation; unresolved matches remained excluded.",
  methodDataAudit:
    "Recorded runs alone and a blanket one-run-per-extra rule both failed the run-margin audit. Accepted evidence was reconciled against external event records; original inputs were preserved.",
  methodDataWindow: `${number(release.verifiedMatches)} matches were completely verified across available years; ${number(release.matches)} remain in the ${release.firstYear}–${release.recentYear} scoring window through ${cutoffText}.`,
  methodPressureTitle: "Define pressure before the delivery.",
  methodPressureIntro:
    "One frozen union rule is used for both roles: late OR collapse OR tight chase. Overlap counts a delivery once.",
  methodLate: `Late: overs ${m.lateStart}–${m.lateEnd} inclusive.`,
  methodCollapse: `Collapse: at least ${m.collapseWickets} wickets in the preceding ${m.collapseBalls} legal balls, or at least ${m.earlyWickets} already lost in overs ${m.earlyStart}–${m.earlyEnd}.`,
  methodChase: `Tight chase: innings ${m.chaseInnings}, ${m.chaseBallsMin}–${m.chaseBallsMax} legal balls remaining, and required runs per ball from ${m.chaseRateMin} to ${m.chaseRateMax} inclusive.`,
  methodOutcomesTitle: "Evaluate the cricket tradeoff.",
  methodOutcomesIntro:
    "Batting combines scoring and preservation; bowling combines concession control and wicket contribution.",
  methodBatting:
    "Batting opportunities exclude wides and include no-balls. Outcomes use batter runs and bowler-attributable striker dismissals, excluding run-outs and other uncredited dismissals.",
  methodBowling:
    "Bowling uses every attempt. Charged runs include batter runs, wides and no-balls; they exclude byes, leg-byes and penalties. Wickets are bowler-credited.",
  methodPeersTitle: "Compare similar measured contexts.",
  methodPeersIntro:
    "Peer cells use competition family, year, innings, phase and pre-ball wicket band. All outcomes of the evaluated player in that role are excluded from their own reference.",
  methodPeersMinimum: `Each cell needs at least ${m.peerOpportunities} other-player opportunities across ${m.peerMatches} matches. No broader-context or cross-year fallback is used.`,
  methodRecency: `Recency has a ${m.recencyDays}-day half-life at ${cutoffText}. Outcome scales were frozen on development evidence through ${release.developmentLastYear}.`,
  methodRatingTitle: "Combine outcomes, then temper small samples.",
  methodRatingIntro:
    "Orient the player-minus-peer run and wicket differences, standardize with development-frozen scales, average over supported pressure mass, and shrink for effective sample size.",
  methodShrinkage: `Shrinkage is n_eff / (n_eff + k), with k=${m.battingShrinkage} for batting and ${m.bowlingShrinkage} for bowling. Effective count is squared total weight divided by the sum of squared weights.`,
  methodEligibility: `Minimum total opportunities: ${m.battingTotal} batting / ${m.bowlingTotal} bowling; pressure: ${m.battingPressure} / ${m.bowlingPressure}; at least ${m.pressureMatches} pressure matches and effective count ${m.effectiveCount}. Source and peer-supported pressure retention must reach ${m.retentionPercent}%.`,
  methodBootstrapTitle: "Rank with whole-match uncertainty.",
  methodBootstrapIntro: `${number(release.bootstrapDraws)} shared whole-match resamples use competition-family/year strata and seed ${m.seed}. Own and peer means, workload, effective counts and shrinkage are recomputed.`,
  methodBootstrapGate: `Eligibility, supported cells and scales stay fixed. At least ${m.finitePercent}% of draws must be finite. Rank by the ${m.quantilePercent}th percentile, then point estimate, supported pressure matches and stable identity.`,
  methodBootstrapLimit:
    "This is conditional match-sampling uncertainty; it does not account for missing-source bias or establish a guaranteed top-ten population.",
  methodUsualTitle: "Keep usual-performance comparisons honest.",
  methodUsualIntro:
    "Every late-over event is pressure, leaving no ordinary control in that phase. No final supported-change interval meets the fixed reliability gate.",
  methodValidationTitle: "Challenge the result before recommending.",
  methodValidationIntro:
    "The development method preceded the committed final-window protocol. Reserved recent-year evaluation preceded the combined window, with scales and rules fixed.",
  metadataDescription: `${release.topCount} batters. ${release.topCount} bowlers. Aggregate evidence for SupeRR Selector Season ${release.season}.`,
};
export type CopyKey = keyof typeof copy;
export const roleContribution = {
  "Late-over scoring":
    "A closing-overs scoring option. Interpret the peer-relative score alongside retained exposure and the evidence-status label.",
  "Middle-over scoring":
    "An option for scoring through the middle overs, with scoring and preservation evaluated together.",
  "Middle / late-over scoring":
    "An option spanning middle and closing-overs scoring tasks, qualified by the retained evidence.",
  "Middle-over control":
    "A middle-overs control option, evaluated through charged runs and credited wickets together.",
  "Powerplay / death bowling":
    "An option spanning the opening and closing bowling tasks observed in the retained workload.",
  "Late-over bowling":
    "A closing-overs bowling option, evaluated through control and wicket contribution together.",
  "Middle-over bowling":
    "A middle-overs bowling option whose role and exposure should be read alongside the frozen score.",
  "Powerplay / late-over bowling":
    "An opening-to-closing bowling option within the observed retained workload.",
  "Pressure bowling":
    "A pressure-bowling option; the retained role label does not establish a more specific tactical assignment.",
  "Middle / late-over bowling":
    "A middle-to-closing bowling option, with concession control and wickets assessed together.",
};
export function contribution(task: string) {
  return (
    roleContribution[task as keyof typeof roleContribution] ?? copy.roleScope
  );
}
