import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, CheckCircle2, CircleAlert, FileCheck2, LoaderCircle, Search } from "lucide-react";
import { api } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { WorkspaceShell } from "@/components/workspace-shell";
import { cn } from "@/lib/utils";

type CriterionFilter = "ALL" | "REVIEWED" | "MANUAL_REVIEW";

export function ProtocolsPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["protocol"], queryFn: api.protocol });
  const [filter, setFilter] = useState<CriterionFilter>("ALL");
  const [query, setQuery] = useState("");

  const criteria = useMemo(() => {
    if (!data) return [];
    const needle = query.trim().toLowerCase();
    return data.criteria.filter((criterion) => {
      const matchesFilter = filter === "ALL" || criterion.review_status === filter;
      const matchesQuery = !needle || `${criterion.criterion_id} ${criterion.source_clause} ${criterion.clinical_concept ?? ""}`.toLowerCase().includes(needle);
      return matchesFilter && matchesQuery;
    });
  }, [data, filter, query]);

  return (
    <WorkspaceShell eyebrow="Protocol intelligence" title="Source-to-rule register">
      {isLoading && <div className="grid h-80 place-items-center"><LoaderCircle className="size-7 animate-spin text-[#1d5a85]" /></div>}
      {error && <Card className="p-6 text-sm text-rose-800">The governed protocol record could not be loaded.</Card>}
      {data && (
        <>
          <section className="grid gap-5 xl:grid-cols-[1fr_360px]">
            <div>
              <div className="mb-3 flex items-center gap-2">
                <Badge className="border-blue-200 bg-blue-50 text-[#1d5a85]">{data.protocol.protocol_id}</Badge>
                <span className="text-xs text-slate-400">Document {data.protocol.document_hash.slice(0, 10)}…</span>
              </div>
              <h2 className="protocol-title max-w-4xl text-3xl leading-tight md:text-4xl">The source clause stays beside the rule it produced.</h2>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{data.protocol.title}</p>
              <a href={data.protocol.source_url} target="_blank" rel="noreferrer" className="mt-4 inline-flex items-center gap-2 text-xs font-bold text-[#1d5a85] hover:underline">
                Open public ClinicalTrials.gov record <ArrowUpRight className="size-4" />
              </a>
            </div>
            <Card className="relative overflow-hidden p-5">
              <div className="absolute inset-y-0 left-0 w-1 bg-[#23877e]" />
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.14em] text-[#23877e]"><FileCheck2 className="size-4" />Extraction record</div>
              <div className="mt-4 font-mono text-xs font-bold">{data.processing.processing_run_id}</div>
              <p className="mt-3 text-xs leading-5 text-slate-500">{data.processing.model_or_function ?? data.processing.processor}</p>
            </Card>
          </section>

          <section className="mt-7 grid gap-4 sm:grid-cols-3">
            <Card className="p-5"><div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">Extracted clauses</div><div className="protocol-title mt-2 text-4xl">{data.processing.extracted_count}</div></Card>
            <Card className="p-5"><div className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#23877e]">Reviewed for screening</div><div className="protocol-title mt-2 text-4xl">{data.processing.reviewed_count}</div></Card>
            <Card className="p-5"><div className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#d7902f]">Held for interpretation</div><div className="protocol-title mt-2 text-4xl">{data.processing.manual_review_count}</div></Card>
          </section>

          <Card className="mt-7 overflow-hidden">
            <div className="flex flex-col gap-4 border-b border-slate-200 p-5 lg:flex-row lg:items-center">
              <div><h3 className="text-sm font-bold">Eligibility clause register</h3><p className="mt-1 text-xs text-slate-500">Only reviewed, machine-evaluable clauses participate in pre-screening.</p></div>
              <div className="flex flex-col gap-3 sm:flex-row lg:ml-auto">
                <div className="flex rounded-lg bg-slate-100 p-1">
                  {(["ALL", "REVIEWED", "MANUAL_REVIEW"] as CriterionFilter[]).map((item) => (
                    <button key={item} onClick={() => setFilter(item)} className={cn("rounded-md px-3 py-1.5 text-[10px] font-bold", filter === item ? "bg-white text-[#10233b] shadow-sm" : "text-slate-500")}>{item.replace("_", " ")}</button>
                  ))}
                </div>
                <label className="relative">
                  <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                  <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find clause or concept" className="h-10 w-full rounded-lg border border-slate-200 pl-9 pr-3 text-xs outline-none focus:ring-2 focus:ring-[#1d5a85] sm:w-64" />
                </label>
              </div>
            </div>
            <div className="divide-y divide-slate-100">
              {criteria.map((criterion) => (
                <article key={criterion.criterion_id} className="grid gap-4 p-5 lg:grid-cols-[170px_1fr_280px]">
                  <div>
                    <div className="font-mono text-[11px] font-bold text-[#1d5a85]">{criterion.criterion_id}</div>
                    <div className="mt-2 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">{criterion.criterion_type} · {criterion.criterion_ordinal}</div>
                    <Badge status={criterion.review_status} className={cn("mt-3", criterion.review_status === "REVIEWED" && "border-teal-200 bg-teal-50 text-teal-800")}>{criterion.review_status.replace("_", " ")}</Badge>
                  </div>
                  <div>
                    <p className="m-0 protocol-title text-lg leading-7 text-[#10233b]">{criterion.source_clause}</p>
                    <p className="mt-2 text-xs text-slate-400">{criterion.source_location}</p>
                  </div>
                  <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-700">
                      {criterion.machine_evaluable ? <CheckCircle2 className="size-4 text-[#23877e]" /> : <CircleAlert className="size-4 text-[#d7902f]" />}
                      {criterion.machine_evaluable ? criterion.operator?.replaceAll("_", " ") : "Coordinator interpretation"}
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{criterion.review_notes ?? criterion.required_evidence ?? "Validated against the source clause."}</p>
                  </div>
                </article>
              ))}
              {!criteria.length && <div className="p-10 text-center text-sm text-slate-500">No clauses match this view.</div>}
            </div>
          </Card>
        </>
      )}
    </WorkspaceShell>
  );
}
