import Image from "next/image";
import assets from "@/content/player-assets.json";
import type { Player } from "@/lib/types";

type Asset = {
  src: string;
  alt: string;
  position?: string;
  attribution?: string;
};
export function Portrait({
  player,
  hero = false,
}: {
  player: Pick<Player, "id" | "role" | "name" | "rank">;
  hero?: boolean;
}) {
  const asset = (assets as Record<string, Asset>)[player.id];
  const gradient = `s-${hero ? "hero" : "card"}-${player.role}-${player.id}`;
  return (
    <div className={`portrait ${player.role} ${hero ? "portrait-hero" : ""}`}>
      <span className="portrait-orbit" aria-hidden="true" />
      {asset ? (
        <Image
          src={asset.src}
          alt={asset.alt}
          fill
          sizes={
            hero
              ? "(max-width: 768px) 90vw, 500px"
              : "(max-width: 768px) 90vw, 400px"
          }
          style={{
            objectFit: "cover",
            objectPosition: asset.position ?? "center 20%",
          }}
          preload={hero}
        />
      ) : (
        <>
          <svg
            viewBox="0 0 320 360"
            className="portrait-silhouette"
            aria-hidden="true"
          >
            <defs>
              <linearGradient id={gradient} x1="0" y1="0" x2="1" y2="1">
                <stop stopColor="currentColor" stopOpacity=".6" />
                <stop offset="1" stopColor="currentColor" stopOpacity=".15" />
              </linearGradient>
            </defs>
            <circle cx="164" cy="100" r="48" fill={`url(#${gradient})`} />
            <path
              d="M55 358V259c0-61 45-100 109-100s109 39 109 100v99Z"
              fill={`url(#${gradient})`}
            />
            <path
              d="m108 166 56 74 56-74M164 240v118"
              stroke="currentColor"
              strokeOpacity=".23"
              strokeWidth="2"
              fill="none"
            />
          </svg>
          <span className="portrait-initials" aria-hidden="true">
            {player.name
              .split(" ")
              .map((n) => n[0])
              .slice(0, 2)
              .join("")}
          </span>
          <span className="portrait-caption">Player portrait forthcoming</span>
        </>
      )}
      <span className="portrait-number" aria-hidden="true">
        {String(player.rank).padStart(2, "0")}
      </span>
    </div>
  );
}
