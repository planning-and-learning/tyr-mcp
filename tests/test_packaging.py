from __future__ import annotations

import tomllib
from pathlib import Path

import pytest


def _pyproject() -> dict:
    return tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())


def test_console_scripts_are_declared() -> None:
    scripts = _pyproject()["project"]["scripts"]
    assert scripts == {
        "pytyr-mcp": "pytyr_mcp.server:main",
        "pytyr-mcp-invoke": "pytyr_mcp.invoke:main",
    }


def test_invoke_result_json_writer_does_not_overwrite(tmp_path) -> None:
    from pytyr_mcp.invoke import _write_result_json

    result_json = tmp_path / "nested" / "result.json"
    _write_result_json(result_json, "first\n")

    with pytest.raises(FileExistsError):
        _write_result_json(result_json, "second\n")

    assert result_json.read_text(encoding="utf-8") == "first\n"


def test_invoke_role_requires_explicit_env(monkeypatch) -> None:
    from pytyr_mcp.invoke import _ensure_tool_allowed

    monkeypatch.delenv("PYTYR_MCP_ROLE", raising=False)

    with pytest.raises(ValueError, match="Tyr MCP role is required"):
        _ensure_tool_allowed("missing.role.check")


def test_invoke_role_allows_declared_tool(monkeypatch) -> None:
    from pytyr_mcp.invoke import _ensure_tool_allowed

    monkeypatch.setenv("PYTYR_MCP_ROLE", "planning/solvability")

    _ensure_tool_allowed("tyr.planning.prove_solvability")


def test_invoke_role_rejects_disallowed_tool(monkeypatch) -> None:
    from pytyr_mcp.invoke import _ensure_tool_allowed

    monkeypatch.setenv("PYTYR_MCP_ROLE", "planning/solvability")

    with pytest.raises(PermissionError, match="not allowed"):
        _ensure_tool_allowed("tyr.planning.sample_generator")
