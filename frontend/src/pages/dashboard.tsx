import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "wouter";
import {
  Activity,
  ArrowRight,
  BellRing,
  Bot,
  Check,
  CircleAlert,
  ClipboardCheck,
  ExternalLink,
  FileSearch,
  FlaskConical,
  LoaderCircle,
  RefreshCw,
  Sparkles,
  Users,
} from "lucide-react";
import { api } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { WorkspaceShell } from "@/components/workspace-shell";

function Kpi({ icon: Icon, label, value, helper, tone }: { icon: typeof Activity; label: string; value: string | number; helper: string; tone: string }) {
  return <Card className="group overflow-hidden p-5 transition hover:-translate-y-0.5 hover:shadow-[0_12px_30px_rgba(16,35,59,0.08)]"><div className="flex items-start"><div className={`grid size-9 place-items-center rounded-xl ${tone}`}><Icon className="size-4" /></div><span className="ml-auto font-mono text-[9px] uppercase tracking-[0.12em] text-slate-400">Live</span></div><div className="protocol-title mt-5 text-4xl leading-none text-[#10233b]">{value}</div><div className="mt-2 text-xs font-bold text-slate-700">{label}</div><div className="mt-1 text-[11px] leading-4 text-slate-400">{helper}</div></Card>;
}

function TrialIntake() {
  const queryClient = useQueryClient();
  const [source, setSource] = useState("");
  const sync = useMutation({
    mutationFn: api.syncTrial,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["trials"] });
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    if (source.trim()) sync.mutate(source.trim());
  }
  return <Card className="relative overflow-hidden border-0 bg-[#10233b] text-white shadow-[0_20px_50px_rgba(16,35,59,0.18)]"><div className="absolute -right-20 -top-20 size-64 rounded-full border border-white/10" /><div className="absolute right-5 top-5 size-28 rounded-full border border-[#70d0c6]/20" /><div className="relative grid gap-7 p-6 lg:grid-cols-[1fr_1.1fr] lg:p-8"><div><div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-[#70d0c6]"><Sparkles className="size-4" />Start a governed run</div><h2 className="protocol-title mt-3 max-w-lg text-3xl leading-tight md:text-4xl">Bring a public trial into ATLAS.</h2><p className="mt-3 max-w-lg text-xs leading-6 text-slate-300">Paste an NCT ID or ClinicalTrials.gov link. ATLAS fetches the current public record, hashes the source version, and stages its criteria for review.</p></div><form onSubmit={submit} className="self-end rounded-2xl border border-white/10 bg-white/[0.06] p-4 backdrop-blur"><label className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-300">ClinicalTrials.gov source</label><div className="mt-2 flex flex-col gap-2 sm:flex-row"><input value={source} onChange={(event) => { setSource(event.target.value); sync.reset(); }} placeholder="NCT number or study URL" className="h-11 min-w-0 flex-1 rounded-lg border border-white/15 bg-white/10 px-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-[#70d0c6] focus:ring-2 focus:ring-[#70d0c6]/20" /><Button className="h-11 bg-[#70d0c6] text-[#10233b] hover:bg-[#8bddd5]" disabled={!source.trim() || sync.isPending}>{sync.isPending ? <LoaderCircle className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}Sync trial</Button></div><button type="button" onClick={() => setSource("NCT00749190")} className="mt-3 text-[10px] font-semibold text-[#70d0c6] hover:text-white">Use the demonstration trial</button>{sync.isSuccess && <div className="mt-3 flex items-start gap-2 rounded-lg border border-teal-300/20 bg-teal-300/10 p-3 text-[11px] leading-5 text-teal-100"><Check className="mt-0.5 size-4 shrink-0" />{sync.data.protocol_id} was synced and versioned. It is waiting for criterion extraction and review.</div>}{sync.error && <div className="mt-3 rounded-lg border border-rose-300/20 bg-rose-300/10 p-3 text-[11px] text-rose-100">{sync.error.message}</div>}</form></div></Card>;
}

export function DashboardPage() {
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard });
  const trials = useQuery({ queryKey: ["trials"], queryFn: api.trials });
  const tasks = useQuery({ queryKey: ["tasks"], queryFn: api.tasks });
  const audit = useQuery({ queryKey: ["audit-events"], queryFn: api.auditEvents });
  const summary = useQuery({ queryKey: ["copilot", "daily-summary"], queryFn: () => api.copilot("Give me a daily coordinator briefing"), staleTime: 120_000 });
  const counts = dashboard.data?.run.counts;
  const openTasks = tasks.data?.items.filter((task) => task.status === "OPEN") ?? [];
  const highPriority = openTasks.filter((task) => task.source_status === "MANUAL_REVIEW").length;
  const protocolUpdates = trials.data?.items.filter((trial) => trial.processing_state !== "READY_FOR_SCREENING").length ?? 0;
  const reviewProgress = dashboard.data ? Math.round(((dashboard.data.run.counts.POTENTIAL_MATCH + dashboard.data.run.counts.EXCLUDED) / dashboard.data.run.cohort_size) * 100) : 0;
  const isLoading = dashboard.isLoading || trials.isLoading || tasks.isLoading;
  return <WorkspaceShell eyebrow="Clinical operations cockpit" title="Today at a glance" aside={<div className="hidden items-center gap-2 rounded-full border border-teal-100 bg-teal-50 px-3 py-1.5 text-[10px] font-bold text-teal-800 sm:flex"><span className="size-1.5 rounded-full bg-teal-500" />Snowflake connected</div>}>
    <TrialIntake />
    {isLoading ? <div className="grid h-48 place-items-center"><LoaderCircle className="size-6 animate-spin text-[#1d5a85]" /></div> : <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5"><Kpi icon={FlaskConical} label="Active trials" value={trials.data?.items.length ?? 0} helper="Public studies in this workspace" tone="bg-blue-50 text-[#1d5a85]" /><Kpi icon={Users} label="Awaiting review" value={(counts?.MISSING_INFORMATION ?? 0) + (counts?.MANUAL_REVIEW ?? 0)} helper="Missing or contradictory evidence" tone="bg-amber-50 text-amber-700" /><Kpi icon={CircleAlert} label="High-priority tasks" value={highPriority} helper="Manual-review cases in the worklist" tone="bg-rose-50 text-rose-700" /><Kpi icon={RefreshCw} label="Protocol updates" value={protocolUpdates} helper="Synced versions awaiting extraction" tone="bg-violet-50 text-violet-700" /><Kpi icon={ClipboardCheck} label="Cohort resolved" value={`${reviewProgress}%`} helper="Observed pre-screen branches, not enrollment" tone="bg-teal-50 text-teal-700" /></section>}
    <section className="mt-6 grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
      <Card className="overflow-hidden"><div className="flex items-center border-b border-slate-100 px-6 py-5"><div className="grid size-9 place-items-center rounded-xl bg-[#e1eef5] text-[#1d5a85]"><Bot className="size-4" /></div><div className="ml-3"><div className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#1d5a85]">Today’s AI summary</div><div className="mt-0.5 text-[11px] text-slate-400">Generated from the latest governed screening run</div></div><Badge className="ml-auto border-teal-200 bg-teal-50 text-teal-800">Cited</Badge></div><div className="p-6">{summary.isLoading ? <div className="flex items-center gap-2 text-sm text-slate-500"><LoaderCircle className="size-4 animate-spin" />Reviewing current evidence…</div> : <p className="m-0 text-[15px] leading-7 text-[#24364b]">{summary.data?.answer ?? "The summary is unavailable until a governed screening run exists."}</p>}<div className="mt-5 flex flex-wrap gap-3"><button type="button" onClick={() => window.dispatchEvent(new Event("atlas:open-copilot"))} className="inline-flex items-center gap-2 text-xs font-bold text-[#1d5a85]">Ask a follow-up <ArrowRight className="size-3.5" /></button>{summary.data && <span className="font-mono text-[9px] text-slate-400">{summary.data.copilot_run_id} · {summary.data.model}</span>}</div></div></Card>
      <Card className="overflow-hidden"><div className="flex items-center border-b border-slate-100 px-5 py-4"><BellRing className="size-4 text-[#1d5a85]" /><h3 className="ml-2 text-sm font-bold">Needs attention</h3><Link href="/notifications" className="ml-auto text-[10px] font-bold text-[#1d5a85]">View all</Link></div><div className="divide-y divide-slate-100">{openTasks.slice(0, 4).map((task) => <Link key={task.task_key} href="/tasks" className="flex items-start gap-3 p-4 transition hover:bg-slate-50"><span className={`mt-1 size-2 shrink-0 rounded-full ${task.source_status === "MANUAL_REVIEW" ? "bg-rose-500" : "bg-amber-500"}`} /><div><div className="text-xs font-bold text-[#10233b]">{task.patient_id} · {task.action_type.replaceAll("_", " ").toLowerCase()}</div><div className="mt-1 line-clamp-1 text-[10px] text-slate-400">{task.reason}</div></div><ArrowRight className="ml-auto size-3.5 text-slate-300" /></Link>)}{!openTasks.length && <div className="p-8 text-center text-xs text-slate-500">No open coordinator tasks.</div>}</div></Card>
    </section>
    <section className="mt-6 grid gap-5 lg:grid-cols-[1fr_340px]"><Card className="overflow-hidden"><div className="flex items-center border-b border-slate-100 px-5 py-4"><Activity className="size-4 text-[#23877e]" /><h3 className="ml-2 text-sm font-bold">Recent governed activity</h3></div><div className="divide-y divide-slate-100">{(audit.data?.items ?? []).slice(0, 5).map((event) => <div key={event.event_id} className="grid gap-2 px-5 py-4 sm:grid-cols-[1fr_auto]"><div><div className="text-xs font-bold text-[#10233b]">{event.event_type.replaceAll("_", " ").toLowerCase()}</div><div className="mt-1 text-[10px] text-slate-400">{event.entity_id}</div></div><div className="text-[10px] text-slate-400">{new Date(event.occurred_at).toLocaleString()}</div></div>)}</div></Card><Card className="p-5"><div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-[#1d5a85]"><FileSearch className="size-4" />Current study</div><h3 className="protocol-title mt-3 text-2xl leading-tight">{dashboard.data?.protocol.title}</h3><p className="mt-3 font-mono text-[10px] text-slate-400">{dashboard.data?.protocol.protocol_id}</p><a href={dashboard.data?.protocol.source_url} target="_blank" rel="noreferrer" className="mt-5 inline-flex items-center gap-2 text-xs font-bold text-[#1d5a85]">Open public source <ExternalLink className="size-3.5" /></a></Card></section>
  </WorkspaceShell>;
}
