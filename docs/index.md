# pytyr-mcp Tool Docs

This directory documents the JSON calling arguments and normalized output structure for each exposed `pytyr-mcp` planning tool.

## Tools

- [`tyr.planning.describe_generator`](tyr.planning.describe_generator.md)
- [`tyr.planning.sample_generator`](tyr.planning.sample_generator.md)
- [`tyr.planning.prove_solvability`](tyr.planning.prove_solvability.md)

## Roles

Tools are role-gated by `PYTYR_MCP_ROLE`:

- `planning/sample`: `tyr.planning.describe_generator`, `tyr.planning.sample_generator`
- `planning/solvability`: `tyr.planning.prove_solvability`
- `planning`: all planning tools
- `all`: all tools exposed by this server

Slash roles also accept dotted aliases such as `planning.sample` and `planning.solvability`.

## Shared Output Conventions

All paths are strings. Tools that write artifacts require an `output_dir`. A tool invocation reserves that directory if it is empty; if it already contains prior MCP output, the tool writes to `run-002`, `run-003`, etc. under it.

Tool results always contain `schema_version`, `tool`, `status`, and `artifacts`. `summary.md` is the human-readable entry point. `summary.json` is the structured entry point. Artifact paths are relative to the selected output directory whenever possible. Tools that naturally produce multiple records, such as `tyr.planning.sample_generator`, also expose an `items` list.
