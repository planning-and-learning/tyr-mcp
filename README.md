# pytyr-mcp

MCP server exposing pytyr planning tools for planning-and-learning agents.

## Roles

Set `PYTYR_MCP_ROLE` before launching the server. The server and invoke CLI fail closed when the role is missing, so restricted agents must be launched with an explicit role:

- `planning/sample`: generator inspection and sampling tools.
- `planning/solvability`: solvability proof tool.
- `planning`: both sampling and solvability planning tools.
- `all`: every pytyr MCP tool; use only for trusted, unrestricted local maintenance.

Slash roles also accept dotted aliases such as `planning.solvability`. The server rejects missing or unknown roles at startup.

## Output Contract

Sampling and solvability tools write layered artifacts under the requested `output_dir`. If that directory already contains output, the tool allocates a numbered child directory such as `run-002` instead of overwriting. Results include `primary` orchestration fields, a structured `summary`, and `items` with relative paths to generated tasks, invalid configs, or proof artifacts.
