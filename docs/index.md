# pytyr-mcp Docs

Typed Python API with caller-managed domains, task contexts, search results, and explicit result dumping.

Current release: `0.0.8`.

## Current Interface

- [Python API](api.md)
- [Contexts](context.md): `create_domain_context(...)`, `create_task_context(...)`
- [Dumping](dumping.md): result `dump(...)`, `DumpFormat`, `DumpResult`
- [Find Satisficing Plan](tyr.planning.find_satisficing_plan.md): `find_satisficing_plan(...)`

```python
from pytyr_mcp import (
    create_domain_context,
    create_task_context,
    find_satisficing_plan,
)

domain = create_domain_context("domain.pddl")
task = create_task_context(domain, "problem.pddl")
result = find_satisficing_plan(task)
dump = result.dump("artifacts/find-plan")
```

Planning returns typed result objects. Dump only when another process needs files.

## Workflow Reference

- [`tyr.planning.find_satisficing_plan`](tyr.planning.find_satisficing_plan.md): `find_satisficing_plan(...)`, optional `result.dump(...)`
