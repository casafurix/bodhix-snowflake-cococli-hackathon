import { useQuery } from "@tanstack/react-query";
import { BellRing, CheckCircle2, CircleAlert, LoaderCircle } from "lucide-react";
import { api } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { WorkspaceShell } from "@/components/workspace-shell";

export function NotificationsPage() {
  const tasks = useQuery({ queryKey: ["tasks"], queryFn: api.tasks });
  const items = tasks.data?.items ?? [];
  return <WorkspaceShell eyebrow="Operational signals" title="Notifications"><section className="max-w-4xl"><Badge className="border-amber-200 bg-amber-50 text-amber-800">Evidence-first alerts</Badge><h2 className="protocol-title mt-3 text-3xl leading-tight md:text-4xl">See what changed and where a person is needed.</h2><p className="mt-3 text-sm leading-6 text-slate-600">This feed is derived from governed worklist state. Protocol monitoring alerts will appear here when scheduled source synchronization is enabled.</p></section><Card className="mt-7 overflow-hidden"><div className="flex items-center border-b border-slate-100 p-5"><BellRing className="size-4 text-[#1d5a85]" /><h3 className="ml-2 text-sm font-bold">Current activity feed</h3><span className="ml-auto text-xs font-bold text-slate-400">{items.length}</span></div>{tasks.isLoading && <div className="grid h-52 place-items-center"><LoaderCircle className="size-6 animate-spin text-[#1d5a85]" /></div>}<div className="divide-y divide-slate-100">{items.map((task) => <article key={task.task_key} className="flex gap-4 p-5"><div className={`grid size-9 shrink-0 place-items-center rounded-full ${task.status === "OPEN" ? "bg-amber-50 text-amber-700" : "bg-teal-50 text-teal-700"}`}>{task.status === "OPEN" ? <CircleAlert className="size-4" /> : <CheckCircle2 className="size-4" />}</div><div><div className="flex flex-wrap items-center gap-2"><span className="text-sm font-bold">{task.patient_id}</span><Badge status={task.source_status}>{task.source_status.replaceAll("_", " ")}</Badge></div><p className="mb-0 mt-2 text-xs leading-5 text-slate-500">{task.reason}</p><div className="mt-2 text-[10px] text-slate-400">{new Date(task.updated_at).toLocaleString()}</div></div></article>)}</div></Card></WorkspaceShell>;
}
