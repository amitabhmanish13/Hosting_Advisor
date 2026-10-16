import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { ResultCard } from "../../components/ResultCard";
import { StatusPill } from "../../components/StatusPill";
import type { AssessmentDetail, KnockoutAnswer, ScoringAnswer } from "../../api/types";

const BANDS = ["A", "B", "C", "D", "E"] as const;

export function AssessmentDetailPage() {
  const { id } = useParams();
  const assessmentId = Number(id);
  const { hasRole } = useAuth();

  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [knockouts, setKnockouts] = useState<KnockoutAnswer[]>([]);
  const [scorings, setScorings] = useState<ScoringAnswer[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [handoffUrl, setHandoffUrl] = useState<string | null>(null);

  const load = () => {
    api.getAssessment(assessmentId).then((a) => {
      setAssessment(a);
      setKnockouts(a.knockout_answers);
      setScorings(a.scoring_answers);
    });
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assessmentId]);

  if (!assessment) return <p>Loading…</p>;

  const answeredCount = knockouts.filter((k) => k.answer).length + scorings.filter((s) => s.band).length;
  const totalCount = knockouts.length + scorings.length;
  const isComplete = answeredCount === totalCount;

  const canEdit = assessment.status === "draft" && hasRole("assessor", "admin");
  const canSubmit = assessment.status === "draft" && hasRole("assessor", "admin");
  const canEndorse = assessment.status === "submitted" && hasRole("approver", "admin");
  const canDecide = assessment.status === "endorsed" && hasRole("approver", "admin");
  const canHandoff = assessment.status === "decided" && assessment.result && ["Private Cloud / On-Prem", "Public Cloud"].includes(assessment.result.recommendation);

  const saveAnswers = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateAnswers(assessmentId, {
        knockout_answers: knockouts.map((k) => ({ knockout_question_id: k.knockout_question_id, answer: k.answer, evidence_reference: k.evidence_reference })),
        scoring_answers: scorings.map((s) => ({ scoring_question_id: s.scoring_question_id, band: s.band, evidence_reference: s.evidence_reference })),
      });
      setAssessment(updated);
      setKnockouts(updated.knockout_answers);
      setScorings(updated.scoring_answers);
      setNotice("Saved.");
    } catch {
      setError("Could not save answers.");
    } finally {
      setSaving(false);
    }
  };

  const runAction = async (action: () => Promise<AssessmentDetail>, successMsg: string) => {
    setSaving(true);
    setError(null);
    try {
      const updated = await action();
      setAssessment(updated);
      setKnockouts(updated.knockout_answers);
      setScorings(updated.scoring_answers);
      setNotice(successMsg);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 style={{ fontSize: 22, margin: 0 }}>{assessment.app_name}</h1>
          <p style={{ color: "var(--ds-text-secondary)", margin: "4px 0" }}>
            {assessment.domain.name} · Questionnaire {assessment.questionnaire_version.version_label}
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {canEdit && (
            <span style={{ fontSize: 13, color: isComplete ? "var(--ds-chip-success-fg)" : "var(--ds-text-secondary)" }}>
              {answeredCount} / {totalCount} answered
            </span>
          )}
          <StatusPill status={assessment.status} />
        </div>
      </div>

      <ResultCard result={assessment.result} />

      {error && <p style={{ color: "var(--dhl-red)" }}>{error}</p>}
      {notice && <p style={{ color: "var(--ds-chip-success-fg)" }}>{notice}</p>}

      <div className="ds-card">
        <h2 style={{ fontSize: 16, marginTop: 0 }}>Part 1 — Knock-out questions</h2>
        <p style={{ fontSize: 13, color: "var(--ds-text-secondary)", marginTop: -8, marginBottom: 16 }}>
          A "Yes" decides placement on its own — answer only from evidence, never a guess.
        </p>
        {knockouts.map((k, i) => {
          const needsEvidence = k.answer === "yes" && !k.evidence_reference;
          return (
            <div
              key={k.knockout_question_id}
              style={{
                padding: "12px 12px 12px 14px",
                borderBottom: "1px solid var(--ds-border)",
                borderLeft: `3px solid ${k.answer ? "var(--ds-chip-success-fg)" : "var(--ds-border)"}`,
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 14 }}>
                {k.code} · {k.dimension}
              </div>
              <p style={{ fontSize: 14, margin: "4px 0 8px" }}>{k.question_text}</p>
              <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
                <label style={{ fontSize: 14 }}>
                  <input
                    type="radio"
                    disabled={!canEdit}
                    checked={k.answer === "yes"}
                    onChange={() => setKnockouts((prev) => prev.map((x, j) => (j === i ? { ...x, answer: "yes" } : x)))}
                  />{" "}
                  Yes
                </label>
                <label style={{ fontSize: 14 }}>
                  <input
                    type="radio"
                    disabled={!canEdit}
                    checked={k.answer === "no"}
                    onChange={() => setKnockouts((prev) => prev.map((x, j) => (j === i ? { ...x, answer: "no" } : x)))}
                  />{" "}
                  No
                </label>
                <input
                  className="ds-input"
                  style={{ maxWidth: 320, borderColor: needsEvidence ? "var(--dhl-red)" : undefined }}
                  placeholder="Evidence — doc ref, note, or estimate"
                  disabled={!canEdit}
                  value={k.evidence_reference ?? ""}
                  onChange={(e) => setKnockouts((prev) => prev.map((x, j) => (j === i ? { ...x, evidence_reference: e.target.value } : x)))}
                />
                {needsEvidence && <span style={{ fontSize: 12, color: "var(--dhl-red)" }}>Required for a "Yes"</span>}
              </div>
            </div>
          );
        })}
      </div>

      <div className="ds-card">
        <h2 style={{ fontSize: 16, marginTop: 0 }}>Part 2 — Scoring questions (band A–E)</h2>
        <p style={{ fontSize: 13, color: "var(--ds-text-secondary)", marginTop: -8, marginBottom: 16 }}>
          Pick the band whose definition the evidence actually matches — C is genuine parity, not "I don't know."
        </p>
        {scorings.map((s, i) => {
          const needsEvidence = !!s.band && !s.evidence_reference;
          return (
            <div
              key={s.scoring_question_id}
              style={{
                padding: "12px 12px 12px 14px",
                borderBottom: "1px solid var(--ds-border)",
                borderLeft: `3px solid ${s.band ? "var(--ds-chip-success-fg)" : "var(--ds-border)"}`,
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 14 }}>
                {s.code} · {s.dimension}
              </div>
              <p style={{ fontSize: 14, margin: "4px 0 8px" }}>{s.question_text}</p>
              <div style={{ display: "grid", gap: 4, marginBottom: 8 }}>
                {([["A", s.band_a_text], ["B", s.band_b_text], ["C", s.band_c_text], ["D", s.band_d_text], ["E", s.band_e_text]] as const).map(
                  ([letter, text]) => (
                    <label key={letter} style={{ fontSize: 13, color: "var(--ds-text-secondary)", display: "flex", gap: 6 }}>
                      <input
                        type="radio"
                        disabled={!canEdit}
                        checked={s.band === letter}
                        onChange={() => setScorings((prev) => prev.map((x, j) => (j === i ? { ...x, band: letter as (typeof BANDS)[number] } : x)))}
                      />
                      <span>
                        <strong>{letter}</strong> = {text}
                      </span>
                    </label>
                  )
                )}
              </div>
              <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                <input
                  className="ds-input"
                  style={{ maxWidth: 320, borderColor: needsEvidence ? "var(--dhl-red)" : undefined }}
                  placeholder="Evidence — doc ref, note, or estimate"
                  disabled={!canEdit}
                  value={s.evidence_reference ?? ""}
                  onChange={(e) => setScorings((prev) => prev.map((x, j) => (j === i ? { ...x, evidence_reference: e.target.value } : x)))}
                />
                {needsEvidence && <span style={{ fontSize: 12, color: "var(--dhl-red)" }}>Required for a scored answer</span>}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        {canEdit && (
          <button className="ds-btn" disabled={saving} onClick={saveAnswers}>
            Save progress
          </button>
        )}
        {canSubmit && (
          <button
            className="ds-btn ds-btn-primary"
            disabled={saving || !isComplete}
            title={isComplete ? undefined : `Answer all ${totalCount} questions first (${answeredCount} done)`}
            onClick={() => runAction(() => api.submit(assessmentId), "Submitted for endorsement.")}
          >
            Submit for endorsement{!isComplete && ` (${answeredCount}/${totalCount})`}
          </button>
        )}
        {canEndorse && (
          <button className="ds-btn ds-btn-primary" disabled={saving} onClick={() => runAction(() => api.endorse(assessmentId), "Endorsed.")}>
            Endorse (Hosting Advisory Group)
          </button>
        )}
        {canDecide && (
          <button className="ds-btn ds-btn-primary" disabled={saving} onClick={() => runAction(() => api.decide(assessmentId), "Board decision recorded.")}>
            Record Board decision
          </button>
        )}
        {canHandoff && !handoffUrl && (
          <button className="ds-btn ds-btn-primary" onClick={() => api.handoff(assessmentId).then((h) => setHandoffUrl(h.url))}>
            Proceed in IPP →
          </button>
        )}
        {handoffUrl && (
          <a className="ds-btn ds-btn-primary" href={handoffUrl} target="_blank" rel="noreferrer">
            Open in IPP →
          </a>
        )}
      </div>

      {assessment.workflow_events.length > 0 && (
        <div className="ds-card">
          <h2 style={{ fontSize: 16, marginTop: 0 }}>Workflow history</h2>
          {assessment.workflow_events.map((e, i) => (
            <div key={i} style={{ fontSize: 13, padding: "6px 0", borderBottom: "1px solid var(--ds-border)" }}>
              <strong>
                {e.from_status} → {e.to_status}
              </strong>{" "}
              <span style={{ color: "var(--ds-text-secondary)" }}>{new Date(e.created_at).toLocaleString()}</span>
              {e.notes && <div style={{ color: "var(--ds-text-secondary)" }}>{e.notes}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
