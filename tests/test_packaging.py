from __future__ import annotations

import tomllib
from pathlib import Path
from typing import cast

from pytyr_mcp.json_types import JsonObject


def _pyproject() -> JsonObject:
    return cast(
        JsonObject,
        tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()),
    )


def _project_table() -> JsonObject:
    project = _pyproject()["project"]
    if not isinstance(project, dict):
        raise TypeError("project table must be a mapping")
    return cast(JsonObject, project)


def test_package_has_no_console_scripts() -> None:
    assert "scripts" not in _project_table()
