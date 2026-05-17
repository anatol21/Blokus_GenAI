"""OpenRouter-backed provider client for agentic review specialists.

This module loads the OpenRouter API key from the environment, builds
chat-completions requests, sends specialist prompt text to the configured
provider URL, retries selected transient failures, and extracts returned message
content. Provider, transport, decoding, and response-shape problems are
normalized into ProviderUnavailable so callers can surface review uncertainty.
This module wraps an external API boundary; it does not prove provider
availability, response stability, credential safety outside this code, or schema
guarantees for the returned content.
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
    """Raised when the OpenRouter provider cannot complete review work.

    Purpose:
        Normalize credential, request, retry, decoding, and response-shape
        failures into one exception type for coordinator/specialist handling.
    Important parameters:
        Inherits RuntimeError message text from each raising branch.
    Return value:
        Exception type; no return value.
    Side effects:
        None.
    Failure or fallback behavior:
        Raised by OpenRouterClient.from_env() and OpenRouterClient.complete()
        instead of returning partial provider content.
    Trace:
        OpenRouterClient.from_env(), OpenRouterClient.complete(),
        coordinator ProviderUnavailable handling.
    """


@dataclass(frozen=True)
class OpenRouterClient:
    """Small OpenRouter chat-completions client for agentic review.

    Purpose:
        Hold provider configuration and send specialist prompts to the
        OpenRouter chat-completions endpoint.
    Important parameters:
        api_key is used for the Authorization header; base_url is normalized by
        from_env(); timeout_seconds is passed to urlopen(); max_retries controls
        retry attempts.
    Return value:
        complete() returns stripped message content from the first response
        choice.
    Side effects:
        Sends HTTP POST requests through urllib.request.urlopen().
    Failure or fallback behavior:
        Raises ProviderUnavailable for missing credentials, invalid retry
        budget, exhausted retries, invalid JSON, missing body, or unexpected
        response shape.
    Trace:
        from_env(), complete(), Request, urlopen, ProviderUnavailable.
    """

    api_key: str
    base_url: str
    timeout_seconds: int
    max_retries: int

    @classmethod
    def from_env(cls, config: ReviewConfig) -> "OpenRouterClient":
        """Create an OpenRouterClient from environment and review config.

        Purpose:
            Load OPENROUTER_API_KEY and combine it with provider settings from
            ReviewConfig.
        Important parameters:
            config.provider supplies base_url, timeout_seconds, and max_retries.
        Return value:
            OpenRouterClient with base_url stripped of trailing slashes.
        Side effects:
            Reads os.environ["OPENROUTER_API_KEY"] through os.environ.get().
        Failure or fallback behavior:
            Raises ProviderUnavailable when the environment variable is absent
            or falsey.
        Trace:
            os.environ.get(), ReviewConfig.provider, ProviderUnavailable.
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
        """Send one chat-completions request and return message content.

        Purpose:
            Submit specialist prompt text to OpenRouter and extract the first
            choice's message content.
        Important parameters:
            model is serialized into the JSON payload; system_prompt and
            user_prompt are sent as chat messages.
        Return value:
            Stripped string content from choices[0].message.content.
        Side effects:
            Builds a urllib Request, adds Content-Type, Authorization, and
            Accept headers, sends HTTP requests with urlopen(), and may sleep
            between retry attempts.
        Failure or fallback behavior:
            Negative max_retries raises immediately. Retryable HTTP errors,
            URLError, TimeoutError, JSONDecodeError, and UnicodeDecodeError
            retry until the attempt budget is exhausted. Non-retryable HTTP
            errors, exhausted network retries, invalid final JSON, empty body,
            and unexpected response shape raise ProviderUnavailable.
        Trace:
            Request(), request.add_header(), urlopen(timeout=timeout_seconds),
            _is_retryable_http_error(), _sleep_before_retry(), json.loads().
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
    """Return whether an HTTPError status should be retried.

    Purpose:
        Centralize the retryable HTTP status allowlist.
    Important parameters:
        error is urllib.error.HTTPError.
    Return value:
        True for status codes 408, 425, 429, 500, 502, 503, or 504.
    Side effects:
        None.
    Failure or fallback behavior:
        Any status code outside the set is treated as non-retryable by
        complete().
    Trace:
        OpenRouterClient.complete() HTTPError branch.
    """
    return error.code in {408, 425, 429, 500, 502, 503, 504}


def _sleep_before_retry(attempt: int, error: HTTPError | None = None) -> None:
    """Sleep before the next provider retry attempt.

    Purpose:
        Apply a small capped linear backoff between retryable provider failures.
    Important parameters:
        attempt is the 1-based attempt number passed by complete().
    Return value:
        None.
    Side effects:
        Calls time.sleep().
    Failure or fallback behavior:
        Sleep duration is min(0.25 * attempt, 1.0).
    Trace:
        time.sleep(), OpenRouterClient.complete() retry branches.
    """
    time.sleep(_retry_delay_seconds(attempt, error))


def _retry_delay_seconds(attempt: int, error: HTTPError | None = None) -> float:
    if error is not None and error.code == 429:
        retry_after = _retry_after_seconds(getattr(error, "headers", None))
        if retry_after is not None:
            return min(retry_after, _MAX_RETRY_AFTER_SECONDS)
        return min(float(2**attempt), 30.0)
    return min(0.25 * attempt, 1.0)


def _retry_after_seconds(headers: object) -> float | None:
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
