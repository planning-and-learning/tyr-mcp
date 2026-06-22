# tyr.planning.describe_generator

Returns the source path and Python `make_problem` signature for a benchmark generator.

## Arguments

| Name | Type | Default | Description |
|---|---:|---:|---|
| `domain_name` | string | required | Name of the classical planning benchmark generator under `generators/classical/<domain_name>/generator.py`. |

## Output

This tool does not use `output_dir` and writes no artifacts.

```json
{
  "schema_version": 1,
  "tool": "tyr.planning.describe_generator",
  "status": "success",
  "primary": {
    "successful": true,
    "domain_name": "<domain-name>",
    "generator_path": "<path>/generator.py",
    "signature": "(param: 'type', ...) -> 'str | None'"
  },
  "summary": {
    "schema_version": 1,
    "tool": "tyr.planning.describe_generator",
    "status": "success",
    "domain_name": "<domain-name>",
    "generator_path": "<path>/generator.py",
    "signature": "(param: 'type', ...) -> 'str | None'"
  },
  "artifacts": {
    "generator_path": "<path>/generator.py"
  },
  "items": []
}
```
