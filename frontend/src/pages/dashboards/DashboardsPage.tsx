import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import type { ByDomainRow, ConfidenceRobustness, NeedsAttentionItem, PortfolioDashboard } from "../../api/types";

export function DashboardsPage() {
  const [portfolio, setPortfolio] = useState<PortfolioDashboard | null>(null);
  const [byDomain, setByDomain] = useState<ByDomainRow[]>([]);
  const [confidence, setConfidence] = useState<ConfidenceRobustness | null>(null);
  const [needsAttention, setNeedsAttention] = useState<NeedsAttentionItem[]>([]);

  useEffect(() => {
    api.portfolio().then(setPortfolio);
    api.byDomain().then(setByDomain);
    api.confidence().then(setConfidence);
    api.needsAttention().then(setNeedsAttention);
  }, []);

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <h1 style={{ fontSize: 22, margin: 0 }}>Portfolio overview</h1>

      <div className="ds-card">
        <div className="ds-label">Total assessments</div>
        <div style={{ fontSize: 32, fontWeight: 700 }}>{portfolio?.total ?? "—"}</div>
        {portfolio && (
          <div style={{ display: "flex", gap: 24, marginTop: 12, flexWrap: "wrap" }}>
            <div>
              <div className="ds-label">By status</div>
              {Object.entries(portfolio.by_status).map(([k, v]) => (
                <div key={k} style={{ fontSize: 14 }}>
                  {k}: <strong>{v}</strong>
                </div>
              ))}
            </div>
            <div>
              <div className="ds-label">By recommendation</div>
              {Object.entries(portfolio.by_recommendation).map(([k, v]) => (
                <div key={k} style={{ fontSize: 14 }}>
                  {k}: <strong>{v}</strong>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="ds-card">
        <div className="ds-label" style={{ marginBottom: 10 }}>
          By domain
        </div>
        <table className="ds-table">
          <thead>
            <tr>
              <th>Domain</th>
              <th>Total</th>
              <th>Private</th>
              <th>Public</th>
              <th>Pending / other</th>
            </tr>
          </thead>
          <tbody>
            {byDomain.map((row) => (
              <tr key={row.domain}>
                <td>{row.domain}</td>
                <td>{row.total}</td>
                <td>{row.private_count}</td>
                <td>{row.public_count}</td>
                <td>{row.pending_or_other_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="ds-card">
        <div className="ds-label" style={{ marginBottom: 10 }}>
          Confidence &amp; robustness
        </div>
        {confidence && (
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
            <div>
              {Object.entries(confidence.by_confidence).map(([k, v]) => (
                <div key={k} style={{ fontSize: 14 }}>
                  {k}: <strong>{v}</strong>
                </div>
              ))}
            </div>
            <div>
              <div style={{ fontSize: 14 }}>Robust: <strong>{confidence.robust_count}</strong></div>
              <div style={{ fontSize: 14 }}>Fragile: <strong>{confidence.fragile_count}</strong></div>
              <div style={{ fontSize: 14 }}>Unknown: <strong>{confidence.unknown_count}</strong></div>
            </div>
          </div>
        )}
      </div>

      <div className="ds-card">
        <div className="ds-label" style={{ marginBottom: 10 }}>
          Needs attention
        </div>
        {needsAttention.length === 0 && <p style={{ color: "var(--ds-text-secondary)", fontSize: 14 }}>Nothing needs attention right now.</p>}
        <table className="ds-table">
          <tbody>
            {needsAttention.map((item, i) => (
              <tr key={i}>
                <td>
                  <Link to={`/assessments/${item.assessment_id}`}>{item.app_name}</Link>
                  <div style={{ color: "var(--ds-text-secondary)", fontSize: 12 }}>{item.domain}</div>
                </td>
                <td>{item.issue}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
