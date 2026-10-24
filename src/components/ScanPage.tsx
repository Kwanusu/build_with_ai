import { useCallback, useEffect, useRef, useState } from "react";
import {
  ApiError,
  createPullRequest,
  getLatestScan,
  getScan,
  setTicked,
  signInHref,
  startScan,
  type Finding,
  type PullRequestResult,
  type Scan,
  type SkippedChange,
} from "../api";
import { useAuth } from "../auth";
import { CANNOT_TICK, CONNECT, SCAN } from "../content";
import { scanHash } from "../route";
import { Connect, Frame } from "./Connect";
import { Findings } from "./Findings";
import { PullRequestCreated } from "./PullRequestCreated";
import { ScanChat } from "./ScanChat";
import { Button, LeafIcon, Notice, Spinner, TriangleAlertIcon } from "./ui";

type View =
  | { kind: "form"; notice?: string; initialUrl?: string }
  | { kind: "loading" }
  | { kind: "scanning"; repo: string; slow: boolean }
  | { kind: "results"; scan: Scan; pull?: PullRequestResult }
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
              ...current,
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
        <div className="flex flex-col items-start gap-2 reading" role="status">
          <span className="disc">
            <Spinner large />
          </span>
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

  if (view.kind === "results" && view.pull) {
    const { scan } = view;
    return (
      <PullRequestCreated
        result={view.pull}
        repo={`${scan.repo.owner}/${scan.repo.name}`}
        onBack={() => setView({ kind: "results", scan })}
      />
    );
  }

  if (view.kind === "results") {
    const { scan } = view;
    return (
      <Results
        scan={scan}
        tickError={tickError}
        onTick={onTick}
        onRescan={() => start(scan.repo.url)}
        onCreatePr={async () => {
          const pull = await createPullRequest(scan.id);
          setView({ kind: "results", scan, pull });
        }}
      />
    );
  }

  return <Connect key={view.initialUrl ?? "empty"} initialUrl={view.initialUrl} notice={view.notice} onSubmit={start} />;
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
            <Button variant="primary" size="lg" onClick={retry} disabled={busy} busy={busy}>
              {SCAN.error.retry}
            </Button>
          )}
          <Button href="#/scan" size="lg">
            {SCAN.error.other}
          </Button>
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
  onCreatePr,
}: {
  scan: Scan;
  tickError: boolean;
  onTick: (finding: Finding, ticked: boolean) => void;
  onRescan: () => Promise<void>;
  onCreatePr: () => Promise<void>;
}) {
  const auth = useAuth();
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string>();
  const [creating, setCreating] = useState(false);
  const [prProblem, setPrProblem] = useState<{ message: string; skipped: SkippedChange[] }>();
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

  async function createPr() {
    setCreating(true);
    setPrProblem(undefined);
    try {
      await onCreatePr();
    } catch (error) {
      const skipped = error instanceof ApiError && Array.isArray(error.details.skipped) ? (error.details.skipped as SkippedChange[]) : [];
      setPrProblem({ message: messageOf(error), skipped });
      setCreating(false);
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
        {!empty && !scan.can_tick && (
          <Notice tone="warning">
            {auth.user ? CANNOT_TICK.publicScan : CANNOT_TICK.signedOut}
            {!auth.user && auth.signInAvailable && (
              <>
                {" "}
                <a className="c-primary" href={signInHref}>
                  {CONNECT.signedOut.signIn}
                </a>
              </>
            )}
          </Notice>
        )}
        {problem && <Notice tone="error">{problem}</Notice>}
        {prProblem && (
          <Notice tone="error">
            {prProblem.message}
            {prProblem.skipped.length > 0 && (
              <ul className="list-none p-0 m-0 mt-1 flex flex-col gap-1">
                {prProblem.skipped.map((change) => (
                  <li key={change.id}>
                    <span className="type-code">{change.item}</span> <span className="type-small">{change.reason}</span>
                  </li>
                ))}
              </ul>
            )}
          </Notice>
        )}
        {tickError && <Notice tone="error">{SCAN.results.tickError}</Notice>}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {!empty && scan.can_tick && (
          <Button variant="primary" onClick={createPr} disabled={creating || ticked === 0} busy={creating}>
            {creating && <Spinner />}
            {creating ? SCAN.results.creatingPr : SCAN.results.createPr}
          </Button>
        )}
        <Button onClick={rescan} disabled={busy} busy={busy}>
          {busy ? SCAN.results.rescanning : SCAN.results.rescan}
        </Button>
        <Button href="#/scan">{SCAN.results.otherRepo}</Button>
        {!empty && scan.can_tick && (
          <p className="type-small c-muted" aria-live="polite">
            {plural(ticked, "item", "items")} ticked. {ticked === 0 ? SCAN.results.prHelp : SCAN.results.tickHelp}
          </p>
        )}
      </div>

      {!empty && scan.can_tick && <p className="type-small c-muted reading">{SCAN.results.prScope}</p>}

      {!empty && auth.chatAvailable && <ScanChat key={scan.id} scanId={scan.id} />}

      <Findings scan={scan} onTick={onTick} />
    </Frame>
  );
}
