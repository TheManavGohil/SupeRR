import { num, phaseName, score } from "@/lib/format";
import type { Player } from "@/lib/types";

export function IntervalChart({
  players,
}: {
  players: Pick<Player, "id" | "name" | "rating">[];
}) {
  const min = Math.min(0, ...players.map((p) => p.rating.low)) - 0.015;
  const max = Math.max(0.05, ...players.map((p) => p.rating.high)) + 0.015;
  const left = 205,
    right = 650,
    height = players.length * 45 + 48;
  const x = (n: number) => left + ((n - min) / (max - min)) * (right - left);
  return (
    <figure className="interval-chart">
      <svg
        viewBox={`0 0 700 ${height}`}
        role="img"
        aria-label="Player point ratings and 10th to 90th percentile intervals. Ranking follows the left endpoint."
      >
        <line
          x1={x(0)}
          x2={x(0)}
          y1="10"
          y2={height - 35}
          stroke="currentColor"
          opacity=".3"
          strokeDasharray="3 5"
        />
        {players.map((p, i) => (
          <g key={p.id} transform={`translate(0 ${i * 45 + 26})`}>
            <text x="0" y="5" className="chart-name">
              {p.name}
            </text>
            <line
              x1={x(p.rating.low)}
              x2={x(p.rating.high)}
              stroke="var(--pink)"
              strokeWidth="3"
            />
            <line
              x1={x(p.rating.low)}
              x2={x(p.rating.low)}
              y1="-6"
              y2="6"
              stroke="var(--pink)"
              strokeWidth="2"
            />
            <circle
              cx={x(p.rating.point)}
              r="5"
              fill="var(--ink)"
              stroke="var(--pink)"
              strokeWidth="2"
            />
            <line
              x1={x(p.rating.high)}
              x2={x(p.rating.high)}
              y1="-6"
              y2="6"
              stroke="var(--pink)"
              strokeWidth="2"
            />
          </g>
        ))}
        {[min, 0, max].map((n, i) => (
          <text
            key={i}
            x={x(n)}
            y={height - 6}
            textAnchor="middle"
            className="chart-tick"
          >
            {n.toFixed(2)}
          </text>
        ))}
      </svg>
      <figcaption>
        Dot: point estimate. Line: 10th–90th percentile. Higher is favourable
        within a role; the left endpoint determines rank.
      </figcaption>
      <details>
        <summary>View the exact interval values</summary>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Player</th>
                <th>10th percentile</th>
                <th>Point</th>
                <th>90th percentile</th>
              </tr>
            </thead>
            <tbody>
              {players.map((p) => (
                <tr key={p.id}>
                  <th>{p.name}</th>
                  <td>{score(p.rating.low)}</td>
                  <td>{score(p.rating.point)}</td>
                  <td>{score(p.rating.high)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}
export function PhaseBars({
  player,
  pressure = false,
}: {
  player: Player;
  pressure?: boolean;
}) {
  const rows = pressure ? player.pressurePhases : player.workload;
  return (
    <div className="phase-bars">
      {["01-06", "07-15", "16-20"].map((phase) => {
        const row = rows.find((r) => r.phase === phase);
        return (
          <div key={phase}>
            <div className="bar-label">
              <span>
                {phaseName(phase)} <small>{phase}</small>
              </span>
              <strong>{row ? `${num(row.share)}%` : "No observations"}</strong>
            </div>
            <div
              className="bar-track"
              role="img"
              aria-label={`${phaseName(phase)}: ${row ? num(row.share) + " percent, " + row.opportunities + " opportunities" : "no observations"}`}
            >
              <span style={{ width: `${row?.share ?? 0}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
export function SeasonChart({ player }: { player: Player }) {
  const max = Math.max(...player.seasons.map((s) => s.runs_per_100), 1);
  return (
    <figure className="season-chart">
      <div className="season-columns">
        {[2023, 2024, 2025, 2026].map((year) => {
          const s = player.seasons.find((r) => r.year === year);
          return (
            <div className="season-column" key={year}>
              <span className="season-value">
                {s ? num(s.runs_per_100) : "—"}
              </span>
              <div className="season-track">
                <div
                  style={{
                    height: s
                      ? `${Math.max(2, (s.runs_per_100 / max) * 100)}%`
                      : "0",
                  }}
                />
              </div>
              <strong>{year}</strong>
              <small>
                {s
                  ? `${s.opportunities} opportunities`
                  : "No pressure observations"}
              </small>
            </div>
          );
        })}
      </div>
      <figcaption>
        Observed {player.role === "batting" ? "batter runs" : "runs conceded"}{" "}
        per 100 pressure opportunities. These are descriptive rates, not annual
        selection scores.
      </figcaption>
    </figure>
  );
}
