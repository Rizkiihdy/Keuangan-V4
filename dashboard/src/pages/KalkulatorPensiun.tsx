import { useEffect, useState } from "react";
import { Clock, Target, TrendingUp, Calendar } from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import Spinner, { ErrorBox } from "../components/Spinner";
import { api } from "../api/client";

function rp(n: number) {
  return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(n);
}
function rpShort(n: number) {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}M`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}jt`;
  return `${(n / 1_000).toFixed(0)}rb`;
}

export default function KalkulatorPensiun() {
  const [pensiun, setPensiun] = useState<any>(null);
  const [tabungan, setTabungan] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.kalkPensiun(), api.kalkTabunganPensiun()])
      .then(([p, t]) => { setPensiun(p); setTabungan(t); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox msg={error} />;

  const usiaNow = pensiun?.usia_sekarang ?? tabungan?.usia_sekarang ?? 0;
  const usiaPensiun = pensiun?.usia_pensiun ?? tabungan?.usia_pensiun ?? 0;
  const sisaTahun = usiaPensiun > usiaNow ? usiaPensiun - usiaNow : 0;
  const gaji = pensiun?.gaji_pensiun ?? 0;
  const saldoNow = tabungan?.saldo_sekarang ?? 0;
  const nilaiFuture = tabungan?.nilai_masa_depan ?? 0;
  const tahunInv = tabungan?.tahun_investasi ?? sisaTahun;

  // Proyeksi pertumbuhan sederhana untuk chart
  const growthRate = nilaiFuture > 0 && saldoNow > 0 && tahunInv > 0
    ? Math.pow(nilaiFuture / (saldoNow || 1), 1 / tahunInv) - 1
    : 0.08;

  const proyeksiData = Array.from({ length: tahunInv + 1 }, (_, i) => ({
    tahun: `${usiaNow + i}`,
    nilai: Math.round(saldoNow * Math.pow(1 + growthRate, i)),
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Kalkulator Pensiun</h1>
        <p className="text-slate-500 text-sm mt-1">Proyeksi rencana pensiun dari Google Sheet</p>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card py-4 text-center">
          <div className="flex justify-center mb-2"><Clock size={22} className="text-indigo-500" /></div>
          <p className="text-xs text-slate-500 uppercase tracking-wide">Usia Sekarang</p>
          <p className="text-3xl font-black text-slate-800 mt-1">{usiaNow || "—"}</p>
          <p className="text-xs text-slate-400">tahun</p>
        </div>
        <div className="card py-4 text-center">
          <div className="flex justify-center mb-2"><Calendar size={22} className="text-emerald-500" /></div>
          <p className="text-xs text-slate-500 uppercase tracking-wide">Usia Pensiun</p>
          <p className="text-3xl font-black text-emerald-600 mt-1">{usiaPensiun || "—"}</p>
          <p className="text-xs text-slate-400">tahun</p>
        </div>
        <div className="card py-4 text-center">
          <div className="flex justify-center mb-2"><Target size={22} className="text-amber-500" /></div>
          <p className="text-xs text-slate-500 uppercase tracking-wide">Sisa Waktu</p>
          <p className="text-3xl font-black text-amber-500 mt-1">{sisaTahun || "—"}</p>
          <p className="text-xs text-slate-400">tahun lagi</p>
        </div>
        <div className="card py-4 text-center">
          <div className="flex justify-center mb-2"><TrendingUp size={22} className="text-violet-500" /></div>
          <p className="text-xs text-slate-500 uppercase tracking-wide">Est. Nilai Pensiun</p>
          <p className="text-xl font-black text-violet-600 mt-1">{nilaiFuture ? rpShort(nilaiFuture) : "—"}</p>
        </div>
      </div>

      {/* Tabungan detail */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Tabungan Dana Pensiun</h2>
          <div className="space-y-3">
            <div className="flex justify-between text-sm border-b border-slate-50 pb-2">
              <span className="text-slate-500">Saldo Tabungan Saat Ini</span>
              <span className="font-bold text-slate-800">{rp(saldoNow)}</span>
            </div>
            <div className="flex justify-between text-sm border-b border-slate-50 pb-2">
              <span className="text-slate-500">Target Nilai di Masa Depan</span>
              <span className="font-bold text-indigo-600">{rp(nilaiFuture)}</span>
            </div>
            <div className="flex justify-between text-sm border-b border-slate-50 pb-2">
              <span className="text-slate-500">Kontribusi Bulanan</span>
              <span className="font-bold text-slate-800">{tabungan?.kontribusi_bulanan ? rp(tabungan.kontribusi_bulanan) : "—"}</span>
            </div>
            <div className="flex justify-between text-sm border-b border-slate-50 pb-2">
              <span className="text-slate-500">Expected Return / Tahun</span>
              <span className="font-bold text-emerald-600">{tabungan?.return_tahunan ?? "—"}</span>
            </div>
          </div>
        </div>
        <div className="card">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Kebutuhan saat Pensiun</h2>
          <div className="space-y-3">
            <div className="flex justify-between text-sm border-b border-slate-50 pb-2">
              <span className="text-slate-500">Gaji / Pengeluaran saat Pensiun</span>
              <span className="font-bold text-slate-800">{gaji ? rp(gaji) : "—"} / bln</span>
            </div>
            <div className="flex justify-between text-sm border-b border-slate-50 pb-2">
              <span className="text-slate-500">Kebutuhan Setahun</span>
              <span className="font-bold text-slate-800">{gaji ? rp(gaji * 12) : "—"}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Dana agar cukup 20 tahun</span>
              <span className="font-bold text-amber-600">{gaji ? rp(gaji * 12 * 20) : "—"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Proyeksi Chart */}
      {proyeksiData.length > 1 && saldoNow > 0 && (
        <div className="card">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Proyeksi Pertumbuhan Tabungan</h2>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={proyeksiData}>
              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="tahun" tick={{ fontSize: 11, fill: "#94a3b8" }} />
              <YAxis tickFormatter={rpShort} tick={{ fontSize: 10, fill: "#94a3b8" }} width={60} />
              <Tooltip
                formatter={(v: number) => rp(v)}
                contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 12 }}
              />
              <Area type="monotone" dataKey="nilai" stroke="#6366f1" strokeWidth={2} fill="url(#areaGrad)" name="Estimasi Nilai" />
            </AreaChart>
          </ResponsiveContainer>
          <p className="text-xs text-slate-400 mt-2 text-center">* Proyeksi berdasarkan asumsi return {(growthRate * 100).toFixed(0)}% per tahun</p>
        </div>
      )}
    </div>
  );
}
