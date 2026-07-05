import { useEffect, useState } from "react";
import { fetchOverview, fetchCashflow, formatRp, scoreLabel, MOTIVASI } from "../api/client";
import { SkeletonCard } from "../components/Spinner";
import CountUp from "../components/CountUp";
import GaugeRing from "../components/GaugeRing";
import BarChart from "../components/BarChart";
import AIInsightPanel from "../components/AIInsightPanel";
import LiveActivity from "../components/LiveActivity";
import Notifications from "../components/Notifications";

export default function Home() {
  const [ov, setOv] = useState<any>(null);
  const [cf, setCf] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchOverview(), fetchCashflow()])
      .then(([o, c]) => { setOv(o); setCf(c); })
      .finally(() => setLoading(false));
  }, []);

  const todayIdx = new Date().getDay();
  const motivasi = MOTIVASI[todayIdx % MOTIVASI.length];

  return (
    <div className="p-4 md:p-6 space-y-5 max-w-7xl mx-auto">
      {/* NOTIFICATIONS */}
      {ov && <Notifications data={ov} />}

      {/* HERO SECTION */}
      <div className="rounded-2xl p-5 md:p-6 relative overflow-hidden"
        style={{ background: "linear-gradient(135deg, #1e3a8a 0%, #1e1b4b 50%, #0f172a 100%)", border: "1px solid rgba(99,102,241,0.2)" }}>
        <div className="absolute inset-0 pointer-events-none" style={{
          background: "radial-gradient(circle at 80% 20%, rgba(99,102,241,0.15) 0%, transparent 60%)",
        }} />
        <div className="relative">
          <p className="text-blue-200 text-sm font-medium mb-1">👋 Halo, Zee!</p>
          <p className="text-blue-100 text-xs mb-4" style={{ opacity: 0.7 }}>{new Date().toLocaleDateString("id-ID", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Total Saldo */}
            <div className="col-span-2 md:col-span-1">
              <p className="text-blue-300 text-xs mb-1">💰 Total Saldo</p>
              <p className="text-2xl md:text-3xl font-black text-white leading-tight">
                {loading ? <span className="skeleton inline-block w-32 h-8 rounded" /> :
                  <CountUp value={ov?.total_saldo || 0} prefix="Rp" />}
              </p>
            </div>
            {/* Cash Flow */}
            <div>
              <p className="text-blue-300 text-xs mb-1">📈 Cash Flow Bulan Ini</p>
              <p className={`text-xl font-bold ${!ov || ov.cashflow_bulan >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {loading ? <span className="skeleton inline-block w-24 h-7 rounded" /> :
                  <CountUp value={ov?.cashflow_bulan || 0} prefix={ov?.cashflow_bulan >= 0 ? "+Rp" : "-Rp"} />}
              </p>
            </div>
            {/* Score */}
            <div>
              <p className="text-blue-300 text-xs mb-1">🎯 Financial Score</p>
              {loading ? <span className="skeleton inline-block w-20 h-7 rounded" /> : (
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-white">{ov?.financial_score}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full font-semibold"
                    style={{ background: scoreLabel(ov?.financial_score || 0).color + "30", color: scoreLabel(ov?.financial_score || 0).color }}>
                    {scoreLabel(ov?.financial_score || 0).label}
                  </span>
                </div>
              )}
            </div>
            {/* Saving Rate */}
            <div>
              <p className="text-blue-300 text-xs mb-1">🔥 Saving Rate</p>
              <p className="text-xl font-bold text-amber-400">
                {loading ? <span className="skeleton inline-block w-16 h-7 rounded" /> :
                  `${ov?.saving_rate || 0}%`}
              </p>
            </div>
          </div>

          {/* Income / Expense row */}
          <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t" style={{ borderColor: "rgba(99,102,241,0.2)" }}>
            <div>
              <p className="text-xs text-blue-300 mb-0.5">💵 Pemasukan {ov?.bulan_ini}</p>
              <p className="font-semibold text-emerald-400 text-sm">
                {loading ? "…" : formatRp(ov?.pemasukan_bulan || 0)}
              </p>
            </div>
            <div>
              <p className="text-xs text-blue-300 mb-0.5">💸 Pengeluaran {ov?.bulan_ini}</p>
              <p className="font-semibold text-red-400 text-sm">
                {loading ? "…" : formatRp(ov?.pengeluaran_bulan || 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* FINANCIAL HEALTH */}
      <div className="card p-5">
        <h3 className="font-bold text-sm mb-4" style={{ color: "var(--text-primary)" }}>🏥 Financial Health</h3>
        {loading ? (
          <div className="flex gap-6 justify-around">
            {[1,2,3,4].map(i => <SkeletonCard key={i} h="h-24" />)}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="flex flex-col items-center">
              <GaugeRing value={ov?.financial_score || 0} color={scoreLabel(ov?.financial_score || 0).color} label="Score" />
            </div>
            <div className="flex flex-col items-center">
              <GaugeRing value={ov?.saving_rate || 0} color="#f59e0b" label="Saving Rate %" />
            </div>
            <div className="flex flex-col items-center">
              <GaugeRing value={Math.min(ov?.expense_ratio || 0, 100)} color="#ef4444" label="Expense Ratio %" />
            </div>
            <div className="col-span-2 sm:col-span-3 lg:col-span-3 space-y-2">
              {[
                { label: "Cash Flow", val: ov?.cashflow_bulan >= 0 ? "Positif ✅" : "Negatif ❌", ok: ov?.cashflow_bulan >= 0 },
                { label: "Saving Rate", val: ov?.saving_rate >= 20 ? "Excellent 🟢" : ov?.saving_rate >= 10 ? "Good 🟡" : "Perlu Ditingkatkan 🔴", ok: ov?.saving_rate >= 10 },
                { label: "Expense Ratio", val: ov?.expense_ratio <= 70 ? "Sehat 🟢" : ov?.expense_ratio <= 90 ? "Perhatikan 🟡" : "Kritis 🔴", ok: ov?.expense_ratio <= 80 },
              ].map(item => (
                <div key={item.label} className="flex justify-between items-center py-2 px-3 rounded-xl" style={{ background: "rgba(255,255,255,0.03)" }}>
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>{item.label}</span>
                  <span className="text-xs font-semibold" style={{ color: item.ok ? "#10b981" : "#f59e0b" }}>{item.val}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ACCOUNTS */}
      {!loading && ov?.akun_list?.length > 0 && (
        <div>
          <h3 className="font-bold text-sm mb-3" style={{ color: "var(--text-primary)" }}>💳 Saldo Akun</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {ov.akun_list.map((a: any) => (
              <div key={a.nama} className="card p-4 hover:scale-[1.02] transition-transform">
                <p className="text-xs mb-2 truncate" style={{ color: "var(--text-muted)" }}>
                  {a.nama.toLowerCase().includes("cash") ? "💵" :
                   a.nama.toLowerCase().includes("bca") ? "🏦" :
                   a.nama.toLowerCase().includes("invest") ? "📈" : "🏧"} {a.nama}
                </p>
                <p className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>{formatRp(a.balance, true)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CASH FLOW CHART */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>📊 Cash Flow — 6 Bulan Terakhir</h3>
          <div className="flex gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm inline-block bg-emerald-500" /> Income</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm inline-block bg-red-500" /> Expense</span>
          </div>
        </div>
        {!cf ? <SkeletonCard h="h-44" /> : (
          <BarChart data={cf.monthly} height={180} />
        )}
      </div>

      {/* SPENDING BY CATEGORY */}
      {!loading && ov?.spending_by_cat?.length > 0 && (
        <div className="card p-5">
          <h3 className="font-bold text-sm mb-4" style={{ color: "var(--text-primary)" }}>🍕 Pengeluaran per Kategori — {ov.bulan_ini}</h3>
          <div className="space-y-3">
            {ov.spending_by_cat.map((item: any, i: number) => {
              const max = ov.spending_by_cat[0][1] || 1;
              const pct = Math.round((item[1] / max) * 100);
              const colors = ["#ef4444","#f97316","#f59e0b","#eab308","#84cc16","#22c55e","#06b6d4","#8b5cf6"];
              return (
                <div key={item[0]}>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span style={{ color: "var(--text-primary)" }}>{item[0]}</span>
                    <span style={{ color: "var(--text-muted)" }}>{formatRp(item[1], true)}</span>
                  </div>
                  <div className="progress-bar">
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: colors[i % colors.length] }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* AI INSIGHT + LIVE ACTIVITY */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <AIInsightPanel />
        <LiveActivity />
      </div>

      {/* MOTIVATION */}
      <div className="rounded-2xl p-5" style={{
        background: "linear-gradient(135deg, rgba(16,185,129,0.12), rgba(59,130,246,0.08))",
        border: "1px solid rgba(16,185,129,0.2)"
      }}>
        <p className="text-xs font-semibold mb-1" style={{ color: "#6ee7b7" }}>✨ Motivasi Harian</p>
        <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{motivasi}</p>
      </div>

      {/* QUICK ACTIONS */}
      <div className="card p-5">
        <h3 className="font-bold text-sm mb-4" style={{ color: "var(--text-primary)" }}>⚡ Akses Cepat</h3>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
          {[
            { icon: "📄", label: "Laporan" },
            { icon: "📈", label: "Investasi" },
            { icon: "🏠", label: "Rumah" },
            { icon: "🚗", label: "Kredit" },
            { icon: "💳", label: "Utang" },
            { icon: "👴", label: "Freedom" },
          ].map(q => (
            <button key={q.label} className="flex flex-col items-center gap-2 p-3 rounded-xl transition-all hover:scale-105"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)", color: "var(--text-secondary)" }}>
              <span className="text-2xl">{q.icon}</span>
              <span className="text-xs font-medium">{q.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
