import { useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useLocation } from "wouter";
import {
  Activity,
  ArrowUpRight,
  BookOpenText,
  Check,
  ChevronRight,
  CircleAlert,
  ClipboardCheck,
  FileSearch,
  FlaskConical,
  History,
  LayoutDashboard,
  LoaderCircle,
  Menu,
  MessageSquareText,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import { api } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { CopilotResponse, PatientSummary, ScreeningStatus } from "@/types";

const statusLabel: Record<ScreeningStatus, string> = {
  POTENTIAL_MATCH: "Potential match",
  EXCLUDED: "Excluded by pre-screen",
  MISSING_INFORMATION: "Missing information",
  MANUAL_REVIEW: "Manual review",
};

const statusTone: Record<ScreeningStatus, string> = {
  POTENTIAL_MATCH: "bg-[#23877e]",
  EXCLUDED: "bg-[#b84b52]",
  MISSING_INFORMATION: "bg-[#d7902f]",
  MANUAL_REVIEW: "bg-[#1d5a85]",
};

const nav = [
  [LayoutDashboard, "Command center", "/"],
  [BookOpenText, "Protocols", "/protocols"],
  [Users, "Screening", "/screening"],
  [ClipboardCheck, "Worklist", "/worklist"],
  [Activity, "Operations", "/operations"],
  [FlaskConical, "Scenario lab", "/scenarios"],
  [History, "Audit history", "/audit"],
] as const;

function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [location] = useLocation();
  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-40 flex w-[264px] flex-col bg-[#10233b] text-white transition-transform lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full",
      )}
    >
      <div className="flex h-20 items-center border-b border-white/10 px-6">
        <div className="grid size-10 place-items-center rounded-lg border border-white/15 bg-white/10">
          <FileSearch className="size-5 text-[#70d0c6]" />
        </div>
        <div className="ml-3">
          <div className="protocol-title text-[17px] font-semibold tracking-wide">ATLAS</div>
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Trial intelligence</div>
        </div>
        <button className="ml-auto lg:hidden" onClick={onClose} aria-label="Close navigation">
          <X className="size-5" />
        </button>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-6">
        <div className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Workspace</div>
        {nav.map(([Icon, label, path]) => (
          <Link
            key={label}
            href={path}
            className={cn(
                "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors",
                location === path ? "bg-white/10 font-semibold text-white" : "text-slate-400 hover:bg-white/5 hover:text-white",
              )}
            onClick={onClose}
          >
            <Icon className="size-[18px]" />
            {label}
          </Link>
        ))}
      </nav>
      <div className="m-3 rounded-xl border border-white/10 bg-white/[0.04] p-4">
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-200">
          <ShieldCheck className="size-4 text-[#70d0c6]" /> Synthetic data
        </div>
        <p className="m-0 text-[11px] leading-5 text-slate-400">Decision support only. No PHI or automated enrollment.</p>
      </div>
    </aside>
  );
}

function Metric({ label, value, accent, helper }: { label: string; value: number; accent: string; helper: string }) {
  return (
    <Card className="relative overflow-hidden p-5">
      <div className={cn("absolute inset-y-0 left-0 w-1", accent)} />
      <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500">{label}</div>
      <div className="protocol-title mt-2 text-4xl leading-none text-[#10233b]">{value}</div>
      <div className="mt-3 text-xs text-slate-500">{helper}</div>
    </Card>
  );
}

function CandidateRow({ patient, active, onSelect }: { patient: PatientSummary; active: boolean; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      className={cn(
        "grid w-full grid-cols-[1.2fr_1fr_0.75fr_0.8fr_auto] items-center gap-4 border-t border-slate-100 px-5 py-4 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#1d5a85]",
        active ? "bg-blue-50/70" : "bg-white hover:bg-slate-50",
      )}
    >
      <div>
        <div className="text-sm font-bold text-[#10233b]">{patient.display_name}</div>
        <div className="mt-1 font-mono text-[10px] text-slate-400">{patient.patient_id} · {patient.site_id}</div>
      </div>
      <Badge status={patient.status}>{statusLabel[patient.status]}</Badge>
      <div>
        <div className="text-xs font-semibold text-slate-700">{patient.evidence_completeness}%</div>
        <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-[#1d5a85]" style={{ width: `${patient.evidence_completeness}%` }} />
        </div>
      </div>
      <div className="text-xs text-slate-600">
        <span className="font-semibold">HbA1c</span> {patient.hba1c ?? "—"}%
      </div>
      <ChevronRight className="size-4 text-slate-400" />
    </button>
  );
}

function EvidencePanel({ patientId, onClose }: { patientId: string; onClose: () => void }) {
  const [, navigate] = useLocation();
  const { data, isLoading, error } = useQuery({
    queryKey: ["patient", patientId],
    queryFn: () => api.patient(patientId),
  });
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-[#10233b]/30 backdrop-blur-[2px]" role="dialog" aria-modal="true">
      <button className="flex-1 cursor-default" onClick={onClose} aria-label="Close evidence panel" />
      <section className="h-full w-full max-w-[640px] overflow-y-auto bg-[#f7f9fb] shadow-2xl">
        <div className="sticky top-0 z-10 flex items-start border-b border-slate-200 bg-white/95 px-6 py-5 backdrop-blur">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#1d5a85]">Evidence review</div>
            <h2 className="protocol-title mt-1 text-2xl text-[#10233b]">{data?.display_name ?? patientId}</h2>
          </div>
          <Button variant="ghost" size="icon" className="ml-auto" onClick={onClose} aria-label="Close">
            <X className="size-5" />
          </Button>
        </div>
        {isLoading && <div className="grid h-80 place-items-center"><LoaderCircle className="size-6 animate-spin text-[#1d5a85]" /></div>}
        {error && <div className="m-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">Evidence could not be loaded.</div>}
        {data && (
          <div className="p-6">
            <div className="flex flex-wrap items-center gap-3">
              <Badge status={data.status}>{statusLabel[data.status]}</Badge>
              <span className="text-xs text-slate-500">{data.evidence_completeness}% evidence complete</span>
              <span className="font-mono text-[10px] text-slate-400">{data.run_id}</span>
            </div>
            <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-900">
              {data.disclaimer}
            </div>
            <div className="mt-7 flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#10233b]">Criterion evidence rail</h3>
              <span className="text-xs text-slate-400">{data.criteria.length} reviewed rules</span>
            </div>
            <div className="relative mt-4 space-y-3 before:absolute before:bottom-6 before:left-[19px] before:top-6 before:w-px before:bg-slate-200">
              {data.criteria.map((item) => (
                <div key={item.criterion_id} className="relative grid grid-cols-[40px_1fr] gap-3">
                  <div className={cn("z-[1] mt-5 grid size-10 place-items-center rounded-full border-4 border-[#f7f9fb] text-white", item.status === "MET" ? "bg-[#23877e]" : item.status === "NOT_MET" ? "bg-[#b84b52]" : item.status === "UNKNOWN" ? "bg-[#d7902f]" : "bg-[#1d5a85]") }>
                    {item.status === "MET" ? <Check className="size-4" /> : <CircleAlert className="size-4" />}
                  </div>
                  <Card className="p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-mono text-[10px] font-bold text-[#1d5a85]">{item.criterion_id}</div>
                      <Badge status={item.status}>{item.status.replace("_", " ")}</Badge>
                    </div>
                    <p className="mt-3 text-sm font-semibold leading-5 text-[#10233b]">{item.source_clause}</p>
                    <div className="mt-3 grid gap-2 border-t border-slate-100 pt-3 text-xs leading-5">
                      <div><span className="font-semibold text-slate-700">Protocol</span><span className="ml-2 text-slate-500">{item.protocol_citation}</span></div>
                      <div><span className="font-semibold text-slate-700">Patient</span><span className="ml-2 font-mono text-[10px] text-slate-500">{item.patient_citation ?? "No governed evidence"}</span></div>
                      <p className="m-0 text-slate-600">{item.explanation}</p>
                    </div>
                  </Card>
                </div>
              ))}
            </div>
            <div className="sticky bottom-0 -mx-6 mt-8 flex gap-3 border-t border-slate-200 bg-white/95 px-6 py-4 backdrop-blur">
              <Button className="flex-1" onClick={() => navigate("/worklist")}><ClipboardCheck className="size-4" />Open governed worklist</Button>
              <Button variant="outline" onClick={onClose}>Close evidence</Button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

function CopilotCard({ contextPatientId }: { contextPatientId?: string }) {
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const ask = useMutation({
    mutationFn: (value: string) => api.copilot(value, contextPatientId),
    onSuccess: setResponse,
  });
  const confirm = useMutation({
    mutationFn: (proposalId: string) => api.confirmCopilot(proposalId, "Coordinator confirmed the ATLAS proposal."),
    onSuccess: async () => {
      setResponse((current) => current ? { ...current, proposal: null, answer: `${current.answer}\n\nAction approved and written to the governed worklist.` } : current);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["tasks"] }),
        queryClient.invalidateQueries({ queryKey: ["audit-events"] }),
      ]);
    },
  });
  const examples = [
    "Why is P004 in manual review?",
    "Which candidates need evidence?",
    "Compare site workload",
    "What should I do for P008?",
    "Why did screening exclude P005?",
    "What is the current recruitment risk?",
  ];

  function submit(event: FormEvent) {
    event.preventDefault();
    const value = query.trim();
    if (value) ask.mutate(value);
  }

  return (
    <Card className="overflow-hidden border-[#c7dce4]">
      <div className="bg-[#10233b] p-5 text-white">
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-[#70d0c6]"><MessageSquareText className="size-4" /> ATLAS copilot</div>
        <h3 className="protocol-title mt-2 text-2xl">Ask the evidence desk.</h3>
        <p className="mt-2 text-xs leading-5 text-slate-300">Answers stay inside the trial context, show their sources, and never turn into an autonomous clinical decision.</p>
      </div>
      <form onSubmit={submit} className="p-5">
        <textarea
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask about a candidate, evidence, site, recruitment, or compliance…"
          rows={3}
          className="w-full resize-none rounded-lg border border-slate-200 bg-[#fbfcfd] p-3 text-xs leading-5 outline-none transition focus:border-[#23877e] focus:ring-2 focus:ring-[#70d0c6]/30"
          aria-label="Ask ATLAS copilot"
        />
        <div className="mt-3 flex flex-wrap gap-2">
          {examples.map((example) => <button key={example} type="button" onClick={() => setQuery(example)} className="rounded-full border border-slate-200 px-2.5 py-1 text-[10px] font-semibold text-slate-500 transition hover:border-[#70d0c6] hover:text-[#1d5a85]">{example}</button>)}
        </div>
        <Button type="submit" className="mt-4 w-full" disabled={!query.trim() || ask.isPending}>
          {ask.isPending ? <LoaderCircle className="size-4 animate-spin" /> : <Sparkles className="size-4" />} {ask.isPending ? "Reviewing evidence" : "Ask ATLAS"}
        </Button>
        {ask.error && <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">The assistant could not complete that request. Try a candidate ID such as P004.</div>}
        {response && (
          <div className="mt-5 border-t border-slate-100 pt-5">
            <div className="flex items-center justify-between gap-3">
              <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#1d5a85]">{response.state === "ANSWERED" ? "Grounded answer" : response.state === "REFUSED" ? "Safety boundary" : "Clarify the question"}</div>
              <span className="font-mono text-[9px] text-slate-400">{response.model}</span>
            </div>
            <p className="mt-3 whitespace-pre-line text-sm leading-6 text-[#10233b]">{response.answer}</p>
            {response.citations.length > 0 && <div className="mt-4 space-y-1.5 border-t border-slate-100 pt-3">{response.citations.slice(0, 4).map((citation) => <div key={`${citation.label}-${citation.source}`} className="flex gap-2 text-[10px] text-slate-500"><span className="font-semibold text-slate-700">{citation.label}</span><span className="font-mono">{citation.source}</span></div>)}</div>}
            {response.retrieved_evidence.length > 0 && <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50/60 p-3"><div className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#1d5a85]">Retrieved grounding</div><div className="mt-2 space-y-2">{response.retrieved_evidence.slice(0, 3).map((evidence, index) => <div key={`${evidence.source_id ?? evidence.title ?? index}`} className="text-[10px] leading-4 text-slate-600"><div className="font-semibold text-slate-700">{evidence.title ?? evidence.document_type ?? "Evidence record"}</div><div>{evidence.search_text}</div><div className="mt-0.5 font-mono text-[9px] text-slate-400">{evidence.source_id ?? "Governed Snowflake evidence"}</div></div>)}</div></div>}
            {response.proposal && <div className="mt-4 rounded-lg border border-[#9edbd2] bg-[#effaf8] p-3"><div className="text-xs font-bold text-[#17665e]">Proposed coordinator action</div><div className="mt-1 text-xs leading-5 text-[#275f5a]">{response.proposal.action_type.replaceAll("_", " ").toLowerCase()}. Confirming records a human-reviewed worklist transition.</div><Button type="button" size="sm" className="mt-3" onClick={() => confirm.mutate(response.proposal!.proposal_id)} disabled={confirm.isPending}>{confirm.isPending ? <LoaderCircle className="size-3 animate-spin" /> : <Check className="size-3" />} Confirm action</Button></div>}
            {confirm.error && <div className="mt-3 text-xs text-rose-700">This proposal could not be applied. Refresh the worklist and try again.</div>}
          </div>
        )}
      </form>
    </Card>
  );
}

export default function App() {
  const [location] = useLocation();
  const isScreening = location === "/screening";
  const queryClient = useQueryClient();
  const [menuOpen, setMenuOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<ScreeningStatus | "ALL">("ALL");
  const [search, setSearch] = useState("");
  const dashboard = useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard });
  const rerun = useMutation({
    mutationFn: api.rerun,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["tasks"] }),
        queryClient.invalidateQueries({ queryKey: ["audit-events"] }),
        queryClient.invalidateQueries({ queryKey: ["operations"] }),
      ]);
    },
  });

  const patients = useMemo(() => {
    const rows = dashboard.data?.patients ?? [];
    return rows.filter((patient) => {
      const matchesFilter = filter === "ALL" || patient.status === filter;
      const query = search.trim().toLowerCase();
      const matchesSearch = !query || `${patient.patient_id} ${patient.display_name} ${patient.site_id}`.toLowerCase().includes(query);
      return matchesFilter && matchesSearch;
    });
  }, [dashboard.data, filter, search]);

  if (dashboard.isLoading) {
    return <div className="grid min-h-screen place-items-center"><LoaderCircle className="size-8 animate-spin text-[#1d5a85]" /></div>;
  }
  if (dashboard.error || !dashboard.data) {
    return <div className="grid min-h-screen place-items-center p-6"><Card className="max-w-md p-6"><h1 className="protocol-title text-2xl">ATLAS is offline</h1><p className="mt-3 text-sm text-slate-600">Start the FastAPI backend on port 8000, then refresh this page.</p></Card></div>;
  }

  const { protocol, run } = dashboard.data;
  return (
    <div className="min-h-screen">
      <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
      {menuOpen && <button className="fixed inset-0 z-30 bg-black/20 lg:hidden" onClick={() => setMenuOpen(false)} aria-label="Close menu" />}
      <main className="lg:pl-[264px]">
        <header className="flex h-20 items-center border-b border-slate-200 bg-white/90 px-4 backdrop-blur md:px-8">
          <Button variant="ghost" size="icon" className="mr-2 lg:hidden" onClick={() => setMenuOpen(true)}><Menu className="size-5" /></Button>
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#1d5a85]">Coordinator workspace</div>
            <h1 className="protocol-title mt-1 text-xl font-semibold">{isScreening ? "Cohort screening" : "Command center"}</h1>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <div className="text-xs font-semibold text-slate-700">Synthetic demo</div>
              <div className="text-[10px] text-slate-400">Decision support · human verified</div>
            </div>
            <div className="grid size-9 place-items-center rounded-full bg-[#e1eef5] text-xs font-bold text-[#1d5a85]">TC</div>
          </div>
        </header>

        <div className="mx-auto max-w-[1440px] p-4 md:p-8">
          <section className="grid gap-5 xl:grid-cols-[1fr_auto] xl:items-end">
            <div>
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Badge className="border-blue-200 bg-blue-50 text-[#1d5a85]">{protocol.protocol_id}</Badge>
                <span className="text-xs text-slate-400">{protocol.criteria_count} reviewed criteria · {run.cohort_size} synthetic candidates</span>
              </div>
              <h2 className="protocol-title max-w-4xl text-3xl leading-tight text-[#10233b] md:text-4xl">{isScreening ? "Every candidate has a criterion-level record." : "The cohort review already happened. Verify the evidence."}</h2>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{protocol.title}</p>
            </div>
            <Button variant="outline" onClick={() => rerun.mutate()} disabled={rerun.isPending}>
              <RefreshCw className={cn("size-4", rerun.isPending && "animate-spin")} /> Re-run screening
            </Button>
          </section>

          <section className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Metric label="Potential matches" value={run.counts.POTENTIAL_MATCH} accent="bg-[#23877e]" helper="Ready for coordinator verification" />
            <Metric label="Missing information" value={run.counts.MISSING_INFORMATION} accent="bg-[#d7902f]" helper="Existing evidence needs locating" />
            <Metric label="Manual review" value={run.counts.MANUAL_REVIEW} accent="bg-[#1d5a85]" helper="Ambiguous or contradictory" />
            <Metric label="Excluded" value={run.counts.EXCLUDED} accent="bg-[#b84b52]" helper="Cited pre-screen exclusions" />
          </section>

          <section className="mt-7 grid gap-5 xl:grid-cols-[1fr_340px]">
            <Card className="overflow-hidden">
              <div className="flex flex-col gap-4 border-b border-slate-200 p-5 md:flex-row md:items-center">
                <div>
                  <h3 className="text-sm font-bold">Candidate evidence queue</h3>
                  <p className="mt-1 text-xs text-slate-500">Sorted by safe decision branch and evidence completeness.</p>
                </div>
                <div className="relative md:ml-auto">
                  <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                  <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search candidate or site" className="h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-xs outline-none focus:ring-2 focus:ring-[#1d5a85] md:w-60" />
                </div>
              </div>
              <div className="flex gap-2 overflow-x-auto border-b border-slate-100 px-5 py-3">
                {(["ALL", "POTENTIAL_MATCH", "MISSING_INFORMATION", "MANUAL_REVIEW", "EXCLUDED"] as const).map((item) => (
                  <button key={item} onClick={() => setFilter(item)} className={cn("whitespace-nowrap rounded-full px-3 py-1.5 text-[11px] font-bold", filter === item ? "bg-[#10233b] text-white" : "bg-slate-100 text-slate-500 hover:bg-slate-200")}>
                    {item === "ALL" ? "All candidates" : statusLabel[item]}
                  </button>
                ))}
              </div>
              <div className="hidden grid-cols-[1.2fr_1fr_0.75fr_0.8fr_auto] gap-4 bg-slate-50 px-5 py-2.5 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400 md:grid">
                <span>Candidate</span><span>Pre-screen result</span><span>Evidence</span><span>Key lab</span><span />
              </div>
              <div className="overflow-x-auto">
                <div className="min-w-[720px]">
                  {patients.map((patient) => <CandidateRow key={patient.patient_id} patient={patient} active={selectedId === patient.patient_id} onSelect={() => setSelectedId(patient.patient_id)} />)}
                  {!patients.length && <div className="p-10 text-center text-sm text-slate-500">No candidates match these filters.</div>}
                </div>
              </div>
            </Card>

            <div className="space-y-5">
              <Card className="p-5">
                <div className="flex items-center gap-2"><Sparkles className="size-4 text-[#1d5a85]" /><h3 className="text-sm font-bold">Run composition</h3></div>
                <div className="mt-5 flex h-3 overflow-hidden rounded-full bg-slate-100">
                  {(Object.keys(run.counts) as ScreeningStatus[]).map((status) => <div key={status} className={statusTone[status]} style={{ width: `${(run.counts[status] / run.cohort_size) * 100}%` }} title={`${statusLabel[status]}: ${run.counts[status]}`} />)}
                </div>
                <div className="mt-5 space-y-3">
                  {(Object.keys(run.counts) as ScreeningStatus[]).map((status) => (
                    <div key={status} className="flex items-center text-xs"><span className={cn("mr-2 size-2 rounded-full", statusTone[status])} /><span className="text-slate-600">{statusLabel[status]}</span><span className="ml-auto font-bold">{run.counts[status]}</span></div>
                  ))}
                </div>
              </Card>
              <Card className="overflow-hidden">
                <div className="border-b border-slate-100 p-5"><div className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#1d5a85]">Governed run</div><div className="mt-2 font-mono text-xs font-bold text-[#10233b]">{run.run_id}</div></div>
                <div className="p-5 text-xs leading-5 text-slate-500">Every result was computed from reviewed criteria and synthetic evidence. Unknowns fail closed; no confidence score becomes eligibility.</div>
                <a href={protocol.source_url} target="_blank" rel="noreferrer" className="flex items-center border-t border-slate-100 px-5 py-3 text-xs font-semibold text-[#1d5a85] hover:bg-slate-50">View public protocol <ArrowUpRight className="ml-auto size-4" /></a>
              </Card>
              <CopilotCard />
            </div>
          </section>
        </div>
      </main>
      {selectedId && <EvidencePanel patientId={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  );
}
