interface TelemetryCardProps {
  label: string;
  value: string;
  unit?: string;
  tone?: "default" | "warn" | "fault" | "online";
}

const TONE_COLOR: Record<NonNullable<TelemetryCardProps["tone"]>, string> = {
  default: "var(--color-text-primary)",
  warn: "var(--color-status-warn)",
  fault: "var(--color-status-fault)",
  online: "var(--color-status-online)",
};

export function TelemetryCard({ label, value, unit, tone = "default" }: TelemetryCardProps) {
  return (
    <div
      className="rounded border px-3 py-2"
      style={{ background: "var(--color-bg-inset)", borderColor: "var(--color-line)" }}
    >
      <div className="text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>
        {label}
      </div>
      <div className="mt-0.5 tabular-mono text-lg font-semibold" style={{ color: TONE_COLOR[tone] }}>
        {value}
        {unit && <span className="ml-1 text-xs font-normal" style={{ color: "var(--color-text-secondary)" }}>{unit}</span>}
      </div>
    </div>
  );
}
