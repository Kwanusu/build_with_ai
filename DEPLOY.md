# Deploying Lopper

Three pieces, each on its own service:

| Piece | Where | What it does |
|---|---|---|
| Database | Supabase (Postgres) | Keeps scans, findings, users and sessions |
| API | Render (Docker, `backend/Dockerfile`) | The Flask app and the scanner |
| Site | Cloudflare Pages | The React site, plus a small function that forwards `/api` to the API |

The site calls `/api` on its own address and the function in `functions/api/[[path]].ts` forwards it to Render. To the browser the API is the same site, so the sign-in cookie works and there is no CORS to set up.

Do the steps in this order, because each one needs an address from the one before.

## 1. Supabase

1. Create a project. Pick a strong database password and keep it.
2. Open **Connect** and copy the **Transaction pooler** connection string (port 6543). Add `?sslmode=require` at the end. That is your `DATABASE_URL`.
3. Nothing else to do: the API creates its own tables the first time it starts (`lopper db-init`). The tables have row level security on and no policies, so Supabase's public REST API can't read them. Only the API can, through this connection string.

## 2. Render (the API)

1. **New > Blueprint**, choose this repo. Render reads `render.yaml`.
2. Fill in the values it asks for:
   - `DATABASE_URL`: from step 1.
   - `FRONTEND_URL`: the address the site will have, for example `https://lopper.pages.dev`. If you don't know it yet, put your guess and fix it after step 3.
   - `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`: leave empty to run without sign-in for now.
3. After the first deploy, open `https://<your-service>.onrender.com/api/health`. It should say `{"database":true,"status":"ok"}`.
4. In the service's **Environment** tab, copy the generated `PROXY_SECRET`. You need it in step 3.

## 3. Cloudflare (the site)

Cloudflare has two kinds of project that can serve the site. Both work, and both read the same two variables. If your site address ends in `.workers.dev` it is a Worker. If it ends in `.pages.dev` it is a Pages project.

**Worker** (`wrangler.jsonc` and `worker/index.ts`): **Workers & Pages > Create > Import a repository**, choose this repo, and name the Worker `lopper` (it must match `name` in `wrangler.jsonc`). Build command `npm run build`, deploy command `npx wrangler deploy`. Add the variable `NODE_VERSION` = `22` under build variables. Only `/api/*` runs the Worker. Everything else is served straight from `dist/`.

**Pages** (`functions/api/[[path]].ts`): **Workers & Pages > Create > Pages > Connect to Git**, choose this repo. Build command `npm run build`, output folder `dist`, and the variable `NODE_VERSION` = `22`.

Either way, under **Settings > Variables and Secrets** (runtime variables, not build variables), add:

- `API_ORIGIN`: your Render address, for example `https://lopper-api.onrender.com` (no trailing slash, no `/api`).
- `PROXY_SECRET`: the value from Render. Make it a secret.

Then redeploy, because variables are read at deploy time. Leave `VITE_API_URL` unset: the site and `/api` share one address. If the site's address differs from the `FRONTEND_URL` you gave Render, update it there.

To test, open `<your site>/api/health`. It should show `{"database":true,"status":"ok"}`. A `405 Method Not Allowed` on `/api/scans` means the forwarder isn't running: the site is being served as plain files.

## 4. GitHub sign-in (optional)

Create a GitHub OAuth app (see [Sign in with GitHub](backend/README.md#sign-in-with-github)) with:

- Homepage URL: your Pages address.
- Authorization callback URL: `<your Pages address>/api/auth/github/callback`.

Then put its client ID and secret into the Render service's environment and redeploy.

## Things to know

- **Free Render services sleep** after about 15 minutes idle. The next visit waits roughly a minute while it wakes. A scan that is running when the service sleeps is lost, and the site offers to scan again.
- **One worker.** Scans run in threads inside the API process and the rate limit is kept in memory, so the Dockerfile runs one gunicorn worker with threads. Don't raise `--workers` without moving both elsewhere.
- **Secrets** live only in Render's and Cloudflare's settings. Never put them in the repo.
- **Local development doesn't change.** With no `DATABASE_URL` the API uses the SQLite file `backend/lopper.db`.
