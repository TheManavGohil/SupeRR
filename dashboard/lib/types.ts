export type Role = "batting" | "bowling";
export type CardPlayer = Pick<
  Player,
  "id" | "role" | "name" | "rank" | "task" | "rating" | "exposure" | "recent"
>;
export type ComparePlayer = CardPlayer &
  Pick<Player, "selected" | "pressure" | "pressurePhases"> & {
    editorial: Pick<NonNullable<Player["editorial"]>, "why" | "caution"> | null;
    repeatability: Pick<Player["repeatability"], "seasonsInadequate">;
  };
export interface Rate {
  runs_per_100: number;
  wickets_per_100: number;
}
export interface Player {
  id: string;
  role: Role;
  name: string;
  rank: number;
  selected: boolean;
  task: string;
  editorial: {
    title: string;
    why: string;
    caution: string;
    contribution: string;
    review: string | null;
  } | null;
  rating: { point: number; low: number; high: number; finiteFraction: number };
  exposure: {
    pressureEvents: number;
    pressureMatches: number;
    effectiveEvents: number;
    retainedEvents: number;
    sourceEvents: number;
    sourceRetention: number;
    peerRetention: number;
  };
  pressure: Rate & {
    runs: number;
    wickets: number;
    weighted_runs_per_100: number;
    weighted_wickets_per_100: number;
  };
  ordinary: (Rate & { opportunities: number; matches: number }) | null;
  workload: { phase: string; opportunities: number; share: number }[];
  pressurePhases: (Rate & {
    phase: string;
    opportunities: number;
    share: number;
  })[];
  seasons: (Rate & { year: number; opportunities: number; matches: number })[];
  families: {
    family: string;
    pressure_events: number;
    pressure_matches: number;
    point: number;
    p10: number;
    p90: number;
    interval_reliable: boolean;
  }[];
  repeatability: {
    matchPointLow: number | null;
    matchPointHigh: number | null;
    seasonsInadequate: number;
    seasonDeletions: {
      removed: string;
      point: number | null;
      remaining_sample_adequate: boolean;
    }[];
  };
  usual: {
    reliable: boolean;
    sampleEligible: boolean;
    pressureFraction: number;
    pressureEvents: number;
    ordinaryEvents: number;
    observedRunsDifference: number | null;
    observedWicketsDifference: number | null;
  };
  recent: {
    status: "adequate" | "limited" | "no_retained_pressure";
    events: number;
    matches: number;
    rating: number | null;
  };
  variants: {
    variant: string;
    rank: number;
    point: number;
    p10: number;
    p90: number;
  }[];
  cases: (Rate & {
    match_id: string | number;
    match_date: string;
    family: string;
    opposition: string;
    phases: string;
    opportunities: number;
    runs: number;
    wickets: number;
    case_reasons: string;
    small_sample: boolean;
    first_over: number;
    score_before: number;
    wickets_before: number;
    balls_remaining: number;
    runs_required: number | null;
    required_run_rate: number | null;
  })[];
  alternatives: {
    id: string;
    rank: number;
    boundary: boolean;
    roleSimilar: boolean;
  }[];
}
