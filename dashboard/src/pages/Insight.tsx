import { useEffect, useState } from "react";
import { fetchInsight, formatRp } from "../api/client";
import Spinner from "../components/Spinner";

export default function Insight() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInsight()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (!data) return <p className="text-center text-slate-400 py-12">Gagal memuat data</p>;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Weekly */}
      {data.top_weekly?.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">⚡ Top Pengeluaran Minggu Ini</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {data.top_weekly.map((item: any, i: number) => (
              <div key={i} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                <p className="text-xs text-slate-400 mb-1">#{i + 1} {item.label}</p>
                <p className="text-lg font-bold text-slate-800">{item.nilai}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Memo Analysis */}
      {data.memo_analysis?.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">📝 Analisis Berdasarkan Memo</h3>
          <div className="space-y-3">
            {data.memo_analysis.map((item: any, i: number) => {
              const max = data.memo_analysis[0].total || 1;
              const pct = (item.total / max) * 100;
              return (
                <div key={item.nama}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-700 font-medium">{item.nama}</span>
                    <span className="text-slate-500">{formatRp(item.total)} — {item.frekuensi}x</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Payee Analysis */}
      {data.payee_analysis?.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">🏧 Analisis Berdasarkan Tempat / Payee</h3>
          <div className="space-y-3">
            {data.payee_analysis.map((item: any, i: number) => {
              const max = data.payee_analysis[0].total || 1;
              const pct = (item.total / max) * 100;
              return (
                <div key={item.nama}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-700 font-medium">{item.nama}</span>
                    <span className="text-slate-500">{formatRp(item.total)} — {item.frekuensi}x</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Stats */}
      {Object.keys(data.stats || {}).length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">📈 Statistik Kebiasaan</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(data.stats).map(([k, v]) => (
              <div key={k} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                <p className="text-xs text-slate-400 mb-1">{k}</p>
                <p className="text-lg font-bold text-slate-800">{String(v)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
