# Python API

Typed API for keeping parsing, task setup, search results, and dump decisions in memory.

```text
src/pytyr_mcp/
  context.py          # DomainContext and TaskContext
  dumping.py          # DumpFormat and DumpResult
  planning/search.py  # find_satisficing_plan and result type
  __init__.py         # public convenience exports
```

Callers own all state. `TaskContext` stores the `DomainContext` that created it. Planning calls do not write artifacts; result objects dump themselves later.

## Typical Flow

```python
from pytyr_mcp import (
    DumpFormat,
    create_domain_context,
    create_task_context,
    find_satisficing_plan,
)

domain = create_domain_context("domain.pddl")
task = create_task_context(domain, "problem.pddl")
result = find_satisficing_plan(task, max_num_states=100_000, max_time_seconds=5.0)

if result.solved:
    plan = result.plan

dump = result.dump(
    "artifacts/find-plan",
    formats=(DumpFormat.JSON, DumpFormat.MD),
    include_plan_text=True,
)
```

## References

- [Contexts](context.md): `create_domain_context(...)`, `create_task_context(...)`
- [Dumping](dumping.md): result `dump(...)`, `DumpFormat`, `DumpResult`
- [Find Satisficing Plan](tyr.planning.find_satisficing_plan.md): current planning call

## Planning

- `find_satisficing_plan(task_context, max_num_states=100_000, max_time_seconds=5.0, ...)`

`find_satisficing_plan(...)` runs lifted GBFS lazy search with hFF. Success means a satisficing plan was found; failure means no plan was found within the search status/budgets.

Every result includes `id`, `status`, raw pytyr `search_status`, `TaskContext`, `solved`, optional in-memory `plan`, optional `plan_length`/`plan_cost`, and `dump(...)`.

## Dumping

```python
dump = result.dump("artifacts/find-plan", formats=(DumpFormat.JSON,))
```

Typed task/search/plan data stays in memory; strings/files are produced at dump/output boundaries.
