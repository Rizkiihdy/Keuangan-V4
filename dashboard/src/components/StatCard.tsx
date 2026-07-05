import { formatRp } from "../api/client";

export default function StatCard({
  title,
  value,
  subtitle,
  icon,
  color,
}: {
  title: string;
  value: number;
  subtitle?: string;
  icon: string;
  color: "emerald" | "red" | "blue" | "amber" | "slate";
}) {
  const colorMap: Record<string, { bg: string; text: string; border: string }> = {
    emerald: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-100" },
    red: { bg: "bg-red-50", text: "text-red-700", border: "border-red-100" },
    blue: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-100" },
    amber: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-100" },
    slate: { bg: "bg-slate-50", text: "text-slate-700", border: "border-slate-100" },
  };
  const c = colorMap[color];

  return (
    <div className={`bg-white rounded-2xl border ${c.border} p-5 shadow-sm`}>
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 rounded-xl ${c.bg} ${c.text} flex items-center justify-center text-xl`}>
          {icon}
        </div>
      </div>
      <p className="text-sm text-slate-500 mb-1">{title}</p>
      <p className="text-2xl font-bold text-slate-800">{formatRp(value)}</p>
      {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
    </div>
  );
}
