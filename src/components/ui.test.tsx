import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Button } from "./ui";

describe("Button", () => {
  it("renders a link when given an href", () => {
    render(<Button href="#/scan">Scan</Button>);
    const link = screen.getByRole("link", { name: "Scan" });
    expect(link).toHaveAttribute("href", "#/scan");
    expect(link).toHaveClass("btn", "btn-secondary");
    expect(link).not.toHaveAttribute("target");
  });

  it("opens an external link in a new tab without leaking the opener", () => {
    render(
      <Button href="https://github.com/octo/web/pull/1" external>
        Open
      </Button>,
    );
    const link = screen.getByRole("link", { name: "Open" });
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renders a button that calls onClick", () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Retry</Button>);
    const button = screen.getByRole("button", { name: "Retry" });
    expect(button).toHaveAttribute("type", "button");
    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("can be a submit button, disabled and busy", () => {
    render(
      <Button type="submit" disabled busy>
        Send
      </Button>,
    );
    const button = screen.getByRole("button", { name: "Send" });
    expect(button).toHaveAttribute("type", "submit");
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  });

  it("applies the variant and size classes", () => {
    render(
      <Button variant="plain" size="sm" onClick={() => {}}>
        Sign out
      </Button>,
    );
    const button = screen.getByRole("button", { name: "Sign out" });
    expect(button).toHaveClass("btn-plain", "btn-sm");
  });
});
