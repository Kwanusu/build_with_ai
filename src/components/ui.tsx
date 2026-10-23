import type { ReactNode } from "react";

type ButtonVariant = "primary" | "secondary";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps {
  href: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
}

const SIZE_CLASS: Record<ButtonSize, string> = { sm: "btn-sm", md: "", lg: "btn-lg" };

/** Use variant="primary" (the ochre fill) once per view, for the main action. */
export function Button({ href, variant = "secondary", size = "md", children }: ButtonProps) {
  return (
    <a href={href} className={`btn btn-${variant} ${SIZE_CLASS[size]}`.trim()}>
      {children}
    </a>
  );
}

type BadgeTone = "success" | "warning" | "neutral";

interface BadgeProps {
  tone: BadgeTone;
  icon?: ReactNode;
  className?: string;
  children: ReactNode;
}

export function Badge({ tone, icon, className = "", children }: BadgeProps) {
  return (
    <span className={`badge badge-${tone} ${className}`.trim()}>
      {icon}
      {children}
    </span>
  );
}

export function CircleCheckIcon() {
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export function TriangleAlertIcon() {
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </svg>
  );
}

export function CheckIcon() {
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}
