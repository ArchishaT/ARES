import { useEffect, useRef, useState } from "react";
import { Panel } from "../components/ui/Panel";
import { SystemHealth } from "../components/SystemHealth";
import { api } from "../services/api";
import type { SystemHealth as SystemHealthType } from "../types";

interface DiagnosticsPageProps {
  wsConnected: boolean;
}

export function DiagnosticsPage({ wsConnected }: DiagnosticsPageProps) {
  const [health, setHealth] = useState<SystemHealthType | null>(null);
  const [fps, setFps] = useState(60);
  const frames = useRef(0);
  const lastCheck = useRef(performance.now());

  useEffect(() => {
    let raf: number;
    const loop = () => {
      frames.current += 1;
      const now = performance.now();
      if (now - lastCheck.current >= 1000) {
        setFps(frames.current);
        frames.current = 0;
        lastCheck.current = now;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    const poll = () => api.diagnostics().then(setHealth).catch(() => void 0);
    poll();
    const id = setInterval(poll, 2000);
    return () => clearInterval(id);
  }, []);

  return (
    <Panel eyebrow="System Health" title="Diagnostics" className="h-full">
      <SystemHealth health={health} wsConnected={wsConnected} fps={fps} />
    </Panel>
  );
}
