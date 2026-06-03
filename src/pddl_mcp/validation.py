"""Lightweight plan validation."""

from __future__ import annotations

import re

from .models import PDDLModel, PlannerResult, ValidationResult


class PlanValidator:
    def validate(self, model: PDDLModel, planner_result: PlannerResult) -> ValidationResult:
        if not planner_result.success:
            return ValidationResult(False, [planner_result.error or "Planner failed."], "Planner failed.")
        if not planner_result.plan:
            return ValidationResult(True, [], "Planner reported success with an empty plan.")

        action_names = set(re.findall(r"\(:action\s+([^\s)]+)", model.domain_content, flags=re.IGNORECASE))
        issues = []
        for step in planner_result.plan:
            match = re.match(r"\(?\s*([^\s)]+)", step)
            if match and match.group(1) not in action_names:
                issues.append(f"Plan step uses an action not declared in the generated domain: {step}")
        if issues:
            return ValidationResult(False, issues, "Plan references undeclared actions.")
        return ValidationResult(True, [], f"Plan contains {len(planner_result.plan)} valid declared action(s).")
