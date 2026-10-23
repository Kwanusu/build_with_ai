## Stack

- TypeScript, React 19 and Vite. Styling is Tailwind CSS 4, with the theme generated from DESIGN.md. Tests use Vitest and Testing Library.
- `npm run dev` starts the dev server. `npm run build` type-checks and builds to `dist/`. `npm run typecheck` only type-checks.
- `npm test` runs the tests. Run it, and `npm run build`, before every commit.
- Layout: `src/content.ts` holds page copy, `src/components/` the React components, `src/index.css` the semantic colour roles and component styles, and `styles.css` the generated Tailwind theme.
- Logos are in `assets/logo/`. Use the files as supplied through `src/components/Logo.tsx`; never retype, recolour or redraw them. The lockup goes in the header, the wordmark in the footer and on small screens, and the app icon is the favicon.
- Write the front end and the VS Code extension in TypeScript. Keep copy in `src/content.ts`, not inline in components.

## Back end and extension

- The back end is Python 3.11+ with Flask and SQLite, in `backend/`. It has its own virtual environment at `backend/.venv`. Run its tests with `backend/.venv/Scripts/python -m pytest` from `backend/` (`.venv/bin/python` on macOS and Linux).
- The database is a SQLite file in development (`backend/lopper.db`, or `DATABASE_PATH`) and Postgres in production (`DATABASE_URL`, Supabase). Write SQL once in the shared dialect (`?` for parameters, `IS ?` for NULL-safe equality; see `lopper/api/db.py`), and keep `schema.sql` and `schema.postgres.sql` in step. Each API test gets its own temporary SQLite file. To check the Postgres path, run the tests with `TEST_DATABASE_URL` set (it empties that database).
- Hosting: the site on Cloudflare Pages (`functions/api/[[path]].ts` forwards `/api`), the API on Render (`render.yaml`, `backend/Dockerfile`), the database on Supabase. Steps are in DEPLOY.md. Keep the API at one gunicorn worker.
- The scanner reads code and never changes or runs it. Keep it conservative: when a finding could be wrong, mark it `uncertain` rather than `safe`. Add a test for every false positive you fix.
- Only `github.com` repo URLs may be cloned (public ones, or private ones through the signed-in person's token). Keep that check in `backend/lopper/repo.py`, and never pass user input to a shell.
- The VS Code extension is in `extension/` and only runs the `lopper` command in the terminal. Build commands in `extension/src/commands.ts` (no VS Code imports) so they can be tested, and quote every argument for the user's shell. Run `npm test` and `npm run compile` there.
- Sign-in with GitHub (`backend/lopper/api/auth*.py`, `github.py`): a scan made while signed in is private to that person and only they can tick it; a scan made without signing in is public and can't be ticked. Keep that rule, and add a test when you touch it. Never log, return or put a GitHub token or the OAuth secret in a command line, a message or a commit. Keep secrets in the git-ignored `backend/.env`.
- The front end reads who is signed in from `src/auth.tsx` and never sees a token. Pages must work signed out, and when sign-in isn't set up on the server.
- Before every commit, run the tests for every part you touched.

## Design

- Read DESIGN.md before any change to the interface.
- Use only the colors, fonts, sizes, spacing and corner radius in DESIGN.md. Never hard-code a value that isn't in it.
- If a screen needs something DESIGN.md doesn't have, ask me first, then add it to DESIGN.md before using it.
- After any edit to DESIGN.md, run `npm run design:lint` and fix every error and contrast warning, then run `npm run tokens` to regenerate `styles.css`. (`npx @google/design.md lint` prints nothing on this machine, so the script calls the CLI with node directly.)
- Use the primary (ochre) button once per view.
