import { useQuery } from "@tanstack/react-query";
import { Activity, CircleAlert, LoaderCircle, MapPin, Users } from "lucide-react";
import { api } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { WorkspaceShell } from "@/components/workspace-shell";

const segments = [
  ["potential_match_count", "bg-[#23877e]", "Potential"],
  ["missing_information_count", "bg-[#d7902f]", "Missing"],
  ["manual_review_count", "bg-[#1d5a85]", "Manual"],
  ["excluded_count", "bg-[#b84b52]", "Excluded"],
] as const;

export function OperationsPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["operations"], queryFn: api.operations });
  const total = data?.sites.reduce((sum, site) => sum + site.candidate_count, 0) ?? 0;
  const reviewLoad = data?.sites.reduce((sum, site) => sum + site.missing_information_count + site.manual_review_count, 0) ?? 0;

  return (
    <WorkspaceShell eyebrow="Hospital trial operations" title="Site evidence load">
      <section className="grid gap-5 xl:grid-cols-[1fr_360px] xl:items-end">
        <div><Badge className="border-blue-200 bg-blue-50 text-[#1d5a85]">Current screening run</Badge><h2 className="protocol-title mt-3 text-3xl leading-tight md:text-4xl">See where evidence work is accumulating before it becomes delay.</h2><p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">This view uses the same governed candidate results as the coordinator workspace. It does not estimate enrollment from invented historical data.</p></div>
        <Card className="p-5"><div className="font-mono text-[10px] font-bold text-[#1d5a85]">{data?.run_id ?? "—"}</div><div className="mt-4 flex items-end gap-8"><div><div className="protocol-title text-4xl">{total}</div><div className="text-xs text-slate-500">candidates</div></div><div><div className="protocol-title text-4xl text-[#d7902f]">{reviewLoad}</div><div className="text-xs text-slate-500">need evidence work</div></div></div></Card>
      </section>

      {isLoading && <div className="grid h-64 place-items-center"><LoaderCircle className="size-6 animate-spin text-[#1d5a85]" /></div>}
      {error && <Card className="mt-7 p-6 text-sm text-rose-800">Site operations could not be loaded.</Card>}
      <section className="mt-7 grid gap-5 lg:grid-cols-3">
        {(data?.sites ?? []).map((site) => (
          <Card key={site.site_id} className="overflow-hidden">
            <div className="border-b border-slate-100 p-5"><div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-[#1d5a85]"><MapPin className="size-4" />Synthetic site</div><h3 className="protocol-title mt-2 text-2xl">{site.site_id}</h3></div>
            <div className="p-5">
              <div className="flex items-center text-xs text-slate-500"><Users className="mr-2 size-4" />{site.candidate_count} candidates<span className="ml-auto font-bold text-slate-700">{site.average_evidence_completeness}% complete</span></div>
              <div className="mt-5 flex h-3 overflow-hidden rounded-full bg-slate-100">
                {segments.map(([key, tone]) => <div key={key} className={tone} style={{ width: `${(site[key] / site.candidate_count) * 100}%` }} />)}
              </div>
              <div className="mt-5 grid grid-cols-2 gap-3">
                {segments.map(([key, tone, label]) => <div key={key} className="flex items-center rounded-lg bg-slate-50 p-3 text-xs"><span className={`mr-2 size-2 rounded-full ${tone}`} /><span className="text-slate-500">{label}</span><span className="ml-auto font-bold">{site[key]}</span></div>)}
              </div>
              {(site.missing_information_count + site.manual_review_count) > 0 && <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-100 bg-amber-50 p-3 text-[11px] leading-4 text-amber-900"><CircleAlert className="mt-0.5 size-4 shrink-0" />{site.missing_information_count + site.manual_review_count} cases need coordinator evidence resolution.</div>}
            </div>
          </Card>
        ))}
      </section>
      <Card className="mt-7 p-5 text-xs leading-5 text-slate-500"><div className="flex items-center gap-2 font-bold text-slate-700"><Activity className="size-4 text-[#23877e]" />Scope boundary</div><p className="mb-0 mt-2">Recruitment forecasting needs historical screening, enrollment, dropout, and capacity measures. Until those governed inputs are loaded, this page reports only observed synthetic cohort workload.</p></Card>
    </WorkspaceShell>
  );
}
