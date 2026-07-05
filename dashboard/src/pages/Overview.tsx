import { useEffect, useState } from "react";
import { fetchOverview, formatRp } from "../api/client";
import StatCard from "../components/StatCard";
import Spinner from "../components/Spinner";

export default function Overview() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverview()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (!data) return <p className="text-center text-slate-400 py-12">Gagal memuat data</p>;

  const d = data;
  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Saldo Total" value={d.saldo_total} icon="💳" color="emerald" subtitle="Semua akun" />
        <StatCard title="Tabungan" value={d.tabungan_total} icon="🎯" color="blue" subtitle="Target goals" />
        <StatCard title="Pemasukan Bulan Ini" value={d.pemasukan_bulan} icon="📥" color="emerald" subtitle={d.bulan_ini} />
        <StatCard title="Pengeluaran Bulan Ini" value={d.pengeluaran_bulan} icon="📤" color="red" subtitle={d.bulan_ini} />
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-800 mb-4">📊 Ringkasan {d.bulan_ini}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-emerald-50 rounded-xl p-4">
            <p className="text-sm text-emerald-600 font-medium">Pemasukan Minggu Ini</p>
            <p className="text-xl font-bold text-emerald-800">{formatRp(d.pemasukan_minggu)}</p>
          </div>
          <div className="bg-red-50 rounded-xl p-4">
            <p className="text-sm text-red-600 font-medium">Pengeluaran Minggu Ini</p>
            <p className="text-xl font-bold text-red-800">{formatRp(d.pengeluaran_minggu)}</p>
          </div>
          <div className={`rounded-xl p-4 ${d.selisih_bulan >= 0 ? "bg-emerald-50" : "bg-red-50"}`}>
            <p className={`text-sm font-medium ${d.selisih_bulan >= 0 ? "text-emerald-600" : "text-red-600"}`}>
              {d.selisih_bulan >= 0 ? "Surplus Bulan Ini" : "Defisit Bulan Ini"}
            </p>
            <p className={`text-xl font-bold ${d.selisih_bulan >= 0 ? "text-emerald-800" : "text-red-800"}`}>
              {formatRp(Math.abs(d.selisih_bulan))}
            </p>
          </div>
        </div>
      </div>

      {d.spending_by_kategori?.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">📊 Pengeluaran per Kategori — {d.bulan_ini}</h3>
          <div className="space-y-3">
            {d.spending_by_kategori.map((item: any, i: number) => {
              const max = d.spending_by_kategori[0].jumlah;
              const pct = (item.jumlah / max) * 100;
              const colors = ["bg-red-500", "bg-orange-500", "bg-amber-500", "bg-yellow-500", "bg-lime-500", "bg-green-500", "bg-emerald-500", "bg-teal-500"];
              return (
                <div key={item.kategori}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-700 font-medium">{item.kategori}</span>
                    <span className="text-slate-500">{formatRp(item.jumlah)}</span>
                  </div>
                  <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full ${colors[i % colors.length]} rounded-full transition-all`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {d.income_by_kategori?.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">📥 Pemasukan per Kategori — {d.bulan_ini}</h3>
          <div className="space-y-3">
            {d.income_by_kategori.map((item: any) => (
              <div key={item.kategori} className="flex justify-between items-center py-2 border-b border-slate-100 last:border-0">
                <span className="text-slate-700">{item.kategori}</span>
                <span className="font-semibold text-emerald-700">{formatRp(item.jumlah)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
