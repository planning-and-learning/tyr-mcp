# pytyr-mcp

`pytyr-mcp` is a typed Python API for planning-and-learning agents. Callers keep parsed domains, task contexts, and search results in memory; filesystem artifacts are written only at the dump boundary.

Current release: `0.0.8`.

See [`docs/api.md`](docs/api.md) for the API and [`docs/index.md`](docs/index.md) for workflow/output docs.

## Basic Flow

```python
from pytyr_mcp import (
    DumpFormat,
    SearchBudget,
    create_domain_context,
    create_task_context,
    find_satisficing_plan,
)

domain = create_domain_context("domain.pddl")
task = create_task_context(domain, "problem.pddl")

result = find_satisficing_plan(task, search_budget=SearchBudget(100_000, 5.0))
dump = result.dump("artifacts/find-plan", formats=(DumpFormat.JSON,), include_plan_text=True)
```

## Entry Points

Context:

- `create_domain_context(domain_file)`
- `create_task_context(domain_context, problem_file, num_threads=1)`

Planning:

- `find_satisficing_plan(task_context, search_budget=PROVE_SEARCH_BUDGET)`

Dumping:

- `result.dump(...)`

Planning calls return typed result objects and do not write files.
