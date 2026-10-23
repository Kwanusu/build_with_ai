import { render, screen, within } from "@testing-library/react";
import { App } from "./App";
import { CTA_LABEL, NAV_LINKS } from "./content";

describe("landing page", () => {
  it("has one h1 with the headline", () => {
    render(<App />);
    const h1 = screen.getAllByRole("heading", { level: 1 });
    expect(h1).toHaveLength(1);
    expect(h1[0]).toHaveTextContent("Prune dead code with the evidence in front of you");
  });

  it("has exactly one ochre (primary) action, in the hero", () => {
    const { container } = render(<App />);
    const primary = container.querySelectorAll(".btn-primary");
    expect(primary).toHaveLength(1);
    expect(primary[0]).toHaveTextContent(CTA_LABEL);
    expect(primary[0].closest("section")).toBe(container.querySelector("main section"));
  });

  it("offers the connect action in the header, hero and closing section", () => {
    render(<App />);
    expect(screen.getAllByRole("link", { name: CTA_LABEL })).toHaveLength(3);
  });

  it("links every nav item to a section that exists", () => {
    const { container } = render(<App />);
    const nav = screen.getByRole("navigation", { name: "Main" });
    for (const link of NAV_LINKS) {
      expect(within(nav).getByRole("link", { name: link.label })).toHaveAttribute("href", link.href);
      expect(container.querySelector(link.href)).not.toBeNull();
    }
  });

  it("says nothing is removed until the pull request is merged, before the main action", () => {
    render(<App />);
    expect(
      screen.getAllByText(/Nothing will be removed until you merge the pull request\./).length,
    ).toBeGreaterThanOrEqual(2);
  });

  it("shows the evidence path and a status word with every example finding", () => {
    render(<App />);
    const results = screen.getByRole("group", { name: "Example results screen" });
    const items = within(results).getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(within(items[0]).getByText("packages/billing/src/format.ts:42")).toBeInTheDocument();
    expect(within(items[0]).getByText("Safe to remove")).toBeInTheDocument();
    expect(within(items[0]).getByRole("img", { name: "Ticked" })).toBeInTheDocument();
    expect(within(items[1]).getByText("Needs a closer look")).toBeInTheDocument();
    expect(within(items[1]).getByRole("img", { name: "Not ticked" })).toBeInTheDocument();
  });

  it("uses the supplied logo files in the header and footer", () => {
    const { container } = render(<App />);
    const header = container.querySelector("header")!;
    const footer = container.querySelector("footer")!;
    expect(within(header).getByRole("link", { name: "Lopper home" })).toHaveAttribute("href", "#top");
    expect(header.querySelector(".logo-lockup .logo-light")).toHaveAttribute("src", expect.stringContaining("lopper-lockup-light.svg"));
    expect(header.querySelector(".logo-lockup .logo-dark")).toHaveAttribute("src", expect.stringContaining("lopper-lockup-dark.svg"));
    expect(footer.querySelector(".logo-wordmark .logo-light")).toHaveAttribute("src", expect.stringContaining("lopper-wordmark-light.svg"));
    expect(footer.querySelector(".logo-wordmark .logo-dark")).toHaveAttribute("src", expect.stringContaining("lopper-wordmark-dark.svg"));
  });

  it("hides the dark logo copy from screen readers so the name is read once", () => {
    const { container } = render(<App />);
    for (const img of container.querySelectorAll("img.logo-dark")) {
      expect(img).toHaveAttribute("alt", "");
      expect(img).toHaveAttribute("aria-hidden", "true");
    }
  });

  it("shows a copyright with the current year in the footer", () => {
    const { container } = render(<App />);
    const footer = container.querySelector("footer")!;
    expect(footer).toHaveTextContent(`© ${new Date().getFullYear()} Lopper. All rights reserved.`);
  });

  it("labels lint issues as report only", () => {
    render(<App />);
    expect(screen.getByText("Report only")).toBeInTheDocument();
  });

  it("follows the voice rules in DESIGN.md", () => {
    const { container } = render(<App />);
    const text = container.textContent ?? "";
    expect(text).not.toContain("!");
    for (const word of ["simply", "just", "easy", "nuke", "magic", "guaranteed", "bloat", "blazing"]) {
      expect(text.toLowerCase()).not.toMatch(new RegExp(`\\b${word}\\b`));
    }
    expect(text).not.toMatch(/\b(OK|Submit)\b/);
  });

  it("uses sentence case for headings", () => {
    render(<App />);
    for (const heading of screen.getAllByRole("heading")) {
      const words = (heading.textContent ?? "").split(" ").slice(1);
      for (const word of words) {
        // Only proper names and code identifiers may start with a capital after the first word.
        if (/^[A-Z]/.test(word)) expect(["Lopper", "JavaScript", "TypeScript", "Python", "Go", "GitHub"]).toContain(word);
      }
    }
  });
});
