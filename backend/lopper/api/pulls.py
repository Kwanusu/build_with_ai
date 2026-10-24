"""Opening a pull request from the items a person ticked.

Only a signed-in person can do it, only for their own finished scan, and only for what is ticked on it (the server's
copy, not a list the browser sends). The commit goes on a new branch and a person merges the pull request: the
default branch is never written to.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..changes import describe_pull_request, plan_changes
from .github import GitHubClient, GitHubError


class PullRequestError(Exception):
    def __init__(self, message: str, code: str, status: int, **extra) -> None:
        super().__init__(message)
        self.message, self.code, self.status, self.extra = message, code, status, extra


def open_pull_request(scan: dict, github: GitHubClient, token: str) -> dict:
    """Make the pull request for `scan`'s ticked items. Raises PullRequestError (or GitHubError) when it can't."""
    if not scan["can_tick"]:
        raise PullRequestError("Only the person who made a scan while signed in can open a pull request from it.", "public_scan", 403)
    if scan["status"] != "done":
        raise PullRequestError("That scan hasn't finished yet. Wait for it to finish, then try again.", "scan_not_done", 409)
    ticked = [f for f in scan["findings"] if f["ticked"] and not f["report_only"]]
    if not ticked:
        raise PullRequestError("Tick at least one item to include in the pull request. Nothing has been changed.", "nothing_ticked", 400)

    owner, name = scan["repo"]["owner"], scan["repo"]["name"]
    repo = github.get_repo(token, owner, name)
    if not repo["can_push"]:
        raise PullRequestError(
            f"Your GitHub account can't push to {owner}/{name}, so Lopper can't open a pull request there. "
            "Ask the owner for write access. Nothing has been changed.",
            "no_write_access", 403,
        )
    base = repo["default_branch"]

    plan = plan_changes(ticked, lambda path: github.read_file(token, owner, name, path, base))
    if not plan.files:
        raise PullRequestError(
            "Lopper can't make any of the ticked changes on its own. They're listed below for you to make by hand. Nothing has been changed.",
            "nothing_to_change", 422, skipped=plan.skipped,
        )

    title, body = describe_pull_request(f"{owner}/{name}", plan)
    branch = "lopper/remove-unused-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    pull = github.create_pull_request(
        token, owner, name, base=base, branch=branch, title=title, body=body, commit_message=title, files=plan.files
    )
    return {"pull_request": {**pull, "title": title, "base": base}, "applied": plan.applied, "skipped": plan.skipped}


def github_problem(problem: GitHubError, repo: str) -> tuple[str, str, int]:
    """(message, code, status) for a GitHub failure. Fixed text only: nothing from GitHub's reply is passed on."""
    if problem.code == "forbidden":
        return (
            f"GitHub didn't let Lopper write to {repo}. If it belongs to an organisation, the organisation may need to approve "
            "the Lopper app. Nothing has been changed.", "github_forbidden", 403,
        )
    if problem.code == "not_found":
        return (f"GitHub can't find {repo} with your sign-in. Nothing has been changed.", "github_not_found", 404)
    if problem.code == "conflict":
        return ("GitHub refused the change, for example because the branch already exists. Try again in a moment. Nothing has been changed on the default branch.", "github_conflict", 409)
    return ("We couldn't reach GitHub to open the pull request. Try again in a moment. Nothing has been changed.", "github_unavailable", 502)
