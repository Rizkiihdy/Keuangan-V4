import {
  LayoutDashboard,
  ArrowLeftRight,
  PieChart,
  TrendingUp,
  Target,
  Home,
  Clock,
  Car,
  CreditCard,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import type { Page } from "../App";

interface NavItem {
  id: Page;
  label: string;
  icon: React.ReactNode;
  group?: string;
}

const NAV: NavItem[] = [
  { id: "overview", label: "Beranda", icon: <LayoutDashboard size={18} />, group: "Keuangan Harian" },
  { id: "transaksi", label: "Transaksi", icon: <ArrowLeftRight size={18} />, group: "Keuangan Harian" },
  { id: "anggaran", label: "Anggaran", icon: <PieChart size={18} />, group: "Keuangan Harian" },
  { id: "investasi", label: "Investasi", icon: <TrendingUp size={18} />, group: "Portofolio" },
  { id: "goals", label: "Target Tabungan", icon: <Target size={18} />, group: "Portofolio" },
  { id: "rumah", label: "Kalk. Rumah", icon: <Home size={18} />, group: "Kalkulator" },
  { id: "pensiun", label: "Kalk. Pensiun", icon: <Clock size={18} />, group: "Kalkulator" },
  { id: "kredit", label: "Simulasi Kredit", icon: <Car size={18} />, group: "Kalkulator" },
  { id: "utang", label: "Kalk. Utang", icon: <CreditCard size={18} />, group: "Kalkulator" },
];

const GROUPS = ["Keuangan Harian", "Portofolio", "Kalkulator"];

interface Props {
  currentPage: Page;
  onNavigate: (p: Page) => void;
  isOpen: boolean;
  onToggle: () => void;
}

export default function Sidebar({ currentPage, onNavigate, isOpen, onToggle }: Props) {
  return (
    <aside
      className="flex-shrink-0 flex flex-col transition-all duration-300 overflow-hidden"
      style={{
        width: isOpen ? 230 : 64,
        background: "#0f172a",
        minHeight: "100vh",
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-800">
        <div
          className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center text-lg font-bold"
          style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}
        >
          💰
        </div>
        {isOpen && (
          <div className="overflow-hidden">
            <p className="text-white font-bold text-sm leading-tight">Oliv</p>
            <p className="text-slate-400 text-xs">Keuangan Pribadi</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 overflow-y-auto">
        {GROUPS.map((group) => {
          const items = NAV.filter((n) => n.group === group);
          return (
            <div key={group} className="mb-4">
              {isOpen && (
                <p className="text-xs font-semibold text-slate-600 uppercase tracking-widest px-3 mb-1">
                  {group}
                </p>
              )}
              {items.map((item) => (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  className={`sidebar-item w-full mb-0.5 ${currentPage === item.id ? "active" : ""}`}
                  title={!isOpen ? item.label : undefined}
                >
                  <span className="flex-shrink-0">{item.icon}</span>
                  {isOpen && <span className="truncate">{item.label}</span>}
                </button>
              ))}
            </div>
          );
        })}
      </nav>

      {/* Toggle */}
      <button
        onClick={onToggle}
        className="flex items-center justify-center h-10 w-10 mx-auto mb-4 rounded-xl text-slate-500 hover:text-white hover:bg-slate-700 transition-colors"
      >
        {isOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
      </button>
    </aside>
  );
}
