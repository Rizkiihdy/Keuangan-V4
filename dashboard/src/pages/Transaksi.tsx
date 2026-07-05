import { useEffect, useState } from "react";
import { fetchTransaksi, formatRp, formatDate } from "../api/client";
import Spinner from "../components/Spinner";

export default function Transaksi() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("semua");

  useEffect(() => {
    fetchTransaksi()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (!data) return <p className="text-center text-slate-400 py-12">Gagal memuat data</p>;

  const filtered = filter === "semua"
    ? data.data
    : data.data.filter((t: any) => t.tipe === filter);

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <div className="flex flex-wrap gap-2">
        {[
          { key: "semua", label: "Semua" },
          { key: "Pengeluaran", label: "📤 Pengeluaran" },
          { key: "Pemasukan", label: "📥 Pemasukan" },
          { key: "Transfer", label: "🔄 Transfer" },
        ].map((b) => (
          <button
            key={b.key}
            onClick={() => setFilter(b.key)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filter === b.key
                ? "bg-emerald-600 text-white"
                : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
            }`}
          >
            {b.label}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="text-left px-4 py-3 text-slate-500 font-medium">Tanggal</th>
                <th className="text-left px-4 py-3 text-slate-500 font-medium">Akun</th>
                <th className="text-left px-4 py-3 text-slate-500 font-medium">Memo</th>
                <th className="text-left px-4 py-3 text-slate-500 font-medium">Kategori</th>
                <th className="text-left px-4 py-3 text-slate-500 font-medium">Tipe</th>
                <th className="text-right px-4 py-3 text-slate-500 font-medium">Jumlah</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t: any, i: number) => (
                <tr key={i} className="border-t border-slate-100 hover:bg-slate-50/50">
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{formatDate(t.tanggal)}</td>
                  <td className="px-4 py-3 text-slate-700 font-medium">{t.akun}</td>
                  <td className="px-4 py-3 text-slate-600">{t.memo || "-"}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-600">
                      {t.kategori}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${
                        t.tipe === "Pemasukan"
                          ? "bg-emerald-100 text-emerald-700"
                          : t.tipe === "Transfer"
                          ? "bg-blue-100 text-blue-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {t.tipe}
                    </span>
                  </td>
                  <td className={`px-4 py-3 text-right font-semibold whitespace-nowrap ${
                    t.tipe === "Pemasukan" ? "text-emerald-700" : "text-red-700"
                  }`}>
                    {formatRp(t.jumlah)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <p className="text-center text-slate-400 py-8">Tidak ada transaksi</p>
        )}
        <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-400">
          Menampilkan {filtered.length} dari {data.total} transaksi total
        </div>
      </div>
    </div>
  );
}
