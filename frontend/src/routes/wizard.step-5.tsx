import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { useVenture } from "@/context/VentureContext";
import { GlassCard, ScanCard, ErrorBanner, PrimaryButton, SecondaryButton, GradientText } from "@/components/venture/primitives";
import { toast } from "sonner";

export const Route = createFileRoute("/wizard/step-5")({ component: Step5 });

function Step5() {
  const navigate = useNavigate();
  const { state, update } = useVenture();
  const [data, setData] = useState<any>(state.competitorData);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = async () => {
    if (!state.startupIdea) { toast.error("No startup idea set"); return; }
    setLoading(true); setErr(null);
    try {
      const a: any = await api.analyzeCompetitors(state.startupIdea);
      let ml: any = null;
      try { ml = await api.competitorsAnalyze({ startup_idea: state.startupIdea, competitors: a?.competitors || a }); } catch {}
      const merged = { ...a, ml };
      setData(merged);
      update({ competitorData: merged });
    } catch (e: any) { setErr(e.message); toast.error(e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => { if (!data) run(); /* eslint-disable-next-line */ }, []);

  const competitors: any[] = data?.competitors || data?.results || [];
  const matches: any[] = data?.ml?.semantic_matches || data?.semantic_matches || [];
  const gaps: string[] = data?.market_gaps || data?.gaps || data?.opportunities || [];
  const recs: string[] = data?.ml?.recommendations || data?.recommendations || [];

  return (
    <div className="max-w-6xl">
      <h2 className="text-3xl font-bold"><GradientText>Competitor & Market Gap Analysis</GradientText></h2>
      {loading && <div className="mt-6"><ScanCard label="Competitor Agent querying Qdrant vector index…" /></div>}
      {err && <div className="mt-6"><ErrorBanner message={err} onRetry={run} /></div>}

      {data && (
        <div className="space-y-4 mt-6">
          <GlassCard>
            <div className="text-xs uppercase tracking-wider text-slate-500 mb-3">Competitor Landscape</div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-left text-xs text-slate-500 border-b border-slate-800"><th className="py-2">Name</th><th className="py-2">Strengths</th><th className="py-2">Weaknesses</th></tr></thead>
                <tbody>
                  {competitors.length === 0 && <tr><td colSpan={3} className="py-3 text-slate-500 text-xs">No competitors found.</td></tr>}
                  {competitors.map((c, i) => (
                    <tr key={i} className="border-b border-slate-800/40">
                      <td className="py-2 text-slate-200 font-medium">{c.name || c.title}</td>
                      <td className="py-2 text-slate-400 text-xs">{(c.strengths || []).join(", ") || "—"}</td>
                      <td className="py-2 text-slate-400 text-xs">{(c.weaknesses || []).join(", ") || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <GlassCard>
              <div className="text-xs uppercase tracking-wider text-violet-300 mb-3">Semantic Matches</div>
              <ul className="space-y-2">
                {matches.length === 0 && <li className="text-xs text-slate-500">None.</li>}
                {matches.map((m, i) => (
                  <li key={i} className="flex items-center justify-between text-sm">
                    <span className="text-slate-200">{m.name || m.title}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-violet-500/15 text-violet-300 border border-violet-500/30">
                      {Math.round((m.similarity ?? m.score ?? 0) * 100)}%
                    </span>
                  </li>
                ))}
              </ul>
            </GlassCard>
            <GlassCard>
              <div className="text-xs uppercase tracking-wider text-emerald-300 mb-3">Market Gaps & Opportunities</div>
              <ul className="space-y-2">
                {gaps.length === 0 && <li className="text-xs text-slate-500">No gaps surfaced.</li>}
                {gaps.map((g: any, i) => <li key={i} className="text-sm text-slate-300 flex gap-2"><span className="text-emerald-400">▸</span>{typeof g === "string" ? g : (g?.title || JSON.stringify(g))}</li>)}
              </ul>
            </GlassCard>
          </div>

          {recs.length > 0 && (
            <GlassCard>
              <div className="text-xs uppercase tracking-wider text-indigo-300 mb-3">Strategic Recommendations</div>
              <ul className="space-y-2">{recs.map((r, i) => <li key={i} className="text-sm text-slate-300 flex gap-2"><span className="text-indigo-400">▸</span>{r}</li>)}</ul>
            </GlassCard>
          )}
        </div>
      )}

      <div className="flex items-center justify-between mt-6">
        <Link to="/wizard/step-4"><SecondaryButton><ArrowLeft className="w-4 h-4" /> Back</SecondaryButton></Link>
        <PrimaryButton disabled={!data} onClick={() => navigate({ to: "/wizard/step-6" })}>Trigger Red Team Critique <ArrowRight className="w-4 h-4" /></PrimaryButton>
      </div>
    </div>
  );
}