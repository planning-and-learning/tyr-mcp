# tyr.planning.find_satisficing_plan

## Python Call

```python
result = find_satisficing_plan(
    task_context,
    search_budget=SearchBudget(100_000, 5.0),
)
```

Runs lifted GBFS lazy search with hFF on one parsed task and returns the first satisficing plan found within the budgets. The call is in-memory; dump explicitly when files are needed.

## Arguments

| Name | Type | Default | Description |
|---|---|---|---|
| `task_context` | `TaskContext` | required | Parsed task context returned by `create_task_context(...)`; contains its parent `DomainContext`. |
| `search_budget` | `SearchBudget` | `PROVE_SEARCH_BUDGET` | Search state and wall-time budget. Both fields must be non-`None`. |

## Result Object

Returns `FindSatisficingPlanResult`.

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Stable per-domain result ID such as `result_000001`. |
| `status` | `str` | `success` when a plan is found, otherwise `failure`. |
| `context` | `TaskContext` | Task context used for the search. |
| `search_status` | `SearchStatus` | Raw pytyr search status, such as `SOLVED` or `TIMEOUT`. |
| `solved` | `bool` | `True` when `search_status` is `SOLVED`. |
| `plan` | plan object or `None` | In-memory pytyr plan when found. |
| `plan_length` | `int | None` | Plan length when a plan exists. |
| `plan_cost` | `float | None` | Plan cost when a plan exists. |

## Dump Artifacts

```python
dump = result.dump(
    output_dir,
    formats=(DumpFormat.JSON, DumpFormat.MD),
    include_plan_text=True,
)
```

```text
output_dir/
  result.json
  task.json
  plan.txt      # only when include_plan_text=True and a plan exists
  summary.md    # only when DumpFormat.MD is requested
```

`task.json` records plan metadata, not the plan body:

| Field | Meaning |
|---|---|
| `status` | Raw pytyr search status, such as `SOLVED` or `TIMEOUT`. |
| `solved` | `true` when a plan was found. |
| `plan_length` | Number of plan steps, or `null` when no plan exists. |
| `plan_cost` | Plan cost, or `null` when no plan exists. |
| `plan_path` | Absolute path to `plan.txt`, or `null` when no plan file was written. |

`plan.txt` is the standard textual plan trace. It contains a metadata header, one block per step, and a `[facts]` section for the initial state and every successor state. `summary.md` includes a plan metadata table with task, search status, solved flag, length, cost, and plan file name.
