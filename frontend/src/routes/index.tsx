import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Rocket, Compass, FileText, TrendingUp, Activity, Brain } from "lucide-react";
import { api } from "@/lib/api";
import { useVenture } from "@/context/VentureContext";
import { GlassCard, GradientText, VerdictBadge, MotionFadeUp, ErrorBanner, SkeletonCard, GlowOrb, CountUp } from "@/components/venture/primitives";
import { NeuralBackground, ParticleField } from "@/components/venture/NeuralBackground";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard · VentureMind AI" },
      { name: "description", content: "Autonomous Venture Intelligence OS — discover, validate, and roadmap startups end-to-end." },
      { property: "og:title", content: "VentureMind AI Dashboard" },
      { property: "og:description", content: "Autonomous Venture Intelligence OS" },
    ],
  }),
  component: Dashboard,
});

const HERO_WORDS = ["Autonomous", "Venture", "Intelligence", "OS"];

function Dashboard() {
  const navigate = useNavigate();
  const { loadFromMemory } = useVenture();
  const [items, setItems] = useState<any[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true); setErr(null);
    try {
      const r: any = await api.memoryContext();
      const arr = Array.isArray(r) ? r : r?.records || r?.history || r?.items || [];
      setItems(arr);
    } catch (e: any) {
      setErr(e.message || "Failed to load memory history");
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const topGrade = (() => {
    if (!items || items.length === 0) return "—";
    const grades = items.map((x) => x?.scores?.grade || x?.grade).filter(Boolean);
    return grades[0] || "—";
  })();

  return (
    <div className="relative">
      {/* Hero */}
      <section className="relative overflow-hidden px-6 lg:px-10 pt-12 pb-16">
        <NeuralBackground />
        <ParticleField count={36} />
        <GlowOrb color="indigo" className="w-[500px] h-[500px] -top-32 -left-32" />
        <GlowOrb color="violet" className="w-[400px] h-[400px] top-10 right-10" />

        <div className="relative max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full vm-glass text-xs text-indigo-300 mb-6"
          >
            <Brain className="w-3.5 h-3.5" /> Powered by multi-agent reasoning
          </motion.div>
          <h1 className="text-5xl lg:text-7xl font-bold tracking-tight leading-[1.05]">
            {HERO_WORDS.map((w, i) => (
              <motion.span
                key={w}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 + i * 0.12 }}
                className="inline-block mr-3"
              >
                {i < 3 ? <span className="text-slate-100">{w}</span> : <GradientText className="text-5xl lg:text-7xl">{w}</GradientText>}
              </motion.span>
            ))}
          </h1>
          <motion.p
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }}
            className="mt-6 text-lg text-slate-400 max-w-2xl"
          >
            Discover problems, generate solutions, validate viability, scout competitors, and ship a roadmap — orchestrated by autonomous agents over a Qdrant-backed knowledge graph.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.85 }}
            className="mt-8 flex flex-wrap gap-3"
          >
            <Link to="/autopilot" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-xl shadow-indigo-500/40 hover:shadow-indigo-500/60 transition-all hover:scale-[1.03]">
              <Rocket className="w-4 h-4" /> Launch Autonomous Autopilot
            </Link>
            <Link to="/wizard/step-1" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium vm-glass text-slate-200 hover:bg-slate-800/60 transition-all hover:scale-[1.03]">
              <Compass className="w-4 h-4" /> Step-by-Step Venture Wizard
            </Link>
          </motion.div>
        </div>

        {/* Stats row */}
        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-4 mt-12 max-w-4xl">
          {[
            { label: "Total Analyses", value: items?.length ?? 0, icon: FileText, color: "indigo" as const },
            { label: "Highest Viability Grade", value: topGrade, icon: TrendingUp, color: "violet" as const, raw: true },
            { label: "System Telemetry", value: "Live", icon: Activity, color: "emerald" as const, raw: true },
          ].map((s, i) => {
            const Icon = s.icon;
            return (
              <MotionFadeUp key={s.label} delay={0.9 + i * 0.1}>
                <GlassCard className="relative">
                  <GlowOrb color={s.color} className="w-32 h-32 -top-10 -right-10 opacity-50" />
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-xs uppercase tracking-wider text-slate-500">{s.label}</div>
                      <div className="text-3xl font-bold mt-2 text-white">
                        {s.raw ? s.value : <CountUp to={Number(s.value) || 0} />}
                      </div>
                    </div>
                    <Icon className="w-5 h-5 text-indigo-300" />
                  </div>
                </GlassCard>
              </MotionFadeUp>
            );
          })}
        </div>
      </section>

      {/* History */}
      <section className="px-6 lg:px-10 pb-16">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-semibold text-slate-100">Recent Venture Runs</h2>
          <button onClick={load} className="text-xs text-slate-400 hover:text-slate-200 transition">Refresh</button>
        </div>
        {err && <ErrorBanner message={err} onRetry={load} />}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
          {loading && Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
          {!loading && items && items.length === 0 && (
            <GlassCard className="md:col-span-2 lg:col-span-3 text-center text-slate-400">
              No venture runs in memory yet. Launch the Autopilot or run the Wizard to record your first analysis.
            </GlassCard>
          )}
          {items?.map((it, i) => {
            const score = it?.scores?.innovation_score ?? it?.innovation_score ?? it?.score;
            const verdict = it?.verdict ?? it?.critic_feedback?.verdict;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07, duration: 0.45 }}
              >
                <GlassCard className="hover:border-indigo-500/40 transition-all group h-full flex flex-col">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-xs uppercase tracking-wider text-indigo-300/80">{it.domain || "Domain"}</div>
                      <div className="text-sm font-semibold text-slate-100 mt-1 truncate">{it.startup_idea || it.startupIdea || "Untitled venture"}</div>
                    </div>
                    <VerdictBadge verdict={verdict} />
                  </div>
                  <p className="text-xs text-slate-400 mt-3 line-clamp-3 flex-1">{it.problem_statement || it.summary || "—"}</p>
                  <div className="flex items-center justify-between mt-4">
                    <div className="text-[11px] text-slate-500">
                      Innovation <span className="text-slate-300 font-medium">{score !== undefined ? Number(score).toFixed(0) : "—"}</span>
                    </div>
                    <button
                      onClick={() => { loadFromMemory(it); navigate({ to: "/report" }); }}
                      className="text-xs px-3 py-1.5 rounded-md bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-200 border border-indigo-500/40 transition-all group-hover:scale-[1.03]"
                    >
                      Open Report
                    </button>
                  </div>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
