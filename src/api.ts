export type FindingType = "unused-package" | "unused-dev-dependency" | "unused-export" | "lint-issue";
export type ScanStatus = "running" | "done" | "failed";

export interface Finding {
  id: number;
  type: FindingType;
  package: string;
  item: string;
  file_path: string;
  line: number | null;
  evidence: string;
  confidence: "safe" | "uncertain";
  language: string;
  report_only: boolean;
  ticked: boolean;
}

export interface Scan {
  id: number;
  status: ScanStatus;
  repo: { url: string; owner: string; name: string };
  started_at: string;
  finished_at: string | null;
  error: string | null;
  files_scanned: number;
  packages_scanned: number;
  languages: string[];
  counts: Record<FindingType, number>;
  /** True only for the person who made the scan while signed in. */
  can_tick: boolean;
  findings: Finding[];
}

export interface User {
  login: string;
  avatar_url: string | null;
}

export interface Me {
  user: User | null;
  sign_in_available: boolean;
  /** False when the server has no chat key, so there is nothing to ask. */
  chat_available: boolean;
}

export interface RepoSummary {
  full_name: string;
  owner: string;
  name: string;
  private: boolean;
  description: string | null;
  language: string | null;
  pushed_at: string | null;
}

/** An error from the API (or from reaching it). `message` is written to be shown to the person. */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  /** Anything else the server sent with the error, such as the items a pull request couldn't include. */
  readonly details: Record<string, unknown>;

  constructor(message: string, code: string, status: number, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

const BASE: string = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}/api${path}`, {
      headers: { "Content-Type": "application/json" },
      credentials: "include", // the sign-in cookie
      ...init,
    });
  } catch {
    throw new ApiError(
      "We couldn't reach the Lopper server. Check that it's running, then try again. Nothing has been changed.",
      "network",
      0,
    );
  }
  const data = (await response.json().catch(() => null)) as ({ error?: string; code?: string } & Record<string, unknown>) | null;
  if (!response.ok) {
    throw new ApiError(data?.error ?? "Something went wrong. Nothing has been changed.", data?.code ?? "http_error", response.status, data ?? {});
  }
  return data as T;
}

export async function startScan(repoUrl: string): Promise<Scan> {
  const { scan } = await request<{ scan: Scan }>("/scans", { method: "POST", body: JSON.stringify({ repo_url: repoUrl }) });
  return scan;
}

export async function getScan(id: number): Promise<Scan> {
  return (await request<{ scan: Scan }>(`/scans/${id}`)).scan;
}

export async function getLatestScan(owner: string, name: string): Promise<Scan> {
  return (await request<{ scan: Scan }>(`/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/scan`)).scan;
}

export interface PullRequestResult {
  pull_request: { url: string; number: number; branch: string; title: string; base: string };
  /** What the pull request changes. */
  applied: { id: number; item: string; type: FindingType; file_path: string; summary: string }[];
  /** Ticked items Lopper couldn't change on its own, with the reason. */
  skipped: SkippedChange[];
}

export interface SkippedChange {
  id: number;
  item: string;
  type: FindingType;
  reason: string;
}

/** Open a pull request that makes the changes ticked on this scan. Only the signed-in owner of the scan can. */
export async function createPullRequest(scanId: number): Promise<PullRequestResult> {
  return request<PullRequestResult>(`/scans/${scanId}/pull-request`, { method: "POST" });
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/** The server's limits on a conversation. A question can be this long, and a conversation this many messages. */
export const MAX_QUESTION_CHARS = 1000;
export const MAX_CHAT_MESSAGES = 20;

/** Ask about a finished scan. `messages` is the whole conversation so far, ending with the new question. Returns the answer. */
export async function askAboutScan(scanId: number, messages: ChatMessage[]): Promise<string> {
  const { reply } = await request<{ reply: string }>(`/scans/${scanId}/chat`, { method: "POST", body: JSON.stringify({ messages }) });
  return reply;
}

export async function setTicked(findingId: number, ticked: boolean): Promise<Finding> {
  return (await request<{ finding: Finding }>(`/findings/${findingId}`, { method: "PATCH", body: JSON.stringify({ ticked }) })).finding;
}

/** Where the "Sign in with GitHub" link goes. The server sends the browser on to GitHub and back. */
export const signInHref = `${BASE}/api/auth/github/login`;

export async function getMe(): Promise<Me> {
  return request<Me>("/auth/me");
}

export async function signOut(): Promise<void> {
  await request<{ ok: boolean }>("/auth/logout", { method: "POST" });
}

export async function listRepos(): Promise<RepoSummary[]> {
  return (await request<{ repos: RepoSummary[] }>("/repos")).repos;
}
