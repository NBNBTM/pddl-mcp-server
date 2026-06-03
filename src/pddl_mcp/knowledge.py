"""Domain-template matching."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from .models import DomainTemplate, SemanticRepresentation

DOMAIN_ALIASES = {
    "blocks_world": "PUZZLE",
    "blocksworld": "PUZZLE",
    "puzzle": "PUZZLE",
    "navigation": "NAVIGATION",
    "logistics": "LOGISTICS",
    "transportation": "TRANSPORTATION",
    "transport": "TRANSPORT",
    "planning": "PLANNING",
    "general": "PLANNING",
}


class KnowledgeMatcher:
    def __init__(self, templates: list[DomainTemplate] | None = None):
        self.templates = templates or load_templates()

    def match(self, semantic: SemanticRepresentation) -> tuple[DomainTemplate, list[str]]:
        warnings: list[str] = []
        target = DOMAIN_ALIASES.get(semantic.domain_type.lower(), semantic.domain_type.upper())
        candidates = [template for template in self.templates if template.domain_type.upper() == target]
        if not candidates and target == "PUZZLE":
            candidates = [
                template
                for template in self.templates
                if "block" in " ".join(template.actions + template.predicates).lower()
                or "积木" in template.description
            ]
        if not candidates:
            candidates = [template for template in self.templates if template.domain_type.upper() == "PLANNING"]
            warnings.append(f"No exact domain template for {semantic.domain_type}; generic planning template used.")
        if not candidates:
            candidates = [_fallback_template()]
            warnings.append("Domain template resource was empty; built-in fallback template used.")
        return max(candidates, key=lambda template: template.confidence_score), warnings


def load_templates() -> list[DomainTemplate]:
    resource = files("pddl_mcp.resources").joinpath("domain_templates.json")
    data = json.loads(resource.read_text(encoding="utf-8"))
    templates = []
    for item in data:
        templates.append(
            DomainTemplate(
                name=str(item.get("name", "planning")),
                domain_type=str(item.get("domain_type", "PLANNING")),
                description=str(item.get("description", "")),
                predicates=list(item.get("predicates", [])),
                actions=list(item.get("actions", [])),
                requirements=list(item.get("requirements", [])),
                typical_entities=list(item.get("typical_entities", [])),
                typical_constraints=list(item.get("typical_constraints", [])),
                confidence_score=float(item.get("confidence_score", 0.0)),
                source=str(item.get("benchmark_source", "resource")),
            )
        )
    return templates


def _fallback_template() -> DomainTemplate:
    return DomainTemplate(
        name="generic-planning",
        domain_type="PLANNING",
        description="Generic movement and delivery planning template",
        predicates=["at-agent", "at-item", "connected", "carrying"],
        actions=["move", "pickup", "drop"],
        requirements=[":strips", ":typing"],
        typical_entities=["agent", "item", "location"],
        confidence_score=0.1,
        source="built-in",
    )


def template_to_dict(template: DomainTemplate) -> dict[str, Any]:
    return {
        "name": template.name,
        "domain_type": template.domain_type,
        "description": template.description,
        "predicates": template.predicates,
        "actions": template.actions,
        "requirements": template.requirements,
        "confidence_score": template.confidence_score,
        "source": template.source,
    }
