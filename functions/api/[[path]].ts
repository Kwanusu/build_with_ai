/**
 * Cloudflare Pages Function: forwards every /api/* request to the Flask API.
 *
 * The site calls /api on its own address, so the browser treats the API as the same site. That keeps the
 * sign-in cookie (SameSite=Lax) working and needs no CORS. Set these in the Pages project's settings:
 *   API_ORIGIN    where the API is, for example https://lopper-api.onrender.com
 *   PROXY_SECRET  the same value as the API's PROXY_SECRET. It lets us tell the API who the real visitor is,
 *                 so the API's rate limit counts visitors and not this forwarder.
 */

interface Env {
  API_ORIGIN?: string;
  PROXY_SECRET?: string;
}

// Headers a visitor could send to pretend to be someone else, or that only make sense for this hop.
const DROPPED = ["host", "x-forwarded-for", "x-forwarded-host", "x-real-ip", "x-lopper-client-ip", "x-lopper-proxy-secret"];

function problem(status: number, error: string, code: string): Response {
  return new Response(JSON.stringify({ error, code }), { status, headers: { "content-type": "application/json" } });
}

export async function forward(request: Request, env: Env, send: typeof fetch = fetch): Promise<Response> {
  if (!env.API_ORIGIN) {
    return problem(503, "This site isn't connected to its server yet. Nothing has been changed.", "api_not_configured");
  }
  const origin = new URL(env.API_ORIGIN);
  const incoming = new URL(request.url);
  // Build the address as text, then check where it points: a path like //example.com must not change the host.
  const target = new URL(origin.origin + incoming.pathname + incoming.search);
  if (target.origin !== origin.origin) {
    return problem(400, "That request can't be forwarded. Nothing has been changed.", "bad_request");
  }

  const headers = new Headers(request.headers);
  DROPPED.forEach((name) => headers.delete(name));
  const visitor = request.headers.get("cf-connecting-ip");
  if (env.PROXY_SECRET && visitor) {
    headers.set("x-lopper-client-ip", visitor);
    headers.set("x-lopper-proxy-secret", env.PROXY_SECRET);
  }

  const init: RequestInit = { method: request.method, headers, redirect: "manual" };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }
  try {
    const upstream = await send(target, init);
    // Passing the response through keeps its status, redirects and Set-Cookie headers as they are.
    return new Response(upstream.body, upstream);
  } catch {
    return problem(502, "We couldn't reach the server. Your code hasn't been changed. Try again in a moment.", "api_unreachable");
  }
}

export function onRequest(context: { request: Request; env: Env }): Promise<Response> {
  return forward(context.request, context.env);
}
