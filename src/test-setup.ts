import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

// jsdom doesn't implement scrolling. (Tests that run in plain node, like the /api forwarder's, have no window.)
if (typeof window !== "undefined") {
  window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;
  Element.prototype.scrollIntoView = vi.fn();
}
