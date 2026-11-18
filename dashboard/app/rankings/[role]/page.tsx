import { copy } from "@/content/copy";
import Link from "next/link";
import { notFound } from "next/navigation";
import { selected, roles, roleLabel } from "@/lib/data";
import type { Role } from "@/lib/types";
import { PageIntro } from "@/components/ui";
import { RankingsExplorer } from "@/components/rankings-explorer";

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
  return {
    title: role === "bowling" ? "Top ten bowlers" : "Top ten batters",
    alternates: { canonical: `/rankings/${role}` },
  };
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
            title={
              role === "batting"
                ? copy.rankingTitleBatting
                : copy.rankingTitleBowling
            }
          >
            <p>{copy.scoreDescription}</p>
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
                <span>{selected(r).length}</span>
              </Link>
            ))}
          </nav>
        }
        players={list}
        role={role}
      />
    </div>
  );
}
