import { useState } from "react";
import { Panel } from "../components/ui/Panel";
import { SimulationCanvas } from "../simulation/SimulationCanvas";
import { RobotStatus } from "../components/RobotStatus";
import { MissionControls } from "../components/MissionControls";
import { NavigationPanel } from "../components/NavigationPanel";
import { EmergencyStop } from "../components/EmergencyStop";
import { EventLog } from "../components/EventLog";
import { api, ApiError } from "../services/api";
import type { EnvironmentInfo, LogEntry, PathPlanResult, RobotTelemetry, SensorFrame, WorldPoint } from "../types";

interface MissionControlPageProps {
  env: EnvironmentInfo | null;
  telemetry: RobotTelemetry | null;
  sensors: SensorFrame | null;
  logs: LogEntry[];
  refreshEnvironment: () => void;
  plan: PathPlanResult | null;
  onPlanChange: (p: PathPlanResult | null) => void;
}

export function MissionControlPage({ env, telemetry, sensors, logs, refreshEnvironment, plan, onPlanChange }: MissionControlPageProps) {
  const [destination, setDestination] = useState<WorldPoint | null>(null);
  const [error, setError] = useState<string | null>(null);
  const setPlan = onPlanChange;

  const handleMapClick = async (x: number, y: number) => {
    setDestination({ x, y });
    setPlan(null);
    try {
      await api.setDestination(x, y);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to set destination.");
    }
  };

  return (
    <div className="grid h-full grid-cols-1 gap-3 lg:grid-cols-[1fr_360px]">
      <div className="flex flex-col gap-3">
        <Panel eyebrow="Main Simulation View" title="Environment Map" className="min-h-[420px] flex-1" noPadding>
          <SimulationCanvas
            env={env}
            telemetry={telemetry}
            sensors={sensors}
            plannedPath={plan?.waypoints ?? []}
            destination={destination}
            onMapClick={handleMapClick}
          />
        </Panel>
        <Panel eyebrow="Mission" title="Mission Controls">
          {error && (
            <div className="mb-2 rounded border px-2 py-1 text-xs" style={{ borderColor: "var(--color-status-fault)", color: "var(--color-status-fault)" }}>
              {error}
            </div>
          )}
          <MissionControls
            telemetry={telemetry}
            hasDestination={!!destination}
            plan={plan}
            onPlanned={setPlan}
            onError={setError}
            refreshEnvironment={() => {
              setDestination(null);
              setPlan(null);
              refreshEnvironment();
            }}
          />
        </Panel>
      </div>

      <div className="flex flex-col gap-3">
        <Panel eyebrow="Rover" title="Robot Status">
          <RobotStatus telemetry={telemetry} />
        </Panel>
        <Panel eyebrow="Navigation">
          <NavigationPanel plan={plan} />
        </Panel>
        <Panel>
          <EmergencyStop state={telemetry?.state ?? "IDLE"} onError={setError} />
        </Panel>
        <Panel eyebrow="Recent Activity" title="Event Log" className="min-h-[160px] flex-1">
          <EventLog logs={logs} compact />
        </Panel>
      </div>
    </div>
  );
}
