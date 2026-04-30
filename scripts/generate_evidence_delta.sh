#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <output-path> <test-log-path> <evaluate-log-path>" >&2
  exit 1
fi

OUTPUT_PATH="$1"
TEST_LOG_PATH="$2"
EVALUATE_LOG_PATH="$3"

if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
else
  export PYTHONPATH=src
fi

export OUTPUT_PATH TEST_LOG_PATH EVALUATE_LOG_PATH

python - <<'PY'
from __future__ import annotations

import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from blokus.release import classify_release_areas, extract_bullets_under_heading


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


output_path = Path(os.environ["OUTPUT_PATH"])
test_log_path = Path(os.environ["TEST_LOG_PATH"])
evaluate_log_path = Path(os.environ["EVALUATE_LOG_PATH"])

try:
    base_tag = git("describe", "--tags", "--abbrev=0", "--match", "v*", "HEAD^")
except subprocess.CalledProcessError:
    base_tag = ""

if base_tag:
    compare_range = f"{base_tag}..HEAD"
    changed_paths = git("diff", "--name-only", compare_range).splitlines()
    log_lines = git("log", "--pretty=%H%x09%s", compare_range).splitlines()
else:
    compare_range = "initial release candidate"
    changed_paths = git("ls-tree", "-r", "--name-only", "HEAD").splitlines()
    log_lines = git("log", "--pretty=%H%x09%s", "HEAD").splitlines()

ignored_prefixes = (".idea/", "artifacts/", "dist/", ".venv/")
changed_paths = [
    path for path in changed_paths
    if path and not path.startswith(ignored_prefixes) and "__pycache__" not in path
]

areas = classify_release_areas(changed_paths)
seen_prs: set[str] = set()
merged_prs: list[tuple[str, str]] = []
for line in log_lines:
    if "\t" not in line:
        continue
    _, subject = line.split("\t", 1)
    for pr_number in re.findall(r"#(\d+)", subject):
        if pr_number not in seen_prs:
            seen_prs.add(pr_number)
            merged_prs.append((pr_number, subject))


def last_non_empty_line(path: Path) -> str:
    if not path.exists():
        return "Log not available."
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines[-1] if lines else "Log was empty."


requirements_text = Path("docs/requirements.md").read_text(encoding="utf-8")
open_risks = extract_bullets_under_heading(requirements_text, "Open risks and open issues")

body_lines = [
    "# Evidence Delta",
    "",
    f"- Generated at: `{datetime.now(UTC).isoformat()}`",
    f"- Commit: `{git('rev-parse', 'HEAD')}`",
    f"- Comparison base: `{base_tag or 'none'}`",
    f"- Comparison range: `{compare_range}`",
    f"- Changed areas: {', '.join(f'`{area}`' for area in areas) or '`none detected`'}",
    f"- Test summary: `{last_non_empty_line(test_log_path)}`",
    f"- Evaluation summary: `{last_non_empty_line(evaluate_log_path)}`",
    "",
    "## Merged PRs since the comparison base",
]

if merged_prs:
    body_lines.extend(f"- PR #{number}: {subject}" for number, subject in merged_prs)
else:
    body_lines.append("- No PR numbers were detected in commit subjects for this range.")

body_lines.extend(["", "## Changed files by area"])
if changed_paths:
    preview = changed_paths[:20]
    body_lines.extend(f"- `{path}`" for path in preview)
    if len(changed_paths) > len(preview):
        body_lines.append(f"- ...and `{len(changed_paths) - len(preview)}` more")
else:
    body_lines.append("- No changed files detected.")

body_lines.extend(["", "## Open risks carried into this candidate"])
if open_risks:
    body_lines.extend(f"- {risk}" for risk in open_risks)
else:
    body_lines.append("- No open risks were extracted from `docs/requirements.md`.")

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text("\n".join(body_lines) + "\n", encoding="utf-8")
PY
