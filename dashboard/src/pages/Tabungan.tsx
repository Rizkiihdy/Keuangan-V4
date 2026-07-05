import { useEffect, useState } from "react";
import { fetchGoals, fetchAkun, formatRp } from "../api/client";
import Spinner from "../components/Spinner";

export default function Tabungan() {
  const [goals, setGoals] = useState<any>(null);
  const [akun, setAkun] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchGoals(), fetchAkun()])
      .then(([g, a]) => {
        setGoals(g);
        setAkun(a);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Accounts */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-800 mb-4">💳 Daftar Akun</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {akun?.data?.map((a: any) => (
            <div key={a.nama} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <p className="text-sm text-slate-500">{a.nama}</p>
              <p className="text-xl font-bold text-slate-800 mt-1">{formatRp(a.balance)}</p>
              {a.goal && <p className="text-xs text-slate-400 mt-1">Goal: {a.goal}</p>}
            </div>
          ))}
          {!akun?.data?.length && <p className="text-sm text-slate-400">Tidak ada data akun</p>}
        </div>
      </div>

      {/* Goals */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-800 mb-4">🎯 Target Tabungan</h3>
        <div className="space-y-4">
          {goals?.data?.map((g: any) => {
            const pct = g.target > 0 ? Math.min(100, Math.round((g.balance / g.target) * 100)) : 0;
            return (
              <div key={g.nama} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-slate-700">{g.nama}</span>
                  <span className="text-sm font-semibold text-emerald-700">{g.persen}</span>
                </div>
                <div className="flex justify-between text-xs text-slate-500 mb-2">
                  <span>Terkumpul: {formatRp(g.balance)}</span>
                  <span>Target: {formatRp(g.target)}</span>
                </div>
                <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
          {!goals?.data?.length && <p className="text-sm text-slate-400">Tidak ada data goals</p>}
        </div>
      </div>
    </div>
  );
}
