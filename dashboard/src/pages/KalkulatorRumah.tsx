import { useEffect, useState } from "react";
import { Home, TrendingUp, Wallet, CreditCard } from "lucide-react";
import Spinner, { ErrorBox } from "../components/Spinner";
import { api } from "../api/client";

function rp(n: number) {
  return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(n);
}

interface InfoRow { label: string; value: string; sub?: string; color?: string; icon: React.ReactNode }

function InfoCard({ label, value, sub, icon, color = "#6366f1" }: InfoRow) {
  return (
    <div className="card flex items-start gap-4">
      <div className="p-3 rounded-xl flex-shrink-0" style={{ background: color + "18" }}>
        <span style={{ color }}>{icon}</span>
      </div>
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wide font-medium">{label}</p>
        <p className="text-xl font-bold text-slate-800 mt-0.5">{value}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

export default function KalkulatorRumah() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.kalkRumah()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorBox msg={error} />;

  const penghasilan = data?.penghasilan_tahunan ?? 0;
  const hargaRumah = data?.harga_rumah_estimasi ?? 0;
  const cicilanMaks = data?.cicilan_maks ?? 0;
  const pctMaks = data?.pct_maks ?? "—";

  const rasio = penghasilan > 0 && hargaRumah > 0
    ? ((hargaRumah / penghasilan) * 100).toFixed(0)
    : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Kalkulator Kemampuan Beli Rumah</h1>
        <p className="text-slate-500 text-sm mt-1">Berdasarkan data di Google Sheet — Kalkulator Kemampuan Membeli Rumah</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <InfoCard
          label="Penghasilan Kotor per Tahun"
          value={rp(penghasilan)}
          sub={`= ${rp(penghasilan / 12)} / bulan`}
          icon={<Wallet size={22} />}
          color="#10b981"
        />
        <InfoCard
          label="Estimasi Harga Rumah"
          value={rp(hargaRumah)}
          sub="Berdasarkan DTI dan penghasilan"
          icon={<Home size={22} />}
          color="#6366f1"
        />
        <InfoCard
          label="Maksimum Cicilan per Bulan"
          value={rp(cicilanMaks)}
          sub={`Persentase maks: ${pctMaks}`}
          icon={<CreditCard size={22} />}
          color="#f59e0b"
        />
        <InfoCard
          label="Rasio Harga / Penghasilan Tahunan"
          value={rasio ? `${rasio}%` : "—"}
          sub="Idealnya < 500% (5x gaji tahunan)"
          icon={<TrendingUp size={22} />}
          color={rasio && Number(rasio) < 500 ? "#10b981" : "#ef4444"}
        />
      </div>

      {/* Affordability Meter */}
      {penghasilan > 0 && hargaRumah > 0 && (
        <div className="card">
          <h2 className="text-base font-semibold text-slate-700 mb-4">Indikator Keterjangkauan</h2>
          <div className="space-y-4">
            {/* Cicilan vs Penghasilan */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-600 font-medium">Cicilan vs Penghasilan Bulanan</span>
                <span className="font-bold text-slate-800">
                  {penghasilan > 0 ? ((cicilanMaks / (penghasilan / 12)) * 100).toFixed(0) : 0}%
                </span>
              </div>
              <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-indigo-500"
                  style={{ width: `${Math.min((cicilanMaks / (penghasilan / 12)) * 100, 100)}%` }}
                />
              </div>
              <p className="text-xs text-slate-400 mt-1">Batas aman: maks 30% dari penghasilan bulanan</p>
            </div>
          </div>
        </div>
      )}

      {/* Tips Box */}
      <div className="rounded-2xl border border-indigo-100 bg-indigo-50 p-5">
        <h3 className="font-semibold text-indigo-800 mb-2">💡 Tips Beli Rumah</h3>
        <ul className="space-y-1 text-sm text-indigo-700">
          <li>• DP minimal 20–30% dari harga rumah agar cicilan ringan</li>
          <li>• Cicilan sebaiknya tidak melebihi 30% dari penghasilan bersih</li>
          <li>• Siapkan dana darurat 3–6 bulan pengeluaran sebelum beli rumah</li>
          <li>• Perhatikan biaya tambahan: notaris, BPHTB, biaya KPR ±5–10% dari harga</li>
        </ul>
      </div>
    </div>
  );
}
