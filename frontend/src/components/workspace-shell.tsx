import { useState, type ReactNode } from "react";
import { Link, useLocation } from "wouter";
import {
  Activity,
  BookOpenText,
  ClipboardCheck,
  FileSearch,
  FlaskConical,
  History,
  LayoutDashboard,
  Menu,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const nav = [
  [LayoutDashboard, "Command center", "/"],
  [BookOpenText, "Protocols", "/protocols"],
  [Users, "Screening", "/screening"],
  [ClipboardCheck, "Worklist", "/worklist"],
  [Activity, "Operations", "/operations"],
  [FlaskConical, "Scenario lab", "/scenarios"],
  [History, "Audit history", "/audit"],
] as const;

export function WorkspaceShell({
  eyebrow,
  title,
  children,
  aside,
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
  aside?: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [location] = useLocation();

  return (
    <div className="min-h-screen">
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
            <div className="protocol-title text-[17px] font-semibold tracking-wide">TrialOps</div>
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Evidence desk</div>
          </div>
          <button className="ml-auto lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation">
            <X className="size-5" />
          </button>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-6">
          <div className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Workspace</div>
          {nav.map(([Icon, label, path]) => (
            <Link
              key={path}
              href={path}
              onClick={() => setOpen(false)}
              className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                  location === path ? "bg-white/10 font-semibold text-white" : "text-slate-400 hover:bg-white/5 hover:text-white",
                )}
            >
              <Icon className="size-[18px]" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="m-3 rounded-xl border border-white/10 bg-white/[0.04] p-4">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-200">
            <ShieldCheck className="size-4 text-[#70d0c6]" /> Governed synthetic data
          </div>
          <p className="m-0 text-[11px] leading-5 text-slate-400">Decision support only. Human approval is recorded before workflow state changes.</p>
        </div>
      </aside>

      {open && <button className="fixed inset-0 z-30 bg-black/20 lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu" />}

      <main className="lg:pl-[264px]">
        <header className="flex h-20 items-center border-b border-slate-200 bg-white/90 px-4 backdrop-blur md:px-8">
          <Button variant="ghost" size="icon" className="mr-2 lg:hidden" onClick={() => setOpen(true)}>
            <Menu className="size-5" />
          </Button>
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#1d5a85]">{eyebrow}</div>
            <h1 className="protocol-title mt-1 text-xl font-semibold">{title}</h1>
          </div>
          <div className="ml-auto flex items-center gap-3">
            {aside}
            <div className="grid size-9 place-items-center rounded-full bg-[#e1eef5] text-xs font-bold text-[#1d5a85]">TC</div>
          </div>
        </header>
        <div className="mx-auto max-w-[1440px] p-4 md:p-8">{children}</div>
      </main>
    </div>
  );
}
