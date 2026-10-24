import { readFileSync } from "node:fs";
import { join } from "node:path";
import { THEME_ORDER, THEME_STORAGE_KEY, getPreference, initTheme, nextPreference, resolveTheme, setPreference, subscribe } from "./theme";
import { mockSystemTheme } from "./testing";

const root = document.documentElement;
const shown = () => root.getAttribute("data-theme");
let stop: (() => void) | undefined;

function start() {
  stop = initTheme();
}

afterEach(() => {
  stop?.();
  stop = undefined;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.localStorage.clear();
  root.removeAttribute("data-theme");
  root.style.removeProperty("--c-page");
  document.querySelector('meta[name="theme-color"]')?.remove();
});

describe("which theme is shown", () => {
  it("follows the device when nothing has been chosen", () => {
    mockSystemTheme(true);
    start();
    expect(getPreference()).toBe("system");
    expect(shown()).toBe("dark");
  });

  it("is light on a light device", () => {
    mockSystemTheme(false);
    start();
    expect(shown()).toBe("light");
  });

  it("shows what was saved, whatever the device says", () => {
    mockSystemTheme(true);
    window.localStorage.setItem(THEME_STORAGE_KEY, "light");
    start();
    expect(getPreference()).toBe("light");
    expect(shown()).toBe("light");
  });

  it("ignores a saved value it doesn't know", () => {
    mockSystemTheme(true);
    window.localStorage.setItem(THEME_STORAGE_KEY, "sepia");
    start();
    expect(getPreference()).toBe("system");
    expect(shown()).toBe("dark");
  });

  it("is light when the browser can't say what the device prefers", () => {
    vi.stubGlobal("matchMedia", undefined);
    start();
    expect(shown()).toBe("light");
  });
});

describe("choosing a theme", () => {
  it("shows it, saves it and tells whoever is listening", () => {
    mockSystemTheme(false);
    start();
    const heard = vi.fn();
    const unsubscribe = subscribe(heard);

    setPreference("dark");
    expect(shown()).toBe("dark");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");
    expect(heard).toHaveBeenCalledTimes(1);

    unsubscribe();
    setPreference("light");
    expect(heard).toHaveBeenCalledTimes(1);
  });

  it("keeps nothing for match your device, so the device decides again", () => {
    mockSystemTheme(true);
    start();
    setPreference("light");
    setPreference("system");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBeNull();
    expect(shown()).toBe("dark");
  });

  it("steps through match your device, light and dark, and round again", () => {
    expect(THEME_ORDER).toEqual(["system", "light", "dark"]);
    expect(nextPreference("system")).toBe("light");
    expect(nextPreference("light")).toBe("dark");
    expect(nextPreference("dark")).toBe("system");
  });

  it("still works when the browser won't let the page save anything", () => {
    mockSystemTheme(false);
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    start();
    expect(getPreference()).toBe("system");
    expect(() => setPreference("dark")).not.toThrow();
    expect(shown()).toBe("dark");
    expect(() => setPreference("system")).not.toThrow();
  });
});

describe("keeping up with the device and other tabs", () => {
  it("follows the device when it changes, while the choice is match your device", () => {
    const device = mockSystemTheme(false);
    start();
    expect(shown()).toBe("light");
    device.change(true);
    expect(shown()).toBe("dark");
    device.change(false);
    expect(shown()).toBe("light");
  });

  it("doesn't let the device override a theme that was chosen", () => {
    const device = mockSystemTheme(false);
    start();
    setPreference("light");
    device.change(true);
    expect(shown()).toBe("light");
  });

  it("follows a choice made in another tab", () => {
    mockSystemTheme(false);
    start();
    const heard = vi.fn();
    subscribe(heard);
    window.localStorage.setItem(THEME_STORAGE_KEY, "dark");
    window.dispatchEvent(new StorageEvent("storage", { key: THEME_STORAGE_KEY }));
    expect(getPreference()).toBe("dark");
    expect(shown()).toBe("dark");
    expect(heard).toHaveBeenCalled();
  });

  it("ignores other things changing in storage", () => {
    mockSystemTheme(false);
    start();
    window.dispatchEvent(new StorageEvent("storage", { key: "something-else" }));
    expect(shown()).toBe("light");
  });

  it("stops listening when asked to", () => {
    const device = mockSystemTheme(false);
    start();
    expect(device.listenerCount()).toBe(1);
    stop?.();
    stop = undefined;
    expect(device.listenerCount()).toBe(0);
    device.change(true);
    expect(shown()).toBe("light");
  });
});

describe("the browser's own colour", () => {
  it("is set from the page colour, so it matches the theme", () => {
    mockSystemTheme(false);
    root.style.setProperty("--c-page", "#1d2420");
    start();
    expect(document.querySelector('meta[name="theme-color"]')).toHaveAttribute("content", "#1d2420");
    root.style.setProperty("--c-page", "#eef0ea");
    setPreference("light");
    expect(document.querySelectorAll('meta[name="theme-color"]')).toHaveLength(1);
    expect(document.querySelector('meta[name="theme-color"]')).toHaveAttribute("content", "#eef0ea");
  });
});

describe("the script in index.html that picks the theme before the first paint", () => {
  const html = readFileSync(join(process.cwd(), "index.html"), "utf8");
  const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0]?.[1] ?? "";
  const runScript = () => new Function(script)();

  it("is there", () => {
    expect(script).toContain("lopper-theme");
  });

  it.each([null, "light", "dark", "system", "sepia"])("picks the same theme as the app does when %s is saved", (saved) => {
    for (const deviceIsDark of [true, false]) {
      mockSystemTheme(deviceIsDark);
      window.localStorage.clear();
      if (saved) window.localStorage.setItem(THEME_STORAGE_KEY, saved);

      root.removeAttribute("data-theme");
      runScript();
      const fromScript = shown();

      root.removeAttribute("data-theme");
      stop?.();
      start();
      expect(fromScript, `saved ${saved}, device ${deviceIsDark ? "dark" : "light"}`).toBe(shown());
      expect(fromScript).toBe(resolveTheme(getPreference()));
    }
  });

  it("doesn't fail when storage and the device setting are both unavailable, and says light", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.stubGlobal("matchMedia", undefined);
    expect(runScript).not.toThrow();
    expect(shown()).toBe("light");
  });

  it("still follows the device when only storage is blocked", () => {
    mockSystemTheme(true);
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    runScript();
    expect(shown()).toBe("dark");
  });
});
