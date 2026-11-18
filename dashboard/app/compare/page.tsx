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
          Compare up to three players in the same role. Observed roles, retained
          exposure and standalone evidence status.
        </p>
      </PageIntro>
      <Suspense fallback={<p>Loading comparison controls…</p>}>
        <CompareExplorer players={players} />
      </Suspense>
    </div>
  );
}
