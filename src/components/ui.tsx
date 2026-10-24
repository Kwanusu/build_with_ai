import type { ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "plain";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonBaseProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
}

/** With `href` it renders a link, opening a new tab when `external`. */
interface ButtonLinkProps extends ButtonBaseProps {
  href: string;
  external?: boolean;
}

/** Without `href` it renders a `<button>`. `busy` sets aria-busy while an action runs. */
interface ButtonActionProps extends ButtonBaseProps {
  href?: undefined;
  type?: "button" | "submit";
  onClick?: () => void;
  disabled?: boolean;
  busy?: boolean;
  "aria-label"?: string;
}

type ButtonProps = ButtonLinkProps | ButtonActionProps;

const SIZE_CLASS: Record<ButtonSize, string> = { sm: "btn-sm", md: "", lg: "btn-lg" };

/** Use variant="primary" (the ochre fill) once per view, for the main action. */
export function Button(props: ButtonProps) {
  const { variant = "secondary", size = "md", children } = props;
  const className = `btn btn-${variant} ${SIZE_CLASS[size]}`.trim();

  if (props.href !== undefined) {
    return (
      <a
        href={props.href}
        className={className}
        {...(props.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      >
        {children}
      </a>
    );
  }

  return (
    <button
      type={props.type ?? "button"}
      className={className}
      onClick={props.onClick}
      disabled={props.disabled}
      aria-busy={props.busy}
      aria-label={props["aria-label"]}
    >
      {children}
    </button>
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

export function CircleAlertIcon() {
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" x2="12" y1="8" y2="12" />
      <line x1="12" x2="12.01" y1="16" y2="16" />
    </svg>
  );
}

export function LeafIcon() {
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
      <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
    </svg>
  );
}

export function Spinner({ large = false }: { large?: boolean }) {
  return <span className={large ? "spinner spinner-lg" : "spinner"} aria-hidden="true" />;
}

type NoticeTone = "success" | "warning" | "error";

/** An inline message with a tone icon. Errors use role="alert"; the rest use role="status". */
export function Notice({ tone, children }: { tone: NoticeTone; children: ReactNode }) {
  const icon = tone === "success" ? <CircleCheckIcon /> : tone === "warning" ? <TriangleAlertIcon /> : <CircleAlertIcon />;
  return (
    <div className={`notice notice-${tone}`} role={tone === "error" ? "alert" : "status"}>
      <span className="icon-md flex-none" aria-hidden="true">{icon}</span>
      <div className="min-w-0">{children}</div>
    </div>
  );
}
