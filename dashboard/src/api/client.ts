async function api<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  return res.json();
}

export const fetchOverview = () => api<any>("/api/overview");
export const fetchAkun = () => api<any>("/api/akun");
export const fetchTransaksi = () => api<any>("/api/transaksi");
export const fetchBudget = () => api<any>("/api/budget");
export const fetchGoals = () => api<any>("/api/goals");
export const fetchCashflow = () => api<any>("/api/cashflow");
export const fetchInsightData = () => api<any>("/api/insight");
export const fetchAiInsight = () => api<any>("/api/ai-insight");
export const fetchActivity = () => api<any>("/api/activity");

export function formatRp(n: number, compact = false): string {
  if (!n && n !== 0) return "Rp0";
  const neg = n < 0;
  const abs = Math.abs(n);
  let s: string;
  if (compact) {
    if (abs >= 1_000_000_000) s = (abs / 1_000_000_000).toFixed(1) + "M";
    else if (abs >= 1_000_000) s = (abs / 1_000_000).toFixed(1) + "jt";
    else if (abs >= 1_000) s = (abs / 1_000).toFixed(0) + "rb";
    else s = String(abs);
  } else {
    s = abs.toLocaleString("id-ID");
  }
  return `${neg ? "-" : ""}Rp${s}`;
}

export function formatDate(iso: string): string {
  if (!iso) return "-";
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
}

export function scoreLabel(score: number): { label: string; color: string; emoji: string } {
  if (score >= 80) return { label: "Excellent", color: "#10b981", emoji: "🟢" };
  if (score >= 60) return { label: "Good", color: "#3b82f6", emoji: "🟢" };
  if (score >= 40) return { label: "Warning", color: "#f59e0b", emoji: "🟡" };
  return { label: "Critical", color: "#ef4444", emoji: "🔴" };
}

export const MOTIVASI = [
  "Hari ini kamu selangkah lebih dekat menuju Financial Freedom. 💪",
  "Konsisten lebih penting daripada sempurna. Terus catat! 📝",
  "Setiap rupiah yang kamu investasikan hari ini bekerja untuk masa depanmu. 🌱",
  "Anggaran bukan tentang batasan — ini tentang kebebasan. 🎯",
  "Financial freedom dimulai dari satu kebiasaan baik hari ini. ✨",
  "Uang yang dicatat adalah uang yang dikendalikan. 💡",
  "Saving 20% hari ini = 100% ketenangan di masa depan. 🏦",
  "Kekayaan sejati dimulai dari disiplin keuangan sehari-hari. 🌟",
];
