"""Shared data models for the planning workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SemanticEntity:
    name: str
    type: str
    properties: dict[str, Any] = field(default_factory=dict)
    relations: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SemanticConstraint:
    type: str
    entities: list[str] = field(default_factory=list)
    condition: str = ""
    description: str = ""


@dataclass
class SemanticGoal:
    type: str
    target_state: dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    description: str = ""


@dataclass
class SemanticRepresentation:
    domain_type: str
    entities: list[SemanticEntity] = field(default_factory=list)
    constraints: list[SemanticConstraint] = field(default_factory=list)
    goals: list[SemanticGoal] = field(default_factory=list)
    initial_state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainTemplate:
    name: str
    domain_type: str
    description: str
    predicates: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    typical_entities: list[str] = field(default_factory=list)
    typical_constraints: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    source: str = "resource"


@dataclass
class PDDLModel:
    domain_name: str
    problem_name: str
    domain_content: str
    problem_content: str
    symbol_map: dict[str, str] = field(default_factory=dict)


@dataclass
class PlannerResult:
    success: bool
    plan: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    return_code: int | None = None
    duration_sec: float = 0.0
    plan_path: Path | None = None
    log_path: Path | None = None
    command: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class ValidationResult:
    is_valid: bool
    issues: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class WorkflowStep:
    name: str
    success: bool
    duration_sec: float
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "success": self.success,
            "duration_sec": round(self.duration_sec, 6),
            "message": self.message,
        }


@dataclass
class PlanningArtifacts:
    domain_path: Path | None = None
    problem_path: Path | None = None
    plan_path: Path | None = None
    log_path: Path | None = None
    result_path: Path | None = None

    def to_dict(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for key, value in {
            "domain_path": self.domain_path,
            "problem_path": self.problem_path,
            "plan_path": self.plan_path,
            "log_path": self.log_path,
            "result_path": self.result_path,
        }.items():
            if value:
                result[key] = str(value)
        return result


@dataclass
class PlanningResponse:
    success: bool
    task_id: str
    plan_content: str = ""
    explanation: str = ""
    artifacts: PlanningArtifacts = field(default_factory=PlanningArtifacts)
    workflow_steps: list[WorkflowStep] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "task_id": self.task_id,
            "plan_content": self.plan_content,
            "explanation": self.explanation,
            "artifacts": self.artifacts.to_dict(),
            "workflow_steps": [step.to_dict() for step in self.workflow_steps],
            "warnings": self.warnings,
            "error": self.error,
        }
