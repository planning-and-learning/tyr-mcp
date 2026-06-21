from __future__ import annotations

import json
from pathlib import Path
from pytyr_mcp.json_types import JsonDictList, JsonObject, JsonValue
from pytyr_mcp.paths import relative_to


def write_json(path: Path, data: JsonValue) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2, sort_keys=True) + "\n")


RESERVATION_MARKER = ".pytyr-mcp-output"


def has_existing_output(output_dir: Path) -> bool:
    return any(
        (output_dir / name).exists()
        for name in (RESERVATION_MARKER, "summary.json", "summary.md", "raw", "tasks", "domain.pddl")
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
    tasks: JsonDictList,
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

    by_status: dict[str, JsonDictList] = {}
    for task in tasks:
        by_status.setdefault(str(task["status"]), []).append(task)

    task_dir = output_dir / "tasks"
    task_items: JsonDictList = []
    for index, task in enumerate(tasks, start=1):
        task_id = f"task-{index:03d}"
        task_path = task_dir / f"{task_id}.json"
        task_data = dict(task)
        task_data["path"] = _summary_task_path(task, output_dir)
        task_data.setdefault("schema_version", 1)
        task_data.setdefault("id", task_id)
        write_json(task_path, task_data)
        task_items.append(
            {
                "id": task_id,
                "name": task["name"],
                "status": task["status"],
                "path": relative_to(task_path, output_dir),
            }
        )

    summary = {
        "schema_version": 1,
        "tool": tool,
        "status": status,
        "metadata": metadata,
        "counts": {
            "tasks": len(tasks),
            "solved": sum(1 for task in tasks if task.get("solved")),
            "unsolved": sum(1 for task in tasks if not task.get("solved")),
            "statuses": len(by_status),
        },
        "by_status": {
            status_name: {
                "count": len(values),
                "tasks": [
                    {
                        "name": task["name"],
                        "path": _summary_task_path(task, output_dir),
                        "plan_length": task.get("plan_length"),
                    }
                    for task in values
                ],
            }
            for status_name, values in sorted(by_status.items())
        },
        "tasks": task_items,
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
        "raw_stdout": "raw/stdout.txt",
        "raw_stderr": "raw/stderr.txt",
        "output_dir": output_dir.as_posix(),
    }
    task_statuses = [(task["name"], task["status"]) for task in tasks]
    prompt_summary = {
        "tool": tool,
        "status": status,
        "successful": status == "success",
        "output_dir": output_dir.as_posix(),
        "summary_json": artifacts["summary_json"],
        "summary_md": artifacts["summary_md"],
        "counts": summary["counts"],
        "task_statuses": task_statuses,
        "solved": [task["name"] for task in tasks if task.get("solved")],
        "unsolved": [task["name"] for task in tasks if not task.get("solved")],
        "note": "Detailed per-task solvability records are written under output_dir; start with summary_md/summary_json.",
    }
    primary = {
        "successful": status == "success",
        "all_solved": status == "success",
        "solved": prompt_summary["solved"],
        "unsolved": prompt_summary["unsolved"],
        "task_statuses": task_statuses,
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
        "items": task_items,
        "tasks": summary["tasks"],
        "summary_path": artifacts["summary_json"],
        "summary_md_path": artifacts["summary_md"],
        "output_dir": output_dir.as_posix(),
        "counts": summary["counts"],
        "by_status": summary["by_status"],
    }


def write_solvability_markdown(path: Path, summary: JsonObject) -> None:
    lines = [
        f"# {summary['tool']}",
        "",
        f"Status: `{summary['status']}`",
        "",
        "## Counts",
        "",
        f"- Tasks: {summary['counts']['tasks']}",
        f"- Solved: {summary['counts']['solved']}",
        f"- Unsolved: {summary['counts']['unsolved']}",
        "",
        "## Tasks",
        "",
    ]
    for item in summary["tasks"]:
        lines.append(f"- `{item['name']}`: `{item['status']}` (`{item['path']}`)")
    with path.open("x", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
