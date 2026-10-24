// @vitest-environment node
import { forward } from "../worker/forward";
import worker, { handle } from "../worker/index";

const ENV = { API_ORIGIN: "https://api.example.com", PROXY_SECRET: "shh" };

function fakeApi(reply: Response = new Response("{}", { status: 200 })) {
  const calls: { url: string; init: RequestInit }[] = [];
  const send = (async (url: URL, init: RequestInit) => {
    calls.push({ url: String(url), init });
    return reply;
  }) as unknown as typeof fetch;
  return { calls, send };
}

describe("the /api forwarder", () => {
  it("sends the request on to the API with its path and query", async () => {
    const { calls, send } = fakeApi();
    await forward(new Request("https://lopper.pages.dev/api/scans/3?finding_type=lint-issue"), ENV, send);
    expect(calls[0].url).toBe("https://api.example.com/api/scans/3?finding_type=lint-issue");
  });

  it("tells the API who the visitor is, and replaces anything the visitor claimed", async () => {
    const { calls, send } = fakeApi();
    const request = new Request("https://lopper.pages.dev/api/scans", {
      method: "POST",
      body: '{"repo_url":"https://github.com/a/b"}',
      headers: { "cf-connecting-ip": "203.0.113.9", "x-lopper-client-ip": "10.0.0.1", "x-lopper-proxy-secret": "guess", cookie: "lopper_session=abc" },
    });
    await forward(request, ENV, send);
    const headers = new Headers(calls[0].init.headers);
    expect(headers.get("x-lopper-client-ip")).toBe("203.0.113.9");
    expect(headers.get("x-lopper-proxy-secret")).toBe("shh");
    expect(headers.get("cookie")).toBe("lopper_session=abc");
    expect(calls[0].init.method).toBe("POST");
  });

  it("never passes on a client address a visitor made up when there is no secret", async () => {
    const { calls, send } = fakeApi();
    const request = new Request("https://lopper.pages.dev/api/health", { headers: { "x-lopper-client-ip": "10.0.0.1" } });
    await forward(request, { API_ORIGIN: ENV.API_ORIGIN }, send);
    expect(new Headers(calls[0].init.headers).get("x-lopper-client-ip")).toBeNull();
  });

  it("keeps redirects and cookies from the API as they are", async () => {
    const reply = new Response(null, { status: 302, headers: { location: "https://lopper.pages.dev/#/scan", "set-cookie": "lopper_session=abc; HttpOnly" } });
    const response = await forward(new Request("https://lopper.pages.dev/api/auth/github/callback?code=x"), ENV, fakeApi(reply).send);
    expect(response.status).toBe(302);
    expect(response.headers.get("location")).toBe("https://lopper.pages.dev/#/scan");
    expect(response.headers.get("set-cookie")).toContain("lopper_session=abc");
  });

  it("can't be pointed at another host with a // path", async () => {
    const { calls, send } = fakeApi();
    await forward(new Request("https://lopper.pages.dev//evil.example/api/x"), ENV, send);
    expect(new URL(calls[0].url).host).toBe("api.example.com");
  });

  it("explains itself when there is no API address or the API is down", async () => {
    expect((await forward(new Request("https://lopper.pages.dev/api/health"), {})).status).toBe(503);
    const down = (async () => {
      throw new Error("refused");
    }) as unknown as typeof fetch;
    const response = await forward(new Request("https://lopper.pages.dev/api/health"), ENV, down);
    expect(response.status).toBe(502);
    expect((await response.json()).error).toContain("hasn't been changed");
  });
});

describe("the Worker", () => {
  const assets = { fetch: async () => new Response("<html>site</html>") };

  it("forwards /api to the API and serves everything else from the built site", async () => {
    const { calls, send } = fakeApi();
    const api = await handle(new Request("https://lopper.example.workers.dev/api/scans", { method: "POST", body: "{}" }), { ...ENV, ASSETS: assets }, send);
    expect(api.status).toBe(200);
    expect(calls[0].url).toBe("https://api.example.com/api/scans");
    expect(calls[0].init.method).toBe("POST");

    const page = await handle(new Request("https://lopper.example.workers.dev/"), { ...ENV, ASSETS: assets }, send);
    expect(await page.text()).toBe("<html>site</html>");
    expect(calls).toHaveLength(1);
  });
});

describe("the Worker as Cloudflare runs it", () => {
  const assets = { fetch: async () => new Response("<html>site</html>") };
  // Cloudflare calls fetch(request, env, ctx). The third argument is its execution context, never a function for calling the API.
  const ctx = { waitUntil() {}, passThroughOnException() {}, props: {} };

  afterEach(() => vi.unstubAllGlobals());

  it("forwards /api to the API with the real fetch, however many arguments Cloudflare passes", async () => {
    const calls: string[] = [];
    vi.stubGlobal("fetch", async (url: URL) => {
      calls.push(String(url));
      return new Response('{"status":"ok"}', { status: 200 });
    });
    const response = await worker.fetch(new Request("https://lopper.example.workers.dev/api/health"), { ...ENV, ASSETS: assets }, ctx as never);
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ status: "ok" });
    expect(calls).toEqual(["https://api.example.com/api/health"]);
  });

  it("serves the built site for everything else", async () => {
    const page = await worker.fetch(new Request("https://lopper.example.workers.dev/"), { ...ENV, ASSETS: assets }, ctx as never);
    expect(await page.text()).toBe("<html>site</html>");
  });
});
