import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ChevronRight, CircleAlert, ClipboardCheck, LoaderCircle, PencilLine, ShieldCheck, X } from "lucide-react";
import { api } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { WorkspaceShell } from "@/components/workspace-shell";
import { cn } from "@/lib/utils";
import type { CoordinatorTask, TaskDecision } from "@/types";

const actionLabel: Record<string, string> = {
  REVIEW_FOR_SCREENING: "Review for screening",
  REQUEST_MISSING_INFORMATION: "Locate missing evidence",
  CLINICAL_REVIEW_REQUIRED: "Resolve clinical ambiguity",
  LOCATE_EXISTING_LAB: "Locate existing lab",
};

function DecisionPanel({ task, onClose }: { task: CoordinatorTask; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [decision, setDecision] = useState<TaskDecision>("APPROVE");
  const [reason, setReason] = useState("");
  const [editedAction, setEditedAction] = useState(task.action_type);
  const mutation = useMutation({
    mutationFn: () => api.decideTask(task.task_key, {
      decision,
      actor: "TRIAL_COORDINATOR_DEMO",
      reason,
      ...(decision === "EDIT" ? { edited_action: editedAction } : {}),
    }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["tasks"] }),
        queryClient.invalidateQueries({ queryKey: ["audit-events"] }),
      ]);
    },
  });

  return (
    <Card className="sticky top-6 overflow-hidden">
      <div className="flex items-start border-b border-slate-100 p-5">
        <div><div className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#1d5a85]">Human decision</div><h3 className="protocol-title mt-1 text-xl">{task.patient_id}</h3></div>
        <Button variant="ghost" size="icon" className="ml-auto" onClick={onClose}><X className="size-4" /></Button>
      </div>
      <div className="p-5">
        <div className="rounded-lg border border-blue-100 bg-blue-50/60 p-4 text-xs leading-5 text-blue-950">
          <div className="font-bold">Original recommendation</div>
          <div className="mt-1">{actionLabel[task.action_type] ?? task.action_type.replaceAll("_", " ")}</div>
          <div className="mt-2 text-blue-800/70">{task.reason}</div>
        </div>

        {mutation.isSuccess ? (
          <div className="mt-5 rounded-lg border border-teal-200 bg-teal-50 p-4 text-sm text-teal-900">
            <div className="flex items-center gap-2 font-bold"><Check className="size-4" />Decision recorded</div>
            <p className="mb-0 mt-2 text-xs leading-5">The task and append-only audit history were updated in Snowflake.</p>
            <Button className="mt-4" size="sm" onClick={onClose}>Return to worklist</Button>
          </div>
        ) : (
          <>
            <div className="mt-5 grid grid-cols-2 gap-2">
              {(["APPROVE", "EDIT", "REJECT", "DISMISS"] as TaskDecision[]).map((item) => (
                <button key={item} onClick={() => setDecision(item)} className={cn("rounded-lg border px-3 py-2 text-xs font-bold", decision === item ? "border-[#1d5a85] bg-[#e8f1f6] text-[#10233b]" : "border-slate-200 bg-white text-slate-500 hover:bg-slate-50")}>{item}</button>
              ))}
            </div>
            {decision === "EDIT" && (
              <label className="mt-4 block text-xs font-bold text-slate-700">Edited safe action
                <select value={editedAction} onChange={(event) => setEditedAction(event.target.value)} className="mt-2 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs font-normal outline-none focus:ring-2 focus:ring-[#1d5a85]">
                  <option value="REVIEW_FOR_SCREENING">Review for screening</option>
                  <option value="LOCATE_EXISTING_LAB">Locate existing lab</option>
                  <option value="LOCATE_EXISTING_REPORT">Locate existing report</option>
                  <option value="CLINICAL_REVIEW_REQUIRED">Clinical review required</option>
                </select>
              </label>
            )}
            <label className="mt-4 block text-xs font-bold text-slate-700">Decision reason
              <textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={4} placeholder="Record what you verified and why this transition is appropriate." className="mt-2 w-full resize-none rounded-lg border border-slate-200 p-3 text-xs font-normal leading-5 outline-none focus:ring-2 focus:ring-[#1d5a85]" />
            </label>
            <div className="mt-3 flex items-start gap-2 text-[11px] leading-4 text-slate-500"><ShieldCheck className="mt-0.5 size-4 shrink-0 text-[#23877e]" />Approve adds the case to a coordinator verification queue. It never enrolls or contacts a patient.</div>
            {mutation.error && <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">The transition was not applied. Refresh the task state and try again.</div>}
            <Button className="mt-5 w-full" disabled={reason.trim().length < 3 || mutation.isPending} onClick={() => mutation.mutate()}>
              {mutation.isPending ? <LoaderCircle className="size-4 animate-spin" /> : <ClipboardCheck className="size-4" />}
              Record {decision.toLowerCase()}
            </Button>
          </>
        )}
      </div>
    </Card>
  );
}

export function WorklistPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["tasks"], queryFn: api.tasks });
  const [selected, setSelected] = useState<CoordinatorTask | null>(null);
  const [filter, setFilter] = useState<"ALL" | "OPEN" | "CLOSED">("OPEN");
  const tasks = useMemo(() => (data?.items ?? []).filter((task) => filter === "ALL" || (filter === "OPEN" ? task.status === "OPEN" : task.status !== "OPEN")), [data, filter]);

  return (
    <WorkspaceShell eyebrow="Coordinator action orchestrator" title="Human decision worklist">
      <section className="max-w-4xl">
        <Badge className="border-blue-200 bg-blue-50 text-[#1d5a85]">Human approval gate</Badge>
        <h2 className="protocol-title mt-3 text-3xl leading-tight md:text-4xl">The copilot proposes. The coordinator changes state.</h2>
        <p className="mt-3 text-sm leading-6 text-slate-600">Every transition preserves the original recommendation, actor, reason, prior state, new state, citations, and screening run.</p>
      </section>

      <section className="mt-7 grid gap-5 xl:grid-cols-[1fr_380px]">
        <Card className="overflow-hidden">
          <div className="flex items-center border-b border-slate-200 p-5">
            <div><h3 className="text-sm font-bold">Current governed run</h3><p className="mt-1 text-xs text-slate-500">Excluded candidates have audit events but no outreach tasks.</p></div>
            <div className="ml-auto flex rounded-lg bg-slate-100 p-1">
              {(["OPEN", "CLOSED", "ALL"] as const).map((item) => <button key={item} onClick={() => setFilter(item)} className={cn("rounded-md px-3 py-1.5 text-[10px] font-bold", filter === item ? "bg-white shadow-sm" : "text-slate-500")}>{item}</button>)}
            </div>
          </div>
          {isLoading && <div className="grid h-64 place-items-center"><LoaderCircle className="size-6 animate-spin text-[#1d5a85]" /></div>}
          {error && <div className="p-6 text-sm text-rose-800">The worklist could not be loaded.</div>}
          <div className="divide-y divide-slate-100">
            {tasks.map((task) => (
              <button key={task.task_key} onClick={() => setSelected(task)} className={cn("grid w-full gap-4 p-5 text-left transition-colors md:grid-cols-[130px_1fr_180px_auto] md:items-center", selected?.task_key === task.task_key ? "bg-blue-50/70" : "hover:bg-slate-50")}>
                <div><div className="font-mono text-xs font-bold">{task.patient_id}</div><div className="mt-1 font-mono text-[9px] text-slate-400">{task.protocol_id}</div></div>
                <div><div className="text-sm font-bold">{actionLabel[task.action_type] ?? task.action_type.replaceAll("_", " ")}</div><p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">{task.reason}</p></div>
                <div className="flex flex-wrap gap-2"><Badge status={task.source_status}>{task.source_status.replaceAll("_", " ")}</Badge><Badge className={task.status === "OPEN" ? "border-amber-200 bg-amber-50 text-amber-800" : "border-slate-200 bg-slate-50 text-slate-600"}>{task.status}</Badge></div>
                <ChevronRight className="size-4 text-slate-400" />
              </button>
            ))}
            {!isLoading && !tasks.length && <div className="p-10 text-center"><CircleAlert className="mx-auto size-6 text-slate-300" /><p className="mb-0 mt-3 text-sm text-slate-500">No tasks in this state.</p></div>}
          </div>
        </Card>
        {selected ? <DecisionPanel task={selected} onClose={() => setSelected(null)} /> : <Card className="grid min-h-64 place-items-center border-dashed p-8 text-center"><div><PencilLine className="mx-auto size-7 text-slate-300" /><p className="mt-3 text-sm font-bold">Select a task to review</p><p className="mt-2 text-xs leading-5 text-slate-500">The decision panel keeps the original recommendation visible while you record the human outcome.</p></div></Card>}
      </section>
    </WorkspaceShell>
  );
}
