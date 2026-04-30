"""Prompt file loading for agentic review."""

from __future__ import annotations

from pathlib import Path

from blokus.review.config import ReviewConfig


def load_prompt(config: ReviewConfig, name: str) -> str:
    """Load one prompt asset by short name."""

    prompt_path = config.prompt_dir / f"{name}.md"
    return prompt_path.read_text(encoding="utf-8").strip()


def load_spec(config: ReviewConfig) -> str:
    """Load the canonical review spec."""

    return config.spec_path.read_text(encoding="utf-8").strip()


def relative_prompt_path(config: ReviewConfig, name: str) -> Path:
    """Return the resolved prompt path for tests or diagnostics."""

    return config.prompt_dir / f"{name}.md"
