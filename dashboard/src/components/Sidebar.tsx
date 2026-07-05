import type { Page } from "../App";

const ITEMS: { page: Page; label: string; icon: string }[] = [
  { page: "overview", label: "Beranda", icon: "📊" },
  { page: "transaksi", label: "Transaksi", icon: "📝" },
  { page: "anggaran", label: "Anggaran", icon: "💸" },
  { page: "tabungan", label: "Tabungan", icon: "🎯" },
  { page: "insight", label: "Insight", icon: "💡" },
];

export default function Sidebar({
  currentPage,
  onNavigate,
  isOpen,
  onToggle,
}: {
  currentPage: Page;
  onNavigate: (p: Page) => void;
  isOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-slate-900 text-white flex flex-col transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="p-5 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center text-xl font-bold">
              💰
            </div>
            <div>
              <h2 className="font-bold text-lg leading-tight">Oliv</h2>
              <p className="text-xs text-slate-400">Keuangan Pribadi</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {ITEMS.map((item) => (
            <button
              key={item.page}
              onClick={() => onNavigate(item.page)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                currentPage === item.page
                  ? "bg-emerald-600 text-white shadow-lg shadow-emerald-500/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-800"
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="bg-slate-800 rounded-xl p-3">
            <p className="text-xs text-slate-400">Data dari</p>
            <p className="text-sm font-medium text-slate-200">Google Sheets</p>
          </div>
        </div>
      </aside>
    </>
  );
}
