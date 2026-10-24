import type { Finding, FindingType, RepoSummary, Scan } from "./api";
import type { AuthValue } from "./auth";

let nextId = 1;

export function finding(overrides: Partial<Finding> = {}): Finding {
  return {
    id: nextId++,
    type: "unused-export",
    package: "packages/billing",
    item: "formatInvoice",
    file_path: "packages/billing/src/format.ts",
    line: 42,
    evidence: "formatInvoice is exported from packages/billing/src/format.ts:42 and no other file mentions it. Searched 1,208 source files across 12 packages.",
    confidence: "safe",
    language: "typescript",
    report_only: false,
    ticked: true,
    ...overrides,
  };
}

export function scan(overrides: Partial<Scan> = {}, findings: Finding[] = []): Scan {
  const counts = { "unused-package": 0, "unused-dev-dependency": 0, "unused-export": 0, "lint-issue": 0 } as Record<FindingType, number>;
  for (const f of findings) counts[f.type]++;
  return {
    id: 1,
    status: "done",
    repo: { url: "https://github.com/acme/web-platform", owner: "acme", name: "web-platform" },
    started_at: "2026-10-23T17:00:00+03:00",
    finished_at: "2026-10-23T17:00:09+03:00",
    error: null,
    files_scanned: 1208,
    packages_scanned: 12,
    languages: ["javascript"],
    counts,
    can_tick: true,
    findings,
    ...overrides,
  };
}

type Handler = (body: unknown, url: URL) => { status?: number; body: unknown } | Promise<{ status?: number; body: unknown }>;

/** Stand in for fetch. Keys look like "GET /api/scans/1". Records every call in `calls`. */
export function mockApi(handlers: Record<string, Handler>) {
  const calls: { key: string; body: unknown }[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), "http://localhost");
    const key = `${init?.method ?? "GET"} ${url.pathname}`;
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ key, body });
    const handler = handlers[key];
    if (!handler) throw new Error(`Unexpected request: ${key}`);
    const { status = 200, body: payload } = await handler(body, url);
    return new Response(JSON.stringify(payload), { status, headers: { "Content-Type": "application/json" } });
  });
  vi.stubGlobal("fetch", fetchMock);
  return { calls, fetchMock };
}


export function repoSummary(overrides: Partial<RepoSummary> = {}): RepoSummary {
  return {
    full_name: "octo/web",
    owner: "octo",
    name: "web",
    private: false,
    description: null,
    language: "TypeScript",
    pushed_at: "2026-10-20T10:00:00Z",
    ...overrides,
  };
}

/** A value for AuthContext.Provider in tests. */
export function authValue(overrides: Partial<AuthValue> = {}): AuthValue {
  return {
    status: "ready",
    user: null,
    signInAvailable: false,
    chatAvailable: false,
    refresh: vi.fn(async () => {}),
    signOut: vi.fn(async () => {}),
    ...overrides,
  };
}

export const OCTO = { login: "octo", avatar_url: "https://avatars.example/octo.png" };
