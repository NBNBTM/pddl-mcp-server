from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mcp_quickstart_avoids_transitive_dependencies() -> None:
    source = (ROOT / "examples/mcp_client_quickstart.py").read_text(encoding="utf-8")
    assert "from pydantic" not in source
    assert "ClientSession" in source
    assert "plan_from_text" in source
