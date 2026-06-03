"""Configuration loading for the PDDL MCP server."""

from __future__ import annotations

import os
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _path_from_env(key: str, default: str, root: Path) -> Path:
    value = _env(key, default)
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    output_dir: Path
    fast_downward_path: str
    search: str
    max_planning_time: int
    log_level: str
    llm_api_url: str
    llm_api_key: str
    llm_model: str
    llm_timeout: int
    llm_retries: int

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_url and self.llm_api_key)

    @property
    def fast_downward_configured(self) -> bool:
        return bool(self.fast_downward_path)


def load_settings() -> Settings:
    root = _project_root()
    if load_dotenv and os.environ.get("PDDL_MCP_DISABLE_DOTENV") != "1":
        load_dotenv(root / ".env")

    llm_key = _env("LLM_API_KEY") or _env("LLM_API_TOKEN")
    timeout_raw = _env("MAX_PLANNING_TIME", "300")
    try:
        timeout = int(timeout_raw)
    except ValueError:
        timeout = 300
    llm_timeout_raw = _env("LLM_TIMEOUT", "30")
    try:
        llm_timeout = int(llm_timeout_raw)
    except ValueError:
        llm_timeout = 30
    llm_retries_raw = _env("LLM_RETRIES", "1")
    try:
        llm_retries = int(llm_retries_raw)
    except ValueError:
        llm_retries = 1

    return Settings(
        project_root=root,
        output_dir=_path_from_env("OUTPUT_DIR", "output", root),
        fast_downward_path=_env("FAST_DOWNWARD_PATH", ""),
        search=_env("FAST_DOWNWARD_SEARCH", "astar(blind())"),
        max_planning_time=timeout,
        log_level=_env("LOG_LEVEL", "INFO"),
        llm_api_url=_env("LLM_API_URL", ""),
        llm_api_key=llm_key,
        llm_model=_env("LLM_MODEL", "gpt-4o-mini"),
        llm_timeout=llm_timeout,
        llm_retries=max(0, llm_retries),
    )


def ensure_output_dirs(settings: Settings) -> dict[str, Path]:
    paths = {
        "output": settings.output_dir,
        "domains": settings.output_dir / "domains",
        "problems": settings.output_dir / "problems",
        "plans": settings.output_dir / "plans",
        "logs": settings.output_dir / "logs",
        "results": settings.output_dir / "results",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def validate_runtime(settings: Settings | None = None) -> dict[str, object]:
    settings = settings or load_settings()
    fd_path = settings.fast_downward_path
    fd_exists = False
    fd_resolved = ""
    if fd_path:
        expanded_path = Path(fd_path).expanduser()
        if expanded_path.exists():
            fd_exists = True
            fd_resolved = str(expanded_path)
        else:
            first_token = shlex.split(fd_path)[0]
            resolved = shutil.which(first_token)
            if resolved:
                fd_exists = True
                fd_resolved = resolved

    return {
        "success": True,
        "config": {
            "project_root": str(settings.project_root),
            "output_dir": str(settings.output_dir),
            "fast_downward_path": fd_path,
            "fast_downward_configured": settings.fast_downward_configured,
            "fast_downward_exists": fd_exists,
            "fast_downward_resolved": fd_resolved,
            "llm_configured": settings.llm_configured,
            "llm_api_url": settings.llm_api_url,
            "llm_model": settings.llm_model,
            "llm_timeout": settings.llm_timeout,
            "llm_retries": settings.llm_retries,
            "max_planning_time": settings.max_planning_time,
            "log_level": settings.log_level,
        },
        "warnings": _validation_warnings(settings, fd_exists),
    }


def _validation_warnings(settings: Settings, fd_exists: bool) -> list[str]:
    warnings: list[str] = []
    if not settings.fast_downward_configured:
        warnings.append("FAST_DOWNWARD_PATH is not set; generated PDDL will be saved but planning cannot run.")
    elif not fd_exists:
        warnings.append("FAST_DOWNWARD_PATH is set but the executable/script was not found from this environment.")
    if not settings.llm_configured:
        warnings.append("LLM configuration is missing; deterministic semantic fallback will be used.")
    return warnings
