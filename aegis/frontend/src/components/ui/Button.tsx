import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
}

const VARIANTS: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "text-black font-semibold",
  secondary: "",
  danger: "text-black font-semibold",
  ghost: "",
};

export function Button({ variant = "secondary", className = "", style, disabled, ...props }: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-1.5 rounded px-3 py-1.5 text-xs font-medium uppercase tracking-wide transition-colors disabled:opacity-40 disabled:cursor-not-allowed";

  let bg = "var(--color-bg-panel-raised)";
  let border = "var(--color-line-strong)";
  let color = "var(--color-text-primary)";

  if (variant === "primary") {
    bg = "var(--color-status-nav)";
    color = "#06141a";
    border = "var(--color-status-nav)";
  } else if (variant === "danger") {
    bg = "var(--color-status-fault)";
    color = "#1a0605";
    border = "var(--color-status-fault)";
  } else if (variant === "ghost") {
    bg = "transparent";
    border = "transparent";
  }

  return (
    <button
      className={`${base} ${VARIANTS[variant]} ${className} border`}
      style={{ background: disabled ? "var(--color-bg-panel-raised)" : bg, borderColor: border, color: disabled ? "var(--color-text-tertiary)" : color, ...style }}
      disabled={disabled}
      {...props}
    />
  );
}
