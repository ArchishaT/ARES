import type { PathPlanResult } from "../types";

interface NavigationPanelProps {
  plan: PathPlanResult | null;
}

export function NavigationPanel({ plan }: NavigationPanelProps) {
  if (!plan) {
    return (
      <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
        No route planned. Click the map to set a destination, then Plan Route.
      </div>
    );
  }

  const rows: [string, string][] = [
    ["STATUS", plan.status === "ready" ? "PATH READY" : "PLANNING FAILED"],
    ["ALGORITHM", plan.algorithm],
    ["PATH LENGTH", `${plan.path_length_m.toFixed(1)} m`],
    ["EST. TIME", `${plan.estimated_time_s.toFixed(1)} s`],
    ["WAYPOINTS", `${plan.waypoints.length}`],
    ["PLAN TIME", `${plan.planning_time_ms.toFixed(1)} ms`],
  ];

  return (
    <div className="flex flex-col gap-1.5 tabular-mono text-xs">
      {rows.map(([label, value]) => (
        <div key={label} className="flex items-center justify-between border-b py-1" style={{ borderColor: "var(--color-line-soft)" }}>
          <span style={{ color: "var(--color-text-tertiary)" }}>{label}</span>
          <span
            style={{
              color:
                label === "STATUS"
                  ? plan.status === "ready"
                    ? "var(--color-status-online)"
                    : "var(--color-status-fault)"
                  : "var(--color-text-primary)",
            }}
          >
            {value}
          </span>
        </div>
      ))}
    </div>
  );
}
