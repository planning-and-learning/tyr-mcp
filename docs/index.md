# pytyr-mcp Docs

Typed Python API with in-memory domains, task contexts, search results, and explicit result dumping.

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
- [`tyr.planning.prove_solvability`](tyr.planning.prove_solvability.md): raw-file workflow that writes artifacts directly
- [`tyr.planning.describe_generator`](tyr.planning.describe_generator.md)
- [`tyr.planning.sample_generator`](tyr.planning.sample_generator.md)

## Roles

- `planning/sample`: generator inspection and sampling workflows.
- `planning/solvability`: plan-finding workflow.
- `planning`: all planning workflows.
- `all`: all tools exposed by this package.

Slash roles also accept dotted aliases such as `planning.sample` and `planning.solvability`.
