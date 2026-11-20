import { useMemo, useState } from "react";
import type { LogEntry, LogSeverity } from "../types";
import { SEVERITY_COLORS } from "../utils/format";

interface EventLogProps {
  logs: LogEntry[];
  compact?: boolean;
}

const SEVERITIES: LogSeverity[] = ["INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"];

export function EventLog({ logs, compact = false }: EventLogProps) {
  const [filter, setFilter] = useState<Set<LogSeverity>>(new Set(SEVERITIES));

  const filtered = useMemo(() => logs.filter((l) => filter.has(l.severity)).slice().reverse(), [logs, filter]);

  const toggle = (s: LogSeverity) => {
    setFilter((prev) => {
      const next = new Set(prev);
      if (next.has(s)) next.delete(s);
      else next.add(s);
      return next;
    });
  };

  return (
    <div className="flex h-full flex-col">
      {!compact && (
        <div className="mb-2 flex flex-wrap gap-1.5">
          {SEVERITIES.map((s) => (
            <button
              key={s}
              onClick={() => toggle(s)}
              className="rounded border px-2 py-0.5 text-[10px] uppercase tracking-wide"
              style={{
                borderColor: filter.has(s) ? SEVERITY_COLORS[s] : "var(--color-line)",
                color: filter.has(s) ? SEVERITY_COLORS[s] : "var(--color-text-tertiary)",
                background: filter.has(s) ? "var(--color-bg-inset)" : "transparent",
              }}
            >
              {s}
            </button>
          ))}
        </div>
      )}
      <div className="flex-1 overflow-y-auto tabular-mono text-[11px] leading-relaxed">
        {filtered.length === 0 && (
          <div className="py-4 text-center" style={{ color: "var(--color-text-tertiary)" }}>
            No events.
          </div>
        )}
        {filtered.slice(0, compact ? 8 : undefined).map((log, i) => (
          <div key={i} className="flex gap-2 border-b py-1" style={{ borderColor: "var(--color-line-soft)" }}>
            <span style={{ color: "var(--color-text-tertiary)" }}>{log.timestamp}</span>
            <span className="w-24 shrink-0" style={{ color: SEVERITY_COLORS[log.severity] }}>
              {log.source}
            </span>
            <span style={{ color: "var(--color-text-secondary)" }}>{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
