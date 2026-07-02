# pytyr-mcp

`pytyr-mcp` is a typed Python API for planning-and-learning agents. Callers keep parsed domains, task contexts, search results, and generated sample metadata in memory; filesystem artifacts are written only at the dump boundary.

See [`docs/api.md`](docs/api.md) for the API and [`docs/index.md`](docs/index.md) for workflow/output docs.

## Basic Flow

```python
from pytyr_mcp import (
    create_domain_context,
    create_task_context,
    find_satisficing_plan,
)

domain = create_domain_context("domain.pddl")
task = create_task_context(domain, "problem.pddl")

result = find_satisficing_plan(task, max_time_seconds=5.0)
dump = result.dump("artifacts/find-plan", include_plan_text=True)
```

## Entry Points

Context:

- `create_domain_context(domain_file)`
- `create_task_context(domain_context, problem_file, num_threads=1)`

Planning:

- `find_satisficing_plan(task_context, max_num_states=100_000, max_time_seconds=5.0, ...)`

Dumping:

- `result.dump(output_dir, formats=(DumpFormat.JSON,), include_plan_text=False)`

Planning calls return typed result objects and do not write files.
