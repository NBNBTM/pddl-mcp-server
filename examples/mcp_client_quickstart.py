"""Call the local PDDL MCP server over stdio."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def default_request() -> str:
    return (
        "A farmer must take a wolf, a goat, and a cabbage across a river. "
        "The boat must be driven by the farmer and can carry at most one item. "
        "If the farmer is absent, the wolf eats the goat and the goat eats the cabbage. "
        "Plan how to move everything safely to the other side."
    )


def _structured_payload(result: Any) -> dict[str, Any]:
    payload = getattr(result, "structuredContent", None)
    if payload is None:
        payload = getattr(result, "structured_content", None)
    if payload is None and isinstance(result, dict):
        payload = result.get("structuredContent") or result.get("structured_content")
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    if not isinstance(payload, dict):
        raise TypeError("Expected structured tool output from the MCP server.")
    return payload


async def run_example(text: str) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(repo_root / "server.py")],
        cwd=str(repo_root),
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Available tools:", ", ".join(tool.name for tool in tools.tools))

            system_result = await session.call_tool("get_system_info", arguments={})
            print("System info:")
            print(json.dumps(_structured_payload(system_result), indent=2, ensure_ascii=False))

            plan_result = await session.call_tool(
                "plan_from_text",
                arguments={
                    "text": text,
                    "options": {"task_id": "mcp-client-quickstart"},
                },
            )

    return _structured_payload(plan_result)


def print_summary(payload: dict[str, Any]) -> None:
    print("\nPlanning result:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--text",
        default=default_request(),
        help="Natural-language request passed to plan_from_text.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print_summary(asyncio.run(run_example(args.text)))


if __name__ == "__main__":
    main()
