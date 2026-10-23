import { parseHash, scanHash } from "./route";

describe("parseHash", () => {
  it("treats everything but #/scan as the landing page", () => {
    for (const hash of ["", "#", "#top", "#how", "#/", "#/scanner", "#/scan/only-owner/x/y"]) {
      expect(parseHash(hash)).toEqual({ name: "landing" });
    }
  });

  it("reads the scan page and the repo in its address", () => {
    expect(parseHash("#/scan")).toEqual({ name: "scan" });
    expect(parseHash("#/scan/")).toEqual({ name: "scan" });
    expect(parseHash("#/scan/acme/web-platform")).toEqual({ name: "scan", owner: "acme", repo: "web-platform" });
    expect(parseHash("#/scan/acme/my.repo/")).toEqual({ name: "scan", owner: "acme", repo: "my.repo" });
  });

  it("round-trips through scanHash", () => {
    expect(scanHash()).toBe("#/scan");
    expect(parseHash(scanHash("acme", "web-platform"))).toEqual({ name: "scan", owner: "acme", repo: "web-platform" });
  });
});
