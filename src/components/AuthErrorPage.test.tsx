import { render, screen } from "@testing-library/react";
import { AuthContext } from "../auth";
import { OCTO, authValue } from "../testing";
import { AuthErrorPage } from "./AuthErrorPage";

const renderPage = (code: string, auth = authValue({ signInAvailable: true })) =>
  render(
    <AuthContext.Provider value={auth}>
      <AuthErrorPage code={code} />
    </AuthContext.Provider>,
  );

describe("the sign-in error page", () => {
  it.each([
    ["access_denied", /You chose not to let Lopper in on GitHub/],
    ["invalid_state", /didn't match the one we started, or it took too long/],
    ["invalid_code", /GitHub didn't accept that sign-in/],
    ["github_unavailable", /We couldn't reach GitHub to finish signing you in/],
  ])("explains %s in plain words and says nothing was changed", (code, message) => {
    renderPage(code);
    expect(screen.getByRole("heading", { level: 1, name: "We couldn't sign you in" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(message);
    expect(screen.getByRole("alert")).toHaveTextContent("Nothing has been changed");
  });

  it("lets you try again, with the one main action being Sign in with GitHub", () => {
    renderPage("invalid_state");
    expect(screen.getByRole("link", { name: "Sign in with GitHub" })).toHaveAttribute("href", "/api/auth/github/login");
    expect(screen.getByRole("link", { name: "Sign in with GitHub" })).toHaveClass("btn-primary");
    expect(screen.getByRole("link", { name: "Scan a public repo" })).toHaveClass("btn-secondary");
    expect(document.querySelectorAll(".btn-primary")).toHaveLength(1);
  });

  it("says sign-in isn't set up, and offers only the public route, as the one main action", () => {
    renderPage("not_configured", authValue({ signInAvailable: false }));
    expect(screen.getByRole("alert")).toHaveTextContent("isn't set up on this server yet");
    expect(screen.queryByRole("link", { name: "Sign in with GitHub" })).toBeNull();
    expect(screen.getByRole("link", { name: "Scan a public repo" })).toHaveClass("btn-primary");
    expect(screen.getByRole("link", { name: "Scan a public repo" })).toHaveAttribute("href", "#/scan");
  });

  it("has a fallback for a reason it doesn't know", () => {
    renderPage("something_new");
    expect(screen.getByRole("alert")).toHaveTextContent("We couldn't sign you in. Nothing has been changed. Try again.");
  });

  it("doesn't ask someone who is already signed in to sign in again", () => {
    renderPage("invalid_state", authValue({ user: OCTO, signInAvailable: true }));
    expect(screen.queryByRole("link", { name: "Sign in with GitHub" })).toBeNull();
    expect(screen.getByRole("link", { name: "Scan a public repo" })).toBeInTheDocument();
  });
});
