import { copy } from "@/content/copy";
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
        <p>{copy.methodIntro}</p>
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
                <ul>
                  {s.points.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
              </div>
            </section>
          ))}
          <Notice title="Interpret the score in its scope">
            <p>{copy.scoreDescription}</p>
          </Notice>
          <div style={{ marginTop: 30 }}>
            <ActionLink href="/validation">Inspect the validation</ActionLink>
          </div>
        </div>
      </div>
    </div>
  );
}
