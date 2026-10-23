import { beforeEach, describe, expect, it, vi } from "vitest";

type Handler = (...args: unknown[]) => unknown;

const state = vi.hoisted(() => ({
  handlers: new Map<string, Handler>(),
  terminals: [] as { name: string; exitStatus: undefined; show: ReturnType<typeof vi.fn>; sendText: ReturnType<typeof vi.fn>; cwd?: string }[],
  folders: [] as { uri: { fsPath: string } }[],
  config: {} as Record<string, unknown>,
  shell: "/bin/bash" as string | undefined,
  input: undefined as string | undefined,
  errors: [] as string[],
  infos: [] as string[],
  statusBar: undefined as { text: string; command: string; show: ReturnType<typeof vi.fn> } | undefined,
}));

vi.mock("vscode", () => ({
  commands: {
    registerCommand: (id: string, handler: Handler) => {
      state.handlers.set(id, handler);
      return { dispose() {} };
    },
    executeCommand: (id: string, ...args: unknown[]) => state.handlers.get(id)?.(...args),
  },
  window: {
    get terminals() {
      return state.terminals;
    },
    createTerminal: (options: { name: string; cwd?: string }) => {
      const terminal = { name: options.name, cwd: options.cwd, exitStatus: undefined, show: vi.fn(), sendText: vi.fn() };
      state.terminals.push(terminal);
      return terminal;
    },
    showInputBox: async () => state.input,
    showInformationMessage: (message: string) => state.infos.push(message),
    showErrorMessage: (message: string) => state.errors.push(message),
    showWorkspaceFolderPick: async () => state.folders[1],
    createStatusBarItem: () => {
      state.statusBar = { text: "", command: "", show: vi.fn() };
      return state.statusBar;
    },
  },
  workspace: {
    get workspaceFolders() {
      return state.folders.length ? state.folders : undefined;
    },
    getConfiguration: () => ({ get: (key: string, fallback: unknown) => (key in state.config ? state.config[key] : fallback) }),
  },
  env: {
    get shell() {
      return state.shell;
    },
  },
  StatusBarAlignment: { Left: 1 },
}));

import { activate } from "./extension";

const folder = (fsPath: string) => ({ uri: { fsPath } });

beforeEach(() => {
  state.handlers.clear();
  state.terminals.length = 0;
  state.folders = [folder("/work/app")];
  state.config = {};
  state.shell = "/bin/bash";
  state.input = undefined;
  state.errors.length = 0;
  state.infos.length = 0;
  activate({ subscriptions: [] } as never);
});

const sent = () => state.terminals.flatMap((t) => t.sendText.mock.calls.map((call) => call[0]));

describe("activation", () => {
  it("registers every command in the manifest and a status bar item", async () => {
    const manifest = (await import("../package.json")).default;
    const declared = manifest.contributes.commands.map((c: { command: string }) => c.command).sort();
    expect([...state.handlers.keys()].sort()).toEqual(declared);
    expect(state.statusBar).toMatchObject({ text: "$(search) Lopper", command: "lopper.scanWorkspace" });
    expect(state.statusBar?.show).toHaveBeenCalled();
  });
});

describe("commands", () => {
  it("scans the workspace in the Lopper terminal", async () => {
    await state.handlers.get("lopper.scanWorkspace")!();
    expect(state.terminals).toHaveLength(1);
    expect(state.terminals[0].name).toBe("Lopper");
    expect(state.terminals[0].cwd).toBe("/work/app");
    expect(state.terminals[0].show).toHaveBeenCalledWith(true);
    expect(sent()).toEqual(["lopper scan '/work/app'"]);
  });

  it("reuses the same terminal for a second scan", async () => {
    await state.handlers.get("lopper.scanWorkspace")!();
    await state.handlers.get("lopper.scanWorkspace")!();
    expect(state.terminals).toHaveLength(1);
    expect(sent()).toHaveLength(2);
  });

  it("asks which folder to scan in a multi-root workspace", async () => {
    state.folders = [folder("/work/one"), folder("/work/two")];
    await state.handlers.get("lopper.scanWorkspace")!();
    expect(sent()).toEqual(["lopper scan '/work/two'"]);
  });

  it("tells you to open a folder when there is none, and runs nothing", async () => {
    state.folders = [];
    await state.handlers.get("lopper.scanWorkspace")!();
    expect(sent()).toEqual([]);
    expect(state.infos[0]).toContain("Open a folder first");
  });

  it("scans a folder picked in the explorer", async () => {
    await state.handlers.get("lopper.scanFolder")!({ fsPath: "/work/app/packages/billing" });
    expect(sent()).toEqual(["lopper scan '/work/app/packages/billing'"]);
  });

  it("scans a pasted repo URL", async () => {
    state.input = "github.com/pallets/flask";
    await state.handlers.get("lopper.scanRepoUrl")!();
    expect(sent()).toEqual(["lopper scan --url 'https://github.com/pallets/flask'"]);
  });

  it("sends nothing when the URL box is cancelled or the URL is wrong", async () => {
    state.input = undefined;
    await state.handlers.get("lopper.scanRepoUrl")!();
    state.input = "https://evil.example/x/y; calc";
    await state.handlers.get("lopper.scanRepoUrl")!();
    expect(sent()).toEqual([]);
    expect(state.errors[0]).toContain("GitHub repo URL");
  });

  it("saves a JSON report", async () => {
    await state.handlers.get("lopper.saveReport")!();
    expect(sent()).toEqual(["lopper scan '/work/app' --format json --output '/work/app/lopper-report.json'"]);
  });

  it("checks the install", async () => {
    await state.handlers.get("lopper.checkInstall")!();
    expect(sent()).toEqual(["lopper --version"]);
  });

  it("follows the settings and the user's shell", async () => {
    state.config = { command: "python -m lopper.cli", includeLint: false };
    state.shell = "C:\\Windows\\System32\\cmd.exe";
    state.folders = [folder("C:\\My Projects\\app")];
    await state.handlers.get("lopper.scanWorkspace")!();
    expect(sent()).toEqual(['python -m lopper.cli scan "C:\\My Projects\\app" --no-lint']);
  });

  it("explains a path it can't pass safely instead of running it", async () => {
    state.shell = "C:\\Windows\\System32\\cmd.exe";
    state.folders = [folder("C:\\a&b")];
    await state.handlers.get("lopper.scanWorkspace")!();
    expect(sent()).toEqual([]);
    expect(state.errors[0]).toContain("cmd.exe can't take safely");
  });
});
