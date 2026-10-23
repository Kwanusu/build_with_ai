export const CTA_LABEL = "Connect a GitHub repo";
export const CTA_HREF = "#";

export interface NavLink {
  label: string;
  href: string;
}

export interface Card {
  title: string;
  body: string;
  badge?: string;
}

export interface Step extends Card {
  number: string;
}

export type FindingTone = "success" | "warning";

export interface ExampleFinding {
  statement: string;
  name: string;
  path: string;
  detail: string;
  tone: FindingTone;
  badge: string;
  ticked: boolean;
}

export const NAV_LINKS: NavLink[] = [
  { label: "How it works", href: "#how" },
  { label: "What it finds", href: "#finds" },
  { label: "Why you can trust it", href: "#trust" },
];

export const HERO = {
  title: "Prune dead code with the evidence in front of you",
  body: "Lopper scans your frontend and backend repos on every push, shows why each package or export looks unused, and opens a pull request for the ones you tick.",
  reassurance: "Nothing will be removed until you merge the pull request.",
  secondaryLabel: "See how it works",
};

export const EXAMPLE = {
  caption: "Example results · acme/web-platform",
  title: "Found 14 unused exports across 3 packages",
  summary: "This pull request would remove 1 item and leave 13 unused items for later.",
  findings: [
    {
      statement: "is exported but never imported",
      name: "formatInvoice",
      path: "packages/billing/src/format.ts:42",
      detail: "Searched 1,208 files across 12 packages and found 0 imports.",
      tone: "success",
      badge: "Safe to remove",
      ticked: true,
    },
    {
      statement: "is used only in tests",
      name: "parseLegacyToken",
      path: "packages/auth/src/token.ts:18",
      detail: "1 import, in packages/auth/src/token.test.ts.",
      tone: "warning",
      badge: "Needs a closer look",
      ticked: false,
    },
  ] satisfies ExampleFinding[],
};

export const HOW = {
  id: "how",
  title: "From push to pull request in three steps",
  intro: "There's nothing to configure. Sign in, read what we found, and decide.",
  steps: [
    {
      number: "01",
      title: "Connect a repo",
      body: "Sign in with GitHub and pick a repo. We start scanning right away, with no config files and no plugins.",
    },
    {
      number: "02",
      title: "Read the evidence",
      body: "Every finding shows where the code is defined, where we searched and why nothing uses it. Uncertain findings start unticked.",
    },
    {
      number: "03",
      title: "Create a pull request",
      body: "Tick what to remove and we open a pull request. You review it and merge it on GitHub.",
    },
  ] satisfies Step[],
};

export const FINDS = {
  id: "finds",
  title: "What Lopper looks for",
  intro:
    "We scan JavaScript, TypeScript, Python and Go on every push to the branches you choose, in frontend and backend code alike.",
  cards: [
    { title: "Unused packages", body: "Dependencies that no file in the repo imports." },
    {
      title: "Unused exports",
      body: "Functions, classes and constants that are exported but never imported.",
    },
    {
      title: "Unused dev dependencies",
      body: "Build and test tooling that no script or config refers to.",
    },
    {
      title: "Lint issues",
      body: "We list them so you can see them. We never remove them for you.",
      badge: "Report only",
    },
  ] satisfies Card[],
};

export const TRUST = {
  id: "trust",
  title: "A person decides every cut",
  intro: "Scans report and people remove. That's how it works, every time.",
  cards: [
    {
      title: "Evidence before every cut",
      body: "If we can't show why something is unused, we don't flag it.",
    },
    {
      title: "Ready the moment you arrive",
      body: "Sign in with GitHub, pick a repo, and the scan begins.",
    },
    {
      title: "A human hand on the shears",
      body: "Nothing leaves your codebase without a pull request a person has read and merged.",
    },
  ] satisfies Card[],
  push: {
    caption: "After each push",
    line: "Push e41c9a2 by @renata · 6 min ago",
    result: "This pull request leaves 2 unused items and 1 lint issue.",
  },
};

export const CLOSING = {
  title: "Start with one repo",
  body: "Pick a repo and we'll start scanning. Nothing will be removed until you merge the pull request.",
};

export const COPYRIGHT_HOLDER = "Lopper";

export const FOOTER_NOTE = "Automatic scans report and people remove. Lint issues are report only.";
