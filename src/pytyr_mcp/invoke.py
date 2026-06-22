from __future__ import annotations

import argparse
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from collections.abc import Callable
from typing import TypeAlias

from pytyr_mcp.json_types import JsonObject, JsonValue
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


ToolResult: TypeAlias = JsonObject


class Args:
    def __init__(self, values: JsonObject) -> None:
        self.values = values

    def value(self, key: str, default: JsonValue | None = None) -> JsonValue | None:
        return self.values[key] if key in self.values else default

    def string(self, key: str, default: str | None = None) -> str:
        value = self.value(key, default)
        if not isinstance(value, str):
            raise TypeError(f"{key} must be a string")
        return value

    def integer(self, key: str, default: int) -> int:
        value = self.value(key, default)
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{key} must be an integer")
        return value

    def number(self, key: str, default: float) -> float:
        value = self.value(key, default)
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise TypeError(f"{key} must be a number")
        return float(value)

    def boolean(self, key: str, default: bool) -> bool:
        value = self.value(key, default)
        if not isinstance(value, bool):
            raise TypeError(f"{key} must be a boolean")
        return value

    def path(self, key: str) -> Path:
        return Path(self.string(key)).resolve()

    def configs(self, key: str) -> list[JsonObject]:
        value = self.value(key, [])
        if not isinstance(value, list):
            raise TypeError(f"{key} must be a list of objects")
        configs: list[JsonObject] = []
        for index, item in enumerate(value, start=1):
            if not isinstance(item, dict) or not all(isinstance(item_key, str) for item_key in item):
                raise TypeError(f"{key}[{index}] must be an object with string keys")
            configs.append(dict(item))
        return configs


ToolHandler: TypeAlias = Callable[[Args], ToolResult]


def _args(args: Args | JsonObject) -> Args:
    return args if isinstance(args, Args) else Args(args)


def _sample(args: Args | JsonObject) -> ToolResult:
    args = _args(args)
    result = sample_generator(
        SampleGeneratorOptions(
            domain_name=args.string("domain_name"),
            output_dir=args.path("output_dir"),
            batch_name=args.string("batch_name", "sample"),
            configs=args.configs("configs"),
            allow_invalid=args.boolean("allow_invalid", False),
        )
    )
    return sample_generator_result(result)


def _describe(args: Args | JsonObject) -> ToolResult:
    args = _args(args)
    domain_name = args.string("domain_name")
    return describe_generator_result(
        domain_name=domain_name,
        generator_path=get_generator_path(domain_name),
        signature=describe_make_problem(domain_name),
    )


def _solvability(args: Args | JsonObject) -> ToolResult:
    args = _args(args)
    return prove_solvability(
        ProveSolvabilityOptions(
            domain_file=args.string("domain_file"),
            problem_file=args.string("problem_file"),
            output_dir=args.string("output_dir"),
            num_threads=args.integer("num_threads", 1),
            max_num_states=args.integer("max_num_states", 100_000),
            max_time_seconds=args.number("max_time_seconds", 5.0),
            include_plans=args.boolean("include_plans", False),
        )
    )


TOOLS: dict[str, ToolHandler] = {
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
        result = TOOLS[parsed.tool](Args(args))
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
