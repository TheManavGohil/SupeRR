export type Role = "batting" | "bowling";
export interface Player {
  id: string;
  role: Role;
  name: string;
  rank: number;
  selected: boolean;
  task: string;
  rating: { low: number };
  exposure: {
    pressureMatches: number;
    pressureEvents: number;
    peerSupportedMatches: number;
  };
  recent: { status: "adequate" | "limited" | "no_retained_pressure" };
  eligibility: { primary: boolean };
}
export type CardPlayer = Player;
export type ComparePlayer = Player;
