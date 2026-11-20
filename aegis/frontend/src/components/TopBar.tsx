import type { RobotTelemetry } from "../types";
import { StatusBadge } from "./ui/StatusBadge";

interface TopBarProps {
  wsConnected: boolean;
  simTime: number;
  telemetry: RobotTelemetry | null;
}

function formatSimTime(t: number): string {
  const m = Math.floor(t / 60).toString().padStart(2, "0");
  const s = Math.floor(t % 60).toString().padStart(2, "0");
  const ms = Math.floor((t % 1) * 100).toString().padStart(2, "0");
  return `${m}:${s}.${ms}`;
}

export function TopBar({ wsConnected, simTime, telemetry }: TopBarProps) {
  return (
    <header
      className="flex h-14 shrink-0 items-center justify-between border-b px-4"
      style={{ background: "var(--color-bg-base)", borderColor: "var(--color-line)" }}
    >
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded border" style={{ borderColor: "var(--color-status-nav)" }}>
          <div className="h-2.5 w-2.5" style={{ background: "var(--color-status-nav)", clipPath: "polygon(50% 0%, 0% 100%, 100% 100%)" }} />
        </div>
        <div>
          <div className="text-sm font-bold tracking-widest">AEGIS</div>
          <div className="text-[9px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>
            Autonomous Robotics Command System
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden items-center gap-2 tabular-mono text-xs md:flex" style={{ color: "var(--color-text-secondary)" }}>
          <span style={{ color: "var(--color-text-tertiary)" }}>MISSION T+</span>
          {formatSimTime(simTime)}
        </div>
        <StatusBadge label={wsConnected ? "WS CONNECTED" : "WS OFFLINE"} tone={wsConnected ? "online" : "fault"} pulse={wsConnected} />
        <StatusBadge label="SYSTEM ONLINE" tone="online" />
        {telemetry && (
          <div
            className="hidden items-center gap-1.5 rounded border px-2 py-1 text-[11px] uppercase tracking-wide lg:flex"
            style={{ borderColor: "var(--color-line)", color: "var(--color-text-secondary)" }}
          >
            Mission: <span style={{ color: "var(--color-text-primary)" }}>{telemetry.state.replace(/_/g, " ")}</span>
          </div>
        )}
        <div
          className="flex h-7 w-7 items-center justify-center rounded-full border text-[10px] font-semibold"
          style={{ borderColor: "var(--color-line-strong)", color: "var(--color-text-secondary)" }}
        >
          OP
        </div>
      </div>
    </header>
  );
}
