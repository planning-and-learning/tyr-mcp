from __future__ import annotations

import json
from pathlib import Path
from pytyr_mcp.json_types import JsonObject, JsonValue
from pytyr_mcp.paths import relative_to


def write_json(path: Path, data: JsonValue) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2, sort_keys=True) + "\n")


RESERVATION_MARKER = ".pytyr-mcp-output"


def has_existing_output(output_dir: Path) -> bool:
    return any(
        (output_dir / name).exists()
        for name in (RESERVATION_MARKER, "summary.json", "summary.md", "raw", "task.json", "tasks", "domain.pddl")
    )


def _reserve_output_dir(output_dir: Path) -> bool:
    output_dir.mkdir(parents=True, exist_ok=True)
    if has_existing_output(output_dir):
        return False
    try:
        with (output_dir / RESERVATION_MARKER).open("x", encoding="utf-8") as fh:
            fh.write("reserved\n")
    except FileExistsError:
        return False
    return True


def fresh_output_dir(output_dir: Path) -> Path:
    if _reserve_output_dir(output_dir):
        return output_dir
    for index in range(2, 10000):
        candidate = output_dir / f"run-{index:03d}"
        if _reserve_output_dir(candidate):
            return candidate
    raise RuntimeError(f"could not allocate fresh Tyr MCP output directory under {output_dir}")


def _summary_task_path(task: JsonObject, output_dir: Path) -> str:
    raw_path = task.get("path")
    if raw_path is None:
        return ""
    path = Path(str(raw_path))
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.relative_to(output_dir).as_posix()
    except ValueError:
        return "<omitted: outside output_dir>"


def write_solvability_summary(
    *,
    tool: str,
    status: str,
    output_dir: Path,
    metadata: JsonObject,
    task: JsonObject,
    stdout: str = "",
    stderr: str = "",
) -> JsonObject:
    output_dir = fresh_output_dir(output_dir)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    with (raw_dir / "stdout.txt").open("x", encoding="utf-8") as fh:
        fh.write(stdout)
    with (raw_dir / "stderr.txt").open("x", encoding="utf-8") as fh:
        fh.write(stderr)

    task_data = dict(task)
    task_data["path"] = _summary_task_path(task, output_dir)
    task_data.setdefault("schema_version", 1)
    write_json(output_dir / "task.json", task_data)

    solved = bool(task.get("solved"))
    summary = {
        "schema_version": 1,
        "tool": tool,
        "status": status,
        "metadata": metadata,
        "task": {
            "name": task["name"],
            "status": task["status"],
            "solved": solved,
            "path": "task.json",
            "plan_length": task.get("plan_length"),
        },
        "raw": {
            "stdout_path": "raw/stdout.txt",
            "stderr_path": "raw/stderr.txt",
        },
    }
    write_json(output_dir / "summary.json", summary)
    write_solvability_markdown(output_dir / "summary.md", summary)
    artifacts = {
        "summary_json": relative_to(output_dir / "summary.json", output_dir),
        "summary_md": relative_to(output_dir / "summary.md", output_dir),
        "task_json": "task.json",
        "raw_stdout": "raw/stdout.txt",
        "raw_stderr": "raw/stderr.txt",
        "output_dir": output_dir.as_posix(),
    }
    prompt_summary = {
        "tool": tool,
        "status": status,
        "successful": status == "success",
        "output_dir": artifacts["output_dir"],
        "summary_json": artifacts["summary_json"],
        "summary_md": artifacts["summary_md"],
        "task_json": artifacts["task_json"],
        "task_name": task["name"],
        "task_status": task["status"],
        "solved": solved,
        "plan_length": task.get("plan_length"),
        "note": "Solvability details are written under output_dir; start with summary_md/summary_json.",
    }
    primary = {
        "successful": status == "success",
        "task_name": task["name"],
        "task_status": task["status"],
        "solved": solved,
        "plan_length": task.get("plan_length"),
        "prompt_summary": prompt_summary,
    }
    return {
        "schema_version": summary["schema_version"],
        "tool": tool,
        "status": status,
        "primary": primary,
        "summary": summary,
        "artifacts": artifacts,
        "prompt_summary": prompt_summary,
        "successful": status == "success",
        "task_name": task["name"],
        "task_status": task["status"],
        "solved": solved,
        "summary_path": artifacts["summary_json"],
        "summary_md_path": artifacts["summary_md"],
        "task_path": artifacts["task_json"],
        "output_dir": output_dir.as_posix(),
    }


def write_solvability_markdown(path: Path, summary: JsonObject) -> None:
    task = summary["task"]
    lines = [
        f"# {summary['tool']}",
        "",
        f"Status: `{summary['status']}`",
        "",
        "## Task",
        "",
        f"- Name: `{task['name']}`",
        f"- Search status: `{task['status']}`",
        f"- Solved: `{task['solved']}`",
        f"- Plan length: `{task['plan_length']}`",
        f"- Detail: `{task['path']}`",
    ]
    with path.open("x", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
