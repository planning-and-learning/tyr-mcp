# tyr.planning.sample_generator

Generates PDDL sample problems from a benchmark generator's `make_problem(**config)` function.

## Arguments

| Name | Type | Default | Description |
|---|---:|---:|---|
| `domain_name` | string | required | Name of the classical planning benchmark generator. |
| `output_dir` | string | required | Directory for generated domain/problem files and summaries. |
| `batch_name` | string | required | Batch directory and generated problem filename prefix. Invalid filename characters are replaced by `_`. |
| `configs` | array of objects | required | Generator keyword argument objects, one per requested problem. |
| `allow_invalid` | boolean | `false` | If `false`, stop after the first invalid config. If `true`, keep trying later configs and report all invalid configs. |

## Output Directory

```text
output_dir/
  .pytyr-mcp-output
  domain.pddl
  summary.json
  summary.md
  <batch-name>/
    configs.json
    <batch-name>-001.pddl
    <batch-name>-002.pddl
    ...
```

If `output_dir` already contains MCP output, the same structure is written under `output_dir/run-002/`, then `run-003/`, etc.

If `<batch-name>/` already exists inside the selected output directory, the batch is written to `<batch-name>-002/`, then `<batch-name>-003/`, etc.

## Result Object

`status` is `success` when no config failed. It is `failure` when at least one invalid config or generator error was observed.

```json
{
  "schema_version": 1,
  "tool": "tyr.planning.sample_generator",
  "status": "success|failure",
  "primary": {
    "successful": true,
    "domain_path": "<output-dir>/domain.pddl",
    "problem_dir": "<output-dir>/<batch-name>",
    "generator_path": "<path>/generator.py",
    "signature": "(param: 'type', ...) -> 'str | None'",
    "generated_count": 2,
    "invalid_count": 0
  },
  "summary": {
    "schema_version": 1,
    "tool": "tyr.planning.sample_generator",
    "status": "success|failure",
    "counts": {"generated": 2, "invalid": 0},
    "generated": [
      {
        "kind": "generated_problem",
        "index": 1,
        "name": "<batch-name>-001.pddl",
        "path": "<batch-name>/<batch-name>-001.pddl",
        "config": {}
      }
    ],
    "invalid": []
  },
  "artifacts": {
    "domain_path": "<output-dir>/domain.pddl",
    "problem_dir": "<output-dir>/<batch-name>",
    "summary_json": "summary.json",
    "summary_md": "summary.md",
    "configs_json": "<batch-name>/configs.json",
    "output_dir": "<output-dir>"
  },
  "items": [
    {
      "kind": "generated_problem",
      "index": 1,
      "name": "<batch-name>-001.pddl",
      "path": "<batch-name>/<batch-name>-001.pddl",
      "config": {}
    }
  ],
  "diagnostics": []
}
```

Invalid config diagnostics have this shape:

```json
{
  "kind": "invalid_config|generator_error",
  "index": 1,
  "config": {},
  "reason": "<exception message>",
  "error_type": "TypeError|ValueError|...",
  "error_category": "invalid_config|generator_error"
}
```
