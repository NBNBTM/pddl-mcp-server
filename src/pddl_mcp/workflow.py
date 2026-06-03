"""End-to-end planning workflow."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import ensure_output_dirs, load_settings
from .knowledge import KnowledgeMatcher, template_to_dict
from .modeling import PDDLModeler
from .models import PDDLModel, PlannerResult, PlanningArtifacts, PlanningResponse, WorkflowStep
from .planner import FastDownwardPlanner
from .semantic import SemanticProcessor
from .validation import PlanValidator


def plan_from_text_response(text: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
    return PlanningWorkflow().run_from_text(text, options or {}).to_dict()


def generate_plan_response(task: dict[str, Any]) -> dict[str, Any]:
    return PlanningWorkflow().run_task(task).to_dict()


class PlanningWorkflow:
    def __init__(self):
        self.settings = load_settings()
        self.paths = ensure_output_dirs(self.settings)
        self.semantic_processor = SemanticProcessor(self.settings)
        self.matcher = KnowledgeMatcher()
        self.modeler = PDDLModeler()
        self.planner = FastDownwardPlanner(self.settings)
        self.validator = PlanValidator()

    def run_task(self, task: dict[str, Any]) -> PlanningResponse:
        if not isinstance(task, dict):
            return PlanningResponse(False, _task_id(), error="Task must be a dictionary.")
        if task.get("domain_path") and task.get("problem_path"):
            return self.run_existing_pddl(Path(task["domain_path"]), Path(task["problem_path"]), task)
        description = str(task.get("description") or task.get("text") or "").strip()
        if not description:
            description = _description_from_structured_task(task)
        if not description:
            return PlanningResponse(False, str(task.get("task_id") or _task_id()), error="Task requires domain_path/problem_path or description.")
        return self.run_from_text(description, task)

    def run_from_text(self, text: str, options: dict[str, Any] | None = None) -> PlanningResponse:
        options = options or {}
        task_id = str(options.get("task_id") or _task_id())
        artifacts = PlanningArtifacts()
        steps: list[WorkflowStep] = []
        warnings: list[str] = []
        if not text or not isinstance(text, str):
            return PlanningResponse(False, task_id, artifacts=artifacts, error="Text input is required.")

        try:
            semantic, step_warnings = self._timed("semantic", steps, lambda: self.semantic_processor.process(text))
            warnings.extend(step_warnings)
            template, match_warnings = self._timed("knowledge", steps, lambda: self.matcher.match(semantic))
            warnings.extend(match_warnings)
            model = self._timed("modeling", steps, lambda: self.modeler.generate(semantic, template))
            task_dir = self._task_dir(task_id)
            artifacts.domain_path, artifacts.problem_path = self._write_model(task_dir, model)
            planner_result = self._timed("planning", steps, lambda: self.planner.plan(artifacts.domain_path, artifacts.problem_path, task_dir))
            artifacts.plan_path = planner_result.plan_path
            artifacts.log_path = planner_result.log_path
            validation = self._timed("validation", steps, lambda: self.validator.validate(model, planner_result))
            plan_content = "\n".join(planner_result.plan)
            explanation = _explain(text, semantic.domain_type, template.name, validation.summary, planner_result)
            success = planner_result.success and validation.is_valid
            error = "" if success else (planner_result.error or "; ".join(validation.issues) or "Planning failed.")
            response = PlanningResponse(success, task_id, plan_content, explanation, artifacts, steps, warnings, error)
            artifacts.result_path = self._write_result(task_dir, response, model, semantic, template)
            return response
        except Exception as exc:  # noqa: BLE001 - MCP tools should return errors, not raise
            return PlanningResponse(False, task_id, artifacts=artifacts, workflow_steps=steps, warnings=warnings, error=str(exc))

    def run_existing_pddl(self, domain_path: Path, problem_path: Path, task: dict[str, Any]) -> PlanningResponse:
        task_id = str(task.get("task_id") or _task_id())
        artifacts = PlanningArtifacts(domain_path=domain_path, problem_path=problem_path)
        steps: list[WorkflowStep] = []
        warnings: list[str] = []
        if not domain_path.exists():
            return PlanningResponse(False, task_id, artifacts=artifacts, error=f"Domain file does not exist: {domain_path}")
        if not problem_path.exists():
            return PlanningResponse(False, task_id, artifacts=artifacts, error=f"Problem file does not exist: {problem_path}")
        task_dir = self._task_dir(task_id)
        planner_result = self._timed("planning", steps, lambda: self.planner.plan(domain_path, problem_path, task_dir))
        artifacts.plan_path = planner_result.plan_path
        artifacts.log_path = planner_result.log_path
        if not self.settings.fast_downward_configured:
            warnings.append("FAST_DOWNWARD_PATH is not set; direct PDDL planning was not run.")
        success = planner_result.success
        response = PlanningResponse(
            success=success,
            task_id=task_id,
            plan_content="\n".join(planner_result.plan),
            explanation=_explain_existing(planner_result),
            artifacts=artifacts,
            workflow_steps=steps,
            warnings=warnings,
            error="" if success else planner_result.error,
        )
        artifacts.result_path = self._write_result(task_dir, response)
        return response

    def _timed(self, name: str, steps: list[WorkflowStep], fn):
        start = time.perf_counter()
        try:
            result = fn()
            steps.append(WorkflowStep(name, True, time.perf_counter() - start))
            return result
        except Exception as exc:
            steps.append(WorkflowStep(name, False, time.perf_counter() - start, str(exc)))
            raise

    def _task_dir(self, task_id: str) -> Path:
        path = self.settings.output_dir / task_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _write_model(self, task_dir: Path, model: PDDLModel) -> tuple[Path, Path]:
        domain_path = task_dir / "domain.pddl"
        problem_path = task_dir / "problem.pddl"
        domain_path.write_text(model.domain_content, encoding="utf-8")
        problem_path.write_text(model.problem_content, encoding="utf-8")
        return domain_path, problem_path

    def _write_result(self, task_dir: Path, response: PlanningResponse, model: PDDLModel | None = None, semantic=None, template=None) -> Path:
        path = task_dir / "result.json"
        payload: dict[str, Any] = response.to_dict()
        if model:
            payload["model"] = {"domain_name": model.domain_name, "problem_name": model.problem_name, "symbol_map": model.symbol_map}
        if semantic:
            payload["semantic"] = asdict(semantic)
        if template:
            payload["template"] = template_to_dict(template)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path


def _task_id() -> str:
    return f"task-{uuid.uuid4().hex[:12]}"


def _description_from_structured_task(task: dict[str, Any]) -> str:
    robot = task.get("robot")
    start = task.get("start")
    goal = task.get("goal")
    if robot and start and goal:
        return f"Move robot {robot} from {start} to {goal}."
    goal_data = task.get("goal", {})
    init_data = task.get("init", {})
    objects = task.get("objects", {})
    if isinstance(goal_data, dict) and isinstance(init_data, dict) and isinstance(objects, dict):
        robots = objects.get("robots") or ["robot1"]
        init_at = init_data.get("at") or []
        goal_at = goal_data.get("at") or []
        if init_at and goal_at:
            return f"Move robot {robots[0]} from {init_at[0][-1]} to {goal_at[0][-1]}."
    return ""


def _explain(text: str, domain_type: str, template_name: str, validation_summary: str, planner_result: PlannerResult) -> str:
    if planner_result.plan:
        plan_summary = f"Generated {len(planner_result.plan)} step(s)."
    else:
        plan_summary = "No executable plan was produced."
    return "\n".join(
        [
            f"Task: {text}",
            f"Domain: {domain_type}",
            f"Template: {template_name}",
            plan_summary,
            validation_summary,
        ]
    )


def _explain_existing(planner_result: PlannerResult) -> str:
    if planner_result.plan:
        return f"Planner generated {len(planner_result.plan)} step(s) from the provided PDDL files."
    return "Planner did not produce a plan from the provided PDDL files."
