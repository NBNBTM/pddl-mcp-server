from pddl_mcp.config import load_settings, validate_runtime


def test_load_settings_uses_env_and_alias(monkeypatch, tmp_path):
    monkeypatch.setenv("PDDL_MCP_DISABLE_DOTENV", "1")
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("LLM_API_URL", "https://example.test/chat")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_API_TOKEN", "token-from-alias")
    monkeypatch.setenv("LLM_TIMEOUT", "90")
    monkeypatch.setenv("LLM_RETRIES", "3")
    monkeypatch.setenv("FAST_DOWNWARD_PATH", "/missing/fd.py")
    settings = load_settings()

    assert settings.output_dir == tmp_path / "out"
    assert settings.llm_api_key == "token-from-alias"
    assert settings.llm_configured is True
    assert settings.llm_timeout == 90
    assert settings.llm_retries == 3
    assert settings.fast_downward_path == "/missing/fd.py"


def test_validate_runtime_reports_missing_planner(monkeypatch):
    monkeypatch.setenv("PDDL_MCP_DISABLE_DOTENV", "1")
    monkeypatch.delenv("FAST_DOWNWARD_PATH", raising=False)
    monkeypatch.delenv("LLM_API_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_TOKEN", raising=False)

    result = validate_runtime(load_settings())

    assert result["success"] is True
    assert result["config"]["fast_downward_configured"] is False
    assert any("FAST_DOWNWARD_PATH" in warning for warning in result["warnings"])
