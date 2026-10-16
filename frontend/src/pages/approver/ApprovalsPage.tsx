import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { RecommendationPill } from "../../components/StatusPill";
import type { AssessmentListItem } from "../../api/types";

function Queue({ title, items }: { title: string; items: AssessmentListItem[] }) {
  return (
    <div className="ds-card">
      <h2 style={{ fontSize: 16, marginTop: 0 }}>{title}</h2>
      {items.length === 0 && <p style={{ color: "var(--ds-text-secondary)", fontSize: 14 }}>Nothing waiting here.</p>}
      <table className="ds-table">
        <tbody>
          {items.map((a) => (
            <tr key={a.id}>
              <td>
                <Link to={`/assessments/${a.id}`}>{a.app_name}</Link>
                <div style={{ color: "var(--ds-text-secondary)", fontSize: 12 }}>{a.domain.name}</div>
              </td>
              <td>
                <RecommendationPill recommendation={a.recommendation} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ApprovalsPage() {
  const [submitted, setSubmitted] = useState<AssessmentListItem[]>([]);
  const [endorsed, setEndorsed] = useState<AssessmentListItem[]>([]);

  useEffect(() => {
    api.listAssessments({ status: "submitted" }).then(setSubmitted);
    api.listAssessments({ status: "endorsed" }).then(setEndorsed);
  }, []);

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <h1 style={{ fontSize: 22, margin: 0 }}>Approvals</h1>
      <Queue title="Awaiting Hosting Advisory Group endorsement" items={submitted} />
      <Queue title="Awaiting Management Board decision" items={endorsed} />
    </div>
  );
}
