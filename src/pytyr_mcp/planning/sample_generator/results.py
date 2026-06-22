from __future__ import annotations

import json
from pathlib import Path

from pytyr_mcp.json_types import JsonDictList, JsonObject, JsonValue
from pytyr_mcp.planning.sample_generator.service import SampleGeneratorResult


def _write_json(path: Path, data: JsonValue) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _write_sample_markdown(path: Path, summary: JsonObject) -> None:
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


def describe_generator_result(*, domain_name: str, generator_path: Path, signature: str) -> JsonObject:
    prompt_summary = {
        "tool": "tyr.planning.describe_generator",
        "status": "success",
        "successful": True,
        "domain_name": domain_name,
        "generator_path": generator_path.as_posix(),
        "signature": signature,
    }
    primary = {
        "successful": True,
        "domain_name": domain_name,
        "generator_path": generator_path.as_posix(),
        "signature": signature,
        "prompt_summary": prompt_summary,
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
        "prompt_summary": prompt_summary,
        "domain_name": domain_name,
        "generator_path": generator_path.as_posix(),
        "signature": signature,
    }


def sample_generator_result(result: SampleGeneratorResult) -> JsonObject:
    output_dir = result.domain_path.parent
    generated: JsonDictList = [
        {
            "kind": "generated_problem",
            "index": item.index,
            "name": item.path.name,
            "path": item.path.resolve().as_posix(),
            "config": item.config,
        }
        for item in result.generated
    ]
    invalid: JsonDictList = [
        {
            "kind": item.error_category,
            "index": item.index,
            "config": item.config,
            "reason": item.reason,
            "error_type": item.error_type,
            "error_category": item.error_category,
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
        "summary_json": summary_json.resolve().as_posix(),
        "summary_md": summary_md.resolve().as_posix(),
        "configs_json": (result.problem_dir / "configs.json").resolve().as_posix(),
        "output_dir": output_dir.resolve().as_posix(),
    }
    prompt_summary = {
        "tool": "tyr.planning.sample_generator",
        "status": status,
        "successful": result.is_successful,
        "output_dir": artifacts["output_dir"],
        "summary_json": artifacts["summary_json"],
        "summary_md": artifacts["summary_md"],
        "domain_path": artifacts["domain_path"],
        "problem_dir": artifacts["problem_dir"],
        "counts": summary["counts"],
        "generated": [item["name"] for item in generated],
        "invalid_count": len(invalid),
        "note": "Generated PDDL tasks and configs are written under problem_dir; start with summary_md/summary_json.",
    }
    primary["prompt_summary"] = prompt_summary
    return {
        "schema_version": 1,
        "tool": "tyr.planning.sample_generator",
        "status": status,
        "primary": primary,
        "summary": summary,
        "artifacts": artifacts,
        "prompt_summary": prompt_summary,
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
