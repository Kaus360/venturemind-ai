import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, AlertOctagon, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { useVenture } from "@/context/VentureContext";
import { GlassCard, ScanCard, ErrorBanner, PrimaryButton, SecondaryButton, GradientText, VerdictBadge } from "@/components/venture/primitives";

export const Route = createFileRoute("/wizard/step-6")({ component: Step6 });

function Step6() {
  const navigate = useNavigate();
  const { state, update } = useVenture();
  const [data, setData] = useState<any>(state.criticFeedback);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = async () => {
    setLoading(true); setErr(null);
    try {
      const r: any = await api.redteamCritique(state.startupIdea, state.validation || {});
      setData(r); update({ criticFeedback: r });
    } catch (e: any) { setErr(e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => { if (!data) run(); /* eslint-disable-next-line */ }, []);

  const verdict = (data?.verdict || "").toUpperCase();
  const flaws: string[] = data?.critical_flaws || data?.flaws || [];
  const assumptions: string[] = data?.unrealistic_assumptions || data?.assumptions || [];
  const viability = Number(data?.viability_score ?? data?.viability ?? 0);
  const pulse = verdict === "PASS" ? "vm-pulse-emerald" : verdict === "FAIL" ? "vm-pulse-rose" : "vm-pulse-indigo";

  return (
    <div className="max-w-5xl">
      <h2 className="text-3xl font-bold"><GradientText>Red Team Critique</GradientText></h2>
      {loading && <div className="mt-6"><ScanCard label="Red Team Critic executing devil's advocate review…" /></div>}
      {err && <div className="mt-6"><ErrorBanner message={err} onRetry={run} /></div>}
      {data && (
        <>
          <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 90, delay: 0.1 }}>
            <GlassCard className={`mt-6 text-center py-8 ${pulse}`}>
              <div className="text-xs uppercase tracking-wider text-slate-400">Verdict</div>
              <div className="mt-3 flex items-center justify-center gap-3">
                <VerdictBadge verdict={verdict} />
              </div>
              <div className="mt-4 max-w-md mx-auto">
                <div className="text-xs text-slate-500 mb-1">Viability Score · {Math.round(viability)}</div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden"><motion.div initial={{ width: 0 }} animate={{ width: `${viability}%` }} transition={{ duration: 1.2, ease: "easeOut" }} className="h-full bg-gradient-to-r from-indigo-500 to-violet-500" /></div>
              </div>
            </GlassCard>
          </motion.div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
            <GlassCard>
              <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-rose-300 mb-3"><AlertOctagon className="w-3.5 h-3.5" /> Critical Flaws</div>
              <ul className="space-y-2">{flaws.length === 0 ? <li className="text-xs text-slate-500">None.</li> : flaws.map((f, i) => <li key={i} className="text-sm text-slate-300 flex gap-2"><span className="text-rose-400">▸</span>{f}</li>)}</ul>
            </GlassCard>
            <GlassCard>
              <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-amber-300 mb-3"><AlertCircle className="w-3.5 h-3.5" /> Unrealistic Assumptions</div>
              <ul className="space-y-2">{assumptions.length === 0 ? <li className="text-xs text-slate-500">None.</li> : assumptions.map((a, i) => <li key={i} className="text-sm text-slate-300 flex gap-2"><span className="text-amber-400">▸</span>{a}</li>)}</ul>
            </GlassCard>
          </div>
        </>
      )}
      <div className="flex items-center justify-between mt-6">
        <Link to="/wizard/step-5"><SecondaryButton><ArrowLeft className="w-4 h-4" /> Back</SecondaryButton></Link>
        <PrimaryButton disabled={!data} onClick={() => navigate({ to: "/wizard/step-7" })}>Generate Roadmap <ArrowRight className="w-4 h-4" /></PrimaryButton>
      </div>
    </div>
  );
}