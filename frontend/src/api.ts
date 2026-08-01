import type { DashboardData, PatientDetail } from "@/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

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
};

