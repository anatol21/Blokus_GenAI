"""Shared types for agentic PR review."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


SEVERITY_ORDER = {
    "critical": 4,
    "high": 3,
    "moderate": 2,
    "low": 1,
}

CONFIDENCE_ORDER = {
    "high": 3,
    "medium": 2,
    "low": 1,
}


@dataclass(frozen=True)
class LineSpan:
    """A changed line span in the post-change file."""

    start: int
    end: int

    def contains(self, line_number: int) -> bool:
        return self.start <= line_number <= self.end


@dataclass(frozen=True)
class ChangedFile:
    """One changed file in the review diff."""

    path: str
    status: str
    patch: str
    line_spans: tuple[LineSpan, ...]
    executable: bool
    categories: tuple[str, ...]
    old_path: str | None = None
    performance_sensitive: bool = False
    patch_truncated: bool = False

    def touches_line(self, line_number: int) -> bool:
        return any(span.contains(line_number) for span in self.line_spans)


@dataclass(frozen=True)
class ReviewPayload:
    """Metadata serialized under the JSON review payload."""

    number: int | None
    head_sha: str | None
    base_sha: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "head_sha": self.head_sha,
            "base_sha": self.base_sha,
        }


@dataclass(frozen=True)
class Finding:
    """One normalized review finding."""

    id: str
    title: str
    severity: str
    confidence: str
    category: str
    file: str
    line_start: int
    line_end: int
    evidence: str
    impact: str
    suggested_action: str
    blocking_recommendation: bool
    source: str = "coordinator"

    def rank(self) -> tuple[int, int, int]:
        return (
            1 if self.blocking_recommendation else 0,
            SEVERITY_ORDER.get(self.severity, 0),
            CONFIDENCE_ORDER.get(self.confidence, 0),
        )

    def dedupe_key(self) -> tuple[str, str, int, str]:
        return (
            self.category,
            self.file,
            self.line_start,
            self.title.strip().lower(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "confidence": self.confidence,
            "category": self.category,
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "evidence": self.evidence,
            "impact": self.impact,
            "suggested_action": self.suggested_action,
            "blocking_recommendation": self.blocking_recommendation,
        }


@dataclass(frozen=True)
class UncertainRisk:
    """A risk the coordinator could not verify conclusively."""

    risk: str
    reason_uncertain: str
    suggested_verification: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk": self.risk,
            "reason_uncertain": self.reason_uncertain,
            "suggested_verification": self.suggested_verification,
        }


@dataclass(frozen=True)
class ReviewSummary:
    """Top-level review posture summary."""

    overall_risk: str
    test_posture: str
    static_analysis_posture: str
    performance_posture: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_risk": self.overall_risk,
            "test_posture": self.test_posture,
            "static_analysis_posture": self.static_analysis_posture,
            "performance_posture": self.performance_posture,
        }


@dataclass(frozen=True)
class ReviewResult:
    """Final review output plus the computed verdict."""

    pr: ReviewPayload
    summary: ReviewSummary
    findings: tuple[Finding, ...]
    uncertain_risks: tuple[UncertainRisk, ...]
    verdict: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pr": self.pr.to_dict(),
            "summary": self.summary.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
            "uncertain_risks": [risk.to_dict() for risk in self.uncertain_risks],
        }


@dataclass(frozen=True)
class ReviewContext:
    """Collected review inputs for one PR or branch diff."""

    pr: ReviewPayload
    base_ref: str
    head_ref: str
    branch_name: str
    commits: tuple[str, ...]
    changed_files: tuple[ChangedFile, ...]
    impact: str
    bias_risks: tuple[str, ...]
    same_repo: bool
    executable_files: tuple[ChangedFile, ...] = field(default_factory=tuple)
    raw_diff: str = ""


@dataclass(frozen=True)
class SpecialistResponse:
    """Structured result from one specialist reviewer."""

    findings: tuple[Finding, ...]
    uncertain_risks: tuple[UncertainRisk, ...] = field(default_factory=tuple)
    note: str = ""


def stable_finding_id(*parts: object) -> str:
    """Build a stable short identifier for one finding."""

    digest = hashlib.sha1("::".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    return digest[:12]
