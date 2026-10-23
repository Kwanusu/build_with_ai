import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { ApiError, getLatestScan, getScan, setTicked, startScan, type Finding, type Scan } from "../api";
import { SCAN } from "../content";
import { scanHash } from "../route";
import { Findings } from "./Findings";
import { CircleAlertIcon, LeafIcon, Notice, Spinner, TriangleAlertIcon } from "./ui";

type View =
  | { kind: "form"; notice?: string; initialUrl?: string }
  | { kind: "loading" }
  | { kind: "scanning"; repo: string; slow: boolean }
  | { kind: "results"; scan: Scan }
  | { kind: "error"; message: string; repoUrl?: string };

interface ScanPageProps {
  owner?: string;
  repo?: string;
  /** How often to check on a running scan. Tests set this to 0. */
  pollMs?: number;
}

const SLOW_AFTER_POLLS = 60;
const GIVE_UP_AFTER_POLLS = 300;

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));
const plural = (count: number, one: string, many: string) => `${count.toLocaleString("en-US")} ${count === 1 ? one : many}`;

function messageOf(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Nothing has been changed.";
}

export function ScanPage({ owner, repo, pollMs = 1000 }: ScanPageProps) {
  const [view, setView] = useState<View>(owner && repo ? { kind: "loading" } : { kind: "form" });
  const [tickError, setTickError] = useState(false);
  const run = useRef(0);

  /** Watch a scan until it stops running, then show it. A newer run cancels this one. */
  const follow = useCallback(
    async (first: Scan, id: number) => {
      let scan = first;
      for (let polls = 0; scan.status === "running"; polls++) {
        if (polls >= GIVE_UP_AFTER_POLLS) {
          setView({ kind: "error", message: SCAN.scanning.slow, repoUrl: scan.repo.url });
          return;
        }
        setView({ kind: "scanning", repo: `${scan.repo.owner}/${scan.repo.name}`, slow: polls >= SLOW_AFTER_POLLS });
        await sleep(pollMs);
        if (id !== run.current) return;
        try {
          scan = await getScan(scan.id);
        } catch (error) {
          if (id === run.current) setView({ kind: "error", message: messageOf(error), repoUrl: scan.repo.url });
          return;
        }
        if (id !== run.current) return;
      }
      if (scan.status === "failed") {
        setView({ kind: "error", message: scan.error ?? "We couldn't finish scanning this repo. Your code hasn't been changed.", repoUrl: scan.repo.url });
      } else {
        setView({ kind: "results", scan });
      }
    },
    [pollMs],
  );

  const load = useCallback(
    async (ownerName: string, repoName: string) => {
      const id = ++run.current;
      setView({ kind: "loading" });
      try {
        const scan = await getLatestScan(ownerName, repoName);
        if (id === run.current) await follow(scan, id);
      } catch (error) {
        if (id !== run.current) return;
        if (error instanceof ApiError && error.status === 404) {
          setView({ kind: "form", notice: SCAN.form.notScanned, initialUrl: `https://github.com/${ownerName}/${repoName}` });
        } else {
          setView({ kind: "error", message: messageOf(error), repoUrl: `https://github.com/${ownerName}/${repoName}` });
        }
      }
    },
    [follow],
  );

  useEffect(() => {
    if (owner && repo) {
      void load(owner, repo);
    } else {
      run.current++;
      setView({ kind: "form" });
    }
    return () => {
      run.current++;
    };
  }, [owner, repo, load]);

  /** Start a scan, then move to that repo's address so the page can be shared and reloaded. */
  const start = useCallback(
    async (repoUrl: string): Promise<void> => {
      const scan = await startScan(repoUrl);
      const target = scanHash(scan.repo.owner, scan.repo.name);
      if (window.location.hash === target) {
        await load(scan.repo.owner, scan.repo.name);
      } else {
        window.location.hash = target;
      }
    },
    [load],
  );

  /** Tick or untick straight away, save it, and put it back with a message if saving fails. */
  const onTick = useCallback((finding: Finding, ticked: boolean) => {
    const apply = (value: boolean) =>
      setView((current) =>
        current.kind === "results"
          ? {
              kind: "results",
              scan: {
                ...current.scan,
                findings: current.scan.findings.map((f) => (f.id === finding.id ? { ...f, ticked: value } : f)),
              },
            }
          : current,
      );
    setTickError(false);
    apply(ticked);
    setTicked(finding.id, ticked).catch(() => {
      apply(!ticked);
      setTickError(true);
    });
  }, []);

  if (view.kind === "loading") {
    return (
      <Frame>
        <div className="flex items-center gap-1" role="status">
          <Spinner />
          <p className="type-body-lg c-muted">Loading the latest scan</p>
        </div>
      </Frame>
    );
  }

  if (view.kind === "scanning") {
    return (
      <Frame>
        <div className="flex flex-col gap-2 reading" role="status">
          <div className="flex items-center gap-1">
            <Spinner />
            <p className="type-code c-muted">{view.repo}</p>
          </div>
          <h1 className="type-h1">Scanning {view.repo}</h1>
          <p className="type-body-lg c-muted">{SCAN.scanning.body}</p>
          {view.slow && <p className="type-small c-muted">{SCAN.scanning.slow}</p>}
        </div>
      </Frame>
    );
  }

  if (view.kind === "error") {
    return <ErrorView message={view.message} repoUrl={view.repoUrl} onRetry={start} />;
  }

  if (view.kind === "results") {
    return (
      <Results
        scan={view.scan}
        tickError={tickError}
        onTick={onTick}
        onRescan={() => start(view.scan.repo.url)}
      />
    );
  }

  return <ScanForm key={view.initialUrl ?? "empty"} initialUrl={view.initialUrl} notice={view.notice} onSubmit={start} />;
}

function Frame({ children }: { children: React.ReactNode }) {
  return <section className="page py-6 flex flex-col gap-4">{children}</section>;
}

function ScanForm({ initialUrl = "", notice, onSubmit }: { initialUrl?: string; notice?: string; onSubmit: (url: string) => Promise<void> }) {
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
    <Frame>
      <div className="flex flex-col gap-1 reading">
        <h1 className="type-h1">{SCAN.form.title}</h1>
        <p className="type-body-lg c-muted">{SCAN.form.intro}</p>
      </div>
      {(notice || problem) && (
        <div className="reading">
          <Notice tone={problem ? "error" : "warning"}>{problem ?? notice}</Notice>
        </div>
      )}
      <form className="flex flex-col gap-3 reading" onSubmit={submit} noValidate>
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
              {SCAN.form.helper}
            </p>
          )}
        </div>
        <div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={busy || url.trim() === ""} aria-busy={busy}>
            {busy ? SCAN.form.submitting : SCAN.form.submit}
          </button>
        </div>
      </form>
    </Frame>
  );
}

function ErrorView({ message, repoUrl, onRetry }: { message: string; repoUrl?: string; onRetry: (url: string) => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  const [again, setAgain] = useState<string>();
  async function retry() {
    if (!repoUrl) return;
    setBusy(true);
    setAgain(undefined);
    try {
      await onRetry(repoUrl);
    } catch (error) {
      setAgain(messageOf(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Frame>
      <div className="flex flex-col items-start gap-2 reading">
        <span className="disc">
          <TriangleAlertIcon />
        </span>
        <h1 className="type-h1">{SCAN.error.title}</h1>
        <p className="type-body-lg c-muted" role="alert">
          {message}
        </p>
        {again && <Notice tone="error">{again}</Notice>}
        <div className="flex flex-wrap gap-2">
          {repoUrl && (
            <button type="button" className="btn btn-primary btn-lg" onClick={retry} disabled={busy} aria-busy={busy}>
              {SCAN.error.retry}
            </button>
          )}
          <a className="btn btn-secondary btn-lg" href="#/scan">
            {SCAN.error.other}
          </a>
        </div>
      </div>
    </Frame>
  );
}

function Results({
  scan,
  tickError,
  onTick,
  onRescan,
}: {
  scan: Scan;
  tickError: boolean;
  onTick: (finding: Finding, ticked: boolean) => void;
  onRescan: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string>();
  const unused = scan.counts["unused-package"] + scan.counts["unused-dev-dependency"] + scan.counts["unused-export"];
  const lint = scan.counts["lint-issue"];
  const ticked = scan.findings.filter((f) => f.ticked).length;
  const searched = `Searched ${plural(scan.files_scanned, "file", "files")} across ${plural(scan.packages_scanned, "package", "packages")}${
    scan.languages.length ? ` (${scan.languages.join(", ")})` : ""
  }.`;

  async function rescan() {
    setBusy(true);
    setProblem(undefined);
    try {
      await onRescan();
    } catch (error) {
      setProblem(messageOf(error));
    } finally {
      setBusy(false);
    }
  }

  const empty = scan.findings.length === 0;
  return (
    <Frame>
      <div className="flex flex-col gap-1 reading">
        <p className="type-code c-muted">Results · {scan.repo.owner}/{scan.repo.name}</p>
        {empty ? (
          <div className="flex flex-col items-start gap-2">
            <span className="disc">
              <LeafIcon />
            </span>
            <h1 className="type-h1">Nothing to prune</h1>
            <p className="type-body-lg c-muted">
              {searched} We found no unused packages or exports.
            </p>
          </div>
        ) : (
          <>
            <h1 className="type-h1">
              {unused > 0
                ? `Found ${plural(unused, "unused item", "unused items")} across ${plural(scan.packages_scanned, "package", "packages")}`
                : "We found no unused packages or exports"}
            </h1>
            <p className="type-body-lg c-muted">
              {searched}
              {lint > 0 && ` We also found ${plural(lint, "lint issue", "lint issues")}. ${SCAN.results.lintNote}`}
            </p>
          </>
        )}
      </div>

      <div className="reading flex flex-col gap-2">
        {!empty && <Notice tone="warning">{SCAN.results.notice}</Notice>}
        {problem && <Notice tone="error">{problem}</Notice>}
        {tickError && <Notice tone="error">{SCAN.results.tickError}</Notice>}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button type="button" className="btn btn-secondary" onClick={rescan} disabled={busy} aria-busy={busy}>
          {busy ? SCAN.results.rescanning : SCAN.results.rescan}
        </button>
        <a className="btn btn-secondary" href="#/scan">
          {SCAN.results.otherRepo}
        </a>
        {!empty && (
          <p className="type-small c-muted" aria-live="polite">
            {plural(ticked, "item", "items")} ticked. {SCAN.results.tickHelp}
          </p>
        )}
      </div>

      <Findings scan={scan} onTick={onTick} />
    </Frame>
  );
}
