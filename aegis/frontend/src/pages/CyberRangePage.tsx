import { useState } from "react";
import { Panel } from "../components/ui/Panel";
import { Button } from "../components/ui/Button";
import { NotesPanel } from "../components/NotesPanel";
import { api } from "../services/api";
import type { BlueTeamResult, RedTeamResult, RedTeamTechnique, SystemConfig, VulnerabilityType } from "../types";

const TECHNIQUES: { id: RedTeamTechnique; label: string }[] = [
  { id: "port_scan", label: "Port Scan" },
  { id: "brute_force_login", label: "Brute-Force Login" },
  { id: "phishing_foothold", label: "Phishing Foothold" },
  { id: "privilege_escalation", label: "Privilege Escalation" },
  { id: "lateral_movement", label: "Lateral Movement" },
  { id: "data_exfiltration", label: "Data Exfiltration" },
];

const VULNS: { id: VulnerabilityType; label: string }[] = [
  { id: "trojan", label: "Trojan" },
  { id: "backdoor", label: "Backdoor" },
  { id: "time_bomb", label: "Time Bomb" },
  { id: "worm", label: "Worm" },
  { id: "rootkit", label: "Rootkit" },
];

const DEFAULT_SYSTEM: SystemConfig = {
  os_type: "linux",
  patch_level_pct: 60,
  open_ports: [22, 80, 443],
  firewall_enabled: false,
  ids_enabled: false,
  strong_auth_enabled: false,
  least_privilege_enabled: false,
  network_segmentation_enabled: false,
};

export function CyberRangePage() {
  const [mode, setMode] = useState<"red" | "blue">("red");
  const [system, setSystem] = useState<SystemConfig>({ ...DEFAULT_SYSTEM });
  const [techniques, setTechniques] = useState<Set<RedTeamTechnique>>(new Set(["port_scan", "brute_force_login"]));
  const [vuln, setVuln] = useState<VulnerabilityType>("trojan");
  const [redResult, setRedResult] = useState<RedTeamResult | null>(null);
  const [blueResult, setBlueResult] = useState<BlueTeamResult | null>(null);
  const [busy, setBusy] = useState(false);

  const toggleTech = (t: RedTeamTechnique) =>
    setTechniques((prev) => {
      const next = new Set(prev);
      next.has(t) ? next.delete(t) : next.add(t);
      return next;
    });

  const toggleFlag = (key: keyof SystemConfig) =>
    setSystem((prev) => ({ ...prev, [key]: !prev[key] }));

  const runRed = async () => {
    setBusy(true);
    try {
      setRedResult(await api.runRedTeam(system, Array.from(techniques)));
    } finally {
      setBusy(false);
    }
  };

  const runBlue = async () => {
    setBusy(true);
    try {
      setBlueResult(await api.runBlueTeam(vuln, system, 80));
    } finally {
      setBusy(false);
    }
  };

  const flagFields: { id: keyof SystemConfig; label: string }[] = [
    { id: "firewall_enabled", label: "Firewall" },
    { id: "ids_enabled", label: "Intrusion Detection (IDS)" },
    { id: "strong_auth_enabled", label: "Strong Authentication (MFA)" },
    { id: "least_privilege_enabled", label: "Least Privilege" },
    { id: "network_segmentation_enabled", label: "Network Segmentation" },
  ];

  return (
    <div className="grid h-full grid-cols-1 gap-3 lg:grid-cols-[360px_1fr]">
      <div className="flex flex-col gap-3">
        <Panel eyebrow="Mode" title="Exercise Type">
          <div className="flex gap-2">
            <Button variant={mode === "red" ? "danger" : "secondary"} className="flex-1" onClick={() => setMode("red")}>
              Red Team
            </Button>
            <Button variant={mode === "blue" ? "primary" : "secondary"} className="flex-1" onClick={() => setMode("blue")}>
              Blue Team
            </Button>
          </div>
        </Panel>

        <Panel eyebrow="Target System" title="System Configuration">
          <div className="grid grid-cols-2 gap-1.5">
            {flagFields.map((f) => (
              <label key={f.id} className="flex items-center gap-2 text-xs" style={{ color: "var(--color-text-secondary)" }}>
                <input type="checkbox" checked={system[f.id] as boolean} onChange={() => toggleFlag(f.id)} />
                {f.label}
              </label>
            ))}
          </div>
          <label className="mt-3 block text-xs" style={{ color: "var(--color-text-tertiary)" }}>
            Patch level <span className="tabular-mono" style={{ color: "var(--color-text-primary)" }}>{system.patch_level_pct}%</span>
            <input
              type="range" min={0} max={100} value={system.patch_level_pct}
              onChange={(e) => setSystem((p) => ({ ...p, patch_level_pct: parseInt(e.target.value) }))}
              className="w-full"
            />
          </label>
        </Panel>

        {mode === "red" ? (
          <Panel eyebrow="Red Team" title="Attack Techniques">
            <div className="flex flex-col gap-1.5">
              {TECHNIQUES.map((t) => (
                <label key={t.id} className="flex items-center gap-2 text-xs" style={{ color: "var(--color-text-secondary)" }}>
                  <input type="checkbox" checked={techniques.has(t.id)} onChange={() => toggleTech(t.id)} />
                  {t.label}
                </label>
              ))}
            </div>
            <Button variant="danger" className="mt-3 w-full" disabled={busy} onClick={runRed}>
              {busy ? "Running Campaign…" : "Launch Attack Campaign"}
            </Button>
          </Panel>
        ) : (
          <Panel eyebrow="Blue Team" title="Assigned Vulnerability">
            <div className="flex flex-col gap-1.5">
              {VULNS.map((v) => (
                <label key={v.id} className="flex items-center gap-2 text-xs" style={{ color: "var(--color-text-secondary)" }}>
                  <input type="radio" name="vuln" checked={vuln === v.id} onChange={() => setVuln(v.id)} />
                  {v.label}
                </label>
              ))}
            </div>
            <Button variant="primary" className="mt-3 w-full" disabled={busy} onClick={runBlue}>
              {busy ? "Running Defense Round…" : "Run Defense Round"}
            </Button>
          </Panel>
        )}

        <Panel eyebrow="Notetaker" title="Session Notes">
          <NotesPanel />
        </Panel>
      </div>

      <div className="flex flex-col gap-3">
        {mode === "red" && redResult && (
          <>
            <div className="grid grid-cols-4 gap-2">
              <Metric label="Compromise" value={`${redResult.overall_compromise_pct}%`} />
              <Metric label="Detection Rate" value={`${redResult.detection_rate_pct}%`} />
              <Metric label="Mean Time to Compromise" value={`${redResult.mean_time_to_compromise_s}s`} />
              <Metric label="Stealth Score" value={`${redResult.overall_stealth_score}`} />
            </div>
            <Panel eyebrow="Campaign Log" title="Technique Results" className="flex-1">
              <div className="flex flex-col gap-2">
                {redResult.techniques.map((t, i) => (
                  <div key={i} className="rounded border px-3 py-2 text-xs" style={{ borderColor: "var(--color-line)", background: "var(--color-bg-inset)" }}>
                    <div className="flex items-center justify-between">
                      <span className="font-medium" style={{ color: "var(--color-text-primary)" }}>
                        {TECHNIQUES.find((x) => x.id === t.technique)?.label}
                      </span>
                      <span style={{ color: t.success ? "var(--color-status-fault)" : "var(--color-status-online)" }}>
                        {t.success ? "SUCCEEDED" : "FAILED"}
                      </span>
                    </div>
                    <div className="mt-1 tabular-mono" style={{ color: "var(--color-text-tertiary)" }}>
                      {t.notes} · {t.time_to_outcome_s}s · stealth {t.stealth_score}
                    </div>
                  </div>
                ))}
              </div>
            </Panel>
          </>
        )}

        {mode === "blue" && blueResult && (
          <>
            <div className="grid grid-cols-4 gap-2">
              <Metric label="Defense Score" value={`${blueResult.defense_score_0_100}/100`} />
              <Metric label="Final Integrity" value={`${blueResult.final_integrity_pct}%`} />
              <Metric label="Time to Detect" value={blueResult.mean_time_to_detect_s !== null ? `${blueResult.mean_time_to_detect_s} ticks` : "N/A"} />
              <Metric label="Breach?" value={blueResult.breach_occurred ? "YES" : "NO"} tone={blueResult.breach_occurred ? "fault" : "online"} />
            </div>
            <Panel eyebrow="Timeline" title="Defense Round Events" className="flex-1">
              <div className="flex flex-col gap-1.5 tabular-mono text-xs">
                {blueResult.timeline.map((t, i) => (
                  <div key={i} className="flex gap-3 border-b py-1" style={{ borderColor: "var(--color-line-soft)" }}>
                    <span style={{ color: "var(--color-text-tertiary)" }}>tick {t.tick}</span>
                    <span style={{ color: t.mitigated ? "var(--color-status-online)" : t.detected ? "var(--color-status-warn)" : "var(--color-status-fault)" }}>
                      {t.event}
                    </span>
                  </div>
                ))}
              </div>
            </Panel>
          </>
        )}

        {((mode === "red" && !redResult) || (mode === "blue" && !blueResult)) && (
          <Panel className="flex-1 items-center justify-center text-center">
            <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
              Configure the target system and run a {mode === "red" ? "red team campaign" : "blue team defense round"} to see results.
              All techniques and vulnerabilities are abstracted simulations — no real attack tooling or malware exists in this project.
            </div>
          </Panel>
        )}
      </div>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "fault" | "online" }) {
  return (
    <div className="rounded border px-3 py-2" style={{ background: "var(--color-bg-inset)", borderColor: "var(--color-line)" }}>
      <div className="text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>{label}</div>
      <div className="tabular-mono text-lg" style={{ color: tone === "fault" ? "var(--color-status-fault)" : tone === "online" ? "var(--color-status-online)" : "var(--color-status-nav)" }}>
        {value}
      </div>
    </div>
  );
}
