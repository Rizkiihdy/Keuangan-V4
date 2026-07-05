import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Overview from "./pages/Overview";
import Transaksi from "./pages/Transaksi";
import Anggaran from "./pages/Anggaran";
import Investasi from "./pages/Investasi";
import Goals from "./pages/Goals";
import KalkulatorRumah from "./pages/KalkulatorRumah";
import KalkulatorPensiun from "./pages/KalkulatorPensiun";
import SimulasiKredit from "./pages/SimulasiKredit";
import KalkulatorUtang from "./pages/KalkulatorUtang";

export type Page =
  | "overview"
  | "transaksi"
  | "anggaran"
  | "investasi"
  | "goals"
  | "rumah"
  | "pensiun"
  | "kredit"
  | "utang";

export default function App() {
  const [page, setPage] = useState<Page>("overview");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const renderPage = () => {
    switch (page) {
      case "overview": return <Overview />;
      case "transaksi": return <Transaksi />;
      case "anggaran": return <Anggaran />;
      case "investasi": return <Investasi />;
      case "goals": return <Goals />;
      case "rumah": return <KalkulatorRumah />;
      case "pensiun": return <KalkulatorPensiun />;
      case "kredit": return <SimulasiKredit />;
      case "utang": return <KalkulatorUtang />;
      default: return <Overview />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar
        currentPage={page}
        onNavigate={setPage}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      <main
        className="flex-1 overflow-y-auto transition-all duration-300"
        style={{ marginLeft: sidebarOpen ? 0 : 0 }}
      >
        <div className="p-6 md:p-8 max-w-7xl mx-auto">
          {renderPage()}
        </div>
      </main>
    </div>
  );
}
