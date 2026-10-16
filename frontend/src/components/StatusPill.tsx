const STATUS_STYLE: Record<string, { bg: string; fg: string }> = {
  draft: { bg: "var(--ds-chip-neutral-bg)", fg: "var(--ds-chip-neutral-fg)" },
  submitted: { bg: "var(--ds-chip-warn-bg)", fg: "var(--ds-chip-warn-fg)" },
  endorsed: { bg: "var(--ds-chip-private-bg)", fg: "var(--ds-chip-private-fg)" },
  decided: { bg: "var(--ds-chip-success-bg)", fg: "var(--ds-chip-success-fg)" },
};

export function StatusPill({ status }: { status: string }) {
  const style = STATUS_STYLE[status] ?? STATUS_STYLE.draft;
  return (
    <span className="ds-pill" style={{ background: style.bg, color: style.fg }}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

export function RecommendationPill({ recommendation }: { recommendation: string | null }) {
  if (!recommendation) return <span className="ds-pill" style={{ background: "var(--ds-chip-neutral-bg)", color: "var(--ds-chip-neutral-fg)" }}>—</span>;
  if (recommendation.startsWith("Private"))
    return <span className="ds-pill" style={{ background: "var(--ds-chip-private-bg)", color: "var(--ds-chip-private-fg)" }}>Private Cloud / On-Prem</span>;
  if (recommendation.startsWith("Public"))
    return <span className="ds-pill" style={{ background: "var(--ds-chip-public-bg)", color: "var(--ds-chip-public-fg)" }}>Public Cloud</span>;
  if (recommendation.startsWith("Near-tie"))
    return <span className="ds-pill" style={{ background: "var(--ds-chip-warn-bg)", color: "var(--ds-chip-warn-fg)" }}>Near-tie</span>;
  if (recommendation.startsWith("Conflict"))
    return <span className="ds-pill" style={{ background: "var(--ds-chip-warn-bg)", color: "var(--ds-chip-warn-fg)" }}>Conflict</span>;
  return <span className="ds-pill" style={{ background: "var(--ds-chip-neutral-bg)", color: "var(--ds-chip-neutral-fg)" }}>Pending</span>;
}

export function ConfidencePill({ confidence }: { confidence: string }) {
  const map: Record<string, { bg: string; fg: string }> = {
    high: { bg: "var(--ds-chip-success-bg)", fg: "var(--ds-chip-success-fg)" },
    medium: { bg: "var(--ds-chip-warn-bg)", fg: "var(--ds-chip-warn-fg)" },
    low: { bg: "var(--ds-chip-public-bg)", fg: "var(--ds-chip-public-fg)" },
    "n/a": { bg: "var(--ds-chip-neutral-bg)", fg: "var(--ds-chip-neutral-fg)" },
  };
  const style = map[confidence] ?? map["n/a"];
  return (
    <span className="ds-pill" style={{ background: style.bg, color: style.fg }}>
      {confidence === "n/a" ? "N/A" : confidence.charAt(0).toUpperCase() + confidence.slice(1)} confidence
    </span>
  );
}
