import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useState } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { useVenture } from "@/context/VentureContext";
import { GlassCard, PrimaryButton, SecondaryButton, GradientText } from "@/components/venture/primitives";

export const Route = createFileRoute("/wizard/step-2")({ component: Step2 });

function Step2() {
  const navigate = useNavigate();
  const { state, update } = useVenture();
  const [statement, setStatement] = useState(state.problemStatement);
  const [focus, setFocus] = useState(state.customFocus);
  const [audience, setAudience] = useState(state.audienceOverride);

  const proceed = () => {
    update({ problemStatement: statement, customFocus: focus, audienceOverride: audience });
    navigate({ to: "/wizard/step-3" });
  };

  return (
    <div className="max-w-3xl">
      <h2 className="text-3xl font-bold"><GradientText>Problem Directives</GradientText></h2>
      <p className="text-sm text-slate-400 mt-2">Refine the problem statement and add focus directives before the Solution Generator runs.</p>

      <GlassCard className="mt-6">
        <label className="text-xs uppercase tracking-wider text-slate-500">Selected Problem Statement</label>
        <textarea
          value={statement}
          onChange={(e) => setStatement(e.target.value)}
          rows={4}
          className="mt-2 w-full bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/20"
        />
      </GlassCard>

      <GlassCard className="mt-4">
        <label className="text-xs uppercase tracking-wider text-slate-500">Custom Focus Prompt</label>
        <textarea
          value={focus}
          onChange={(e) => setFocus(e.target.value)}
          rows={3}
          placeholder="e.g., Focus on B2B SaaS, avoid hardware, prioritize regulated markets…"
          className="mt-2 w-full bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/20"
        />
      </GlassCard>

      <GlassCard className="mt-4">
        <label className="text-xs uppercase tracking-wider text-slate-500">Target Audience Override</label>
        <input
          value={audience}
          onChange={(e) => setAudience(e.target.value)}
          placeholder="e.g., Mid-market healthcare CIOs"
          className="mt-2 w-full bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/20"
        />
      </GlassCard>

      <div className="flex items-center justify-between mt-6">
        <Link to="/wizard/step-1"><SecondaryButton><ArrowLeft className="w-4 h-4" /> Back to Problems</SecondaryButton></Link>
        <PrimaryButton onClick={proceed}>Generate Startup Solution <ArrowRight className="w-4 h-4" /></PrimaryButton>
      </div>
    </div>
  );
}