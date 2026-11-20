import { useState } from "react";
import type { PathPlanResult, RobotTelemetry } from "../types";
import { Button } from "./ui/Button";
import { api, ApiError } from "../services/api";

interface MissionControlsProps {
  telemetry: RobotTelemetry | null;
  hasDestination: boolean;
  plan: PathPlanResult | null;
  onPlanned: (plan: PathPlanResult) => void;
  onError: (msg: string) => void;
  refreshEnvironment: () => void;
}

export function MissionControls({ telemetry, hasDestination, plan, onPlanned, onError, refreshEnvironment }: MissionControlsProps) {
  const [busy, setBusy] = useState(false);

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Request failed.");
    } finally {
      setBusy(false);
    }
  };

  const state = telemetry?.state ?? "IDLE";
const canPlan = hasDestination && (state === "IDLE" || state === "MISSION_COMPLETE" || state === "PLANNING");
const canStart = plan?.status === "ready" && (state === "IDLE" || state === "MISSION_COMPLETE" || state === "PLANNING");
  const canPause = state === "NAVIGATING";
  const canResume = state === "PAUSED";
  const canAbort = state === "NAVIGATING" || state === "PAUSED" || state === "REPLANNING" || state === "OBSTACLE_DETECTED";

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="primary"
        disabled={busy || !canPlan}
        onClick={() => run(async () => onPlanned(await api.planRoute()))}
      >
        Plan Route
      </Button>
      <Button
        variant="primary"
        disabled={busy || !canStart}
        onClick={() => run(() => api.startMission())}
      >
        Start Autonomous Mission
      </Button>
      <Button disabled={busy || !canPause} onClick={() => run(() => api.pauseMission())}>
        Pause
      </Button>
      <Button disabled={busy || !canResume} onClick={() => run(() => api.resumeMission())}>
        Resume
      </Button>
      <Button variant="danger" disabled={busy || !canAbort} onClick={() => run(() => api.abortMission())}>
        Abort
      </Button>
      <Button
        disabled={busy}
        onClick={() =>
          run(async () => {
            await api.resetSimulation();
            refreshEnvironment();
          })
        }
      >
        Reset Simulation
      </Button>
    </div>
  );
}
