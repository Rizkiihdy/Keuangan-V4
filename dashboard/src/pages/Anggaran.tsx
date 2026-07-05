import { useEffect, useState } from "react";
import { fetchBudget, formatRp } from "../api/client";
import { Spinner } from "../components/Spinner";

function BudgetRow({ item }: { item: any }) {
  const pct = item.budget_bulan > 0 ? Math.min(Math.round((item.aktual / item.budget_bulan) * 100), 120) : 0;
  const over = item.aktual > item.budget_bulan && item.budget_bulan > 0;
  const warn = pct >= 80 && !over;
  const color = over ? "#ef4444" : warn ? "#f59e0b" : "#10b981";

  return (
    <div className="p-4 rounded-xl transition-all hover:scale-[1.01]" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
      <div className="flex justify-between items-center mb-2">
        <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{item.nama}</p>
        {over && <span className="badge text-xs" style={{ background: "#ef444420", color: "#f87171" }}>⚠ Over</span>}
        {warn && <span className="badge text-xs" style={{ background: "#f59e0b20", color: "#fbbf24" }}>⚡ Hampir</span>}
        {!over && !warn && item.budget_bulan > 0 && <span className="badge text-xs" style={{ background: "#10b98120", color: "#34d399" }}>✓ Aman</span>}
      </div>
      {item.budget_bulan > 0 ? (
        <>
          <div className="flex justify-between text-xs mb-2" style={{ color: "var(--text-muted)" }}>
            <span>Terpakai: {formatRp(item.aktual, true)}</span>
            <span>Budget: {formatRp(item.budget_bulan, true)}</span>
          </div>
          <div className="progress-bar">
            <div className="h-full rounded-full transition-all duration-700" style={{ width: `${Math.min(pct, 100)}%`, background: color }} />
          </div>
          <div className="flex justify-between text-xs mt-1.5">
            <span style={{ color }}>{pct}%</span>
            <span style={{ color: "var(--text-muted)" }}>Sisa: {formatRp(Math.max(0, item.sisa), true)}</span>
          </div>
        </>
      ) : (
        <div className="flex justify-between text-xs" style={{ color: "var(--text-muted)" }}>
          <span>Total: {formatRp(item.aktual, true)}</span>
          <span>Budget belum diset</span>
        </div>
      )}
    </div>
  );
}

export default function Anggaran() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"expense" | "income">("expense");

  useEffect(() => {
    fetchBudget().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (!data) return <p className="text-center py-10 text-sm" style={{ color: "var(--text-muted)" }}>Gagal memuat</p>;

  const overCount = data.expense.filter((i: any) => i.aktual > i.budget_bulan && i.budget_bulan > 0).length;
  const warnCount = data.expense.filter((i: any) => {
    const p = i.budget_bulan > 0 ? i.aktual / i.budget_bulan * 100 : 0;
    return p >= 80 && p < 100;
  }).length;

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-5">
      {/* Summary badges */}
      <div className="flex gap-3 flex-wrap">
        {overCount > 0 && (
          <div className="px-4 py-2 rounded-xl text-sm font-medium" style={{ background: "#ef444420", color: "#f87171" }}>
            ⚠️ {overCount} kategori melebihi budget
          </div>
        )}
        {warnCount > 0 && (
          <div className="px-4 py-2 rounded-xl text-sm font-medium" style={{ background: "#f59e0b20", color: "#fbbf24" }}>
            ⚡ {warnCount} kategori hampir habis
          </div>
        )}
        {overCount === 0 && warnCount === 0 && (
          <div className="px-4 py-2 rounded-xl text-sm font-medium" style={{ background: "#10b98120", color: "#34d399" }}>
            ✅ Semua budget aman — {data.bulan}
          </div>
        )}
      </div>

      {/* Tab */}
      <div className="flex gap-2">
        {[
          { k: "expense", label: "📤 Pengeluaran" },
          { k: "income", label: "📥 Pendapatan" },
        ].map(t => (
          <button key={t.k} onClick={() => setTab(t.k as any)}
            className="px-4 py-2 rounded-xl text-sm font-semibold transition-all"
            style={tab === t.k
              ? { background: "linear-gradient(135deg,#3b82f6,#6366f1)", color: "white" }
              : { background: "var(--bg-card)", color: "var(--text-secondary)", border: "1px solid var(--border)" }}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {(tab === "expense" ? data.expense : data.income).map((item: any) => (
          <BudgetRow key={item.nama} item={item} />
        ))}
        {(tab === "expense" ? data.expense : data.income).length === 0 && (
          <p className="col-span-3 text-center py-10 text-sm" style={{ color: "var(--text-muted)" }}>Tidak ada data budget</p>
        )}
      </div>
    </div>
  );
}
