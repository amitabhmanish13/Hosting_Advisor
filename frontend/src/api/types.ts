export type Role = "admin" | "assessor" | "approver" | "viewer";
export type AssessmentStatus = "draft" | "submitted" | "endorsed" | "decided";

export interface Me {
  id: number;
  email: string;
  display_name: string;
  domain: string | null;
  roles: { role: Role; domain_id: number | null }[];
}

export interface Domain {
  id: number;
  name: string;
}

export interface KnockoutQuestion {
  id: number;
  order_index: number;
  code: string;
  direction: "private" | "public";
  dimension: string;
  question_text: string;
  evidence_hint: string | null;
  dhl_ref: string | null;
}

export interface ScoringQuestion {
  id: number;
  order_index: number;
  code: string;
  dimension: string;
  question_text: string;
  evidence_hint: string | null;
  band_a_text: string;
  band_b_text: string;
  band_c_text: string;
  band_d_text: string;
  band_e_text: string;
  dhl_ref: string | null;
}

export interface QuestionnaireVersion {
  id: number;
  version_label: string;
  status: "draft" | "published";
  changelog: string | null;
  published_by: string | null;
  published_at: string | null;
  knockout_questions: KnockoutQuestion[];
  scoring_questions: ScoringQuestion[];
}

export interface QuestionnaireSummary {
  id: number;
  version_label: string;
  status: "draft" | "published";
  changelog: string | null;
  published_at: string | null;
  assessment_count: number;
}

export interface DriverSignal {
  code: string;
  dimension: string;
  net_private_points: number;
}

export interface AssessmentResult {
  private_points: number;
  public_points: number;
  private_fit: number | null;
  public_fit: number | null;
  recommendation: string;
  confidence: "high" | "medium" | "low" | "n/a";
  robust: boolean | null;
  evidence_complete: boolean;
  top_private_drivers: DriverSignal[];
  top_public_drivers: DriverSignal[];
}

export interface KnockoutAnswer {
  knockout_question_id: number;
  code: string;
  direction: string;
  dimension: string;
  question_text: string;
  evidence_hint: string | null;
  answer: "yes" | "no" | null;
  evidence_reference: string | null;
}

export interface ScoringAnswer {
  scoring_question_id: number;
  code: string;
  dimension: string;
  question_text: string;
  evidence_hint: string | null;
  band_a_text: string;
  band_b_text: string;
  band_c_text: string;
  band_d_text: string;
  band_e_text: string;
  band: "A" | "B" | "C" | "D" | "E" | null;
  evidence_reference: string | null;
}

export interface WorkflowEvent {
  from_status: AssessmentStatus;
  to_status: AssessmentStatus;
  actor_user_id: number;
  notes: string | null;
  created_at: string;
}

export interface AssessmentListItem {
  id: number;
  app_name: string;
  domain: Domain;
  status: AssessmentStatus;
  questionnaire_version_label: string;
  created_at: string;
  recommendation: string | null;
  confidence: string | null;
}

export interface AssessmentDetail {
  id: number;
  app_name: string;
  domain: Domain;
  status: AssessmentStatus;
  business_owner: string | null;
  technical_owner: string | null;
  data_classification: string | null;
  business_criticality: string | null;
  current_hosting: string | null;
  target_go_live: string | null;
  rto_rpo: string | null;
  created_at: string;
  questionnaire_version: QuestionnaireVersion;
  knockout_answers: KnockoutAnswer[];
  scoring_answers: ScoringAnswer[];
  result: AssessmentResult | null;
  workflow_events: WorkflowEvent[];
}

export interface PortfolioDashboard {
  total: number;
  by_status: Record<string, number>;
  by_recommendation: Record<string, number>;
}

export interface ByDomainRow {
  domain: string;
  total: number;
  private_count: number;
  public_count: number;
  pending_or_other_count: number;
}

export interface ConfidenceRobustness {
  by_confidence: Record<string, number>;
  robust_count: number;
  fragile_count: number;
  unknown_count: number;
}

export interface NeedsAttentionItem {
  assessment_id: number;
  app_name: string;
  domain: string;
  status: AssessmentStatus;
  issue: string;
}

export interface Handoff {
  url: string;
  app_name: string;
  recommended_target: string;
  assessment_id: number;
}

export interface UserAccount {
  id: number;
  email: string;
  display_name: string;
  domain: Domain | null;
  roles: { role: Role; domain_id: number | null }[];
}
