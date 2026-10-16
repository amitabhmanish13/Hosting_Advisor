import type { AssessmentResult } from "../api/types";
import { ConfidencePill, RecommendationPill } from "./StatusPill";

export function ResultCard({ result }: { result: AssessmentResult | null }) {
  if (!result) return null;
  const privatePct = result.private_fit != null ? Math.round(result.private_fit * 100) : null;
  const publicPct = result.public_fit != null ? Math.round(result.public_fit * 100) : null;
  // The pill already states the outcome; only show a second line when the
  // engine's text has something the pill's short label doesn't (the "why"
  // on Conflict/Near-tie/Pending) — never repeat "Private Cloud / On-Prem"
  // or "Public Cloud" verbatim right under their own pill.
  const [, explanation] = result.recommendation.split(" — ");

  return (
    <div className="ds-card">
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <RecommendationPill recommendation={result.recommendation} />
        <ConfidencePill confidence={result.confidence} />
        {result.robust !== null && (
          <span className="ds-pill" style={{ background: "var(--ds-chip-neutral-bg)", color: "var(--ds-chip-neutral-fg)" }}>
            {result.robust ? "Robust — no single answer can flip this" : "Fragile — one answer could flip this"}
          </span>
        )}
        {!result.evidence_complete && (
          <span className="ds-pill" style={{ background: "var(--ds-chip-warn-bg)", color: "var(--ds-chip-warn-fg)" }}>
            Evidence incomplete
          </span>
        )}
      </div>

      {explanation && <p style={{ color: "var(--ds-text-secondary)", fontSize: 14, margin: "12px 0 0" }}>{explanation}</p>}

      {privatePct != null && publicPct != null && (
        <>
          <div style={{ display: "flex", height: 10, borderRadius: 999, overflow: "hidden", background: "var(--ds-chip-neutral-bg)", marginTop: 14 }}>
            <div style={{ width: `${privatePct}%`, background: "var(--ds-chip-private-fg)" }} />
            <div style={{ width: `${publicPct}%`, background: "var(--ds-chip-public-fg)" }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 13, color: "var(--ds-text-secondary)" }}>
            <span>Private {privatePct}%</span>
            <span>Public {publicPct}%</span>
          </div>
        </>
      )}

      {(result.top_private_drivers.length > 0 || result.top_public_drivers.length > 0) && (
        <div style={{ display: "flex", gap: 24, marginTop: 16, flexWrap: "wrap" }}>
          {result.top_private_drivers.length > 0 && (
            <div>
              <div className="ds-label">Strongest Private-leaning evidence</div>
              {result.top_private_drivers.map((d) => (
                <div key={d.code} style={{ fontSize: 14 }}>
                  {d.code} — {d.dimension}
                </div>
              ))}
            </div>
          )}
          {result.top_public_drivers.length > 0 && (
            <div>
              <div className="ds-label">Strongest Public-leaning evidence</div>
              {result.top_public_drivers.map((d) => (
                <div key={d.code} style={{ fontSize: 14 }}>
                  {d.code} — {d.dimension}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
