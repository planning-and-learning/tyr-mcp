# tyr.planning.prove_solvability

Runs lifted GBFS lazy search with hFF on one PDDL problem and reports whether the task is solvable.

## Arguments

| Name | Type | Default | Description |
|---|---:|---:|---|
| `domain_file` | string | required | Path to the planning domain PDDL file. |
| `problem_file` | string | required | Path to the problem PDDL file. |
| `output_dir` | string | required | Directory for normalized solvability artifacts. |
| `num_threads` | integer | `1` | Execution context thread count. |
| `max_num_states` | integer | `100000` | Search state budget. |
| `max_time_seconds` | number | `5.0` | Search wall-time budget in seconds. |
| `include_plans` | boolean | `false` | Include the textual plan in `task.json` when a plan is found. |

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

If `output_dir` already contains MCP output, the same structure is written under `output_dir/run-002/`, then `run-003/`, etc.

## Result Object

`status` is `success` when the task is solved. Otherwise it is `failure`. The immediate result is intentionally compact; detailed structured data lives in `summary.json` and `task.json`.

```json
{
  "schema_version": 1,
  "tool": "tyr.planning.prove_solvability",
  "status": "success|failure",
  "successful": true,
  "task_name": "p01.pddl",
  "task_status": "SOLVED",
  "solved": true,
  "artifacts": {
    "summary_json": "summary.json",
    "summary_md": "summary.md",
    "task_json": "task.json",
    "raw_stdout": "raw/stdout.txt",
    "raw_stderr": "raw/stderr.txt",
    "output_dir": "<output-dir>"
  },
  "summary_path": "summary.json",
  "summary_md_path": "summary.md",
  "task_path": "task.json",
  "output_dir": "<output-dir>"
}
```

`summary.json` contains invocation metadata and the compact task index:

```json
{
  "schema_version": 1,
  "tool": "tyr.planning.prove_solvability",
  "status": "success|failure",
  "metadata": {
    "domain_file": "<domain.pddl>",
    "problem_file": "<problem.pddl>",
    "num_threads": 1,
    "max_num_states": 100000,
    "max_time_seconds": 5.0,
    "include_plans": false
  },
  "task": {
    "name": "p01.pddl",
    "status": "SOLVED",
    "solved": true,
    "path": "task.json",
    "plan_length": 2
  },
  "raw": {"stdout_path": "raw/stdout.txt", "stderr_path": "raw/stderr.txt"}
}
```

`task.json` contains the detailed result:

```json
{
  "schema_version": 1,
  "name": "p01.pddl",
  "path": "<problem path or omitted marker>",
  "status": "SOLVED|TIMEOUT|...",
  "solved": true,
  "plan_length": 2,
  "plan_cost": 2.0,
  "plan": null
}
```
