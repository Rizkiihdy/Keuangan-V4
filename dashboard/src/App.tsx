import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Overview from "./pages/Overview";
import Transaksi from "./pages/Transaksi";
import Anggaran from "./pages/Anggaran";
import Tabungan from "./pages/Tabungan";
import Insight from "./pages/Insight";

export type Page = "overview" | "transaksi" | "anggaran" | "tabungan" | "insight";

const PAGE_TITLES: Record<Page, string> = {
  overview: "Ringkasan Keuangan",
  transaksi: "Riwayat Transaksi",
  anggaran: "Anggaran Bulanan",
  tabungan: "Target Tabungan",
  insight: "Insight & Analisis",
};

export default function App() {
  const [page, setPage] = useState<Page>("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const renderPage = () => {
    switch (page) {
      case "overview": return <Overview />;
      case "transaksi": return <Transaksi />;
      case "anggaran": return <Anggaran />;
      case "tabungan": return <Tabungan />;
      case "insight": return <Insight />;
      default: return <Overview />;
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Sidebar
        currentPage={page}
        onNavigate={(p) => { setPage(p); setSidebarOpen(false); }}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3 shrink-0">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden p-2 rounded-lg hover:bg-slate-100 text-slate-500"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12h18M3 6h18M3 18h18" />
            </svg>
          </button>
          <div>
            <h1 className="text-lg font-semibold text-slate-800">{PAGE_TITLES[page]}</h1>
            <p className="text-xs text-slate-400 hidden sm:block">Oliv — Keuangan Pribadi</p>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}
