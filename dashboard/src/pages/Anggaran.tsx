import { useEffect, useState } from "react";
import { fetchBudget, formatRp } from "../api/client";
import Spinner from "../components/Spinner";

export default function Anggaran() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBudget()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (!data) return <p className="text-center text-slate-400 py-12">Gagal memuat data</p>;

  const now = new Date();
  const currentMonthIdx = now.getMonth();

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* INCOME */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-emerald-700 mb-4 flex items-center gap-2">
            <span>📥</span> Pendapatan
          </h3>
          <div className="space-y-3">
            {data.income.map((item: any) => (
              <div key={item.nama}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-700 font-medium">{item.nama}</span>
                  <span className="text-slate-500">{formatRp(item.total)}</span>
                </div>
                <div className="flex gap-1">
                  {item.bulanan.map((v: number, i: number) => (
                    <div
                      key={i}
                      className={`flex-1 h-6 rounded-md flex items-center justify-center text-[10px] font-medium ${
                        v > 0 ? "bg-emerald-100 text-emerald-700" : "bg-slate-50 text-slate-300"
                      } ${i === currentMonthIdx ? "ring-1 ring-emerald-400" : ""}`}
                      title={`${data.months[i]}: ${formatRp(v)}`}
                    >
                      {v > 0 ? (v >= 1000000 ? (v / 1000000).toFixed(0) + "jt" : (v / 1000).toFixed(0) + "rb") : "-"}
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {data.income.length === 0 && <p className="text-sm text-slate-400">Tidak ada data pendapatan</p>}
          </div>
        </div>

        {/* EXPENSE */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-red-700 mb-4 flex items-center gap-2">
            <span>📤</span> Pengeluaran
          </h3>
          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {data.expense.map((item: any) => (
              <div key={item.nama}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-700 font-medium">{item.nama}</span>
                  <span className="text-slate-500">{formatRp(item.total)}</span>
                </div>
                <div className="flex gap-1">
                  {item.bulanan.map((v: number, i: number) => (
                    <div
                      key={i}
                      className={`flex-1 h-6 rounded-md flex items-center justify-center text-[10px] font-medium ${
                        v > 0 ? "bg-red-100 text-red-700" : "bg-slate-50 text-slate-300"
                      } ${i === currentMonthIdx ? "ring-1 ring-red-400" : ""}`}
                      title={`${data.months[i]}: ${formatRp(v)}`}
                    >
                      {v > 0 ? (v >= 1000000 ? (v / 1000000).toFixed(0) + "jt" : (v / 1000).toFixed(0) + "rb") : "-"}
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {data.expense.length === 0 && <p className="text-sm text-slate-400">Tidak ada data pengeluaran</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
