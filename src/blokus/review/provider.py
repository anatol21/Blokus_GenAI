"""OpenRouter-backed model provider for agentic review."""

from __future__ import annotations

import json
import os
import time
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
    max_retries: int

    @classmethod
    def from_env(cls, config: ReviewConfig) -> "OpenRouterClient":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ProviderUnavailable("`OPENROUTER_API_KEY` is not set.")
        return cls(
            api_key=api_key,
            base_url=config.provider.base_url.rstrip("/"),
            timeout_seconds=config.provider.timeout_seconds,
            max_retries=config.provider.max_retries,
        )

    def complete(self, *, model: str, system_prompt: str, user_prompt: str) -> str:
        if self.max_retries < 0:
            raise ProviderUnavailable("OpenRouter `max_retries` must be greater than or equal to 0.")
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

        attempt_count = self.max_retries + 1
        body: object | None = None
        for attempt in range(1, attempt_count + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    raw_body = response.read()
                    body = json.loads(raw_body.decode("utf-8"))
                break
            except HTTPError as exc:
                if attempt == attempt_count or not _is_retryable_http_error(exc):
                    raise ProviderUnavailable(f"OpenRouter request failed: {exc}") from exc
                _sleep_before_retry(attempt)
            except (URLError, TimeoutError) as exc:
                if attempt == attempt_count:
                    raise ProviderUnavailable(
                        f"OpenRouter request failed after {attempt_count} attempts: {exc}"
                    ) from exc
                _sleep_before_retry(attempt)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                if attempt == attempt_count:
                    raise ProviderUnavailable("OpenRouter response was not valid JSON.") from exc
                _sleep_before_retry(attempt)

        if body is None:
            raise ProviderUnavailable("OpenRouter request did not produce a response body.")

        try:
            return str(body["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderUnavailable("OpenRouter response did not contain a usable message.") from exc


def _is_retryable_http_error(error: HTTPError) -> bool:
    return error.code in {408, 425, 429, 500, 502, 503, 504}


def _sleep_before_retry(attempt: int) -> None:
    time.sleep(min(0.25 * attempt, 1.0))
