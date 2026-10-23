import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthContext } from "../auth";
import { OCTO, authValue, mockApi, repoSummary } from "../testing";
import { Connect } from "./Connect";

afterEach(() => vi.unstubAllGlobals());

const renderConnect = (auth = authValue(), onSubmit = vi.fn(async () => {}), extra: { notice?: string; initialUrl?: string } = {}) => {
  render(
    <AuthContext.Provider value={auth}>
      <Connect onSubmit={onSubmit} {...extra} />
    </AuthContext.Provider>,
  );
  return { onSubmit, auth };
};

const primaryButtons = () => document.querySelectorAll(".btn-primary");

describe("when sign-in isn't set up", () => {
  it("is just the public repo form, with Scan repo as the one main action", () => {
    renderConnect();
    expect(screen.getByRole("heading", { level: 1, name: "Scan a public GitHub repo" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Sign in with GitHub" })).toBeNull();
    expect(primaryButtons()).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Scan repo" })).toHaveClass("btn-primary");
  });
});

describe("when you're signed out and sign-in is available", () => {
  const signedOut = () => authValue({ signInAvailable: true });

  it("makes Sign in with GitHub the one main action and offers public repos as the alternative", () => {
    renderConnect(signedOut());
    expect(screen.getByRole("heading", { level: 1, name: "Connect a GitHub repo" })).toBeInTheDocument();
    const signIn = screen.getByRole("link", { name: "Sign in with GitHub" });
    expect(signIn).toHaveAttribute("href", "/api/auth/github/login");
    expect(signIn).toHaveClass("btn-primary");
    expect(screen.getByRole("heading", { level: 2, name: "Or scan a public repo" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Scan repo" })).toHaveClass("btn-secondary");
    expect(primaryButtons()).toHaveLength(1);
    expect(screen.getByText(/GitHub will show you what Lopper is asking for/)).toBeInTheDocument();
  });

  it("says it reads code and never changes it", () => {
    renderConnect(signedOut());
    expect(screen.getByText(/We read the code and never change it/)).toBeInTheDocument();
  });

  it("scans a pasted public URL without signing in", async () => {
    const { onSubmit } = renderConnect(signedOut());
    await userEvent.type(screen.getByLabelText("GitHub repo URL"), "https://github.com/acme/web-platform");
    await userEvent.click(screen.getByRole("button", { name: "Scan repo" }));
    expect(onSubmit).toHaveBeenCalledWith("https://github.com/acme/web-platform");
  });

  it("shows a notice above the sign-in button when there is one", () => {
    renderConnect(signedOut(), undefined, { notice: "We haven't scanned that repo yet. Scan it to see what we find." });
    expect(screen.getByRole("status")).toHaveTextContent("We haven't scanned that repo yet");
  });
});

describe("while we find out who you are", () => {
  it("says so and offers nothing yet", () => {
    renderConnect(authValue({ status: "loading", signInAvailable: true }));
    expect(screen.getByRole("status")).toHaveTextContent("Checking your sign-in");
    expect(screen.queryByRole("link", { name: "Sign in with GitHub" })).toBeNull();
    expect(screen.queryByLabelText("GitHub repo URL")).toBeNull();
  });
});

describe("when you're signed in", () => {
  const signedIn = () => authValue({ user: OCTO, signInAvailable: true });
  const repos = [
    repoSummary({ full_name: "octo/web", private: true, language: "TypeScript", pushed_at: "2026-10-20T10:00:00Z" }),
    repoSummary({ full_name: "octo/api", name: "api", language: "Python" }),
    repoSummary({ full_name: "octo/notes", name: "notes", language: null, pushed_at: null }),
  ];

  it("lists your repos with Private badges, the language and when they were last pushed", async () => {
    mockApi({ "GET /api/repos": () => ({ body: { repos } }) });
    renderConnect(signedIn());
    expect(screen.getByRole("heading", { level: 1, name: "Choose a repo to scan" })).toBeInTheDocument();
    const list = await screen.findByRole("list", { name: "Your repos" });
    const rows = within(list).getAllByRole("listitem");
    expect(rows).toHaveLength(3);
    expect(within(rows[0]).getByText("octo/web")).toBeInTheDocument();
    expect(within(rows[0]).getByText("Private")).toBeInTheDocument();
    expect(within(rows[0]).getByText(/TypeScript · Pushed .* ago/)).toBeInTheDocument();
    expect(within(rows[1]).queryByText("Private")).toBeNull();
    expect(within(rows[2]).getByText("Pushed never")).toBeInTheDocument();
  });

  it("doesn't say public repos only, because your account can read private ones", async () => {
    mockApi({ "GET /api/repos": () => ({ body: { repos } }) });
    renderConnect(signedIn());
    await screen.findByRole("list", { name: "Your repos" });
    expect(screen.getByText(/Any repo your GitHub account can read/)).toBeInTheDocument();
    expect(screen.queryByText(/Public repos only/)).toBeNull();
  });

  it("makes the paste form, not a repo row, the one main action", async () => {
    mockApi({ "GET /api/repos": () => ({ body: { repos } }) });
    renderConnect(signedIn());
    await screen.findByRole("list", { name: "Your repos" });
    expect(primaryButtons()).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Scan repo" })).toHaveClass("btn-primary");
    expect(screen.getByRole("button", { name: "Scan octo/web" })).toHaveClass("btn-secondary");
  });

  it("scans the repo you pick, and shows it is starting", async () => {
    mockApi({ "GET /api/repos": () => ({ body: { repos } }) });
    let finish: () => void = () => {};
    const onSubmit = vi.fn(() => new Promise<void>((resolve) => (finish = resolve)));
    renderConnect(signedIn(), onSubmit);
    await userEvent.click(await screen.findByRole("button", { name: "Scan octo/web" }));
    expect(onSubmit).toHaveBeenCalledWith("https://github.com/octo/web");
    expect(screen.getByRole("button", { name: "Scan octo/web" })).toHaveTextContent("Starting");
    expect(screen.getByRole("button", { name: "Scan octo/api" })).toBeDisabled();
    finish();
    await waitFor(() => expect(screen.getByRole("button", { name: "Scan octo/web" })).toHaveTextContent("Scan"));
  });

  it("explains a failure to start a scan and lets you try another", async () => {
    mockApi({ "GET /api/repos": () => ({ body: { repos } }) });
    const onSubmit = vi.fn(async () => {
      throw new Error("boom");
    });
    renderConnect(signedIn(), onSubmit);
    await userEvent.click(await screen.findByRole("button", { name: "Scan octo/web" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Something went wrong. Nothing has been changed.");
    expect(screen.getByRole("button", { name: "Scan octo/api" })).toBeEnabled();
  });

  it("filters by name", async () => {
    mockApi({ "GET /api/repos": () => ({ body: { repos } }) });
    renderConnect(signedIn());
    await screen.findByRole("list", { name: "Your repos" });
    await userEvent.type(screen.getByLabelText("Filter your repos"), "API");
    expect(within(screen.getByRole("list", { name: "Your repos" })).getAllByRole("listitem")).toHaveLength(1);
    expect(screen.getByText("octo/api")).toBeInTheDocument();
    await userEvent.clear(screen.getByLabelText("Filter your repos"));
    await userEvent.type(screen.getByLabelText("Filter your repos"), "zzz");
    expect(screen.getByText("No repos match that. Try part of the name.")).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Your repos" })).toBeNull();
  });

  it("says so when you have no repos, and still lets you paste a URL", async () => {
    mockApi({ "GET /api/repos": () => ({ body: { repos: [] } }) });
    renderConnect(signedIn());
    expect(await screen.findByText(/We couldn't find any repos on your account/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Filter your repos")).toBeNull();
    expect(screen.getByLabelText("GitHub repo URL")).toBeInTheDocument();
  });

  it("explains when GitHub can't be reached and lets you try again", async () => {
    let attempts = 0;
    mockApi({
      "GET /api/repos": () => {
        attempts++;
        return attempts === 1
          ? { status: 502, body: { error: "We couldn't reach GitHub to list your repos. Try again in a moment. Nothing has been changed.", code: "github_unavailable" } }
          : { body: { repos } };
      },
    });
    renderConnect(signedIn());
    expect(await screen.findByRole("alert")).toHaveTextContent("We couldn't reach GitHub to list your repos");
    expect(screen.getByLabelText("GitHub repo URL")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("list", { name: "Your repos" })).toBeInTheDocument();
  });

  it("asks who is signed in again when the server says the sign-in has ended", async () => {
    mockApi({ "GET /api/repos": () => ({ status: 401, body: { error: "GitHub no longer accepts your sign-in.", code: "sign_in_required" } }) });
    const { auth } = renderConnect(signedIn());
    await waitFor(() => expect(auth.refresh).toHaveBeenCalledTimes(1));
  });
});
