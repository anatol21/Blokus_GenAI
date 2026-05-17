"""Build and validate prompt-driven specialist review responses.

This module builds prompt payloads for specialist LLM reviewers and sends
bounded diff context to the configured provider. It loads common and
specialist-specific prompt assets, constructs user prompts with changed files,
commits, bias risks, and rendered diff text, then parses provider JSON
responses. Accepted findings are normalized only when they reference changed
files and overlap touched line spans; malformed, incomplete, or unrelated
output is discarded or converted into UncertainRisk where the parser explicitly
does so. The module is a prompt and response-validation layer, not proof that
LLM findings are complete, deterministic, or automatically correct.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from blokus.review.config import ReviewConfig
from blokus.review.prompts import load_prompt
from blokus.review.provider import OpenRouterClient
from blokus.review.types import ChangedFile, Finding, ReviewContext, SpecialistResponse, UncertainRisk, stable_finding_id

MAX_PROMPT_FILES = 80
MAX_PROMPT_COMMITS = 25
MAX_SPECIALIST_FINDINGS = 3
MAX_SPECIALIST_FINDINGS_TO_INSPECT = 100
MAX_SPECIALIST_UNCERTAIN_RISKS_TO_INSPECT = 25
MAX_UNMATCHED_PATH_UNCERTAIN_RISKS = 10


@dataclass(frozen=True)
class _PromptContextBlocks:
    file_list: str
    commit_block: str
    truncated: bool


@dataclass(frozen=True)
class SpecialistRunner:
    """Invoke specialist prompt reviews through the configured provider.

    Purpose:
        Load common and specialist prompt assets, build a bounded user prompt,
        call the provider, and parse the specialist's JSON response.
    Important parameters:
        config supplies prompt paths and model selection; provider is an
        OpenRouterClient-compatible object used by provider.complete().
    Return value:
        run() returns SpecialistResponse.
    Side effects:
        May read prompt files through load_prompt() and submit prompt text plus
        rendered diff context to provider.complete().
    Failure or fallback behavior:
        Missing prompt assets return a SpecialistResponse with an UncertainRisk;
        empty file sets return a no-findings response without provider calls.
    Trace:
        _common_prompt, _specialist_prompt(), _build_user_prompt(),
        OpenRouterClient.complete(), _parse_specialist_response().
    """

    config: ReviewConfig
    provider: OpenRouterClient
    _specialist_prompt_cache: dict[str, str] = field(default_factory=dict, init=False, repr=False, compare=False)

    @property
    def _common_prompt(self) -> str:
        cached = self._specialist_prompt_cache.get("__common__")
        if cached is None:
            cached = load_prompt(self.config, "review-common")
            self._specialist_prompt_cache["__common__"] = cached
        return cached


    def run(
        self,
        specialist: str,
        context: ReviewContext,
        files: tuple[ChangedFile, ...],
        rendered_diff: str,
    ) -> SpecialistResponse:
        """Run one specialist review and normalize its response.

        Purpose:
            Combine shared and specialist prompts, build the user prompt, submit
            it to the provider, and parse the provider response into review
            data.
        Important parameters:
            specialist selects `review-{specialist}` prompt and model; context,
            files, and rendered_diff define the scoped review input.
        Return value:
            SpecialistResponse containing accepted findings, uncertain risks,
            and note text.
        Side effects:
            Reads prompt assets and calls provider.complete() with model,
            system_prompt, and user_prompt.
        Failure or fallback behavior:
            No files returns a note-only response; FileNotFoundError while
            loading prompts returns an UncertainRisk and skips
            provider.complete().
        Trace:
            load_prompt(), config.model_for(), _build_user_prompt(),
            provider.complete(), _parse_specialist_response().
        """
        if not files:
            return SpecialistResponse(findings=(), note="No relevant files were available for this specialist.")

        try:
            common_prompt = self._common_prompt
        except FileNotFoundError:
            return _missing_prompt_response(
                prompt_name="review-common",
                specialist=specialist,
                shared=True,
            )

        try:
            specialist_prompt = self._specialist_prompt(specialist)
        except FileNotFoundError:
            return _missing_prompt_response(
                prompt_name=f"review-{specialist}",
                specialist=specialist,
                shared=False,
            )
        system_prompt = f"{common_prompt}\n\n{specialist_prompt}"
        user_prompt = _build_user_prompt(specialist, context, files, rendered_diff)
        raw_response = self.provider.complete(
            model=self.config.model_for(specialist),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        return _parse_specialist_response(raw_response, specialist, files)

    def _specialist_prompt(self, specialist: str) -> str:
        """Load and cache a specialist-specific prompt asset.

        Purpose:
            Resolve `.github/prompts/review-{specialist}.md` through
            load_prompt() once per SpecialistRunner instance.
        Important parameters:
            specialist is the prompt suffix used in `review-{specialist}`.
        Return value:
            Prompt text.
        Side effects:
            Reads from the configured prompt directory on cache miss and mutates
            _specialist_prompt_cache.
        Failure or fallback behavior:
            Propagates FileNotFoundError to run(), which converts it into an
            UncertainRisk response.
        Trace:
            load_prompt(), _specialist_prompt_cache, run().
        """
        prompt = self._specialist_prompt_cache.get(specialist)
        if prompt is None:
            prompt = load_prompt(self.config, f"review-{specialist}")
            self._specialist_prompt_cache[specialist] = prompt
        return prompt


def _build_user_prompt(
    specialist: str,
    context: ReviewContext,
    files: tuple[ChangedFile, ...],
    rendered_diff: str,
) -> str:
    """Build the user-facing prompt body for a specialist.

    Purpose:
        Combine file list, impact, branch, commit subjects, bias risks, response
        JSON shape, finding limit instruction, and rendered diff text.
    Important parameters:
        specialist names the reviewer role; context supplies metadata and bias
        risks; files scope prompt context; rendered_diff is the diff body.
    Return value:
        Stripped prompt string sent to provider.complete().
    Side effects:
        None.
    Failure or fallback behavior:
        Prompt context file/commit lists may contain omission notes produced by
        _build_prompt_context_blocks().
    Trace:
        _build_prompt_context_blocks(), MAX_PROMPT_FILES, MAX_PROMPT_COMMITS.
    """
    prompt_context = _build_prompt_context_blocks(context, files)
    bias_block = "\n".join(f"- {risk}" for risk in context.bias_risks)

    return f"""
Review the following files from the current diff against the base ref.

Files to review:
{prompt_context.file_list}

Context:
- Specialist: {specialist}
- Overall impact: {context.impact}
- Branch name: {context.branch_name}
- Commits:
{prompt_context.commit_block}
- Bias risks to avoid:
{bias_block}

Return JSON in this exact shape:
{{
  "findings": [
    {{
      "id": "optional-stable-id",
      "title": "Short finding title",
      "severity": "critical | high | moderate | low",
      "confidence": "high | medium | low",
      "category": "correctness | tests | performance | static-analysis | requirements",
      "file": "path/to/file",
      "line_start": 1,
      "line_end": 1,
      "evidence": "Concrete evidence from the diff.",
      "impact": "Concrete user or system impact.",
      "suggested_action": "Specific remediation.",
      "blocking_recommendation": true
    }}
  ],
  "uncertain_risks": [
    {{
      "risk": "Risk that could not be verified.",
      "reason_uncertain": "Why it remains uncertain.",
      "suggested_verification": "Concrete next verification step."
    }}
  ],
  "note": "Optional short note"
}}

Review only changed code. Do not exceed 3 findings.

Diff:
{rendered_diff}
""".strip()


def _parse_specialist_response(
    raw_response: str,
    specialist: str,
    files: tuple[ChangedFile, ...],
) -> SpecialistResponse:
    """Parse provider JSON into validated SpecialistResponse data.

    Purpose:
        Load JSON, accept only complete finding objects that match changed files
        and touched line spans, preserve valid uncertain risks, and cap findings
        to three.
    Important parameters:
        raw_response is provider text; specialist is used for source and
        fallback stable IDs; files are the changed files this specialist was
        asked to review.
    Return value:
        SpecialistResponse with tuple(findings[:3]), uncertain risks, and note.
    Side effects:
        None.
    Failure or fallback behavior:
        Invalid JSON returns an empty response with an invalid-response note;
        missing required finding keys, invalid line numbers, unmatched paths,
        and non-overlapping line spans are discarded. Unmatched paths add one or
        more UncertainRisk entries.
    Trace:
        _load_json_object(), _dict_list(), _index_changed_paths(),
        _lookup_changed_file(), _int_value(), ChangedFile.touches_span(),
        stable_finding_id().
    """
    data = _load_json_object(raw_response)
    changed_paths = _index_changed_paths(files)
    required_keys = {
        "title",
        "severity",
        "confidence",
        "category",
        "file",
        "line_start",
        "line_end",
        "evidence",
        "impact",
        "suggested_action",
        "blocking_recommendation",
    }

    findings: list[Finding] = []
    uncertain_risks: list[UncertainRisk] = []
    unmatched_paths: set[str] = set()
    findings_value = data.get("findings")
    raw_findings = findings_value if isinstance(findings_value, list) else []
    findings_were_truncated = len(raw_findings) > MAX_SPECIALIST_FINDINGS_TO_INSPECT
    for item in raw_findings[:MAX_SPECIALIST_FINDINGS_TO_INSPECT]:
        if not isinstance(item, dict):
            continue
        if not required_keys.issubset(item):
            continue
        raw_path = str(item["file"])
        changed_file = _lookup_changed_file(raw_path, changed_paths)
        if changed_file is None:
            normalized_path = _normalize_specialist_path(raw_path)
            if normalized_path:
                unmatched_paths.add(normalized_path)
            continue
        path = changed_file.path

        line_start = _int_value(item.get("line_start"))
        line_end = _int_value(item.get("line_end"))
        if line_start is None or line_end is None:
            continue
        if line_end < line_start:
            continue
        if changed_file.line_spans and not changed_file.touches_span(line_start, line_end):
            continue

        severity = _normalize_severity(item["severity"])
        confidence = _normalize_confidence(item["confidence"])
        category = _normalize_category(item["category"])

        findings.append(
            Finding(
                id=str(item.get("id") or stable_finding_id(specialist, path, line_start, item.get("title", ""))),
                title=str(item["title"]),
                severity=severity,
                confidence=confidence,
                category=category,
                file=path,
                line_start=line_start,
                line_end=line_end,
                evidence=str(item["evidence"]),
                impact=str(item["impact"]),
                suggested_action=str(item["suggested_action"]),
                blocking_recommendation=_parse_blocking_recommendation(item["blocking_recommendation"]),
                source=specialist,
            )
        )
        if len(findings) >= MAX_SPECIALIST_FINDINGS:
            break

    sorted_unmatched_paths = sorted(unmatched_paths)
    for unmatched_path in sorted_unmatched_paths[:MAX_UNMATCHED_PATH_UNCERTAIN_RISKS]:
        uncertain_risks.append(
            UncertainRisk(
                risk="Specialist findings were discarded because their file path did not match the current diff.",
                reason_uncertain=f"The specialist referenced `{unmatched_path}`, which could not be reconciled to a changed file path or rename target.",
                suggested_verification="Inspect the specialist output and normalize the referenced path if the finding should apply to a changed file.",
            )
        )

    if len(sorted_unmatched_paths) > MAX_UNMATCHED_PATH_UNCERTAIN_RISKS:
        omitted = len(sorted_unmatched_paths) - MAX_UNMATCHED_PATH_UNCERTAIN_RISKS
        uncertain_risks.append(
            UncertainRisk(
                risk="Additional unmatched specialist paths were omitted for scale.",
                reason_uncertain=(
                    f"{omitted} additional unmatched specialist paths were omitted after capping at "
                    f"{MAX_UNMATCHED_PATH_UNCERTAIN_RISKS}."
                ),
                suggested_verification="Inspect the raw specialist output if omitted unmatched paths may matter.",
            )
        )

    if findings_were_truncated:
        uncertain_risks.append(
            UncertainRisk(
                risk="Specialist findings were truncated for scale.",
                reason_uncertain=(
                    f"The specialist returned more than {MAX_SPECIALIST_FINDINGS_TO_INSPECT} raw findings, so only the "
                    f"first {MAX_SPECIALIST_FINDINGS_TO_INSPECT} were inspected."
                ),
                suggested_verification="Inspect the raw specialist output or rerun with a narrower diff if the omitted findings may matter.",
            )
        )

    uncertain_risks_value = data.get("uncertain_risks")
    raw_uncertain_risks = uncertain_risks_value if isinstance(uncertain_risks_value, list) else []
    uncertain_risks_were_truncated = len(raw_uncertain_risks) > MAX_SPECIALIST_UNCERTAIN_RISKS_TO_INSPECT
    for item in raw_uncertain_risks[:MAX_SPECIALIST_UNCERTAIN_RISKS_TO_INSPECT]:
        if not isinstance(item, dict):
            continue
        if not all(key in item for key in ("risk", "reason_uncertain", "suggested_verification")):
            continue
        uncertain_risks.append(
            UncertainRisk(
                risk=str(item["risk"]),
                reason_uncertain=str(item["reason_uncertain"]),
                suggested_verification=str(item["suggested_verification"]),
            )
        )
    if uncertain_risks_were_truncated:
        uncertain_risks.append(
            UncertainRisk(
                risk="Specialist uncertain risks were truncated for scale.",
                reason_uncertain=(
                    f"The specialist returned more than {MAX_SPECIALIST_UNCERTAIN_RISKS_TO_INSPECT} uncertain risks, "
                    f"so only the first {MAX_SPECIALIST_UNCERTAIN_RISKS_TO_INSPECT} were kept."
                ),
                suggested_verification="Inspect the raw specialist output if the omitted uncertain risks may matter.",
            )
        )

    return SpecialistResponse(
        findings=tuple(findings[:MAX_SPECIALIST_FINDINGS]),
        uncertain_risks=tuple(uncertain_risks),
        note=str(data.get("note", "")),
    )
def _int_value(value: object) -> int | None:
    """Parse provider line-number values as integers.

    Purpose:
        Convert line_start and line_end values from JSON output into ints for
        span validation.
    Important parameters:
        value is any JSON-derived object.
    Return value:
        int on successful conversion, otherwise None.
    Side effects:
        None.
    Failure or fallback behavior:
        TypeError and ValueError return None, causing the finding to be skipped.
    Trace:
        _parse_specialist_response(), ChangedFile.touches_span().
    """
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _parse_blocking_recommendation(value: object) -> bool:
    """Parse blocking_recommendation field safely.

    Handles JSON booleans, strings ("true"/"false"), and defaults to False.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value in {0, 0.0}:
            return False
        if value in {1, 1.0}:
            return True
        return False
    if isinstance(value, str):
        normalized = value.lower().strip()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    return False


def _normalize_severity(value: object) -> str:
    normalized = str(value).strip().lower()
    return {
        "medium": "moderate",
        "med": "moderate",
    }.get(normalized, normalized)


def _normalize_confidence(value: object) -> str:
    normalized = str(value).strip().lower()
    return {
        "moderate": "medium",
        "med": "medium",
    }.get(normalized, normalized)


def _normalize_category(value: object) -> str:
    return str(value).strip().lower().replace("_", "-").replace(" ", "-")


def _missing_prompt_response(*, prompt_name: str, specialist: str, shared: bool) -> SpecialistResponse:
    if shared:
        risk = "The shared review prompt asset was unavailable."
        reason_uncertain = (
            f"The shared `{prompt_name}` prompt could not be loaded from the configured prompt directory, "
            f"so the `{specialist}` specialist could not be prepared."
        )
        suggested_verification = (
            "Restore `.github/prompts/review-common.md` or update the configured prompt path before rerunning the review."
        )
        note = "Prompt asset missing for `review-common`."
    else:
        risk = "A specialist prompt asset was unavailable."
        reason_uncertain = (
            f"The `{specialist}` specialist prompt could not be loaded from the configured prompt directory."
        )
        suggested_verification = (
            f"Restore `.github/prompts/{prompt_name}.md` or update the configured prompt path before rerunning the review."
        )
        note = f"Prompt asset missing for specialist `{specialist}`."

    return SpecialistResponse(
        findings=(),
        uncertain_risks=(
            UncertainRisk(
                risk=risk,
                reason_uncertain=reason_uncertain,
                suggested_verification=suggested_verification,
            ),
        ),
        note=note,
    )


def _load_json_object(raw_response: str) -> dict[str, object]:
    """Load a JSON object from provider response text.

    Purpose:
        Parse the provider response directly, or recover the substring between
        the first `{` and last `}` when extra text surrounds JSON.
    Important parameters:
        raw_response is the untrusted provider response string.
    Return value:
        Parsed JSON object or a fallback dict with empty findings, empty
        uncertain_risks, and an invalid-response note.
    Side effects:
        None.
    Failure or fallback behavior:
        JSONDecodeError triggers substring recovery; failed recovery returns the
        fallback invalid non-JSON response object.
    Trace:
        json.loads(), raw_response.find(), raw_response.rfind().
    """
    try:
        payload = json.loads(raw_response)
        if isinstance(payload, dict):
            return payload
        return _invalid_specialist_payload("Specialist returned non-object JSON.")
    except json.JSONDecodeError:
        start = raw_response.find("{")
        end = raw_response.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return _invalid_specialist_payload("Invalid non-JSON specialist response.")
        try:
            payload = json.loads(raw_response[start : end + 1])
            if isinstance(payload, dict):
                return payload
            return _invalid_specialist_payload("Specialist returned non-object JSON.")
        except json.JSONDecodeError:
            return _invalid_specialist_payload("Invalid non-JSON specialist response.")


def _invalid_specialist_payload(note: str) -> dict[str, object]:
    return {"findings": [], "uncertain_risks": [], "note": note}


def prompt_context_was_truncated(context: ReviewContext, files: tuple[ChangedFile, ...]) -> bool:
    """Report whether prompt metadata context would be truncated.

    Purpose:
        Let the coordinator decide whether to add a prompt-context truncation
        risk for a specialist input.
    Important parameters:
        context supplies commit truncation and commits; files supplies changed
        paths for the specialist.
    Return value:
        Boolean _PromptContextBlocks.truncated value.
    Side effects:
        None.
    Failure or fallback behavior:
        Uses the same limits as _build_prompt_context_blocks().
    Trace:
        _build_prompt_context_blocks(), MAX_PROMPT_FILES, MAX_PROMPT_COMMITS.
    """
    return _build_prompt_context_blocks(context, files).truncated


def _build_prompt_context_blocks(
    context: ReviewContext,
    files: tuple[ChangedFile, ...],
) -> _PromptContextBlocks:
    """Build bounded file-list and commit blocks for specialist prompts.

    Purpose:
        Convert changed paths and commit subjects into bullet blocks with
        omission notes when file or commit limits are exceeded.
    Important parameters:
        context supplies commits and commit_context_truncated; files supplies
        ChangedFile.path values.
    Return value:
        _PromptContextBlocks with file_list, commit_block, and truncated flag.
    Side effects:
        None.
    Failure or fallback behavior:
        Empty file or commit blocks become "- none"; truncated is true when
        context commit context was truncated, commit count exceeds
        MAX_PROMPT_COMMITS, or file count exceeds MAX_PROMPT_FILES.
    Trace:
        MAX_PROMPT_FILES, MAX_PROMPT_COMMITS, _bullet_block().
    """
    file_count = len(files)
    file_paths = [changed_file.path for changed_file in files[:MAX_PROMPT_FILES]]
    truncated = context.commit_context_truncated or len(context.commits) > MAX_PROMPT_COMMITS
    file_list = _bullet_block(
        file_paths,
        "... additional changed files omitted",
        file_count > MAX_PROMPT_FILES,
    )
    commit_block = _bullet_block(
        list(context.commits[:MAX_PROMPT_COMMITS]),
        "... additional commit subjects omitted",
        truncated,
    )
    return _PromptContextBlocks(
        file_list=file_list or "- none",
        commit_block=commit_block or "- none",
        truncated=truncated or file_count > MAX_PROMPT_FILES,
    )


def _bullet_block(items: list[str], overflow_note: str, truncated: bool) -> str:
    lines = [f"- {item}" for item in items]
    if truncated:
        lines.append(f"- {overflow_note}")
    return "\n".join(lines)


def _index_changed_paths(files: tuple[ChangedFile, ...]) -> dict[str, ChangedFile]:
    changed_paths: dict[str, ChangedFile] = {}
    for changed_file in files:
        for candidate in (changed_file.path, changed_file.old_path):
            normalized = _normalize_specialist_path(candidate)
            if normalized:
                changed_paths[normalized] = changed_file
    return changed_paths


def _lookup_changed_file(path: str, changed_paths: dict[str, ChangedFile]) -> ChangedFile | None:
    """Match a specialist-reported path to a changed file.

    Purpose:
        Normalize provider-reported file paths and reconcile direct, old-path,
        and unambiguous suffix matches to ChangedFile objects.
    Important parameters:
        path is a provider-reported file path; changed_paths maps normalized new
        and old paths to ChangedFile instances.
    Return value:
        Matching ChangedFile or None.
    Side effects:
        None.
    Failure or fallback behavior:
        Empty normalized paths return None; ambiguous suffix matches return None
        instead of guessing.
    Trace:
        _normalize_specialist_path(), _index_changed_paths(),
        ChangedFile.old_path.
    """
    normalized = _normalize_specialist_path(path)
    if not normalized:
        return None
    direct_match = changed_paths.get(normalized)
    if direct_match is not None:
        return direct_match

    suffix_match: ChangedFile | None = None
    for candidate, changed_file in changed_paths.items():
        if not (normalized.endswith(f"/{candidate}") or candidate.endswith(f"/{normalized}")):
            continue
        if suffix_match is None:
            suffix_match = changed_file
            continue
        if suffix_match.path != changed_file.path:
            return None
    return suffix_match


def _normalize_specialist_path(path: object) -> str:
    """Normalize a provider-reported path for matching.

    Purpose:
        Convert path-like provider output into a stable POSIX-style path key.
    Important parameters:
        path may be None or any object convertible to str.
    Return value:
        Normalized string or "" when no usable path remains.
    Side effects:
        None.
    Failure or fallback behavior:
        None, empty strings, and "." normalize to ""; leading "./" prefixes are
        removed; backslashes become slashes; surrounding backticks/quotes are
        stripped.
    Trace:
        PurePosixPath, _lookup_changed_file(), _index_changed_paths().
    """
    if path is None:
        return ""
    normalized = str(path).strip().strip("`'\"").replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized or normalized == ".":
        return ""
    return PurePosixPath(normalized).as_posix()
