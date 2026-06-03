from pddl_mcp.config import load_settings
from pddl_mcp.knowledge import KnowledgeMatcher
from pddl_mcp.modeling import PDDLModeler
from pddl_mcp.semantic import SemanticProcessor, fallback_semantic_parse


def test_semantic_fallback_navigation(monkeypatch):
    monkeypatch.setenv("PDDL_MCP_DISABLE_DOTENV", "1")
    monkeypatch.delenv("LLM_API_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_TOKEN", raising=False)
    semantic, warnings = SemanticProcessor(load_settings()).process("Move robot r1 from room1 to room3")

    assert semantic.domain_type == "navigation"
    assert semantic.initial_state["start"] == "room1"
    assert semantic.initial_state["goal"] == "room3"
    assert warnings


def test_farmer_crossing_uses_llm_then_normalizes(monkeypatch):
    monkeypatch.setenv("PDDL_MCP_DISABLE_DOTENV", "1")
    monkeypatch.setenv("LLM_API_URL", "https://example.test/chat")
    monkeypatch.setenv("LLM_API_KEY", "test-token")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setattr(
        "pddl_mcp.semantic.LLMClient.extract",
        lambda self, text: {
            "domain_type": "river_crossing",
            "entities": ["farmer", "wolf", "goat", "cabbage"],
            "goals": [{"type": "transport_all", "priority": "high", "target_state": {"side": "right"}}],
            "confidence": "0.82",
        },
    )

    semantic, warnings = SemanticProcessor(load_settings()).process(
        "A farmer must take a wolf, a goat, and a cabbage across a river."
    )

    assert warnings == []
    assert semantic.domain_type == "farmer_crossing"
    assert semantic.metadata["source"] == "llm+farmer_crossing_normalizer"
    assert semantic.metadata["llm_domain_type"] == "river_crossing"
    assert semantic.metadata["llm_confidence"] == 0.82


def test_knowledge_matcher_uses_resource_templates():
    semantic = fallback_semantic_parse("Deliver package1 from warehouse to customer")
    template, warnings = KnowledgeMatcher().match(semantic)

    assert template.domain_type.upper() == "LOGISTICS"
    assert template.predicates
    assert warnings == []


def test_modeling_generates_navigation_pddl():
    semantic = fallback_semantic_parse("Move robot r1 from room1 to room3")
    template, _ = KnowledgeMatcher().match(semantic)
    model = PDDLModeler().generate(semantic, template)

    assert "(define (domain" in model.domain_content
    assert "(:action move" in model.domain_content
    assert "(at-agent r1 room3)" in model.problem_content


def test_modeling_generates_blocks_world_pddl():
    semantic = fallback_semantic_parse("Blocks A B C. Put A on B and B on C.")
    template, _ = KnowledgeMatcher().match(semantic)
    model = PDDLModeler().generate(semantic, template)

    assert "(:action stack" in model.domain_content
    assert "(on a b)" in model.problem_content


def test_modeling_generates_farmer_crossing_pddl():
    semantic = fallback_semantic_parse("A farmer must take a wolf, a goat, and a cabbage across a river.")
    template, _ = KnowledgeMatcher().match(semantic)
    model = PDDLModeler().generate(semantic, template)

    assert "(:action cross-with" in model.domain_content
    assert "(at wolf right)" in model.problem_content
    assert "(at goat right)" in model.problem_content
    assert "(at cabbage right)" in model.problem_content
