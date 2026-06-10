import { useEffect, useState } from "react";

export function NeuralBackground() {
  const [paths, setPaths] = useState<string[]>([]);
  useEffect(() => {
    const rand = (a: number, b: number) => a + Math.random() * (b - a);
    const arr = Array.from({ length: 6 }, () => {
      const x1 = rand(0, 400);
      const y1 = rand(0, 300);
      const x2 = rand(600, 1000);
      const y2 = rand(50, 300);
      const cx = rand(300, 700);
      const cy = rand(-100, 400);
      return `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`;
    });
    setPaths(arr);
  }, []);
  return (
    <svg viewBox="0 0 1000 400" className="absolute inset-0 w-full h-full pointer-events-none opacity-40" preserveAspectRatio="none">
      <defs>
        <linearGradient id="vmline" x1="0" x2="1">
          <stop offset="0%" stopColor="#6366f1" stopOpacity="0" />
          <stop offset="50%" stopColor="#8b5cf6" stopOpacity="0.7" />
          <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
        </linearGradient>
      </defs>
      {paths.map((d, i) => (
        <path key={i} d={d} fill="none" stroke="url(#vmline)" strokeWidth="1.2" strokeDasharray="4 8">
          <animate attributeName="stroke-dashoffset" from="0" to="-120" dur={`${8 + i * 2}s`} repeatCount="indefinite" />
        </path>
      ))}
    </svg>
  );
}

export function ParticleField({ count = 30 }: { count?: number }) {
  const particles = Array.from({ length: count }, (_, i) => {
    const left = Math.random() * 100;
    const drift = Math.random() * 80 - 40;
    const dur = 10 + Math.random() * 18;
    const delay = Math.random() * 12;
    const size = 1.5 + Math.random() * 2.5;
    const hue = Math.random() > 0.5 ? "#818cf8" : "#22d3ee";
    return (
      <span
        key={i}
        className="absolute bottom-0 rounded-full"
        style={{
          left: `${left}%`,
          width: size,
          height: size,
          background: hue,
          boxShadow: `0 0 8px ${hue}`,
          animation: `vm-float-up ${dur}s linear ${delay}s infinite`,
          ["--drift" as any]: `${drift}px`,
        }}
      />
    );
  });
  return <div className="absolute inset-0 overflow-hidden pointer-events-none">{particles}</div>;
}