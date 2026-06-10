import { motion, type HTMLMotionProps } from "framer-motion";
import { useEffect, useState, type ReactNode, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function GlassCard({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("vm-glass p-5 relative overflow-hidden", className)} {...props}>
      {children}
    </div>
  );
}

export function GradientText({ children, className }: { children: ReactNode; className?: string }) {
  return <span className={cn("vm-text-gradient font-semibold", className)}>{children}</span>;
}

export function GlowOrb({ color = "indigo", className = "" }: { color?: "indigo" | "violet" | "emerald" | "rose" | "amber"; className?: string }) {
  const map: Record<string, string> = {
    indigo: "bg-indigo-500/30",
    violet: "bg-violet-500/30",
    emerald: "bg-emerald-500/30",
    rose: "bg-rose-500/30",
    amber: "bg-amber-500/30",
  };
  return <div className={cn("absolute rounded-full blur-3xl pointer-events-none", map[color], className)} />;
}

export function VerdictBadge({ verdict }: { verdict?: string | null }) {
  const v = (verdict || "").toUpperCase();
  const cls =
    v === "PASS"
      ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/40"
      : v === "NEEDS_WORK"
      ? "bg-amber-500/15 text-amber-300 border-amber-500/40"
      : v === "FAIL"
      ? "bg-rose-500/15 text-rose-300 border-rose-500/40"
      : "bg-slate-500/15 text-slate-300 border-slate-500/40";
  return (
    <span className={cn("px-2.5 py-0.5 rounded-full text-xs font-medium border whitespace-nowrap", cls)}>
      {v || "UNKNOWN"}
    </span>
  );
}

export function CountUp({ to, duration = 1200, className, suffix = "", decimals }: { to: number; duration?: number; className?: string; suffix?: string; decimals?: number }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(to * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to, duration]);
  const d = decimals ?? (to >= 10 ? 0 : 1);
  return <span className={className}>{val.toFixed(d)}{suffix}</span>;
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="vm-glass border-rose-500/40 p-4 flex items-center justify-between gap-4">
      <div className="text-sm text-rose-200">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="text-xs px-3 py-1.5 rounded-md bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 border border-rose-500/40 transition-all hover:scale-[1.03]">
          Retry
        </button>
      )}
    </div>
  );
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn("vm-glass p-5 relative overflow-hidden", className)}>
      <div className="absolute inset-0 vm-shimmer opacity-40" />
      <div className="h-4 w-32 bg-slate-700/60 rounded mb-3" />
      <div className="h-3 w-full bg-slate-800/60 rounded mb-2" />
      <div className="h-3 w-5/6 bg-slate-800/60 rounded" />
    </div>
  );
}

export function MotionFadeUp({ children, delay = 0, className, ...props }: HTMLMotionProps<"div"> & { delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay, ease: "easeOut" }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export function ScanCard({ label }: { label: string }) {
  return (
    <div className="vm-glass p-6 flex items-center gap-4 relative overflow-hidden">
      <div className="absolute inset-0 vm-shimmer opacity-30" />
      <div className="w-10 h-10 rounded-full border-2 border-indigo-500/40 border-t-indigo-400 vm-spin-slow" />
      <div className="text-sm text-slate-300 z-10">{label}</div>
    </div>
  );
}

export function PrimaryButton({ children, className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={cn(
        "inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium",
        "bg-gradient-to-r from-indigo-500 to-violet-500 text-white",
        "shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50",
        "transition-all hover:scale-[1.03] disabled:opacity-50 disabled:hover:scale-100",
        className,
      )}
    >{children}</button>
  );
}

export function SecondaryButton({ children, className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className={cn(
        "inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium",
        "bg-slate-800/70 hover:bg-slate-700/70 text-slate-200 border border-slate-700/60",
        "transition-all hover:scale-[1.03] disabled:opacity-50 disabled:hover:scale-100",
        className,
      )}
    >{children}</button>
  );
}