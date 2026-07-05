export default function GaugeRing({ value, max = 100, color, size = 80, label }: {
  value: number; max?: number; color: string; size?: number; label?: string;
}) {
  const r = (size - 10) / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(value / max, 1);
  const dash = pct * circ;

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
        <circle
          cx={size/2} cy={size/2} r={r} fill="none"
          stroke={color} strokeWidth="8"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 1s ease-out" }}
        />
        <text x={size/2} y={size/2} textAnchor="middle" dominantBaseline="middle"
          style={{ transform: "rotate(90deg)", transformOrigin: `${size/2}px ${size/2}px`, fill: color, fontSize: size < 70 ? 12 : 15, fontWeight: 700, fontFamily: "Inter" }}>
          {Math.round(value)}
        </text>
      </svg>
      {label && <p className="text-xs text-center" style={{ color: "var(--text-muted)", maxWidth: size }}>{label}</p>}
    </div>
  );
}
