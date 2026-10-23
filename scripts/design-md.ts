import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const cli = join(root, "node_modules", "@google", "design.md", "dist", "index.js");

// The `design.md` bin shim prints nothing on some machines, so call the CLI with node directly.
function run(...args: string[]): string {
  return execFileSync(process.execPath, [cli, ...args], { cwd: root, encoding: "utf8" });
}

export function exportTheme(): string {
  const theme = run("export", "--format", "css-tailwind", "DESIGN.md");
  return `@import "tailwindcss";\n\n/* Generated from DESIGN.md by \`npm run tokens\`. Do not edit by hand. */\n${theme}`;
}

const command = process.argv[2];

if (command === "tokens") {
  writeFileSync(join(root, "styles.css"), exportTheme());
  console.log("styles.css written from DESIGN.md");
} else if (command === "lint") {
  let out = "";
  try {
    out = run("lint", "DESIGN.md");
  } catch (error) {
    out = (error as { stdout?: string }).stdout ?? "";
    process.exitCode = 1;
  }
  const { findings, summary } = JSON.parse(out) as {
    findings: { severity: string; rule?: string; path?: string; message: string }[];
    summary: { errors: number; warnings: number };
  };
  const blocking = findings.filter((f) => f.severity === "error" || f.rule === "contrast-ratio");
  for (const f of blocking) console.log(`${f.severity} ${f.path ?? ""} ${f.message}`);
  console.log(`errors: ${summary.errors}, warnings: ${summary.warnings}, contrast warnings: ${blocking.filter((f) => f.rule === "contrast-ratio").length}`);
  if (blocking.length > 0) process.exitCode = 1;
}
