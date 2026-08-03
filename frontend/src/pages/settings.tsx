import { Bell, Bot, Database, FileKey, ShieldCheck, Stethoscope } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { WorkspaceShell } from "@/components/workspace-shell";

const integrations = [
  [Database, "Snowflake data plane", "Connected", "Governed protocol, synthetic evidence, tasks, and audit state."],
  [Bot, "Cortex AI", "Connected", "Search retrieval and bounded LLM explanations."],
  [Stethoscope, "EHR / FHIR", "Not connected", "Production extension; no real patient system is connected."],
  [Bell, "Notifications", "Demo feed", "In-app worklist signals; email and messaging delivery are not enabled."],
] as const;

export function SettingsPage() {
  return <WorkspaceShell eyebrow="Workspace controls" title="Settings & integrations"><section className="max-w-4xl"><Badge className="border-blue-200 bg-blue-50 text-[#1d5a85]">Transparent configuration</Badge><h2 className="protocol-title mt-3 text-3xl leading-tight md:text-4xl">Know exactly what ATLAS is connected to.</h2><p className="mt-3 text-sm leading-6 text-slate-600">Hackathon connections are shown explicitly so a demonstration boundary cannot be mistaken for a production integration.</p></section><section className="mt-7 grid gap-4 md:grid-cols-2">{integrations.map(([Icon, title, status, copy]) => <Card key={title} className="p-5"><div className="flex items-start"><div className="grid size-10 place-items-center rounded-xl bg-[#e1eef5] text-[#1d5a85]"><Icon className="size-5" /></div><Badge className={`ml-auto ${status === "Connected" ? "border-teal-200 bg-teal-50 text-teal-800" : "border-slate-200 bg-slate-50 text-slate-600"}`}>{status}</Badge></div><h3 className="mt-4 text-sm font-bold">{title}</h3><p className="mb-0 mt-2 text-xs leading-5 text-slate-500">{copy}</p></Card>)}</section><Card className="mt-6 p-5"><div className="flex items-center gap-2 text-sm font-bold"><ShieldCheck className="size-4 text-[#23877e]" />Safety and access</div><div className="mt-4 grid gap-4 text-xs leading-5 text-slate-500 md:grid-cols-3"><div><FileKey className="mb-2 size-4 text-[#1d5a85]" />Secrets remain in local or deployment secret stores, never the frontend or repository.</div><div><ShieldCheck className="mb-2 size-4 text-[#1d5a85]" />The application role receives limited model and database privileges.</div><div><Database className="mb-2 size-4 text-[#1d5a85]" />The current patient cohort is synthetic and contains no PHI.</div></div></Card></WorkspaceShell>;
}
