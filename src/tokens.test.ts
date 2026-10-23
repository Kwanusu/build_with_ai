import { execFileSync } from "node:child_process";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const read = (path: string) => readFileSync(join(root, path), "utf8");

function sourceFiles(dir: string): string[] {
  return readdirSync(join(root, dir)).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(join(root, path)).isDirectory()) return sourceFiles(path);
    return /\.(tsx?|css)$/.test(name) && !/\.test\./.test(name) ? [path] : [];
  });
}

describe("design tokens", () => {
  const theme = read("styles.css");
  const defined = new Set([...theme.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));

  it("styles.css is the Tailwind theme exported from DESIGN.md", () => {
    expect(theme).toContain("@theme {");
    expect(theme).toContain("--color-primary: #36503f;");
    expect(theme).toContain("--color-dark-primary: #a9c0a6;");
    expect(theme).toContain("--radius-control: 6px;");
    expect(theme).toContain("--text-display: 60px;");
    expect(theme).toContain("--text-h1: 48px;");
    expect(theme).toContain("--text-h2: 36px;");
  });

  it("styles.css is in sync with DESIGN.md (run `npm run tokens` if this fails)", () => {
    const cli = join(root, "node_modules", "@google", "design.md", "dist", "index.js");
    const exported = execFileSync(process.execPath, [cli, "export", "--format", "css-tailwind", "DESIGN.md"], {
      cwd: root,
      encoding: "utf8",
    });
    const normalise = (s: string) => s.replace(/\r\n/g, "\n").trim();
    expect(normalise(theme)).toContain(normalise(exported));
  });

  it("assets/logo has every logo file DESIGN.md lists, with no scripts or external links", () => {
    const files = [
      "lopper-wordmark-light.svg",
      "lopper-wordmark-dark.svg",
      "lopper-lockup-light.svg",
      "lopper-lockup-dark.svg",
      "lopper-app-icon.svg",
    ];
    for (const file of files) {
      const svg = read(`assets/logo/${file}`);
      expect(svg.startsWith("<svg")).toBe(true);
      expect(svg).not.toMatch(/<script|onload=|href="https?:/i);
    }
  });

  it("src/index.css only uses variables that styles.css or itself defines", () => {
    const css = read("src/index.css");
    const own = new Set([...css.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));
    const used = [...css.matchAll(/var\((--[\w-]+)/g)].map((m) => m[1]);
    const missing = used.filter((name) => !defined.has(name) && !own.has(name));
    expect(missing).toEqual([]);
  });

  it("no source file hard-codes a colour", () => {
    const offenders = sourceFiles("src").filter((file) => /#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(/.test(read(file)));
    expect(offenders).toEqual([]);
  });

  it("dark mode defines every semantic role the light theme does", () => {
    const css = read("src/index.css");
    const roles = (block: string) =>
      new Set([...block.matchAll(/(--c-[\w-]+)\s*:/g)].map((m) => m[1]));
    const light = roles(css.slice(css.indexOf(":root"), css.indexOf('[data-theme="dark"] {')));
    const dark = roles(css.slice(css.indexOf('[data-theme="dark"] {'), css.indexOf("@layer base")));
    expect([...light].sort()).toEqual([...dark].sort());
  });
});
