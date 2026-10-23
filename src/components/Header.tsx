import { CTA_HREF, CTA_LABEL, NAV_LINKS } from "../content";
import { Button } from "./ui";
import { Logo } from "./Logo";

export function Header({ showAction = true }: { showAction?: boolean }) {
  return (
    <header className="bg-page sticky top-0 z-10 border-b rule">
      <div className="page flex items-center justify-between h-topbar-height">
        <a href="#top" aria-label="Lopper home">
          <Logo variant="lockup" className="hidden sm:inline-flex" />
          <Logo variant="wordmark" className="sm:hidden" />
        </a>
        <nav aria-label="Main" className="hidden md:flex items-center gap-3">
          {NAV_LINKS.map((link) => (
            <a key={link.href} className="nav-link" href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>
        {showAction ? (
          <Button href={CTA_HREF} size="sm">
            {CTA_LABEL}
          </Button>
        ) : (
          <span aria-hidden="true" />
        )}
      </div>
    </header>
  );
}
