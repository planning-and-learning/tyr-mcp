from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pytyr_mcp.artifacts import fresh_output_dir


class DumpFormat(StrEnum):
    JSON = "json"
    MD = "md"


@dataclass(frozen=True, slots=True)
class DumpResult:
    output_dir: Path
    files: tuple[Path, ...]


def allocate_output_dir(output_dir: str | Path) -> Path:
    return fresh_output_dir(Path(output_dir).resolve())
