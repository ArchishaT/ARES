import type { ReactNode } from "react";

interface PanelProps {
  title?: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  noPadding?: boolean;
}

export function Panel({ title, eyebrow, action, children, className = "", noPadding = false }: PanelProps) {
  return (
    <div
      className={`flex flex-col rounded-md border ${className}`}
      style={{ background: "var(--color-bg-panel)", borderColor: "var(--color-line)" }}
    >
      {(title || eyebrow) && (
        <div
          className="flex items-center justify-between border-b px-3 py-2"
          style={{ borderColor: "var(--color-line)" }}
        >
          <div>
            {eyebrow && (
              <div
                className="text-[10px] font-semibold uppercase tracking-widest"
                style={{ color: "var(--color-text-tertiary)" }}
              >
                {eyebrow}
              </div>
            )}
            {title && <div className="text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>{title}</div>}
          </div>
          {action}
        </div>
      )}
      <div className={noPadding ? "flex-1" : "flex-1 p-3"}>{children}</div>
    </div>
  );
}
