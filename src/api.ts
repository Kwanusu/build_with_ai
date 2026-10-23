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
  findings: Finding[];
}

/** An error from the API (or from reaching it). `message` is written to be shown to the person. */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

const BASE: string = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}/api${path}`, { headers: { "Content-Type": "application/json" }, ...init });
  } catch {
    throw new ApiError(
      "We couldn't reach the Lopper server. Check that it's running, then try again. Nothing has been changed.",
      "network",
      0,
    );
  }
  const data = (await response.json().catch(() => null)) as { error?: string; code?: string } | null;
  if (!response.ok) {
    throw new ApiError(data?.error ?? "Something went wrong. Nothing has been changed.", data?.code ?? "http_error", response.status);
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

export async function setTicked(findingId: number, ticked: boolean): Promise<Finding> {
  return (await request<{ finding: Finding }>(`/findings/${findingId}`, { method: "PATCH", body: JSON.stringify({ ticked }) })).finding;
}
