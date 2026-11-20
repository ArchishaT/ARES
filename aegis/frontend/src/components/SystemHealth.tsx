import type { SystemHealth as SystemHealthType } from "../types";
import { StatusBadge } from "./ui/StatusBadge";

interface SystemHealthProps {
  health: SystemHealthType | null;
  wsConnected: boolean;
  fps: number;
}

export function SystemHealth({ health, wsConnected, fps }: SystemHealthProps) {
  if (!health) {
    return <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>Fetching diagnostics…</div>;
  }

  const systems: [string, string][] = [
    ["Simulation Engine", health.simulation_engine],
    ["Navigation", health.navigation],
    ["Sensor System", health.sensor_system],
    ["Vision", health.vision],
    ["WebSocket", wsConnected ? "ONLINE" : "OFFLINE"],
    ["Backend API", health.backend_api],
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {systems.map(([name, status]) => (
          <div
            key={name}
            className="flex items-center justify-between rounded border px-3 py-2"
            style={{ background: "var(--color-bg-inset)", borderColor: "var(--color-line)" }}
          >
            <span className="text-xs" style={{ color: "var(--color-text-secondary)" }}>{name}</span>
            <StatusBadge label={status} tone={status === "ONLINE" ? "online" : status === "IDLE" ? "idle" : "fault"} />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Metric label="Frontend FPS" value={fps.toFixed(0)} />
        <Metric label="Backend Latency" value={`${health.backend_latency_ms.toFixed(1)} ms`} />
        <Metric label="WS Latency" value={`${health.ws_latency_ms.toFixed(2)} ms`} />
        <Metric label="Tick Rate" value={`${health.simulation_tick_rate_hz.toFixed(0)} Hz`} />
        <Metric label="Active Connections" value={`${health.active_connections}`} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border px-3 py-2" style={{ background: "var(--color-bg-inset)", borderColor: "var(--color-line)" }}>
      <div className="text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>{label}</div>
      <div className="tabular-mono text-base" style={{ color: "var(--color-status-nav)" }}>{value}</div>
    </div>
  );
}
