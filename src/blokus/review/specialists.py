"""Prompt-driven specialist review orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import cast

from blokus.review.config import ReviewConfig
from blokus.review.prompts import load_prompt
from blokus.review.provider import OpenRouterClient
from blokus.review.types import ChangedFile, Finding, ReviewContext, SpecialistResponse, UncertainRisk, stable_finding_id
from functools import cached_property

@dataclass(frozen=True)
class SpecialistRunner:
    """Invoke specialist prompts against the configured provider."""

    config: ReviewConfig
    provider: OpenRouterClient

    @cached_property
    def _common_prompt(self) -> str:
        return load_prompt(self.config, "review-common")

    @cached_property
    def _specialist_prompts(self) -> dict[str, str]:
        return {

            "correctness": load_prompt(self.config, "review-correctness"),

            "tests": load_prompt(self.config, "review-tests"),

            "performance": load_prompt(self.config, "review-performance"),

        }
    def run(
        self,
        specialist: str,
        context: ReviewContext,
        files: tuple[ChangedFile, ...],
        rendered_diff: str,
    ) -> SpecialistResponse:
        if not files:
            return SpecialistResponse(findings=(), note="No relevant files were available for this specialist.")

        #common_prompt = load_prompt(self.config, "review-common")
        #specialist_prompt = load_prompt(self.config, f"review-{specialist}")
        #system_prompt = f"{common_prompt}\n\n{specialist_prompt}"
        specialist_prompt = self._specialist_prompts.get(specialist)
        if specialist_prompt is None:
            specialist_prompt = load_prompt(self.config, f"review-{specialist}")

        system_prompt = f"{self._common_prompt}\n\n{specialist_prompt}"
        user_prompt = _build_user_prompt(specialist, context, files, rendered_diff)
        raw_response = self.provider.complete(
            model=self.config.model_for(specialist),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        return _parse_specialist_response(raw_response, specialist, files)


def _build_user_prompt(
    specialist: str,
    context: ReviewContext,
    files: tuple[ChangedFile, ...],
    rendered_diff: str,
) -> str:
    file_list = "\n".join(f"- {changed_file.path}" for changed_file in files)
    commit_block = "\n".join(f"- {commit}" for commit in context.commits) or "- none"
    bias_block = "\n".join(f"- {risk}" for risk in context.bias_risks)

    return f"""
Review the following files from the current diff against the base ref.

Files to review:
{file_list}

Context:
- Specialist: {specialist}
- Overall impact: {context.impact}
- Branch name: {context.branch_name}
- Commits:
{commit_block}
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
    changed_paths = {changed_file.path: changed_file for changed_file in files}
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
    for item in _dict_list(data.get("findings")):
        if not required_keys.issubset(item):
            continue
        path = str(item["file"])

        line_start = _int_value(item.get("line_start"))
        line_end = _int_value(item.get("line_end"))
        if line_start is None or line_end is None:
            continue
        changed_file = changed_paths.get(path)
        if changed_file is None:
            continue
        if changed_file.line_spans and not changed_file.touches_line(line_start):
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

    uncertain_risks: list[UncertainRisk] = []
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
