export const CTA_LABEL = "Connect a GitHub repo";
export const CTA_HREF = "#/scan";

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

export const SCAN = {
  form: {
    title: "Scan a public GitHub repo",
    intro: "Paste a repo URL and we'll start scanning. There's nothing to set up. We read the code and never change it.",
    label: "GitHub repo URL",
    helper: "Public repos only for now, like https://github.com/owner/repo.",
    helperSignedIn: "Any repo your GitHub account can read, like https://github.com/owner/repo.",
    placeholder: "https://github.com/owner/repo",
    submit: "Scan repo",
    submitting: "Starting the scan",
    notScanned: "We haven't scanned that repo yet. Scan it to see what we find.",
  },
  scanning: {
    body: "We're reading the repo. Your code isn't being changed.",
    slow: "This is taking longer than usual. You can leave this page open, or come back to this address later.",
  },
  results: {
    rescan: "Rescan repo",
    rescanning: "Starting the scan",
    otherRepo: "Scan another repo",
    notice:
      "Nothing will be removed until you merge the pull request. Tick what you want gone, then create a pull request and read it before you merge.",
    createPr: "Create pull request",
    creatingPr: "Creating pull request",
    prHelp: "Tick at least one item to create a pull request.",
    prScope: "Lopper edits JavaScript and TypeScript projects for now. Anything it can't change is left on your list.",
    lintNote: "Lint issues are report only.",
    openOnGithub: "Open on GitHub",
    tickHelp: "Items with no use found start ticked. Items that need a closer look start unticked.",
    tickError: "We couldn't save that change. Nothing has been changed in your code. Try again.",
  },
  error: {
    title: "We couldn't finish that scan",
    retry: "Scan again",
    other: "Use a different repo",
  },
  groups: [
    { type: "unused-package", title: "Unused packages" },
    { type: "unused-dev-dependency", title: "Unused dev dependencies" },
    { type: "unused-export", title: "Unused exports" },
    { type: "lint-issue", title: "Lint issues", badge: "Report only" },
  ] as const,
  badges: { safe: "No use found", uncertain: "Needs a closer look" },
};

export const CONNECT = {
  signedOut: {
    title: "Connect a GitHub repo",
    intro:
      "Sign in with GitHub to scan any repo you can access, including private ones, and keep your choices. We read the code and never change it.",
    signIn: "Sign in with GitHub",
    permissions: "GitHub will show you what Lopper is asking for before you agree.",
    orPublic: "Or scan a public repo",
  },
  picker: {
    title: "Choose a repo to scan",
    intro: "Pick one of your repos, or paste a repo URL below.",
    filterLabel: "Filter your repos",
    filterPlaceholder: "Search by name",
    scan: "Scan",
    starting: "Starting",
    loading: "Loading your repos",
    empty: "We couldn't find any repos on your account. Paste a repo URL below instead.",
    noMatches: "No repos match that. Try part of the name.",
    private: "Private",
    retry: "Try again",
    pasteTitle: "Or paste a repo URL",
  },
};

export const ACCOUNT = {
  signOut: "Sign out",
  signingOut: "Signing out",
  signedInAs: "Signed in as",
};

export const AUTH_ERROR = {
  title: "We couldn't sign you in",
  retry: "Sign in with GitHub",
  publicRepo: "Scan a public repo",
  messages: {
    access_denied: "You chose not to let Lopper in on GitHub, so you're not signed in. Nothing has been changed.",
    invalid_state: "That sign-in didn't match the one we started, or it took too long. Nothing has been changed. Try again.",
    invalid_code: "GitHub didn't accept that sign-in. Nothing has been changed. Try again.",
    github_unavailable: "We couldn't reach GitHub to finish signing you in. Nothing has been changed. Try again in a moment.",
    not_configured: "Sign-in with GitHub isn't set up on this server yet. You can still scan a public repo.",
  } as Record<string, string>,
  fallback: "We couldn't sign you in. Nothing has been changed. Try again.",
};

export const PULL_REQUEST = {
  title: "Pull request created",
  summary: (changes: number, repo: string) =>
    `${changes.toLocaleString("en-US")} ${changes === 1 ? "change" : "changes"} on a new branch of ${repo}. Nothing is removed until you merge it.`,
  open: "Open pull request on GitHub",
  back: "Back to results",
  changesTitle: "What changed",
  leftTitle: "Left for you",
  leftIntro: "Lopper couldn't make these changes on its own. They're still on your list.",
  lockfiles: "Lock files aren't updated. Run your install command to refresh them.",
};

export const CANNOT_TICK = {
  signedOut: "Sign in with GitHub to tick items and keep your choices.",
  publicScan: "This is a public scan, so items can't be ticked on it. Rescan to get your own copy that you can tick.",
};
