import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { api, getApiBase, setApiBase } from "@/lib/api";
import { GlassCard, PrimaryButton, SecondaryButton, GradientText, ErrorBanner } from "@/components/venture/primitives";
import { ConfirmModal } from "@/components/venture/ConfirmModal";
import { toast } from "sonner";

export const Route = createFileRoute("/admin")({
  head: () => ({ meta: [{ title: "Admin · VentureMind AI" }] }),
  component: Admin,
});

function Admin() {
  const [health, setHealth] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [base, setBase] = useState(getApiBase());
  const [confirm1, setConfirm1] = useState(false);
  const [confirm2, setConfirm2] = useState(false);

  const load = async () => {
    try { setHealth(await api.health()); setErr(null); }
    catch (e: any) { setErr(e.message); setHealth(null); }
  };
  useEffect(() => { load(); }, []);

  const pg = health?.postgres || health?.services?.postgres || {};
  const qd = health?.qdrant || health?.services?.qdrant || {};

  return (
    <div className="px-6 lg:px-10 py-8 max-w-5xl">
      <h1 className="text-3xl font-bold"><GradientText>Admin Control Room</GradientText></h1>

      <GlassCard className="mt-6">
        <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">API Base URL</div>
        <div className="flex gap-2">
          <input value={base} onChange={(e) => setBase(e.target.value)} className="flex-1 bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm font-mono" />
          <PrimaryButton onClick={() => { setApiBase(base); toast.success("API base saved"); load(); }}>Save</PrimaryButton>
        </div>
        <div className="text-[11px] text-slate-500 mt-2">Persisted to localStorage. Default: http://localhost:8000</div>
      </GlassCard>

      {err && <div className="mt-4"><ErrorBanner message={err} onRetry={load} /></div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <GlassCard>
          <div className="text-xs uppercase tracking-wider text-emerald-300 mb-2">PostgreSQL</div>
          <pre className="text-xs text-slate-300 bg-slate-950/60 rounded p-3 overflow-auto vm-scrollbar">{JSON.stringify(pg, null, 2)}</pre>
        </GlassCard>
        <GlassCard>
          <div className="text-xs uppercase tracking-wider text-violet-300 mb-2">Qdrant</div>
          <pre className="text-xs text-slate-300 bg-slate-950/60 rounded p-3 overflow-auto vm-scrollbar">{JSON.stringify(qd, null, 2)}</pre>
        </GlassCard>
      </div>

      <div className="flex gap-2 mt-6">
        <PrimaryButton onClick={async () => { try { await api.bootstrap(); toast.success("Collections bootstrapped"); } catch (e: any) { toast.error(e.message); } }}>Bootstrap Collections</PrimaryButton>
        <SecondaryButton className="!bg-rose-500/10 !border-rose-500/40 !text-rose-200 hover:!bg-rose-500/20" onClick={() => setConfirm1(true)}>Graceful Shutdown</SecondaryButton>
      </div>

      <ConfirmModal open={confirm1} title="Confirm shutdown?" description="This will gracefully stop backend services." destructive confirmLabel="Yes, continue" onConfirm={() => { setConfirm1(false); setConfirm2(true); }} onClose={() => setConfirm1(false)} />
      <ConfirmModal open={confirm2} title="Are you absolutely sure?" description="This action is irreversible." destructive confirmLabel="Shutdown now"
        onConfirm={async () => { setConfirm2(false); try { await api.shutdown(); toast.success("Shutdown initiated"); } catch (e: any) { toast.error(e.message); } }}
        onClose={() => setConfirm2(false)} />
    </div>
  );
}