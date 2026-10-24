import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthContext } from "../auth";
import { OCTO, authValue } from "../testing";
import { Header } from "./Header";

const renderHeader = (auth = authValue(), showAction = true) => {
  render(
    <AuthContext.Provider value={auth}>
      <Header showAction={showAction} />
    </AuthContext.Provider>,
  );
  return auth;
};

describe("the header when you're signed out", () => {
  it("offers Connect a GitHub repo on the landing page", () => {
    renderHeader();
    expect(screen.getByRole("link", { name: "Connect a GitHub repo" })).toHaveAttribute("href", "#/scan");
    expect(screen.queryByRole("button", { name: "Sign out" })).toBeNull();
  });

  it("offers nothing extra on the scan page, which has its own sign-in button", () => {
    renderHeader(authValue(), false);
    expect(screen.queryByRole("link", { name: "Connect a GitHub repo" })).toBeNull();
    // The theme toggle is the only button.
    expect(screen.getAllByRole("button").map((button) => button.getAttribute("aria-label"))).toEqual([
      expect.stringMatching(/^Theme: /),
    ]);
  });

  it("has the theme toggle, for tablets and up", () => {
    renderHeader();
    const toggle = screen.getByRole("button", { name: /^Theme: / });
    expect(toggle).toHaveClass("hidden", "sm:inline-flex");
  });
});

describe("the header when you're signed in", () => {
  it("shows who you are and a way to sign out, on every page", () => {
    renderHeader(authValue({ user: OCTO }));
    expect(screen.getByText("@octo")).toBeInTheDocument();
    expect(screen.getByText(/Signed in as/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign out" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Connect a GitHub repo" })).toBeNull();
  });

  it("hides the avatar from screen readers because the name is already there", () => {
    const { container } = render(
      <AuthContext.Provider value={authValue({ user: OCTO })}>
        <Header />
      </AuthContext.Provider>,
    );
    const avatar = container.querySelector("img.avatar")!;
    expect(avatar).toHaveAttribute("src", "https://avatars.example/octo.png");
    expect(avatar).toHaveAttribute("alt", "");
  });

  it("copes with a user who has no avatar", () => {
    const { container } = render(
      <AuthContext.Provider value={authValue({ user: { login: "ghost", avatar_url: null } })}>
        <Header />
      </AuthContext.Provider>,
    );
    expect(container.querySelector("img.avatar")).toBeNull();
    expect(screen.getByText("@ghost")).toBeInTheDocument();
  });

  it("signs out, showing that it is working", async () => {
    let finish: () => void = () => {};
    const auth = authValue({ user: OCTO, signOut: vi.fn(() => new Promise<void>((resolve) => (finish = resolve))) });
    renderHeader(auth);
    await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
    expect(auth.signOut).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Signing out" })).toBeDisabled();
    finish();
    await waitFor(() => expect(screen.getByRole("button", { name: "Sign out" })).toBeEnabled());
  });

  it("keeps the one-ochre-button rule: the account area adds no primary button", () => {
    renderHeader(authValue({ user: OCTO }));
    expect(document.querySelectorAll(".btn-primary")).toHaveLength(0);
  });
});
