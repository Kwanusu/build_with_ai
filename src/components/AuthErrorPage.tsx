import { signInHref } from "../api";
import { useAuth } from "../auth";
import { AUTH_ERROR } from "../content";
import { Frame } from "./Connect";
import { Button, TriangleAlertIcon } from "./ui";

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
            <Button href={signInHref} variant="primary" size="lg">
              {AUTH_ERROR.retry}
            </Button>
          )}
          <Button href="#/scan" variant={canRetry ? "secondary" : "primary"} size="lg">
            {AUTH_ERROR.publicRepo}
          </Button>
        </div>
      </div>
    </Frame>
  );
}
