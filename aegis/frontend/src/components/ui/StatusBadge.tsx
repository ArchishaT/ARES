interface StatusBadgeProps {
  label: string;
  tone?: "online" | "warn" | "fault" | "nav" | "idle";
  pulse?: boolean;
}

const TONE_MAP: Record<NonNullable<StatusBadgeProps["tone"]>, { fg: string; bg: string }> = {
  online: { fg: "var(--color-status-online)", bg: "var(--color-status-online-dim)" },
  warn: { fg: "var(--color-status-warn)", bg: "var(--color-status-warn-dim)" },
  fault: { fg: "var(--color-status-fault)", bg: "var(--color-status-fault-dim)" },
  nav: { fg: "var(--color-status-nav)", bg: "var(--color-status-nav-dim)" },
  idle: { fg: "var(--color-status-idle)", bg: "var(--color-bg-inset)" },
};

export function StatusBadge({ label, tone = "idle", pulse = false }: StatusBadgeProps) {
  const c = TONE_MAP[tone];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-[11px] font-medium tabular-mono uppercase tracking-wide"
      style={{ color: c.fg, background: c.bg }}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${pulse ? "pulse-dot" : ""}`}
        style={{ background: c.fg }}
      />
      {label}
    </span>
  );
}
