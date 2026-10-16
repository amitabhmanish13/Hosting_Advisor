import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { QuestionnaireSummary, QuestionnaireVersion } from "../../api/types";

type KoRow = { code: string; direction: string; dimension: string; question_text: string; evidence_hint: string; dhl_ref: string };
type ScRow = {
  code: string;
  dimension: string;
  question_text: string;
  evidence_hint: string;
  band_a_text: string;
  band_b_text: string;
  band_c_text: string;
  band_d_text: string;
  band_e_text: string;
  dhl_ref: string;
};

function toKoRows(v: QuestionnaireVersion): KoRow[] {
  return v.knockout_questions.map((k) => ({
    code: k.code,
    direction: k.direction,
    dimension: k.dimension,
    question_text: k.question_text,
    evidence_hint: k.evidence_hint ?? "",
    dhl_ref: k.dhl_ref ?? "",
  }));
}

function toScRows(v: QuestionnaireVersion): ScRow[] {
  return v.scoring_questions.map((s) => ({
    code: s.code,
    dimension: s.dimension,
    question_text: s.question_text,
    evidence_hint: s.evidence_hint ?? "",
    band_a_text: s.band_a_text,
    band_b_text: s.band_b_text,
    band_c_text: s.band_c_text,
    band_d_text: s.band_d_text,
    band_e_text: s.band_e_text,
    dhl_ref: s.dhl_ref ?? "",
  }));
}

export function QuestionEditorPage() {
  const [draft, setDraft] = useState<QuestionnaireVersion | null>(null);
  const [versions, setVersions] = useState<QuestionnaireSummary[]>([]);
  const [kos, setKos] = useState<KoRow[]>([]);
  const [scs, setScs] = useState<ScRow[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [versionLabel, setVersionLabel] = useState("");
  const [changelog, setChangelog] = useState("");

  const load = () => {
    api.getDraft().then((d) => {
      setDraft(d);
      setKos(toKoRows(d));
      setScs(toScRows(d));
    });
    api.listQuestionnaires().then(setVersions);
  };

  useEffect(load, []);

  if (!draft) return <p>Loading…</p>;

  const saveDraft = async () => {
    await api.updateDraft({ knockout_questions: kos, scoring_questions: scs });
    setNotice("Draft saved.");
  };

  const publish = async () => {
    if (!versionLabel || !changelog) {
      setNotice("Version label and changelog are required to publish.");
      return;
    }
    await saveDraft();
    await api.publishDraft(versionLabel, changelog);
    setNotice(`Published ${versionLabel}. New assessments will use it; existing assessments keep their original version.`);
    setVersionLabel("");
    setChangelog("");
    load();
  };

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <div>
        <h1 style={{ fontSize: 22, margin: 0 }}>Questionnaire editor — draft</h1>
        <p style={{ fontSize: 13, color: "var(--ds-text-secondary)", margin: "4px 0 0" }}>
          Safe to edit freely: nothing here is live until you publish, and every past assessment stays locked to the
          version it was scored against.
        </p>
      </div>
      {notice && <p style={{ color: "var(--ds-chip-success-fg)" }}>{notice}</p>}

      <div className="ds-card">
        <h2 style={{ fontSize: 16, marginTop: 0 }}>Part 1 — Knock-out questions</h2>
        {kos.map((k, i) => (
          <div key={i} className="ds-card" style={{ marginBottom: 10, display: "grid", gap: 6 }}>
            <div style={{ display: "flex", gap: 8 }}>
              <input className="ds-input" style={{ maxWidth: 90 }} value={k.code} onChange={(e) => setKos((p) => p.map((x, j) => (j === i ? { ...x, code: e.target.value } : x)))} placeholder="KO1" />
              <select className="ds-select" style={{ maxWidth: 140 }} value={k.direction} onChange={(e) => setKos((p) => p.map((x, j) => (j === i ? { ...x, direction: e.target.value } : x)))}>
                <option value="private">private</option>
                <option value="public">public</option>
              </select>
              <input className="ds-input" value={k.dimension} onChange={(e) => setKos((p) => p.map((x, j) => (j === i ? { ...x, dimension: e.target.value } : x)))} placeholder="Dimension" />
              <button className="ds-btn" onClick={() => setKos((p) => p.filter((_, j) => j !== i))}>✕</button>
            </div>
            <textarea className="ds-textarea" rows={2} value={k.question_text} onChange={(e) => setKos((p) => p.map((x, j) => (j === i ? { ...x, question_text: e.target.value } : x)))} placeholder="Question text" />
            <input className="ds-input" value={k.evidence_hint} onChange={(e) => setKos((p) => p.map((x, j) => (j === i ? { ...x, evidence_hint: e.target.value } : x)))} placeholder="Evidence required" />
          </div>
        ))}
        <button className="ds-btn" onClick={() => setKos((p) => [...p, { code: "", direction: "private", dimension: "", question_text: "", evidence_hint: "", dhl_ref: "" }])}>
          + Add knock-out
        </button>
      </div>

      <div className="ds-card">
        <h2 style={{ fontSize: 16, marginTop: 0 }}>Part 2 — Scoring questions</h2>
        {scs.map((s, i) => (
          <div key={i} className="ds-card" style={{ marginBottom: 10, display: "grid", gap: 6 }}>
            <div style={{ display: "flex", gap: 8 }}>
              <input className="ds-input" style={{ maxWidth: 90 }} value={s.code} onChange={(e) => setScs((p) => p.map((x, j) => (j === i ? { ...x, code: e.target.value } : x)))} placeholder="Q1" />
              <input className="ds-input" value={s.dimension} onChange={(e) => setScs((p) => p.map((x, j) => (j === i ? { ...x, dimension: e.target.value } : x)))} placeholder="Dimension" />
              <button className="ds-btn" onClick={() => setScs((p) => p.filter((_, j) => j !== i))}>✕</button>
            </div>
            <textarea className="ds-textarea" rows={2} value={s.question_text} onChange={(e) => setScs((p) => p.map((x, j) => (j === i ? { ...x, question_text: e.target.value } : x)))} placeholder="Question text" />
            {(["band_a_text", "band_b_text", "band_c_text", "band_d_text", "band_e_text"] as const).map((field, bi) => (
              <input
                key={field}
                className="ds-input"
                value={s[field]}
                onChange={(e) => setScs((p) => p.map((x, j) => (j === i ? { ...x, [field]: e.target.value } : x)))}
                placeholder={`Band ${"ABCDE"[bi]} definition`}
              />
            ))}
          </div>
        ))}
        <button
          className="ds-btn"
          onClick={() =>
            setScs((p) => [
              ...p,
              { code: "", dimension: "", question_text: "", evidence_hint: "", band_a_text: "", band_b_text: "", band_c_text: "", band_d_text: "", band_e_text: "", dhl_ref: "" },
            ])
          }
        >
          + Add scoring question
        </button>
      </div>

      <div className="ds-card">
        <h2 style={{ fontSize: 16, marginTop: 0 }}>Save &amp; publish</h2>
        <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
          <button className="ds-btn" onClick={saveDraft}>
            Save draft
          </button>
        </div>
        <label className="ds-label">New version label (e.g. v1.1)</label>
        <input className="ds-input" style={{ marginBottom: 10 }} value={versionLabel} onChange={(e) => setVersionLabel(e.target.value)} />
        <label className="ds-label">Changelog (required — recorded for governance)</label>
        <textarea className="ds-textarea" rows={2} value={changelog} onChange={(e) => setChangelog(e.target.value)} style={{ marginBottom: 10 }} />
        <button className="ds-btn ds-btn-primary" onClick={publish}>
          Publish — existing assessments stay on their original version
        </button>
      </div>

      <div className="ds-card">
        <h2 style={{ fontSize: 16, marginTop: 0 }}>Version history</h2>
        <table className="ds-table">
          <thead>
            <tr>
              <th>Version</th>
              <th>Status</th>
              <th>Published</th>
              <th>Changelog</th>
              <th>Assessments scored against it</th>
            </tr>
          </thead>
          <tbody>
            {versions.map((v) => (
              <tr key={v.id}>
                <td>{v.version_label}</td>
                <td>{v.status}</td>
                <td>{v.published_at ? new Date(v.published_at).toLocaleDateString() : "—"}</td>
                <td>{v.changelog}</td>
                <td>{v.assessment_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
