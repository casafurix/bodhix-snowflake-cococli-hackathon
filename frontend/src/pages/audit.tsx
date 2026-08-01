import { useQuery } from "@tanstack/react-query";
import { History, LoaderCircle, ShieldCheck } from "lucide-react";
import { api } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { WorkspaceShell } from "@/components/workspace-shell";

export function AuditPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["audit-events"], queryFn: api.auditEvents });

  return (
    <WorkspaceShell eyebrow="Governed history" title="Append-only audit trail" aside={<div className="hidden items-center gap-2 text-xs font-semibold text-slate-500 sm:flex"><ShieldCheck className="size-4 text-[#23877e]" />Snowflake persisted</div>}>
      <section className="max-w-4xl">
        <Badge className="border-teal-200 bg-teal-50 text-teal-800">No silent rewrites</Badge>
        <h2 className="protocol-title mt-3 text-3xl leading-tight md:text-4xl">Every recommendation and human transition leaves a new record.</h2>
        <p className="mt-3 text-sm leading-6 text-slate-600">Corrections append another event. They do not erase the original state or its citations.</p>
      </section>
      <Card className="mt-7 overflow-hidden">
        <div className="grid grid-cols-[54px_1fr] border-b border-slate-200 bg-slate-50 px-5 py-3 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400"><span /><span>Latest events</span></div>
        {isLoading && <div className="grid h-64 place-items-center"><LoaderCircle className="size-6 animate-spin text-[#1d5a85]" /></div>}
        {error && <div className="p-6 text-sm text-rose-800">Audit history could not be loaded.</div>}
        <div className="relative divide-y divide-slate-100 before:absolute before:bottom-8 before:left-[46px] before:top-8 before:w-px before:bg-slate-200">
          {(data?.items ?? []).map((event) => (
            <article key={event.event_id} className="relative grid grid-cols-[54px_1fr] gap-3 p-5">
              <div className="z-[1] grid size-8 place-items-center rounded-full border-4 border-white bg-[#e1eef5] text-[#1d5a85]"><History className="size-3.5" /></div>
              <div className="grid gap-4 lg:grid-cols-[1fr_220px]">
                <div><div className="flex flex-wrap items-center gap-2"><span className="font-mono text-[10px] font-bold text-[#1d5a85]">{event.event_type}</span><Badge className="border-slate-200 bg-slate-50 text-slate-600">{event.actor}</Badge></div><p className="mt-2 text-sm font-semibold leading-5">{event.reason}</p><p className="mt-2 font-mono text-[10px] text-slate-400">{event.entity_id}</p></div>
                <div className="text-xs text-slate-500"><div>{new Date(event.occurred_at).toLocaleString()}</div><div className="mt-2 font-mono text-[10px]">{event.source_run_id}</div></div>
              </div>
            </article>
          ))}
          {!isLoading && !(data?.items.length) && <div className="p-10 text-center text-sm text-slate-500">No audit events are available in the offline fixture.</div>}
        </div>
      </Card>
    </WorkspaceShell>
  );
}
