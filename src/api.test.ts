import { ApiError, getLatestScan, getScan, setTicked, startScan } from "./api";
import { finding, mockApi, scan } from "./testing";

afterEach(() => vi.unstubAllGlobals());

describe("api client", () => {
  it("starts a scan with the repo URL", async () => {
    const { calls } = mockApi({ "POST /api/scans": () => ({ status: 202, body: { scan: scan({ status: "running" }) } }) });
    const started = await startScan("https://github.com/acme/web-platform");
    expect(started.status).toBe("running");
    expect(calls[0].body).toEqual({ repo_url: "https://github.com/acme/web-platform" });
  });

  it("reads a scan and a repo's latest scan", async () => {
    mockApi({
      "GET /api/scans/7": () => ({ body: { scan: scan({ id: 7 }) } }),
      "GET /api/repos/acme/web-platform/scan": () => ({ body: { scan: scan({ id: 9 }) } }),
    });
    expect((await getScan(7)).id).toBe(7);
    expect((await getLatestScan("acme", "web-platform")).id).toBe(9);
  });

  it("ticks a finding", async () => {
    const f = finding({ id: 5 });
    const { calls } = mockApi({ "PATCH /api/findings/5": () => ({ body: { finding: { ...f, ticked: false } } }) });
    expect((await setTicked(5, false)).ticked).toBe(false);
    expect(calls[0].body).toEqual({ ticked: false });
  });

  it("turns an API error into an ApiError with the server's message and code", async () => {
    mockApi({ "POST /api/scans": () => ({ status: 400, body: { error: "That doesn't look like a GitHub repo URL.", code: "invalid_repo_url" } }) });
    await expect(startScan("nope")).rejects.toMatchObject({
      name: "ApiError",
      message: "That doesn't look like a GitHub repo URL.",
      code: "invalid_repo_url",
      status: 400,
    });
  });

  it("explains when the server can't be reached, and says nothing was changed", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const error = await getScan(1).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("network");
    expect((error as ApiError).message).toContain("Nothing has been changed");
  });

  it("copes with a reply that isn't JSON", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>Bad gateway</html>", { status: 502 })));
    await expect(getScan(1)).rejects.toMatchObject({ status: 502, message: expect.stringContaining("Nothing has been changed") });
  });
});
