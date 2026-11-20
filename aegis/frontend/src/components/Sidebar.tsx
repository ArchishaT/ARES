import {
  Activity,
  AlertTriangle,
  Compass,
  Gauge,
  LayoutGrid,
  ListTree,
  Radar,
  Settings,
  ScanEye,
  ShieldAlert,
  Swords,
} from "lucide-react";
import type { NavSection } from "../types";

interface SidebarProps {
  active: NavSection;
  onSelect: (s: NavSection) => void;
}

const ITEMS: { id: NavSection; label: string; icon: React.ElementType }[] = [
  { id: "mission", label: "Mission Control", icon: LayoutGrid },
  { id: "simulation", label: "Simulation", icon: Gauge },
  { id: "navigation", label: "Navigation", icon: Compass },
  { id: "sensors", label: "Sensors", icon: Radar },
  { id: "vision", label: "Vision", icon: ScanEye },
  { id: "telemetry", label: "Telemetry", icon: Activity },
  { id: "log", label: "Event Log", icon: ListTree },
  { id: "diagnostics", label: "Diagnostics", icon: AlertTriangle },
  { id: "security", label: "Security (ARES)", icon: ShieldAlert },
  { id: "cyberrange", label: "Cyber Range", icon: Swords },
  { id: "settings", label: "Settings", icon: Settings },
];

export function Sidebar({ active, onSelect }: SidebarProps) {
  return (
    <nav
      className="flex w-16 shrink-0 flex-col items-center gap-1 border-r py-3 md:w-48 md:items-stretch md:px-2"
      style={{ background: "var(--color-bg-base)", borderColor: "var(--color-line)" }}
    >
      {ITEMS.map(({ id, label, icon: Icon }) => {
        const isActive = active === id;
        return (
          <button
            key={id}
            onClick={() => onSelect(id)}
            title={label}
            className="group flex items-center gap-3 rounded px-3 py-2 text-left text-xs transition-colors"
            style={{
              background: isActive ? "var(--color-bg-panel-raised)" : "transparent",
              color: isActive ? "var(--color-status-nav)" : "var(--color-text-secondary)",
              borderLeft: isActive ? "2px solid var(--color-status-nav)" : "2px solid transparent",
            }}
          >
            <Icon size={16} />
            <span className="hidden md:inline">{label}</span>
          </button>
        );
      })}
    </nav>
  );
}
