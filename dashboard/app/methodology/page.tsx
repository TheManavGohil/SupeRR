import { PageIntro, Notice, ActionLink } from "@/components/ui";
import { methodSections } from "@/content/method";
export const metadata = { title: "The complete methodology" };
export default function Methodology() {
  return (
    <div className="page-wrap" style={{ paddingBottom: 70 }}>
      <PageIntro
        kicker="THE COMPLETE APPROACH"
        title="From the ball. To the shortlist."
      >
        <p>
          A reproducible pressure definition, a task-specific comparison and a
          declared ranking rule. Here is how the evidence becomes the two lists.
        </p>
      </PageIntro>
      <div className="method-layout">
        <nav className="method-toc" aria-label="Methodology sections">
          {methodSections.map((s, i) => (
            <a key={s.id} href={`#${s.id}`}>
              0{i + 1} /{" "}
              {s.id === "usual"
                ? "Usual performance"
                : s.id.charAt(0).toUpperCase() + s.id.slice(1)}
            </a>
          ))}
        </nav>
        <div>
          {methodSections.map((s, i) => (
            <section className="method-step" id={s.id} key={s.id}>
              <span className="step-num">0{i + 1}</span>
              <div>
                <h2>{s.title}</h2>
                <p>{s.intro}</p>
                {s.id === "rating" && (
                  <div className="formula">
                    Batting cell: +0.60 × run difference / run SD − 0.40 ×
                    dismissal difference / wicket SD
                    <br />
                    <br />
                    Bowling cell: −0.60 × concession difference / run SD + 0.40
                    × wicket difference / wicket SD
                    <br />
                    <br />
                    Point = pressure-mass-weighted cell average × n_eff / (n_eff
                    + k)
                  </div>
                )}
                <ul>
                  {s.points.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
              </div>
            </section>
          ))}
          <Notice title="Interpret the score in its scope">
            <p>
              The index describes observed performance against retained
              contemporaneous peers in broad contexts. Native values are not win
              probabilities or scores out of 100. All selections carry sample,
              context and temporal qualifications.
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
