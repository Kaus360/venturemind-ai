import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Plus, RefreshCw, X } from "lucide-react";
import { api } from "@/lib/api";
import { useVenture } from "@/context/VentureContext";
import { GlassCard, ScanCard, ErrorBanner, PrimaryButton, SecondaryButton, GradientText } from "@/components/venture/primitives";
import { toast } from "sonner";

export const Route = createFileRoute("/wizard/step-3")({ component: Step3 });

type Solution = {
  startup_idea: string;
  value_proposition: string;
  target_audience: string;
  innovation_summary: string;
  key_features: string[];
};

function Step3() {
  const navigate = useNavigate();
  const { state, update } = useVenture();
  const [sol, setSol] = useState<Solution | null>(state.solution as Solution | null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const generate = async () => {
    if (!state.problemStatement) { toast.error("Go back and pick a problem first"); return; }
    setLoading(true); setErr(null);
    try {
      const r: any = await api.generateSolution(state.problemStatement);
      const norm: Solution = {
        startup_idea: r.startup_idea || r.idea || "",
        value_proposition: r.value_proposition || r.value_prop || "",
        target_audience: r.target_audience || r.audience || state.audienceOverride || "",
        innovation_summary: r.innovation_summary || r.summary || "",
        key_features: r.key_features || r.features || [],
      };
      setSol(norm);
      update({ solution: norm, startupIdea: norm.startup_idea });
    } catch (e: any) { setErr(e.message); toast.error(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { if (!sol) generate(); /* eslint-disable-next-line */ }, []);

  const setField = (k: keyof Solution, v: any) => {
    if (!sol) return;
    const next = { ...sol, [k]: v };
    setSol(next);
    update({ solution: next, startupIdea: next.startup_idea });
  };
  const addFeature = () => sol && setField("key_features", [...sol.key_features, "New feature"]);
  const removeFeature = (i: number) => sol && setField("key_features", sol.key_features.filter((_, j) => j !== i));
  const updateFeature = (i: number, v: string) => sol && setField("key_features", sol.key_features.map((f, j) => j === i ? v : f));

  return (
    <div className="max-w-6xl">
      <h2 className="text-3xl font-bold"><GradientText>Solution Editor</GradientText></h2>
      <p className="text-sm text-slate-400 mt-2">Edit the generated solution before validation.</p>

      {loading && <div className="mt-6"><ScanCard label="Solution Generator Agent structuring concepts…" /></div>}
      {err && <div className="mt-6"><ErrorBanner message={err} onRetry={generate} /></div>}

      {sol && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6">
          <GlassCard className="space-y-4">
            {(["startup_idea", "value_proposition", "target_audience", "innovation_summary"] as const).map((k) => (
              <div key={k}>
                <label className="text-xs uppercase tracking-wider text-slate-500">{k.replace(/_/g, " ")}</label>
                {k === "innovation_summary" || k === "value_proposition" ? (
                  <textarea value={(sol as any)[k]} onChange={(e) => setField(k, e.target.value)} rows={3}
                    className="mt-1 w-full bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/20" />
                ) : (
                  <input value={(sol as any)[k]} onChange={(e) => setField(k, e.target.value)}
                    className="mt-1 w-full bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500/60 focus:ring-2 focus:ring-indigo-500/20" />
                )}
              </div>
            ))}
          </GlassCard>
          <GlassCard>
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs uppercase tracking-wider text-slate-500">Key Features</label>
              <button onClick={addFeature} className="text-xs inline-flex items-center gap-1 px-2 py-1 rounded bg-indigo-500/20 text-indigo-200 border border-indigo-500/40 hover:scale-[1.03] transition">
                <Plus className="w-3 h-3" /> Add
              </button>
            </div>
            <div className="space-y-2 max-h-[420px] overflow-y-auto vm-scrollbar pr-1">
              {sol.key_features.length === 0 && <div className="text-xs text-slate-500">No features yet.</div>}
              {sol.key_features.map((f, i) => (
                <div key={i} className="flex gap-2">
                  <input value={f} onChange={(e) => updateFeature(i, e.target.value)}
                    className="flex-1 bg-slate-900/70 border border-slate-700 rounded-md px-3 py-1.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500/60" />
                  <button onClick={() => removeFeature(i)} className="p-1.5 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 transition">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      )}

      <div className="flex items-center justify-between mt-6">
        <div className="flex gap-2">
          <Link to="/wizard/step-2"><SecondaryButton><ArrowLeft className="w-4 h-4" /> Back</SecondaryButton></Link>
          <SecondaryButton onClick={generate} disabled={loading}><RefreshCw className="w-4 h-4" /> Re-generate</SecondaryButton>
        </div>
        <PrimaryButton disabled={!sol} onClick={() => navigate({ to: "/wizard/step-4" })}>Proceed to Validation <ArrowRight className="w-4 h-4" /></PrimaryButton>
      </div>
    </div>
  );
}