import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Target } from "lucide-react";
import { api } from "@/lib/api";
import { GlassCard, ErrorBanner, PrimaryButton, GradientText, SkeletonCard } from "@/components/venture/primitives";

export const Route = createFileRoute("/market-gaps")({
  head: () => ({ meta: [{ title: "Market Gaps · VentureMind AI" }] }),
  component: Page,
});

function Page() {
  const [domain, setDomain] = useState("");
  const [topK, setTopK] = useState(10);
  const [gaps, setGaps] = useState<any[] | null>(null);
  const [comps, setComps] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = async () => {
    if (!domain.trim()) return;
    setLoading(true); setErr(null);
    try {
      const g: any = await api.retrievalMarketGaps(domain, topK);
      setGaps(Array.isArray(g) ? g : g?.results || g?.gaps || []);
      try {
        const c: any = await api.retrievalCompetitors(domain, topK);
        setComps(Array.isArray(c) ? c : c?.results || c?.competitors || []);
      } catch {}
    } catch (e: any) { setErr(e.message); } finally { setLoading(false); }
  };

  return (
    <div className="px-6 lg:px-10 py-8 max-w-6xl">
      <h1 className="text-3xl font-bold"><GradientText>Market Gap Finder</GradientText></h1>
      <GlassCard className="mt-6 flex gap-2 items-center">
        <input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="Domain" className="flex-1 bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm" />
        <input type="number" min={1} max={100} value={topK} onChange={(e) => setTopK(Number(e.target.value) || 10)} className="w-20 bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm" />
        <PrimaryButton onClick={run}><Target className="w-4 h-4" /> Analyze Gaps</PrimaryButton>
      </GlassCard>
      {err && <div className="mt-4"><ErrorBanner message={err} onRetry={run} /></div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-6">
        {loading && Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        {gaps?.map((g: any, i) => (
          <GlassCard key={i}>
            <div className="text-xs uppercase tracking-wider text-emerald-300/80">Opportunity</div>
            <div className="text-sm font-semibold text-slate-100 mt-1">{g.title || g.opportunity || `Gap ${i + 1}`}</div>
            <p className="text-xs text-slate-400 mt-2">{g.description || "—"}</p>
            <div className="flex gap-2 mt-3 flex-wrap">
              {g.confidence !== undefined && <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">Confidence {Math.round(g.confidence * 100)}%</span>}
              {g.competition_score !== undefined && <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">Competition {Math.round(g.competition_score * 100)}%</span>}
              {(g.signals || g.tags || []).map((t: string, j: number) => <span key={j} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">{t}</span>)}
            </div>
          </GlassCard>
        ))}
      </div>

      {comps.length > 0 && (
        <GlassCard className="mt-6">
          <div className="text-xs uppercase tracking-wider text-violet-300 mb-4">Competitor Sonar</div>
          <div className="flex justify-center">
            <svg viewBox="-110 -110 220 220" width="320" height="320">
              {[1, 2, 3, 4].map((r) => <circle key={r} r={r * 25} fill="none" stroke="rgba(139,92,246,0.15)" strokeWidth="1" />)}
              <line x1="-100" y1="0" x2="100" y2="0" stroke="rgba(139,92,246,0.1)" />
              <line x1="0" y1="-100" x2="0" y2="100" stroke="rgba(139,92,246,0.1)" />
              <g style={{ transformOrigin: "0 0", animation: "vm-radar-sweep 4s linear infinite" }}>
                <path d="M 0 0 L 100 0 A 100 100 0 0 1 70.7 70.7 Z" fill="url(#sweep)" opacity="0.5" />
                <defs><linearGradient id="sweep"><stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.6" /><stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" /></linearGradient></defs>
              </g>
              {comps.slice(0, 12).map((c: any, i) => {
                const sim = Number(c.similarity ?? c.score ?? 0.5);
                const ang = (i / 12) * Math.PI * 2;
                const dist = (1 - sim) * 90 + 10;
                const x = Math.cos(ang) * dist;
                const y = Math.sin(ang) * dist;
                return <g key={i}><circle cx={x} cy={y} r="3" fill="#a78bfa" style={{ filter: "drop-shadow(0 0 6px #a78bfa)" }}><animate attributeName="r" values="3;5;3" dur="2s" repeatCount="indefinite" /></circle></g>;
              })}
            </svg>
          </div>
        </GlassCard>
      )}
    </div>
  );
}