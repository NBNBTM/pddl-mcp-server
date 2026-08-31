import json
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by Python 3.10 CI
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "4.0.1"
ACTION_REF = re.compile(r"uses:\s+([^@\s]+)@([^\s#]+)")


def test_release_version_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    mcp_config = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    server = (ROOT / "src/pddl_mcp/server.py").read_text(encoding="utf-8")
    pages = (ROOT / "docs/index.html").read_text(encoding="utf-8")

    assert project["project"]["version"] == EXPECTED_VERSION
    assert mcp_config["version"] == EXPECTED_VERSION
    assert server.count(f'"version": "{EXPECTED_VERSION}"') == 1
    assert f'version="{EXPECTED_VERSION}"' in server
    assert f"releases/tag/v{EXPECTED_VERSION}" in pages
    assert (ROOT / f"docs/releases/v{EXPECTED_VERSION}.md").is_file()


def test_actions_are_pinned_to_full_shas() -> None:
    workflow_paths = sorted((ROOT / ".github/workflows").glob("*.yml"))
    refs = []
    for path in workflow_paths:
        refs.extend(ACTION_REF.findall(path.read_text(encoding="utf-8")))

    assert refs
    assert all(re.fullmatch(r"[0-9a-f]{40}", ref) for _, ref in refs)
    assert {action for action, _ in refs} <= {
        "actions/checkout",
        "actions/setup-python",
        "github/codeql-action/init",
        "github/codeql-action/analyze",
    }


def test_ci_covers_supported_python_versions() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for version in ("3.10", "3.11", "3.12", "3.13", "3.14"):
        assert f'"{version}"' in workflow


def test_maintenance_files_exist() -> None:
    required = (
        ".github/CODEOWNERS",
        ".dockerignore",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "Dockerfile",
        "examples/mcp_client_quickstart.py",
    )
    assert all((ROOT / path).is_file() for path in required)


def test_dockerfile_embeds_a_pinned_planner_without_secrets() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.14-slim" in dockerfile
    assert re.search(r"ARG FAST_DOWNWARD_REF=[0-9a-f]{40}", dockerfile)
    assert "FAST_DOWNWARD_PATH=/opt/fast-downward/fast-downward.py" in dockerfile
    assert "COPY .env" not in dockerfile
    assert 'CMD ["python", "server.py"]' in dockerfile
