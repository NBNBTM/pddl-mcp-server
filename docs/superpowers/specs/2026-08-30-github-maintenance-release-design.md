# GitHub Maintenance Release v4.0.1 Design

## Purpose

Bring the public `NBNBTM/pddl-mcp-server` repository to a current, internally consistent, and maintainable state without changing the planning workflow's public MCP interfaces. The work covers repository files, CI coverage, GitHub governance and security settings, contributor-facing documentation, two open pull requests, and a maintenance release.

## Scope

The maintenance release will:

- upgrade GitHub-owned Actions to their current major versions and pin every action to a full commit SHA;
- test every supported CPython minor version from 3.10 through 3.14;
- add policy tests that detect version drift and insecure workflow references;
- remove the unused standalone `fastmcp` dependency and dead `errors.py` module;
- add `CODEOWNERS`, `CONTRIBUTING.md`, and Contributor Covenant 3.0;
- provide a tested MCP client quickstart and a complete Docker setup;
- make all project version declarations `4.0.1`;
- replace the current broad ruleset with a default-branch ruleset that requires the repository's actual checks;
- restrict Actions to GitHub-owned actions pinned by full SHA;
- improve security-scanning settings where the account and repository support them;
- update repository Topics and merge settings;
- resolve the two open pull requests with clear attribution and comments; and
- publish and verify release `v4.0.1` after the maintenance PR is merged.

The natural-language semantic workflow, PDDL model generation, Fast Downward invocation, validation behavior, and four MCP tool interfaces remain unchanged.

## Repository File Design

### Workflow and version policy

The CI workflow will use the current `actions/checkout` and `actions/setup-python` v7 commits. CodeQL will remain on its current v4 line and will also be pinned to a full SHA. Inline comments will retain the human-readable release version beside each SHA so Dependabot updates remain reviewable.

The CI matrix will cover Python 3.10, 3.11, 3.12, 3.13, and 3.14 because `pyproject.toml` declares `>=3.10` with no upper bound. A repository-configuration test will parse project metadata and workflow text to enforce:

- `pyproject.toml`, `.mcp.json`, server-reported versions, and release documentation all declare `4.0.1`;
- all GitHub Actions references use a 40-character SHA;
- the Python matrix contains every supported minor version; and
- community and container files required by this release exist.

The test is written and observed failing before the configuration changes are applied.

### Dependency and dead-code cleanup

`fastmcp>=0.4.1` will be removed from `pyproject.toml` because the code imports `FastMCP` from `mcp.server.fastmcp` and does not import the standalone `fastmcp` package. The `mcp` dependency remains. `src/pddl_mcp/errors.py` will be deleted because no source file or test imports its exception classes.

### Community files

`CODEOWNERS` will assign the repository to `@NBNBTM`. It documents ownership but will not be enforced as a mandatory self-review for a single-maintainer repository.

`CONTRIBUTING.md` will define the supported setup command, test commands, branch and PR expectations, security-reporting boundary, and requirement to avoid employer-confidential material and credentials.

`CODE_OF_CONDUCT.md` will use Contributor Covenant 3.0. Conduct reports will be directed to the maintainer through the private contact method available on the maintainer's GitHub profile; security vulnerabilities will continue to use private vulnerability reporting under `SECURITY.md`.

### MCP client quickstart

The existing external contribution in PR #9 will be reviewed first. If it uses the current MCP Python API, contains no secrets, and passes syntax and configuration tests, it will be merged to preserve contributor authorship. If its API is stale, the PR will receive a concrete explanation and the maintenance branch will provide a corrected minimal client under `examples/` with attribution in the PR or release notes.

The example must read configuration from environment or command-line arguments, invoke the local server through stdio, call `get_system_info` and `plan_from_text`, print structured JSON, and avoid embedded credentials or machine-specific paths.

### Docker support

PR #10 only changes README text and does not provide a Dockerfile, so it will not be merged as complete Docker support. The maintenance branch will add:

- a multi-stage or otherwise compact Python 3.14-compatible `Dockerfile`;
- `.dockerignore` excluding `.git`, `.env`, local outputs, reports, caches, and `.tools`;
- a container health/import check that does not require an LLM or Fast Downward; and
- README commands that distinguish the MCP server container from an optional externally mounted Fast Downward installation.

The image will not embed API keys or copy the local Fast Downward checkout. A local Docker build will be run when Docker is available; otherwise the Dockerfile will be syntax-checked and the limitation will be reported.

## GitHub Settings Design

### Ruleset

The active branch ruleset will target `~DEFAULT_BRANCH`, not `~ALL`. It will require:

- changes through a pull request;
- successful checks for `test (3.10)`, `test (3.11)`, `test (3.12)`, `test (3.13)`, `test (3.14)`, `docker`, and `Analyze Python`;
- the branch to be up to date with the default branch;
- resolution of review conversations;
- signed commits on the protected branch; and
- prevention of non-fast-forward updates.

The approval count remains zero because the repository has one maintainer and GitHub does not allow meaningful self-approval. Code-owner review enforcement will be disabled while `CODEOWNERS` remains informative. Repository administrators retain an emergency bypass; broad write/maintain-role bypasses will be removed when the API exposes their role identity unambiguously.

The required status checks will be added only after the new workflow has run and produced the exact check names.

### Actions and merge policy

After pinned workflows are merged, repository Actions permissions will be changed to:

- Actions enabled;
- only GitHub-owned Actions allowed;
- verified third-party Actions disabled;
- no additional action patterns; and
- full-SHA pinning required.

Default workflow token permissions remain read-only, and workflows cannot approve pull requests. Repository merge settings will keep squash merge and auto-merge, disable merge commits and rebase merges, delete merged branches, and allow maintainers to update pull-request branches.

### Security, Pages, and discovery

Dependabot security updates, secret scanning, push protection, private vulnerability reporting, CodeQL, and automated security fixes remain enabled. Secret-scanning validity checks and non-provider patterns will be enabled if GitHub accepts those settings for this public personal repository; unsupported settings will be recorded rather than worked around.

Pages remains deployed from `main:/docs` with HTTPS enforced. The current custom social preview remains in place. Topics will retain the current eight entries and add `mcp-server` and `model-context-protocol` for clearer discovery.

## Pull Request and Release Sequence

1. Review PR #9 independently and preserve its contributor attribution if it is usable.
2. Comment on and close PR #10 as incomplete Docker support; reference the superseding maintenance PR.
3. Push the maintenance branch and open one PR containing repository, workflow, community, Docker, and version changes.
4. Run local tests, GitHub CI, CodeQL, and any available Docker validation.
5. Merge through GitHub using squash merge so the protected-branch commit is GitHub-verified.
6. Apply the stricter Actions policy and default-branch ruleset after the pinned checks exist on `main`.
7. Re-run and verify CI, CodeQL, Pages, Dependabot, and security-alert state.
8. Create release `v4.0.1` at the final `main` commit with release notes covering maintenance, security, Docker, and contributor changes.
9. Fetch the final remote state locally and verify that local `main`, `origin/main`, the `v4.0.1` tag, and the release target all identify the intended commit.

## Failure and Rollback Strategy

All repository file changes are isolated on a branch until checks pass. GitHub settings are read before mutation and re-read afterward. Actions restrictions are applied only after workflows are SHA-pinned. Required checks are applied only after GitHub has registered their contexts. If a setting update is rejected, the previous settings remain active and the exact API response is reported.

The existing `v4.0.0` tag and release remain immutable historical references. No force push, history rewrite, or deletion of previous releases is part of this design.

## Acceptance Criteria

- Local tests, Ruff, and compile checks pass.
- The configuration policy test passes and detects a deliberately unpinned action during its red phase.
- The Docker image builds successfully when Docker is available, or the unavailable runtime is explicitly reported with static validation passing.
- The maintenance PR's five Python checks, Docker check, and CodeQL check pass.
- The default-branch ruleset requires those checks and applies only to `main`.
- GitHub Actions allows GitHub-owned actions only and requires full SHA references.
- Pages returns HTTP 200 over HTTPS and the custom social preview remains enabled.
- Open security alert counts remain zero.
- PR #9 and PR #10 are resolved with public explanations and appropriate attribution.
- `v4.0.1` is the latest non-draft, non-prerelease release and points to the final maintenance commit.
- Local `main` and `origin/main` are identical with no uncommitted tracked files.
