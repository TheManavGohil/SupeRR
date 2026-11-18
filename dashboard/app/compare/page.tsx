import { CopyText } from "@/components/data-value";

import { Suspense } from "react";
import { players } from "@/lib/data";
import { CompareExplorer } from "@/components/compare-explorer";
import { PageIntro } from "@/components/ui";
export const metadata = {
  title: "Compare player evidence",
  alternates: { canonical: "/compare" },
};
export default function ComparePage() {
  return (
    <div className="page-wrap" style={{ paddingBottom: 70 }}>
      <PageIntro
        kicker="SIDE BY SIDE"
        title="Close calls deserve a closer look."
      >
        <p>
          <CopyText name="comparisonIntro" />
        </p>
      </PageIntro>
      <Suspense fallback={<p>Loading comparison controls…</p>}>
        <CompareExplorer players={players} />
      </Suspense>
    </div>
  );
}
