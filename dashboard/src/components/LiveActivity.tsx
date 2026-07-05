import { useEffect, useState } from "react";
import { fetchActivity, formatRp } from "../api/client";

export default function LiveActivity() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchActivity().then(r => setData(r.data || [])).finally(() => setLoading(false));
  }, []);

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>⚡ Live Activity</h3>
        <span className="text-xs px-2 py-1 rounded-full animate-pulse"
          style={{ background: "#10b98120", color: "#10b981" }}>● Live</span>
      </div>
      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {loading ? (
          [1,2,3,4].map(i => <div key={i} className="skeleton h-12 rounded-xl" />)
        ) : data.map((item, i) => (
          <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all hover:scale-[1.01]"
            style={{ background: "rgba(255,255,255,0.03)" }}>
            <span className="text-base shrink-0">{item.emoji}</span>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate" style={{ color: "var(--text-primary)" }}>{item.memo}</p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>{item.akun} · {item.tanggal_fmt}</p>
            </div>
            <span className={`text-xs font-bold shrink-0 ${item.tipe === "income" ? "text-emerald-400" : item.tipe === "transfer" ? "text-blue-400" : "text-red-400"}`}>
              {item.tipe === "expense" ? "-" : "+"}{formatRp(item.jumlah, true)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
