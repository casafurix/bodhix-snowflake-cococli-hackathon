export type ScreeningStatus =
  | "POTENTIAL_MATCH"
  | "EXCLUDED"
  | "MISSING_INFORMATION"
  | "MANUAL_REVIEW";

export interface PatientSummary {
  patient_id: string;
  display_name: string;
  site_id: string;
  status: ScreeningStatus;
  evidence_completeness: number;
  age: number | null;
  hba1c: number | null;
  bmi: number | null;
}

export interface DashboardData {
  protocol: {
    protocol_id: string;
    title: string;
    source: string;
    source_url: string;
    criteria_count: number;
    review_status: string;
  };
  run: {
    run_id: string;
    computed_at: string;
    cohort_size: number;
    counts: Record<ScreeningStatus, number>;
  };
  patients: PatientSummary[];
}

export interface CriterionDetail {
  criterion_id: string;
  status: "MET" | "NOT_MET" | "UNKNOWN" | "CONTRADICTORY";
  explanation: string;
  protocol_citation: string;
  patient_citation: string | null;
  criterion_type: "INCLUSION" | "EXCLUSION";
  source_clause: string;
}

export interface PatientDetail extends PatientSummary {
  protocol_id: string;
  run_id: string;
  computed_at: string;
  criteria: CriterionDetail[];
  disclaimer: string;
}

export interface ProtocolCriterion {
  criterion_id: string;
  criterion_type: "INCLUSION" | "EXCLUSION";
  criterion_ordinal: number;
  source_clause: string;
  source_location: string;
  clinical_concept: string | null;
  operator: string | null;
  threshold_value: number | null;
  threshold_upper: number | null;
  threshold_unit: string | null;
  temporal_window: string | null;
  required_evidence: string | null;
  machine_evaluable: boolean;
  review_status: "DRAFT" | "REVIEWED" | "MANUAL_REVIEW" | "REJECTED";
  review_notes: string | null;
}

export interface ProtocolData {
  protocol: {
    protocol_id: string;
    title: string;
    source: string;
    source_url: string;
    document_hash: string;
    overall_status: string;
    retrieved_at: string;
  };
  processing: {
    processing_run_id: string;
    processor: string;
    model_or_function?: string;
    extracted_count: number;
    reviewed_count: number;
    manual_review_count: number;
    rejected_count: number;
    processed_at?: string;
  };
  criteria: ProtocolCriterion[];
}

export interface CoordinatorTask {
  task_key: string;
  patient_id: string;
  protocol_id: string;
  action_type: string;
  status: "OPEN" | "APPROVED" | "REJECTED" | "DISMISSED";
  reason: string;
  source_status: ScreeningStatus;
  created_at: string;
  updated_at: string;
}

export type TaskDecision = "APPROVE" | "EDIT" | "REJECT" | "DISMISS";

export interface AuditEvent {
  event_id: string;
  event_type: string;
  actor: string;
  entity_type: string;
  entity_id: string;
  prior_state: Record<string, unknown>;
  new_state: Record<string, unknown>;
  reason: string;
  source_run_id: string;
  occurred_at: string;
}

export interface SiteOperations {
  site_id: string;
  candidate_count: number;
  potential_match_count: number;
  missing_information_count: number;
  manual_review_count: number;
  excluded_count: number;
  average_evidence_completeness: number;
}

export interface OperationsData {
  run_id: string;
  sites: SiteOperations[];
}
