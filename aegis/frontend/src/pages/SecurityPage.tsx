import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Panel } from "../components/ui/Panel";
import { Button } from "../components/ui/Button";
import { NotesPanel } from "../components/NotesPanel";
import { api } from "../services/api";
import type { AttackType, ComparisonResult, DefenseConfig } from "../types";

const ATTACKS: { id: AttackType; label: string }[] = [
  { id: "sensor_spoofing", label: "Sensor / Telemetry Spoofing" },
  { id: "unauthorized_command", label: "Unauthorized Command" },
  { id: "replay_attack", label: "Replayed Command" },
  { id: "compromised_channel", label: "Compromised Channel (MITM)" },
  { id: "malicious_nav_injection", label: "Malicious Nav Injection" },
  { id: "dos_flood", label: "Denial of Service Flood" },
];

const DEFENSE_FIELDS: { id: keyof DefenseConfig; label: string }[] = [
  { id: "authentication_enabled", label: "Authentication (HMAC signing)" },
  { id: "integrity_checks_enabled", label: "Integrity / Freshness Checks" },
  { id: "anomaly_detection_enabled", label: "Anomaly Detection" },
  { id: "rate_limiting_enabled", label: "Rate Limiting" },
  { id: "secure_channel_enabled", label: "Secure Channel (tamper detection)" },
];

export function SecurityPage() {
  const [selectedAttacks, setSelectedAttacks] = useState<Set<AttackType>>(new Set(ATTACKS.map((a) => a.id)));
  const [defenses, setDefenses] = useState<DefenseConfig>({
    authentication_enabled: true,
    integrity_checks_enabled: true,
    anomaly_detection_enabled: true,
    rate_limiting_enabled: true,
    secure_channel_enabled: true,
  });
  const [intensity, setIntensity] = useState(0.35);
  const [ticks, setTicks] = useState(200);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [busy, setBusy] = useState(false);

  const toggleAttack = (a: AttackType) =>
    setSelectedAttacks((prev) => {
      const next = new Set(prev);
      next.has(a) ? next.delete(a) : next.add(a);
      return next;
    });

  const run = async () => {
    setBusy(true);
    try {
      const res = await api.runSecurityComparison({
        attacks: Array.from(selectedAttacks),
        defenses,
        duration_ticks: ticks,
        attack_intensity: intensity,
      });
      setResult(res);
    } finally {
      setBusy(false);
    }
  };

  const chartData = result
    ? [
        { metric: "Detection Rate %", Unsecured: result.unsecured.detection_rate_pct, Secured: result.secured.detection_rate_pct },
        { metric: "Nav Degradation %", Unsecured: result.unsecured.navigation_degradation_pct, Secured: result.secured.navigation_degradation_pct },
        { metric: "Position Error (m)", Unsecured: result.unsecured.final_position_error_m, Secured: result.secured.final_position_error_m },
        { metric: "Cmds Rejected", Unsecured: result.unsecured.commands_rejected, Secured: result.secured.commands_rejected },
      ]
    : [];

  return (
    <div className="grid h-full grid-cols-1 gap-3 lg:grid-cols-[360px_1fr]">
      <div className="flex flex-col gap-3">
        <Panel eyebrow="Attack Scenario" title="Active Attack Types">
          <div className="flex flex-col gap-1.5">
            {ATTACKS.map((a) => (
              <label key={a.id} className="flex items-center gap-2 text-xs" style={{ color: "var(--color-text-secondary)" }}>
                <input type="checkbox" checked={selectedAttacks.has(a.id)} onChange={() => toggleAttack(a.id)} />
                {a.label}
              </label>
            ))}
          </div>
          <div className="mt-3 flex flex-col gap-2">
            <label className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
              Attack intensity <span className="tabular-mono" style={{ color: "var(--color-text-primary)" }}>{intensity.toFixed(2)}</span>
              <input type="range" min={0.05} max={1} step={0.05} value={intensity} onChange={(e) => setIntensity(parseFloat(e.target.value))} className="w-full" />
            </label>
            <label className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
              Duration (ticks) <span className="tabular-mono" style={{ color: "var(--color-text-primary)" }}>{ticks}</span>
              <input type="range" min={50} max={500} step={10} value={ticks} onChange={(e) => setTicks(parseInt(e.target.value))} className="w-full" />
            </label>
          </div>
        </Panel>

        <Panel eyebrow="Countermeasures" title="Defenses (Secured Run)">
          <div className="flex flex-col gap-1.5">
            {DEFENSE_FIELDS.map((d) => (
              <label key={d.id} className="flex items-center gap-2 text-xs" style={{ color: "var(--color-text-secondary)" }}>
                <input
                  type="checkbox"
                  checked={defenses[d.id]}
                  onChange={(e) => setDefenses((prev) => ({ ...prev, [d.id]: e.target.checked }))}
                />
                {d.label}
              </label>
            ))}
          </div>
          <Button variant="primary" className="mt-3 w-full" disabled={busy} onClick={run}>
            {busy ? "Running…" : "Run Unsecured vs Secured Comparison"}
          </Button>
          <p className="mt-2 text-[10px]" style={{ color: "var(--color-text-tertiary)" }}>
            Runs the identical attack sequence twice (same random seed): once with no defenses, once with the
            countermeasures above. All attacks and defenses are simulated against an in-memory model — no real
            network traffic or code execution is involved.
          </p>
        </Panel>

        <Panel eyebrow="Notetaker" title="Session Notes">
          <NotesPanel />
        </Panel>
      </div>

      <div className="flex flex-col gap-3">
        {!result ? (
          <Panel className="flex-1 items-center justify-center text-center">
            <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
              Configure a scenario and run the comparison to see detection rate, response time, and navigation
              degradation for an unsecured vs. a secured robot.
            </div>
          </Panel>
        ) : (
          <>
            <Panel eyebrow="Comparison" title="Unsecured vs. Secured — Key Metrics">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-line-soft)" />
                  <XAxis dataKey="metric" tick={{ fill: "var(--color-text-tertiary)", fontSize: 10 }} />
                  <YAxis tick={{ fill: "var(--color-text-tertiary)", fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: "var(--color-bg-panel-raised)", border: "1px solid var(--color-line-strong)" }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="Unsecured" fill="var(--color-status-fault)" />
                  <Bar dataKey="Secured" fill="var(--color-status-online)" />
                </BarChart>
              </ResponsiveContainer>
            </Panel>

            <div className="grid grid-cols-2 gap-3">
              <MetricsTable title="Unsecured" tone="fault" m={result.unsecured} />
              <MetricsTable title="Secured" tone="online" m={result.secured} />
            </div>

            <Panel eyebrow="Event Log" title="Secured Run — Attack Outcomes" className="min-h-[160px] flex-1">
              <div className="max-h-56 overflow-y-auto tabular-mono text-[11px]">
                {result.events_secured.map((e, i) => (
                  <div key={i} className="flex gap-2 border-b py-1" style={{ borderColor: "var(--color-line-soft)" }}>
                    <span style={{ color: "var(--color-text-tertiary)" }}>t={e.tick}</span>
                    <span style={{ color: e.blocked ? "var(--color-status-online)" : "var(--color-status-fault)" }}>
                      {e.blocked ? "BLOCKED" : "ACCEPTED"}
                    </span>
                    <span style={{ color: "var(--color-text-secondary)" }}>{e.description}</span>
                  </div>
                ))}
              </div>
            </Panel>
          </>
        )}
      </div>
    </div>
  );
}

function MetricsTable({ title, tone, m }: { title: string; tone: "fault" | "online"; m: ComparisonResult["unsecured"] }) {
  const rows: [string, string][] = [
    ["Detection Rate", `${m.detection_rate_pct}%`],
    ["Blocked Attacks", `${m.blocked_attacks}/${m.total_attacks}`],
    ["False Positives", `${m.false_positive_count}`],
    ["Avg Response Time", `${m.avg_response_time_ms} ms`],
    ["Nav Degradation", `${m.navigation_degradation_pct}%`],
    ["Final Position Error", `${m.final_position_error_m} m`],
  ];
  return (
    <Panel eyebrow={title} title={title === "Unsecured" ? "No Defenses" : "Defenses Active"}>
      <div className="flex flex-col gap-1 tabular-mono text-xs">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between border-b py-1" style={{ borderColor: "var(--color-line-soft)" }}>
            <span style={{ color: "var(--color-text-tertiary)" }}>{label}</span>
            <span style={{ color: tone === "fault" ? "var(--color-status-fault)" : "var(--color-status-online)" }}>{value}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}
