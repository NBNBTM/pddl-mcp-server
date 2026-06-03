"""Natural-language semantic processing with deterministic fallback."""

from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

from .config import Settings
from .models import SemanticConstraint, SemanticEntity, SemanticGoal, SemanticRepresentation


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def configured(self) -> bool:
        return self.settings.llm_configured

    def extract(self, text: str) -> dict[str, Any]:
        payload = {
            "model": self.settings.llm_model,
            "temperature": 0.0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return only JSON for a PDDL planning request with keys: "
                        "domain_type, entities, constraints, goals, initial_state, confidence. "
                        "Entity objects use name,type,properties,relations. Goal objects use "
                        "type,target_state,priority,description."
                    ),
                },
                {"role": "user", "content": text},
            ],
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.settings.llm_api_key}",
        }
        response = None
        for attempt in range(self.settings.llm_retries + 1):
            try:
                response = requests.post(
                    self.settings.llm_api_url,
                    json=payload,
                    headers=headers,
                    timeout=self.settings.llm_timeout,
                )
                break
            except requests.RequestException:
                if attempt >= self.settings.llm_retries:
                    raise
                time.sleep(min(2.0, 0.5 * (attempt + 1)))
        if response is None:  # pragma: no cover - defensive guard
            raise RuntimeError("LLM request did not return a response.")
        response.raise_for_status()
        data = response.json()
        content = _extract_content(data)
        return _parse_json_content(content)


class SemanticProcessor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm_client = LLMClient(settings)

    def process(self, text: str) -> tuple[SemanticRepresentation, list[str]]:
        warnings: list[str] = []
        if self.llm_client.configured():
            try:
                llm_data = self.llm_client.extract(text)
                if _is_farmer_crossing_text(text):
                    normalized = _parse_farmer_crossing(text)
                    normalized.metadata["source"] = "llm+farmer_crossing_normalizer"
                    if isinstance(llm_data, dict):
                        normalized.metadata["llm_domain_type"] = str(llm_data.get("domain_type", "planning")).lower()
                        normalized.metadata["llm_confidence"] = _parse_confidence(llm_data.get("confidence", 0.7))
                    return normalized, warnings
                semantic = _semantic_from_dict(llm_data, source="llm")
                if not semantic.entities or not semantic.goals:
                    warnings.append("LLM semantic response was incomplete; deterministic fallback used.")
                    return fallback_semantic_parse(text), warnings
                return semantic, warnings
            except Exception as exc:  # noqa: BLE001 - fallback is intentional
                warnings.append(f"LLM semantic processing failed; deterministic fallback used: {exc}")
        else:
            warnings.append("LLM is not configured; deterministic semantic fallback used.")
        return fallback_semantic_parse(text), warnings


def fallback_semantic_parse(text: str) -> SemanticRepresentation:
    lowered = text.lower()
    if _looks_like_blocks(text):
        return _parse_blocks_world(text)
    if any(word in lowered for word in ["farmer", "wolf", "goat", "cabbage", "农夫", "狼", "羊", "白菜"]):
        return _parse_farmer_crossing(text)
    if any(word in lowered for word in ["package", "parcel", "deliver", "warehouse", "包裹", "配送", "仓库", "客户"]):
        return _parse_navigation_like(text, "logistics")
    return _parse_navigation_like(text, "navigation")


def _parse_navigation_like(text: str, domain_type: str) -> SemanticRepresentation:
    start, goal = _extract_start_goal(text)
    agent_name = _extract_first(text, [r"\brobot\s+([\w-]+)\b", r"\b(robot[\w-]*)\b", r"机器人\s*([\w-]+)", r"(机器人[\w-]*)"], "robot1")
    item_name = _extract_first(text, [r"\bpackage\s+([\w-]+)\b", r"\b(package[\w-]*)\b", r"\b(parcel[\w-]*)\b", r"包裹\s*([\w-]+)", r"(包裹[\w-]*)"], "package1")
    entities = [
        SemanticEntity(agent_name, "agent"),
        SemanticEntity(start, "location"),
        SemanticEntity(goal, "location"),
    ]
    target_state: dict[str, Any]
    goal_type = "move"
    if domain_type == "logistics":
        entities.append(SemanticEntity(item_name, "item"))
        target_state = {"at": {"entity": item_name, "location": goal}}
        goal_type = "deliver"
    else:
        target_state = {"at": {"entity": agent_name, "location": goal}}

    return SemanticRepresentation(
        domain_type=domain_type,
        entities=entities,
        constraints=[
            SemanticConstraint("location", [agent_name], f"at {start}", f"{agent_name} starts at {start}"),
            SemanticConstraint("connectivity", [start, goal], "connected", f"{start} connects to {goal}"),
        ],
        goals=[SemanticGoal(goal_type, target_state, 1, f"move target to {goal}")],
        initial_state={"start": start, "goal": goal, "agent": agent_name, "item": item_name if domain_type == "logistics" else ""},
        metadata={"confidence": 0.55, "source": "fallback"},
    )


def _parse_blocks_world(text: str) -> SemanticRepresentation:
    block_names = _extract_blocks(text)
    goals = _extract_on_goals(text)
    if not goals and len(block_names) >= 2:
        goals = [(block_names[0], block_names[1])]
    entities = [SemanticEntity(name, "block") for name in block_names]
    return SemanticRepresentation(
        domain_type="blocks_world",
        entities=entities,
        constraints=[SemanticConstraint("stacking", block_names, "clear blocks", "blocks can be stacked")],
        goals=[
            SemanticGoal("on", {"on": [{"top": top, "bottom": bottom} for top, bottom in goals]}, 1, "stack blocks")
        ],
        initial_state={"blocks": block_names},
        metadata={"confidence": 0.65, "source": "fallback"},
    )


def _parse_farmer_crossing(text: str) -> SemanticRepresentation:
    entities = [
        SemanticEntity("farmer", "agent"),
        SemanticEntity("wolf", "item"),
        SemanticEntity("goat", "item"),
        SemanticEntity("cabbage", "item"),
        SemanticEntity("left", "location"),
        SemanticEntity("right", "location"),
    ]
    return SemanticRepresentation(
        domain_type="farmer_crossing",
        entities=entities,
        constraints=[
            SemanticConstraint("safety", ["wolf", "goat"], "not alone without farmer", "wolf cannot be left alone with goat"),
            SemanticConstraint("safety", ["goat", "cabbage"], "not alone without farmer", "goat cannot be left alone with cabbage"),
            SemanticConstraint("capacity", ["boat"], "farmer plus at most one item", "boat carries farmer and at most one item"),
        ],
        goals=[
            SemanticGoal(
                "transport_all",
                {"at": {"farmer": "right", "wolf": "right", "goat": "right", "cabbage": "right"}},
                1,
                "transport farmer, wolf, goat, and cabbage to the right bank",
            )
        ],
        initial_state={"side": "left", "target": "right", "source_text": text},
        metadata={"confidence": 0.9, "source": "fallback", "puzzle": "farmer_wolf_goat_cabbage"},
    )


def _looks_like_blocks(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in ["block", "blocks", "积木", "方块", "堆叠", "stack"])


def _is_farmer_crossing_text(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in ["farmer", "wolf", "goat", "cabbage", "农夫", "狼", "羊", "白菜"])


def _extract_blocks(text: str) -> list[str]:
    names = re.findall(r"(?:block|积木|方块)\s*([A-Za-z][\w-]*)", text, flags=re.IGNORECASE)
    names.extend(re.findall(r"\b([A-Z])\b", text))
    deduped = []
    for name in names or ["A", "B", "C"]:
        if name not in deduped:
            deduped.append(name)
    return deduped[:10]


def _extract_on_goals(text: str) -> list[tuple[str, str]]:
    goals: list[tuple[str, str]] = []
    patterns = [
        r"\b([A-Za-z][\w-]*)\s+on\s+([A-Za-z][\w-]*)\b",
        r"([A-Za-z][\w-]*)\s*(?:放在|叠在|堆在)\s*([A-Za-z][\w-]*)\s*上",
    ]
    for pattern in patterns:
        goals.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return [(a, b) for a, b in goals if a.lower() != "block"]


def _extract_start_goal(text: str) -> tuple[str, str]:
    patterns = [
        r"\bfrom\s+([\w.-]+)\s+to\s+([\w.-]+)\b",
        r"\b(?:move|deliver|send|transport).*?\b([\w.-]+)\s+(?:to|into)\s+([\w.-]+)\b",
        r"从\s*([\w\u4e00-\u9fff.-]+)\s*(?:移动|运送|送|搬|到|去).*?(?:到|至)\s*([\w\u4e00-\u9fff.-]+)",
        r"把.*?从\s*([\w\u4e00-\u9fff.-]+).*?(?:到|至)\s*([\w\u4e00-\u9fff.-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)
    return "loc1", "loc2"


def _extract_first(text: str, patterns: list[str], default: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return default


def _extract_content(data: Any) -> str:
    if isinstance(data, dict):
        if data.get("choices"):
            return data["choices"][0]["message"]["content"]
        for key in ("content", "message", "response", "data"):
            if key in data:
                value = data[key]
                return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if isinstance(data, str):
        return data
    return json.dumps(data, ensure_ascii=False)


def _parse_json_content(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _semantic_from_dict(data: dict[str, Any], source: str) -> SemanticRepresentation:
    entities = [_entity_from_llm_item(item) for item in data.get("entities", [])]
    constraints = [_constraint_from_llm_item(item) for item in data.get("constraints", [])]
    goals = [_goal_from_llm_item(item) for item in data.get("goals", [])]
    metadata = {"confidence": _parse_confidence(data.get("confidence", 0.7)), "source": source}
    return SemanticRepresentation(
        domain_type=str(data.get("domain_type", "planning")).lower(),
        entities=[item for item in entities if item.name],
        constraints=constraints,
        goals=goals,
        initial_state=dict(data.get("initial_state", {})),
        metadata=metadata,
    )


def _entity_from_llm_item(item: Any) -> SemanticEntity:
    if isinstance(item, str):
        return SemanticEntity(name=item, type="object")
    if not isinstance(item, dict):
        return SemanticEntity(name="", type="object")
    return SemanticEntity(
        name=str(item.get("name", "")),
        type=str(item.get("type", "object")),
        properties=dict(item.get("properties", {})),
        relations=list(item.get("relations", [])),
    )


def _constraint_from_llm_item(item: Any) -> SemanticConstraint:
    if isinstance(item, str):
        return SemanticConstraint(type="constraint", description=item)
    if not isinstance(item, dict):
        return SemanticConstraint(type="constraint")
    return SemanticConstraint(
        type=str(item.get("type", "constraint")),
        entities=list(item.get("entities", [])),
        condition=str(item.get("condition", "")),
        description=str(item.get("description", "")),
    )


def _goal_from_llm_item(item: Any) -> SemanticGoal:
    if isinstance(item, str):
        return SemanticGoal(type="goal", description=item)
    if not isinstance(item, dict):
        return SemanticGoal(type="goal")
    target_state = item.get("target_state", {})
    return SemanticGoal(
        type=str(item.get("type", "goal")),
        target_state=target_state if isinstance(target_state, dict) else {"description": str(target_state)},
        priority=_parse_priority(item.get("priority", 1)),
        description=str(item.get("description", "")),
    )


def _parse_confidence(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.7


def _parse_priority(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip().lower()
    if text in {"high", "highest", "critical", "重要", "高"}:
        return 1
    if text in {"medium", "normal", "中"}:
        return 2
    if text in {"low", "低"}:
        return 3
    try:
        return int(text)
    except ValueError:
        return 1
