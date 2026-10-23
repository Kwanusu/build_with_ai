# Lopper for VS Code

Finds unused packages, exports and dev dependencies, and shows the evidence. The commands run the `lopper` command in VS Code's terminal, so you read the report where you work. Lopper reads your code and never changes it.

## Before you start

Install the `lopper` command from `../backend` (Python 3.11 or newer):

```bash
cd backend
pip install -e .
lopper --version
```

If `lopper` isn't on your PATH, set `lopper.command` in VS Code settings, for example `python -m lopper.cli` or the full path to the executable. **Lopper: Check that the lopper command works** runs `lopper --version` in the terminal so you can see.

## Commands

Open the Command Palette and type "Lopper", or click **Lopper** in the status bar.

| Command | Runs in the terminal |
|---|---|
| Lopper: Scan this workspace | `lopper scan <workspace folder>` |
| Lopper: Scan this folder with Lopper (right-click a folder in the Explorer) | `lopper scan <that folder>` |
| Lopper: Scan a GitHub repo URL | `lopper scan --url <url>` |
| Lopper: Scan this workspace and save a JSON report | `lopper scan <folder> --format json --output <folder>/lopper-report.json` |
| Lopper: Check that the lopper command works | `lopper --version` |

In a workspace with more than one folder, you pick which one to scan.

## Settings

| Setting | Default | What it does |
|---|---|---|
| `lopper.command` | `lopper` | The command that runs Lopper |
| `lopper.includeLint` | `true` | Include lint issues (report only). Off adds `--no-lint` |
| `lopper.reportFile` | `lopper-report.json` | File name for the JSON report |

## Safety

Paths and URLs are checked and quoted for your shell (PowerShell, cmd or a POSIX shell) before they reach the terminal. A pasted URL must be a public `github.com` repo. A path the shell can't take safely is refused with a message instead of being run.

## Develop

```bash
npm install
npm test            # command building and the extension's registration
npm run compile     # builds to out/
npm run package     # builds lopper-vscode-0.1.0.vsix
```

To try it, open this folder in VS Code and press F5. To install the package, run `code --install-extension lopper-vscode-0.1.0.vsix`.
