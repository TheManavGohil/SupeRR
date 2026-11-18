import { copy } from "../content/copy";
import { CopyText } from "./data-value";
export function ScoreScope() {
  return (
    <section className="section score-scope" aria-label={copy.scoreScopeTitle}>
      <h2>
        <CopyText name="scoreScopeTitle" />
      </h2>
      <ul>
        {(
          [
            "scoreScopeProduction",
            "scoreScopeRole",
            "scoreScopeAdjustment",
            "scoreScopeFuture",
          ] as const
        ).map((name) => (
          <li key={name}>
            <CopyText name={name} />
          </li>
        ))}
      </ul>
    </section>
  );
}
