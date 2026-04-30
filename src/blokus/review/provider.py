"""OpenRouter-backed model provider for agentic review."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from blokus.review.config import ReviewConfig


class ProviderUnavailable(RuntimeError):
    """Raised when the LLM provider cannot be used."""


@dataclass(frozen=True)
class OpenRouterClient:
    """Thin OpenRouter client using the chat-completions API."""

    api_key: str
    base_url: str
    timeout_seconds: int

    @classmethod
    def from_env(cls, config: ReviewConfig) -> "OpenRouterClient":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ProviderUnavailable("`OPENROUTER_API_KEY` is not set.")
        return cls(
            api_key=api_key,
            base_url=config.provider.base_url.rstrip("/"),
            timeout_seconds=config.provider.timeout_seconds,
        )

    def complete(self, *, model: str, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        request.add_header("Content-Type", "application/json")
        request.add_header("Authorization", f"Bearer {self.api_key}")
        request.add_header("Accept", "application/json")

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ProviderUnavailable(f"OpenRouter request failed: {exc}") from exc

        try:
            return str(body["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderUnavailable("OpenRouter response did not contain a usable message.") from exc
