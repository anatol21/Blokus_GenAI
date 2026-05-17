#!/usr/bin/env python3
"""Execute one bounded autonomous repair attempt for a pull request.

This script is the command-line entry point for the autonomous repair workflow
after a CI failure has been classified. It reads workflow event inputs, checks
pull request labels and changed files through the GitHub helper client, applies
the bounded repair policy from :mod:`blokus.automation`, and records retry state
in a managed PR comment. Depending on the failure category and eligibility, it
may run deterministic lint repair commands, commit and push changes to the PR
branch, rerun failed CI jobs, or stop with labels that ask for human review.
"""

from __future__ import annotations

import os
import subprocess

from blokus.automation import (
    COMMENT_MARKERS,
    REPAIR_STATE_MARKER,
    parse_state_marker,
    render_state_marker,
    repair_allowed,
)

from gh_helpers import GitHubClient, load_event_payload


def _run(command: list[str]) -> None:
    """Run one local subprocess command and fail on a nonzero exit.

    Purpose:
        Centralize shell-out behavior for the deterministic repair commands used
        by this workflow.
    Important parameters:
        command is an argv-style command list passed directly to
        :func:`subprocess.run`.
    Return value:
        None.
    Side effects:
        Executes a subprocess in the current working directory.
    Failure or fallback behavior:
        :class:`subprocess.CalledProcessError` propagates because ``check=True``
        is used. There is no retry or command-specific fallback in this helper.
    Trace:
        Wraps ``subprocess.run(command, check=True)`` and is called by
        :func:`_commit_and_push` and the lint branch in :func:`main`.

    Warning:
        The command is executed locally as provided by the caller; maintainers
        should review every call site before adding commands that mutate files,
        install dependencies, or contact external services.
    """
    subprocess.run(command, check=True)


def _has_diff() -> bool:
    """Return whether the working tree contains changes after repair commands.

    Purpose:
        Decide whether the lint repair path should commit and push a patch or
        rerun failed CI jobs because no deterministic edit was produced.
    Important parameters:
        None.
    Return value:
        ``True`` when ``git status --short`` writes non-empty output; otherwise
        ``False``.
    Side effects:
        Runs ``git status --short`` with captured text output.
    Failure or fallback behavior:
        :class:`subprocess.CalledProcessError` propagates because ``check=True``
        is used. The caller does not attempt an alternate diff check.
    Trace:
        Uses :func:`subprocess.run` with ``["git", "status", "--short"]`` and
        feeds the result into the lint branch in :func:`main`.
    """
    result = subprocess.run(
        ["git", "status", "--short"],
        check=True,
        text=True,
        capture_output=True,
    )
    return bool(result.stdout.strip())


def _commit_and_push(branch_name: str, pull_number: int) -> str:
    """Commit all working-tree changes and push them to the PR branch.

    Purpose:
        Publish deterministic repair edits produced by the lint repair path.
    Important parameters:
        branch_name is used as the remote ref target in ``HEAD:{branch_name}``.
        pull_number is interpolated into the repair commit message.
    Return value:
        The action summary string ``"pushed bounded repair patch"`` for the PR
        comment body assembled by :func:`main`.
    Side effects:
        Configures the git author as ``github-actions[bot]``, stages every
        working-tree change with ``git add -A``, creates a commit, and pushes to
        ``origin``.
    Failure or fallback behavior:
        Any failing git command propagates :class:`subprocess.CalledProcessError`
        through :func:`_run`. The function does not inspect branch protection,
        remote permissions, or the contents of the staged patch.
    Trace:
        Calls :func:`_run` for ``git config``, ``git add -A``, ``git commit``,
        and ``git push origin HEAD:{branch_name}``.

    Warning:
        ``git add -A`` stages all working-tree changes visible to the script, so
        future repair commands must keep their write scope explicit before this
        function is called.
    """
    _run(["git", "config", "user.name", "github-actions[bot]"])
    _run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])
    _run(["git", "add", "-A"])
    _run(["git", "commit", "-m", f"Apply bounded repair for PR #{pull_number}"])
    _run(["git", "push", "origin", f"HEAD:{branch_name}"])
    return "pushed bounded repair patch"


def main() -> int:
    """Execute one bounded autonomous repair attempt.

    Purpose:
        Read workflow inputs, inspect pull request state, enforce
        :func:`blokus.automation.repair_allowed`, apply one repair or rerun
        action, update labels and comments, and persist retry state in the
        repair comment.
    Important parameters:
        Reads ``GITHUB_EVENT_PATH``, ``GITHUB_REPOSITORY``, and ``GITHUB_TOKEN``
        from :data:`os.environ`. The event payload is expected to contain
        ``inputs`` with ``pull_number``, ``head_branch``, ``ci_run_id``, and
        ``failure_category``.
    Return value:
        Returns ``0`` for handled code paths, including already-handled runs,
        disallowed repairs, reruns, and attempted lint repairs.
    Side effects:
        Calls GitHub APIs through :class:`gh_helpers.GitHubClient`; may mutate
        PR labels and comments, rerun failed jobs, run dependency installation,
        run Ruff autofix, and commit or push git changes.
    Failure or fallback behavior:
        A previously handled ``ci_run_id`` exits without action. Disallowed
        repairs remove ``repair-loop``, add ``agent-blocked`` and
        ``needs-review``, write a stopped comment, and return ``0``. Allowed
        non-lint categories rerun failed jobs within the retry budget, while
        lint repairs rerun failed jobs only when Ruff produces no local diff.
    Trace:
        Uses :func:`load_event_payload`, :func:`repair_allowed`,
        :func:`parse_state_marker`, :func:`render_state_marker`,
        :data:`COMMENT_MARKERS`, :data:`REPAIR_STATE_MARKER`,
        :class:`GitHubClient`, :func:`_run`, :func:`_has_diff`, and
        :func:`_commit_and_push`.

    Warning:
        Environment variables and event payload keys are accessed directly. A
        missing key raises before the script can write a repair comment.

    Warning:
        The lint path runs ``./scripts/install.sh``, installs ``ruff`` with pip,
        and executes ``ruff check --fix .`` across the repository; this code does
        not prove that resulting edits are limited to changed PR files.

    Warning:
        Retry state is recovered from managed issue comments using
        :func:`parse_state_marker` and then coerced with ``int``. A malformed or
        unexpected state payload can fail before label/comment fallback handling.

    Warning:
        GitHub token use is concentrated in :class:`GitHubClient`, which is
        constructed from ``GITHUB_REPOSITORY`` and ``GITHUB_TOKEN`` and then used
        for PR reads, label mutation, comment upserts, and failed-job reruns.
    """
    payload = load_event_payload(os.environ["GITHUB_EVENT_PATH"])
    inputs = payload["inputs"]
    pull_number = int(inputs["pull_number"])
    branch_name = inputs["head_branch"]
    run_id = int(inputs["ci_run_id"])
    category = inputs["failure_category"]

    client = GitHubClient(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    pull_request = client.get_pull_request(pull_number)
    labels = [label["name"] for label in pull_request["labels"]]
    changed_files = [item["filename"] for item in client.list_pr_files(pull_number)]

    state = {"attempts": 0, "handled_runs": []}
    for comment in reversed(client.list_issue_comments(pull_number)):
        parsed = parse_state_marker(REPAIR_STATE_MARKER, comment.get("body", ""))
        if parsed is not None:
            state = parsed
            break

    handled_runs = [int(item) for item in state.get("handled_runs", [])]
    if run_id in handled_runs:
        return 0

    retry_count = int(state.get("attempts", 0))
    allowed, reason = repair_allowed(branch_name, labels, category, changed_files, retry_count)
    next_state = {
        "attempts": retry_count,
        "handled_runs": handled_runs,
    }

    if not allowed:
        client.remove_label(pull_number, "repair-loop")
        client.add_labels(pull_number, ["agent-blocked", "needs-review"])
        body = "\n".join(
            [
                f"<!-- {COMMENT_MARKERS['repair']} -->",
                "## Autonomous Repair",
                "- Status: `stopped`",
                f"- Reason: {reason}",
                render_state_marker(REPAIR_STATE_MARKER, next_state),
            ]
        )
        client.upsert_issue_comment(pull_number, COMMENT_MARKERS["repair"], body)
        return 0

    next_state["attempts"] = retry_count + 1
    next_state["handled_runs"] = handled_runs + [run_id]

    if category == "lint":
        _run(["./scripts/install.sh"])
        _run([".venv/bin/python", "-m", "pip", "install", "ruff"])
        _run([".venv/bin/ruff", "check", "--fix", "."])
        if _has_diff():
            action_taken = _commit_and_push(branch_name, pull_number)
        else:
            client.rerun_failed_jobs(run_id)
            action_taken = "reran failed CI jobs after no deterministic lint fix applied"
    else:
        client.rerun_failed_jobs(run_id)
        action_taken = "reran failed CI jobs within the bounded retry budget"

    client.add_labels(pull_number, ["repair-loop"])
    client.remove_label(pull_number, "agent-blocked")

    body = "\n".join(
        [
            f"<!-- {COMMENT_MARKERS['repair']} -->",
            "## Autonomous Repair",
            "- Status: `attempted`",
            f"- Attempt: `{next_state['attempts']}/2`",
            f"- Failure category: `{category}`",
            f"- Action taken: {action_taken}",
            render_state_marker(REPAIR_STATE_MARKER, next_state),
        ]
    )
    client.upsert_issue_comment(pull_number, COMMENT_MARKERS["repair"], body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
