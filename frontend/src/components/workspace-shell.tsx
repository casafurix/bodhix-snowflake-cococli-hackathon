import { useState, type ReactNode } from "react";
import { Link, useLocation } from "wouter";
import {
  Activity,
  Bell,
  BookOpenText,
  ClipboardCheck,
  FileSearch,
  LayoutDashboard,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  ShieldCheck,
  Users,
  Settings,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const nav = [
  [LayoutDashboard, "Dashboard", "/"],
  [BookOpenText, "Trials", "/trials"],
  [Users, "Patients", "/patients"],
  [ClipboardCheck, "Tasks", "/tasks"],
  [Activity, "Analytics", "/analytics"],
  [Bell, "Notifications", "/notifications"],
  [Settings, "Settings", "/settings"],
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
  const [collapsed, setCollapsed] = useState(false);
  const [location] = useLocation();

  return (
    <div className="min-h-screen">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex flex-col bg-[#10233b] text-white transition-[transform,width] duration-200 lg:translate-x-0",
          collapsed ? "w-[72px]" : "w-[264px]",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className={cn("flex h-20 items-center border-b border-white/10", collapsed ? "justify-center px-3" : "px-6")}>
          <div className="grid size-10 place-items-center rounded-lg border border-white/15 bg-white/10">
            <FileSearch className="size-5 text-[#70d0c6]" />
          </div>
          <div className={cn("ml-3", collapsed && "hidden")}>
            <div className="protocol-title text-[17px] font-semibold tracking-wide">ATLAS</div>
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Trial intelligence</div>
          </div>
          <div className={cn("ml-auto flex items-center", collapsed && "absolute right-1 top-2")}>
            <button className="hidden rounded-md p-2 text-slate-300 hover:bg-white/10 lg:block" onClick={() => setCollapsed((value) => !value)} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} title={collapsed ? "Expand sidebar" : "Collapse sidebar"}>{collapsed ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}</button>
            <button className="ml-1 lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation"><X className="size-5" /></button>
          </div>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-6">
          <div className={cn("mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500", collapsed && "sr-only")}>Workspace</div>
          {nav.map(([Icon, label, path]) => (
            <Link
              key={path}
              href={path}
              onClick={() => setOpen(false)}
              className={cn(
                  "flex items-center rounded-lg px-3 py-2.5 text-sm transition-colors",
                  collapsed ? "justify-center" : "gap-3",
                  location === path ? "bg-white/10 font-semibold text-white" : "text-slate-400 hover:bg-white/5 hover:text-white",
              )}
              title={collapsed ? label : undefined}
            >
              <Icon className="size-[18px]" />
              <span className={cn(collapsed && "sr-only")}>{label}</span>
            </Link>
          ))}
        </nav>
        <div className={cn("m-3 rounded-xl border border-white/10 bg-white/[0.04] p-4", collapsed && "grid place-items-center p-3")}>
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-slate-200">
            <ShieldCheck className="size-4 shrink-0 text-[#70d0c6]" /> <span className={cn(collapsed && "sr-only")}>Governed synthetic data</span>
          </div>
          <p className={cn("m-0 text-[11px] leading-5 text-slate-400", collapsed && "hidden")}>Decision support only. Human approval is recorded before workflow state changes.</p>
        </div>
      </aside>

      {open && <button className="fixed inset-0 z-30 bg-black/20 lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu" />}

      <main className={cn("transition-[padding] duration-200", collapsed ? "lg:pl-[72px]" : "lg:pl-[264px]")}>
        <header className="flex h-20 items-center border-b border-slate-200 bg-white/90 px-4 backdrop-blur md:px-8">
          <Button variant="ghost" size="icon" className="mr-2 lg:hidden" onClick={() => setOpen(true)}>
            <Menu className="size-5" />
          </Button>
          <Button variant="ghost" size="icon" className="mr-2 hidden lg:inline-flex" onClick={() => setCollapsed((value) => !value)} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}>
            {collapsed ? <PanelLeftOpen className="size-5" /> : <PanelLeftClose className="size-5" />}
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
