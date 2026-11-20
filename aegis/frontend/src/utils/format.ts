import type { LogSeverity, RobotState } from "../types";

export function fmt(n: number, digits = 2): string {
  return n.toFixed(digits);
}

export const STATE_COLORS: Record<RobotState, string> = {
  IDLE: "var(--color-status-idle)",
  PLANNING: "var(--color-status-nav)",
  NAVIGATING: "var(--color-status-online)",
  OBSTACLE_DETECTED: "var(--color-status-warn)",
  REPLANNING: "var(--color-status-warn)",
  PAUSED: "var(--color-status-idle)",
  MISSION_COMPLETE: "var(--color-status-online)",
  EMERGENCY_STOP: "var(--color-status-fault)",
  FAULT: "var(--color-status-fault)",
};

export const STATE_LABELS: Record<RobotState, string> = {
  IDLE: "IDLE",
  PLANNING: "PLANNING ROUTE",
  NAVIGATING: "NAVIGATING",
  OBSTACLE_DETECTED: "OBSTACLE DETECTED",
  REPLANNING: "REPLANNING",
  PAUSED: "PAUSED",
  MISSION_COMPLETE: "MISSION COMPLETE",
  EMERGENCY_STOP: "EMERGENCY STOP",
  FAULT: "FAULT",
};

export const SEVERITY_COLORS: Record<LogSeverity, string> = {
  INFO: "var(--color-status-nav)",
  SUCCESS: "var(--color-status-online)",
  WARNING: "var(--color-status-warn)",
  ERROR: "var(--color-status-fault)",
  CRITICAL: "var(--color-status-fault)",
};

export function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}
