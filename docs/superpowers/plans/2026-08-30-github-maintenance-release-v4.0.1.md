# GitHub Maintenance Release v4.0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the repository files and GitHub settings, resolve stale pull requests, and publish a verified `v4.0.1` maintenance release without changing the four MCP tool interfaces.

**Architecture:** Repository policy is enforced in two layers: checked-in tests protect version and workflow configuration, while GitHub Rulesets and Actions permissions protect the default branch. File changes land through one maintenance PR before stricter settings are activated, preventing the repository from being locked by checks or SHA rules that do not yet exist.

**Tech Stack:** Python 3.10-3.14, pytest, Ruff, MCP Python SDK, FastMCP from `mcp.server.fastmcp`, Fast Downward, Docker, GitHub Actions, GitHub REST API, GitHub CLI.

**Spec:** `docs/superpowers/specs/2026-08-30-github-maintenance-release-design.md`

## Global Constraints

- Preserve `plan_from_text`, `generate_plan`, `validate_config`, and `get_system_info` signatures and response shapes.
- Do not rewrite Git history or delete release `v4.0.0`.
- Do not commit `.env`, API keys, model tokens, local planner builds, generated output, or `reports/`.
- Use release version `4.0.1` and tag `v4.0.1` for this maintenance release.
- Use only GitHub-owned Actions pinned to full 40-character commit SHAs.
- Keep the deterministic no-LLM fallback and optional Fast Downward configuration behavior.

---

### Task 1: Add repository policy tests in the red phase

**Files:**
- Create: `tests/test_repository_configuration.py`

**Interfaces:**
- Consumes: repository files under the project root.
- Produces: pytest checks for release version, action pinning, Python support, and required maintenance files.

- [ ] **Step 1: Add the failing version consistency test**

```python
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "4.0.1"


def test_release_version_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    mcp_config = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    server = (ROOT / "src/pddl_mcp/server.py").read_text(encoding="utf-8")
    pages = (ROOT / "docs/index.html").read_text(encoding="utf-8")

    assert project["project"]["version"] == EXPECTED_VERSION
    assert mcp_config["version"] == EXPECTED_VERSION
    assert server.count(f'"version": "{EXPECTED_VERSION}"') == 1
    assert f'version="{EXPECTED_VERSION}"' in server
    assert f"releases/tag/v{EXPECTED_VERSION}" in pages
    assert (ROOT / f"docs/releases/v{EXPECTED_VERSION}.md").is_file()
```

- [ ] **Step 2: Run the version test and verify the red phase**

Run: `pytest tests/test_repository_configuration.py::test_release_version_is_consistent -q`

Expected: FAIL because the repository still declares `4.0.0`.

- [ ] **Step 3: Add the failing workflow policy tests**

```python
ACTION_REF = re.compile(r"uses:\s+([^@\s]+)@([^\s#]+)")


def test_actions_are_pinned_to_full_shas() -> None:
    workflow_paths = sorted((ROOT / ".github/workflows").glob("*.yml"))
    refs = []
    for path in workflow_paths:
        refs.extend(ACTION_REF.findall(path.read_text(encoding="utf-8")))

    assert refs
    assert all(re.fullmatch(r"[0-9a-f]{40}", ref) for _, ref in refs)
    assert {action for action, _ in refs} <= {
        "actions/checkout",
        "actions/setup-python",
        "github/codeql-action/init",
        "github/codeql-action/analyze",
    }


def test_ci_covers_supported_python_versions() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for version in ("3.10", "3.11", "3.12", "3.13", "3.14"):
        assert f'"{version}"' in workflow


def test_maintenance_files_exist() -> None:
    required = (
        ".github/CODEOWNERS",
        ".dockerignore",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "Dockerfile",
        "examples/mcp_client_quickstart.py",
    )
    assert all((ROOT / path).is_file() for path in required)
```

- [ ] **Step 4: Run each workflow policy test and verify expected failures**

Run:

```bash
pytest tests/test_repository_configuration.py::test_actions_are_pinned_to_full_shas -q
pytest tests/test_repository_configuration.py::test_ci_covers_supported_python_versions -q
pytest tests/test_repository_configuration.py::test_maintenance_files_exist -q
```

Expected: each test FAILS for its named missing policy.

- [ ] **Step 5: Commit the red tests**

```bash
git add tests/test_repository_configuration.py
git commit -m "test: define repository maintenance policy"
```

### Task 2: Upgrade versions, workflows, and dependencies

**Files:**
- Modify: `pyproject.toml`
- Modify: `.mcp.json`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/codeql.yml`
- Modify: `src/pddl_mcp/server.py`
- Delete: `src/pddl_mcp/errors.py`
- Create: `docs/releases/v4.0.1.md`

**Interfaces:**
- Consumes: policy tests from Task 1.
- Produces: version `4.0.1`, SHA-pinned workflows, and Python 3.10-3.14 checks.

- [ ] **Step 1: Set every runtime and metadata version to `4.0.1`**

Change `pyproject.toml`, `.mcp.json`, and both version strings in `src/pddl_mcp/server.py`. Create release notes at `docs/releases/v4.0.1.md` describing workflow upgrades, community files, Docker, client example, cleanup, and unchanged MCP interfaces.

- [ ] **Step 2: Remove dead dependency and module**

Remove `fastmcp>=0.4.1` from `pyproject.toml`. Delete `src/pddl_mcp/errors.py`. Keep `mcp>=1.0.0` because it provides `mcp.server.fastmcp`.

- [ ] **Step 3: Pin and upgrade CI Actions**

Use these exact references:

```yaml
actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
github/codeql-action/init@cdf488f595d80d6e07e03d4674febd5ab45fa938 # v4
github/codeql-action/analyze@cdf488f595d80d6e07e03d4674febd5ab45fa938 # v4
```

Set the CI matrix to `3.10`, `3.11`, `3.12`, `3.13`, and `3.14`. Remove the nonexistent `develop` push trigger so CI targets `main` and pull requests to `main`.

- [ ] **Step 4: Run the focused policy tests**

Run:

```bash
pytest tests/test_repository_configuration.py::test_release_version_is_consistent -q
pytest tests/test_repository_configuration.py::test_actions_are_pinned_to_full_shas -q
pytest tests/test_repository_configuration.py::test_ci_covers_supported_python_versions -q
```

Expected: version, action pinning, and Python matrix tests PASS; maintenance-files test remains red.

- [ ] **Step 5: Run existing tests and lint**

Run:

```bash
pytest -q -p no:cacheprovider
ruff check . --no-cache
python -m compileall -q src tests server.py
```

Expected: all existing behavior remains green.

- [ ] **Step 6: Commit workflow and version changes**

```bash
git add pyproject.toml .mcp.json .github/workflows/ci.yml .github/workflows/codeql.yml src/pddl_mcp/server.py src/pddl_mcp/errors.py docs/releases/v4.0.1.md
git commit -m "chore: prepare v4.0.1 maintenance release"
```

### Task 3: Add community governance files

**Files:**
- Create: `.github/CODEOWNERS`
- Create: `CONTRIBUTING.md`
- Create: `CODE_OF_CONDUCT.md`

**Interfaces:**
- Consumes: existing README setup and security commands.
- Produces: explicit ownership, contribution workflow, and conduct policy.

- [ ] **Step 1: Add repository ownership**

Create `.github/CODEOWNERS` with:

```text
* @NBNBTM
```

- [ ] **Step 2: Add contribution guidance**

`CONTRIBUTING.md` must include:

- editable installation with `python -m pip install -e ".[dev]"`;
- pytest, Ruff, and compile commands used by CI;
- one focused branch and PR per change;
- no secrets, `.env`, employer-confidential data, planner outputs, or local builds;
- issue-first guidance for behavior changes;
- signed commits and squash-merge expectations; and
- private security reporting through `SECURITY.md`.

- [ ] **Step 3: Add Contributor Covenant 3.0**

Use the canonical Markdown from:

`https://www.contributor-covenant.org/version/3/0/code_of_conduct/code_of_conduct.md`

Set the enforcement contact to the maintainer's public GitHub contact email `yanglinsen761@gmail.com`. State that sensitive conduct reports must not be opened as public issues.

- [ ] **Step 4: Run Markdown secret and placeholder checks**

Run:

```bash
rg -n "TBD|TODO|INSERT CONTACT|sk-[A-Za-z0-9]" CODE_OF_CONDUCT.md CONTRIBUTING.md .github/CODEOWNERS
```

Expected: no matches.

- [ ] **Step 5: Commit community files**

```bash
git add .github/CODEOWNERS CONTRIBUTING.md CODE_OF_CONDUCT.md
git commit -m "docs: add community contribution policies"
```

### Task 4: Resolve and replace the MCP client quickstart contribution

**Files:**
- Create: `examples/mcp_client_quickstart.py`
- Create or modify: `tests/test_examples.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: MCP SDK `ClientSession`, `StdioServerParameters`, and `stdio_client`.
- Produces: `default_request()`, `run_example(text: str)`, `print_summary(payload: dict)`, and CLI `main()`.

- [ ] **Step 1: Review PR #9 in an isolated worktree**

Fetch `refs/pull/9/head`, run compile and dependency checks, and confirm that its direct `pydantic` import is not declared by this project. Record that the contribution is useful but requires correction before inclusion.

- [ ] **Step 2: Add a failing quickstart policy test**

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mcp_quickstart_avoids_transitive_dependencies() -> None:
    source = (ROOT / "examples/mcp_client_quickstart.py").read_text(encoding="utf-8")
    assert "from pydantic" not in source
    assert "ClientSession" in source
    assert "plan_from_text" in source
```

Run: `pytest tests/test_examples.py::test_mcp_quickstart_avoids_transitive_dependencies -q`

Expected: FAIL because the corrected example is not yet present.

- [ ] **Step 3: Implement the corrected client example**

Adapt the useful structure from PR #9 while removing the direct `pydantic` dependency. Normalize the tool result with `model_dump()` only when that method exists, otherwise accept dictionaries and `structuredContent`/`structured_content`. Preserve environment inheritance for subprocess startup and expose `--text`.

- [ ] **Step 4: Document and test the example**

Add the example path and command to README. Run:

```bash
python -m compileall -q examples
pytest tests/test_examples.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the corrected example**

Use a commit message acknowledging the contribution in the body:

```bash
git add examples/mcp_client_quickstart.py tests/test_examples.py README.md
git commit -m "docs: add MCP client quickstart" -m "Based on the useful initial contribution in PR #9 by Arjun Avtani."
```

### Task 5: Add reproducible Docker planner support

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`
- Modify: `tests/test_repository_configuration.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`

**Interfaces:**
- Consumes: package entrypoint `server.py` and official Fast Downward repository.
- Produces: a Linux image running the MCP server with a built Fast Downward planner.

- [ ] **Step 1: Add a failing Docker policy test**

Add assertions that the Dockerfile:

- starts from `python:3.14-slim`;
- pins Fast Downward to a full commit SHA build argument;
- sets `FAST_DOWNWARD_PATH`;
- never copies `.env`; and
- runs `python server.py`.

Run the test and verify it fails because the Dockerfile does not exist.

- [ ] **Step 2: Resolve and pin the current Fast Downward main commit**

Run `gh api repos/aibasel/downward/commits/main --jq .sha` and place the returned 40-character SHA in `ARG FAST_DOWNWARD_REF=`. Do not use an unpinned branch in the Docker build.

- [ ] **Step 3: Implement a two-stage Dockerfile**

The builder stage installs only build requirements, checks out the pinned Fast Downward commit, and runs `python build.py`. The runtime stage installs the PDDL MCP package, copies the built planner, sets `FAST_DOWNWARD_PATH=/opt/fast-downward/fast-downward.py`, sets `PDDL_MCP_DISABLE_DOTENV=1`, and starts `python server.py` over stdio.

- [ ] **Step 4: Add `.dockerignore`**

Ignore `.git`, `.github`, `.env*` except `.env.example`, `.tools`, `output`, `outputs`, `reports`, caches, coverage, local virtual environments, tests, and documentation assets not needed by package installation.

- [ ] **Step 5: Add an independent Docker CI job**

Add a `docker` job on `ubuntu-latest` that checks out the repository with the pinned v7 SHA, builds `pddl-mcp-server:ci`, and runs an import/config smoke check without exposing credentials.

- [ ] **Step 6: Validate Docker support**

Run repository policy tests. If local Docker exists, run `docker build -t pddl-mcp-server:local .`; otherwise record that local Docker is unavailable and rely on the PR's GitHub-hosted `docker` job.

- [ ] **Step 7: Commit Docker support**

```bash
git add Dockerfile .dockerignore .github/workflows/ci.yml tests/test_repository_configuration.py README.md
git commit -m "build: add reproducible Docker planner image"
```

### Task 6: Finish documentation and Pages version updates

**Files:**
- Modify: `README.md`
- Modify: `docs/index.html`
- Modify: `docs/releases/v4.0.1.md`

**Interfaces:**
- Consumes: completed client and Docker commands.
- Produces: public documentation that matches tested repository behavior.

- [ ] **Step 1: Update the repository tree and quickstart sections**

Add community files, Docker files, and `examples/` to the README tree. Document client execution, container build/run, runtime environment variables, and the fact that no secrets are baked into the image.

- [ ] **Step 2: Replace `v4.0.0` current-release links with `v4.0.1`**

Update README current release notes and Pages release links/footer. Keep `docs/releases/v4.0.0.md` as historical documentation.

- [ ] **Step 3: Update expected test count only after running the complete suite**

Use the actual pytest count from the final local run rather than predicting it.

- [ ] **Step 4: Run link and version scans**

Run:

```bash
rg -n "v4\.0\.0|4\.0\.0" README.md docs/index.html pyproject.toml .mcp.json src/pddl_mcp/server.py
rg -n "requirements\.txt|OPENAI_API_KEY|FAST_DOWNWARD_PATH" README.md docs/index.html Dockerfile
```

Expected: `v4.0.0` remains only where explicitly historical; no stale installation command or unsupported `OPENAI_API_KEY` wording remains.

- [ ] **Step 5: Commit documentation updates**

```bash
git add README.md docs/index.html docs/releases/v4.0.1.md
git commit -m "docs: publish v4.0.1 usage guidance"
```

### Task 7: Verify, push, and open the maintenance PR

**Files:**
- Verify all modified files.

**Interfaces:**
- Consumes: Tasks 1-6.
- Produces: a reviewable GitHub pull request with passing checks.

- [ ] **Step 1: Run complete local verification**

```bash
pytest -q -p no:cacheprovider
ruff check . --no-cache
python -m compileall -q src tests examples server.py
git diff --check origin/main...HEAD
git grep -nE 'sk-[A-Za-z0-9]{12,}|(api[_-]?key|token)[[:space:]]*=[[:space:]]*[A-Za-z0-9_-]{16,}' -- ':!*.lock'
```

Expected: tests, lint, compile, diff, and tracked-file secret scan pass.

- [ ] **Step 2: Push the maintenance branch**

Run: `git push -u origin chore/github-maintenance-v4.0.1`

- [ ] **Step 3: Open the maintenance PR**

Open a PR titled `chore: publish v4.0.1 maintenance release` with a summary of workflow, governance, Docker, client, and cleanup changes plus the exact local verification results.

- [ ] **Step 4: Wait for GitHub checks**

Require successful `test (3.10)` through `test (3.14)`, `docker`, and `Analyze Python`. Address failures on the same branch and re-run local verification before every push.

- [ ] **Step 5: Merge through GitHub squash merge**

Merge only after all checks pass. Delete the maintenance branch after merge.

### Task 8: Resolve the two older external pull requests

**Files:**
- No local files unless conflict repair is required.

**Interfaces:**
- Consumes: merged maintenance PR URL.
- Produces: closed PR #9 and PR #10 with public explanations and attribution.

- [ ] **Step 1: Comment on and close PR #9**

Thank Arjun Avtani, explain that the structure informed the corrected quickstart, identify the undeclared direct `pydantic` dependency, and link the merged maintenance PR and final example.

- [ ] **Step 2: Comment on and close PR #10**

Thank the contributor, explain that README-only instructions could not claim an included planner image, and link the merged Dockerfile implementation.

- [ ] **Step 3: Close completed issues #7 and #8**

Link the merged maintenance PR and confirm the acceptance result. Keep logistics issue #6 open because it is independent of this maintenance release.

### Task 9: Apply GitHub governance and security settings

**Files:**
- No repository file changes.

**Interfaces:**
- Consumes: successful checks registered on merged `main`.
- Produces: enforced Actions policy, merge policy, Topics, and default-branch Ruleset.

- [ ] **Step 1: Restrict Actions after pinned workflows are on main**

Set repository Actions permissions to enabled, `allowed_actions=selected`, and `sha_pinning_required=true`. Set selected actions to `github_owned_allowed=true`, `verified_allowed=false`, and an empty pattern list. Re-read both endpoints and verify the returned values.

- [ ] **Step 2: Update repository merge settings and Topics**

Enable squash merge, auto-merge, branch deletion, and update-branch support. Disable merge commits and rebase merges. Preserve existing Topics and add `mcp-server` and `model-context-protocol`.

- [ ] **Step 3: Enable additional secret-scanning settings**

Attempt to enable `secret_scanning_non_provider_patterns` and `secret_scanning_validity_checks`. Re-read `security_and_analysis`; report an unsupported API response without weakening existing secret scanning or push protection.

- [ ] **Step 4: Update Ruleset 6443990**

Use `~DEFAULT_BRANCH`, no bypass actors, and these rules:

- pull request required, zero approvals, no code-owner review, review-thread resolution required, squash only;
- strict required status checks for `test (3.10)`, `test (3.11)`, `test (3.12)`, `test (3.13)`, `test (3.14)`, `docker`, and `Analyze Python`;
- required signatures; and
- non-fast-forward protection.

Re-read the Ruleset and effective `main` rules to confirm each condition.

### Task 10: Publish and verify release v4.0.1

**Files:**
- No further source changes expected.

**Interfaces:**
- Consumes: final protected `main` commit and release notes.
- Produces: tag and latest release `v4.0.1`, plus synchronized local state.

- [ ] **Step 1: Create the release at the exact final main commit**

Fetch `main`, resolve its full SHA, and run:

```bash
gh release create v4.0.1 --repo NBNBTM/pddl-mcp-server --target "$FINAL_MAIN_SHA" --title "PDDL MCP Server v4.0.1" --notes-file docs/releases/v4.0.1.md
```

- [ ] **Step 2: Verify release, tag, and public site**

Confirm the tag and release target the final commit, release is neither draft nor prerelease, Pages returns HTTP 200 over HTTPS, and the custom social preview remains enabled.

- [ ] **Step 3: Verify security and workflows**

Confirm latest CI, CodeQL, Docker, Pages, and Dependency Graph runs are successful. Confirm Dependabot, code-scanning, and secret-scanning open alert counts are zero.

- [ ] **Step 4: Synchronize local main**

Switch to local `main`, fetch with pruning, fast-forward to `origin/main`, fetch tags, and confirm:

```text
local main == origin/main == v4.0.1 release target
```

The ignored `.env`, `.tools/`, `reports/`, and generated output remain local and untracked.
