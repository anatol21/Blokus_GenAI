"""Markdown rendering for agentic review output."""

from __future__ import annotations

from blokus.review.static_analyzer import StaticAnalysisReport
from blokus.review.types import ReviewContext, ReviewResult

_MAX_RENDERED_TITLE_CHARS = 240
_MAX_RENDERED_FINDING_TEXT_CHARS = 1_500
_MAX_RENDERED_RISK_TEXT_CHARS = 1_000
_MAX_RENDERED_UNCERTAIN_RISKS = 10
_MAX_RENDERED_MARKDOWN_CHARS = 80_000
_TEXT_TRUNCATION_MARKER = "... [truncated for scale]"
_MARKDOWN_TRUNCATION_MARKER = "\n... [review markdown truncated for scale]\n"


def render_review_markdown(
    result: ReviewResult,
    context: ReviewContext,
    static_report: StaticAnalysisReport,
    *,
    marker: str,
) -> str:
    """Render the PR comment and artifact markdown."""

    changed_count = len(context.changed_files)
    files_fragment = ", ".join(f"`{changed_file.path}`" for changed_file in context.changed_files[:8]) or "`none`"
    if changed_count > 8:
        files_fragment += f", and `{changed_count - 8}` more"

    lines = [
        f"<!-- {marker} -->",
        "## Agentic Code Review",
        (
            f"This review covered `{changed_count}` changed non-excluded files between "
            f"`{context.base_ref}` and `{context.head_ref}`. "
            f"Overall risk is `{result.summary.overall_risk}` and the current verdict is `{result.verdict}`."
        ),
        (
            f"The main review posture is tests `{result.summary.test_posture}`, "
            f"static analysis `{result.summary.static_analysis_posture}`, "
            f"and performance `{result.summary.performance_posture}`."
        ),
        "",
        "### Changed paths",
        f"- {files_fragment}",
        f"- Branch context: `{context.branch_name}`",
        f"- Bias risks guarded against: {', '.join(f'`{risk}`' for risk in context.bias_risks)}",
        "",
        "### Findings",
    ]

    if result.findings:
        for finding in result.findings:
            lines.extend(
                [
                    (
                        f"- [{finding.severity.upper()}][{finding.category}] "
                        f"{_truncate_text(finding.title, _MAX_RENDERED_TITLE_CHARS)} "
                        f"(`{finding.file}:{finding.line_start}`)"
                    ),
                    f"  Confidence: `{finding.confidence}`. Blocking: `{str(finding.blocking_recommendation).lower()}`.",
                    f"  Evidence: {_truncate_text(finding.evidence, _MAX_RENDERED_FINDING_TEXT_CHARS)}",
                    f"  Impact: {_truncate_text(finding.impact, _MAX_RENDERED_FINDING_TEXT_CHARS)}",
                    f"  Suggested action: {_truncate_text(finding.suggested_action, _MAX_RENDERED_FINDING_TEXT_CHARS)}",
                ]
            )
    else:
        lines.append("- No material findings.")

    lines.extend(["", "### Static Analysis"])
    if static_report.commands:
        for command in static_report.commands:
            lines.append(f"- Ran `{command}`")
    elif static_report.posture == "not_run":
        lines.append("- Static analysis was not run for this review context.")
    else:
        lines.append("- Static analysis was not run because no executable files changed.")

    if result.uncertain_risks:
        lines.extend(["", "### Uncertain Risks"])
        for risk in result.uncertain_risks[:_MAX_RENDERED_UNCERTAIN_RISKS]:
            lines.extend(
                [
                    f"- {_truncate_text(risk.risk, _MAX_RENDERED_RISK_TEXT_CHARS)}",
                    f"  Why uncertain: {_truncate_text(risk.reason_uncertain, _MAX_RENDERED_RISK_TEXT_CHARS)}",
                    f"  Suggested verification: {_truncate_text(risk.suggested_verification, _MAX_RENDERED_RISK_TEXT_CHARS)}",
                ]
            )
        if len(result.uncertain_risks) > _MAX_RENDERED_UNCERTAIN_RISKS:
            omitted = len(result.uncertain_risks) - _MAX_RENDERED_UNCERTAIN_RISKS
            lines.append(f"- `{omitted}` additional uncertain risks were omitted for scale.")

    lines.extend(["", "### Verdict", f"- `{result.verdict}`"])
    rendered = "\n".join(lines) + "\n"
    if len(rendered) <= _MAX_RENDERED_MARKDOWN_CHARS:
        return rendered
    return _truncate_text(
        rendered.rstrip("\n"),
        _MAX_RENDERED_MARKDOWN_CHARS,
        marker=_MARKDOWN_TRUNCATION_MARKER,
    ).rstrip() + "\n"


def _truncate_text(value: str, max_chars: int, *, marker: str = _TEXT_TRUNCATION_MARKER) -> str:
    if max_chars <= 0:
        return ""
    if len(value) <= max_chars:
        return value
    if len(marker) >= max_chars:
        return marker[:max_chars]
    return f"{value[: max_chars - len(marker)].rstrip()}{marker}"
