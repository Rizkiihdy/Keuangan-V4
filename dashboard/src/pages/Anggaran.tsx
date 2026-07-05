import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Cell,
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

export default function Anggaran() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.anggaran()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox msg={error} />;

  const pengeluaran: any[] = (data?.pengeluaran ?? []).filter((d: any) => d.anggaran > 0 || d.total_aktual > 0);
  const totalAnggaran = pengeluaran.reduce((s, d) => s + d.anggaran, 0);
  const totalAktual = pengeluaran.reduce((s, d) => s + d.total_aktual, 0);
  const sisaAnggaran = totalAnggaran - totalAktual;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Anggaran</h1>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Total Anggaran Bulanan</p>
          <p className="text-xl font-bold text-slate-800 mt-1">{rp(totalAnggaran)}</p>
        </div>
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Realisasi Aktual</p>
          <p className="text-xl font-bold text-red-500 mt-1">{rp(totalAktual)}</p>
        </div>
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Sisa / Surplus Anggaran</p>
          <p className={`text-xl font-bold mt-1 ${sisaAnggaran >= 0 ? "text-emerald-600" : "text-red-500"}`}>
            {rp(sisaAnggaran)}
          </p>
        </div>
      </div>

      {/* Bar Chart: Anggaran vs Aktual */}
      <div className="card">
        <h2 className="text-base font-semibold text-slate-700 mb-4">Anggaran vs Aktual per Kategori</h2>
        {pengeluaran.length === 0 ? (
          <p className="text-slate-400 text-sm text-center py-10">Belum ada data anggaran</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={pengeluaran} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tickFormatter={rpShort} tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <YAxis
                type="category"
                dataKey="kategori"
                width={120}
                tick={{ fontSize: 11, fill: "#64748b" }}
              />
              <Tooltip
                formatter={(v: number) => rp(v)}
                contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 12 }}
              />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="anggaran" name="Anggaran" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={10} />
              <Bar dataKey="total_aktual" name="Aktual" fill="#f97316" radius={[0, 4, 4, 0]} barSize={10} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Detail table */}
      <div className="card p-0 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="text-base font-semibold text-slate-700">Detail per Kategori</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wide">Kategori</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Anggaran/bln</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Aktual</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Selisih</th>
                <th className="py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wide">Progress</th>
              </tr>
            </thead>
            <tbody>
              {pengeluaran.map((d: any, i: number) => {
                const pct = d.anggaran > 0 ? Math.min((d.total_aktual / d.anggaran) * 100, 100) : 0;
                const over = d.total_aktual > d.anggaran && d.anggaran > 0;
                return (
                  <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/80">
                    <td className="py-3 px-6 font-medium text-slate-700">{d.kategori}</td>
                    <td className="py-3 px-4 text-right text-slate-600">{rp(d.anggaran)}</td>
                    <td className="py-3 px-4 text-right font-semibold text-slate-800">{rp(d.total_aktual)}</td>
                    <td className={`py-3 px-4 text-right font-semibold ${over ? "text-red-500" : "text-emerald-600"}`}>
                      {over ? "-" : "+"}{rp(Math.abs(d.anggaran - d.total_aktual))}
                    </td>
                    <td className="py-3 px-6">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${over ? "bg-red-400" : pct > 75 ? "bg-orange-400" : "bg-indigo-500"}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-500 w-10 text-right">{pct.toFixed(0)}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {pengeluaran.length === 0 && (
                <tr><td colSpan={5} className="py-10 text-center text-slate-400">Belum ada data anggaran. Isi anggaran di Google Sheet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
