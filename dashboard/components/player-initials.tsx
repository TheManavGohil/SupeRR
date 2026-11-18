export function PlayerInitials({ name }: { name: string }) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const initials =
    parts.length > 1
      ? `${parts[0][0]}${parts.at(-1)![0]}`
      : (parts[0]?.[0] ?? "");
  return (
    <div className="player-initials" aria-hidden="true">
      <span>{initials.toLocaleUpperCase("en-GB")}</span>
    </div>
  );
}
