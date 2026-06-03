"""Minimal MCP client example for calling the local PDDL planner server."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call the local PDDL MCP server over stdio with a sample planning request.",
    )
    parser.add_argument(
        "--text",
        default=default_request(),
        help="Natural-language planning request to send to plan_from_text.",
    )
    return parser.parse_args()


def default_request() -> str:
    return (
        "A farmer must take a wolf, a goat, and a cabbage across a river. "
        "The boat must be driven by the farmer and can carry at most one item. "
        "If the farmer is absent, the wolf eats the goat and the goat eats the cabbage. "
        "Plan how to move everything safely to the other side."
    )


async def run_example(text: str) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(repo_root / "server.py")],
        env=None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:", ", ".join(tool.name for tool in tools.tools))

            result = await session.call_tool(
                "plan_from_text",
                arguments={
                    "text": text,
                    "options": {"task_id": "mcp-client-quickstart"},
                },
            )

    payload = getattr(result, "structured_content", None)
    if payload is None:
        payload = getattr(result, "structuredContent", None)
    if isinstance(payload, BaseModel):
        payload = payload.model_dump()
    if not isinstance(payload, dict):
        raise TypeError("Expected structured tool output from plan_from_text.")
    return payload


def print_summary(payload: dict[str, Any]) -> None:
    print("\nTool response fields:")
    for field in ("success", "plan_content", "artifacts", "warnings", "error"):
        print(f"- {field}: {json.dumps(payload.get(field), indent=2, ensure_ascii=False)}")

    print("\nNotes:")
    print("- `success` is true when the workflow produced a valid plan.")
    print("- `plan_content` contains the planner steps as newline-delimited text.")
    print("- `artifacts` points to generated files such as domain/problem PDDL and result metadata.")
    print("- `warnings` captures non-fatal runtime issues, such as optional planner configuration gaps.")
    print("- `error` contains the failure reason when planning does not succeed.")


def main() -> None:
    args = parse_args()
    payload = asyncio.run(run_example(args.text))
    print_summary(payload)


if __name__ == "__main__":
    main()
