import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { useVenture } from "@/context/VentureContext";
import { GlassCard, ErrorBanner, ScanCard, PrimaryButton, GradientText } from "@/components/venture/primitives";
import { ScoreGauge } from "@/components/venture/ScoreGauge";
import { toast } from "sonner";

const PRESETS = ["Healthcare", "Fintech", "Agtech", "Logistics", "Edtech", "Cybersecurity"];

export const Route = createFileRoute("/wizard/step-1")({ component: Step1 });

function Step1() {
  const navigate = useNavigate();
  const { state, update } = useVenture();
  const [domain, setDomain] = useState(state.domain);
  const [problems, setProblems] = useState<any[] | null>(state.problems);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const analyze = async (d?: string) => {
    const value = (d ?? domain).trim();
    if (!value) { toast.error("Enter a domain to analyze"); return; }
    setDomain(value);
    update({ domain: value });
    setLoading(true); setErr(null); setProblems(null);
    try {
      const r: any = await api.generateProblems(value);
      const arr = Array.isArray(r) ? r : r?.problems || r?.results || [];
      setProblems(arr);
      update({ problems: arr });
      toast.success(`Discovered ${arr.length} problem candidates`);
    } catch (e: any) {
      setErr(e.message || "Problem discovery failed");
      toast.error(e.message || "Problem discovery failed");
    } finally { setLoading(false); }
  };

  const select = (p: any) => {
    const statement = p.problem_statement || p.statement || p.description || p.title || "";
    update({ selectedProblem: p, problemStatement: statement });
    navigate({ to: "/wizard/step-2" });
  };

  return (
    <div className="max-w-5xl">
      <h2 className="text-3xl font-bold"><GradientText>Domain & Problem Discovery</GradientText></h2>
      <p className="text-sm text-slate-400 mt-2">The Problem Discovery Agent will scan market pain points in your chosen vertical.</p>

      <GlassCard className="mt-6">
        <label className="text-xs uppercase tracking-wider text-slate-500">Target Domain</label>
        <div className="flex gap-2 mt-2">
          <input
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && analyze()}
            placeholder="e.g., Healthcare AI, Fintech, Logistics"
            className="flex-1 bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/20"
          />
          <PrimaryButton onClick={() => analyze()} disabled={loading}>
            <Sparkles className="w-4 h-4" /> Analyze Domain
          </PrimaryButton>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {PRESETS.map((p) => (
            <button
              key={p}
              onClick={() => { setDomain(p); analyze(p); }}
              className="text-xs px-3 py-1.5 rounded-full bg-slate-800/70 hover:bg-indigo-500/20 hover:text-indigo-200 text-slate-300 border border-slate-700/60 hover:border-indigo-500/40 transition-all hover:scale-[1.03]"
            >{p}</button>
          ))}
        </div>
      </GlassCard>

      {loading && <div className="mt-6"><ScanCard label="Problem Discovery Agent analyzing market pain points…" /></div>}
      {err && <div className="mt-6"><ErrorBanner message={err} onRetry={() => analyze()} /></div>}

      {problems && problems.length > 0 && (
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-4">
          {problems.map((p, i) => {
            const title = p.title || p.name || `Problem ${i + 1}`;
            const desc = p.description || p.problem_statement || p.statement || "";
            const audience = p.target_audience || p.audience || "—";
            const impact = Number(p.impact_score ?? p.impact ?? 0);
            const feas = Number(p.feasibility_score ?? p.feasibility ?? 0);
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.12, type: "spring", stiffness: 90 }}
              >
                <GlassCard className="h-full flex flex-col hover:border-indigo-500/40 transition-all group">
                  <div className="text-xs uppercase tracking-wider text-indigo-300/80">Candidate {i + 1}</div>
                  <h3 className="text-base font-semibold text-slate-100 mt-1">{title}</h3>
                  <p className="text-xs text-slate-400 mt-2 line-clamp-4">{desc}</p>
                  <div className="text-[11px] text-slate-500 mt-3"><span className="text-slate-400">Audience:</span> {audience}</div>
                  <div className="flex items-center justify-around mt-4">
                    <ScoreGauge value={impact} label="Impact" color="#8b5cf6" size={92} />
                    <ScoreGauge value={feas} label="Feasibility" color="#10b981" size={92} />
                  </div>
                  <PrimaryButton className="mt-4 w-full" onClick={() => select(p)}>
                    Select & Proceed <ArrowRight className="w-4 h-4" />
                  </PrimaryButton>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}