import type {
  AssessmentDetail,
  AssessmentListItem,
  ByDomainRow,
  ConfidenceRobustness,
  Domain,
  Handoff,
  Me,
  NeedsAttentionItem,
  PortfolioDashboard,
  QuestionnaireSummary,
  QuestionnaireVersion,
  UserAccount,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  loginUrl: () => `${BASE_URL}/auth/login`,
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  me: () => request<Me>("/auth/me"),

  domains: () => request<Domain[]>("/domains"),
  createDomain: (name: string) => request<Domain>("/domains", { method: "POST", body: JSON.stringify({ name }) }),

  users: () => request<UserAccount[]>("/users"),
  addRole: (userId: number, role: string, domainId: number | null) =>
    request<UserAccount>(`/users/${userId}/roles`, { method: "POST", body: JSON.stringify({ role, domain_id: domainId }) }),
  removeRole: (userId: number, roleId: number) => request<UserAccount>(`/users/${userId}/roles/${roleId}`, { method: "DELETE" }),

  currentQuestionnaire: () => request<QuestionnaireVersion>("/questionnaires/current"),
  listQuestionnaires: () => request<QuestionnaireSummary[]>("/questionnaires"),
  getDraft: () => request<QuestionnaireVersion>("/questionnaires/draft"),
  updateDraft: (payload: { knockout_questions: unknown[]; scoring_questions: unknown[] }) =>
    request<QuestionnaireVersion>("/questionnaires/draft", { method: "PUT", body: JSON.stringify(payload) }),
  publishDraft: (versionLabel: string, changelog: string) =>
    request<QuestionnaireVersion>("/questionnaires/draft/publish", {
      method: "POST",
      body: JSON.stringify({ version_label: versionLabel, changelog }),
    }),

  createAssessment: (payload: {
    app_name: string;
    domain_id: number;
    business_owner?: string;
    technical_owner?: string;
    data_classification?: string;
    business_criticality?: string;
    current_hosting?: string;
    target_go_live?: string;
    rto_rpo?: string;
  }) => request<AssessmentDetail>("/assessments", { method: "POST", body: JSON.stringify(payload) }),
  listAssessments: (params?: { domain_id?: number; status?: string }) => {
    const qs = new URLSearchParams();
    if (params?.domain_id) qs.set("domain_id", String(params.domain_id));
    if (params?.status) qs.set("status", params.status);
    const suffix = qs.toString() ? `?${qs}` : "";
    return request<AssessmentListItem[]>(`/assessments${suffix}`);
  },
  getAssessment: (id: number) => request<AssessmentDetail>(`/assessments/${id}`),
  updateProfile: (id: number, payload: Record<string, unknown>) =>
    request<AssessmentDetail>(`/assessments/${id}/profile`, { method: "PUT", body: JSON.stringify(payload) }),
  updateAnswers: (
    id: number,
    payload: {
      knockout_answers: { knockout_question_id: number; answer: string | null; evidence_reference: string | null }[];
      scoring_answers: { scoring_question_id: number; band: string | null; evidence_reference: string | null }[];
    }
  ) => request<AssessmentDetail>(`/assessments/${id}/answers`, { method: "PUT", body: JSON.stringify(payload) }),

  submit: (id: number, notes?: string) =>
    request<AssessmentDetail>(`/assessments/${id}/workflow/submit`, { method: "POST", body: JSON.stringify({ notes }) }),
  endorse: (id: number, notes?: string) =>
    request<AssessmentDetail>(`/assessments/${id}/workflow/endorse`, { method: "POST", body: JSON.stringify({ notes }) }),
  decide: (id: number, notes?: string) =>
    request<AssessmentDetail>(`/assessments/${id}/workflow/decide`, { method: "POST", body: JSON.stringify({ notes }) }),

  handoff: (id: number) => request<Handoff>(`/assessments/${id}/handoff`),

  portfolio: () => request<PortfolioDashboard>("/dashboards/portfolio"),
  byDomain: () => request<ByDomainRow[]>("/dashboards/by-domain"),
  confidence: () => request<ConfidenceRobustness>("/dashboards/confidence"),
  needsAttention: () => request<NeedsAttentionItem[]>("/dashboards/needs-attention"),
};

export { ApiError };
