import type { RobotTelemetry } from "../types";
import { STATE_LABELS } from "../utils/format";
import { StatusBadge } from "./ui/StatusBadge";

interface RobotStatusProps {
  telemetry: RobotTelemetry | null;
}

export function RobotStatus({ telemetry }: RobotStatusProps) {
  if (!telemetry) {
    return <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>Awaiting telemetry…</div>;
  }

  const tone =
    telemetry.state === "EMERGENCY_STOP" || telemetry.state === "FAULT"
      ? "fault"
      : telemetry.state === "OBSTACLE_DETECTED" || telemetry.state === "REPLANNING"
      ? "warn"
      : telemetry.state === "NAVIGATING" || telemetry.state === "MISSION_COMPLETE"
      ? "online"
      : "idle";

  return (
    <div className="flex flex-col gap-3">
      <StatusBadge label={STATE_LABELS[telemetry.state]} tone={tone as any} pulse={telemetry.state === "REPLANNING"} />
      <div className="grid grid-cols-3 gap-2 tabular-mono text-sm">
        <div>
          <div className="text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>X</div>
          <div style={{ color: "var(--color-text-primary)" }}>{telemetry.x.toFixed(2)} m</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>Y</div>
          <div style={{ color: "var(--color-text-primary)" }}>{telemetry.y.toFixed(2)} m</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>HEADING</div>
          <div style={{ color: "var(--color-status-nav)" }}>{telemetry.heading_deg.toFixed(0)}°</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>VELOCITY</div>
          <div style={{ color: "var(--color-text-primary)" }}>{telemetry.velocity_mps.toFixed(2)} m/s</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>WAYPOINT</div>
          <div style={{ color: "var(--color-text-primary)" }}>
            {telemetry.current_waypoint_index}/{telemetry.total_waypoints}
          </div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>BATTERY</div>
          <div style={{ color: telemetry.battery_pct < 20 ? "var(--color-status-warn)" : "var(--color-status-online)" }}>
            {telemetry.battery_pct.toFixed(0)}%
          </div>
        </div>
      </div>
    </div>
  );
}
