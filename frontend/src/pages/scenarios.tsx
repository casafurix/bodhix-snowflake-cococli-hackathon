import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, FlaskConical, LoaderCircle, ShieldCheck } from "lucide-react";
import { api } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { WorkspaceShell } from "@/components/workspace-shell";

export function ScenariosPage() {
  const { data, isLoading } = useQuery({ queryKey: ["operations"], queryFn: api.operations });
  const [capacity, setCapacity] = useState(1);
  const [resolution, setResolution] = useState(50);
  const outcome = useMemo(() => {
    const backlog = data?.sites.reduce((sum, site) => sum + site.missing_information_count + site.manual_review_count, 0) ?? 0;
    const resolvedPerWeek = capacity * (resolution / 100) * 2;
    return { backlog, resolvedPerWeek, weeks: resolvedPerWeek > 0 ? Math.ceil(backlog / resolvedPerWeek) : null };
  }, [capacity, data, resolution]);

  return (
    <WorkspaceShell eyebrow="What-if workspace" title="Evidence-resolution scenario">
      <section className="max-w-4xl"><Badge className="border-violet-200 bg-violet-50 text-violet-800">No production mutation</Badge><h2 className="protocol-title mt-3 text-3xl leading-tight md:text-4xl">Change operational assumptions without changing the governed run.</h2><p className="mt-3 text-sm leading-6 text-slate-600">This transparent planning calculation uses current missing-information and manual-review workload. It is not a clinical or enrollment forecast.</p></section>
      {isLoading ? <div className="grid h-64 place-items-center"><LoaderCircle className="size-6 animate-spin text-[#1d5a85]" /></div> : (
        <section className="mt-7 grid gap-5 xl:grid-cols-[1fr_1fr]">
          <Card className="p-6">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.14em] text-[#1d5a85]"><FlaskConical className="size-4" />Assumptions</div>
            <label className="mt-7 block"><div className="flex items-center text-sm font-bold"><span>Additional coordinator capacity</span><span className="ml-auto protocol-title text-2xl">{capacity}</span></div><input type="range" min="0" max="4" step="1" value={capacity} onChange={(event) => setCapacity(Number(event.target.value))} className="mt-3 w-full accent-[#1d5a85]" /><div className="mt-2 flex justify-between text-[10px] text-slate-400"><span>No addition</span><span>Four coordinators</span></div></label>
            <label className="mt-8 block"><div className="flex items-center text-sm font-bold"><span>Cases resolved per available shift</span><span className="ml-auto protocol-title text-2xl">{resolution}%</span></div><input type="range" min="25" max="100" step="25" value={resolution} onChange={(event) => setResolution(Number(event.target.value))} className="mt-3 w-full accent-[#23877e]" /><div className="mt-2 flex justify-between text-[10px] text-slate-400"><span>Conservative</span><span>All assigned cases</span></div></label>
          </Card>
          <Card className="overflow-hidden">
            <div className="border-b border-slate-100 bg-[#10233b] p-6 text-white"><div className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#70d0c6]">Scenario result</div><div className="mt-5 flex items-center gap-5"><div><div className="protocol-title text-5xl">{outcome.backlog}</div><div className="text-xs text-slate-400">current evidence cases</div></div><ArrowRight className="size-6 text-slate-500" /><div><div className="protocol-title text-5xl text-[#70d0c6]">{outcome.weeks ?? "—"}</div><div className="text-xs text-slate-400">estimated weeks to clear</div></div></div></div>
            <div className="p-6"><div className="text-sm font-bold">Transparent formula</div><p className="mt-2 text-xs leading-5 text-slate-500">{capacity} added coordinator{capacity === 1 ? "" : "s"} × 2 evidence shifts/week × {resolution}% resolution = <strong>{outcome.resolvedPerWeek.toFixed(1)} cases/week</strong>.</p><div className="mt-5 flex items-start gap-2 rounded-lg border border-teal-100 bg-teal-50 p-4 text-[11px] leading-4 text-teal-900"><ShieldCheck className="mt-0.5 size-4 shrink-0" />The scenario is calculated in the browser and does not change patients, screening results, tasks, or audit history.</div></div>
          </Card>
        </section>
      )}
    </WorkspaceShell>
  );
}
