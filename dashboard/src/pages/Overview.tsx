import { useEffect, useState } from "react";
import {
  TrendingUp, TrendingDown, Wallet, BarChart3,
  RefreshCw, ArrowUpRight, ArrowDownRight,
} from "lucide-react";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend,
} from "recharts";
import StatCard from "../components/StatCard";
import Spinner, { ErrorBox } from "../components/Spinner";
import { api } from "../api/client";

const COLORS = [
  "#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6",
  "#06b6d4","#f97316","#84cc16","#ec4899","#14b8a6",
];

function rp(n: number) {
  return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(n);
}

function rpShort(n: number) {
  if (n >= 1_000_000_000) return `Rp ${(n / 1_000_000_000).toFixed(1)}M`;
  if (n >= 1_000_000) return `Rp ${(n / 1_000_000).toFixed(1)}jt`;
  if (n >= 1_000) return `Rp ${(n / 1_000).toFixed(0)}rb`;
  return `Rp ${n}`;
}

const MONTHS_ID = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Ags","Sep","Okt","Nov","Des"];

export default function Overview() {
  const [overview, setOverview] = useState<any>(null);
  const [transaksi, setTransaksi] = useState<any[]>([]);
  const [anggaran, setAnggaran] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [ov, tx, ag] = await Promise.all([
        api.overview(), api.transaksi(), api.anggaran(),
      ]);
      setOverview(ov);
      setTransaksi(tx.data.slice(-10).reverse());
      setAnggaran(ag);
      setLastUpdate(new Date());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <Spinner text="Memuat data keuangan..." />;
  if (error) return <ErrorBox msg={error} />;

  const saldo = overview?.saldo_bersih ?? 0;
  const spendingData = (overview?.spending_by_kategori ?? []).filter((d: any) => d.jumlah > 0);

  // Monthly spending chart from anggaran
  const monthlyData = MONTHS_ID.map((bulan, idx) => {
    const pengeluaran = (anggaran?.pengeluaran ?? []).reduce((sum: number, item: any) => {
      const m = item.bulanan?.[idx];
      return sum + (m?.nilai ?? 0);
    }, 0);
    const pemasukan = (anggaran?.pemasukan ?? []).reduce((sum: number, item: any) => {
      const m = item.bulanan?.[idx];
      return sum + (m?.nilai ?? 0);
    }, 0);
    return { bulan, pengeluaran, pemasukan };
  }).filter(d => d.pengeluaran > 0 || d.pemasukan > 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Beranda</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {lastUpdate ? `Update: ${lastUpdate.toLocaleTimeString("id-ID")}` : ""}
          </p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Pemasukan"
          value={rpShort(overview?.total_pemasukan ?? 0)}
          sub="Semua waktu"
          icon={<TrendingUp size={20} />}
          color="green"
        />
        <StatCard
          title="Total Pengeluaran"
          value={rpShort(overview?.total_pengeluaran ?? 0)}
          sub="Semua waktu"
          icon={<TrendingDown size={20} />}
          color="red"
        />
        <StatCard
          title="Saldo Bersih"
          value={rpShort(saldo)}
          sub={saldo >= 0 ? "Surplus" : "Defisit"}
          icon={<Wallet size={20} />}
          color={saldo >= 0 ? "blue" : "orange"}
        />
        <StatCard
          title="Total Investasi"
          value={rpShort(overview?.total_investasi ?? 0)}
          sub="3 akun aktif"
          icon={<BarChart3 size={20} />}
          color="purple"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Spending by Category */}
        <div className="card">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Pengeluaran Bulan Ini per Kategori</h2>
          {spendingData.length === 0 ? (
            <p className="text-slate-400 text-sm text-center py-8">Belum ada data bulan ini</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={spendingData}
                  dataKey="jumlah"
                  nameKey="kategori"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  innerRadius={50}
                  paddingAngle={2}
                >
                  {spendingData.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v: number) => rp(v)}
                  contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 12 }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
          {spendingData.length > 0 && (
            <div className="mt-3 grid grid-cols-2 gap-1">
              {spendingData.slice(0, 6).map((d: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-xs text-slate-600">
                  <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: COLORS[i % COLORS.length] }} />
                  <span className="truncate">{d.kategori}</span>
                  <span className="ml-auto font-medium text-slate-800">{rpShort(d.jumlah)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Monthly chart */}
        <div className="card">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Pengeluaran vs Pemasukan Bulanan</h2>
          {monthlyData.length === 0 ? (
            <p className="text-slate-400 text-sm text-center py-8">Belum ada data bulanan</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={monthlyData} barSize={16}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="bulan" tick={{ fontSize: 11, fill: "#64748b" }} />
                <YAxis tickFormatter={(v) => rpShort(v)} tick={{ fontSize: 10, fill: "#94a3b8" }} width={70} />
                <Tooltip formatter={(v: number) => rp(v)} contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 12 }} />
                <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="pemasukan" fill="#10b981" name="Pemasukan" radius={[4, 4, 0, 0]} />
                <Bar dataKey="pengeluaran" fill="#f87171" name="Pengeluaran" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="card">
        <h2 className="text-base font-semibold text-slate-700 mb-4">Transaksi Terakhir</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Tanggal</th>
                <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Keterangan</th>
                <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Kategori</th>
                <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Jumlah</th>
              </tr>
            </thead>
            <tbody>
              {transaksi.map((t: any, i: number) => (
                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                  <td className="py-2.5 px-3 text-slate-500 whitespace-nowrap">{t.tanggal_raw}</td>
                  <td className="py-2.5 px-3 text-slate-700 max-w-xs truncate">{t.keterangan || "-"}</td>
                  <td className="py-2.5 px-3">
                    <span className="badge bg-slate-100 text-slate-600">{t.kategori}</span>
                  </td>
                  <td className="py-2.5 px-3 text-right font-medium">
                    <span className={`flex items-center justify-end gap-1 ${t.tipe === "Pemasukan" ? "text-emerald-600" : "text-red-500"}`}>
                      {t.tipe === "Pemasukan" ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                      {rp(t.jumlah)}
                    </span>
                  </td>
                </tr>
              ))}
              {transaksi.length === 0 && (
                <tr><td colSpan={4} className="py-8 text-center text-slate-400">Belum ada transaksi</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
