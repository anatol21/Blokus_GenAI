"""Markdown rendering for agentic review output."""

from __future__ import annotations

from blokus.review.static_analyzer import StaticAnalysisReport
from blokus.review.types import ReviewContext, ReviewResult


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
                    f"- [{finding.severity.upper()}][{finding.category}] {finding.title} (`{finding.file}:{finding.line_start}`)",
                    f"  Confidence: `{finding.confidence}`. Blocking: `{str(finding.blocking_recommendation).lower()}`.",
                    f"  Evidence: {finding.evidence}",
                    f"  Impact: {finding.impact}",
                    f"  Suggested action: {finding.suggested_action}",
                ]
            )
    else:
        lines.append("- No material findings.")

    lines.extend(["", "### Static Analysis"])
    if static_report.commands:
        for command in static_report.commands:
            lines.append(f"- Ran `{command}`")
    else:
        lines.append("- Static analysis was not run because no executable files changed.")

    if result.uncertain_risks:
        lines.extend(["", "### Uncertain Risks"])
        for risk in result.uncertain_risks:
            lines.extend(
                [
                    f"- {risk.risk}",
                    f"  Why uncertain: {risk.reason_uncertain}",
                    f"  Suggested verification: {risk.suggested_verification}",
                ]
            )

    lines.extend(["", "### Verdict", f"- `{result.verdict}`"])
    return "\n".join(lines) + "\n"
