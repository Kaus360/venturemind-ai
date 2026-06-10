import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Download, FileText, Database } from "lucide-react";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { api } from "@/lib/api";
import { useVenture } from "@/context/VentureContext";
import { GlassCard, PrimaryButton, SecondaryButton, GradientText, VerdictBadge } from "@/components/venture/primitives";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";

export const Route = createFileRoute("/report")({
  head: () => ({ meta: [{ title: "Venture Report · VentureMind AI" }] }),
  component: Report,
});

const TABS = ["Executive Summary", "Metrics & Validation", "Competitor Landscape", "Risk Matrix", "Execution Roadmap"] as const;

function Report() {
  const { state } = useVenture();
  const [tab, setTab] = useState<(typeof TABS)[number]>("Executive Summary");

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "venture-report.json"; a.click();
    URL.revokeObjectURL(url);
  };
  const indexDb = async () => {
    try {
      await api.embedStartup({
        title: state.startupIdea, domain: state.domain,
        description: state.solution?.innovation_summary || "",
        target_users: state.solution?.target_audience || "",
      });
      toast.success("Indexed in database");
    } catch (e: any) { toast.error(e.message); }
  };

  const v = state.validation || {};
  const radarData = [
    { metric: "Innovation", value: Number(v.innovation_score ?? 0) },
    { metric: "Demand", value: Number(v.market_demand ?? 0) },
    { metric: "Feasibility", value: Number(v.feasibility ?? 0) },
    { metric: "Inv. Competition", value: 100 - Number(v.competition_risk ?? 50) },
    { metric: "Viability", value: Number(state.criticFeedback?.viability_score ?? 0) },
  ];

  return (
    <div className="px-6 lg:px-10 py-8 max-w-6xl">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold"><GradientText>Consolidated Venture Report</GradientText></h1>
          <p className="text-sm text-slate-400 mt-2">{state.domain || "—"} · {state.startupIdea || "Untitled venture"}</p>
        </div>
        <div className="flex gap-2 vm-no-print">
          <SecondaryButton onClick={() => window.print()}><FileText className="w-4 h-4" /> Export PDF</SecondaryButton>
          <SecondaryButton onClick={exportJSON}><Download className="w-4 h-4" /> Export JSON</SecondaryButton>
          <PrimaryButton onClick={indexDb}><Database className="w-4 h-4" /> Index in Database</PrimaryButton>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-1 border-b border-slate-800 vm-no-print">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 text-sm transition relative ${tab === t ? "text-indigo-300" : "text-slate-400 hover:text-slate-200"}`}>
            {t}
            {tab === t && <motion.div layoutId="tab-underline" className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-indigo-500 to-violet-500" />}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div key={tab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }} className="mt-6">
          {tab === "Executive Summary" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <GlassCard><div className="text-xs uppercase tracking-wider text-indigo-300 mb-2">Idea</div><p className="text-sm text-slate-200">{state.startupIdea || "—"}</p></GlassCard>
              <GlassCard><div className="text-xs uppercase tracking-wider text-indigo-300 mb-2">Value Proposition</div><p className="text-sm text-slate-200">{state.solution?.value_proposition || "—"}</p></GlassCard>
              <GlassCard><div className="text-xs uppercase tracking-wider text-indigo-300 mb-2">Problem</div><p className="text-sm text-slate-200">{state.problemStatement || "—"}</p></GlassCard>
              <GlassCard><div className="text-xs uppercase tracking-wider text-indigo-300 mb-2">Verdict</div><div className="flex items-center gap-3"><VerdictBadge verdict={state.criticFeedback?.verdict} /><span className="text-xs text-slate-500">Viability {state.criticFeedback?.viability_score ?? "—"}</span></div></GlassCard>
            </div>
          )}
          {tab === "Metrics & Validation" && (
            <GlassCard>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="rgba(148,163,184,0.2)" />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: "#cbd5e1", fontSize: 11 }} />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: "#475569", fontSize: 10 }} />
                    <Radar dataKey="value" stroke="#8b5cf6" fill="#6366f1" fillOpacity={0.4} animationDuration={1400} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>
          )}
          {tab === "Competitor Landscape" && (
            <GlassCard><pre className="text-xs text-slate-300 overflow-auto vm-scrollbar">{JSON.stringify(state.competitorData, null, 2) || "—"}</pre></GlassCard>
          )}
          {tab === "Risk Matrix" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <GlassCard><div className="text-xs uppercase tracking-wider text-rose-300 mb-2">Critical Flaws</div><ul className="space-y-1.5">{(state.criticFeedback?.critical_flaws || []).map((f: string, i: number) => <li key={i} className="text-sm text-slate-300">▸ {f}</li>)}</ul></GlassCard>
              <GlassCard><div className="text-xs uppercase tracking-wider text-amber-300 mb-2">Unrealistic Assumptions</div><ul className="space-y-1.5">{(state.criticFeedback?.unrealistic_assumptions || []).map((f: string, i: number) => <li key={i} className="text-sm text-slate-300">▸ {f}</li>)}</ul></GlassCard>
            </div>
          )}
          {tab === "Execution Roadmap" && (
            <GlassCard><pre className="text-xs text-slate-300 overflow-auto vm-scrollbar">{JSON.stringify(state.roadmap, null, 2) || "—"}</pre></GlassCard>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}