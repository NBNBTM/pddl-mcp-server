## Summary

Describe what changed and why.

## Type of Change

- [ ] Bug fix
- [ ] Feature
- [ ] Refactor
- [ ] Documentation
- [ ] Tests
- [ ] CI / repository maintenance

## Planning Impact

- [ ] Natural-language semantic parsing
- [ ] Knowledge/domain template matching
- [ ] PDDL generation
- [ ] Fast Downward execution
- [ ] Plan validation / response shape
- [ ] MCP server interface
- [ ] No runtime planning impact

## Validation

Run the relevant checks before requesting review:

```bash
python -m compileall -q src tests server.py
python -m pytest -q -p no:cacheprovider
python -m ruff check . --no-cache
```

## Security Checklist

- [ ] No `.env` file, API key, model token, planner credential, or generated private output is committed.
- [ ] Any new configuration is documented in `.env.example`.
- [ ] Generated artifacts remain under `output/` or another ignored directory.

## Notes

Add screenshots, planner logs, or example `PlanningResponse` output when the change affects user-visible behavior.
