import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { THEME_STORAGE_KEY, initTheme } from "../theme";
import { mockSystemTheme } from "../testing";
import { ThemeToggle } from "./ThemeToggle";

let stop: (() => void) | undefined;

afterEach(() => {
  stop?.();
  stop = undefined;
  vi.unstubAllGlobals();
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});

const shown = () => document.documentElement.getAttribute("data-theme");
const toggles = (name: string) => screen.getAllByRole("button", { name });

function setUp(saved?: string, deviceIsDark = false) {
  mockSystemTheme(deviceIsDark);
  if (saved) window.localStorage.setItem(THEME_STORAGE_KEY, saved);
  stop = initTheme();
  render(
    <>
      <ThemeToggle />
      <ThemeToggle size="lg" />
    </>,
  );
}

describe("the theme toggle", () => {
  it("says what is on and what pressing it does", () => {
    setUp();
    expect(toggles("Theme: match your device. Switch to light.")).toHaveLength(2);
  });

  it("steps through light, dark and back to match your device, showing and saving each", async () => {
    setUp();
    await userEvent.click(toggles("Theme: match your device. Switch to light.")[0]);
    expect(shown()).toBe("light");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("light");

    await userEvent.click(toggles("Theme: light. Switch to dark.")[0]);
    expect(shown()).toBe("dark");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");

    await userEvent.click(toggles("Theme: dark. Switch to match your device.")[0]);
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBeNull();
    expect(shown()).toBe("light"); // the device is light
    expect(toggles("Theme: match your device. Switch to light.")).toHaveLength(2);
  });

  it("goes back to what the device wants, which may be dark", async () => {
    setUp("light", true);
    expect(shown()).toBe("light");
    await userEvent.click(toggles("Theme: light. Switch to dark.")[0]);
    await userEvent.click(toggles("Theme: dark. Switch to match your device.")[0]);
    expect(shown()).toBe("dark");
  });

  it("starts from what was saved", () => {
    setUp("dark");
    expect(toggles("Theme: dark. Switch to match your device.")).toHaveLength(2);
    expect(shown()).toBe("dark");
  });

  it("keeps every toggle on the page in step, because they share the choice", async () => {
    setUp();
    await userEvent.click(toggles("Theme: match your device. Switch to light.")[1]);
    expect(toggles("Theme: light. Switch to dark.")).toHaveLength(2);
  });

  it("is an icon button the size it was asked to be, with a hidden icon and a tooltip", () => {
    setUp();
    const [small, large] = toggles("Theme: match your device. Switch to light.");
    expect(small).toHaveClass("icon-btn");
    expect(small).not.toHaveClass("icon-btn-lg");
    expect(large).toHaveClass("icon-btn-lg");
    expect(small).toHaveAttribute("title", "Theme: match your device. Switch to light.");
    expect(small.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  });

  it("shows a different icon for each choice", async () => {
    setUp();
    const icon = () => screen.getAllByRole("button")[0].querySelector("svg")!.innerHTML;
    const device = icon();
    await userEvent.click(screen.getAllByRole("button")[0]);
    const light = icon();
    await userEvent.click(screen.getAllByRole("button")[0]);
    const dark = icon();
    expect(new Set([device, light, dark]).size).toBe(3);
  });

  it("is never the page's one main action", () => {
    setUp();
    expect(document.querySelectorAll(".btn-primary")).toHaveLength(0);
  });
});
