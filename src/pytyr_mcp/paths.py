from __future__ import annotations

from pathlib import Path


def server_output_dir(output_root: Path, output_dir: str | Path) -> Path:
    root = output_root.resolve()
    requested = Path(output_dir)
    resolved = requested.resolve() if requested.is_absolute() else (root / requested).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"output_dir must resolve under configured output_root: {root}") from exc
    return resolved


def relative_to(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
