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

