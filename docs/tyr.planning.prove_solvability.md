# tyr.planning.prove_solvability

Runs lifted GBFS lazy search with hFF on one PDDL problem and reports whether a plan was found. This workflow accepts raw file paths and writes artifacts directly.

A failed search does not prove unsolvability; it means no plan was found within the configured status/budgets.

## Arguments

| Name | Type | Default | Description |
|---|---|---|---|
| `domain_file` | `str` | required | Planning domain PDDL file. |
| `problem_file` | `str` | required | Problem PDDL file. |
| `output_dir` | `str` | required | Directory for normalized artifacts. |
| `num_threads` | `int` | `1` | Execution context thread count. |
| `max_num_states` | `int` | `100_000` | Search state budget. |
| `max_time_seconds` | `float` | `5.0` | Search wall-time budget in seconds. |
| `include_plans` | `bool` | `False` | Include textual plan in `task.json` when a plan is found. |

## Output Directory

```text
output_dir/
  .pytyr-mcp-output
  summary.json
  summary.md
  task.json
  raw/
    stdout.txt
    stderr.txt
```

If `output_dir` already contains MCP output, writes to `output_dir/run-002/`, then `run-003/`, etc.

## Result Object

`status` is `success` when a plan is found, otherwise `failure`. The immediate result contains orchestration fields; detailed data is in `summary.json` and `task.json`.

```json
{
  "schema_version": 1,
  "tool": "tyr.planning.prove_solvability",
  "status": "success|failure",
  "primary": {"successful": true, "task_status": "SOLVED", "solved": true},
  "summary": {"...": "same data written to summary.json"},
  "artifacts": {
    "summary_json": "<output-dir>/summary.json",
    "summary_md": "<output-dir>/summary.md",
    "task_json": "<output-dir>/task.json",
    "raw_stdout": "<output-dir>/raw/stdout.txt",
    "raw_stderr": "<output-dir>/raw/stderr.txt",
    "output_dir": "<output-dir>"
  }
}
```

`task.json` records task name/path, pytyr search status, `solved`, `plan_length`, `plan_cost`, and optional textual `plan`.
