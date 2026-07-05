import { useEffect, useState, useMemo } from "react";
import { fetchTransaksi, formatRp } from "../api/client";
import { Spinner } from "../components/Spinner";

const PAGE_SIZE = 25;

export default function Transaksi() {
  const [all, setAll] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("semua");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<any>(null);
  const [sortKey, setSortKey] = useState<"tanggal" | "jumlah">("tanggal");
  const [sortAsc, setSortAsc] = useState(false);

  useEffect(() => {
    fetchTransaksi().then(r => setAll(r.data || [])).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let d = [...all];
    if (filter !== "semua") d = d.filter(t => t.tipe === filter);
    if (search.trim()) {
      const q = search.toLowerCase();
      d = d.filter(t => t.memo?.toLowerCase().includes(q) || t.kategori?.toLowerCase().includes(q) || t.akun?.toLowerCase().includes(q));
    }
    d.sort((a, b) => {
      const diff = sortKey === "jumlah" ? a.jumlah - b.jumlah : a.tanggal.localeCompare(b.tanggal);
      return sortAsc ? diff : -diff;
    });
    return d;
  }, [all, filter, search, sortKey, sortAsc]);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const toggleSort = (key: "tanggal" | "jumlah") => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  const summary = useMemo(() => ({
    income: all.filter(t => t.tipe === "Pemasukan").reduce((s, t) => s + t.jumlah, 0),
    expense: all.filter(t => t.tipe === "Pengeluaran").reduce((s, t) => s + t.jumlah, 0),
  }), [all]);

  if (loading) return <Spinner />;

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-5">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total Pemasukan", val: summary.income, color: "#10b981", icon: "📥" },
          { label: "Total Pengeluaran", val: summary.expense, color: "#ef4444", icon: "📤" },
          { label: "Net Cash Flow", val: summary.income - summary.expense, color: summary.income >= summary.expense ? "#10b981" : "#ef4444", icon: "📊" },
        ].map(s => (
          <div key={s.label} className="card p-4">
            <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>{s.icon} {s.label}</p>
            <p className="font-bold text-base" style={{ color: s.color }}>{formatRp(s.val, true)}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
          placeholder="🔍 Cari memo, kategori, akun…" className="flex-1 min-w-48 text-sm" style={{ minWidth: 200 }} />
        <div className="flex gap-1">
          {[
            { k: "semua", label: "Semua" },
            { k: "Pengeluaran", label: "📤 Keluar" },
            { k: "Pemasukan", label: "📥 Masuk" },
            { k: "Transfer", label: "🔄 Transfer" },
          ].map(b => (
            <button key={b.k} onClick={() => { setFilter(b.k); setPage(1); }}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
              style={filter === b.k
                ? { background: "linear-gradient(135deg,#3b82f6,#6366f1)", color: "white" }
                : { background: "var(--bg-card)", color: "var(--text-secondary)", border: "1px solid var(--border)" }}>
              {b.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: "rgba(255,255,255,0.03)", borderBottom: "1px solid var(--border)" }}>
                <th className="text-left px-4 py-3 text-xs font-semibold cursor-pointer select-none"
                  style={{ color: "var(--text-muted)" }} onClick={() => toggleSort("tanggal")}>
                  Tanggal {sortKey === "tanggal" ? (sortAsc ? "↑" : "↓") : ""}
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold" style={{ color: "var(--text-muted)" }}>Akun</th>
                <th className="text-left px-4 py-3 text-xs font-semibold" style={{ color: "var(--text-muted)" }}>Memo</th>
                <th className="text-left px-4 py-3 text-xs font-semibold" style={{ color: "var(--text-muted)" }}>Kategori</th>
                <th className="text-left px-4 py-3 text-xs font-semibold" style={{ color: "var(--text-muted)" }}>Tipe</th>
                <th className="text-right px-4 py-3 text-xs font-semibold cursor-pointer select-none"
                  style={{ color: "var(--text-muted)" }} onClick={() => toggleSort("jumlah")}>
                  Jumlah {sortKey === "jumlah" ? (sortAsc ? "↑" : "↓") : ""}
                </th>
              </tr>
            </thead>
            <tbody>
              {paged.map((t, i) => (
                <tr key={i} onClick={() => setSelected(t)}
                  className="cursor-pointer transition-colors"
                  style={{ borderBottom: "1px solid var(--border)" }}
                  onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}
                  onMouseLeave={e => (e.currentTarget.style.background = "")}>
                  <td className="px-4 py-3 text-xs whitespace-nowrap" style={{ color: "var(--text-muted)" }}>{t.tanggal_fmt}</td>
                  <td className="px-4 py-3 text-xs font-medium" style={{ color: "var(--text-secondary)" }}>{t.akun}</td>
                  <td className="px-4 py-3 text-xs max-w-[180px] truncate" style={{ color: "var(--text-secondary)" }}>{t.memo || "—"}</td>
                  <td className="px-4 py-3">
                    <span className="badge text-xs" style={{ background: "rgba(99,102,241,0.12)", color: "#a5b4fc" }}>{t.kategori}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="badge text-xs" style={
                      t.tipe === "Pemasukan" ? { background: "#10b98120", color: "#34d399" } :
                      t.tipe === "Transfer" ? { background: "#3b82f620", color: "#93c5fd" } :
                      { background: "#ef444420", color: "#f87171" }
                    }>{t.tipe}</span>
                  </td>
                  <td className={`px-4 py-3 text-right text-xs font-bold whitespace-nowrap ${t.tipe === "Pemasukan" ? "text-emerald-400" : "text-red-400"}`}>
                    {t.tipe === "Pemasukan" ? "+" : "-"}{formatRp(t.jumlah, true)}
                  </td>
                </tr>
              ))}
              {paged.length === 0 && (
                <tr><td colSpan={6} className="text-center py-10 text-sm" style={{ color: "var(--text-muted)" }}>Tidak ada transaksi</td></tr>
              )}
            </tbody>
          </table>
        </div>
        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 text-xs" style={{ borderTop: "1px solid var(--border)", color: "var(--text-muted)" }}>
          <span>{filtered.length} transaksi · halaman {page} dari {totalPages}</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}
              className="px-3 py-1 rounded-lg disabled:opacity-30 transition-colors"
              style={{ background: "var(--bg-card)", color: "var(--text-secondary)" }}>← Prev</button>
            <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page >= totalPages}
              className="px-3 py-1 rounded-lg disabled:opacity-30 transition-colors"
              style={{ background: "var(--bg-card)", color: "var(--text-secondary)" }}>Next →</button>
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.7)" }}
          onClick={() => setSelected(null)}>
          <div className="w-full max-w-sm rounded-2xl p-6" style={{ background: "var(--bg-card)", border: "1px solid var(--border-light)" }}
            onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold" style={{ color: "var(--text-primary)" }}>Detail Transaksi</h3>
              <button onClick={() => setSelected(null)} className="text-xl" style={{ color: "var(--text-muted)" }}>✕</button>
            </div>
            {[
              ["Tanggal", selected.tanggal_fmt],
              ["Akun", selected.akun],
              ["Memo", selected.memo || "—"],
              ["Kategori", selected.kategori],
              ["Tipe", selected.tipe],
              ["Jumlah", formatRp(selected.jumlah)],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between py-2" style={{ borderBottom: "1px solid var(--border)" }}>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>{k}</span>
                <span className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
