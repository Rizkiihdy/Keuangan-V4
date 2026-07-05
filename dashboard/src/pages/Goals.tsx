import { useEffect, useState } from "react";
import { Target, CheckCircle2, Clock, AlertCircle } from "lucide-react";
import Spinner, { ErrorBox } from "../components/Spinner";
import { api } from "../api/client";

function rp(n: number) {
  return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(n);
}

const GOAL_COLORS = [
  "#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#f97316",
];

function statusIcon(status: string, pct: number) {
  if (pct >= 100 || status === "Selesai" || status === "Tercapai") return <CheckCircle2 size={16} className="text-emerald-500" />;
  if (status === "Belum Mulai") return <Clock size={16} className="text-slate-400" />;
  return <AlertCircle size={16} className="text-amber-500" />;
}

function statusBadge(status: string, pct: number) {
  if (pct >= 100 || status === "Selesai") return "bg-emerald-100 text-emerald-700";
  if (status === "Belum Mulai") return "bg-slate-100 text-slate-500";
  return "bg-amber-100 text-amber-700";
}

export default function Goals() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.goals()
      .then((r) => setData(r.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox msg={error} />;

  const totalTarget = data.reduce((s, d) => s + (d.target || 0), 0);
  const totalTerkumpul = data.reduce((s, d) => s + (d.terkumpul || 0), 0);
  const tercapai = data.filter((d) => d.persen >= 100).length;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Target Tabungan</h1>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Total Target</p>
          <p className="text-xl font-bold text-slate-800 mt-1">{rp(totalTarget)}</p>
        </div>
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Total Terkumpul</p>
          <p className="text-xl font-bold text-indigo-600 mt-1">{rp(totalTerkumpul)}</p>
        </div>
        <div className="card py-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Goal Tercapai</p>
          <p className="text-xl font-bold text-emerald-600 mt-1">{tercapai} / {data.length}</p>
        </div>
      </div>

      {/* Goal Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.map((goal, i) => {
          const color = GOAL_COLORS[i % GOAL_COLORS.length];
          const pct = Math.min(goal.persen ?? 0, 100);
          const sisa = (goal.target || 0) - (goal.terkumpul || 0);
          return (
            <div key={i} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: color + "20" }}>
                    <Target size={20} style={{ color }} />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">{goal.nama}</h3>
                    <span className={`badge mt-0.5 ${statusBadge(goal.status, pct)}`}>
                      {statusIcon(goal.status, pct)}
                      <span className="ml-1">{goal.status || "Aktif"}</span>
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-black" style={{ color }}>{pct.toFixed(0)}%</p>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mb-3">
                <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${pct}%`, background: color }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <p className="text-xs text-slate-400">Target</p>
                  <p className="text-sm font-bold text-slate-700 mt-0.5">{rp(goal.target)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Terkumpul</p>
                  <p className="text-sm font-bold mt-0.5" style={{ color }}>{rp(goal.terkumpul)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Sisa</p>
                  <p className="text-sm font-bold text-slate-500 mt-0.5">{rp(Math.max(sisa, 0))}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {data.length === 0 && (
        <div className="card text-center py-16">
          <Target size={40} className="text-slate-200 mx-auto mb-3" />
          <p className="text-slate-400 text-base">Belum ada target tabungan.</p>
          <p className="text-slate-300 text-sm mt-1">Data diambil dari sheet <strong>Target Tabungan</strong> di Google Sheets.</p>
        </div>
      )}
    </div>
  );
}
