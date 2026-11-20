import { useEffect, useRef, useState } from "react";
import type { LogEntry, RobotTelemetry, SensorFrame, WSFrame } from "../types";
import { BASE_URL } from "../services/api";

const WS_URL = (import.meta.env.VITE_WS_URL as string | undefined) ?? BASE_URL.replace(/^http/, "ws").replace(/\/api$/, "") + "/ws/telemetry";

export interface TelemetryStreamState {
  connected: boolean;
  telemetry: RobotTelemetry | null;
  sensors: SensorFrame | null;
  simTime: number;
  logs: LogEntry[];
  history: { t: number; velocity: number; heading: number; battery: number; nearestObstacle: number }[];
}

const HISTORY_LIMIT = 200;

/**
 * Owns a single WebSocket connection to /ws/telemetry and reconnects with
 * backoff on drop. Keeps a rolling history buffer for the telemetry
 * charts so pages don't each need their own buffering logic.
 */
export function useTelemetryStream(): TelemetryStreamState {
  const [connected, setConnected] = useState(false);
  const [telemetry, setTelemetry] = useState<RobotTelemetry | null>(null);
  const [sensors, setSensors] = useState<SensorFrame | null>(null);
  const [simTime, setSimTime] = useState(0);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [history, setHistory] = useState<TelemetryStreamState["history"]>([]);
  const seenLogKeys = useRef<Set<string>>(new Set());

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;

    const connect = () => {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!cancelled) retryTimer = setTimeout(connect, 1500);
      };
      ws.onerror = () => ws?.close();

      ws.onmessage = (event) => {
        const frame = JSON.parse(event.data) as WSFrame;
        if (frame.type === "init") {
          setTelemetry(frame.telemetry);
          setLogs(frame.logs);
          return;
        }
        setTelemetry(frame.telemetry);
        setSensors(frame.sensors);
        setSimTime(frame.sim_time_s);

        setLogs((prev) => {
          const merged = [...prev];
          for (const l of frame.logs) {
            const key = `${l.timestamp}-${l.source}-${l.message}`;
            if (!seenLogKeys.current.has(key)) {
              seenLogKeys.current.add(key);
              merged.push(l);
            }
          }
          return merged.slice(-300);
        });

        const nearest = frame.sensors.lidar_ranges.length
          ? Math.min(...frame.sensors.lidar_ranges)
          : frame.sensors.ultrasonic_front;

        setHistory((prev) => {
          const next = [
            ...prev,
            {
              t: frame.sim_time_s,
              velocity: frame.telemetry.velocity_mps,
              heading: frame.telemetry.heading_deg,
              battery: frame.telemetry.battery_pct,
              nearestObstacle: Number.isFinite(nearest) ? nearest : 0,
            },
          ];
          return next.length > HISTORY_LIMIT ? next.slice(next.length - HISTORY_LIMIT) : next;
        });
      };
    };

    connect();

    return () => {
      cancelled = true;
      if (retryTimer) clearTimeout(retryTimer);
      ws?.close();
    };
  }, []);

  return { connected, telemetry, sensors, simTime, logs, history };
}
