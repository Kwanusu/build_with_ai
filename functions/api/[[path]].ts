// Cloudflare Pages runs this for every /api/* request. (A Workers project uses worker/index.ts instead.)
import { forward, type Env } from "../../worker/forward";

export function onRequest(context: { request: Request; env: Env }): Promise<Response> {
  return forward(context.request, context.env);
}
