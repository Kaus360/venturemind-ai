import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import { LayoutDashboard, Rocket, Compass, Search, Target, Shield, Sparkles, History } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useVenture } from "@/context/VentureContext";
import { VerdictBadge } from "./primitives";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/autopilot", label: "Autopilot", icon: Rocket },
  { to: "/wizard/step-1", label: "Venture Wizard", icon: Compass },
  { to: "/startups", label: "Startup Explorer", icon: Search },
  { to: "/market-gaps", label: "Market Gaps", icon: Target },
  { to: "/admin", label: "Admin", icon: Shield },
];

function HealthDot() {
  const [healthy, setHealthy] = useState<boolean | null>(null);
  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const r: any = await api.health();
        const ok = !!(r?.status === "healthy" || r?.healthy || r?.ok || r?.status === "ok");
        if (alive) setHealthy(ok);
      } catch {
        if (alive) setHealthy(false);
      }
    };
    poll();
    const id = setInterval(poll, 30000);
    return () => { alive = false; clearInterval(id); };
  }, []);
  const color = healthy === null ? "bg-slate-500" : healthy ? "bg-emerald-400" : "bg-rose-500";
  return (
    <div className="flex items-center gap-2">
      <div className={cn("w-2.5 h-2.5 rounded-full", color, healthy ? "vm-pulse-emerald" : healthy === false ? "vm-blink" : "")} />
      <span className="text-xs text-slate-400">
        {healthy === null ? "Checking…" : healthy ? "All systems nominal" : "Degraded"}
      </span>
    </div>
  );
}

function MemoryHistory() {
  const { loadFromMemory } = useVenture();
  const navigate = useNavigate();
  const [items, setItems] = useState<any[] | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r: any = await api.memoryContext();
        const arr = Array.isArray(r) ? r : r?.records || r?.history || r?.items || [];
        if (alive) setItems(arr.slice(0, 5));
      } catch {
        if (alive) setErr(true);
      }
    })();
    return () => { alive = false; };
  }, []);
  return (
    <div className="mt-6">
      <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-slate-500 mb-3 px-2">
        <History className="w-3 h-3" /> Memory History
      </div>
      <div className="space-y-1.5 max-h-72 overflow-y-auto vm-scrollbar pr-1">
        {err && <div className="text-[11px] text-rose-400/80 px-2">Memory unavailable</div>}
        {!err && !items && Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-12 rounded-md bg-slate-800/40 vm-shimmer" />
        ))}
        {items && items.length === 0 && <div className="text-[11px] text-slate-500 px-2">No runs yet</div>}
        {items?.map((it, i) => (
          <button
            key={i}
            onClick={() => { loadFromMemory(it); navigate({ to: "/report" }); }}
            className="w-full text-left px-2.5 py-2 rounded-md hover:bg-slate-800/60 transition group relative overflow-hidden"
          >
            <div className="absolute inset-0 vm-shimmer opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative">
              <div className="flex items-center justify-between gap-2">
                <div className="text-xs font-medium text-slate-200 truncate">{it.domain || "Unknown"}</div>
                <VerdictBadge verdict={it.verdict || it.critic_feedback?.verdict} />
              </div>
              <div className="text-[11px] text-slate-500 truncate mt-0.5">
                {it.startup_idea || it.startupIdea || it.problem_statement || "—"}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function Sidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <aside className="w-64 shrink-0 border-r border-slate-800/80 bg-slate-950/70 backdrop-blur-xl flex flex-col vm-no-print">
      <div className="p-5 border-b border-slate-800/60">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/30 group-hover:shadow-indigo-500/60 transition-shadow">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="text-base font-bold leading-tight"><span className="vm-text-gradient">VentureMind</span> <span className="text-slate-200">AI</span></div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">Venture Intelligence OS</div>
          </div>
        </Link>
      </div>
      <nav className="p-3 flex-1 overflow-y-auto vm-scrollbar">
        <div className="space-y-1">
          {NAV.map((n) => {
            const base = n.to === "/wizard/step-1" ? "/wizard" : n.to;
            const active = base === "/" ? pathname === "/" : pathname.startsWith(base);
            const Icon = n.icon;
            return (
              <Link
                key={n.to}
                to={n.to}
                className={cn(
                  "group relative flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-all",
                  active ? "bg-slate-800/60 text-white" : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/30",
                )}
              >
                <span className={cn(
                  "absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-full bg-gradient-to-b from-indigo-400 to-violet-500 transition-all",
                  active ? "opacity-100" : "opacity-0 group-hover:opacity-60",
                )} />
                <Icon className="w-4 h-4" />
                <span>{n.label}</span>
              </Link>
            );
          })}
        </div>
        <MemoryHistory />
      </nav>
      <div className="p-3 border-t border-slate-800/60 text-[10px] text-slate-600">© 2026 VentureMind AI</div>
    </aside>
  );
}

const CRUMBS: Record<string, string> = {
  "/": "Dashboard",
  "/autopilot": "Autopilot",
  "/startups": "Startup Explorer",
  "/market-gaps": "Market Gap Finder",
  "/admin": "Admin Control Room",
  "/report": "Consolidated Report",
  "/wizard/step-1": "Wizard · Domain & Problems",
  "/wizard/step-2": "Wizard · Problem Directives",
  "/wizard/step-3": "Wizard · Solution Editor",
  "/wizard/step-4": "Wizard · Validation",
  "/wizard/step-5": "Wizard · Competitors & Gaps",
  "/wizard/step-6": "Wizard · Red Team",
  "/wizard/step-7": "Wizard · Roadmap",
};

function Topbar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const label = CRUMBS[pathname] || pathname;
  return (
    <header className="h-14 border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-xl flex items-center justify-between px-6 vm-no-print">
      <div className="flex items-center gap-3 text-sm">
        <span className="text-slate-500">VentureMind</span>
        <span className="text-slate-700">/</span>
        <span className="text-slate-200 font-medium">{label}</span>
      </div>
      <div className="flex items-center gap-4">
        <HealthDot />
        <Link
          to="/autopilot"
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md text-sm font-medium bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50 transition-all hover:scale-[1.03]"
        >
          <Rocket className="w-4 h-4" /> New Venture Scan
        </Link>
      </div>
    </header>
  );
}

export function Shell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <div className="vm-mesh-bg min-h-screen text-slate-100 flex">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar />
        <motion.main
          key={pathname}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="flex-1 overflow-y-auto vm-scrollbar"
        >
          {children}
        </motion.main>
      </div>
    </div>
  );
}