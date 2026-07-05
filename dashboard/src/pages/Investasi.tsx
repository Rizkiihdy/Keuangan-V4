import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, Legend,
} from "recharts";
import { TrendingUp, TrendingDown, DollarSign } from "lucide-react";
import Spinner, { ErrorBox } from "../components/Spinner";
import { api } from "../api/client";

function rp(n: number) {
  return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(n);
}
function rpShort(n: number) {
  if (n >= 1_000_000_000) return `Rp ${(n / 1_000_000_000).toFixed(2)}M`;
  if (n >= 1_000_000) return `Rp ${(n / 1_000_000).toFixed(2)}jt`;
  if (n >= 1_000) return `Rp ${(n / 1_000).toFixed(0)}rb`;
  return `Rp ${n}`;
}

const ACC_COLORS = ["#6366f1", "#10b981", "#f59e0b"];
const ACC_NAMES: Record<string, string> = {
  Account1: "Dana Darurat",
  Account2: "Bibit",
  Account3: "Saham",
};

export default function Investasi() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.investasi()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox msg={error} />;

  const accounts: any[] = data?.accounts ?? [];
  const totalInvested: number = data?.total_invested ?? 0;
  const totalValue: number = data?.total_value ?? 0;
  const totalGL: number = totalValue - totalInvested;

  const chartData = accounts.map((a: any, i: number) => ({
    name: ACC_NAMES[a.nama] ?? a.nama,
    Diinvestasikan: a.invested,
    "Nilai Saat Ini": a.value,
    fill: ACC_COLORS[i],
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Portofolio Investasi</h1>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Total Diinvestasikan</p>
          <p className="text-xl font-bold text-slate-800 mt-1">{rpShort(totalInvested)}</p>
        </div>
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Nilai Saat Ini</p>
          <p className="text-xl font-bold text-indigo-600 mt-1">{rpShort(totalValue)}</p>
        </div>
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Gain / Loss</p>
          <p className={`text-xl font-bold mt-1 flex items-center gap-1 ${totalGL >= 0 ? "text-emerald-600" : "text-red-500"}`}>
            {totalGL >= 0 ? <TrendingUp size={18} /> : <TrendingDown size={18} />}
            {rp(Math.abs(totalGL))}
          </p>
        </div>
      </div>

      {/* Account Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {accounts.map((acc: any, i: number) => {
          const gl = acc.value - acc.invested;
          const pctChange = acc.invested > 0 ? ((acc.value - acc.invested) / acc.invested) * 100 : 0;
          return (
            <div key={acc.nama} className="card border-t-4" style={{ borderColor: ACC_COLORS[i] }}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: ACC_COLORS[i] }}>
                    {acc.nama}
                  </p>
                  <p className="font-bold text-slate-700 mt-0.5">{ACC_NAMES[acc.nama] ?? acc.nama}</p>
                </div>
                <div className="p-2 rounded-xl" style={{ background: ACC_COLORS[i] + "20" }}>
                  <DollarSign size={18} style={{ color: ACC_COLORS[i] }} />
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Modal</span>
                  <span className="font-medium text-slate-700">{rp(acc.invested)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Nilai Sekarang</span>
                  <span className="font-semibold text-slate-800">{rp(acc.value)}</span>
                </div>
                <div className="h-px bg-slate-100" />
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Gain/Loss</span>
                  <span className={`font-bold ${gl >= 0 ? "text-emerald-600" : "text-red-500"}`}>
                    {gl >= 0 ? "+" : ""}{rp(gl)} ({pctChange.toFixed(1)}%)
                  </span>
                </div>
              </div>
              {/* Progress bar */}
              <div className="mt-3">
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: acc.invested > 0 ? `${Math.min((acc.value / acc.invested) * 100, 100)}%` : "0%",
                      background: ACC_COLORS[i],
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Bar Chart */}
      {chartData.length > 0 && (
        <div className="card">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Perbandingan Modal vs Nilai</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData} barSize={28}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }} />
              <YAxis tickFormatter={(v) => rpShort(v)} tick={{ fontSize: 10, fill: "#94a3b8" }} width={70} />
              <Tooltip
                formatter={(v: number) => rp(v)}
                contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 12 }}
              />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Diinvestasikan" fill="#94a3b8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Nilai Saat Ini" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {accounts.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-slate-400 text-base">Belum ada data investasi.</p>
          <p className="text-slate-300 text-sm mt-1">Tambahkan lewat bot: <code className="bg-slate-100 px-2 py-0.5 rounded">/invest 1 saham BBCA 100 8500</code></p>
        </div>
      )}
    </div>
  );
}
