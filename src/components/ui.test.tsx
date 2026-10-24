import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { Button, IconButton, TextArea } from "./ui";

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

  it("says whether the thing it shows is showing", () => {
    const { rerender } = render(
      <Button expanded={false} onClick={() => {}}>
        Show
      </Button>,
    );
    expect(screen.getByRole("button", { name: "Show" })).toHaveAttribute("aria-expanded", "false");
    rerender(
      <Button expanded onClick={() => {}}>
        Show
      </Button>,
    );
    expect(screen.getByRole("button", { name: "Show" })).toHaveAttribute("aria-expanded", "true");
  });

  it("leaves aria-expanded off a button that doesn't show or hide anything", () => {
    render(<Button onClick={() => {}}>Retry</Button>);
    expect(screen.getByRole("button", { name: "Retry" })).not.toHaveAttribute("aria-expanded");
  });
});

describe("TextArea", () => {
  function Harness({ onEnter }: { onEnter?: () => void }) {
    const [value, setValue] = useState("");
    return <TextArea id="q" label="Your question" value={value} onChange={setValue} onEnter={onEnter} helper="Press Enter to send." />;
  }

  it("has a label and a helper that the field is described by", () => {
    render(<Harness />);
    const field = screen.getByLabelText("Your question");
    expect(field.tagName).toBe("TEXTAREA");
    expect(field).toHaveClass("input", "input-multiline");
    expect(field).toHaveAccessibleDescription("Press Enter to send.");
  });

  it("reports what is typed", async () => {
    render(<Harness />);
    await userEvent.type(screen.getByLabelText("Your question"), "Why?");
    expect(screen.getByLabelText("Your question")).toHaveValue("Why?");
  });

  it("calls onEnter for Enter but starts a new line for Shift and Enter", async () => {
    const onEnter = vi.fn();
    render(<Harness onEnter={onEnter} />);
    const field = screen.getByLabelText("Your question");
    await userEvent.type(field, "one{Shift>}{Enter}{/Shift}two");
    expect(onEnter).not.toHaveBeenCalled();
    expect(field).toHaveValue("one\ntwo");
    await userEvent.type(field, "{Enter}");
    expect(onEnter).toHaveBeenCalledTimes(1);
    expect(field).toHaveValue("one\ntwo"); // Enter on its own doesn't add a line
  });

  it("lets Enter add a line when nothing is listening for it", async () => {
    render(<Harness />);
    const field = screen.getByLabelText("Your question");
    await userEvent.type(field, "a{Enter}b");
    expect(field).toHaveValue("a\nb");
  });
});

describe("IconButton", () => {
  it("is a button named by its label, which is also its tooltip, and calls onClick", () => {
    const onClick = vi.fn();
    render(
      <IconButton label="Close" onClick={onClick}>
        <svg aria-hidden="true" />
      </IconButton>,
    );
    const button = screen.getByRole("button", { name: "Close" });
    expect(button).toHaveAttribute("type", "button");
    expect(button).toHaveAttribute("title", "Close");
    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("is plain and 40px by default, and takes a size and a variant", () => {
    render(
      <>
        <IconButton label="Default" onClick={() => {}}>
          <svg />
        </IconButton>
        <IconButton label="Small" size="sm" variant="secondary" onClick={() => {}}>
          <svg />
        </IconButton>
        <IconButton label="Large" size="lg" onClick={() => {}} className="sm:hidden">
          <svg />
        </IconButton>
      </>,
    );
    expect(screen.getByRole("button", { name: "Default" }).className).toBe("icon-btn");
    expect(screen.getByRole("button", { name: "Small" })).toHaveClass("icon-btn", "icon-btn-secondary", "icon-btn-sm");
    expect(screen.getByRole("button", { name: "Large" })).toHaveClass("icon-btn", "icon-btn-lg", "sm:hidden");
  });
});
