interface Props {
  title: string;
  value: string;
  sub?: string;
  icon: React.ReactNode;
  color?: "green" | "red" | "blue" | "purple" | "orange";
  trend?: "up" | "down" | "neutral";
}

const colorMap = {
  green: { bg: "bg-emerald-50", icon: "bg-emerald-500", text: "text-emerald-600" },
  red: { bg: "bg-red-50", icon: "bg-red-500", text: "text-red-600" },
  blue: { bg: "bg-blue-50", icon: "bg-blue-500", text: "text-blue-600" },
  purple: { bg: "bg-violet-50", icon: "bg-violet-500", text: "text-violet-600" },
  orange: { bg: "bg-orange-50", icon: "bg-orange-500", text: "text-orange-600" },
};

export default function StatCard({ title, value, sub, icon, color = "blue" }: Props) {
  const c = colorMap[color];
  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{title}</p>
          <p className="text-2xl font-bold text-slate-800 mt-1 leading-tight">{value}</p>
          {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
        </div>
        <div className={`p-2.5 rounded-xl ${c.bg}`}>
          <span className={c.text}>{icon}</span>
        </div>
      </div>
    </div>
  );
}
