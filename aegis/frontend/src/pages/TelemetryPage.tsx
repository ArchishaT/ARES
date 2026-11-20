import { Panel } from "../components/ui/Panel";
import { TelemetryChart } from "../telemetry/TelemetryChart";
import { TelemetryCard } from "../components/TelemetryCard";
import type { RobotTelemetry } from "../types";

interface TelemetryPageProps {
  history: { t: number; velocity: number; heading: number; battery: number; nearestObstacle: number }[];
  telemetry: RobotTelemetry | null;
}

export function TelemetryPage({ history, telemetry }: TelemetryPageProps) {
  return (
    <div className="flex h-full flex-col gap-3">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <TelemetryCard label="Velocity" value={telemetry ? telemetry.velocity_mps.toFixed(2) : "—"} unit="m/s" />
        <TelemetryCard label="Heading" value={telemetry ? telemetry.heading_deg.toFixed(0) : "—"} unit="°" tone="online" />
        <TelemetryCard
          label="Battery"
          value={telemetry ? telemetry.battery_pct.toFixed(0) : "—"}
          unit="%"
          tone={telemetry && telemetry.battery_pct < 20 ? "warn" : "default"}
        />
        <TelemetryCard
          label="Nearest Obstacle"
          value={history.length ? history[history.length - 1].nearestObstacle.toFixed(2) : "—"}
          unit="m"
        />
      </div>

      <div className="grid flex-1 grid-cols-1 gap-3 lg:grid-cols-2">
        <Panel eyebrow="Live Chart" title="Velocity (m/s)">
          <TelemetryChart data={history} dataKey="velocity" color="var(--color-status-nav)" unit="m/s" />
        </Panel>
        <Panel eyebrow="Live Chart" title="Battery (%)">
          <TelemetryChart data={history} dataKey="battery" color="var(--color-status-online)" unit="%" />
        </Panel>
        <Panel eyebrow="Live Chart" title="Heading (°)">
          <TelemetryChart data={history} dataKey="heading" color="var(--color-status-warn)" unit="°" />
        </Panel>
        <Panel eyebrow="Live Chart" title="Nearest Obstacle Distance (m)">
          <TelemetryChart data={history} dataKey="nearestObstacle" color="var(--color-status-fault)" unit="m" />
        </Panel>
      </div>
    </div>
  );
}
