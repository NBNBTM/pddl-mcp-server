"""FastMCP entrypoint and tool functions."""

from __future__ import annotations

import platform
from typing import Any

from .config import load_settings, validate_runtime
from .workflow import generate_plan_response, plan_from_text_response


class _FallbackMCP:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def tool(self):
        def decorator(fn):
            return fn

        return decorator

    def run(self):
        raise RuntimeError("FastMCP is not installed. Install dependencies with `pip install -e .`.")


try:  # pragma: no cover - exercised when FastMCP is installed
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - local tests use the fallback
    FastMCP = _FallbackMCP


def _create_app():
    try:
        return FastMCP(
            "PDDL Planner",
            dependencies=["pddl-mcp"],
        )
    except TypeError:
        return FastMCP(
            title="PDDL Planner",
            description="MCP server for PDDL generation and Fast Downward planning.",
            version="4.0.0",
            dependencies=["pddl-mcp"],
        )


app = _create_app()


@app.tool()
def plan_from_text(text: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Plan from a natural-language task description."""
    return plan_from_text_response(text, options)


@app.tool()
def generate_plan(task: dict[str, Any]) -> dict[str, Any]:
    """Plan from a task dictionary or existing domain/problem PDDL paths."""
    return generate_plan_response(task)


@app.tool()
def validate_config() -> dict[str, Any]:
    """Validate runtime configuration and report missing optional components."""
    return validate_runtime()


@app.tool()
def get_system_info() -> dict[str, Any]:
    """Return server and runtime information."""
    settings = load_settings()
    return {
        "success": True,
        "server_info": {
            "name": "PDDL Planner",
            "version": "4.0.0",
            "framework": "FastMCP",
            "capabilities": ["plan_from_text", "generate_plan", "validate_config", "get_system_info"],
        },
        "system_info": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "project_root": str(settings.project_root),
            "output_dir": str(settings.output_dir),
        },
    }


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()
