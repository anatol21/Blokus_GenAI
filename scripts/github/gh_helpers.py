"""Minimal GitHub REST helpers for workflow scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


API_ROOT = "https://api.github.com"


class GitHubClient:
    """Tiny REST client for repository-local GitHub workflow automation."""

    def __init__(self, repository: str, token: str) -> None:
        self.repository = repository
        self.token = token

    def _request_url(self, method: str, url: str, payload: dict[str, Any] | None = None) -> tuple[Any, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, method=method)
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("Authorization", f"Bearer {self.token}")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        if body is not None:
            request.add_header("Content-Type", "application/json")

        with urlopen(request) as response:
            text = response.read().decode("utf-8")
            data = None if not text else json.loads(text)
            return data, response.headers

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        data, _ = self._request_url(method, f"{API_ROOT}{path}", payload)
        return data

    def paginate(self, path: str) -> list[Any]:
        items: list[Any] = []
        next_url = f"{API_ROOT}{path}"
        while next_url:
            data, headers = self._request_url("GET", next_url)
            if isinstance(data, list):
                items.extend(data)
            elif data is not None:
                items.append(data)
            next_url = _next_link(headers.get("Link", ""))
        return items

    def list_issue_comments(self, issue_number: int) -> list[dict[str, Any]]:
        return self.paginate(f"/repos/{self.repository}/issues/{issue_number}/comments?per_page=100")

    def upsert_issue_comment(self, issue_number: int, marker: str, body: str) -> None:
        existing = None
        for comment in reversed(self.list_issue_comments(issue_number)):
            if marker in comment.get("body", ""):
                existing = comment
                break

        if existing is None:
            self.request(
                "POST",
                f"/repos/{self.repository}/issues/{issue_number}/comments",
                {"body": body},
            )
            return

        self.request(
            "PATCH",
            f"/repos/{self.repository}/issues/comments/{existing['id']}",
            {"body": body},
        )


def load_event_payload(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_link(link_header: str) -> str | None:
    for part in link_header.split(","):
        pieces = [piece.strip() for piece in part.split(";")]
        if len(pieces) < 2:
            continue
        if pieces[1] == 'rel="next"':
            return pieces[0].strip("<>")
    return None
