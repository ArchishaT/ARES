import { useState } from "react";
import { AlertOctagon } from "lucide-react";
import { api, ApiError } from "../services/api";
import type { RobotState } from "../types";

interface EmergencyStopProps {
  state: RobotState;
  onError: (msg: string) => void;
}

export function EmergencyStop({ state, onError }: EmergencyStopProps) {
  const [busy, setBusy] = useState(false);
  const active = state === "EMERGENCY_STOP";

  const trigger = async () => {
    setBusy(true);
    try {
      await api.emergencyStop();
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Failed to trigger emergency stop.");
    } finally {
      setBusy(false);
    }
  };

  const clear = async () => {
    setBusy(true);
    try {
      await api.clearEmergency();
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Failed to clear emergency stop.");
    } finally {
      setBusy(false);
    }
  };

  if (active) {
    return (
      <button
        onClick={clear}
        disabled={busy}
        className="flex w-full items-center justify-center gap-2 rounded border py-2 text-xs font-semibold uppercase tracking-widest flicker-in"
        style={{ borderColor: "var(--color-status-fault)", background: "var(--color-status-fault-dim)", color: "var(--color-status-fault)" }}
      >
        <AlertOctagon size={14} className="pulse-dot" />
        Emergency Stop Active — Reset to Resume
      </button>
    );
  }

  return (
    <button
      onClick={trigger}
      disabled={busy}
      className="flex w-full items-center justify-center gap-2 rounded border py-2 text-xs font-semibold uppercase tracking-widest transition-colors hover:brightness-110"
      style={{ borderColor: "var(--color-status-fault)", background: "transparent", color: "var(--color-status-fault)" }}
    >
      <AlertOctagon size={14} />
      Emergency Stop
    </button>
  );
}
