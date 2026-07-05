import { useEffect, useState, useMemo } from "react";
import { Search, ArrowUpRight, ArrowDownRight, Filter } from "lucide-react";
import Spinner, { ErrorBox } from "../components/Spinner";
import { api } from "../api/client";

function rp(n: number) {
  return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(n);
}

export default function Transaksi() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filterTipe, setFilterTipe] = useState("Semua");
  const [filterKat, setFilterKat] = useState("Semua");

  useEffect(() => {
    api.transaksi()
      .then((r) => setData(r.data.reverse()))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const kategoriList = useMemo(() => {
    const s = new Set(data.map((d) => d.kategori).filter(Boolean));
    return ["Semua", ...Array.from(s).sort()];
  }, [data]);

  const filtered = useMemo(() => {
    return data.filter((d) => {
      const q = search.toLowerCase();
      const matchSearch =
        !q ||
        d.keterangan?.toLowerCase().includes(q) ||
        d.kategori?.toLowerCase().includes(q) ||
        d.jumlah_fmt?.toLowerCase().includes(q);
      const matchTipe = filterTipe === "Semua" || d.tipe === filterTipe;
      const matchKat = filterKat === "Semua" || d.kategori === filterKat;
      return matchSearch && matchTipe && matchKat;
    });
  }, [data, search, filterTipe, filterKat]);

  const totalPemasukan = filtered.filter((d) => d.tipe === "Pemasukan").reduce((s, d) => s + d.jumlah, 0);
  const totalPengeluaran = filtered.filter((d) => d.tipe === "Pengeluaran").reduce((s, d) => s + d.jumlah, 0);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox msg={error} />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Transaksi</h1>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Total Ditampilkan</p>
          <p className="text-xl font-bold text-slate-800 mt-1">{filtered.length} transaksi</p>
        </div>
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Pemasukan</p>
          <p className="text-xl font-bold text-emerald-600 mt-1">{rp(totalPemasukan)}</p>
        </div>
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Pengeluaran</p>
          <p className="text-xl font-bold text-red-500 mt-1">{rp(totalPengeluaran)}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card py-4">
        <div className="flex flex-wrap gap-3 items-center">
          <div className="relative flex-1 min-w-48">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cari keterangan, kategori..."
              className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-slate-50"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={15} className="text-slate-400" />
            <select
              value={filterTipe}
              onChange={(e) => setFilterTipe(e.target.value)}
              className="text-sm border border-slate-200 rounded-xl px-3 py-2 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              {["Semua", "Pengeluaran", "Pemasukan", "Transfer"].map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
            <select
              value={filterKat}
              onChange={(e) => setFilterKat(e.target.value)}
              className="text-sm border border-slate-200 rounded-xl px-3 py-2 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              {kategoriList.map((k) => <option key={k}>{k}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Tanggal</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Keterangan</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Kategori</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Tipe</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Jumlah</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t, i) => (
                <tr key={i} className="border-b border-slate-50 hover:bg-indigo-50/40 transition-colors">
                  <td className="py-3 px-4 text-slate-500 whitespace-nowrap">{t.tanggal_raw}</td>
                  <td className="py-3 px-4 text-slate-700">{t.keterangan || "-"}</td>
                  <td className="py-3 px-4">
                    <span className="badge bg-slate-100 text-slate-600">{t.kategori}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`badge ${t.tipe === "Pemasukan" ? "bg-emerald-100 text-emerald-700" : t.tipe === "Pengeluaran" ? "bg-red-100 text-red-700" : "bg-blue-100 text-blue-700"}`}>
                      {t.tipe}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-semibold">
                    <span className={`flex items-center justify-end gap-1 ${t.tipe === "Pemasukan" ? "text-emerald-600" : "text-red-500"}`}>
                      {t.tipe === "Pemasukan" ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                      {rp(t.jumlah)}
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={5} className="py-12 text-center text-slate-400">Tidak ada transaksi ditemukan</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
