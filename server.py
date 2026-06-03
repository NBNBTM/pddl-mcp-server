#!/usr/bin/env python3
"""Compatibility entrypoint for MCP clients."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pddl_mcp.server import app, generate_plan, get_system_info, main, plan_from_text, validate_config  # noqa: E402

__all__ = ["app", "generate_plan", "get_system_info", "main", "plan_from_text", "validate_config"]


if __name__ == "__main__":
    main()
