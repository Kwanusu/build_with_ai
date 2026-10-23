import { useMemo, useSyncExternalStore } from "react";

export type Route = { name: "landing" } | { name: "scan"; owner?: string; repo?: string };

const SCAN_HASH = /^#\/scan(?:\/([^/]+)\/([^/]+))?\/?$/;

export function parseHash(hash: string): Route {
  const match = SCAN_HASH.exec(hash);
  if (match) {
    return match[1] && match[2]
      ? { name: "scan", owner: decodeURIComponent(match[1]), repo: decodeURIComponent(match[2]) }
      : { name: "scan" };
  }
  return { name: "landing" };
}

export function scanHash(owner?: string, repo?: string): string {
  return owner && repo ? `#/scan/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}` : "#/scan";
}

function subscribe(onChange: () => void): () => void {
  window.addEventListener("hashchange", onChange);
  return () => window.removeEventListener("hashchange", onChange);
}

/** The current page, from the address's #hash. The landing page is every hash that isn't #/scan. */
export function useRoute(): Route {
  const hash = useSyncExternalStore(subscribe, () => window.location.hash, () => "");
  return useMemo(() => parseHash(hash), [hash]);
}
