import * as vscode from "vscode";
import {
  CommandError,
  parseGitHubUrl,
  saveReportCommand,
  scanFolderCommand,
  scanUrlCommand,
  shellKind,
  versionCommand,
  type ScanOptions,
  type ShellKind,
} from "./commands";

const TERMINAL_NAME = "Lopper";

function options(): ScanOptions {
  const config = vscode.workspace.getConfiguration("lopper");
  return {
    command: config.get<string>("command", "lopper").trim() || "lopper",
    includeLint: config.get<boolean>("includeLint", true),
  };
}

function currentShell(): ShellKind {
  return shellKind(vscode.env.shell, process.platform);
}

function lopperTerminal(cwd?: string): vscode.Terminal {
  const existing = vscode.window.terminals.find((t) => t.name === TERMINAL_NAME && t.exitStatus === undefined);
  return existing ?? vscode.window.createTerminal({ name: TERMINAL_NAME, cwd });
}

function run(commandLine: string, cwd?: string): void {
  const terminal = lopperTerminal(cwd);
  terminal.show(true);
  terminal.sendText(commandLine);
}

async function pickWorkspaceFolder(): Promise<vscode.WorkspaceFolder | undefined> {
  const folders = vscode.workspace.workspaceFolders ?? [];
  if (folders.length === 0) {
    vscode.window.showInformationMessage("Open a folder first, then run Lopper again. Nothing has been changed.");
    return undefined;
  }
  if (folders.length === 1) {
    return folders[0];
  }
  return vscode.window.showWorkspaceFolderPick({ placeHolder: "Which folder should Lopper scan?" });
}

function fail(error: unknown): void {
  const message = error instanceof CommandError ? error.message : "Something went wrong starting Lopper. Nothing has been changed.";
  vscode.window.showErrorMessage(message);
}

export function activate(context: vscode.ExtensionContext): void {
  const scanFolder = (folder: string) => {
    try {
      run(scanFolderCommand(folder, options(), currentShell()), folder);
    } catch (error) {
      fail(error);
    }
  };

  context.subscriptions.push(
    vscode.commands.registerCommand("lopper.scanWorkspace", async () => {
      const folder = await pickWorkspaceFolder();
      if (folder) {
        scanFolder(folder.uri.fsPath);
      }
    }),

    vscode.commands.registerCommand("lopper.scanFolder", (uri?: vscode.Uri) => {
      if (uri) {
        scanFolder(uri.fsPath);
      } else {
        void vscode.commands.executeCommand("lopper.scanWorkspace");
      }
    }),

    vscode.commands.registerCommand("lopper.scanRepoUrl", async () => {
      const input = await vscode.window.showInputBox({
        title: "Scan a GitHub repo",
        prompt: "Paste the URL of a public GitHub repo. We read it and never change it.",
        placeHolder: "https://github.com/owner/repo",
        ignoreFocusOut: true,
        validateInput: (value) =>
          value.trim() === "" || parseGitHubUrl(value)
            ? undefined
            : "That doesn't look like a GitHub repo URL. Try https://github.com/owner/repo.",
      });
      if (!input) {
        return;
      }
      try {
        run(scanUrlCommand(input, options(), currentShell()), vscode.workspace.workspaceFolders?.[0]?.uri.fsPath);
      } catch (error) {
        fail(error);
      }
    }),

    vscode.commands.registerCommand("lopper.saveReport", async () => {
      const folder = await pickWorkspaceFolder();
      if (!folder) {
        return;
      }
      try {
        const reportFile = vscode.workspace.getConfiguration("lopper").get<string>("reportFile", "lopper-report.json");
        run(saveReportCommand(folder.uri.fsPath, reportFile, options(), currentShell()), folder.uri.fsPath);
      } catch (error) {
        fail(error);
      }
    }),

    vscode.commands.registerCommand("lopper.checkInstall", () => {
      try {
        run(versionCommand(options(), currentShell()), vscode.workspace.workspaceFolders?.[0]?.uri.fsPath);
      } catch (error) {
        fail(error);
      }
    }),
  );

  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 0);
  status.text = "$(search) Lopper";
  status.tooltip = "Scan this workspace for unused code. Lopper reads your code and never changes it.";
  status.command = "lopper.scanWorkspace";
  status.show();
  context.subscriptions.push(status);
}

export function deactivate(): void {}
