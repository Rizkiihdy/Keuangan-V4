import { useEffect, useState } from "react";
import { CreditCard, TrendingDown, AlertTriangle, CheckCircle } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import Spinner, { ErrorBox } from "../components/Spinner";
import { api } from "../api/client";

function rp(n: number) {
  return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(n);
}
function rpShort(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}jt`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}rb`;
  return `${n}`;
}

const DEBT_COLORS = ["#ef4444", "#f97316", "#f59e0b", "#eab308", "#84cc16"];

export default function KalkulatorUtang() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.kalkUtang()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox msg={error} />;

  const debts: any[] = data?.debts ?? [];
  const totalHutang: number = data?.total_hutang ?? 0;
  const totalMin: number = data?.total_min_pembayaran ?? 0;

  const sortedByBunga = [...debts].sort((a, b) => {
    const ra = parseFloat(a.bunga_tahunan) || 0;
    const rb = parseFloat(b.bunga_tahunan) || 0;
    return rb - ra;
  });

  const chartData = debts.map((d, i) => ({
    name: d.kreditur.length > 12 ? d.kreditur.slice(0, 12) + "…" : d.kreditur,
    sisa: d.sisa_hutang,
    color: DEBT_COLORS[i % DEBT_COLORS.length],
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Kalkulator Pelunasan Utang</h1>
        <p className="text-slate-500 text-sm mt-1">Data dari Google Sheet — Kalkulator Pelunasan Utang</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card py-4 border-t-4 border-red-400">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Total Sisa Hutang</p>
          <p className="text-2xl font-black text-red-500 mt-1">{rp(totalHutang)}</p>
          <p className="text-xs text-slate-400 mt-1">{debts.length} kreditur</p>
        </div>
        <div className="card py-4 border-t-4 border-amber-400">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Min. Pembayaran / Bln</p>
          <p className="text-2xl font-black text-amber-600 mt-1">{rp(totalMin)}</p>
        </div>
        <div className="card py-4 border-t-4 border-indigo-500">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Hutang Terbesar</p>
          <p className="text-lg font-black text-indigo-600 mt-1">
            {debts.length > 0
              ? [...debts].sort((a, b) => b.sisa_hutang - a.sisa_hutang)[0]?.kreditur ?? "—"
              : "—"}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            {debts.length > 0
              ? rp([...debts].sort((a, b) => b.sisa_hutang - a.sisa_hutang)[0]?.sisa_hutang ?? 0)
              : ""}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="card">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Sisa Hutang per Kreditur</h2>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} layout="vertical" margin={{ left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" tickFormatter={rpShort} tick={{ fontSize: 10, fill: "#94a3b8" }} />
                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11, fill: "#64748b" }} />
                <Tooltip formatter={(v: number) => rp(v)} contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 12 }} />
                <Bar dataKey="sisa" radius={[0, 6, 6, 0]} barSize={20}>
                  {chartData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-400 text-center py-10 text-sm">Belum ada data hutang</p>
          )}
        </div>

        {/* Debt List sorted by interest */}
        <div className="card">
          <h2 className="text-base font-semibold text-slate-700 mb-1">Strategi Avalanche (Bunga Tertinggi Dulu)</h2>
          <p className="text-xs text-slate-400 mb-4">Prioritaskan hutang dengan bunga tertinggi untuk hemat bayar bunga</p>
          <div className="space-y-3">
            {sortedByBunga.map((d, i) => {
              const bunga = parseFloat(d.bunga_tahunan) || 0;
              return (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors">
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                    style={{ background: DEBT_COLORS[i % DEBT_COLORS.length] }}
                  >
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-slate-800 text-sm truncate">{d.kreditur}</p>
                    <p className="text-xs text-slate-500">{rp(d.sisa_hutang)} · Min: {rp(d.min_pembayaran)}/bln</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className={`badge ${bunga > 25 ? "bg-red-100 text-red-700" : bunga > 15 ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-600"}`}>
                      {d.bunga_tahunan}
                    </span>
                  </div>
                </div>
              );
            })}
            {debts.length === 0 && (
              <div className="text-center py-6">
                <CheckCircle className="text-emerald-300 mx-auto mb-2" size={32} />
                <p className="text-slate-400 text-sm">Bebas hutang! 🎉</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tips */}
      {debts.length > 0 && (
        <div className="rounded-2xl bg-amber-50 border border-amber-200 p-5">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={18} className="text-amber-600" />
            <h3 className="font-semibold text-amber-800">Strategi Pelunasan</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-amber-700">
            <div>
              <p className="font-medium mb-1">🔥 Avalanche (Hemat Bunga)</p>
              <p className="text-xs">Lunasi hutang dengan bunga tertinggi dulu. Bayar minimum untuk yang lain, surplus ke hutang termahal.</p>
            </div>
            <div>
              <p className="font-medium mb-1">❄️ Snowball (Motivasi)</p>
              <p className="text-xs">Lunasi hutang terkecil dulu. Memberi rasa pencapaian lebih cepat meski bayar bunga lebih banyak.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
