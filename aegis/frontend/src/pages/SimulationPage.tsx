import { useState } from "react";
import { Panel } from "../components/ui/Panel";
import { Button } from "../components/ui/Button";
import { SimulationCanvas } from "../simulation/SimulationCanvas";
import { api, ApiError } from "../services/api";
import type { EnvironmentInfo, EnvironmentPreset, RobotTelemetry, SensorFrame } from "../types";

interface SimulationPageProps {
  env: EnvironmentInfo | null;
  telemetry: RobotTelemetry | null;
  sensors: SensorFrame | null;
  refreshEnvironment: () => void;
}

const PRESETS: { id: EnvironmentPreset; label: string }[] = [
  { id: "open_field", label: "Open Field" },
  { id: "warehouse", label: "Warehouse" },
  { id: "maze", label: "Maze" },
  { id: "urban_grid", label: "Urban Grid" },
];

const SPEEDS = [0.25, 0.5, 1, 2, 5];

export function SimulationPage({ env, telemetry, sensors, refreshEnvironment }: SimulationPageProps) {
  const [obstacleRadius, setObstacleRadius] = useState(0.7);
  const [speed, setSpeed] = useState(1);
  const [error, setError] = useState<string | null>(null);

  const setPreset = async (preset: EnvironmentPreset) => {
    try {
      await api.setEnvironment(preset);
      refreshEnvironment();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to change environment.");
    }
  };

  const placeObstacle = async (x: number, y: number) => {
    try {
      await api.addObstacle(x, y, obstacleRadius);
      refreshEnvironment();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to add obstacle.");
    }
  };

  const setSimSpeed = async (mult: number) => {
    setSpeed(mult);
    try {
      await api.setSpeed(mult);
    } catch {
      /* non-fatal */
    }
  };

  return (
    <div className="grid h-full grid-cols-1 gap-3 lg:grid-cols-[1fr_320px]">
      <Panel eyebrow="Simulation" title="Environment" className="min-h-[420px] flex-1" noPadding>
        <SimulationCanvas
          env={env}
          telemetry={telemetry}
          sensors={sensors}
          plannedPath={[]}
          destination={null}
          onMapClick={placeObstacle}
        />
      </Panel>

      <div className="flex flex-col gap-3">
        {error && (
          <div className="rounded border px-2 py-1 text-xs" style={{ borderColor: "var(--color-status-fault)", color: "var(--color-status-fault)" }}>
            {error}
          </div>
        )}
        <Panel eyebrow="Presets" title="Environment Layout">
          <div className="grid grid-cols-2 gap-2">
            {PRESETS.map((p) => (
              <Button key={p.id} onClick={() => setPreset(p.id)} className="w-full">
                {p.label}
              </Button>
            ))}
          </div>
        </Panel>

        <Panel eyebrow="Obstacles" title="Place Obstacle">
          <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
            Click the map to place a dynamic obstacle at that point.
          </div>
          <label className="mt-3 flex flex-col gap-1 text-xs">
            <span style={{ color: "var(--color-text-tertiary)" }}>
              Radius <span className="tabular-mono" style={{ color: "var(--color-text-primary)" }}>{obstacleRadius.toFixed(1)} m</span>
            </span>
            <input
              type="range"
              min={0.3}
              max={2}
              step={0.1}
              value={obstacleRadius}
              onChange={(e) => setObstacleRadius(parseFloat(e.target.value))}
            />
          </label>
        </Panel>

        <Panel eyebrow="Simulation Speed">
          <div className="flex gap-2">
            {SPEEDS.map((s) => (
              <button
                key={s}
                onClick={() => setSimSpeed(s)}
                className="flex-1 rounded border py-1.5 text-xs tabular-mono"
                style={{
                  borderColor: speed === s ? "var(--color-status-nav)" : "var(--color-line-strong)",
                  color: speed === s ? "var(--color-status-nav)" : "var(--color-text-secondary)",
                  background: speed === s ? "var(--color-status-nav-dim)" : "transparent",
                }}
              >
                {s}x
              </button>
            ))}
          </div>
        </Panel>

        <Panel eyebrow="Environment Stats">
          <div className="tabular-mono text-xs" style={{ color: "var(--color-text-secondary)" }}>
            {env ? (
              <>
                {env.width_m}m × {env.height_m}m grid · cell {env.cell_size_m}m<br />
                {env.obstacles.length} obstacles ({env.obstacles.filter((o) => o.dynamic).length} dynamic)
              </>
            ) : (
              "Loading…"
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}
