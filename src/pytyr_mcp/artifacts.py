from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pytyr_mcp.paths import relative_to


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_solvability_summary(
    *,
    tool: str,
    status: str,
    output_dir: Path,
    metadata: dict[str, Any],
    tasks: list[dict[str, Any]],
    stdout: str = "",
    stderr: str = "",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
    (raw_dir / "stderr.txt").write_text(stderr, encoding="utf-8")

    by_status: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        by_status.setdefault(str(task["status"]), []).append(task)

    task_dir = output_dir / "tasks"
    task_items = []
    for index, task in enumerate(tasks, start=1):
        task_id = f"task-{index:03d}"
        task_path = task_dir / f"{task_id}.json"
        task_data = dict(task)
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
                        "path": task["path"],
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
    primary = {
        "successful": status == "success",
        "all_solved": status == "success",
        "solved": [task["name"] for task in tasks if task.get("solved")],
        "unsolved": [task["name"] for task in tasks if not task.get("solved")],
        "task_statuses": [(task["name"], task["status"]) for task in tasks],
    }
    artifacts = {
        "summary_json": relative_to(output_dir / "summary.json", output_dir),
        "summary_md": relative_to(output_dir / "summary.md", output_dir),
        "raw_stdout": "raw/stdout.txt",
        "raw_stderr": "raw/stderr.txt",
        "output_dir": output_dir.as_posix(),
    }
    return {
        "schema_version": summary["schema_version"],
        "tool": tool,
        "status": status,
        "primary": primary,
        "summary": summary,
        "artifacts": artifacts,
        "items": task_items,
        "tasks": summary["tasks"],
        "summary_path": artifacts["summary_json"],
        "summary_md_path": artifacts["summary_md"],
        "output_dir": output_dir.as_posix(),
        "counts": summary["counts"],
        "by_status": summary["by_status"],
    }


def write_solvability_markdown(path: Path, summary: dict[str, Any]) -> None:
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
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
