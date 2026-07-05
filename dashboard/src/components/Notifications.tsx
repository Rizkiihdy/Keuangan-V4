export default function Notifications({ data }: { data: any }) {
  if (!data) return null;
  const notifs: { type: string; msg: string }[] = [];

  if (data.saving_rate < 10)
    notifs.push({ type: "danger", msg: `⚠️ Saving Rate hanya ${data.saving_rate}% — target minimal 20%` });
  if (data.cashflow_bulan < 0)
    notifs.push({ type: "danger", msg: `🔴 Cash Flow bulan ini negatif (${(data.cashflow_bulan / 1e6).toFixed(1)}jt)` });
  if (data.expense_ratio > 80)
    notifs.push({ type: "warning", msg: `🟡 Pengeluaran mencapai ${data.expense_ratio}% dari pemasukan` });
  if (data.financial_score < 40)
    notifs.push({ type: "danger", msg: `🔴 Financial Score rendah (${data.financial_score}/100)` });
  if (data.saving_rate >= 20 && data.cashflow_bulan > 0)
    notifs.push({ type: "success", msg: `🟢 Cash flow positif! Keuangan bulan ini sehat.` });

  if (!notifs.length) return null;

  const colors: Record<string, string> = {
    danger: "#ef444420",
    warning: "#f59e0b20",
    success: "#10b98120",
  };
  const borders: Record<string, string> = {
    danger: "#ef4444",
    warning: "#f59e0b",
    success: "#10b981",
  };

  return (
    <div className="space-y-2 mb-6">
      {notifs.map((n, i) => (
        <div key={i} className="px-4 py-3 rounded-xl text-sm font-medium"
          style={{ background: colors[n.type], borderLeft: `3px solid ${borders[n.type]}`, color: "var(--text-primary)" }}>
          {n.msg}
        </div>
      ))}
    </div>
  );
}
