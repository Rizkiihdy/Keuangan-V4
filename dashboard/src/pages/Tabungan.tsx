import { useEffect, useState } from "react";
import { fetchGoals, fetchAkun, formatRp } from "../api/client";
import { Spinner } from "../components/Spinner";

function GoalRing({ goal }: { goal: any }) {
  const pct = Math.min(goal.persen, 100);
  const size = 100;
  const r = 42;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  const color = pct >= 80 ? "#10b981" : pct >= 50 ? "#3b82f6" : pct >= 25 ? "#f59e0b" : "#6366f1";

  const icons: Record<string, string> = {
    rumah: "🏠", investasi: "📈", kendaraan: "🚗", mobil: "🚗",
    freedom: "👴", darurat: "💰", dana: "💰", travel: "✈️",
  };
  const iconKey = Object.keys(icons).find(k => goal.nama.toLowerCase().includes(k)) || "";
  const icon = icons[iconKey] || "🎯";

  return (
    <div className="card p-5 flex flex-col items-center gap-3">
      <div className="relative">
        <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="8"
            strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" style={{ transition: "stroke-dasharray 1s ease-out" }} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center" style={{ transform: "none" }}>
          <span className="text-2xl">{icon}</span>
          <span className="font-bold text-sm mt-0.5" style={{ color }}>{pct}%</span>
        </div>
      </div>
      <div className="text-center">
        <p className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>{goal.nama}</p>
        <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
          {formatRp(goal.balance, true)} / {formatRp(goal.target, true)}
        </p>
      </div>
      {goal.target > 0 && (
        <div className="w-full space-y-1">
          <div className="progress-bar">
            <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color, transition: "width 1s ease-out" }} />
          </div>
          <p className="text-xs text-center" style={{ color: "var(--text-muted)" }}>
            Sisa: {formatRp(Math.max(0, goal.target - goal.balance), true)}
          </p>
        </div>
      )}
    </div>
  );
}

export default function Tabungan() {
  const [goals, setGoals] = useState<any>(null);
  const [akun, setAkun] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchGoals(), fetchAkun()])
      .then(([g, a]) => { setGoals(g); setAkun(a); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;

  const totalTabungan = goals?.data?.reduce((s: number, g: any) => s + (g.balance || 0), 0) || 0;
  const totalTarget = goals?.data?.reduce((s: number, g: any) => s + (g.target || 0), 0) || 0;

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>🎯 Total Tabungan</p>
          <p className="font-bold text-lg" style={{ color: "#10b981" }}>{formatRp(totalTabungan, true)}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>🏆 Total Target</p>
          <p className="font-bold text-lg" style={{ color: "var(--text-primary)" }}>{formatRp(totalTarget, true)}</p>
        </div>
        <div className="card p-4 col-span-2 md:col-span-1">
          <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>📊 Progress Overall</p>
          <p className="font-bold text-lg" style={{ color: "#3b82f6" }}>
            {totalTarget > 0 ? `${Math.round(totalTabungan / totalTarget * 100)}%` : "—"}
          </p>
        </div>
      </div>

      {/* Goals Grid */}
      <div>
        <h3 className="font-bold text-sm mb-3" style={{ color: "var(--text-primary)" }}>🎯 Target Keuangan</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {goals?.data?.map((g: any) => <GoalRing key={g.nama} goal={g} />)}
          {!goals?.data?.length && <p className="col-span-4 text-sm text-center py-8" style={{ color: "var(--text-muted)" }}>Tidak ada data goals</p>}
        </div>
      </div>

      {/* Accounts */}
      <div>
        <h3 className="font-bold text-sm mb-3" style={{ color: "var(--text-primary)" }}>💳 Daftar Akun</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {akun?.data?.map((a: any) => {
            const icons: Record<string, string> = { cash: "💵", bca: "🏦", bri: "🏦", mandiri: "🏦", ovo: "💜", gopay: "💚" };
            const key = Object.keys(icons).find(k => a.nama.toLowerCase().includes(k)) || "";
            return (
              <div key={a.nama} className="card p-5 hover:scale-[1.02] transition-all">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-2xl">{icons[key] || "🏧"}</span>
                  <span className="badge text-xs" style={{
                    background: a.perubahan_bulan >= 0 ? "#10b98120" : "#ef444420",
                    color: a.perubahan_bulan >= 0 ? "#34d399" : "#f87171"
                  }}>
                    {a.perubahan_bulan >= 0 ? "↑" : "↓"} {formatRp(Math.abs(a.perubahan_bulan), true)}
                  </span>
                </div>
                <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>{a.nama}</p>
                <p className="font-bold text-lg" style={{ color: "var(--text-primary)" }}>{formatRp(a.balance, true)}</p>
                {a.cleared !== a.balance && (
                  <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Cleared: {formatRp(a.cleared, true)}</p>
                )}
              </div>
            );
          })}
          {!akun?.data?.length && <p className="col-span-3 text-sm text-center py-8" style={{ color: "var(--text-muted)" }}>Tidak ada data akun</p>}
        </div>
      </div>
    </div>
  );
}
