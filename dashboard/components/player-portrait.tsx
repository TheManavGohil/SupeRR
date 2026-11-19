import Image from "next/image";
import assets from "@/content/player-assets.json";
import type { Player } from "@/lib/types";
import { PlayerInitials } from "./player-initials";

type Asset = {
  src: string;
  width: number;
  height: number;
  crop: { x: number; y: number; width: number; height: number };
  trim: number[];
  sha256: string;
};

export function PlayerPortrait({
  player,
  variant = "card",
}: {
  player: Pick<Player, "id" | "name">;
  variant?: "card" | "profile" | "hero";
}) {
  const asset = (assets as Record<string, Asset>)[player.id];
  if (!asset) return <PlayerInitials name={player.name} />;
  const scale = asset.width / asset.crop.width;
  return (
    <div
      className={`player-portrait player-portrait-${variant}`}
      data-player-image={player.id}
    >
      <div className="player-portrait-frame">
        <Image
          className="player-portrait-photo"
          src={asset.src}
          alt={`${player.name} — supplied RR-kit illustration`}
          width={asset.width}
          height={asset.height}
          sizes={
            variant === "hero"
              ? `(max-width: 600px) ${Math.round(360 * scale)}px, ${Math.round(560 * scale)}px`
              : variant === "profile"
                ? `(max-width: 600px) ${(90 * scale).toFixed(2)}vw, ${Math.round(450 * scale)}px`
                : `(max-width: 600px) ${(90 * scale).toFixed(2)}vw, (max-width: 1100px) ${(43 * scale).toFixed(2)}vw, ${Math.round(400 * scale)}px`
          }
          style={{
            width: `${scale * 100}%`,
            left: `${(-asset.crop.x / asset.crop.width) * 100}%`,
            top: `${(-asset.crop.y / asset.crop.height) * 100}%`,
            clipPath: `inset(${asset.trim.map((n, i) => `${(n / (i % 2 === 0 ? asset.height : asset.width)) * 100}%`).join(" ")})`,
          }}
          preload={variant === "hero"}
        />
      </div>
    </div>
  );
}
