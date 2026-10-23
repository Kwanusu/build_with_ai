import { useState } from "react";
import { useAuth } from "../auth";
import { ACCOUNT, CTA_HREF, CTA_LABEL, NAV_LINKS } from "../content";
import { Button } from "./ui";
import { Logo } from "./Logo";

function Account() {
  const auth = useAuth();
  const [busy, setBusy] = useState(false);
  if (!auth.user) return null;

  async function signOut() {
    setBusy(true);
    try {
      await auth.signOut();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-1">
      {auth.user.avatar_url && <img className="avatar" src={auth.user.avatar_url} alt="" width={32} height={32} />}
      <span className="type-label c-text hidden sm:inline">
        <span className="sr-only">{ACCOUNT.signedInAs} </span>@{auth.user.login}
      </span>
      <button type="button" className="btn btn-plain btn-sm" onClick={signOut} disabled={busy} aria-busy={busy}>
        {busy ? ACCOUNT.signingOut : ACCOUNT.signOut}
      </button>
    </div>
  );
}

export function Header({ showAction = true }: { showAction?: boolean }) {
  const auth = useAuth();
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
        {auth.user ? (
          <Account />
        ) : showAction ? (
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
