import { Panel } from "../components/ui/Panel";
import { BASE_URL } from "../services/api";

export function SettingsPage() {
  return (
    <Panel eyebrow="Configuration" title="Settings" className="h-full">
      <div className="flex flex-col gap-4 tabular-mono text-xs">
        <div>
          <div className="mb-1 text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>
            Backend API URL
          </div>
          <div className="rounded border px-2 py-1" style={{ borderColor: "var(--color-line)", color: "var(--color-text-primary)" }}>
            {BASE_URL}
          </div>
          <div className="mt-1 text-[10px]" style={{ color: "var(--color-text-tertiary)" }}>
            Set VITE_API_URL / VITE_WS_URL in a .env file to point at a different backend.
          </div>
        </div>
        <div>
          <div className="mb-1 text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>
            About
          </div>
          <p style={{ color: "var(--color-text-secondary)" }}>
            AEGIS v1.0.0 — simulation-first autonomous robotics command platform. See the README for
            hardware integration notes (ROS2 / MQTT / Serial → ESP32 / Raspberry Pi).
          </p>
        </div>
      </div>
    </Panel>
  );
}
