"""Coordinator for agentic PR review."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import subprocess
from dataclasses import dataclass

from blokus.review.config import ReviewConfig
from blokus.review.diff import build_review_context, should_run_performance_review
from blokus.review.provider import OpenRouterClient, ProviderUnavailable
from blokus.review.renderer import render_review_markdown
from blokus.review.specialists import SpecialistRunner, prompt_context_was_truncated
from blokus.review.static_analyzer import StaticAnalysisReport, StaticAnalyzer
from blokus.review.types import ChangedFile, Finding, ReviewContext, ReviewPayload, ReviewResult, ReviewSummary, SpecialistResponse, UncertainRisk

ALLOWED_FINDING_CATEGORIES = {
    "correctness",
    "tests",
    "performance",
    "static-analysis",
    "requirements",
}
MAX_RENDERED_DIFF_CHARS = 120_000
MAX_RENDERED_PATCH_CHARS = 12_000
_RENDERED_PATCH_TRUNCATION_MARKER = "\n... [diff hunk truncated for scale]\n"
_RENDERED_BUNDLE_TRUNCATION_MARKER = "\n\n... [additional diff context truncated for scale]"


@dataclass(frozen=True)
class ReviewRun:
    """Final bundled review outputs."""

    context: ReviewContext
    result: ReviewResult
    markdown: str
    static_report: StaticAnalysisReport


@dataclass(frozen=True)
class _RenderedDiffBundle:
    text: str
    truncated: bool


@dataclass
class _RenderedBlockCache:
    blocks: dict[str, tuple[str, bool]]

    def __init__(self) -> None:
        self.blocks = {}

    def get(self, changed_file: ChangedFile) -> tuple[str, bool]:
        block = self.blocks.get(changed_file.path)
        if block is None:
            block = _render_patch_block(changed_file)
            self.blocks[changed_file.path] = block
        return block


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
        else:
            static_report = self.static_analyzer.analyze(context)
            findings = list(static_report.findings)
            uncertain_risks = list(static_report.uncertain_risks)
            performance_requested = should_run_performance_review(self.config, context)

        provider_available = False
        provider: OpenRouterClient | None = None
        provider_error: str | None = None
        diff_context_truncated = any(changed_file.patch_truncated for changed_file in context.changed_files)
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
            findings, uncertain_risks, rendered_diff_truncated = self._run_specialists(
                specialist_runner,
                context,
                findings,
                uncertain_risks,
                performance_requested,
            )
            diff_context_truncated = diff_context_truncated or rendered_diff_truncated

        if diff_context_truncated:
            _append_diff_truncation_risk(uncertain_risks)

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
    ) -> tuple[list[Finding], list[UncertainRisk], bool]:
        rendered_blocks = _RenderedBlockCache()
        all_changed_diff = (
            _RenderedDiffBundle(text=context.raw_diff, truncated=False)
            if context.raw_diff
            else _render_diff_bundle(context.changed_files, rendered_blocks)
        )
        executable_diff = (
            all_changed_diff
            if context.changed_files == context.executable_files
            else _render_diff_bundle(context.executable_files, rendered_blocks)
        )
        specialist_specs: list[tuple[str, tuple[ChangedFile, ...], str]] = [
            ("correctness", context.executable_files, executable_diff.text),
            ("tests", context.changed_files, all_changed_diff.text),
        ]
        if performance_requested:
            specialist_specs.append(("performance", context.executable_files, executable_diff.text))
        prompt_context_truncated = any(
            prompt_context_was_truncated(context, files)
            for _, files, _ in specialist_specs
        )

        futures_by_specialist: dict[str, Future[SpecialistResponse]] = {}
        with ThreadPoolExecutor(max_workers=len(specialist_specs)) as executor:
            for specialist, files, rendered_diff in specialist_specs:
                futures_by_specialist[specialist] = executor.submit(
                    self._run_specialist,
                    specialist,
                    specialist_runner,
                    context,
                    files,
                    rendered_diff,
                )

            # Merge results in a stable specialist order even though the provider
            # requests themselves run in parallel.
            for specialist, _, _ in specialist_specs:
                try:
                    response = futures_by_specialist[specialist].result()
                except Exception as exc:
                    response = _specialist_failure_response(specialist, exc)
                findings.extend(response.findings)
                uncertain_risks.extend(response.uncertain_risks)

        if prompt_context_truncated:
            _append_prompt_context_truncation_risk(uncertain_risks)

        return findings, uncertain_risks, all_changed_diff.truncated or executable_diff.truncated

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
        if any(_requires_discussion(risk) for risk in uncertain_risks):
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
            finding.category in ALLOWED_FINDING_CATEGORIES,
        ]
    )


def _render_diff_bundle(
    files: tuple[ChangedFile, ...],
    rendered_blocks: _RenderedBlockCache | None = None,
) -> _RenderedDiffBundle:
    blocks: list[str] = []
    total_length = 0
    truncated = False

    for changed_file in files:
        if rendered_blocks is None:
            block, block_truncated = _render_patch_block(changed_file)
        else:
            block, block_truncated = rendered_blocks.get(changed_file)
        if not block:
            continue
        separator = "\n\n" if blocks else ""
        candidate = f"{separator}{block}"
        if total_length + len(candidate) > MAX_RENDERED_DIFF_CHARS:
            truncated = True
            break
        blocks.append(candidate)
        total_length += len(candidate)
        truncated = truncated or block_truncated

    rendered = "".join(blocks)
    if truncated:
        available = MAX_RENDERED_DIFF_CHARS - len(rendered)
        marker = _truncate_text(_RENDERED_BUNDLE_TRUNCATION_MARKER, available, _RENDERED_BUNDLE_TRUNCATION_MARKER)
        rendered = f"{rendered}{marker}"
    return _RenderedDiffBundle(text=rendered, truncated=truncated)


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


def _render_patch_block(changed_file: ChangedFile) -> tuple[str, bool]:
    patch_body = changed_file.patch.strip()
    if not patch_body:
        return "", False

    prefix = f"File: {changed_file.path}\n```diff\n"
    suffix = "\n```"
    available_patch_chars = max(0, MAX_RENDERED_PATCH_CHARS - len(prefix) - len(suffix))
    rendered_patch = _truncate_text(
        patch_body,
        available_patch_chars,
        _RENDERED_PATCH_TRUNCATION_MARKER,
    )
    return f"{prefix}{rendered_patch}{suffix}", rendered_patch != patch_body


def _truncate_text(text: str, limit: int, marker: str) -> str:
    if limit <= 0:
        return ""
    if limit <= len(marker):
        return marker[:limit]
    if len(text) <= limit:
        return text
    available = max(0, limit - len(marker))
    trimmed = text[:available].rstrip("\n")
    return f"{trimmed}{marker}"


def _append_diff_truncation_risk(uncertain_risks: list[UncertainRisk]) -> None:
    risk = UncertainRisk(
        risk="Diff context was truncated for scale.",
        reason_uncertain="One or more stored patches or rendered specialist diff bundles exceeded the internal size limits, so omitted hunks may not have been reviewed in full.",
        suggested_verification="Manually inspect the full git diff for very large PRs, especially omitted hunks or files not fully included in the review prompt.",
    )
    if any(existing.risk == risk.risk for existing in uncertain_risks):
        return
    uncertain_risks.append(risk)


def _append_prompt_context_truncation_risk(uncertain_risks: list[UncertainRisk]) -> None:
    risk = UncertainRisk(
        risk="Commit or file-list context was truncated for scale.",
        reason_uncertain="The specialist prompts capped commit subjects or changed-path lists to stay within a bounded context window, so some metadata context was omitted.",
        suggested_verification="Inspect large PRs manually when commit history or changed-file breadth may materially affect the review.",
    )
    if any(existing.risk == risk.risk for existing in uncertain_risks):
        return
    uncertain_risks.append(risk)


_NON_BLOCKING_UNCERTAIN_RISKS = {
    "Dependency-related files changed in this PR.",
    "Diff context was truncated for scale.",
    "Commit or file-list context was truncated for scale.",
}


def _requires_discussion(risk: UncertainRisk) -> bool:
    if risk.risk in _NON_BLOCKING_UNCERTAIN_RISKS:
        return False
    if risk.risk.endswith("specialist could not complete this run.") and "OpenRouter" in risk.reason_uncertain:
        return False
    return True


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
