import { DataValue } from "@/components/data-value";
import Link from "next/link";
export default function NotFound() {
  return (
    <div className="not-found">
      <h1>
        <DataValue source="site.notFoundStatus" />
      </h1>
      <h2>Outside the evidence.</h2>
      <p>This player or page is not part of the published release.</p>
      <Link className="button" href="/rankings/batting">
        Explore the selections
      </Link>
    </div>
  );
}
