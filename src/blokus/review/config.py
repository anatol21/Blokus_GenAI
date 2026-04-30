"""Configuration loading for agentic review."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProviderConfig:
    """Provider runtime configuration."""

    name: str
    base_url: str
    timeout_seconds: int
    max_retries: int


@dataclass(frozen=True)
class PerformanceConfig:
    """Config for deciding when to invoke the performance reviewer."""

    path_markers: tuple[str, ...]
    diff_markers: tuple[str, ...]


@dataclass(frozen=True)
class HeuristicConfig:
    """Repository-aware heuristic configuration."""

    schema_test_paths: tuple[str, ...]
    fixture_test_paths: tuple[str, ...]
    cli_test_paths: tuple[str, ...]
    serialization_paths: tuple[str, ...]
    dependency_files: tuple[str, ...]


@dataclass(frozen=True)
class ReviewConfig:
    """Top-level configuration for agentic review."""

    repo_root: Path
    max_findings: int
    excluded_globs: tuple[str, ...]
    blocking_severities: tuple[str, ...]
    prompt_dir: Path
    spec_path: Path
    schema_path: Path
    provider: ProviderConfig
    performance: PerformanceConfig
    heuristics: HeuristicConfig
    models: dict[str, str]

    def model_for(self, specialist: str) -> str:
        override_map = {
            "correctness": os.environ.get("REVIEW_MODEL_CORRECTNESS"),
            "tests": os.environ.get("REVIEW_MODEL_TESTS"),
            "performance": os.environ.get("REVIEW_MODEL_PERFORMANCE"),
        }
        if override_map.get(specialist):
            return override_map[specialist] or ""
        default_override = os.environ.get("REVIEW_MODEL_DEFAULT")
        if default_override:
            return default_override
        return self.models.get(specialist, self.models["default"])

    def validate_provider(self) -> None:
        if self.provider.name != "openrouter":
            raise ValueError(
                f"Unsupported review provider `{self.provider.name}`. "
                "Only `openrouter` is implemented in v1."
            )


def load_review_config(path: str | Path | None = None, *, repo_root: str | Path | None = None) -> ReviewConfig:
    """Load agentic review configuration from TOML."""

    root = Path(repo_root or Path.cwd()).resolve()
    config_path = root / (Path(path) if path is not None else Path(".github/agentic-review.toml"))
    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))

    provider_block = raw["provider"]
    performance_block = raw["performance"]
    heuristics_block = raw["heuristics"]
    models_block = raw["models"]

    return ReviewConfig(
        repo_root=root,
        max_findings=int(raw["max_findings"]),
        excluded_globs=tuple(raw["excluded_globs"]),
        blocking_severities=tuple(raw["blocking_severities"]),
        prompt_dir=root / raw["prompt_dir"],
        spec_path=root / raw["spec_path"],
        schema_path=root / raw["schema_path"],
        provider=ProviderConfig(
            name=str(provider_block["name"]),
            base_url=str(provider_block["base_url"]),
            timeout_seconds=int(provider_block["timeout_seconds"]),
            max_retries=int(provider_block["max_retries"]),
        ),
        performance=PerformanceConfig(
            path_markers=tuple(performance_block["path_markers"]),
            diff_markers=tuple(performance_block["diff_markers"]),
        ),
        heuristics=HeuristicConfig(
            schema_test_paths=tuple(heuristics_block["schema_test_paths"]),
            fixture_test_paths=tuple(heuristics_block["fixture_test_paths"]),
            cli_test_paths=tuple(heuristics_block["cli_test_paths"]),
            serialization_paths=tuple(heuristics_block["serialization_paths"]),
            dependency_files=tuple(heuristics_block["dependency_files"]),
        ),
        models={str(key): str(value) for key, value in models_block.items()},
    )
