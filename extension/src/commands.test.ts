import { describe, expect, it } from "vitest";
import {
  CommandError,
  parseGitHubUrl,
  quote,
  saveReportCommand,
  scanFolderCommand,
  scanUrlCommand,
  shellKind,
  versionCommand,
} from "./commands";

const lint = { command: "lopper", includeLint: true };
const noLint = { command: "lopper", includeLint: false };

describe("parseGitHubUrl", () => {
  it.each([
    ["https://github.com/pallets/flask", "https://github.com/pallets/flask"],
    ["https://github.com/pallets/flask.git", "https://github.com/pallets/flask"],
    ["github.com/pallets/flask/", "https://github.com/pallets/flask"],
    ["  https://www.github.com/pallets/flask ", "https://github.com/pallets/flask"],
  ])("accepts %s", (input, expected) => {
    expect(parseGitHubUrl(input)).toBe(expected);
  });

  it.each([
    "",
    "pallets/flask",
    "http://github.com/pallets/flask",
    "https://gitlab.com/pallets/flask",
    "https://github.com.evil.example/pallets/flask",
    "https://user:pass@github.com/pallets/flask",
    "https://github.com/pallets/flask/tree/main",
    "https://github.com/pallets/flask; rm -rf /",
    "https://github.com/pallets/$(whoami)",
    "https://github.com/../flask",
  ])("rejects %s", (input) => {
    expect(parseGitHubUrl(input)).toBeUndefined();
  });
});

describe("shellKind", () => {
  it("recognises the common shells", () => {
    expect(shellKind("C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "win32")).toBe("powershell");
    expect(shellKind("C:\\Program Files\\PowerShell\\7\\pwsh.exe", "win32")).toBe("powershell");
    expect(shellKind("C:\\Windows\\System32\\cmd.exe", "win32")).toBe("cmd");
    expect(shellKind("/bin/zsh", "darwin")).toBe("posix");
    expect(shellKind("/usr/bin/bash", "linux")).toBe("posix");
    expect(shellKind(undefined, "win32")).toBe("powershell");
    expect(shellKind(undefined, "linux")).toBe("posix");
  });
});

describe("quote", () => {
  it("wraps paths with spaces for each shell", () => {
    expect(quote("C:\\My Projects\\app", "powershell")).toBe("'C:\\My Projects\\app'");
    expect(quote("C:\\My Projects\\app", "cmd")).toBe('"C:\\My Projects\\app"');
    expect(quote("/home/me/my app", "posix")).toBe("'/home/me/my app'");
  });

  it("neutralises shell metacharacters", () => {
    expect(quote("a'b", "powershell")).toBe("'a''b'");
    expect(quote("a'b$(whoami)", "posix")).toBe("'a'\\''b$(whoami)'");
    expect(quote("$(whoami)`x`", "powershell")).toBe("'$(whoami)`x`'");
  });

  it("refuses what it can't pass safely", () => {
    expect(() => quote("a\nb", "posix")).toThrow(CommandError);
    expect(() => quote("a&calc", "cmd")).toThrow(CommandError);
    expect(() => quote("100%", "cmd")).toThrow(CommandError);
  });
});

describe("commands", () => {
  it("scans a folder", () => {
    expect(scanFolderCommand("/work/app", lint, "posix")).toBe("lopper scan '/work/app'");
    expect(scanFolderCommand("C:\\work\\app", noLint, "powershell")).toBe("lopper scan 'C:\\work\\app' --no-lint");
  });

  it("scans a repo URL after normalising it", () => {
    expect(scanUrlCommand("github.com/pallets/flask.git", lint, "posix")).toBe("lopper scan --url 'https://github.com/pallets/flask'");
  });

  it("refuses a URL that isn't a GitHub repo, so nothing reaches the terminal", () => {
    expect(() => scanUrlCommand("https://evil.example/x/y; calc", lint, "posix")).toThrow(/GitHub repo URL/);
  });

  it("saves a JSON report next to the scanned folder", () => {
    expect(saveReportCommand("/work/app", "lopper-report.json", lint, "posix")).toBe(
      "lopper scan '/work/app' --format json --output '/work/app/lopper-report.json'",
    );
    expect(saveReportCommand("C:\\work\\app", "r.json", noLint, "powershell")).toBe(
      "lopper scan 'C:\\work\\app' --format json --output 'C:\\work\\app\\r.json' --no-lint",
    );
  });

  it("only writes the report as a plain file name", () => {
    for (const bad of ["", "../x.json", "a/b.json", "a\\b.json", ".."]) {
      expect(() => saveReportCommand("/work", bad, lint, "posix")).toThrow(CommandError);
    }
  });

  it("uses the call operator in PowerShell when the command has spaces or quotes", () => {
    const custom = { command: '"C:\\Program Files\\Lopper\\lopper.exe"', includeLint: true };
    expect(scanFolderCommand("C:\\w", custom, "powershell")).toBe(`& "C:\\Program Files\\Lopper\\lopper.exe" scan 'C:\\w'`);
    expect(scanFolderCommand("C:\\w", custom, "cmd")).toBe(`"C:\\Program Files\\Lopper\\lopper.exe" scan "C:\\w"`);
    expect(scanFolderCommand("/w", { command: "python -m lopper.cli", includeLint: true }, "posix")).toBe("python -m lopper.cli scan '/w'");
  });

  it("checks the install with --version", () => {
    expect(versionCommand(lint, "posix")).toBe("lopper --version");
  });
});
