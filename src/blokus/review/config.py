"""Configuration loading for agentic review."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore  # Python <3.11 fallback


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
            "correctness": _normalized_env_value("REVIEW_MODEL_CORRECTNESS"),
            "tests": _normalized_env_value("REVIEW_MODEL_TESTS"),
            "performance": _normalized_env_value("REVIEW_MODEL_PERFORMANCE"),
        }
        specialist_override = override_map.get(specialist, "")
        if specialist_override:
            return specialist_override
        default_override = _normalized_env_value("REVIEW_MODEL_DEFAULT")
        if default_override:
            return default_override
        specialist_model = self.models.get(specialist, "").strip()
        if specialist_model:
            return specialist_model
        default_model = self.models.get("default", "").strip()
        if default_model:
            return default_model
        raise ValueError("Review config must define a non-empty `models.default` value.")

    def validate_provider(self) -> None:
        if self.provider.name != "openrouter":
            raise ValueError(
                f"Unsupported review provider `{self.provider.name}`. "
                "Only `openrouter` is implemented in v1."
            )
        if self.provider.max_retries < 0:
            raise ValueError("Review provider `max_retries` must be greater than or equal to 0.")
        if self.provider.timeout_seconds <= 0:
            raise ValueError("Review provider `timeout_seconds` must be greater than 0.")
        if not self.provider.base_url or not self.provider.base_url.strip():
            raise ValueError("Review provider `base_url` must be non-empty.")
        if not self.provider.base_url.startswith(("http://", "https://")):
            raise ValueError("Review provider `base_url` must be a valid HTTP(S) URL.")
        if not self.models.get("default", "").strip():
            raise ValueError("Review config must define a non-empty `models.default` value.")


def load_review_config(path: str | Path | None = None, *, repo_root: str | Path | None = None) -> ReviewConfig:
    """Load agentic review configuration from TOML."""

    root = Path(repo_root or Path.cwd()).resolve()
    config_path = root / (Path(path) if path is not None else Path(".github/agentic-review.toml"))
    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"Agentic review config was not found at `{config_path}`.") from exc
    try:
        raw = tomllib.loads(raw_text)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Agentic review config at `{config_path}` is not valid TOML: {exc}") from exc

    try:
        provider_block = raw["provider"]
        performance_block = raw["performance"]
        heuristics_block = raw["heuristics"]
        models_block = raw["models"]

        config = ReviewConfig(
            repo_root=root,
            max_findings=int(raw["max_findings"]),
            excluded_globs=_coerce_str_list(raw["excluded_globs"], "excluded_globs", config_path),
            blocking_severities=_coerce_str_list(raw["blocking_severities"], "blocking_severities", config_path),
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
                path_markers=_coerce_str_list(performance_block["path_markers"], "performance.path_markers", config_path),
                diff_markers=_coerce_str_list(performance_block["diff_markers"], "performance.diff_markers", config_path),
            ),
            heuristics=HeuristicConfig(
                schema_test_paths=_coerce_str_list(heuristics_block["schema_test_paths"], "heuristics.schema_test_paths", config_path),
                fixture_test_paths=_coerce_str_list(heuristics_block["fixture_test_paths"], "heuristics.fixture_test_paths", config_path),
                cli_test_paths=_coerce_str_list(heuristics_block["cli_test_paths"], "heuristics.cli_test_paths", config_path),
                serialization_paths=_coerce_str_list(heuristics_block["serialization_paths"], "heuristics.serialization_paths", config_path),
                dependency_files=_coerce_str_list(heuristics_block["dependency_files"], "heuristics.dependency_files", config_path),
            ),
            models={str(key): str(value) for key, value in models_block.items()},
        )
    except KeyError as exc:
        raise ValueError(
            f"Agentic review config at `{config_path}` is missing required key `{exc.args[0]}`."
        ) from exc
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Agentic review config at `{config_path}` contains an invalid value: {exc}") from exc
    config.validate_provider()
    return config


def _normalized_env_value(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _coerce_str_list(value: object, field_name: str, config_path: Path) -> tuple[str, ...]:
    """Coerce a value to a tuple of strings.
    
    Handles lists of strings (normal case) and single strings (coerced to single-item list).
    Raises ValueError for invalid types.
    """
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if isinstance(value, str):
        import warnings
        warnings.warn(
            f"Config field `{field_name}` should be a list, not a string. "
            f"Coercing '{value}' to ['{value}'].",
            UserWarning,
            stacklevel=3,
        )
        return (value,)
    raise ValueError(
        f"Config field `{field_name}` must be a list of strings or a single string, "
        f"got {type(value).__name__}."
    )
