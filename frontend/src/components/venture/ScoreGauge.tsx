import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from "recharts";

export function ScoreGauge({
  value,
  max = 100,
  label,
  color = "#6366f1",
  size = 140,
  centerText,
}: {
  value: number;
  max?: number;
  label?: string;
  color?: string;
  size?: number;
  centerText?: string;
}) {
  const pct = Math.max(0, Math.min(max, value));
  const data = [{ name: "score", value: pct, fill: color }];
  return (
    <div className="relative inline-flex flex-col items-center justify-center" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart innerRadius="75%" outerRadius="100%" data={data} startAngle={90} endAngle={-270}>
          <PolarAngleAxis type="number" domain={[0, max]} tick={false} />
          <RadialBar background={{ fill: "rgba(148,163,184,0.12)" }} dataKey="value" cornerRadius={10} animationDuration={1400} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="text-2xl font-bold text-white">{centerText ?? Math.round(pct)}</div>
        {label && <div className="text-[10px] uppercase tracking-wider text-slate-400 mt-0.5 px-2 text-center">{label}</div>}
      </div>
    </div>
  );
}