/**
 * The Cloudflare Worker for the site. /api/* goes to the Flask API; everything else is the built site.
 * (wrangler.jsonc sends only /api/* here and lets Cloudflare serve the files itself.)
 */
import { forward, type Env } from "./forward";

interface WorkerEnv extends Env {
  ASSETS: { fetch(request: Request): Promise<Response> };
}

export async function handle(request: Request, env: WorkerEnv, send?: typeof fetch): Promise<Response> {
  if (new URL(request.url).pathname.startsWith("/api/")) {
    return forward(request, env, send);
  }
  return env.ASSETS.fetch(request);
}

// Cloudflare calls fetch(request, env, ctx). Pass on only what handle needs: its third parameter is a stand-in for fetch
// that tests use, so handing it Cloudflare's context would make every /api request fail with a 502.
export default { fetch: (request: Request, env: WorkerEnv, _ctx?: unknown) => handle(request, env) };
