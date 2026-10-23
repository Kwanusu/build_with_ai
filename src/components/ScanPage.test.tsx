import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthContext } from "../auth";
import { OCTO, authValue, finding, mockApi, scan } from "../testing";
import { ScanPage } from "./ScanPage";

afterEach(() => {
  vi.unstubAllGlobals();
  window.location.hash = "";
});

const REPO = { owner: "acme", repo: "web-platform" };
const LATEST = "GET /api/repos/acme/web-platform/scan";

function renderResults(findings = [finding()], overrides = {}, extra: Parameters<typeof mockApi>[0] = {}) {
  const result = scan(overrides, findings);
  const api = mockApi({ [LATEST]: () => ({ body: { scan: result } }), ...extra });
  render(<ScanPage {...REPO} pollMs={0} />);
  return { api, result };
}

describe("the scan form", () => {
  it("asks for a public repo URL and keeps the button off until there is one", async () => {
    mockApi({});
    render(<ScanPage />);
    expect(screen.getByRole("heading", { level: 1, name: "Scan a public GitHub repo" })).toBeInTheDocument();
    expect(screen.getByLabelText("GitHub repo URL")).toBeInTheDocument();
    expect(screen.getByText(/Public repos only for now/)).toBeInTheDocument();
    const button = screen.getByRole("button", { name: "Scan repo" });
    expect(button).toBeDisabled();
    await userEvent.type(screen.getByLabelText("GitHub repo URL"), "https://github.com/acme/web-platform");
    expect(button).toBeEnabled();
    expect(button).toHaveClass("btn-primary");
  });

  it("shows the server's reason under the field when the URL is wrong", async () => {
    const { fetchMock } = mockApi({
      "POST /api/scans": () => ({
        status: 400,
        body: { error: "That doesn't look like a GitHub repo URL. Paste one like https://github.com/owner/repo.", code: "invalid_repo_url" },
      }),
    });
    render(<ScanPage />);
    await userEvent.type(screen.getByLabelText("GitHub repo URL"), "https://gitlab.com/a/b");
    await userEvent.click(screen.getByRole("button", { name: "Scan repo" }));
    const input = screen.getByLabelText("GitHub repo URL");
    expect(await screen.findByRole("alert")).toHaveTextContent("doesn't look like a GitHub repo URL");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Scan repo" })).toBeEnabled();
  });

  it("explains a rate limit or a down server above the form, and keeps what was typed", async () => {
    mockApi({
      "POST /api/scans": () => ({
        status: 429,
        body: { error: "That's a lot of scans in a minute. Wait a moment and try again. Nothing has been changed.", code: "rate_limited" },
      }),
    });
    render(<ScanPage />);
    await userEvent.type(screen.getByLabelText("GitHub repo URL"), "https://github.com/acme/web-platform");
    await userEvent.click(screen.getByRole("button", { name: "Scan repo" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Wait a moment and try again");
    expect(screen.getByLabelText("GitHub repo URL")).toHaveValue("https://github.com/acme/web-platform");
  });

  it("starts the scan and moves to the repo's own address", async () => {
    const { calls } = mockApi({
      "POST /api/scans": () => ({ status: 202, body: { scan: scan({ status: "running" }) } }),
    });
    render(<ScanPage />);
    await userEvent.type(screen.getByLabelText("GitHub repo URL"), "  https://github.com/acme/web-platform ");
    await userEvent.click(screen.getByRole("button", { name: "Scan repo" }));
    await waitFor(() => expect(window.location.hash).toBe("#/scan/acme/web-platform"));
    expect(calls[0]).toEqual({ key: "POST /api/scans", body: { repo_url: "https://github.com/acme/web-platform" } });
  });

  it("offers the form with the URL filled in when that repo hasn't been scanned yet", async () => {
    mockApi({ [LATEST]: () => ({ status: 404, body: { error: "We haven't scanned that repo yet.", code: "not_found" } }) });
    render(<ScanPage {...REPO} pollMs={0} />);
    expect(await screen.findByLabelText("GitHub repo URL")).toHaveValue("https://github.com/acme/web-platform");
    expect(screen.getByRole("status")).toHaveTextContent("We haven't scanned that repo yet");
  });
});

describe("a running scan", () => {
  it("says it is working and that the code isn't changed, then shows the results", async () => {
    let polls = 0;
    mockApi({
      [LATEST]: () => ({ body: { scan: scan({ status: "running", repo: scan().repo }) } }),
      "GET /api/scans/1": () => {
        polls++;
        return { body: { scan: polls < 2 ? scan({ status: "running" }) : scan({}, [finding()]) } };
      },
    });
    render(<ScanPage {...REPO} pollMs={0} />);
    expect(await screen.findByRole("heading", { level: 1, name: "Scanning acme/web-platform" })).toBeInTheDocument();
    expect(screen.getByText("We're reading the repo. Your code isn't being changed.")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { level: 1, name: /Found 1 unused item/ })).toBeInTheDocument();
    expect(polls).toBe(2);
  });
});

describe("results", () => {
  const set = () => [
    finding({ id: 101, type: "unused-package", item: "left-pad", file_path: "package.json", line: 6, package: ".", language: "javascript",
      evidence: "No file under the repo root imports 'left-pad', and no script or config file mentions it." }),
    finding({ id: 102, type: "unused-dev-dependency", item: "prettier", file_path: "package.json", line: 9, confidence: "uncertain", ticked: false,
      evidence: "It looks like tooling that a config file can load by name, so check before removing it." }),
    finding({ id: 103, item: "formatInvoice" }),
    finding({ id: 104, item: "parseLegacyToken", file_path: "packages/auth/src/token.ts", line: 18, confidence: "uncertain", ticked: false,
      evidence: "parseLegacyToken is exported and only test files mention it." }),
    finding({ id: 105, type: "lint-issue", item: "Unused import 'useEffect'", file_path: "src/App.tsx", line: 2, report_only: true, ticked: false,
      evidence: "'useEffect' is imported on line 2 of src/App.tsx and is not used anywhere else in the file." }),
  ];

  it("leads with a specific count and what was searched", async () => {
    renderResults(set());
    expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent("Found 4 unused items across 12 packages");
    expect(screen.getByText(/Searched 1,208 files across 12 packages \(javascript\)\./)).toBeInTheDocument();
    expect(screen.getByText(/We also found 1 lint issue\. Lint issues are report only\./)).toBeInTheDocument();
    expect(screen.getByText("Results · acme/web-platform")).toBeInTheDocument();
  });

  it("groups findings and shows the evidence and location for each", async () => {
    renderResults(set());
    await screen.findByRole("heading", { level: 1 });
    const headings = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(headings).toEqual(["Unused packages", "Unused dev dependencies", "Unused exports", "Lint issues"]);
    const row = screen.getByText("left-pad").closest("li")!;
    expect(within(row).getByText("package.json:6")).toBeInTheDocument();
    expect(within(row).getByRole("link", { name: "package.json:6" })).toHaveAttribute(
      "href",
      "https://github.com/acme/web-platform/blob/HEAD/package.json#L6",
    );
    const lint = screen.getByText("Unused import 'useEffect'").closest("li")!;
    expect(within(lint).getByRole("link", { name: "src/App.tsx:2" })).toHaveAttribute("target", "_blank");
    expect(within(row).getByText(/No file under the repo root imports 'left-pad'/)).toBeInTheDocument();
    expect(within(row).getByText("No use found")).toBeInTheDocument();
    const uncertain = screen.getByText("parseLegacyToken").closest("li")!;
    expect(within(uncertain).getByText("Needs a closer look")).toBeInTheDocument();
  });

  it("starts safe items ticked and uncertain ones unticked", async () => {
    renderResults(set());
    await screen.findByRole("heading", { level: 1 });
    expect(screen.getByRole("checkbox", { name: "Tick left-pad to remove it" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Tick prettier to remove it" })).not.toBeChecked();
    expect(screen.getByText(/2 items ticked\./)).toBeInTheDocument();
  });

  it("gives lint issues no checkbox, because they are report only", async () => {
    renderResults(set());
    await screen.findByRole("heading", { level: 1 });
    const row = screen.getByText("Unused import 'useEffect'").closest("li")!;
    expect(within(row).queryByRole("checkbox")).toBeNull();
    expect(within(row).queryByText("No use found")).toBeNull();
    expect(screen.getAllByRole("checkbox")).toHaveLength(4);
    expect(screen.getByText("Report only")).toBeInTheDocument();
  });

  it("says plainly that pull requests aren't available yet and offers no pull request button", async () => {
    renderResults(set());
    await screen.findByRole("heading", { level: 1 });
    expect(screen.getByText(/Pull requests aren't available yet/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /pull request/i })).toBeNull();
    expect(document.querySelectorAll(".btn-primary")).toHaveLength(0);
  });

  it("saves a tick and updates the count straight away", async () => {
    const { api } = renderResults(set(), {}, {
      "PATCH /api/findings/104": (body) => ({ body: { finding: { ...set()[3], ticked: (body as { ticked: boolean }).ticked } } }),
    });
    await screen.findByRole("heading", { level: 1 });
    await userEvent.click(screen.getByRole("checkbox", { name: "Tick parseLegacyToken to remove it" }));
    expect(screen.getByRole("checkbox", { name: "Tick parseLegacyToken to remove it" })).toBeChecked();
    expect(screen.getByText(/3 items ticked\./)).toBeInTheDocument();
    expect(api.calls.find((c) => c.key === "PATCH /api/findings/104")?.body).toEqual({ ticked: true });
  });

  it("puts a tick back and says so when saving fails", async () => {
    renderResults(set(), {}, {
      "PATCH /api/findings/103": () => ({ status: 500, body: { error: "Something went wrong.", code: "http_error" } }),
    });
    await screen.findByRole("heading", { level: 1 });
    await userEvent.click(screen.getByRole("checkbox", { name: "Tick formatInvoice to remove it" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("We couldn't save that change. Nothing has been changed in your code.");
    expect(screen.getByRole("checkbox", { name: "Tick formatInvoice to remove it" })).toBeChecked();
  });

  it("rescans the repo and shows the new result", async () => {
    let started = false;
    const { api } = renderResults(set(), {}, {
      "POST /api/scans": () => {
        started = true;
        return { status: 202, body: { scan: scan({ id: 2, status: "running" }) } };
      },
    });
    await screen.findByRole("heading", { level: 1 });
    window.location.hash = "#/scan/acme/web-platform";
    await userEvent.click(screen.getByRole("button", { name: "Rescan repo" }));
    await waitFor(() => expect(started).toBe(true));
    expect(api.calls.some((c) => c.key === "POST /api/scans" && (c.body as { repo_url: string }).repo_url === "https://github.com/acme/web-platform")).toBe(true);
    await waitFor(() => expect(api.calls.filter((c) => c.key === LATEST).length).toBeGreaterThanOrEqual(2));
  });

  it("celebrates nothing and just says there's nothing to prune", async () => {
    renderResults([]);
    expect(await screen.findByRole("heading", { level: 1, name: "Nothing to prune" })).toBeInTheDocument();
    expect(screen.getByText(/Searched 1,208 files across 12 packages \(javascript\)\. We found no unused packages or exports\./)).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("!");
    expect(screen.queryByText(/Pull requests aren't available yet/)).toBeNull();
  });
});

describe("errors", () => {
  it("shows a failed scan's reason, with a way to try again and a way to pick another repo", async () => {
    const message = "We couldn't clone https://github.com/acme/web-platform. Lopper can only read public repos right now. Your code hasn't been changed.";
    const { api } = (() => {
      const api = mockApi({
        [LATEST]: () => ({ body: { scan: scan({ status: "failed", error: message }) } }),
        "POST /api/scans": () => ({ status: 202, body: { scan: scan({ id: 2, status: "running" }) } }),
      });
      return { api };
    })();
    render(<ScanPage {...REPO} pollMs={0} />);
    expect(await screen.findByRole("heading", { level: 1, name: "We couldn't finish that scan" })).toBeInTheDocument();
    expect(screen.getByText(message)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Use a different repo" })).toHaveAttribute("href", "#/scan");
    window.location.hash = "#/scan/acme/web-platform";
    await userEvent.click(screen.getByRole("button", { name: "Scan again" }));
    await waitFor(() => expect(api.calls.some((c) => c.key === "POST /api/scans")).toBe(true));
  });

  it("explains when the server can't be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    render(<ScanPage {...REPO} pollMs={0} />);
    expect(await screen.findByText(/We couldn't reach the Lopper server/)).toBeInTheDocument();
    expect(screen.getByText(/Nothing has been changed/)).toBeInTheDocument();
  });
});

describe("scans you can't tick", () => {
  const items = () => [finding({ id: 201, item: "formatInvoice" }), finding({ id: 202, type: "lint-issue", item: "Unused import 'x'", report_only: true, ticked: false })];

  function renderUntickable(auth = authValue()) {
    mockApi({ [LATEST]: () => ({ body: { scan: scan({ can_tick: false }, items()) } }) });
    render(
      <AuthContext.Provider value={auth}>
        <ScanPage {...REPO} pollMs={0} />
      </AuthContext.Provider>,
    );
  }

  it("shows the findings and evidence but no checkboxes or tick count", async () => {
    renderUntickable();
    expect(await screen.findByText("formatInvoice")).toBeInTheDocument();
    expect(screen.getAllByText(/no other file mentions it/).length).toBeGreaterThan(0);
    expect(screen.queryByRole("checkbox")).toBeNull();
    expect(screen.queryByText(/items? ticked/)).toBeNull();
  });

  it("tells a signed-out visitor to sign in, with a link when sign-in is available", async () => {
    renderUntickable(authValue({ signInAvailable: true }));
    expect(await screen.findByText(/Sign in with GitHub to tick items and keep your choices\./)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign in with GitHub" })).toHaveAttribute("href", "/api/auth/github/login");
  });

  it("offers no sign-in link when sign-in isn't set up", async () => {
    renderUntickable(authValue({ signInAvailable: false }));
    expect(await screen.findByText(/Sign in with GitHub to tick items/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Sign in with GitHub" })).toBeNull();
  });

  it("tells a signed-in person it is a public scan and to rescan for their own copy", async () => {
    renderUntickable(authValue({ user: OCTO, signInAvailable: true }));
    expect(await screen.findByText(/This is a public scan, so items can't be ticked on it\. Rescan to get your own copy/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Sign in with GitHub" })).toBeNull();
    expect(screen.getByRole("button", { name: "Rescan repo" })).toBeInTheDocument();
  });

  it("a scan you own still shows checkboxes and no sign-in message", async () => {
    mockApi({ [LATEST]: () => ({ body: { scan: scan({ can_tick: true }, items()) } }) });
    render(
      <AuthContext.Provider value={authValue({ user: OCTO, signInAvailable: true })}>
        <ScanPage {...REPO} pollMs={0} />
      </AuthContext.Provider>,
    );
    expect(await screen.findByRole("checkbox", { name: "Tick formatInvoice to remove it" })).toBeChecked();
    expect(screen.queryByText(/Sign in with GitHub to tick/)).toBeNull();
    expect(screen.queryByText(/public scan/)).toBeNull();
  });
});

