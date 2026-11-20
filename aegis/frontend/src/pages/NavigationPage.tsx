import { useCallback, useEffect } from "react";
import { Panel } from "../components/ui/Panel";
import { NavigationPanel } from "../components/NavigationPanel";
import { api } from "../services/api";
import type { PathPlanResult, RobotState } from "../types";
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Square } from "lucide-react";

interface NavigationPageProps {
  plan: PathPlanResult | null;
  robotState: RobotState;
}

export function NavigationPage({ plan, robotState }: NavigationPageProps) {
  const send = useCallback((cmd: "forward" | "reverse" | "left" | "right" | "stop") => {
    api.manualControl(cmd).catch(() => void 0);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.repeat) return;
      const map: Record<string, "forward" | "reverse" | "left" | "right" | "stop"> = {
        w: "forward",
        s: "reverse",
        a: "left",
        d: "right",
        " ": "stop",
      };
      const cmd = map[e.key.toLowerCase()];
      if (cmd) send(cmd);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [send]);

  const disabled = robotState === "EMERGENCY_STOP";

  return (
    <div className="grid h-full grid-cols-1 gap-3 lg:grid-cols-2">
      <Panel eyebrow="Path Planning" title="Route Details">
        <NavigationPanel plan={plan} />
      </Panel>

      <Panel eyebrow="Manual Override" title="Manual Control">
        <div className="text-xs mb-4" style={{ color: "var(--color-text-tertiary)" }}>
          Manual commands cancel any active autonomous mission. Keyboard: W/A/S/D to drive, Space to stop.
        </div>
        <div className="mx-auto grid w-48 grid-cols-3 gap-2">
          <div />
          <CtrlButton icon={ArrowUp} onClick={() => send("forward")} disabled={disabled} label="Forward (W)" />
          <div />
          <CtrlButton icon={ArrowLeft} onClick={() => send("left")} disabled={disabled} label="Rotate Left (A)" />
          <CtrlButton icon={Square} onClick={() => send("stop")} disabled={disabled} label="Stop (Space)" danger />
          <CtrlButton icon={ArrowRight} onClick={() => send("right")} disabled={disabled} label="Rotate Right (D)" />
          <div />
          <CtrlButton icon={ArrowDown} onClick={() => send("reverse")} disabled={disabled} label="Reverse (S)" />
          <div />
        </div>
      </Panel>
    </div>
  );
}

function CtrlButton({
  icon: Icon,
  onClick,
  label,
  danger = false,
  disabled = false,
}: {
  icon: React.ElementType;
  onClick: () => void;
  label: string;
  danger?: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      disabled={disabled}
      className="flex aspect-square items-center justify-center rounded border transition-colors disabled:opacity-40"
      style={{
        borderColor: danger ? "var(--color-status-fault)" : "var(--color-line-strong)",
        color: danger ? "var(--color-status-fault)" : "var(--color-text-primary)",
        background: "var(--color-bg-inset)",
      }}
    >
      <Icon size={20} />
    </button>
  );
}
