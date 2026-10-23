/**
 * Building the terminal commands the extension runs. This file has no VS Code imports so it can be
 * tested on its own. Everything a person types or picks is validated and quoted for their shell.
 */

export type ShellKind = "powershell" | "cmd" | "posix";

export interface ScanOptions {
  /** The command that runs Lopper, from the `lopper.command` setting. It is the user's own and is not quoted. */
  command: string;
  includeLint: boolean;
}

const GITHUB_URL = /^(?:https:\/\/)?(?:www\.)?github\.com\/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))\/([A-Za-z0-9_.-]{1,100}?)(?:\.git)?\/?$/;

export class CommandError extends Error {}

/** The normalised https URL for a pasted GitHub repo, or undefined if it isn't one. */
export function parseGitHubUrl(input: string): string | undefined {
  const match = GITHUB_URL.exec(input.trim());
  if (!match || match[2] === "." || match[2] === "..") {
    return undefined;
  }
  return `https://github.com/${match[1]}/${match[2]}`;
}

export function shellKind(shellPath: string | undefined, platform: string): ShellKind {
  const name = (shellPath ?? "").replace(/\\/g, "/").split("/").pop()?.toLowerCase() ?? "";
  if (name.includes("pwsh") || name.includes("powershell")) {
    return "powershell";
  }
  if (name === "cmd.exe" || name === "cmd") {
    return "cmd";
  }
  if (name === "" && platform === "win32") {
    return "powershell";
  }
  return "posix";
}

/** Quote one argument for the given shell. Throws if the value can't be passed safely. */
export function quote(value: string, shell: ShellKind): string {
  if (/[\u0000-\u001f\u007f]/.test(value)) {
    throw new CommandError("That path has a control character in it, so we can't pass it to the terminal safely.");
  }
  switch (shell) {
    case "powershell":
      return `'${value.replace(/'/g, "''")}'`;
    case "cmd":
      if (/["%^&|<>!]/.test(value)) {
        throw new CommandError("That path has a character cmd.exe can't take safely. Open a PowerShell terminal, or rename the folder.");
      }
      return `"${value}"`;
    default:
      return `'${value.replace(/'/g, `'\\''`)}'`;
  }
}

function withFlags(parts: string[], options: ScanOptions): string[] {
  return options.includeLint ? parts : [...parts, "--no-lint"];
}

function invoke(command: string, shell: ShellKind): string {
  // PowerShell needs the call operator to run a command held in a string that contains quotes or spaces.
  return shell === "powershell" && /[ "]/.test(command) && !command.startsWith("&") ? `& ${command}` : command;
}

export function scanFolderCommand(folder: string, options: ScanOptions, shell: ShellKind): string {
  return withFlags([invoke(options.command, shell), "scan", quote(folder, shell)], options).join(" ");
}

export function scanUrlCommand(url: string, options: ScanOptions, shell: ShellKind): string {
  const normalised = parseGitHubUrl(url);
  if (!normalised) {
    throw new CommandError("That doesn't look like a GitHub repo URL. Paste one like https://github.com/owner/repo.");
  }
  return withFlags([invoke(options.command, shell), "scan", "--url", quote(normalised, shell)], options).join(" ");
}

export function saveReportCommand(folder: string, reportFile: string, options: ScanOptions, shell: ShellKind): string {
  if (!reportFile.trim() || /[\\/]|^\.\.?$/.test(reportFile)) {
    throw new CommandError("Set lopper.reportFile to a plain file name, like lopper-report.json.");
  }
  return withFlags(
    [invoke(options.command, shell), "scan", quote(folder, shell), "--format", "json", "--output", quote(`${folder}${folder.includes("\\") ? "\\" : "/"}${reportFile}`, shell)],
    options,
  ).join(" ");
}

export function versionCommand(options: ScanOptions, shell: ShellKind): string {
  return `${invoke(options.command, shell)} --version`;
}
