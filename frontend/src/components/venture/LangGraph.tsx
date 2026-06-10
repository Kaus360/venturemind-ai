import { Check, X } from "lucide-react";

export type NodeStatus = "idle" | "active" | "done" | "failed";
export type LGNode = { id: string; label: string; x: number; y: number; status: NodeStatus };

export function LangGraphVisualizer({ nodes, activeIndex }: { nodes: LGNode[]; activeIndex: number }) {
  return (
    <svg viewBox="0 0 900 220" className="w-full h-[260px]">
      <defs>
        <linearGradient id="edge-active" x1="0" x2="1">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>
      {nodes.slice(0, -1).map((n, i) => {
        const next = nodes[i + 1];
        const reached = i < activeIndex;
        return (
          <g key={`e-${i}`}>
            <line x1={n.x} y1={n.y} x2={next.x} y2={next.y} stroke="rgba(99,102,241,0.15)" strokeWidth="2" />
            <line
              x1={n.x} y1={n.y} x2={next.x} y2={next.y}
              stroke="url(#edge-active)" strokeWidth="2"
              strokeDasharray="600"
              strokeDashoffset={reached ? 0 : 600}
              style={{ transition: "stroke-dashoffset 0.8s ease-out" }}
              className={i === activeIndex - 1 ? "vm-dash-flow" : ""}
              filter="url(#glow)"
            />
          </g>
        );
      })}
      {nodes.map((n) => {
        const fill =
          n.status === "done" ? "#10b981" :
          n.status === "active" ? "#6366f1" :
          n.status === "failed" ? "#f43f5e" : "#1e293b";
        const stroke =
          n.status === "done" ? "#34d399" :
          n.status === "active" ? "#a5b4fc" :
          n.status === "failed" ? "#fb7185" : "#334155";
        return (
          <g key={n.id} transform={`translate(${n.x},${n.y})`}>
            {n.status === "active" && (
              <circle r="26" fill="none" stroke="#6366f1" strokeWidth="2" opacity="0.6">
                <animate attributeName="r" from="20" to="34" dur="1.6s" repeatCount="indefinite" />
                <animate attributeName="opacity" from="0.8" to="0" dur="1.6s" repeatCount="indefinite" />
              </circle>
            )}
            <circle r="18" fill={fill} stroke={stroke} strokeWidth="2" filter={n.status === "active" ? "url(#glow)" : undefined} />
            {n.status === "active" && (
              <circle r="22" fill="none" stroke="#a5b4fc" strokeWidth="1.5" strokeDasharray="8 4" opacity="0.7">
                <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="2s" repeatCount="indefinite" />
              </circle>
            )}
            <foreignObject x="-10" y="-10" width="20" height="20">
              <div className="w-5 h-5 flex items-center justify-center text-white">
                {n.status === "done" && <Check className="w-3.5 h-3.5" />}
                {n.status === "failed" && <X className="w-3.5 h-3.5" />}
              </div>
            </foreignObject>
            <text x="0" y="38" textAnchor="middle" fontSize="10" fill="#cbd5e1" className="font-medium">{n.label}</text>
          </g>
        );
      })}
    </svg>
  );
}