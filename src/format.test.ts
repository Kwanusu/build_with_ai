import { timeAgo } from "./format";

const now = new Date("2026-10-23T12:00:00Z");

describe("timeAgo", () => {
  it.each([
    ["2026-10-23T11:59:30Z", "just now"],
    ["2026-10-23T11:59:00Z", "1 minute ago"],
    ["2026-10-23T11:15:00Z", "45 minutes ago"],
    ["2026-10-23T10:00:00Z", "2 hours ago"],
    ["2026-10-22T12:00:00Z", "1 day ago"],
    ["2026-10-13T12:00:00Z", "10 days ago"],
    ["2026-08-23T12:00:00Z", "2 months ago"],
    ["2024-10-23T12:00:00Z", "2 years ago"],
  ])("%s is %s", (iso, expected) => {
    expect(timeAgo(iso, now)).toBe(expected);
  });

  it("copes with a missing or broken date, and a date in the future", () => {
    expect(timeAgo(null, now)).toBe("never");
    expect(timeAgo("not a date", now)).toBe("unknown");
    expect(timeAgo("2026-10-24T12:00:00Z", now)).toBe("just now");
  });
});
