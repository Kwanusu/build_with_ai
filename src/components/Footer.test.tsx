import { render, screen } from "@testing-library/react";
import { Footer } from "./Footer";

describe("the footer", () => {
  it("says who it belongs to and that automatic scans report and people remove", () => {
    render(<Footer />);
    expect(screen.getByText(/All rights reserved\./)).toBeInTheDocument();
    expect(screen.getByText(/Automatic scans report and people remove/)).toBeInTheDocument();
  });

  it("has the theme toggle for phones, where the header has no room for it", () => {
    render(<Footer />);
    const toggle = screen.getByRole("button", { name: /^Theme: / });
    expect(toggle).toHaveClass("sm:hidden", "icon-btn-lg"); // 48px, a comfortable target on a phone
  });
});
