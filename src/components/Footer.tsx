import { COPYRIGHT_HOLDER, FOOTER_NOTE } from "../content";
import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t rule">
      <div className="page py-4 flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <Logo variant="wordmark" />
          <p className="type-small c-muted reading">{FOOTER_NOTE}</p>
        </div>
        <div className="flex items-center justify-between gap-2">
          <p className="type-small c-muted">
            © {year} {COPYRIGHT_HOLDER}. All rights reserved.
          </p>
          {/* The header has this one from tablet width up. */}
          <ThemeToggle size="lg" className="sm:hidden" />
        </div>
      </div>
    </footer>
  );
}
