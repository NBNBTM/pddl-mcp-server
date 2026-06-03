# PDDL MCP Server

Single-version MCP backend for turning natural-language or explicit PDDL planning requests into Fast Downward plans.

## What It Does

- Accepts natural-language tasks through `plan_from_text`.
- Accepts either `description` or `domain_path` plus `problem_path` through `generate_plan`.
- Uses an LLM only when `LLM_API_URL` and `LLM_API_KEY` are configured.
- Falls back to deterministic local parsing when LLM configuration is missing or fails.
- Saves generated PDDL, planner logs, plans, and result JSON under `OUTPUT_DIR`.

## Project Layout

```text
pddl-mcp/
├── pyproject.toml
├── server.py
├── src/pddl_mcp/
│   ├── config.py
│   ├── knowledge.py
│   ├── modeling.py
│   ├── planner.py
│   ├── semantic.py
│   ├── server.py
│   ├── validation.py
│   ├── workflow.py
│   └── resources/domain_templates.json
└── tests/
```

## Setup

```bash
python -m pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` if you want live LLM parsing or real Fast Downward execution:

```bash
FAST_DOWNWARD_PATH=/absolute/path/to/fast-downward.py
LLM_API_URL=https://your-llm-endpoint.example/v1/chat/completions
LLM_API_KEY=...
LLM_TIMEOUT=30
LLM_RETRIES=1
```

## Run

```bash
python server.py
```

## Python Usage

```python
from pddl_mcp.workflow import plan_from_text_response

result = plan_from_text_response("Move robot r1 from room1 to room3")
print(result)
```

## MCP Tools

- `plan_from_text(text: str, options: dict | None = None)`
- `generate_plan(task: dict)`
- `validate_config()`
- `get_system_info()`

`PlanningResponse` always contains:

```text
success, task_id, plan_content, explanation, artifacts, workflow_steps, warnings, error
```

## Tests

```bash
python -m compileall src tests
pytest
ruff check .
```

If `FAST_DOWNWARD_PATH` is not configured, real planner tests are skipped or return a clear configuration warning; mock workflow tests still run.
