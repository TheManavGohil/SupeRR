export const methodSections = [
  {
    id: "data",
    title: "Start with a trustworthy match state.",
    intro:
      "The supplied pack contained ambiguous extras. We tested score reconstruction before defining exact chase pressure, then aligned accepted matches to external event records.",
    points: [
      "Recorded runs alone and a blanket one-run-per-extra rule both failed the run-margin audit. Original sources were preserved; unresolved matches stayed excluded.",
      "651 supplied matches were fully verified across available years. The scoring window retains 511 matches in 2023–1 November 2026; 2022 contributes no player scoring evidence.",
      "The later official archive revises extra quantities. Its extra totals agree with all 121,891 final retained events; two existing batter-run repairs remain. No post-evaluation cohort expansion was made.",
    ],
  },
  {
    id: "pressure",
    title: "Define pressure before the delivery.",
    intro:
      "One frozen union rule is used for both roles: late OR collapse OR tight chase. A delivery can satisfy several reasons and still counts only once.",
    points: [
      "Late: overs 16–20 inclusive.",
      "Collapse: at least two wickets in the preceding twelve legal balls, or at least four wickets already lost during overs 1–10. The early-innings clause ends after over ten.",
      "Tight chase: second innings, 1–60 legal balls remaining, and required runs per ball between 0.75 and 1.5 inclusive.",
      "The rule labels 35.30% of final delivery attempts, above the 20–30% diagnostic target. All late overs plus collapse/chase expansion explain the breadth; thresholds were not tuned to player names.",
    ],
  },
  {
    id: "outcomes",
    title: "Evaluate the cricket tradeoff.",
    intro:
      "Batting combines scoring and preservation; bowling combines concession control and wicket contribution. Headline strike rate or economy alone is insufficient.",
    points: [
      "Batting opportunities exclude wides and include no-balls. Outcomes are batter runs and bowler-attributable striker dismissals; run-outs and other excluded dismissals are not credited to this metric.",
      "Bowling uses every attempt. Concessions include batter runs, wides and no-balls, excluding byes, leg-byes and penalties. Wickets are bowler-credited.",
      "Displayed rates per 100 analytical opportunities are not official strike rate/economy. Phase workload and the pressure subset are shown separately; tactical assignments are not invented.",
    ],
  },
  {
    id: "peers",
    title: "Compare similar measured contexts.",
    intro:
      "Each player's pressure outcomes are compared with retained other-player outcomes in family × year × innings × phase × pre-ball wicket-band cells.",
    points: [
      "Exclude every observation of the evaluated player in that role from their own peer means, including observations outside the candidate cohort.",
      "A peer cell requires twenty opportunities across three matches. All retained other players can contribute; there is no broader-context or cross-year fallback.",
      "Use 730-day recency at 1 November 2026. Standardise outcomes with weighted population outcome SDs frozen from 2023–2025 development pressure evidence at 31 December 2025.",
      "Venue, opposition strength and exact chase difficulty remain incompletely measured. Matching broad cells is not full contextual equivalence or causal identification.",
    ],
  },
  {
    id: "rating",
    title: "Combine outcomes, then temper small samples.",
    intro:
      "The default index assigns 60% to runs and 40% to wickets. Contributions are averaged over the player's supported pressure workload, then shrunk for effective sample size.",
    points: [
      "Batting rewards own-minus-peer runs and penalises own-minus-peer dismissals. Bowling reverses those directions.",
      "Effective count is (sum of weights)² / sum of squared weights. Shrinkage is n_eff / (n_eff + k), with k=75 for batting and 60 for bowling.",
      "Minimum total exposure: 300 batting opportunities or 240 bowling attempts. Pressure minima: 75 batting or 60 bowling, eight pressure matches and effective pressure count at least forty.",
      "Reapply pressure minima within peer-supported cells. Require at least 80% source retention and 80% pressure retention by both count and recency-weighted mass.",
    ],
  },
  {
    id: "uncertainty",
    title: "Rank with match-level uncertainty.",
    intro:
      "We use 1,000 shared whole-match resamples, stratified by competition family/year, with seed 1729. Deliveries from a match stay together.",
    points: [
      "Each draw recomputes own and leave-player-out peer means, workload shares, effective counts and shrinkage. Eligibility, support and development scales stay fixed.",
      "Positive own mass without peer mass invalidates a player draw; zero own mass has zero workload weight. Repeated match copies contribute linearly to squared-weight sums.",
      "Require at least 95% finite draws. Rank by the 10th percentile, then point estimate, supported pressure-match count and stable player ID for ties.",
      "The 10th–90th interval is conditional match-sampling uncertainty, not a posterior probability, simultaneous top-ten guarantee or accounting for missing-source bias.",
    ],
  },
  {
    id: "usual",
    title: "Keep usual-performance comparisons honest.",
    intro:
      "All-ordinary background rates and supported same-player pressure-minus-ordinary comparisons answer different questions. Missing comparison evidence is not poor pressure performance.",
    points: [
      "Within each same-player/family/year/innings/phase/wicket-band cell, each group needs twenty peer opportunities over three matches and ten player opportunities over two matches.",
      "Aggregate change needs the original pressure exposure minima plus 100 ordinary opportunities across five matches. No ordinary death-over control exists because every late-over event is pressure.",
      "In resampling, losing either player group from any originally supported cell makes that change draw unavailable. No final supported-change interval meets the 95% finite-draw rule.",
      "The approved primary index therefore orders pressure level; the registered 70/30 and 50/50 level/change blends remain conditional companions and are withheld when change is unreliable. Missing change is never zero.",
    ],
  },
  {
    id: "validation",
    title: "Challenge the result before recommending.",
    intro:
      "Development review preceded the committed final-window protocol. Reserved 2026 was evaluated separately before the combined 2023–2026 window, using the same method and scales.",
    points: [
      "Prior aggregate 2026 EDA is disclosed: the reserved check is retrospective, not a pristine unseen forecast test.",
      "Registered 50/50 and 70/30 runs/wickets variants use identical cohorts. Match/season deletion, family diagnostics and frozen supporting/adverse case selection qualify each recommendation.",
      "Only seven selected entries meet all standalone 2026 rating requirements; two have no retained 2026 pressure observations. No inactivity, availability or price filter was added after seeing the ranks.",
      "Historical predictive baselines were fitted and failed their calibration gates. The final method is a descriptive peer-relative index; it does not establish future IPL ability or a causal response to pressure.",
    ],
  },
];
