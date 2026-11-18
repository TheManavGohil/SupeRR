import Link from "next/link";
import { notFound } from "next/navigation";
import { selected, roles, roleLabel } from "@/lib/data";
import type { Role } from "@/lib/types";
import { PageIntro, Notice, SectionHeading } from "@/components/ui";
import { RankingsExplorer } from "@/components/rankings-explorer";
import { IntervalChart } from "@/components/charts";

export const dynamicParams = false;
export function generateStaticParams() {
  return roles.map((role) => ({ role }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ role: string }>;
}) {
  const { role } = await params;
  return { title: role === "bowling" ? "Top ten bowlers" : "Top ten batters" };
}
export default async function Rankings({
  params,
}: {
  params: Promise<{ role: string }>;
}) {
  const { role: value } = await params;
  if (!roles.includes(value as Role)) notFound();
  const role = value as Role;
  const list = selected(role);
  return (
    <div className="page-wrap">
      <RankingsExplorer
        key={role}
        intro={
          <PageIntro
            kicker="THE FINAL SELECTIONS"
            title={`Ten ${roleLabel(role).toLowerCase()}. Every pick explained.`}
          >
            <p>
              Ranked by the conservative 10th percentile of observed
              peer-relative pressure performance. Read the evidence, compare the
              tradeoffs, inspect the counterexamples.
            </p>
          </PageIntro>
        }
        tabs={
          <nav className="role-tabs" aria-label="Player category">
            {roles.map((r) => (
              <Link
                key={r}
                href={`/rankings/${r}`}
                aria-current={r === role ? "page" : undefined}
              >
                {roleLabel(r)}
                <span>10</span>
              </Link>
            ))}
          </nav>
        }
        players={list.map(
          ({ id, role, name, rank, task, rating, exposure, recent }) => ({
            id,
            role,
            name,
            rank,
            task,
            rating,
            exposure,
            recent,
          }),
        )}
        role={role}
      />
      <section className="section">
        <SectionHeading
          index="THE ORDER"
          title="See the room for uncertainty."
          detail="Intervals can overlap even when the declared statistic gives a clear order."
        />
        <IntervalChart players={list} />
        <Notice title="Native units, transparent interpretation">
          <p>
            The score combines standardised runs and wickets, shrunk for
            effective sample size. It is not a probability or a score out of
            100. Filters preserve the frozen list order.
          </p>
        </Notice>
      </section>
    </div>
  );
}
