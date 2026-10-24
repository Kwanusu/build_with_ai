"""Talking to GitHub: the sign-in handshake, a person's repos, and opening pull requests. Standard library only."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
API_URL = "https://api.github.com"


class GitHubError(Exception):
    """`code` is one of: unavailable, bad_code, token_invalid, not_found, forbidden, conflict."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class GitHubClient:
    def __init__(self, client_id: str, client_secret: str, scopes: str, timeout: int = 10) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes
        self.timeout = timeout

    def authorize_url(self, state: str) -> str:
        query = urllib.parse.urlencode({"client_id": self.client_id, "scope": self.scopes, "state": state, "allow_signup": "true"})
        return f"{AUTHORIZE_URL}?{query}"

    def _request(self, url: str, *, data: dict | None = None, token: str | None = None) -> dict | list:
        headers = {"Accept": "application/json", "User-Agent": "Lopper"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        request = urllib.request.Request(url, data=body, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310 - fixed https hosts above
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 401:
                raise GitHubError("token_invalid", "GitHub no longer accepts that sign-in.") from error
            raise GitHubError("unavailable", f"GitHub answered with an error ({error.code}).") from error
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
            raise GitHubError("unavailable", "We couldn't reach GitHub.") from error

    def exchange_code(self, code: str) -> str:
        reply = self._request(
            TOKEN_URL, data={"client_id": self.client_id, "client_secret": self.client_secret, "code": code}
        )
        token = reply.get("access_token") if isinstance(reply, dict) else None
        if not token:
            raise GitHubError("bad_code", "GitHub didn't accept that sign-in code.")
        return token

    def get_user(self, token: str) -> dict:
        user = self._request(f"{API_URL}/user", token=token)
        if not isinstance(user, dict) or "id" not in user or "login" not in user:
            raise GitHubError("unavailable", "GitHub sent back something we didn't expect.")
        return {"id": user["id"], "login": user["login"], "avatar_url": user.get("avatar_url")}

    def list_repos(self, token: str, limit: int = 300) -> list[dict]:
        repos: list[dict] = []
        page = 1
        while len(repos) < limit:
            query = urllib.parse.urlencode(
                {"per_page": 100, "page": page, "sort": "pushed", "affiliation": "owner,collaborator,organization_member"}
            )
            batch = self._request(f"{API_URL}/user/repos?{query}", token=token)
            if not isinstance(batch, list):
                raise GitHubError("unavailable", "GitHub sent back something we didn't expect.")
            for item in batch:
                if item.get("archived") or item.get("disabled"):
                    continue
                repos.append(
                    {
                        "full_name": item["full_name"],
                        "owner": item["owner"]["login"],
                        "name": item["name"],
                        "private": bool(item.get("private")),
                        "description": item.get("description"),
                        "language": item.get("language"),
                        "pushed_at": item.get("pushed_at"),
                    }
                )
            if len(batch) < 100:
                break
            page += 1
        return repos[:limit]

    # ----- pull requests -----

    def _rest(self, method: str, path: str, token: str, body: dict | None = None) -> dict | list:
        headers = {
            "Accept": "application/vnd.github+json", "User-Agent": "Lopper", "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(f"{API_URL}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310 - fixed https host above
                return json.load(response)
        except urllib.error.HTTPError as error:
            # Messages here are fixed text: nothing from the request, and never the token, goes into them.
            if error.code == 401:
                raise GitHubError("token_invalid", "GitHub no longer accepts that sign-in.") from error
            if error.code == 403:
                raise GitHubError("forbidden", "GitHub says this sign-in isn't allowed to do that.") from error
            if error.code == 404:
                raise GitHubError("not_found", "GitHub couldn't find that, or this sign-in can't see it.") from error
            if error.code in (409, 422):
                raise GitHubError("conflict", "GitHub refused the change.") from error
            raise GitHubError("unavailable", f"GitHub answered with an error ({error.code}).") from error
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
            raise GitHubError("unavailable", "We couldn't reach GitHub.") from error

    def get_repo(self, token: str, owner: str, name: str) -> dict:
        repo = self._rest("GET", f"/repos/{owner}/{name}", token)
        if not isinstance(repo, dict) or "default_branch" not in repo:
            raise GitHubError("unavailable", "GitHub sent back something we didn't expect.")
        permissions = repo.get("permissions") or {}
        return {"default_branch": repo["default_branch"], "can_push": bool(permissions.get("push") or permissions.get("admin"))}

    def read_file(self, token: str, owner: str, name: str, path: str, ref: str) -> str | None:
        """A file's text on a branch, or None if it isn't there (or isn't a plain text file)."""
        quoted = urllib.parse.quote(path, safe="/")
        try:
            item = self._rest("GET", f"/repos/{owner}/{name}/contents/{quoted}?ref={urllib.parse.quote(ref, safe='')}", token)
        except GitHubError as problem:
            if problem.code == "not_found":
                return None
            raise
        if not isinstance(item, dict) or item.get("type") != "file" or item.get("encoding") != "base64":
            return None
        try:
            return base64.b64decode(item["content"]).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return None

    def create_pull_request(
        self, token: str, owner: str, name: str, *, base: str, branch: str, title: str, body: str,
        commit_message: str, files: dict[str, str],
    ) -> dict:
        """Put `files` (path -> new text) in one commit on a new branch, and open a pull request into `base`.

        The default branch is never written to: the commit goes on `branch`, and a person merges the pull request.
        """
        repo = f"/repos/{owner}/{name}"
        head = self._rest("GET", f"{repo}/git/ref/heads/{urllib.parse.quote(base, safe='/')}", token)
        commit_sha = head["object"]["sha"]
        commit = self._rest("GET", f"{repo}/git/commits/{commit_sha}", token)
        tree = self._rest(
            "POST", f"{repo}/git/trees", token,
            {"base_tree": commit["tree"]["sha"],
             "tree": [{"path": path, "mode": "100644", "type": "blob", "content": text} for path, text in sorted(files.items())]},
        )
        new_commit = self._rest("POST", f"{repo}/git/commits", token, {"message": commit_message, "tree": tree["sha"], "parents": [commit_sha]})
        self._rest("POST", f"{repo}/git/refs", token, {"ref": f"refs/heads/{branch}", "sha": new_commit["sha"]})
        pull = self._rest("POST", f"{repo}/pulls", token, {"title": title, "head": branch, "base": base, "body": body})
        return {"url": pull["html_url"], "number": pull["number"], "branch": branch}
