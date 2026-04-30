"""Coordinator for agentic PR review."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from blokus.review.config import ReviewConfig
from blokus.review.diff import build_review_context, should_run_performance_review
from blokus.review.provider import OpenRouterClient, ProviderUnavailable
from blokus.review.renderer import render_review_markdown
from blokus.review.specialists import SpecialistRunner
from blokus.review.static_analyzer import StaticAnalysisReport, StaticAnalyzer
from blokus.review.types import ChangedFile, Finding, ReviewContext, ReviewPayload, ReviewResult, ReviewSummary, SpecialistResponse, UncertainRisk


@dataclass(frozen=True)
class ReviewRun:
    """Final bundled review outputs."""

    context: ReviewContext
    result: ReviewResult
    markdown: str
    static_report: StaticAnalysisReport


class ReviewCoordinator:
    """Run the end-to-end agentic PR review flow."""

    def __init__(self, config: ReviewConfig) -> None:
        self.config = config
        self.config.validate_provider()
        self.static_analyzer = StaticAnalyzer(config)

    def run(
        self,
        *,
        event_payload: dict[str, object] | None = None,
        base_ref: str | None = None,
        head_ref: str | None = None,
        pr_number: int | None = None,
    ) -> ReviewRun:
        try:
            context = build_review_context(
                self.config,
                event_payload=event_payload,
                base_ref=base_ref,
                head_ref=head_ref,
                pr_number=pr_number,
            )
            static_report = self.static_analyzer.analyze(context)
            findings = list(static_report.findings)
            uncertain_risks = list(static_report.uncertain_risks)
            performance_requested = should_run_performance_review(self.config, context)
        except (subprocess.CalledProcessError, KeyError, TypeError, ValueError) as exc:
            context = _fallback_review_context(event_payload, base_ref, head_ref, pr_number)
            static_report = StaticAnalysisReport(
                findings=(),
                uncertain_risks=(),
                commands=(),
                posture="not_run",
            )
            findings = []
            uncertain_risks = [
                UncertainRisk(
                    risk="Diff-based review was skipped because the requested refs were unavailable locally.",
                    reason_uncertain=str(exc),
                    suggested_verification="Fetch the missing refs or rerun the review in an environment with the required git history.",
                )
            ]
            performance_requested = False

        provider_available = False
        provider: OpenRouterClient | None = None
        provider_error: str | None = None
        if context.same_repo and context.changed_files:
            try:
                provider = OpenRouterClient.from_env(self.config)
                provider_available = True
            except ProviderUnavailable as exc:
                provider_error = str(exc)
                uncertain_risks.append(
                    UncertainRisk(
                        risk="OpenRouter review was unavailable for this run.",
                        reason_uncertain=provider_error,
                        suggested_verification="Restore the OpenRouter credential or rerun the review when the provider is available.",
                    )
                )
        elif not context.same_repo and context.changed_files:
            uncertain_risks.append(
                UncertainRisk(
                    risk="LLM review was skipped for a forked pull request.",
                    reason_uncertain="Same-repo review credentials are intentionally unavailable for forked `pull_request` runs.",
                    suggested_verification="Rerun the review on a trusted branch or perform a human review for the LLM-only parts.",
                )
            )

        if provider is not None and context.changed_files:
            specialist_runner = SpecialistRunner(self.config, provider)
            findings, uncertain_risks = self._run_specialists(
                specialist_runner,
                context,
                findings,
                uncertain_risks,
                performance_requested,
            )

        findings = self._dedupe_and_limit(findings)
        summary = self._build_summary(context, findings, static_report, performance_requested, provider_available)
        verdict = self._build_verdict(findings, uncertain_risks)
        result = ReviewResult(
            pr=context.pr,
            summary=summary,
            findings=tuple(findings),
            uncertain_risks=tuple(uncertain_risks),
            verdict=verdict,
        )
        markdown = render_review_markdown(
            result,
            context,
            static_report,
            marker="agentic-code-review",
        )
        return ReviewRun(context=context, result=result, markdown=markdown, static_report=static_report)

    def _run_specialists(
        self,
        specialist_runner: SpecialistRunner,
        context: ReviewContext,
        findings: list[Finding],
        uncertain_risks: list[UncertainRisk],
        performance_requested: bool,
    ) -> tuple[list[Finding], list[UncertainRisk]]:
        all_changed_diff = context.raw_diff or _render_diff_bundle(context.changed_files)
        executable_diff = (
            all_changed_diff
            if context.changed_files == context.executable_files
            else _render_diff_bundle(context.executable_files)
        )
        correctness = self._run_specialist(
            "correctness",
            specialist_runner,
            context,
            context.executable_files,
            executable_diff,
        )
        tests = self._run_specialist(
            "tests",
            specialist_runner,
            context,
            context.changed_files,
            all_changed_diff,
        )

        findings.extend(correctness.findings)
        findings.extend(tests.findings)
        uncertain_risks.extend(correctness.uncertain_risks)
        uncertain_risks.extend(tests.uncertain_risks)

        if performance_requested:
            performance = self._run_specialist(
                "performance",
                specialist_runner,
                context,
                context.executable_files,
                executable_diff,
            )
            findings.extend(performance.findings)
            uncertain_risks.extend(performance.uncertain_risks)

        return findings, uncertain_risks

    def _run_specialist(
        self,
        specialist: str,
        specialist_runner: SpecialistRunner,
        context: ReviewContext,
        files: tuple[ChangedFile, ...],
        rendered_diff: str,
    ) -> "SpecialistResponse":
        try:
            return specialist_runner.run(specialist, context, files, rendered_diff)
        except Exception as exc:
            return _specialist_failure_response(specialist, exc)

    def _dedupe_and_limit(self, findings: list[Finding]) -> list[Finding]:
        deduped: dict[tuple[str, str, int, str], Finding] = {}
        for finding in findings:
            if not _is_valid_finding(finding):
                continue
            key = finding.dedupe_key()
            current = deduped.get(key)
            if current is None or finding.rank() > current.rank():
                deduped[key] = finding

        ordered = sorted(
            deduped.values(),
            key=lambda finding: finding.rank(),
            reverse=True,
        )
        return ordered[: self.config.max_findings]

    def _build_summary(
        self,
        context: ReviewContext,
        findings: list[Finding],
        static_report: StaticAnalysisReport,
        performance_requested: bool,
        provider_available: bool,
    ) -> ReviewSummary:
        overall_risk = context.impact
        if findings:
            overall_risk = max(
                [context.impact, *[finding.severity for finding in findings]],
                key=lambda severity: {"low": 1, "moderate": 2, "high": 3, "critical": 4}[severity],
            )

        test_findings = [finding for finding in findings if finding.category == "tests"]
        if test_findings:
            test_posture = "weak" if any(finding.blocking_recommendation for finding in test_findings) else "partial"
        elif any(changed_file.path.startswith(("src/", "schemas/", "fixtures/")) for changed_file in context.changed_files):
            test_posture = "adequate"
        else:
            test_posture = "unknown"

        performance_findings = [finding for finding in findings if finding.category == "performance"]
        if performance_findings:
            performance_posture = "issues_found"
        elif performance_requested and provider_available:
            performance_posture = "clean"
        elif performance_requested:
            performance_posture = "review_recommended"
        else:
            performance_posture = "not_applicable"

        return ReviewSummary(
            overall_risk=overall_risk,
            test_posture=test_posture,
            static_analysis_posture=static_report.posture,
            performance_posture=performance_posture,
        )

    def _build_verdict(self, findings: list[Finding], uncertain_risks: list[UncertainRisk]) -> str:
        if any(finding.blocking_recommendation for finding in findings):
            return "NEEDS CHANGES"
        if uncertain_risks:
            return "DISCUSS"
        return "LGTM"


def _is_valid_finding(finding: Finding) -> bool:
    return all(
        [
            finding.title.strip(),
            finding.evidence.strip(),
            finding.impact.strip(),
            finding.suggested_action.strip(),
            finding.file.strip(),
            finding.line_start >= 1,
            finding.line_end >= finding.line_start,
            finding.severity in {"critical", "high", "moderate", "low"},
            finding.confidence in {"high", "medium", "low"},
        ]
    )


def _render_diff_bundle(files: tuple[ChangedFile, ...]) -> str:
    return "\n\n".join(
        f"File: {changed_file.path}\n```diff\n{changed_file.patch.strip()}\n```"
        for changed_file in files
        if changed_file.patch
    )


def _specialist_failure_response(specialist: str, error: Exception) -> "SpecialistResponse":
    return SpecialistResponse(
        findings=(),
        uncertain_risks=(
            UncertainRisk(
                risk=f"{specialist.title()} specialist could not complete this run.",
                reason_uncertain=str(error),
                suggested_verification="Rerun the review or inspect the specialist/provider output for malformed data.",
            ),
        ),
        note="",
    )


def _fallback_review_context(
    event_payload: dict[str, object] | None,
    base_ref: str | None,
    head_ref: str | None,
    pr_number: int | None,
) -> ReviewContext:
    payload = _fallback_payload(event_payload, base_ref, head_ref, pr_number)
    return ReviewContext(
        pr=payload,
        base_ref=payload.base_sha or base_ref or "origin/main",
        head_ref=payload.head_sha or head_ref or "HEAD",
        branch_name="unavailable",
        commits=(),
        changed_files=(),
        impact="moderate",
        bias_risks=(
            "self-declared-correctness-bias",
            "authority-bias",
            "reverse-authority-bias",
            "misleading-task-bias",
            "illusory-complexity-bias",
            "variable-change-bias",
        ),
        same_repo=_fallback_same_repo(event_payload),
        executable_files=(),
        raw_diff="",
    )


def _fallback_payload(
    event_payload: dict[str, object] | None,
    base_ref: str | None,
    head_ref: str | None,
    pr_number: int | None,
) -> ReviewPayload:
    pull_request = event_payload.get("pull_request") if isinstance(event_payload, dict) else None
    if not isinstance(pull_request, dict):
        return ReviewPayload(
            number=pr_number,
            head_sha=head_ref,
            base_sha=base_ref,
        )

    base_data = pull_request.get("base")
    head_data = pull_request.get("head")
    return ReviewPayload(
        number=_optional_int(pull_request.get("number"), pr_number),
        head_sha=_nested_sha(head_data) or head_ref,
        base_sha=_nested_sha(base_data) or base_ref,
    )


def _fallback_same_repo(event_payload: dict[str, object] | None) -> bool:
    pull_request = event_payload.get("pull_request") if isinstance(event_payload, dict) else None
    if not isinstance(pull_request, dict):
        return True
    base_full_name = _nested_full_name(pull_request.get("base"))
    head_full_name = _nested_full_name(pull_request.get("head"))
    if not base_full_name or not head_full_name:
        return True
    return head_full_name == base_full_name


def _nested_sha(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    sha = value.get("sha")
    return str(sha) if sha else None


def _nested_full_name(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    repo = value.get("repo")
    if not isinstance(repo, dict):
        return None
    full_name = repo.get("full_name")
    return str(full_name) if full_name else None


def _optional_int(value: object, default: int | None) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default
