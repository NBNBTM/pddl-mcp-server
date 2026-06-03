"""PDDL model generation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import DomainTemplate, PDDLModel, SemanticEntity, SemanticRepresentation


@dataclass
class SymbolTable:
    mapping: dict[str, str]

    def get(self, name: str, prefix: str) -> str:
        if name in self.mapping:
            return self.mapping[name]
        base = _sanitize_ascii(name)
        if not base or base in self.mapping.values():
            base = f"{prefix}{len(self.mapping) + 1}"
        self.mapping[name] = base
        return base


class PDDLModeler:
    def generate(self, semantic: SemanticRepresentation, template: DomainTemplate) -> PDDLModel:
        if _looks_like_farmer_crossing(semantic):
            return self._generate_farmer_crossing()
        if semantic.domain_type.lower() in {"blocks_world", "blocksworld"}:
            return self._generate_blocks_world(semantic)
        return self._generate_movement_model(semantic, template)

    def _generate_movement_model(self, semantic: SemanticRepresentation, template: DomainTemplate) -> PDDLModel:
        symbols = SymbolTable({})
        agents = [entity for entity in semantic.entities if entity.type in {"agent", "robot", "vehicle"}]
        items = [entity for entity in semantic.entities if entity.type in {"item", "object", "package", "parcel"}]
        locations = [entity for entity in semantic.entities if entity.type == "location"]

        if not agents:
            agents = [SemanticEntity("robot1", "agent")]
        start = str(semantic.initial_state.get("start") or (locations[0].name if locations else "loc1"))
        goal = str(semantic.initial_state.get("goal") or (locations[-1].name if len(locations) > 1 else "loc2"))
        location_names = _dedupe([start, goal] + [entity.name for entity in locations])
        agent_names = _dedupe([entity.name for entity in agents])
        item_names = _dedupe([entity.name for entity in items])

        domain_name = _domain_name(template.domain_type)
        domain_content = f"""(define (domain {domain_name})
  (:requirements :strips :typing)
  (:types agent item location)
  (:predicates
    (at-agent ?a - agent ?l - location)
    (at-item ?i - item ?l - location)
    (connected ?from - location ?to - location)
    (carrying ?a - agent ?i - item)
  )
  (:action move
    :parameters (?a - agent ?from - location ?to - location)
    :precondition (and (at-agent ?a ?from) (connected ?from ?to))
    :effect (and (not (at-agent ?a ?from)) (at-agent ?a ?to))
  )
  (:action pickup
    :parameters (?a - agent ?i - item ?l - location)
    :precondition (and (at-agent ?a ?l) (at-item ?i ?l))
    :effect (and (not (at-item ?i ?l)) (carrying ?a ?i))
  )
  (:action drop
    :parameters (?a - agent ?i - item ?l - location)
    :precondition (and (at-agent ?a ?l) (carrying ?a ?i))
    :effect (and (not (carrying ?a ?i)) (at-item ?i ?l))
  )
)"""

        agent_symbols = [symbols.get(name, "agent") for name in agent_names]
        item_symbols = [symbols.get(name, "item") for name in item_names]
        location_symbols = [symbols.get(name, "loc") for name in location_names]
        start_symbol = symbols.get(start, "loc")
        goal_symbol = symbols.get(goal, "loc")
        init_lines = [f"(at-agent {agent_symbols[0]} {start_symbol})"]
        init_lines.extend(f"(at-item {item} {start_symbol})" for item in item_symbols)
        init_lines.extend(
            f"(connected {left} {right})"
            for left in location_symbols
            for right in location_symbols
            if left != right
        )
        if item_symbols and semantic.domain_type.lower() == "logistics":
            goal_expr = f"(at-item {item_symbols[0]} {goal_symbol})"
        else:
            goal_expr = f"(at-agent {agent_symbols[0]} {goal_symbol})"

        objects = []
        objects.append(f"{' '.join(agent_symbols)} - agent")
        if item_symbols:
            objects.append(f"{' '.join(item_symbols)} - item")
        objects.append(f"{' '.join(location_symbols)} - location")
        problem_content = f"""(define (problem {domain_name}-problem)
  (:domain {domain_name})
  (:objects
    {chr(10).join('    ' + item for item in objects)}
  )
  (:init
    {chr(10).join('    ' + item for item in init_lines)}
  )
  (:goal (and {goal_expr}))
)"""
        return PDDLModel(domain_name, f"{domain_name}-problem", domain_content, problem_content, symbols.mapping)

    def _generate_blocks_world(self, semantic: SemanticRepresentation) -> PDDLModel:
        symbols = SymbolTable({})
        blocks = _dedupe([entity.name for entity in semantic.entities if entity.type == "block"]) or ["A", "B", "C"]
        block_symbols = [symbols.get(name, "block") for name in blocks]
        goals = []
        for goal in semantic.goals:
            for pair in goal.target_state.get("on", []):
                top = symbols.get(str(pair.get("top", "")), "block")
                bottom = symbols.get(str(pair.get("bottom", "")), "block")
                if top and bottom:
                    goals.append(f"(on {top} {bottom})")
        if not goals and len(block_symbols) >= 2:
            goals.append(f"(on {block_symbols[0]} {block_symbols[1]})")
        goal_expr = " ".join(goals) if goals else "(handempty)"
        domain_name = "pddl-mcp-blocks"
        domain_content = f"""(define (domain {domain_name})
  (:requirements :strips :typing)
  (:types block)
  (:predicates
    (on ?x - block ?y - block)
    (ontable ?x - block)
    (clear ?x - block)
    (holding ?x - block)
    (handempty)
  )
  (:action pickup
    :parameters (?x - block)
    :precondition (and (clear ?x) (ontable ?x) (handempty))
    :effect (and (not (ontable ?x)) (not (clear ?x)) (not (handempty)) (holding ?x))
  )
  (:action putdown
    :parameters (?x - block)
    :precondition (holding ?x)
    :effect (and (ontable ?x) (clear ?x) (handempty) (not (holding ?x)))
  )
  (:action stack
    :parameters (?x - block ?y - block)
    :precondition (and (holding ?x) (clear ?y))
    :effect (and (not (holding ?x)) (not (clear ?y)) (clear ?x) (handempty) (on ?x ?y))
  )
  (:action unstack
    :parameters (?x - block ?y - block)
    :precondition (and (on ?x ?y) (clear ?x) (handempty))
    :effect (and (holding ?x) (clear ?y) (not (clear ?x)) (not (handempty)) (not (on ?x ?y)))
  )
)"""
        init_lines = ["(handempty)"]
        init_lines.extend(f"(ontable {block})" for block in block_symbols)
        init_lines.extend(f"(clear {block})" for block in block_symbols)
        problem_content = f"""(define (problem {domain_name}-problem)
  (:domain {domain_name})
  (:objects {' '.join(block_symbols)} - block)
  (:init
    {chr(10).join('    ' + item for item in init_lines)}
  )
  (:goal (and {goal_expr}))
)"""
        return PDDLModel(domain_name, f"{domain_name}-problem", domain_content, problem_content, symbols.mapping)

    def _generate_farmer_crossing(self) -> PDDLModel:
        domain_name = "pddl-mcp-farmer-crossing"
        domain_content = f"""(define (domain {domain_name})
  (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :equality)
  (:types item side)
  (:constants wolf goat cabbage - item left right - side)
  (:predicates
    (farmer-at ?s - side)
    (at ?i - item ?s - side)
    (opposite ?from - side ?to - side)
  )
  (:action cross-alone
    :parameters (?from - side ?to - side)
    :precondition (and
      (farmer-at ?from)
      (opposite ?from ?to)
      (not (and (at wolf ?from) (at goat ?from)))
      (not (and (at goat ?from) (at cabbage ?from)))
    )
    :effect (and
      (not (farmer-at ?from))
      (farmer-at ?to)
    )
  )
  (:action cross-with
    :parameters (?item - item ?from - side ?to - side)
    :precondition (and
      (farmer-at ?from)
      (at ?item ?from)
      (opposite ?from ?to)
      (or
        (= ?item goat)
        (and
          (not (and (at wolf ?from) (at goat ?from)))
          (not (and (at goat ?from) (at cabbage ?from)))
        )
        (and
          (= ?item wolf)
          (not (and (at goat ?from) (at cabbage ?from)))
        )
        (and
          (= ?item cabbage)
          (not (and (at wolf ?from) (at goat ?from)))
        )
      )
    )
    :effect (and
      (not (farmer-at ?from))
      (farmer-at ?to)
      (not (at ?item ?from))
      (at ?item ?to)
    )
  )
)"""
        problem_content = f"""(define (problem {domain_name}-problem)
  (:domain {domain_name})
  (:init
    (farmer-at left)
    (at wolf left)
    (at goat left)
    (at cabbage left)
    (opposite left right)
    (opposite right left)
  )
  (:goal (and
    (farmer-at right)
    (at wolf right)
    (at goat right)
    (at cabbage right)
  ))
)"""
        return PDDLModel(
            domain_name,
            f"{domain_name}-problem",
            domain_content,
            problem_content,
            {"farmer": "farmer", "wolf": "wolf", "goat": "goat", "cabbage": "cabbage", "left": "left", "right": "right"},
        )


def _domain_name(domain_type: str) -> str:
    normalized = _sanitize_ascii(domain_type.lower()) or "planning"
    return f"pddl-mcp-{normalized}"


def _sanitize_ascii(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = value.strip("-_")
    if value and value[0].isdigit():
        value = f"n-{value}"
    return value


def _dedupe(items: list[str]) -> list[str]:
    result = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def _looks_like_farmer_crossing(semantic: SemanticRepresentation) -> bool:
    names = {entity.name.lower() for entity in semantic.entities}
    domain = semantic.domain_type.lower()
    return domain in {"farmer_crossing", "farmer-crossing"} or {"wolf", "goat", "cabbage"}.issubset(names)
