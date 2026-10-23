"""Talking to GitHub: the sign-in handshake and the list of a person's repos. Standard library only."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
API_URL = "https://api.github.com"


class GitHubError(Exception):
    """`code` is one of: unavailable, bad_code, token_invalid."""

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
