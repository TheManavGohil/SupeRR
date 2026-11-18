import { ScoreScope } from "@/components/score-scope";
import { DataValue, CopyText, KnownText } from "@/components/data-value";

import { PageIntro, Notice, ActionLink } from "@/components/ui";
import { methodSections } from "@/content/method";
export const metadata = {
  title: "The complete methodology",
  alternates: { canonical: "/methodology" },
};
export default function Methodology() {
  return (
    <div className="page-wrap" style={{ paddingBottom: 70 }}>
      <PageIntro
        kicker="THE COMPLETE APPROACH"
        title="From the ball. To the shortlist."
      >
        <p>
          <CopyText name="methodIntro" />
        </p>
      </PageIntro>
      <ScoreScope />
      <div className="method-layout">
        <nav className="method-toc" aria-label="Methodology sections">
          {methodSections.map((s, i) => (
            <a key={s.id} href={`#${s.id}`}>
              <DataValue source={`site.uiCounts.${i + 1}`} /> /{" "}
              {s.id === "usual"
                ? "Usual performance"
                : s.id.charAt(0).toUpperCase() + s.id.slice(1)}
            </a>
          ))}
        </nav>
        <div>
          {methodSections.map((s, i) => (
            <section className="method-step" id={s.id} key={s.id}>
              <span className="step-num">
                <DataValue source={`site.uiCounts.${i + 1}`} />
              </span>
              <div>
                <h2>
                  <KnownText value={s.title} />
                </h2>
                <p>
                  <KnownText value={s.intro} />
                </p>
                <ul>
                  {s.points.map((p) => (
                    <li key={p}>
                      <KnownText value={p} />
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          ))}
          <Notice title="Interpret the score in its scope">
            <p>
              <CopyText name="scoreDescription" />
            </p>
          </Notice>
          <div style={{ marginTop: 30 }}>
            <ActionLink href="/validation">Inspect the validation</ActionLink>
          </div>
        </div>
      </div>
    </div>
  );
}
