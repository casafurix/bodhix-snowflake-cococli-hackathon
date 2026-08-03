import type {
  AuditEvent,
  CoordinatorTask,
  DashboardData,
  OperationsData,
  PatientDetail,
  ProtocolData,
  TaskDecision,
  CopilotResponse,
} from "@/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  dashboard: () => request<DashboardData>("/dashboard"),
  patient: (patientId: string) => request<PatientDetail>(`/patients/${patientId}`),
  rerun: () => request<{ run_id: string; status: string }>("/screening-runs", { method: "POST" }),
  protocol: () => request<ProtocolData>("/protocol"),
  tasks: () => request<{ items: CoordinatorTask[] }>("/tasks"),
  auditEvents: () => request<{ items: AuditEvent[] }>("/audit-events"),
  operations: () => request<OperationsData>("/operations"),
  decideTask: (
    taskKey: string,
    input: {
      decision: TaskDecision;
      actor: string;
      reason: string;
      edited_action?: string;
    },
  ) =>
    request<Record<string, string>>(`/tasks/${encodeURIComponent(taskKey)}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }),
  copilot: (query: string, contextPatientId?: string) =>
    request<CopilotResponse>("/copilot/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, context_patient_id: contextPatientId }),
    }),
  confirmCopilot: (proposalId: string, reason: string) =>
    request<Record<string, string>>("/copilot/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        proposal_id: proposalId,
        actor: "TRIAL_COORDINATOR_DEMO",
        reason,
      }),
    }),
};
