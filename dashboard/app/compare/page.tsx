import { Suspense } from "react";
import { players } from "@/lib/data";
import { CompareExplorer } from "@/components/compare-explorer";
import { PageIntro } from "@/components/ui";
export const metadata = { title: "Compare player evidence" };
export default function ComparePage() {
  return (
    <div className="page-wrap" style={{ paddingBottom: 70 }}>
      <PageIntro
        kicker="SIDE BY SIDE"
        title="Close calls deserve a closer look."
      >
        <p>
          Compare up to three players in the same role. Scoring, wicket
          outcomes, repeatability and the evidence that challenges each case.
        </p>
      </PageIntro>
      <Suspense fallback={<p>Loading comparison controls…</p>}>
        <CompareExplorer
          players={players.map(
            ({
              id,
              role,
              name,
              rank,
              task,
              rating,
              exposure,
              recent,
              selected,
              pressure,
              pressurePhases,
              editorial,
              repeatability,
            }) => ({
              id,
              role,
              name,
              rank,
              task,
              rating,
              exposure,
              recent,
              selected,
              pressure,
              pressurePhases,
              editorial: editorial
                ? { why: editorial.why, caution: editorial.caution }
                : null,
              repeatability: {
                seasonsInadequate: repeatability.seasonsInadequate,
              },
            }),
          )}
        />
      </Suspense>
    </div>
  );
}
