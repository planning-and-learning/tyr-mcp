from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pytyr_mcp.paths import relative_to
from pytyr_mcp.planning.sample_generator.service import SampleGeneratorResult


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _write_sample_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        f"# {summary['tool']}",
        "",
        f"Status: `{summary['status']}`",
        "",
        "## Counts",
        "",
        f"- Generated: {summary['counts']['generated']}",
        f"- Invalid: {summary['counts']['invalid']}",
        "",
        "## Generated Problems",
        "",
    ]
    if not summary["generated"]:
        lines.append("No generated problems.")
    for item in summary["generated"]:
        lines.append(f"- `{item['name']}`: `{item['path']}`")
    if summary["invalid"]:
        lines.extend(["", "## Invalid Configs", ""])
        for item in summary["invalid"]:
            lines.append(f"- index {item['index']}: {item['reason']}")
    with path.open("x", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")


def describe_generator_result(*, domain_name: str, generator_path: Path, signature: str) -> dict[str, Any]:
    primary = {
        "successful": True,
        "domain_name": domain_name,
        "generator_path": generator_path.as_posix(),
        "signature": signature,
    }
    return {
        "schema_version": 1,
        "tool": "tyr.planning.describe_generator",
        "status": "success",
        "primary": primary,
        "summary": {
            "schema_version": 1,
            "tool": "tyr.planning.describe_generator",
            "status": "success",
            "domain_name": domain_name,
            "generator_path": generator_path.as_posix(),
            "signature": signature,
        },
        "items": [],
        "artifacts": {"generator_path": generator_path.as_posix()},
        "domain_name": domain_name,
        "generator_path": generator_path.as_posix(),
        "signature": signature,
    }


def sample_generator_result(result: SampleGeneratorResult) -> dict[str, Any]:
    output_dir = result.domain_path.parent
    generated = [
        {
            "kind": "generated_problem",
            "index": item.index,
            "name": item.path.name,
            "path": relative_to(item.path, output_dir),
            "config": item.config,
        }
        for item in result.generated
    ]
    invalid = [
        {
            "kind": "invalid_config",
            "index": item.index,
            "config": item.config,
            "reason": item.reason,
        }
        for item in result.invalid
    ]
    status = "success" if result.is_successful else "failure"
    primary = {
        "successful": result.is_successful,
        "domain_path": result.domain_path.as_posix(),
        "problem_dir": result.problem_dir.as_posix(),
        "generator_path": result.generator_path.as_posix(),
        "signature": result.signature,
        "generated_count": len(generated),
        "invalid_count": len(invalid),
    }
    summary = {
        "schema_version": 1,
        "tool": "tyr.planning.sample_generator",
        "status": status,
        "domain_path": result.domain_path.as_posix(),
        "problem_dir": result.problem_dir.as_posix(),
        "generator_path": result.generator_path.as_posix(),
        "signature": result.signature,
        "counts": {"generated": len(generated), "invalid": len(invalid)},
        "generated": generated,
        "invalid": invalid,
    }
    summary_json = output_dir / "summary.json"
    summary_md = output_dir / "summary.md"
    _write_json(summary_json, summary)
    _write_sample_markdown(summary_md, summary)
    artifacts = {
        "domain_path": result.domain_path.as_posix(),
        "problem_dir": result.problem_dir.as_posix(),
        "generator_path": result.generator_path.as_posix(),
        "summary_json": relative_to(summary_json, output_dir),
        "summary_md": relative_to(summary_md, output_dir),
        "configs_json": relative_to(result.problem_dir / "configs.json", output_dir),
        "output_dir": output_dir.as_posix(),
    }
    return {
        "schema_version": 1,
        "tool": "tyr.planning.sample_generator",
        "status": status,
        "primary": primary,
        "summary": summary,
        "artifacts": artifacts,
        "items": generated,
        "diagnostics": invalid,
        "counts": summary["counts"],
        "summary_path": artifacts["summary_json"],
        "summary_md_path": artifacts["summary_md"],
        "output_dir": artifacts["output_dir"],
        "domain_path": result.domain_path.as_posix(),
        "problem_dir": result.problem_dir.as_posix(),
        "generator_path": result.generator_path.as_posix(),
        "signature": result.signature,
        "generated": generated,
        "invalid": invalid,
    }
