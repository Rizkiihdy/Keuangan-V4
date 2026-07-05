const API_BASE = "";

async function api<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const fetchOverview = () => api<any>("/api/overview");
export const fetchTransaksi = () => api<any>("/api/transaksi");
export const fetchAkun = () => api<any>("/api/akun");
export const fetchGoals = () => api<any>("/api/goals");
export const fetchBudget = () => api<any>("/api/budget");
export const fetchInsight = () => api<any>("/api/insight");

export function formatRp(n: number): string {
  if (!n && n !== 0) return "-";
  const neg = n < 0;
  const abs = Math.abs(n);
  const s = abs.toLocaleString("id-ID");
  return `${neg ? "-" : ""}Rp${s}`;
}

export function formatDate(iso: string): string {
  if (!iso) return "-";
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("id-ID", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}
