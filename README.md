# Lopper

Lopper finds unused packages, exports and dev dependencies in frontend and backend repos, shows the evidence, and removes what you tick through a pull request you review. Lint issues are report only. Nothing is removed until a person merges the pull request.

This repository holds the design system, the landing page, the Python back end and the VS Code extension.

| Part | Folder | Docs |
|---|---|---|
| Landing page (React) | `src/` | this file |
| Scanner, `lopper` command and web API (Flask and Postgres) | `backend/` | [backend/README.md](backend/README.md) |
| VS Code extension | `extension/` | [extension/README.md](extension/README.md) |

You can use Lopper three ways: paste a public GitHub repo URL into the web API, run `lopper scan` in a terminal, or use the VS Code commands, which run the same `lopper scan` in VS Code's terminal. The landing page does not call the API yet.

## Stack

- **Front end:** TypeScript, React 19, Vite, Tailwind CSS 4, Vitest and Testing Library.
- **Back end:** Python, Flask and PostgreSQL.
- **VS Code extension:** TypeScript, with Vitest for tests.

## Getting started

```bash
npm install
npm run dev
```

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Starts the dev server |
| `npm run build` | Type-checks, then builds to `dist/` |
| `npm run preview` | Serves the built site |
| `npm run typecheck` | Type-checks only |
| `npm test` | Runs the tests |
| `npm run design:lint` | Lints `DESIGN.md` and fails on errors or contrast warnings |
| `npm run tokens` | Regenerates `styles.css` (the Tailwind theme) from `DESIGN.md` |

## Files

| Path | Purpose |
|---|---|
| `DESIGN.md` | The design system: colors, type, spacing, shapes and components, light and dark |
| `brand-guide.md` | Brand concept, voice and logo rules |
| `spec.md` | Product spec |
| `styles.css` | Tailwind theme generated from `DESIGN.md`. Do not edit by hand |
| `assets/logo/` | The supplied logo SVGs: wordmark and lockup in light and dark, the app icon, and a preview sheet. Use them as they are |
| `src/index.css` | Semantic colour roles and component styles, built only from the tokens |
| `src/content.ts` | Page copy |
| `src/components/` | React components |
| `backend/` | The scanner, the `lopper` command and the Flask API |
| `extension/` | The VS Code extension |
| `CLAUDE.md` | Rules for Claude Code in this project |

## Changing the design

1. Edit `DESIGN.md`.
2. Run `npm run design:lint` and fix every error and contrast warning.
3. Run `npm run tokens`, then `npm test`.

The tests fail if `styles.css` is out of sync with `DESIGN.md` or if a source file hard-codes a colour.

## Checkpoints

Working states are tagged `checkpoint-N-name`. To look at one, run `git checkout checkpoint-1-design-files`, then `git switch main` to return.
