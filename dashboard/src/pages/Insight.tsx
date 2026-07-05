import { useEffect, useState } from "react";
import { fetchInsightData, fetchCashflow, formatRp } from "../api/client";
import { Spinner } from "../components/Spinner";
import AIInsightPanel from "../components/AIInsightPanel";
import LiveActivity from "../components/LiveActivity";
import BarChart from "../components/BarChart";

export default function Insight() {
  const [insight, setInsight] = useState<any>(null);
  const [cf, setCf] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchInsightData(), fetchCashflow()])
      .then(([i, c]) => { setInsight(i); setCf(c); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      {/* AI Insight */}
      <AIInsightPanel />

      {/* Cashflow 6 bulan */}
      <div className="card p-5">
        <h3 className="font-bold text-sm mb-4" style={{ color: "var(--text-primary)" }}>📊 Income vs Expense — 6 Bulan</h3>
        {cf?.monthly && <BarChart data={cf.monthly} height={200} />}
        {/* Monthly table */}
        {cf?.monthly && (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  <th className="text-left py-2 px-3" style={{ color: "var(--text-muted)" }}>Bulan</th>
                  <th className="text-right py-2 px-3 text-emerald-400">Pemasukan</th>
                  <th className="text-right py-2 px-3 text-red-400">Pengeluaran</th>
                  <th className="text-right py-2 px-3" style={{ color: "var(--text-muted)" }}>Net</th>
                </tr>
              </thead>
              <tbody>
                {cf.monthly.map((m: any, i: number) => {
                  const net = m.income - m.expense;
                  return (
                    <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td className="py-2 px-3 font-medium" style={{ color: "var(--text-primary)" }}>{m.month}</td>
                      <td className="py-2 px-3 text-right text-emerald-400">{formatRp(m.income, true)}</td>
                      <td className="py-2 px-3 text-right text-red-400">{formatRp(m.expense, true)}</td>
                      <td className={`py-2 px-3 text-right font-semibold ${net >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {net >= 0 ? "+" : ""}{formatRp(net, true)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Daily 7 */}
      {cf?.daily_7 && (
        <div className="card p-5">
          <h3 className="font-bold text-sm mb-4" style={{ color: "var(--text-primary)" }}>📅 Pengeluaran 7 Hari Terakhir</h3>
          <div className="flex gap-2 items-end h-20">
            {cf.daily_7.map((d: any, i: number) => {
              const max = Math.max(...cf.daily_7.map((x: any) => x.total)) || 1;
              const h = Math.max(4, (d.total / max) * 70);
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <div className="rounded-t-md w-full transition-all" style={{ height: h, background: "linear-gradient(to top, #ef4444, #f97316)" }} title={formatRp(d.total)} />
                  <span className="text-xs" style={{ color: "var(--text-muted)", fontSize: 9 }}>{d.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Memo Analysis */}
      {insight?.memo?.length > 0 && (
        <div className="card p-5">
          <h3 className="font-bold text-sm mb-4" style={{ color: "var(--text-primary)" }}>📝 Analisis Memo (Pengeluaran Terbesar)</h3>
          <div className="space-y-3">
            {insight.memo.map((item: any, i: number) => {
              const max = insight.memo[0]?.total || 1;
              const pct = Math.round((item.total / max) * 100);
              const colors = ["#3b82f6","#6366f1","#8b5cf6","#a855f7","#ec4899","#f43f5e","#f97316","#eab308"];
              return (
                <div key={i}>
                  <div className="flex justify-between text-xs mb-1">
                    <span style={{ color: "var(--text-primary)" }}>{item.nama}</span>
                    <span style={{ color: "var(--text-muted)" }}>{formatRp(item.total, true)} · {item.frekuensi}×</span>
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

      {/* Payee Analysis */}
      {insight?.payee?.length > 0 && (
        <div className="card p-5">
          <h3 className="font-bold text-sm mb-4" style={{ color: "var(--text-primary)" }}>🏧 Analisis Tempat / Payee</h3>
          <div className="space-y-3">
            {insight.payee.map((item: any, i: number) => {
              const max = insight.payee[0]?.total || 1;
              const pct = Math.round((item.total / max) * 100);
              return (
                <div key={i}>
                  <div className="flex justify-between text-xs mb-1">
                    <span style={{ color: "var(--text-primary)" }}>{item.nama}</span>
                    <span style={{ color: "var(--text-muted)" }}>{formatRp(item.total, true)} · {item.frekuensi}×</span>
                  </div>
                  <div className="progress-bar">
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: "#8b5cf6" }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Stats */}
      {insight?.stats && Object.keys(insight.stats).length > 0 && (
        <div className="card p-5">
          <h3 className="font-bold text-sm mb-4" style={{ color: "var(--text-primary)" }}>📈 Statistik Kebiasaan</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {Object.entries(insight.stats).map(([k, v]) => (
              <div key={k} className="p-3 rounded-xl" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
                <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>{k}</p>
                <p className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>{String(v)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <LiveActivity />
    </div>
  );
}
