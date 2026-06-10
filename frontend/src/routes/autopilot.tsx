import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Rocket } from "lucide-react";
import { api } from "@/lib/api";
import { useVenture } from "@/context/VentureContext";
import { GlassCard, ErrorBanner, PrimaryButton, GradientText } from "@/components/venture/primitives";
import { LangGraphVisualizer, type LGNode } from "@/components/venture/LangGraph";
import { toast } from "sonner";

export const Route = createFileRoute("/autopilot")({
  head: () => ({ meta: [{ title: "Autopilot · VentureMind AI" }] }),
  component: Autopilot,
});

const NODES_INIT: LGNode[] = [
  { id: "start", label: "START", x: 60, y: 110, status: "idle" },
  { id: "p", label: "Problems", x: 170, y: 110, status: "idle" },
  { id: "s", label: "Solution", x: 290, y: 110, status: "idle" },
  { id: "v", label: "Validation", x: 410, y: 110, status: "idle" },
  { id: "c", label: "Competitors", x: 530, y: 110, status: "idle" },
  { id: "r", label: "Red Team", x: 650, y: 110, status: "idle" },
  { id: "m", label: "Roadmap", x: 770, y: 110, status: "idle" },
  { id: "end", label: "END", x: 860, y: 110, status: "idle" },
];

function Autopilot() {
  const { update } = useVenture();
  const [domain, setDomain] = useState("");
  const [nodes, setNodes] = useState<LGNode[]>(NODES_INIT);
  const [active, setActive] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const ts = () => new Date().toLocaleTimeString();
  const log = (m: string) => setLogs((l) => [...l, `[${ts()}] ${m}`]);

  const animate = (total: number, onTick: (i: number) => void, onDone: () => void) => {
    let i = 0;
    const step = () => {
      onTick(i);
      i++;
      if (i <= total) setTimeout(step, 700);
      else onDone();
    };
    step();
  };

  const start = async () => {
    if (!domain.trim()) { toast.error("Enter a domain"); return; }
    setRunning(true); setDone(false); setErr(null); setLogs([]); setActive(0);
    setNodes(NODES_INIT.map((n) => ({ ...n, status: "idle" })));
    log(`Initializing autopilot scan for "${domain}"`);

    // Start the API call and stage animation in parallel
    const apiPromise = api.executeWorkflow(domain).catch((e) => { setErr(e.message); return null; });

    animate(NODES_INIT.length, (i) => {
      setActive(i);
      setNodes((ns) => ns.map((n, j) => ({
        ...n,
        status: j < i ? "done" : j === i ? "active" : "idle",
      })));
      if (i > 0 && i < NODES_INIT.length) log(`Agent handoff → ${NODES_INIT[i].label}`);
    }, async () => {
      const r: any = await apiPromise;
      if (r) {
        update({
          domain,
          startupIdea: r.startup_idea || r.solution?.startup_idea || "",
          solution: r.solution || null,
          validation: r.validation || null,
          competitorData: r.competitors || r.competitor_data || null,
          criticFeedback: r.critic_feedback || r.red_team || null,
          roadmap: r.roadmap || null,
        });
        log("Workflow complete · memory persisted");
        setDone(true);
      } else {
        setNodes((ns) => ns.map((n, j) => j === ns.length - 1 ? { ...n, status: "failed" } : n));
        log("Workflow failed");
      }
      setRunning(false);
    });
  };

  return (
    <div className="px-6 lg:px-10 py-8 max-w-6xl">
      <h1 className="text-3xl font-bold"><GradientText>Autonomous Autopilot</GradientText></h1>
      <p className="text-sm text-slate-400 mt-2">Execute the full LangGraph agent pipeline end-to-end.</p>

      <GlassCard className="mt-6 flex gap-2">
        <input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="Domain (e.g., Healthcare AI)"
          className="flex-1 bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/60" />
        <PrimaryButton onClick={start} disabled={running}><Rocket className="w-4 h-4" /> Initiate Autopilot Scan</PrimaryButton>
      </GlassCard>

      {err && <div className="mt-4"><ErrorBanner message={err} /></div>}

      <GlassCard className="mt-6">
        <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">LangGraph Pipeline</div>
        <LangGraphVisualizer nodes={nodes} activeIndex={active} />
      </GlassCard>

      <GlassCard className="mt-4 font-mono">
        <div className="text-xs uppercase tracking-wider text-emerald-300 mb-2">Console</div>
        <div className="bg-slate-950/60 border border-slate-800 rounded-md p-3 h-56 overflow-y-auto vm-scrollbar text-xs text-emerald-300/90">
          {logs.length === 0 && <div className="text-slate-600">Awaiting input…</div>}
          {logs.map((l, i) => <div key={i}>{l}</div>)}
        </div>
      </GlassCard>

      {done && (
        <div className="mt-6">
          <Link to="/report"><PrimaryButton>Open Consolidated Report</PrimaryButton></Link>
        </div>
      )}
    </div>
  );
}