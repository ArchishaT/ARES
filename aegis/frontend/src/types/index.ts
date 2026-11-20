export type RobotState =
  | "IDLE"
  | "PLANNING"
  | "NAVIGATING"
  | "OBSTACLE_DETECTED"
  | "REPLANNING"
  | "PAUSED"
  | "MISSION_COMPLETE"
  | "EMERGENCY_STOP"
  | "FAULT";

export type LogSeverity = "INFO" | "SUCCESS" | "WARNING" | "ERROR" | "CRITICAL";

export type EnvironmentPreset = "open_field" | "warehouse" | "maze" | "urban_grid";

export interface WorldPoint {
  x: number;
  y: number;
}

export interface Obstacle {
  x: number;
  y: number;
  radius: number;
  dynamic: boolean;
}

export interface RobotTelemetry {
  x: number;
  y: number;
  heading_deg: number;
  velocity_mps: number;
  acceleration_mps2: number;
  battery_pct: number;
  state: RobotState;
  current_waypoint_index: number;
  total_waypoints: number;
  obstacle_count: number;
}

export interface SensorFrame {
  lidar_ranges: number[];
  lidar_angles: number[];
  ultrasonic_front: number;
  ultrasonic_left: number;
  ultrasonic_right: number;
  ultrasonic_rear: number;
  gps_x: number;
  gps_y: number;
  gps_accuracy_m: number;
  imu_heading_deg: number;
  imu_angular_velocity_dps: number;
  imu_acceleration_mps2: number;
}

export interface LogEntry {
  timestamp: string;
  severity: LogSeverity;
  source: string;
  message: string;
}

export interface PathPlanResult {
  status: string;
  algorithm: string;
  waypoints: WorldPoint[];
  path_length_m: number;
  estimated_time_s: number;
  planning_time_ms: number;
}

export interface DetectionBox {
  label: string;
  confidence: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface VisionResult {
  model: string;
  objects: DetectionBox[];
  inference_time_ms: number;
  frame_width: number;
  frame_height: number;
}

export interface SystemHealth {
  simulation_engine: string;
  navigation: string;
  sensor_system: string;
  vision: string;
  websocket: string;
  backend_api: string;
  backend_latency_ms: number;
  ws_latency_ms: number;
  simulation_tick_rate_hz: number;
  active_connections: number;
}

export interface EnvironmentInfo {
  width_m: number;
  height_m: number;
  cell_size_m: number;
  obstacles: Obstacle[];
}

export interface TelemetryFrame {
  type: "telemetry";
  sim_time_s: number;
  telemetry: RobotTelemetry;
  sensors: SensorFrame;
  logs: LogEntry[];
}

export interface InitFrame {
  type: "init";
  telemetry: RobotTelemetry;
  logs: LogEntry[];
}

export type WSFrame = TelemetryFrame | InitFrame;

export type NavSection =
  | "mission"
  | "simulation"
  | "navigation"
  | "sensors"
  | "vision"
  | "telemetry"
  | "log"
  | "diagnostics"
  | "security"
  | "cyberrange"
  | "settings";

// -- ARES security layer ---------------------------------------------------
export type AttackType =
  | "sensor_spoofing"
  | "unauthorized_command"
  | "replay_attack"
  | "compromised_channel"
  | "malicious_nav_injection"
  | "dos_flood";

export interface DefenseConfig {
  authentication_enabled: boolean;
  integrity_checks_enabled: boolean;
  anomaly_detection_enabled: boolean;
  rate_limiting_enabled: boolean;
  secure_channel_enabled: boolean;
}

export interface ScenarioConfig {
  attacks: AttackType[];
  defenses: DefenseConfig;
  duration_ticks: number;
  attack_intensity: number;
}

export interface SecurityEventRecord {
  tick: number;
  attack_type: AttackType | null;
  detected: boolean;
  blocked: boolean;
  response_time_ms: number;
  description: string;
}

export interface SecurityMetrics {
  label: string;
  total_attacks: number;
  detected_attacks: number;
  blocked_attacks: number;
  detection_rate_pct: number;
  false_positive_count: number;
  false_positive_rate_pct: number;
  avg_response_time_ms: number;
  navigation_degradation_pct: number;
  final_position_error_m: number;
  commands_accepted: number;
  commands_rejected: number;
}

export interface ComparisonResult {
  scenario: ScenarioConfig;
  unsecured: SecurityMetrics;
  secured: SecurityMetrics;
  events_unsecured: SecurityEventRecord[];
  events_secured: SecurityEventRecord[];
}

// -- Cyber range -------------------------------------------------------------
export type RedTeamTechnique =
  | "port_scan"
  | "brute_force_login"
  | "phishing_foothold"
  | "privilege_escalation"
  | "lateral_movement"
  | "data_exfiltration";

export type VulnerabilityType = "trojan" | "backdoor" | "time_bomb" | "worm" | "rootkit";

export interface SystemConfig {
  os_type: string;
  patch_level_pct: number;
  open_ports: number[];
  firewall_enabled: boolean;
  ids_enabled: boolean;
  strong_auth_enabled: boolean;
  least_privilege_enabled: boolean;
  network_segmentation_enabled: boolean;
}

export interface TechniqueResult {
  technique: RedTeamTechnique;
  success: boolean;
  detected: boolean;
  time_to_outcome_s: number;
  stealth_score: number;
  notes: string;
}

export interface RedTeamResult {
  system: SystemConfig;
  techniques: TechniqueResult[];
  overall_compromise_pct: number;
  mean_time_to_compromise_s: number;
  detection_rate_pct: number;
  overall_stealth_score: number;
}

export interface BlueTeamTick {
  tick: number;
  event: string;
  detected: boolean;
  mitigated: boolean;
}

export interface BlueTeamResult {
  vulnerability: VulnerabilityType;
  system: SystemConfig;
  timeline: BlueTeamTick[];
  mean_time_to_detect_s: number | null;
  mean_time_to_mitigate_s: number | null;
  breach_occurred: boolean;
  final_integrity_pct: number;
  defense_score_0_100: number;
}

export interface NoteItem {
  id: number;
  title: string;
  body: string;
  created_at: string;
}
