import type {
  BlueTeamResult,
  ComparisonResult,
  EnvironmentInfo,
  EnvironmentPreset,
  NoteItem,
  PathPlanResult,
  RedTeamResult,
  RedTeamTechnique,
  RobotTelemetry,
  ScenarioConfig,
  SensorFrame,
  SystemConfig,
  SystemHealth,
  VisionResult,
  VulnerabilityType,
} from "../types";

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000/api";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: init?.body && !(init.body instanceof FormData) ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore parse failure */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; uptime_s: number }>("/health"),

  setDestination: (x: number, y: number) =>
    request<{ ok: boolean }>("/mission/destination", { method: "POST", body: JSON.stringify({ x, y }) }),

  planRoute: () => request<PathPlanResult>("/mission/plan", { method: "POST" }),

  startMission: () => request<{ ok: boolean }>("/mission/start", { method: "POST" }),
  pauseMission: () => request<{ ok: boolean }>("/mission/pause", { method: "POST" }),
  resumeMission: () => request<{ ok: boolean }>("/mission/resume", { method: "POST" }),
  abortMission: () => request<{ ok: boolean }>("/mission/abort", { method: "POST" }),
  resetSimulation: () => request<{ ok: boolean }>("/mission/reset", { method: "POST" }),
  emergencyStop: () => request<{ ok: boolean }>("/mission/emergency-stop", { method: "POST" }),
  clearEmergency: () => request<{ ok: boolean }>("/mission/clear-emergency", { method: "POST" }),

  manualControl: (command: "forward" | "reverse" | "left" | "right" | "stop") =>
    request<{ ok: boolean }>("/mission/manual-control", { method: "POST", body: JSON.stringify({ command }) }),

  getTelemetry: () => request<RobotTelemetry>("/mission/telemetry"),

  setEnvironment: (preset: EnvironmentPreset) =>
    request<{ ok: boolean }>("/environment", { method: "POST", body: JSON.stringify({ preset }) }),
  getEnvironment: () => request<EnvironmentInfo>("/environment"),
  addObstacle: (x: number, y: number, radius = 0.6) =>
    request<{ ok: boolean }>("/environment/obstacle", { method: "POST", body: JSON.stringify({ x, y, radius }) }),

  setSpeed: (multiplier: number) =>
    request<{ ok: boolean }>("/simulation/speed", { method: "POST", body: JSON.stringify({ multiplier }) }),

  getSensors: () => request<SensorFrame>("/sensors"),
  setLidarConfig: (range_m: number, num_rays: number, noise_std: number) =>
    request<{ ok: boolean }>("/sensors/lidar-config", {
      method: "POST",
      body: JSON.stringify({ range_m, num_rays, noise_std }),
    }),

  getLogs: (limit = 100) => request<{ logs: import("../types").LogEntry[] }>(`/logs?limit=${limit}`),

  detectUploaded: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<VisionResult>("/vision/detect", { method: "POST", body: form });
  },
  detectSimulated: () => request<VisionResult>("/vision/simulated"),

  diagnostics: () => request<SystemHealth>("/diagnostics"),

  // -- ARES security layer -------------------------------------------------
  runSecurityComparison: (scenario: ScenarioConfig) =>
    request<ComparisonResult>("/security/run-comparison", { method: "POST", body: JSON.stringify(scenario) }),
  listAttackTypes: () => request<{ attacks: { id: string; label: string; description: string }[] }>("/security/attack-types"),

  // -- Cyber range -----------------------------------------------------------
  runRedTeam: (system: SystemConfig, techniques: RedTeamTechnique[], seed?: number) =>
    request<RedTeamResult>("/cyberrange/red-team/run", {
      method: "POST",
      body: JSON.stringify({ system, techniques, seed }),
    }),
  runBlueTeam: (vulnerability: VulnerabilityType, system: SystemConfig, duration_ticks: number, seed?: number) =>
    request<BlueTeamResult>("/cyberrange/blue-team/run", {
      method: "POST",
      body: JSON.stringify({ vulnerability, system, duration_ticks, seed }),
    }),
  listTechniques: () => request<{ techniques: { id: string; label: string; description: string }[] }>("/cyberrange/techniques"),
  listVulnerabilities: () => request<{ vulnerabilities: { id: string; label: string; description: string }[] }>("/cyberrange/vulnerabilities"),

  // -- Notetaker ---------------------------------------------------------------
  listNotes: () => request<NoteItem[]>("/notes"),
  createNote: (title: string, body: string) =>
    request<NoteItem>("/notes", { method: "POST", body: JSON.stringify({ title, body }) }),
  deleteNote: (id: number) => request<{ ok: boolean }>(`/notes/${id}`, { method: "DELETE" }),
};

export { ApiError, BASE_URL };
