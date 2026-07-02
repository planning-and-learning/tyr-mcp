# Contexts

Contexts keep parsed domain/task state reusable across planning calls.

## `create_domain_context`

```python
domain_context = create_domain_context(domain_file)
```

| Name | Type | Default | Description |
|---|---|---|---|
| `domain_file` | `str | Path` | required | Planning domain PDDL file; resolved to an absolute `Path`. |

Returns a `DomainContext`: parsed planning domain, reusable parser, and per-domain counters for tasks/results.

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Domain identifier, such as `domain_000001`. |
| `domain_file` | `Path` | Absolute domain file path. |
| `parser` | `Parser` | Reusable pytyr parser configured for the domain. |
| `planning_domain` | `PlanningDomain` | Parsed planning domain object. |

## `create_task_context`

```python
task_context = create_task_context(domain_context, problem_file, num_threads=1)
```

| Name | Type | Default | Description |
|---|---|---|---|
| `domain_context` | `DomainContext` | required | Parent domain context. |
| `problem_file` | `str | Path` | required | Problem PDDL file; resolved to an absolute `Path`. |
| `num_threads` | `int` | `1` | Underlying execution-context worker count. |

Returns a `TaskContext`: parent `DomainContext`, parsed problem, and pytyr task/search setup. Planning derives domain state from `task_context.domain_context`.

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Stable task ID such as `task_000001`. |
| `domain_context` | `DomainContext` | Parent domain context. |
| `index` | `int` | Per-domain task index. |
| `problem_file` | `Path` | Absolute problem file path. |
| `execution_context` | `ExecutionContext` | Shared pytyr/yggdrasil execution context. |
| `task` | `Task` | Lifted pytyr task. |

```python
domain = create_domain_context("domain.pddl")
task = create_task_context(domain, "p01.pddl")
result = find_satisficing_plan(task)
```
