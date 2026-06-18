from __future__ import annotations

import asyncio

import pytest

from pytyr_mcp.config import ServerConfig
from pytyr_mcp.roles import (
    PLANNING_SAMPLE_TOOLS,
    PLANNING_SOLVABILITY_TOOLS,
    PLANNING_TOOLS,
    ALL_TOOLS,
    Role,
    load_role,
)
from pytyr_mcp.server import create_server


def _config(tmp_path):
    return ServerConfig(workspace_root=tmp_path, output_root=tmp_path / "out")


def _tool_names(server) -> set[str]:
    return {tool.name for tool in asyncio.run(server.list_tools())}


@pytest.mark.parametrize(
    ("role_name", "allowed"),
    [
        ("planning", PLANNING_TOOLS),
        ("planning/sample", PLANNING_SAMPLE_TOOLS),
        ("planning/solvability", PLANNING_SOLVABILITY_TOOLS),
    ],
)
def test_create_server_registers_only_role_tools(tmp_path, role_name, allowed):
    server = create_server(
        config=_config(tmp_path),
        role=Role(name=role_name, allowed_tools=allowed),
    )

    assert _tool_names(server) == set(allowed) | {"pytyr_mcp.server_info"}


def test_all_role_exposes_every_declared_tool(tmp_path):
    server = create_server(
        config=_config(tmp_path),
        role=Role(name="all", allowed_tools=ALL_TOOLS),
    )

    assert _tool_names(server) == set(ALL_TOOLS) | {"pytyr_mcp.server_info"}


def test_load_role_accepts_aliases(monkeypatch):
    monkeypatch.setenv("PYTYR_MCP_ROLE", "planning.solvability")

    role = load_role()

    assert role.name == "planning.solvability"
    assert role.allowed_tools == PLANNING_SOLVABILITY_TOOLS


def test_load_role_requires_explicit_env(monkeypatch):
    monkeypatch.delenv("PYTYR_MCP_ROLE", raising=False)

    with pytest.raises(ValueError, match="Tyr MCP role is required"):
        load_role()


def test_load_role_rejects_unknown(monkeypatch):
    monkeypatch.setenv("PYTYR_MCP_ROLE", "unknown")

    with pytest.raises(ValueError, match="Unknown PYTYR_MCP_ROLE"):
        load_role()


def test_invoke_rejects_tool_outside_role(monkeypatch):
    from pytyr_mcp.invoke import _ensure_tool_allowed

    monkeypatch.setenv("PYTYR_MCP_ROLE", "planning/solvability")

    with pytest.raises(PermissionError, match="not allowed"):
        _ensure_tool_allowed("tyr.planning.sample_generator")


def test_invoke_allows_tool_inside_role(monkeypatch):
    from pytyr_mcp.invoke import _ensure_tool_allowed

    monkeypatch.setenv("PYTYR_MCP_ROLE", "planning/solvability")

    _ensure_tool_allowed("tyr.planning.prove_solvability")

