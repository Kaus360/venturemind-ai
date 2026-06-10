import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { useVenture } from "@/context/VentureContext";
import { GlassCard, ScanCard, ErrorBanner, PrimaryButton, SecondaryButton, GradientText } from "@/components/venture/primitives";

export const Route = createFileRoute("/wizard/step-7")({ component: Step7 });

function Step7() {
  const navigate = useNavigate();
  const { state, update } = useVenture();
  const [data, setData] = useState<any>(state.roadmap);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const run = async () => {
    setLoading(true); setErr(null);
    try {
      const r: any = await api.generateRoadmap(state.startupIdea, state.solution || {}, state.validation || {});
      setData(r); update({ roadmap: r });
    } catch (e: any) { setErr(e.message); } finally { setLoading(false); }
  };
  useEffect(() => { if (!data) run(); /* eslint-disable-next-line */ }, []);

  const mvp: string[] = data?.mvp_features || data?.mvp || [];
  const phases: any[] = data?.phases || [];
  const scaling: string = data?.scaling_strategy || data?.scaling || "";

  return (
    <div className="max-w-6xl">
      <h2 className="text-3xl font-bold"><GradientText>Roadmap</GradientText></h2>
      {loading && <div className="mt-6"><ScanCard label="Roadmap Agent formulating milestone schedules…" /></div>}
      {err && <div className="mt-6"><ErrorBanner message={err} onRetry={run} /></div>}
      {data && (
        <div className="space-y-4 mt-6">
          <GlassCard>
            <div className="text-xs uppercase tracking-wider text-indigo-300 mb-3">MVP Features</div>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">{mvp.map((m, i) => <li key={i} className="text-sm text-slate-200 flex gap-2"><span className="text-indigo-400">◆</span>{m}</li>)}</ul>
          </GlassCard>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => {
              const p = phases[i] || {};
              return (
                <GlassCard key={i} className="relative">
                  <div className="text-xs uppercase tracking-wider text-violet-300">Phase {i + 1}</div>
                  <div className="text-sm text-slate-300 mt-1">{p.timeline || p.duration || "—"}</div>
                  <ul className="mt-3 space-y-1.5">
                    {(p.goals || p.milestones || []).map((g: string, j: number) => <li key={j} className="text-xs text-slate-400 flex gap-2"><span className="text-violet-400">▸</span>{g}</li>)}
                  </ul>
                </GlassCard>
              );
            })}
          </div>
          {scaling && <GlassCard><div className="text-xs uppercase tracking-wider text-emerald-300 mb-2">Scaling Strategy</div><p className="text-sm text-slate-300 whitespace-pre-line">{scaling}</p></GlassCard>}
        </div>
      )}
      <div className="flex items-center justify-between mt-6">
        <Link to="/wizard/step-6"><SecondaryButton><ArrowLeft className="w-4 h-4" /> Back</SecondaryButton></Link>
        <PrimaryButton disabled={!data} onClick={() => navigate({ to: "/report" })}>View Final Venture Report <ArrowRight className="w-4 h-4" /></PrimaryButton>
      </div>
    </div>
  );
}