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
    expect(screen.getByRole("status").querySelector(".spinner-lg")).not.toBeNull();
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

  it("reassures before a pull request: nothing is removed until it is merged", async () => {
    renderResults(set());
    await screen.findByRole("heading", { level: 1 });
    expect(screen.getByText(/Nothing will be removed until you merge the pull request/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create pull request" })).toBeEnabled();
    // One primary action in the view.
    expect(document.querySelectorAll(".btn-primary")).toHaveLength(1);
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
    expect(screen.queryByRole("button", { name: "Create pull request" })).toBeNull();
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


describe("creating a pull request", () => {
  const PR_URL = "https://github.com/acme/web-platform/pull/7";
  const created = (over = {}) => ({
    pull_request: { url: PR_URL, number: 7, branch: "lopper/remove-unused-20261024-101500", title: "Remove 2 unused items found by Lopper", base: "main" },
    applied: [
      { id: 101, item: "left-pad", type: "unused-package", file_path: "package.json", summary: "Remove left-pad from dependencies" },
      { id: 103, item: "formatInvoice", type: "unused-export", file_path: "src/invoice.ts", summary: "Stop exporting formatInvoice" },
    ],
    skipped: [{ id: 104, item: "parseLegacyToken", type: "unused-export", reason: "This export is in an export list. Remove it by hand." }],
    ...over,
  });
  const items = () => [
    finding({ id: 101, type: "unused-package", item: "left-pad", file_path: "package.json", line: 6, package: "." }),
    finding({ id: 103, item: "formatInvoice" }),
    finding({ id: 104, item: "parseLegacyToken", confidence: "uncertain", ticked: false }),
  ];

  it("asks the server for a pull request and then shows what was made, with a link to it", async () => {
    const { result } = renderResults(items());
    mockApi({
      [LATEST]: () => ({ body: { scan: result } }),
      [`POST /api/scans/${result.id}/pull-request`]: () => ({ status: 201, body: created() }),
    });
    await screen.findByRole("heading", { level: 1 });
    await userEvent.click(screen.getByRole("button", { name: "Create pull request" }));

    expect(await screen.findByRole("heading", { level: 1, name: "Pull request created" })).toBeInTheDocument();
    expect(screen.getByText(/2 changes on a new branch of acme\/web-platform\. Nothing is removed until you merge it\./)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open pull request on GitHub" })).toHaveAttribute("href", PR_URL);
    expect(screen.getByRole("link", { name: "Open pull request on GitHub" })).toHaveAttribute("target", "_blank");
    expect(screen.getByText("Stop exporting formatInvoice")).toBeInTheDocument();
    expect(screen.getByText(/Lock files aren't updated/)).toBeInTheDocument();
    const left = screen.getByRole("heading", { name: "Left for you" }).closest("section")!;
    expect(within(left).getByText("parseLegacyToken")).toBeInTheDocument();
    expect(within(left).getByText(/export list/)).toBeInTheDocument();
  });

  it("goes back to the results with the ticks as they were", async () => {
    const { result } = renderResults(items());
    mockApi({
      [LATEST]: () => ({ body: { scan: result } }),
      [`POST /api/scans/${result.id}/pull-request`]: () => ({ status: 201, body: created() }),
    });
    await screen.findByRole("heading", { level: 1 });
    await userEvent.click(screen.getByRole("button", { name: "Create pull request" }));
    await userEvent.click(await screen.findByRole("button", { name: "Back to results" }));
    expect(await screen.findByRole("checkbox", { name: "Tick formatInvoice to remove it" })).toBeChecked();
  });

  it("disables itself and says what it is doing while it works", async () => {
    const { result } = renderResults(items());
    let finish: (value: unknown) => void = () => {};
    const gate = new Promise((resolve) => (finish = resolve));
    mockApi({
      [LATEST]: () => ({ body: { scan: result } }),
      [`POST /api/scans/${result.id}/pull-request`]: async () => {
        await gate;
        return { status: 201, body: created() };
      },
    });
    await screen.findByRole("heading", { level: 1 });
    await userEvent.click(screen.getByRole("button", { name: "Create pull request" }));
    const busy = await screen.findByRole("button", { name: "Creating pull request" });
    expect(busy).toBeDisabled();
    expect(busy).toHaveAttribute("aria-busy", "true");
    finish(undefined);
    expect(await screen.findByRole("heading", { level: 1, name: "Pull request created" })).toBeInTheDocument();
  });

  it("needs at least one tick", async () => {
    renderResults(items().map((f) => ({ ...f, ticked: false })));
    await screen.findByRole("heading", { level: 1 });
    expect(screen.getByRole("button", { name: "Create pull request" })).toBeDisabled();
    expect(screen.getByText(/Tick at least one item to create a pull request\./)).toBeInTheDocument();
  });

  it("explains a refusal and lists what Lopper couldn't change, and lets you try again", async () => {
    const { result } = renderResults(items());
    mockApi({
      [LATEST]: () => ({ body: { scan: result } }),
      [`POST /api/scans/${result.id}/pull-request`]: () => ({
        status: 422,
        body: {
          error: "Lopper can't make any of the ticked changes on its own. Nothing has been changed.",
          code: "nothing_to_change",
          skipped: [{ id: 101, item: "left-pad", type: "unused-package", reason: "package.json has changed since the scan, so Lopper left it alone." }],
        },
      }),
    });
    await screen.findByRole("heading", { level: 1 });
    await userEvent.click(screen.getByRole("button", { name: "Create pull request" }));
    const alert = await screen.findByText(/can't make any of the ticked changes on its own/);
    expect(within(alert.closest("[role=alert]") as HTMLElement).getByText(/package\.json has changed since the scan/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create pull request" })).toBeEnabled();
  });

  it("offers no pull request button on a scan you can't tick", async () => {
    mockApi({ [LATEST]: () => ({ body: { scan: scan({ can_tick: false }, items()) } }) });
    render(<ScanPage {...REPO} pollMs={0} />);
    await screen.findByRole("heading", { level: 1 });
    expect(screen.queryByRole("button", { name: /pull request/i })).toBeNull();
  });
});

describe("asking about the results", () => {
  const items = () => [finding({ id: 301, item: "formatInvoice" })];

  function renderWith(auth: ReturnType<typeof authValue>, result = scan({}, items()), extra: Parameters<typeof mockApi>[0] = {}) {
    const api = mockApi({ [LATEST]: () => ({ body: { scan: result } }), ...extra });
    render(
      <AuthContext.Provider value={auth}>
        <ScanPage {...REPO} pollMs={0} />
      </AuthContext.Provider>,
    );
    return api;
  }

  it("offers questions about a finished scan when the server has chat set up", async () => {
    renderWith(authValue({ chatAvailable: true }));
    await screen.findByRole("heading", { level: 1 });
    expect(screen.getByRole("heading", { level: 2, name: "Questions about this scan" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ask about these results" })).toBeInTheDocument();
  });

  it("offers nothing when the server has no chat, and the page works as before", async () => {
    renderWith(authValue({ chatAvailable: false }));
    await screen.findByRole("heading", { level: 1 });
    expect(screen.queryByRole("heading", { name: "Questions about this scan" })).toBeNull();
    expect(screen.getByRole("button", { name: "Create pull request" })).toBeEnabled();
  });

  it("offers nothing when there is nothing to ask about", async () => {
    renderWith(authValue({ chatAvailable: true }), scan({}, []));
    await screen.findByRole("heading", { name: "Nothing to prune" });
    expect(screen.queryByRole("heading", { name: "Questions about this scan" })).toBeNull();
  });

  it("is there on a public scan too, since anyone can read it", async () => {
    renderWith(authValue({ chatAvailable: true }), scan({ can_tick: false }, items()));
    await screen.findByRole("heading", { level: 1 });
    expect(screen.getByRole("button", { name: "Ask about these results" })).toBeInTheDocument();
  });

  it("asks about this scan, and leaves Create pull request as the one main action", async () => {
    const api = renderWith(authValue({ chatAvailable: true }), scan({ id: 42 }, items()), {
      "POST /api/scans/42/chat": () => ({ body: { reply: "formatInvoice has no other use in the repo." } }),
    });
    await screen.findByRole("heading", { level: 1 });
    await userEvent.click(screen.getByRole("button", { name: "Ask about these results" }));
    await userEvent.type(screen.getByLabelText("Your question"), "Why is formatInvoice flagged?{Enter}");
    expect(await screen.findByText("formatInvoice has no other use in the repo.")).toBeInTheDocument();
    expect(api.calls.at(-1)).toEqual({ key: "POST /api/scans/42/chat", body: { messages: [{ role: "user", content: "Why is formatInvoice flagged?" }] } });
    expect(document.querySelectorAll(".btn-primary")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Create pull request" })).toHaveClass("btn-primary");
  });
});
