"""Prompt-driven specialist review orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import PurePosixPath
from typing import cast

from blokus.review.config import ReviewConfig
from blokus.review.prompts import load_prompt
from blokus.review.provider import OpenRouterClient
from blokus.review.types import ChangedFile, Finding, ReviewContext, SpecialistResponse, UncertainRisk, stable_finding_id

MAX_PROMPT_FILES = 80
MAX_PROMPT_COMMITS = 25


@dataclass(frozen=True)
class _PromptContextBlocks:
    file_list: str
    commit_block: str
    truncated: bool


@dataclass(frozen=True)
class SpecialistRunner:
    """Invoke specialist prompts against the configured provider."""

    config: ReviewConfig
    provider: OpenRouterClient
    _specialist_prompt_cache: dict[str, str] = field(default_factory=dict, init=False, repr=False, compare=False)

    @cached_property
    def _common_prompt(self) -> str:
        return load_prompt(self.config, "review-common")

    def run(
        self,
        specialist: str,
        context: ReviewContext,
        files: tuple[ChangedFile, ...],
        rendered_diff: str,
    ) -> SpecialistResponse:
        if not files:
            return SpecialistResponse(findings=(), note="No relevant files were available for this specialist.")

        try:
            system_prompt = f"{self._common_prompt}\n\n{self._specialist_prompt(specialist)}"
        except FileNotFoundError:
            return SpecialistResponse(
                findings=(),
                uncertain_risks=(
                    UncertainRisk(
                        risk="A specialist prompt asset was unavailable.",
                        reason_uncertain=f"The `{specialist}` specialist prompt could not be loaded from the configured prompt directory.",
                        suggested_verification=f"Restore `.github/prompts/review-{specialist}.md` or update the configured prompt path before rerunning the review.",
                    ),
                ),
                note=f"Prompt asset missing for specialist `{specialist}`.",
            )
        user_prompt = _build_user_prompt(specialist, context, files, rendered_diff)
        raw_response = self.provider.complete(
            model=self.config.model_for(specialist),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        return _parse_specialist_response(raw_response, specialist, files)

    def _specialist_prompt(self, specialist: str) -> str:
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
    for item in _dict_list(data.get("findings")):
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
        if changed_file.line_spans and not changed_file.touches_span(line_start, line_end):
            continue

        findings.append(
            Finding(
                id=str(item.get("id") or stable_finding_id(specialist, path, line_start, item.get("title", ""))),
                title=str(item["title"]),
                severity=str(item["severity"]),
                confidence=str(item["confidence"]),
                category=str(item["category"]),
                file=path,
                line_start=line_start,
                line_end=line_end,
                evidence=str(item["evidence"]),
                impact=str(item["impact"]),
                suggested_action=str(item["suggested_action"]),
                blocking_recommendation=bool(item["blocking_recommendation"]),
                source=specialist,
            )
        )

    for unmatched_path in sorted(unmatched_paths):
        uncertain_risks.append(
            UncertainRisk(
                risk="Specialist findings were discarded because their file path did not match the current diff.",
                reason_uncertain=f"The specialist referenced `{unmatched_path}`, which could not be reconciled to a changed file path or rename target.",
                suggested_verification="Inspect the specialist output and normalize the referenced path if the finding should apply to a changed file.",
            )
        )

    for item in _dict_list(data.get("uncertain_risks")):
        if not all(key in item for key in ("risk", "reason_uncertain", "suggested_verification")):
            continue
        uncertain_risks.append(
            UncertainRisk(
                risk=str(item["risk"]),
                reason_uncertain=str(item["reason_uncertain"]),
                suggested_verification=str(item["suggested_verification"]),
            )
        )

    return SpecialistResponse(
        findings=tuple(findings[:3]),
        uncertain_risks=tuple(uncertain_risks),
        note=str(data.get("note", "")),
    )


def _dict_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [cast(dict[str, object], item) for item in value if isinstance(item, dict)]


def _int_value(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _load_json_object(raw_response: str) -> dict[str, object]:
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        start = raw_response.find("{")
        end = raw_response.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {"findings": [], "uncertain_risks": [], "note": "Invalid non-JSON specialist response."}
        try:
            return json.loads(raw_response[start : end + 1])
        except json.JSONDecodeError:
            return {"findings": [], "uncertain_risks": [], "note": "Invalid non-JSON specialist response."}


def prompt_context_was_truncated(context: ReviewContext, files: tuple[ChangedFile, ...]) -> bool:
    return _build_prompt_context_blocks(context, files).truncated


def _build_prompt_context_blocks(
    context: ReviewContext,
    files: tuple[ChangedFile, ...],
) -> _PromptContextBlocks:
    file_paths = [changed_file.path for changed_file in files]
    truncated = context.commit_context_truncated or len(context.commits) > MAX_PROMPT_COMMITS
    file_list = _bullet_block(
        file_paths[:MAX_PROMPT_FILES],
        "... additional changed files omitted",
        len(file_paths) > MAX_PROMPT_FILES,
    )
    commit_block = _bullet_block(
        list(context.commits[:MAX_PROMPT_COMMITS]),
        "... additional commit subjects omitted",
        truncated,
    )
    return _PromptContextBlocks(
        file_list=file_list or "- none",
        commit_block=commit_block or "- none",
        truncated=truncated or len(file_paths) > MAX_PROMPT_FILES,
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
    if path is None:
        return ""
    normalized = str(path).strip().strip("`'\"").replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized or normalized == ".":
        return ""
    return PurePosixPath(normalized).as_posix()
