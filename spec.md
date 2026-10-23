That's all eight questions. Here's your spec.

---

# Product spec

## Product name
**Lopper**

## One line description
Find unused packages and exports in your monorepo, with no setup, and remove them through a pull request you can trust.

## Primary user
A senior engineer at a 40-person startup who owns a monorepo. Nobody knows which packages or exports are still used, so everyone is afraid to delete anything. They've tried tools like Knip, fought the config, and given up.

## User types and what each can do
One user type. Anyone who signs in with GitHub and has access to the repo can connect it, run a scan, tick findings, and open a pull request. GitHub's own permissions decide who can merge.

## Core action
Review a list of unused packages and exports, tick what to remove, and get a pull request that deletes it.

## Screens

**1. Connect repo**
- Shows: GitHub sign-in and a list of the user's repos.
- User can: sign in, pick a monorepo, start a scan.

**2. Results**
- Shows: unused packages and exports grouped by package, each with evidence of why it's unused.
- User can: read the evidence, tick items to remove, rescan, and click "Create pull request."

**3. Pull request created**
- Shows: a summary of what will be removed and a link to the PR on GitHub.
- User can: open the PR or go back to Results.

## Data

| Table | Fields | Read / written by |
|---|---|---|
| **Users** | id, GitHub username, GitHub access token | Written: Connect repo. Read: all screens |
| **Repos** | id, user id, GitHub repo name, default branch | Written: Connect repo. Read: Results |
| **Scans** | id, repo id, started at, status (running/done/failed) | Written: Connect repo, Results (rescan). Read: Results. Only the latest is kept per repo. |
| **Findings** | id, scan id, type (package/export), package name, item name, file path, evidence, ticked yes/no | Written: scan; Results (ticking). Read: Results, PR created. Replaced on each new scan. |
| **Pull requests** | id, repo id, GitHub PR link, created at, number of items removed | Written: Results. Read: PR created |

## Out of scope
- Feature flags (a different problem, maybe version two)
- Scan history and progress charts
- Deleting code directly without a pull request
- Roles, teams, or permissions beyond GitHub's own
- GitLab, Bitbucket, or non-JavaScript/TypeScript repos
- Scheduled or automatic scans

## Brand notes
You didn't say much about feel directly, but your answers point to two qualities. It should be **zero setup**, which is the opposite of config-heavy tools. It should also feel **trustworthy and calm**: always show the evidence, and never delete anything without a human approving it.

---

One last challenge before you build: everything depends on the scan being **right**. If it flags something as unused that is actually used, your user loses trust after one mistake. Before designing anything else, I'd test the scanner on two or three real monorepos and check how accurate it is.