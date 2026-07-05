import { useEffect, useState } from "react";
import { Car, Percent, Calendar, DollarSign, TrendingDown } from "lucide-react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import Spinner, { ErrorBox } from "../components/Spinner";
import { api } from "../api/client";

function rp(n: number) {
  return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(n);
}

interface KV { label: string; value: string; icon?: React.ReactNode; color?: string }

function KVRow({ label, value, icon, color = "#6366f1" }: KV) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-slate-50 last:border-0">
      <div className="flex items-center gap-2 text-slate-600 text-sm">
        {icon && <span style={{ color }}>{icon}</span>}
        {label}
      </div>
      <span className="font-bold text-slate-800 text-sm">{value}</span>
    </div>
  );
}

export default function SimulasiKredit() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.kalkKredit()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox msg={error} />;

  const harga = data?.harga_cash ?? 0;
  const dp = data?.uang_muka ?? 0;
  const pokok = data?.pokok_utang ?? 0;
  const cicilan = data?.cicilan_bulanan ?? 0;
  const tenor = data?.tenor_bulan ?? 0;
  const totalKeluar = data?.total_keluar ?? 0;
  const totalBunga = data?.total_bunga ?? cicilan * tenor - pokok;
  const bungaTahunan = data?.bunga_tahunan ?? "—";

  const pokokPct = totalKeluar > 0 ? (pokok / totalKeluar) * 100 : 0;
  const bungaPct = totalKeluar > 0 ? (totalBunga / totalKeluar) * 100 : 0;
  const dpPct = totalKeluar > 0 ? (dp / totalKeluar) * 100 : 0;

  const pieData = [
    { name: "Pokok", value: pokok, color: "#6366f1" },
    { name: "Total Bunga", value: totalBunga, color: "#f87171" },
    { name: "Uang Muka (DP)", value: dp, color: "#10b981" },
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Simulasi Kredit Motor / Mobil</h1>
        <p className="text-slate-500 text-sm mt-1">Data dari Google Sheet — Analisis & Simulasi Kredit</p>
      </div>

      {/* Highlight Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card py-4 text-center border-t-4 border-indigo-500">
          <Car size={20} className="text-indigo-500 mx-auto mb-2" />
          <p className="text-xs text-slate-500 uppercase tracking-wide">Harga Cash</p>
          <p className="text-lg font-black text-slate-800 mt-1">{rp(harga)}</p>
        </div>
        <div className="card py-4 text-center border-t-4 border-emerald-500">
          <DollarSign size={20} className="text-emerald-500 mx-auto mb-2" />
          <p className="text-xs text-slate-500 uppercase tracking-wide">Uang Muka (DP)</p>
          <p className="text-lg font-black text-emerald-600 mt-1">{rp(dp)}</p>
        </div>
        <div className="card py-4 text-center border-t-4 border-amber-500">
          <Calendar size={20} className="text-amber-500 mx-auto mb-2" />
          <p className="text-xs text-slate-500 uppercase tracking-wide">Cicilan / Bulan</p>
          <p className="text-lg font-black text-amber-600 mt-1">{rp(cicilan)}</p>
        </div>
        <div className="card py-4 text-center border-t-4 border-red-400">
          <Percent size={20} className="text-red-400 mx-auto mb-2" />
          <p className="text-xs text-slate-500 uppercase tracking-wide">Bunga Efektif/Thn</p>
          <p className="text-lg font-black text-red-500 mt-1">{bungaTahunan}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Detail Table */}
        <div className="card">
          <h2 className="text-base font-semibold text-slate-700 mb-2">Detail Kredit</h2>
          <KVRow label="Harga Cash" value={rp(harga)} icon={<Car size={15} />} />
          <KVRow label="Uang Muka (DP)" value={rp(dp)} icon={<DollarSign size={15} />} color="#10b981" />
          <KVRow label="Pokok Utang" value={rp(pokok)} icon={<TrendingDown size={15} />} color="#6366f1" />
          <KVRow label="Tenor" value={`${tenor} bulan`} icon={<Calendar size={15} />} color="#f59e0b" />
          <KVRow label="Cicilan per Bulan" value={rp(cicilan)} icon={<Calendar size={15} />} color="#f59e0b" />
          <KVRow label="Total Bunga" value={rp(totalBunga)} icon={<Percent size={15} />} color="#ef4444" />
          <div className="mt-3 pt-3 border-t border-slate-100 flex justify-between">
            <span className="text-sm font-semibold text-slate-700">Total Uang Keluar</span>
            <span className="font-black text-slate-900">{rp(totalKeluar || (dp + cicilan * tenor))}</span>
          </div>
        </div>

        {/* Pie Chart */}
        <div className="card">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Komposisi Total Pembayaran</h2>
          {pieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" cx="50%" cy="50%" outerRadius={80} innerRadius={45} paddingAngle={3}>
                    {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                  </Pie>
                  <Tooltip formatter={(v: number) => rp(v)} contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-3 space-y-2">
                {pieData.map((d, i) => (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full" style={{ background: d.color }} />
                      <span className="text-slate-600">{d.name}</span>
                    </div>
                    <span className="font-semibold text-slate-800">{rp(d.value)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-slate-400 text-center py-10 text-sm">Data belum tersedia</p>
          )}
        </div>
      </div>

      {/* Warning Box */}
      {bungaTahunan && bungaTahunan !== "—" && parseFloat(bungaTahunan) > 20 && (
        <div className="rounded-2xl bg-red-50 border border-red-200 p-5">
          <p className="font-semibold text-red-700 mb-1">⚠️ Perhatian: Bunga Tinggi</p>
          <p className="text-sm text-red-600">
            Bunga efektif tahunan <strong>{bungaTahunan}</strong> tergolong tinggi. Pertimbangkan bayar cash jika memungkinkan, atau negosiasikan tenor yang lebih pendek untuk mengurangi total bunga.
          </p>
        </div>
      )}
    </div>
  );
}
