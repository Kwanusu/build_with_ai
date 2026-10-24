import { useSyncExternalStore } from "react";

/** What the person chose. "system" follows the device and is the default. */
export type ThemePreference = "system" | "light" | "dark";
/** What is on screen. */
export type ResolvedTheme = "light" | "dark";

export const THEME_STORAGE_KEY = "lopper-theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";

/** The order the toggle steps through. */
export const THEME_ORDER: readonly ThemePreference[] = ["system", "light", "dark"];

const isPreference = (value: unknown): value is ThemePreference => value === "system" || value === "light" || value === "dark";

export const nextPreference = (current: ThemePreference): ThemePreference => THEME_ORDER[(THEME_ORDER.indexOf(current) + 1) % THEME_ORDER.length];

/** What was saved, or "system". Storage can be blocked or empty (private windows, cleared site data), so it never throws. */
function storedPreference(): ThemePreference {
  try {
    const value = window.localStorage.getItem(THEME_STORAGE_KEY);
    return isPreference(value) ? value : "system";
  } catch {
    return "system";
  }
}

function systemTheme(): ResolvedTheme {
  try {
    return window.matchMedia(DARK_QUERY).matches ? "dark" : "light";
  } catch {
    return "light";
  }
}

export const resolveTheme = (preference: ThemePreference): ResolvedTheme => (preference === "system" ? systemTheme() : preference);

let preference: ThemePreference = "system";
const listeners = new Set<() => void>();
const notify = () => listeners.forEach((listener) => listener());

/** Phones colour their address bar from this. It is read from the page colour role, so it can't drift from the stylesheet. */
function syncBrowserColour() {
  const colour = getComputedStyle(document.documentElement).getPropertyValue("--c-page").trim();
  if (!colour) return;
  let meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement("meta");
    meta.name = "theme-color";
    document.head.appendChild(meta);
  }
  meta.content = colour;
}

function apply() {
  document.documentElement.setAttribute("data-theme", resolveTheme(preference));
  syncBrowserColour();
}

export const getPreference = (): ThemePreference => preference;

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => void listeners.delete(listener);
}

/** Choose a theme: remember it (nothing is kept for "system"), show it, and tell the toggles. */
export function setPreference(next: ThemePreference) {
  preference = next;
  try {
    if (next === "system") window.localStorage.removeItem(THEME_STORAGE_KEY);
    else window.localStorage.setItem(THEME_STORAGE_KEY, next);
  } catch {
    // The choice still applies until the page is closed.
  }
  apply();
  notify();
}

/**
 * Start up: read what was saved and show it, then keep following the device while the choice is "system", and follow a
 * change made in another tab. index.html has already set data-theme before the first paint, so this doesn't flash.
 * Returns a function that stops listening.
 */
export function initTheme(): () => void {
  preference = storedPreference();
  apply();
  notify();

  let query: MediaQueryList | undefined;
  try {
    query = window.matchMedia(DARK_QUERY);
  } catch {
    query = undefined;
  }
  const onSystemChange = () => {
    if (preference === "system") apply();
  };
  const onStorage = (event: StorageEvent) => {
    if (event.key !== THEME_STORAGE_KEY && event.key !== null) return;
    preference = storedPreference();
    apply();
    notify();
  };
  query?.addEventListener("change", onSystemChange);
  window.addEventListener("storage", onStorage);
  return () => {
    query?.removeEventListener("change", onSystemChange);
    window.removeEventListener("storage", onStorage);
  };
}

/** The current choice, and a way to step to the next one. Every toggle on the page shares it. */
export function useTheme() {
  const current = useSyncExternalStore(subscribe, getPreference, () => "system" as ThemePreference);
  return { preference: current, next: nextPreference(current), cycle: () => setPreference(nextPreference(getPreference())) };
}
