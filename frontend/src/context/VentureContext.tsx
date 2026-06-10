import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type VentureState = {
  domain: string;
  problems: any[] | null;
  selectedProblem: any | null;
  problemStatement: string;
  customFocus: string;
  audienceOverride: string;
  solution: any | null;
  startupIdea: string;
  validation: any | null;
  competitorData: any | null;
  criticFeedback: any | null;
  roadmap: any | null;
};

const initial: VentureState = {
  domain: "",
  problems: null,
  selectedProblem: null,
  problemStatement: "",
  customFocus: "",
  audienceOverride: "",
  solution: null,
  startupIdea: "",
  validation: null,
  competitorData: null,
  criticFeedback: null,
  roadmap: null,
};

type Ctx = {
  state: VentureState;
  update: (patch: Partial<VentureState>) => void;
  reset: () => void;
  loadFromMemory: (rec: any) => void;
};

const VentureContext = createContext<Ctx | null>(null);
const KEY = "vm.context";

export function VentureProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<VentureState>(() => {
    if (typeof window === "undefined") return initial;
    try {
      const raw = window.sessionStorage.getItem(KEY);
      return raw ? { ...initial, ...JSON.parse(raw) } : initial;
    } catch {
      return initial;
    }
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    try { window.sessionStorage.setItem(KEY, JSON.stringify(state)); } catch {}
  }, [state]);

  const update = (patch: Partial<VentureState>) => setState((s) => ({ ...s, ...patch }));
  const reset = () => setState(initial);
  const loadFromMemory = (rec: any) => {
    if (!rec) return;
    setState((s) => ({
      ...s,
      domain: rec.domain || s.domain,
      startupIdea: rec.startup_idea || rec.startupIdea || s.startupIdea,
      problemStatement: rec.problem_statement || s.problemStatement,
      solution: rec.solution || s.solution,
      validation: rec.validation || s.validation,
      competitorData: rec.competitors || rec.competitor_data || s.competitorData,
      criticFeedback: rec.critic_feedback || rec.red_team || s.criticFeedback,
      roadmap: rec.roadmap || s.roadmap,
    }));
  };

  return (
    <VentureContext.Provider value={{ state, update, reset, loadFromMemory }}>
      {children}
    </VentureContext.Provider>
  );
}

export function useVenture() {
  const ctx = useContext(VentureContext);
  if (!ctx) throw new Error("useVenture must be used inside VentureProvider");
  return ctx;
}