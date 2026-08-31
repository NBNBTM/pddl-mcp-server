# Contributing to PDDL MCP Server

Thank you for helping improve PDDL MCP Server. Keep each change focused, reproducible, and safe for a public repository.

## Development setup

Use Python 3.10 or newer in a virtual environment, then install the package and development tools:

```bash
python -m pip install -e ".[dev]"
```

Run the same checks used by continuous integration before opening a pull request:

```bash
python -m pytest -q -p no:cacheprovider
python -m ruff check . --no-cache
python -m compileall -q src tests examples server.py
```

## Change workflow

1. Open or reference an issue before changing public behavior or adding a substantial feature.
2. Create one focused branch and pull request per change.
3. Add or update tests for behavior and configuration changes.
4. Keep the four public MCP tool interfaces backward compatible unless an issue explicitly approves a breaking change.
5. Use signed commits where possible. The repository uses squash merges, so write a clear pull request title and description.

## Public repository boundary

Never commit API keys, tokens, passwords, `.env` files, employer-confidential information, private model catalogs, local Fast Downward builds, generated planner output, or machine-specific paths. Use `.env.example` for documented configuration names and synthetic values only.

Do not include proprietary material from UniDT Co., Ltd. or any other employer. Contributions must be suitable for public release and must credit relevant sources.

## Pull requests

Describe the problem, the approach, and the verification performed. Keep unrelated formatting or refactoring out of the same pull request. Automated checks must pass before merge, and review conversations must be resolved.

## Security reports

Do not disclose security vulnerabilities in public issues. Follow the private reporting instructions in [SECURITY.md](SECURITY.md).
