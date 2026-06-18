from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Callable

from pytyr_mcp.planning.sample_generator.results import describe_generator_result, sample_generator_result
from pytyr_mcp.planning.sample_generator.service import (
    SampleGeneratorOptions,
    describe_make_problem,
    get_generator_path,
    sample_generator,
)
from pytyr_mcp.planning.solvability.schemas import ProveSolvabilityOptions
from pytyr_mcp.planning.solvability.service import prove_solvability
from pytyr_mcp.roles import load_role


def _sample(args: dict[str, Any]) -> dict[str, Any]:
    result = sample_generator(
        SampleGeneratorOptions(
            domain_name=args["domain_name"],
            output_dir=Path(args["output_dir"]).resolve(),
            batch_name=args.get("batch_name", "sample"),
            configs=args.get("configs", []),
            allow_invalid=bool(args.get("allow_invalid", False)),
        )
    )
    return sample_generator_result(result)


def _describe(args: dict[str, Any]) -> dict[str, Any]:
    domain_name = args["domain_name"]
    return describe_generator_result(
        domain_name=domain_name,
        generator_path=get_generator_path(domain_name),
        signature=describe_make_problem(domain_name),
    )


def _solvability(args: dict[str, Any]) -> dict[str, Any]:
    return prove_solvability(
        ProveSolvabilityOptions(
            domain=args["domain"],
            problem_dir=args["problem_dir"],
            output_dir=args["output_dir"],
            num_threads=int(args.get("num_threads", 1)),
            max_num_states=int(args.get("max_num_states", 100_000)),
            max_time_seconds=float(args.get("max_time_seconds", args.get("max_time", 5.0))),
            include_plans=bool(args.get("include_plans", args.get("print_plan", False))),
        )
    )


TOOLS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "tyr.planning.describe_generator": _describe,
    "tyr.planning.sample_generator": _sample,
    "tyr.planning.prove_solvability": _solvability,
}


def _write_result_json(path: Path, rendered: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as fh:
        fh.write(rendered)


def _ensure_tool_allowed(tool_name: str) -> None:
    role = load_role()
    if role.allows(tool_name):
        return
    allowed = ", ".join(sorted(role.allowed_tools))
    raise PermissionError(
        f"{tool_name} is not allowed for PYTYR_MCP_ROLE={role.name}; "
        f"allowed tools: {allowed}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Invoke a pytyr-mcp tool with JSON arguments.")
    parser.add_argument("tool", choices=sorted(TOOLS))
    parser.add_argument("--args-json", required=True)
    parser.add_argument("--result-json")
    parsed = parser.parse_args()
    try:
        _ensure_tool_allowed(parsed.tool)
    except (PermissionError, ValueError) as exc:
        parser.error(str(exc))
    args = json.loads(parsed.args_json)
    if not isinstance(args, dict):
        raise TypeError("--args-json must decode to an object")
    captured_stdout = io.StringIO()
    with redirect_stdout(captured_stdout):
        result = TOOLS[parsed.tool](args)
    tool_stdout = captured_stdout.getvalue()
    if tool_stdout:
        result = {**result, "_tool_stdout": tool_stdout}
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if parsed.result_json:
        result_path = Path(parsed.result_json).resolve()
        _write_result_json(result_path, rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
