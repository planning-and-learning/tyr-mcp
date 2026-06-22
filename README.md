# pytyr-mcp

MCP server exposing pytyr planning tools for planning-and-learning agents.

## Roles

Set `PYTYR_MCP_ROLE` before launching the server. The server and invoke CLI fail closed when the role is missing, so restricted agents must be launched with an explicit role:

- `planning/sample`: generator inspection and sampling tools.
- `planning/solvability`: solvability proof tool.
- `planning`: both sampling and solvability planning tools.
- `all`: every pytyr MCP tool; use only for trusted, unrestricted local maintenance.

Slash roles also accept dotted aliases such as `planning.solvability`. The server rejects missing or unknown roles at startup.

## Tool Documentation

Per-tool calling arguments and normalized output structures are documented in [`docs/index.md`](docs/index.md). The individual tool pages cover:

- `tyr.planning.describe_generator`
- `tyr.planning.sample_generator`
- `tyr.planning.prove_solvability`

Start with the index for shared output directory conventions. The per-tool pages give the exact argument names and artifact trees.

## Output Contract

Sampling and solvability tools write layered artifacts under the requested `output_dir`. If that directory already contains output, the tool allocates a numbered child directory such as `run-002` instead of overwriting.

Sampling writes a copied `domain.pddl`, a generated problem batch directory, `summary.json`, and `summary.md`. Solvability is single-task: it writes `task.json`, `summary.json`, `summary.md`, and raw stdout/stderr logs. Results include `primary` orchestration fields, a structured `summary`, and `artifacts` with relative paths to written files. List-producing tools, such as sampling, also expose `items`. See [`docs/index.md`](docs/index.md) for shared conventions and the per-tool pages for argument tables.

