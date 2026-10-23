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

describe("sign-in error pages", () => {
  it("reads the reason from the address", () => {
    expect(parseHash("#/auth/error/access_denied")).toEqual({ name: "auth-error", code: "access_denied" });
    expect(parseHash("#/auth/error/github_unavailable/")).toEqual({ name: "auth-error", code: "github_unavailable" });
  });

  it("ignores anything that isn't a plain reason code", () => {
    for (const hash of ["#/auth/error", "#/auth/error/", "#/auth/error/Bad-Code", "#/auth/error/a/b", "#/auth/error/<script>"]) {
      expect(parseHash(hash)).toEqual({ name: "landing" });
    }
  });
});

