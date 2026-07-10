from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pytyr_mcp.artifacts import fresh_output_dir
from pytyr_mcp.enums import DumpFormat as DumpFormat


@dataclass(frozen=True, slots=True)
class DumpResult:
    output_dir: Path
    files: tuple[Path, ...]


def allocate_output_dir(output_dir: str | Path) -> Path:
    return fresh_output_dir(Path(output_dir).resolve())
