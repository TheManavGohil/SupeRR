import Image from "next/image";
import assets from "@/content/player-assets.json";
import type { Player } from "@/lib/types";

type Asset = {
  src: string;
  alt: string;
  width: number;
  height: number;
  crop: { x: number; y: number; width: number; height: number };
  trim: readonly number[];
  attribution?: string;
};
export function Portrait({
  player,
  variant = "card",
}: {
  player: Pick<Player, "id" | "role" | "name" | "rank">;
  variant?: "card" | "profile" | "hero";
}) {
  const asset = (assets as Record<string, Asset>)[player.id];
  const hero = variant === "hero";
  const sourceScale = asset ? asset.width / asset.crop.width : 1;
  const gradient = `s-${hero ? "hero" : "card"}-${player.role}-${player.id}`;
  return (
    <div
      className={`portrait ${player.role} portrait-${variant} ${asset ? "portrait-has-image" : ""}`}
      data-player-id={player.id}
    >
      {asset ? (
        <div className="portrait-photo-frame">
          <Image
            className="portrait-photo"
            src={asset.src}
            alt={asset.alt}
            width={asset.width}
            height={asset.height}
            sizes={
              hero
                ? `(max-width: 600px) ${Math.round(360 * sourceScale)}px, ${Math.round(560 * sourceScale)}px`
                : variant === "profile"
                  ? `(max-width: 600px) ${(90 * sourceScale).toFixed(2)}vw, ${Math.round(450 * sourceScale)}px`
                  : `(max-width: 600px) ${(90 * sourceScale).toFixed(2)}vw, (max-width: 1100px) ${(43 * sourceScale).toFixed(2)}vw, ${Math.round(400 * sourceScale)}px`
            }
            style={{
              // A fixed 4:5 viewport preserves the original image proportions.
              // Negative crop origins add white space around narrow screenshots.
              width: `${(asset.width / asset.crop.width) * 100}%`,
              left: `${(-asset.crop.x / asset.crop.width) * 100}%`,
              top: `${(-asset.crop.y / asset.crop.height) * 100}%`,
              clipPath: `inset(${asset.trim
                .map(
                  (n, i) =>
                    `${(n / (i % 2 === 0 ? asset.height : asset.width)) * 100}%`,
                )
                .join(" ")})`,
            }}
            preload={hero}
          />
        </div>
      ) : (
        <>
          <span className="portrait-orbit" aria-hidden="true" />
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
