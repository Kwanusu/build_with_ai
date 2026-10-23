import { useCallback, useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { ApiError, listRepos, signInHref, type RepoSummary } from "../api";
import { useAuth } from "../auth";
import { CONNECT, SCAN } from "../content";
import { timeAgo } from "../format";
import { Badge, CircleAlertIcon, Notice, Spinner } from "./ui";

export function Frame({ children }: { children: ReactNode }) {
  return <section className="page py-6 flex flex-col gap-4">{children}</section>;
}

function messageOf(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Nothing has been changed.";
}

/** The paste-a-URL form. `primary` makes its button the page's one ochre action. */
export function UrlForm({
  initialUrl = "",
  primary,
  helper = SCAN.form.helper,
  onSubmit,
}: {
  initialUrl?: string;
  primary: boolean;
  helper?: string;
  onSubmit: (url: string) => Promise<void>;
}) {
  const [url, setUrl] = useState(initialUrl);
  const [busy, setBusy] = useState(false);
  const [fieldError, setFieldError] = useState<string>();
  const [problem, setProblem] = useState<string>();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setFieldError(undefined);
    setProblem(undefined);
    setBusy(true);
    try {
      await onSubmit(url.trim());
    } catch (error) {
      if (error instanceof ApiError && error.code === "invalid_repo_url") {
        setFieldError(error.message);
      } else {
        setProblem(messageOf(error));
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="flex flex-col gap-3 reading" onSubmit={submit} noValidate>
      {problem && <Notice tone="error">{problem}</Notice>}
      <div className="field">
        <label className="field-label" htmlFor="repo-url">
          {SCAN.form.label}
        </label>
        <input
          id="repo-url"
          className="input input-mono"
          type="url"
          inputMode="url"
          autoComplete="off"
          spellCheck={false}
          placeholder={SCAN.form.placeholder}
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          aria-invalid={fieldError ? true : undefined}
          aria-describedby={fieldError ? "repo-url-error" : "repo-url-help"}
        />
        {fieldError ? (
          <p id="repo-url-error" className="field-error" role="alert">
            <CircleAlertIcon />
            {fieldError}
          </p>
        ) : (
          <p id="repo-url-help" className="field-helper">
            {helper}
          </p>
        )}
      </div>
      <div>
        <button
          type="submit"
          className={`btn ${primary ? "btn-primary" : "btn-secondary"} btn-lg`}
          disabled={busy || url.trim() === ""}
          aria-busy={busy}
        >
          {busy ? SCAN.form.submitting : SCAN.form.submit}
        </button>
      </div>
    </form>
  );
}

/** The Connect screen. What it offers depends on whether you're signed in, and whether sign-in is set up at all. */
export function Connect({
  initialUrl,
  notice,
  onSubmit,
}: {
  initialUrl?: string;
  notice?: string;
  onSubmit: (url: string) => Promise<void>;
}) {
  const auth = useAuth();

  if (auth.status === "loading") {
    return (
      <Frame>
        <div className="flex items-center gap-1" role="status">
          <Spinner />
          <p className="type-body-lg c-muted">Checking your sign-in</p>
        </div>
      </Frame>
    );
  }

  if (auth.user) {
    return <RepoPicker notice={notice} initialUrl={initialUrl} onSubmit={onSubmit} />;
  }

  if (auth.signInAvailable) {
    return (
      <Frame>
        <div className="flex flex-col gap-1 reading">
          <h1 className="type-h1">{CONNECT.signedOut.title}</h1>
          <p className="type-body-lg c-muted">{CONNECT.signedOut.intro}</p>
        </div>
        {notice && (
          <div className="reading">
            <Notice tone="warning">{notice}</Notice>
          </div>
        )}
        <div className="flex flex-col items-start gap-1">
          <a className="btn btn-primary btn-lg" href={signInHref}>
            {CONNECT.signedOut.signIn}
          </a>
          <p className="type-small c-muted">{CONNECT.signedOut.permissions}</p>
        </div>
        <div className="flex flex-col gap-2 pt-3">
          <h2 className="type-h3">{CONNECT.signedOut.orPublic}</h2>
          <UrlForm key={initialUrl ?? "empty"} initialUrl={initialUrl} primary={false} onSubmit={onSubmit} />
        </div>
      </Frame>
    );
  }

  return (
    <Frame>
      <div className="flex flex-col gap-1 reading">
        <h1 className="type-h1">{SCAN.form.title}</h1>
        <p className="type-body-lg c-muted">{SCAN.form.intro}</p>
      </div>
      {notice && (
        <div className="reading">
          <Notice tone="warning">{notice}</Notice>
        </div>
      )}
      <UrlForm key={initialUrl ?? "empty"} initialUrl={initialUrl} primary onSubmit={onSubmit} />
    </Frame>
  );
}

type RepoState = { kind: "loading" } | { kind: "ready"; repos: RepoSummary[] } | { kind: "error"; message: string };

function RepoPicker({
  notice,
  initialUrl,
  onSubmit,
}: {
  notice?: string;
  initialUrl?: string;
  onSubmit: (url: string) => Promise<void>;
}) {
  const auth = useAuth();
  const [state, setState] = useState<RepoState>({ kind: "loading" });
  const [filter, setFilter] = useState("");
  const [starting, setStarting] = useState<string>();
  const [problem, setProblem] = useState<string>();

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      setState({ kind: "ready", repos: await listRepos() });
    } catch (error) {
      if (error instanceof ApiError && error.code === "sign_in_required") {
        await auth.refresh(); // the sign-in ended, so show the signed-out page
        return;
      }
      setState({ kind: "error", message: messageOf(error) });
    }
  }, [auth]);

  useEffect(() => {
    void load();
    // Load once per visit. `auth` changes identity when it refreshes, which must not reload the list.
  }, []);

  const shown = useMemo(() => {
    if (state.kind !== "ready") return [];
    const needle = filter.trim().toLowerCase();
    return needle ? state.repos.filter((repo) => repo.full_name.toLowerCase().includes(needle)) : state.repos;
  }, [state, filter]);

  async function scan(repo: RepoSummary) {
    setProblem(undefined);
    setStarting(repo.full_name);
    try {
      await onSubmit(`https://github.com/${repo.full_name}`);
    } catch (error) {
      setProblem(messageOf(error));
    } finally {
      setStarting(undefined);
    }
  }

  return (
    <Frame>
      <div className="flex flex-col gap-1 reading">
        <h1 className="type-h1">{CONNECT.picker.title}</h1>
        <p className="type-body-lg c-muted">{CONNECT.picker.intro}</p>
      </div>
      {(notice || problem) && (
        <div className="reading">
          <Notice tone={problem ? "error" : "warning"}>{problem ?? notice}</Notice>
        </div>
      )}

      {state.kind === "loading" && (
        <div className="flex items-center gap-1" role="status">
          <Spinner />
          <p className="type-body-lg c-muted">{CONNECT.picker.loading}</p>
        </div>
      )}

      {state.kind === "error" && (
        <div className="flex flex-col items-start gap-2 reading">
          <Notice tone="error">{state.message}</Notice>
          <button type="button" className="btn btn-secondary" onClick={() => void load()}>
            {CONNECT.picker.retry}
          </button>
        </div>
      )}

      {state.kind === "ready" && (
        <div className="flex flex-col gap-2">
          {state.repos.length > 0 ? (
            <>
              <div className="field reading">
                <label className="field-label" htmlFor="repo-filter">
                  {CONNECT.picker.filterLabel}
                </label>
                <input
                  id="repo-filter"
                  className="input"
                  type="search"
                  autoComplete="off"
                  spellCheck={false}
                  placeholder={CONNECT.picker.filterPlaceholder}
                  value={filter}
                  onChange={(event) => setFilter(event.target.value)}
                />
              </div>
              {shown.length === 0 ? (
                <p className="type-body c-muted" role="status">
                  {CONNECT.picker.noMatches}
                </p>
              ) : (
                <ul className="flex flex-col gap-2 list-none p-0 m-0" aria-label="Your repos">
                  {shown.map((repo) => (
                    <li key={repo.full_name} className="evidence flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-col gap-half min-w-0">
                        <div className="flex flex-wrap items-center gap-1">
                          <p className="type-code font-medium wrap-break-word">{repo.full_name}</p>
                          {repo.private && <Badge tone="neutral">{CONNECT.picker.private}</Badge>}
                        </div>
                        <p className="type-small c-muted">
                          {[repo.language, `Pushed ${timeAgo(repo.pushed_at)}`].filter(Boolean).join(" · ")}
                        </p>
                      </div>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => void scan(repo)}
                        disabled={starting !== undefined}
                        aria-busy={starting === repo.full_name}
                        aria-label={`Scan ${repo.full_name}`}
                      >
                        {starting === repo.full_name ? CONNECT.picker.starting : CONNECT.picker.scan}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </>
          ) : (
            <p className="type-body c-muted reading" role="status">
              {CONNECT.picker.empty}
            </p>
          )}
        </div>
      )}

      <div className="flex flex-col gap-2 pt-3">
        <h2 className="type-h3">{CONNECT.picker.pasteTitle}</h2>
        <UrlForm key={initialUrl ?? "empty"} initialUrl={initialUrl} primary helper={SCAN.form.helperSignedIn} onSubmit={onSubmit} />
      </div>
    </Frame>
  );
}
