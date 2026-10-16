import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import type { Domain } from "../../api/types";

export function NewAssessmentPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [domains, setDomains] = useState<Domain[]>([]);
  const [form, setForm] = useState({
    app_name: "",
    domain_id: "",
    business_owner: "",
    technical_owner: "",
    data_classification: "",
    business_criticality: "",
    current_hosting: "",
    target_go_live: "",
    rto_rpo: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.domains().then((all) => {
      setDomains(all);
      const mine = all.find((d) => d.name === user?.domain);
      if (mine) setForm((f) => ({ ...f, domain_id: String(mine.id) }));
    });
  }, [user?.domain]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.app_name || !form.domain_id) {
      setError("Application name and domain are required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const created = await api.createAssessment({
        ...form,
        domain_id: Number(form.domain_id),
        target_go_live: form.target_go_live || undefined,
      });
      navigate(`/assessments/${created.id}`);
    } catch {
      setError("Could not create assessment.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: 560 }}>
      <h1 style={{ fontSize: 22 }}>New assessment — Workload profile</h1>
      <form onSubmit={submit} className="ds-card" style={{ display: "grid", gap: 14 }}>
        <div>
          <label className="ds-label">Application / workload name *</label>
          <input className="ds-input" value={form.app_name} onChange={(e) => setForm({ ...form, app_name: e.target.value })} />
        </div>
        <div>
          <label className="ds-label">Domain *</label>
          <select className="ds-select" value={form.domain_id} onChange={(e) => setForm({ ...form, domain_id: e.target.value })}>
            <option value="">Select domain…</option>
            {domains.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="ds-label">Business owner</label>
          <input className="ds-input" value={form.business_owner} onChange={(e) => setForm({ ...form, business_owner: e.target.value })} />
        </div>
        <div>
          <label className="ds-label">Technical owner</label>
          <input className="ds-input" value={form.technical_owner} onChange={(e) => setForm({ ...form, technical_owner: e.target.value })} />
        </div>
        <div>
          <label className="ds-label">Data classification</label>
          <input className="ds-input" value={form.data_classification} onChange={(e) => setForm({ ...form, data_classification: e.target.value })} placeholder="e.g. For Internal Use" />
        </div>
        <div>
          <label className="ds-label">Business criticality</label>
          <input className="ds-input" value={form.business_criticality} onChange={(e) => setForm({ ...form, business_criticality: e.target.value })} />
        </div>
        <div>
          <label className="ds-label">Current hosting</label>
          <input className="ds-input" value={form.current_hosting} onChange={(e) => setForm({ ...form, current_hosting: e.target.value })} />
        </div>
        <div>
          <label className="ds-label">Target go-live</label>
          <input type="date" className="ds-input" value={form.target_go_live} onChange={(e) => setForm({ ...form, target_go_live: e.target.value })} />
        </div>
        <div>
          <label className="ds-label">Required RTO / RPO</label>
          <input className="ds-input" value={form.rto_rpo} onChange={(e) => setForm({ ...form, rto_rpo: e.target.value })} />
        </div>
        {error && <p style={{ color: "var(--dhl-red)", fontSize: 13 }}>{error}</p>}
        <button className="ds-btn ds-btn-primary" disabled={saving}>
          {saving ? "Creating…" : "Create & start questionnaire"}
        </button>
      </form>
    </div>
  );
}
