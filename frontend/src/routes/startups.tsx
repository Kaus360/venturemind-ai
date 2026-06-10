import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Search, Plus, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { GlassCard, ErrorBanner, PrimaryButton, SecondaryButton, GradientText, SkeletonCard } from "@/components/venture/primitives";
import { ConfirmModal } from "@/components/venture/ConfirmModal";
import { toast } from "sonner";

export const Route = createFileRoute("/startups")({
  head: () => ({ meta: [{ title: "Startup Explorer · VentureMind AI" }] }),
  component: Startups,
});

function Startups() {
  const [q, setQ] = useState("");
  const [domain, setDomain] = useState("");
  const [topK, setTopK] = useState(10);
  const [items, setItems] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [delTarget, setDelTarget] = useState<any | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [form, setForm] = useState({ title: "", domain: "", description: "", target_users: "" });

  const search = async () => {
    setLoading(true); setErr(null);
    try {
      const r: any = await api.retrievalStartups(q, topK, domain || undefined);
      setItems(Array.isArray(r) ? r : r?.results || r?.items || []);
    } catch (e: any) { setErr(e.message); } finally { setLoading(false); }
  };
  const remove = async () => {
    if (!delTarget) return;
    try { await api.deleteStartup(delTarget.id); toast.success("Removed"); setItems((it) => (it || []).filter((x) => x !== delTarget)); }
    catch (e: any) { toast.error(e.message); }
    setDelTarget(null);
  };
  const add = async () => {
    try { await api.embedStartup(form); toast.success("Indexed"); setAddOpen(false); search(); }
    catch (e: any) { toast.error(e.message); }
  };

  return (
    <div className="px-6 lg:px-10 py-8 max-w-6xl">
      <h1 className="text-3xl font-bold"><GradientText>Startup Explorer</GradientText></h1>
      <GlassCard className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-3">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Query" className="md:col-span-2 bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm" />
        <input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="Domain filter" className="bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm" />
        <div className="flex items-center gap-2">
          <input type="range" min={1} max={100} value={topK} onChange={(e) => setTopK(Number(e.target.value))} className="flex-1" />
          <span className="text-xs text-slate-400 w-8">{topK}</span>
        </div>
        <div className="md:col-span-4 flex justify-between">
          <SecondaryButton onClick={() => setAddOpen(true)}><Plus className="w-4 h-4" /> Add Startup to Index</SecondaryButton>
          <PrimaryButton onClick={search}><Search className="w-4 h-4" /> Search</PrimaryButton>
        </div>
      </GlassCard>

      {err && <div className="mt-4"><ErrorBanner message={err} onRetry={search} /></div>}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
        {loading && Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        {items?.map((it, i) => (
          <GlassCard key={i} className="relative group">
            <button onClick={() => setDelTarget(it)} className="absolute top-3 right-3 p-1.5 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 opacity-0 group-hover:opacity-100 transition">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
            <div className="text-xs uppercase tracking-wider text-indigo-300/80">{it.domain || "—"}</div>
            <div className="text-sm font-semibold text-slate-100 mt-1">{it.title || it.startup_idea || "Untitled"}</div>
            <p className="text-xs text-slate-400 mt-2 line-clamp-3">{it.description || "—"}</p>
            {(it.similarity ?? it.score) !== undefined && (
              <div className="mt-3 inline-block text-[11px] px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-300 border border-violet-500/30">
                {Math.round((it.similarity ?? it.score) * 100)}% match
              </div>
            )}
          </GlassCard>
        ))}
        {!loading && items && items.length === 0 && <div className="text-sm text-slate-500 md:col-span-2 lg:col-span-3">No results.</div>}
      </div>

      <ConfirmModal open={!!delTarget} title="Remove startup?" description="This will delete it from the index." destructive confirmLabel="Remove" onConfirm={remove} onClose={() => setDelTarget(null)} />
      <ConfirmModal open={addOpen} title="Add Startup to Index" confirmLabel="Submit" onConfirm={add} onClose={() => setAddOpen(false)}>
        <div className="space-y-2">
          {(["title", "domain", "description", "target_users"] as const).map((k) => (
            <input key={k} placeholder={k.replace("_", " ")} value={(form as any)[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })}
              className="w-full bg-slate-900/70 border border-slate-700 rounded-md px-3 py-2 text-sm" />
          ))}
        </div>
      </ConfirmModal>
    </div>
  );
}