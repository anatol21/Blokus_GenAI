"""OpenRouter-backed model provider for agentic review.

This module builds OpenRouter chat-completions requests for specialist
review prompts. It loads the bearer token from ``OPENROUTER_API_KEY`` and
uses provider settings from ``ReviewConfig`` for the base URL, timeout, and
retry budget. It bounds response reads, normalizes supported message-content
shapes, and maps provider failures to ``ProviderUnavailable``.
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from blokus.review.config import MAX_PROVIDER_RETRIES, ReviewConfig


_MAX_OPENROUTER_RESPONSE_BYTES = 1_000_000
_MAX_CONCURRENT_OPENROUTER_REQUESTS = 2
_MAX_RETRY_AFTER_SECONDS = 30.0
_OPENROUTER_REQUEST_SEMAPHORE = threading.Semaphore(_MAX_CONCURRENT_OPENROUTER_REQUESTS)


class ProviderUnavailable(RuntimeError):
    """Raised when the configured LLM provider cannot complete a request."""


@dataclass(frozen=True)
class OpenRouterClient:
    """Thin OpenRouter client using the chat-completions API.

    Attributes:
        api_key: Bearer token sent in the OpenRouter ``Authorization``
            header.
        base_url: OpenRouter API base URL without a trailing slash.
        timeout_seconds: Timeout passed to ``urlopen`` for each request.
        max_retries: Number of retries after the first request attempt.

    Warning:
        The dataclass stores ``api_key`` as a normal field, so the generated
        representation includes the token unless the class definition changes.
        Avoid logging or exposing client instances directly.
    """

    api_key: str
    base_url: str
    timeout_seconds: int
    max_retries: int

    @classmethod
    def from_env(cls, config: ReviewConfig) -> "OpenRouterClient":
        """Create a client from review config and ``OPENROUTER_API_KEY``.

        Args:
            config: Review configuration containing provider base URL,
                timeout, and retry settings.

        Returns:
            An ``OpenRouterClient`` configured for the provider block in
            ``config``.

        Raises:
            ProviderUnavailable: If ``OPENROUTER_API_KEY`` is not present in
                the environment.
        """
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
        """Request one chat-completion message from OpenRouter.

        Args:
            model: OpenRouter model identifier to include in the request
                payload.
            system_prompt: System message content sent before the user prompt.
            user_prompt: User message content sent to the model.

        Returns:
            The first response choice's normalized message content.

        Raises:
            ProviderUnavailable: If ``max_retries`` is outside the allowed
                range, the request fails beyond the retry budget, a
                non-retryable HTTP error is returned, the response cannot be
                decoded as JSON, or the JSON body does not contain usable
                message content.
        """
        if self.max_retries < 0:
            raise ProviderUnavailable("OpenRouter `max_retries` must be greater than or equal to 0.")
        if self.max_retries > MAX_PROVIDER_RETRIES:
            raise ProviderUnavailable(
                f"OpenRouter `max_retries` must be less than or equal to {MAX_PROVIDER_RETRIES}."
            )
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
        last_error: Exception | None = None
        for attempt in range(1, attempt_count + 1):
            try:
                with _OPENROUTER_REQUEST_SEMAPHORE:
                    with urlopen(request, timeout=self.timeout_seconds) as response:
                        raw_body = _read_bounded_response(response)
                        body = json.loads(raw_body.decode("utf-8"))
                break
            except HTTPError as exc:
                last_error = exc
                if attempt >= attempt_count or not _is_retryable_http_error(exc):
                    raise ProviderUnavailable(f"OpenRouter request failed: {exc}") from exc
                _sleep_before_retry(attempt, exc)
            except (URLError, TimeoutError) as exc:
                last_error = exc
                if attempt >= attempt_count:
                    raise ProviderUnavailable(
                        f"OpenRouter request failed after {attempt_count} attempts: {exc}"
                    ) from exc
                _sleep_before_retry(attempt)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                last_error = exc
                if attempt >= attempt_count:
                    raise ProviderUnavailable("OpenRouter response was not valid JSON.") from exc
                _sleep_before_retry(attempt)

        if body is None:
            if last_error is not None:
                raise ProviderUnavailable("OpenRouter request failed before producing a response body.") from last_error
            raise ProviderUnavailable("OpenRouter request did not produce a response body.")

        if not isinstance(body, dict):
            raise ProviderUnavailable("OpenRouter response did not contain a usable message.")
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderUnavailable("OpenRouter response did not contain a usable message.")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ProviderUnavailable("OpenRouter response did not contain a usable message.")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise ProviderUnavailable("OpenRouter response did not contain a usable message.")
        content = message.get("content")
        if content is None:
            raise ProviderUnavailable("OpenRouter response did not contain a usable message.")
        return _normalize_message_content(content)


def _read_bounded_response(response: object) -> bytes:
    """Read a response body without exceeding the configured byte limit.

    Args:
        response: Object returned by ``urlopen``.

    Returns:
        Response body bytes.

    Raises:
        ProviderUnavailable: If the response declares or returns a body larger
            than the safe size limit, cannot be read, or returns a non-binary
            body.
    """
    content_length = _content_length_header(response)
    if content_length is not None and content_length > _MAX_OPENROUTER_RESPONSE_BYTES:
        raise ProviderUnavailable(
            f"OpenRouter response exceeded the safe size limit of {_MAX_OPENROUTER_RESPONSE_BYTES} bytes."
        )

    read = getattr(response, "read", None)
    if not callable(read):
        raise ProviderUnavailable("OpenRouter response body could not be read.")

    raw_body = read(_MAX_OPENROUTER_RESPONSE_BYTES + 1)
    if not isinstance(raw_body, (bytes, bytearray)):
        raise ProviderUnavailable("OpenRouter response body was not valid binary data.")
    if len(raw_body) > _MAX_OPENROUTER_RESPONSE_BYTES:
        raise ProviderUnavailable(
            f"OpenRouter response exceeded the safe size limit of {_MAX_OPENROUTER_RESPONSE_BYTES} bytes."
        )
    return bytes(raw_body)


def _content_length_header(response: object) -> int | None:
    """Parse a non-negative ``Content-Length`` header when present.

    Args:
        response: Object that may expose mapping-like ``headers``.

    Returns:
        Parsed non-negative content length, or ``None`` when the header is
        absent, unsupported, negative, or invalid.
    """
    headers = getattr(response, "headers", None)
    if headers is None or not hasattr(headers, "get"):
        return None

    raw_value = headers.get("Content-Length")
    if isinstance(raw_value, int):
        return raw_value if raw_value >= 0 else None
    if isinstance(raw_value, str):
        try:
            parsed = int(raw_value.strip())
        except ValueError:
            return None
        return parsed if parsed >= 0 else None
    return None


def _normalize_message_content(content: object) -> str:
    """Normalize supported OpenRouter message-content shapes.

    Args:
        content: Message ``content`` value from the first response choice.

    Returns:
        Stripped text content. Lists are reduced to string items and dict
        items with string ``text`` values.

    Raises:
        ProviderUnavailable: If the content type is unsupported or a list does
            not contain usable text.
    """
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)

        normalized = "".join(parts).strip()
        if normalized:
            return normalized

    raise ProviderUnavailable(
        f"OpenRouter response content had unsupported type `{type(content).__name__}`."
    )


def _is_retryable_http_error(error: HTTPError) -> bool:
    """Return whether an HTTP error should consume retry budget.

    Args:
        error: HTTP error raised while sending an OpenRouter request.

    Returns:
        ``True`` for HTTP status codes that this module retries, otherwise
        ``False``.
    """
    return error.code in {408, 425, 429, 500, 502, 503, 504}


def _sleep_before_retry(attempt: int, error: HTTPError | None = None) -> None:
    """Sleep for the retry delay selected for the failed attempt.

    Args:
        attempt: One-based attempt number that just failed.
        error: Optional HTTP error used to select rate-limit-aware delay.
    """
    time.sleep(_retry_delay_seconds(attempt, error))


def _retry_delay_seconds(attempt: int, error: HTTPError | None = None) -> float:
    """Return the delay before retrying an OpenRouter request.

    Args:
        attempt: One-based attempt number that just failed.
        error: Optional HTTP error whose status and headers may affect delay.

    Returns:
        Delay in seconds. HTTP 429 responses may use ``Retry-After`` when it
        is present and parseable.
    """
    if error is not None and error.code == 429:
        retry_after = _retry_after_seconds(getattr(error, "headers", None))
        if retry_after is not None:
            return min(retry_after, _MAX_RETRY_AFTER_SECONDS)
        return min(float(2**attempt), 30.0)
    return min(0.25 * attempt, 1.0)


def _retry_after_seconds(headers: object) -> float | None:
    """Parse a ``Retry-After`` header into seconds.

    Args:
        headers: Mapping-like header object that may contain ``Retry-After``.

    Returns:
        Non-negative delay in seconds, or ``None`` when the header is absent
        or cannot be parsed.
    """
    if headers is None or not hasattr(headers, "get"):
        return None

    raw_value = headers.get("Retry-After")
    if isinstance(raw_value, (int, float)):
        return max(0.0, float(raw_value))
    if not isinstance(raw_value, str):
        return None

    stripped = raw_value.strip()
    if not stripped:
        return None
    try:
        return max(0.0, float(stripped))
    except ValueError:
        pass
    try:
        retry_at = parsedate_to_datetime(stripped)
    except (TypeError, ValueError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
