import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { ConfidencePill, RecommendationPill, StatusPill } from "../../components/StatusPill";
import type { AssessmentListItem } from "../../api/types";

export function AssessmentsListPage() {
  const [items, setItems] = useState<AssessmentListItem[]>([]);

  useEffect(() => {
    api.listAssessments().then(setItems);
  }, []);

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ fontSize: 22, margin: 0 }}>My assessments</h1>
        <Link className="ds-btn ds-btn-primary" to="/assessments/new">
          + New assessment
        </Link>
      </div>

      <div className="ds-card">
        <table className="ds-table">
          <thead>
            <tr>
              <th>Application</th>
              <th>Domain</th>
              <th>Status</th>
              <th>Recommendation</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {items.map((a) => (
              <tr key={a.id}>
                <td>
                  <Link to={`/assessments/${a.id}`}>{a.app_name}</Link>
                </td>
                <td>{a.domain.name}</td>
                <td>
                  <StatusPill status={a.status} />
                </td>
                <td>
                  <RecommendationPill recommendation={a.recommendation} />
                </td>
                <td>{a.confidence && <ConfidencePill confidence={a.confidence} />}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} style={{ color: "var(--ds-text-secondary)" }}>
                  No assessments yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
