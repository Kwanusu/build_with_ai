import { signInHref } from "../api";
import { useAuth } from "../auth";
import { AUTH_ERROR } from "../content";
import { Frame } from "./Connect";
import { TriangleAlertIcon } from "./ui";

/** Where the server sends you back to when GitHub sign-in didn't work. `code` says why. */
export function AuthErrorPage({ code }: { code: string }) {
  const auth = useAuth();
  const message = AUTH_ERROR.messages[code] ?? AUTH_ERROR.fallback;
  // Trying again only makes sense if sign-in is set up, and you aren't already signed in.
  const canRetry = code !== "not_configured" && !auth.user;
  return (
    <Frame>
      <div className="flex flex-col items-start gap-2 reading">
        <span className="disc">
          <TriangleAlertIcon />
        </span>
        <h1 className="type-h1">{AUTH_ERROR.title}</h1>
        <p className="type-body-lg c-muted" role="alert">
          {message}
        </p>
        <div className="flex flex-wrap gap-2">
          {canRetry && (
            <a className="btn btn-primary btn-lg" href={signInHref}>
              {AUTH_ERROR.retry}
            </a>
          )}
          <a className={`btn ${canRetry ? "btn-secondary" : "btn-primary"} btn-lg`} href="#/scan">
            {AUTH_ERROR.publicRepo}
          </a>
        </div>
      </div>
    </Frame>
  );
}
