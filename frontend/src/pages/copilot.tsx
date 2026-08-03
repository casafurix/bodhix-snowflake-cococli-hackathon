import { Bot, ShieldCheck, Sparkles } from "lucide-react";
import { CopilotCard } from "@/App";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { WorkspaceShell } from "@/components/workspace-shell";

export function CopilotPage() {
  return <WorkspaceShell eyebrow="Evidence-grounded assistant" title="AI Copilot">
    <section className="grid gap-6 xl:grid-cols-[1fr_420px]"><div><Badge className="border-teal-200 bg-teal-50 text-teal-800">Snowflake Cortex + governed rules</Badge><h2 className="protocol-title mt-3 max-w-4xl text-3xl leading-tight md:text-5xl">Ask the workspace. Inspect every step.</h2><p className="mt-4 max-w-3xl text-sm leading-7 text-slate-600">ATLAS answers operational questions using the selected protocol, synthetic evidence, screening results, and current tasks. Every response exposes retrieval, model, citations, and the human approval boundary.</p><div className="mt-8 grid gap-4 sm:grid-cols-2"><Card className="p-5"><Sparkles className="size-5 text-[#1d5a85]" /><h3 className="mt-4 text-sm font-bold">Questions that resolve work</h3><p className="mt-2 text-xs leading-5 text-slate-500">Explain a candidate result, locate missing information, compare site workload, or generate a coordinator briefing.</p></Card><Card className="p-5"><ShieldCheck className="size-5 text-[#23877e]" /><h3 className="mt-4 text-sm font-bold">Actions stay human-gated</h3><p className="mt-2 text-xs leading-5 text-slate-500">The copilot may propose a worklist action. It cannot enroll, contact, diagnose, treat, or order a test.</p></Card></div><div className="mt-8 rounded-2xl border border-[#c7dce4] bg-[#eef5f8] p-6"><div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.15em] text-[#1d5a85]"><Bot className="size-4" />Good questions to try</div><div className="mt-4 grid gap-2 text-xs text-[#24364b]"><span>“Why is P004 in manual review?”</span><span>“Which candidates need evidence?”</span><span>“Which site needs attention today?”</span><span>“Give me a daily coordinator briefing.”</span></div></div></div><div><CopilotCard /></div></section>
  </WorkspaceShell>;
}
