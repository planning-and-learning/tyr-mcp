from __future__ import annotations

import json
from pathlib import Path

from pytyr_mcp.defaults import RESERVATION_MARKER
from pytyr_mcp.json_types import JsonValue


def write_json(path: Path, data: JsonValue) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2, sort_keys=True) + "\n")


def has_existing_output(output_dir: Path) -> bool:
    return any(
        (output_dir / name).exists()
        for name in (
            RESERVATION_MARKER,
            "summary.json",
            "summary.md",
            "task.json",
            "tasks",
            "domain.pddl",
        )
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
    raise RuntimeError(f"could not allocate fresh pytyr output directory under {output_dir}")
