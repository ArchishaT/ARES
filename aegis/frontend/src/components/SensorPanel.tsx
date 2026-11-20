import { useState } from "react";
import type { SensorFrame } from "../types";
import { api } from "../services/api";

interface SensorPanelProps {
  sensors: SensorFrame | null;
}

export function SensorPanel({ sensors }: SensorPanelProps) {
  const [range, setRange] = useState(8);
  const [rays, setRays] = useState(36);
  const [noise, setNoise] = useState(0.03);

  const applyConfig = async () => {
    await api.setLidarConfig(range, rays, noise);
  };

  if (!sensors) {
    return <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>Awaiting sensor data…</div>;
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="mb-2 text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>
          LiDAR
        </div>
        <div className="grid grid-cols-3 gap-3 text-xs">
          <SliderField label="Range" value={range} min={2} max={20} step={0.5} unit="m" onChange={setRange} />
          <SliderField label="Rays" value={rays} min={8} max={120} step={4} onChange={setRays} />
          <SliderField label="Noise σ" value={noise} min={0} max={0.3} step={0.01} onChange={setNoise} />
        </div>
        <button
          onClick={applyConfig}
          className="mt-2 rounded border px-3 py-1 text-[11px] uppercase tracking-wide"
          style={{ borderColor: "var(--color-line-strong)", color: "var(--color-text-primary)" }}
        >
          Apply Config
        </button>
        <div className="mt-2 tabular-mono text-[11px]" style={{ color: "var(--color-text-tertiary)" }}>
          {sensors.lidar_ranges.length} rays active · nearest {Math.min(...sensors.lidar_ranges).toFixed(2)} m
        </div>
      </div>

      <div>
        <div className="mb-2 text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>
          Ultrasonic
        </div>
        <div className="grid grid-cols-2 gap-2 tabular-mono text-sm">
          <Readout label="FRONT" value={sensors.ultrasonic_front} />
          <Readout label="LEFT" value={sensors.ultrasonic_left} />
          <Readout label="RIGHT" value={sensors.ultrasonic_right} />
          <Readout label="REAR" value={sensors.ultrasonic_rear} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="mb-2 text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>GPS</div>
          <div className="tabular-mono text-xs" style={{ color: "var(--color-text-primary)" }}>
            X: {sensors.gps_x.toFixed(2)} m<br />
            Y: {sensors.gps_y.toFixed(2)} m<br />
            ACC: ±{sensors.gps_accuracy_m.toFixed(2)} m
          </div>
        </div>
        <div>
          <div className="mb-2 text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>IMU</div>
          <div className="tabular-mono text-xs" style={{ color: "var(--color-text-primary)" }}>
            HDG: {sensors.imu_heading_deg.toFixed(1)}°<br />
            ω: {sensors.imu_angular_velocity_dps.toFixed(1)} °/s<br />
            a: {sensors.imu_acceleration_mps2.toFixed(2)} m/s²
          </div>
        </div>
      </div>
    </div>
  );
}

function Readout({ label, value }: { label: string; value: number }) {
  const near = value < 1.5;
  return (
    <div className="flex items-center justify-between rounded border px-2 py-1" style={{ background: "var(--color-bg-inset)", borderColor: "var(--color-line)" }}>
      <span style={{ color: "var(--color-text-tertiary)" }}>{label}</span>
      <span style={{ color: near ? "var(--color-status-fault)" : "var(--color-text-primary)" }}>{value.toFixed(1)} m</span>
    </div>
  );
}

function SliderField({
  label,
  value,
  min,
  max,
  step,
  unit,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  onChange: (v: number) => void;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span style={{ color: "var(--color-text-tertiary)" }}>
        {label} <span className="tabular-mono" style={{ color: "var(--color-text-primary)" }}>{value}{unit}</span>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="accent-[color:var(--color-status-nav)]"
      />
    </label>
  );
}
