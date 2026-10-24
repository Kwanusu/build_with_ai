import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "./auth";
import { mockApi } from "./testing";

afterEach(() => vi.unstubAllGlobals());

function Probe() {
  const auth = useAuth();
  return (
    <div>
      <p>status: {auth.status}</p>
      <p>user: {auth.user ? auth.user.login : "nobody"}</p>
      <p>sign-in: {auth.signInAvailable ? "available" : "not available"}</p>
      <p>chat: {auth.chatAvailable ? "available" : "not available"}</p>
      <button onClick={() => void auth.signOut()}>out</button>
    </div>
  );
}

describe("AuthProvider", () => {
  it("is loading, then shows who is signed in", async () => {
    mockApi({ "GET /api/auth/me": () => ({ body: { user: { login: "octo", avatar_url: null }, sign_in_available: true, chat_available: true } }) });
    render(<AuthProvider><Probe /></AuthProvider>);
    expect(screen.getByText("status: loading")).toBeInTheDocument();
    expect(await screen.findByText("user: octo")).toBeInTheDocument();
    expect(screen.getByText("status: ready")).toBeInTheDocument();
    expect(screen.getByText("sign-in: available")).toBeInTheDocument();
    expect(screen.getByText("chat: available")).toBeInTheDocument();
  });

  it("treats a signed-out visitor as nobody, and remembers whether sign-in is set up", async () => {
    mockApi({ "GET /api/auth/me": () => ({ body: { user: null, sign_in_available: false } }) });
    render(<AuthProvider><Probe /></AuthProvider>);
    expect(await screen.findByText("user: nobody")).toBeInTheDocument();
    expect(screen.getByText("sign-in: not available")).toBeInTheDocument();
    // An older server doesn't say, which means no chat.
    expect(screen.getByText("chat: not available")).toBeInTheDocument();
  });

  it("behaves as signed out, not broken, when the server can't be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    render(<AuthProvider><Probe /></AuthProvider>);
    expect(await screen.findByText("status: ready")).toBeInTheDocument();
    expect(screen.getByText("user: nobody")).toBeInTheDocument();
  });

  it("signs out through the API and then asks who is signed in again", async () => {
    let signedIn = true;
    const { calls } = mockApi({
      "GET /api/auth/me": () => ({ body: { user: signedIn ? { login: "octo", avatar_url: null } : null, sign_in_available: true } }),
      "POST /api/auth/logout": () => {
        signedIn = false;
        return { body: { ok: true } };
      },
    });
    render(<AuthProvider><Probe /></AuthProvider>);
    await screen.findByText("user: octo");
    await userEvent.click(screen.getByRole("button", { name: "out" }));
    await waitFor(() => expect(screen.getByText("user: nobody")).toBeInTheDocument());
    expect(calls.map((c) => c.key)).toEqual(["GET /api/auth/me", "POST /api/auth/logout", "GET /api/auth/me"]);
  });

  it("without a provider, nobody is signed in and sign-in isn't offered", () => {
    render(<Probe />);
    expect(screen.getByText("status: ready")).toBeInTheDocument();
    expect(screen.getByText("user: nobody")).toBeInTheDocument();
    expect(screen.getByText("sign-in: not available")).toBeInTheDocument();
  });
});
