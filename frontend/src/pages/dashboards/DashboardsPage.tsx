import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { ConfidencePill, RecommendationPill, StatusPill } from "../../components/StatusPill";
import type { ByDomainRow, ConfidenceRobustness, NeedsAttentionItem, PortfolioDashboard } from "../../api/types";

function CountRow({ pill, count }: { pill: React.ReactNode; count: number }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, padding: "4px 0" }}>
      {pill}
      <strong style={{ fontSize: 14 }}>{count}</strong>
    </div>
  );
}

export function DashboardsPage() {
  const { hasRole } = useAuth();
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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ fontSize: 22, margin: 0 }}>Portfolio overview</h1>
        {hasRole("assessor", "admin") && (
          <Link className="ds-btn ds-btn-primary" to="/assessments/new">
            + New assessment
          </Link>
        )}
      </div>

      <div className="ds-card">
        <div className="ds-label">Total assessments</div>
        <div style={{ fontSize: 32, fontWeight: 700, marginBottom: 12 }}>{portfolio?.total ?? "—"}</div>
        {portfolio && (
          <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
            <div style={{ minWidth: 160 }}>
              <div className="ds-label">By status</div>
              {Object.entries(portfolio.by_status).map(([k, v]) => (
                <CountRow key={k} pill={<StatusPill status={k} />} count={v} />
              ))}
            </div>
            <div style={{ minWidth: 200 }}>
              <div className="ds-label">By recommendation</div>
              {Object.entries(portfolio.by_recommendation).map(([k, v]) => (
                <CountRow key={k} pill={<RecommendationPill recommendation={k} />} count={v} />
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
          <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
            <div style={{ minWidth: 160 }}>
              {Object.entries(confidence.by_confidence).map(([k, v]) => (
                <CountRow key={k} pill={<ConfidencePill confidence={k} />} count={v} />
              ))}
            </div>
            <div style={{ minWidth: 160 }}>
              <CountRow pill={<span style={{ fontSize: 14 }}>Robust</span>} count={confidence.robust_count} />
              <CountRow pill={<span style={{ fontSize: 14 }}>Fragile</span>} count={confidence.fragile_count} />
              <CountRow pill={<span style={{ fontSize: 14, color: "var(--ds-text-secondary)" }}>Unknown</span>} count={confidence.unknown_count} />
            </div>
          </div>
        )}
      </div>

      <div className="ds-card">
        <div className="ds-label" style={{ marginBottom: 10 }}>
          Needs attention
        </div>
        {needsAttention.length === 0 ? (
          <p style={{ color: "var(--ds-text-secondary)", fontSize: 14 }}>Nothing needs attention right now.</p>
        ) : (
          <table className="ds-table">
            <thead>
              <tr>
                <th>Assessment</th>
                <th>Issue</th>
              </tr>
            </thead>
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
        )}
      </div>
    </div>
  );
}
