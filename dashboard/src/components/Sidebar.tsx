import type { Page } from "../App";

const NAV = [
  { page: "home" as Page, label: "Beranda", icon: "🏠" },
  { page: "transaksi" as Page, label: "Transaksi", icon: "📝" },
  { page: "anggaran" as Page, label: "Anggaran", icon: "💸" },
  { page: "tabungan" as Page, label: "Tabungan & Akun", icon: "🎯" },
  { page: "insight" as Page, label: "Insight & Laporan", icon: "💡" },
];

const QUICK_LINKS = [
  { label: "Laporan Bulanan", icon: "📄" },
  { label: "Dashboard Investasi", icon: "📈" },
  { label: "Kalkulator Rumah", icon: "🏠" },
  { label: "Simulasi Kredit", icon: "🚗" },
  { label: "Kalkulator Utang", icon: "💳" },
];

export default function Sidebar({ currentPage, onNavigate, isOpen, onToggle, darkMode, onToggleDark }: {
  currentPage: Page; onNavigate: (p: Page) => void;
  isOpen: boolean; onToggle: () => void;
  darkMode: boolean; onToggleDark: () => void;
}) {
  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 z-40 lg:hidden" style={{ background: "rgba(0,0,0,0.6)" }} onClick={onToggle} />
      )}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-60 flex flex-col transition-transform duration-300 ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
        style={{ background: "var(--bg-secondary)", borderRight: "1px solid var(--border)" }}>
        {/* Logo */}
        <div className="p-4 border-b" style={{ borderColor: "var(--border)" }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg font-bold"
              style={{ background: "linear-gradient(135deg, #3b82f6, #6366f1)" }}>
              💰
            </div>
            <div>
              <p className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>Oliv Finance</p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Keuangan Pribadi</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          <p className="text-xs font-semibold px-3 py-2 uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Menu</p>
          {NAV.map((item) => (
            <button key={item.page} onClick={() => onNavigate(item.page)}
              className={`sidebar-item w-full ${currentPage === item.page ? "active" : ""}`}>
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}

          <p className="text-xs font-semibold px-3 py-2 uppercase tracking-wider mt-4" style={{ color: "var(--text-muted)" }}>Akses Cepat</p>
          {QUICK_LINKS.map((l) => (
            <div key={l.label} className="sidebar-item opacity-50 cursor-not-allowed select-none">
              <span>{l.icon}</span>
              <span className="text-xs">{l.label}</span>
              <span className="ml-auto text-xs px-1.5 py-0.5 rounded-md" style={{ background: "var(--bg-card)", fontSize: "10px" }}>Soon</span>
            </div>
          ))}
        </nav>

        {/* Bottom */}
        <div className="p-3 border-t" style={{ borderColor: "var(--border)" }}>
          <div className="rounded-xl p-3" style={{ background: "var(--bg-card)" }}>
            <p className="text-xs font-medium mb-1" style={{ color: "var(--text-muted)" }}>Sumber Data</p>
            <p className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>📊 Google Sheets — keuangan v4</p>
          </div>
        </div>
      </aside>
    </>
  );
}
