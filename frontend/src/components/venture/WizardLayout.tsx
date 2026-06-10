import { Link, useRouterState } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

const STEPS = [
  { n: 1, to: "/wizard/step-1" as const, label: "Domain" },
  { n: 2, to: "/wizard/step-2" as const, label: "Directives" },
  { n: 3, to: "/wizard/step-3" as const, label: "Solution" },
  { n: 4, to: "/wizard/step-4" as const, label: "Validation" },
  { n: 5, to: "/wizard/step-5" as const, label: "Competitors" },
  { n: 6, to: "/wizard/step-6" as const, label: "Red Team" },
  { n: 7, to: "/wizard/step-7" as const, label: "Roadmap" },
];
const PROGRESS = [0, 15, 30, 45, 55, 75, 88, 95];

export function WizardShell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const current = STEPS.find((s) => pathname.startsWith(s.to))?.n ?? 1;
  const progress = PROGRESS[current] ?? 0;
  return (
    <div className="px-6 lg:px-10 py-6">
      <div className="sticky top-0 z-10 bg-slate-950/70 backdrop-blur-xl -mx-6 lg:-mx-10 px-6 lg:px-10 py-4 border-b border-slate-800/60 vm-no-print">
        <div className="flex items-center justify-between mb-3">
          <div className="text-xs uppercase tracking-wider text-slate-400">Venture Wizard · Step {current} of 7</div>
          <div className="text-xs text-slate-500">{progress}%</div>
        </div>
        <div className="h-1.5 bg-slate-800/80 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-indigo-500 to-violet-500"
            initial={false}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        </div>
        <div className="hidden md:flex items-center justify-between mt-4">
          {STEPS.map((s) => (
            <Link
              key={s.n}
              to={s.to}
              className={cn(
                "flex flex-col items-center gap-1 text-[11px] transition",
                s.n === current ? "text-indigo-300" : s.n < current ? "text-emerald-400/80" : "text-slate-600 hover:text-slate-400",
              )}
            >
              <div className={cn(
                "w-6 h-6 rounded-full border flex items-center justify-center text-[10px] font-medium",
                s.n === current ? "border-indigo-400 bg-indigo-500/20 text-indigo-200 shadow-lg shadow-indigo-500/30" :
                s.n < current ? "border-emerald-500/60 bg-emerald-500/10 text-emerald-300" :
                "border-slate-700 text-slate-500",
              )}>{s.n}</div>
              <span>{s.label}</span>
            </Link>
          ))}
        </div>
      </div>
      <AnimatePresence mode="wait">
        <motion.div
          key={pathname}
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -40 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="py-8"
        >
          {children}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}