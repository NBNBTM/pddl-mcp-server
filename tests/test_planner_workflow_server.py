from pathlib import Path

from pddl_mcp.config import load_settings
from pddl_mcp.models import PlannerResult
from pddl_mcp.planner import FastDownwardPlanner, parse_plan_from_output
from pddl_mcp.workflow import PlanningWorkflow, generate_plan_response, plan_from_text_response


def test_parse_plan_from_output():
    output = "Solution found\n(move r1 room1 room2)\n; cost = 1\n"
    assert parse_plan_from_output(output) == ["(move r1 room1 room2)"]


def test_build_command_for_python_script(monkeypatch):
    monkeypatch.setenv("PDDL_MCP_DISABLE_DOTENV", "1")
    monkeypatch.setenv("FAST_DOWNWARD_PATH", "/tmp/downward/fast-downward.py")
    settings = load_settings()
    command = FastDownwardPlanner(settings).build_command(Path("domain.pddl"), Path("problem.pddl"))

    assert command[0].endswith("python") or "python" in command[0]
    assert command[1] == "/tmp/downward/fast-downward.py"
    assert "--search" in command


def test_generate_plan_without_planner_returns_standard_shape(monkeypatch, tmp_path):
    monkeypatch.setenv("PDDL_MCP_DISABLE_DOTENV", "1")
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    monkeypatch.delenv("FAST_DOWNWARD_PATH", raising=False)
    result = plan_from_text_response("Move robot r1 from room1 to room3")

    assert result["success"] is False
    assert set(["success", "task_id", "plan_content", "explanation", "artifacts", "workflow_steps", "warnings", "error"]).issubset(result)
    assert result["artifacts"]["domain_path"].endswith("domain.pddl")
    assert "FAST_DOWNWARD_PATH" in result["error"]


def test_workflow_success_with_mocked_planner(monkeypatch, tmp_path):
    monkeypatch.setenv("PDDL_MCP_DISABLE_DOTENV", "1")
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    monkeypatch.delenv("FAST_DOWNWARD_PATH", raising=False)

    def fake_plan(self, domain_path, problem_path, work_dir):
        return PlannerResult(
            success=True,
            plan=["(move r1 room1 room3)"],
            plan_path=work_dir / "sas_plan",
            log_path=work_dir / "planner.log",
        )

    monkeypatch.setattr("pddl_mcp.planner.FastDownwardPlanner.plan", fake_plan)
    result = PlanningWorkflow().run_from_text("Move robot r1 from room1 to room3").to_dict()

    assert result["success"] is True
    assert result["plan_content"] == "(move r1 room1 room3)"
    assert result["workflow_steps"][-1]["name"] == "validation"


def test_generate_plan_accepts_description(monkeypatch, tmp_path):
    monkeypatch.setenv("PDDL_MCP_DISABLE_DOTENV", "1")
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))

    def fake_plan(self, domain_path, problem_path, work_dir):
        return PlannerResult(success=True, plan=["(move r1 room1 room3)"])

    monkeypatch.setattr("pddl_mcp.planner.FastDownwardPlanner.plan", fake_plan)
    result = generate_plan_response({"description": "Move robot r1 from room1 to room3"})

    assert result["success"] is True
    assert result["plan_content"] == "(move r1 room1 room3)"
