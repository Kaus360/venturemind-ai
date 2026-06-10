import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { useVenture } from "@/context/VentureContext";
import { GlassCard, ScanCard, ErrorBanner, PrimaryButton, SecondaryButton, GradientText, GlowOrb, CountUp } from "@/components/venture/primitives";
import { ScoreGauge } from "@/components/venture/ScoreGauge";
import { toast } from "sonner";

export const Route = createFileRoute("/wizard/step-4")({ component: Step4 });

function Step4() {
  const navigate = useNavigate();
  const { state, update } = useVenture();
  const [val, setVal] = useState<any>(state.validation);
  const [scores, setScores] = useState<any>(state.validation?.ml_scores);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = async () => {
    if (!state.startupIdea) { toast.error("No startup idea set"); return; }
    setLoading(true); setErr(null);
    try {
      const v: any = await api.validateStartup(state.startupIdea);
      setVal(v);
      const payload = {
        startup_idea: state.startupIdea,
        innovation_score: v.innovation_score ?? 70,
        market_demand: v.market_demand ?? 70,
        competition_risk: v.competition_risk ?? 50,
        feasibility: v.feasibility ?? 70,
      };
      try {
        const s: any = await api.scoresStartup(payload);
        setScores(s);
        const merged = { ...v, ml_scores: s };
        update({ validation: merged });
      } catch {
        update({ validation: v });
      }
    } catch (e: any) { setErr(e.message); toast.error(e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => { if (!val) run(); /* eslint-disable-next-line */ }, []);

  const composite = Number(scores?.composite_score ?? val?.composite_score ?? val?.overall_score ?? 0);
  const grade = scores?.grade ?? val?.grade ?? "—";
  const metrics = [
    { label: "Innovation", v: Number(val?.innovation_score ?? 0), c: "#6366f1" },
    { label: "Market Demand", v: Number(val?.market_demand ?? 0), c: "#8b5cf6" },
    { label: "Competition Risk", v: Number(val?.competition_risk ?? 0), c: "#f59e0b" },
    { label: "Feasibility", v: Number(val?.feasibility ?? 0), c: "#10b981" },
  ];
  const weaknesses: string[] = val?.weaknesses || val?.risks || [];
  const recs: string[] = scores?.recommendations || val?.recommendations || [];

  return (
    <div className="max-w-6xl">
      <h2 className="text-3xl font-bold"><GradientText>Validation Dashboard</GradientText></h2>
      <p className="text-sm text-slate-400 mt-2">Composite viability scoring across innovation, demand, risk, and feasibility.</p>

      {loading && <div className="mt-6"><ScanCard label="Validation Agent computing viability metrics…" /></div>}
      {err && <div className="mt-6"><ErrorBanner message={err} onRetry={run} /></div>}

      {val && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-6">
            <GlassCard className="lg:col-span-1 flex flex-col items-center justify-center relative">
              <GlowOrb color="indigo" className="w-64 h-64 inset-0 m-auto opacity-40" />
              <div className="relative">
                <ScoreGauge value={composite} size={200} color="#818cf8" centerText={String(grade)} label="Composite" />
              </div>
              <div className="mt-3 text-xs text-slate-400"><CountUp to={composite} suffix=" / 100" /></div>
            </GlassCard>
            <div className="lg:col-span-2 grid grid-cols-2 gap-4">
              {metrics.map((m) => (
                <GlassCard key={m.label} className="relative">
                  <GlowOrb color="indigo" className="w-24 h-24 -top-6 -right-6" />
                  <div className="text-xs uppercase tracking-wider text-slate-500">{m.label}</div>
                  <div className="flex items-center justify-between mt-2">
                    <div className="text-3xl font-bold text-white"><CountUp to={m.v} /></div>
                    <ScoreGauge value={m.v} size={72} color={m.c} centerText="" />
                  </div>
                </GlassCard>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
            <GlassCard>
              <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-amber-300 mb-3"><AlertTriangle className="w-3.5 h-3.5" /> Weaknesses</div>
              <ul className="space-y-2">
                {weaknesses.length === 0 && <li className="text-xs text-slate-500">No weaknesses reported.</li>}
                {weaknesses.map((w, i) => (
                  <li key={i} className="text-sm text-slate-300 flex gap-2"><span className="text-amber-400">▸</span>{w}</li>
                ))}
              </ul>
            </GlassCard>
            <GlassCard>
              <div className="text-xs uppercase tracking-wider text-indigo-300 mb-3">Recommendations</div>
              <ul className="space-y-2">
                {recs.length === 0 && <li className="text-xs text-slate-500">No recommendations.</li>}
                {recs.map((r, i) => (
                  <li key={i} className="text-sm text-slate-300 flex gap-2"><span className="text-indigo-400">▸</span>{r}</li>
                ))}
              </ul>
            </GlassCard>
          </div>
        </>
      )}

      <div className="flex items-center justify-between mt-6">
        <Link to="/wizard/step-3"><SecondaryButton><ArrowLeft className="w-4 h-4" /> Back</SecondaryButton></Link>
        <PrimaryButton disabled={!val} onClick={() => navigate({ to: "/wizard/step-5" })}>Run Competitor & Market Gap Scans <ArrowRight className="w-4 h-4" /></PrimaryButton>
      </div>
    </div>
  );
}