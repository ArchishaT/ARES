import { useCallback, useEffect, useState } from "react";
import { Landing } from "./pages/Landing";
import { TopBar } from "./components/TopBar";
import { Sidebar } from "./components/Sidebar";
import { MissionControlPage } from "./pages/MissionControlPage";
import { SimulationPage } from "./pages/SimulationPage";
import { NavigationPage } from "./pages/NavigationPage";
import { SensorsPage } from "./pages/SensorsPage";
import { VisionPage } from "./pages/VisionPage";
import { TelemetryPage } from "./pages/TelemetryPage";
import { EventLogPage } from "./pages/EventLogPage";
import { DiagnosticsPage } from "./pages/DiagnosticsPage";
import { SecurityPage } from "./pages/SecurityPage";
import { CyberRangePage } from "./pages/CyberRangePage";
import { SettingsPage } from "./pages/SettingsPage";
import { useTelemetryStream } from "./hooks/useTelemetryStream";
import { api } from "./services/api";
import type { EnvironmentInfo, NavSection, PathPlanResult } from "./types";

export default function App() {
  const [entered, setEntered] = useState(false);
  const [section, setSection] = useState<NavSection>("mission");
  const [env, setEnv] = useState<EnvironmentInfo | null>(null);
  const [plan, setPlan] = useState<PathPlanResult | null>(null);
  const [backendReachable, setBackendReachable] = useState(true);

  const stream = useTelemetryStream();

  const refreshEnvironment = useCallback(() => {
    api
      .getEnvironment()
      .then((e) => {
        setEnv(e);
        setBackendReachable(true);
      })
      .catch(() => setBackendReachable(false));
  }, []);

  useEffect(() => {
    if (!entered) return;
    refreshEnvironment();
  }, [entered, refreshEnvironment]);

  if (!entered) {
    return <Landing onEnter={() => setEntered(true)} />;
  }

  return (
    <div className="flex h-screen flex-col" style={{ background: "var(--color-bg-void)" }}>
      <TopBar wsConnected={stream.connected} simTime={stream.simTime} telemetry={stream.telemetry} />
      <div className="flex min-h-0 flex-1">
        <Sidebar active={section} onSelect={setSection} />
        <main className="min-w-0 flex-1 overflow-y-auto p-3">
          {!backendReachable && (
            <div
              className="mb-3 rounded border px-3 py-2 text-xs"
              style={{
                borderColor: "var(--color-status-fault)",
                color: "var(--color-status-fault)",
                background: "var(--color-status-fault-dim)",
              }}
            >
              Cannot reach the AEGIS backend at the configured API URL. Start the FastAPI server (see README)
              and refresh, or check Settings to change the endpoint.
            </div>
          )}

          {section === "mission" && (
            <MissionControlPage
              env={env}
              telemetry={stream.telemetry}
              sensors={stream.sensors}
              logs={stream.logs}
              refreshEnvironment={refreshEnvironment}
              plan={plan}
              onPlanChange={setPlan}
            />
          )}
          {section === "simulation" && (
            <SimulationPage
              env={env}
              telemetry={stream.telemetry}
              sensors={stream.sensors}
              refreshEnvironment={refreshEnvironment}
            />
          )}
          {section === "navigation" && (
            <NavigationPage plan={plan} robotState={stream.telemetry?.state ?? "IDLE"} />
          )}
          {section === "sensors" && <SensorsPage sensors={stream.sensors} />}
          {section === "vision" && <VisionPage />}
          {section === "telemetry" && <TelemetryPage history={stream.history} telemetry={stream.telemetry} />}
          {section === "log" && <EventLogPage logs={stream.logs} />}
          {section === "diagnostics" && <DiagnosticsPage wsConnected={stream.connected} />}
          {section === "security" && <SecurityPage />}
          {section === "cyberrange" && <CyberRangePage />}
          {section === "settings" && <SettingsPage />}
        </main>
      </div>
    </div>
  );
}
