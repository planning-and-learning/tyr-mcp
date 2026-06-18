from __future__ import annotations

import pytest

from pytyr_mcp.config import ServerConfig
from pytyr_mcp.paths import server_output_dir
from pytyr_mcp.planning.sample_generator import tools as sample_tools


class FakeMCP:
    def __init__(self) -> None:
        self.tools = {}

    def tool(self, *, name: str):
        def decorator(fn):
            self.tools[name] = fn
            return fn

        return decorator


def test_server_output_dir_places_relative_paths_under_output_root(tmp_path):
    output_root = tmp_path / "mcp-output"

    assert server_output_dir(output_root, "samples/run") == output_root.resolve() / "samples" / "run"


def test_server_output_dir_accepts_absolute_paths_inside_output_root(tmp_path):
    output_root = tmp_path / "mcp-output"
    requested = output_root / "samples" / "run"

    assert server_output_dir(output_root, requested) == requested.resolve()


def test_server_output_dir_rejects_escape_paths(tmp_path):
    output_root = tmp_path / "mcp-output"

    with pytest.raises(ValueError):
        server_output_dir(output_root, "../outside")

    with pytest.raises(ValueError):
        server_output_dir(output_root, tmp_path / "outside")


def test_registered_sample_tool_constrains_output_dir(monkeypatch, tmp_path):
    output_root = tmp_path / "mcp-output"
    config = ServerConfig(workspace_root=tmp_path, output_root=output_root)
    mcp = FakeMCP()
    captured = {}

    def fake_sample_generator(options):
        captured["output_dir"] = options.output_dir
        return object()

    monkeypatch.setattr(sample_tools, "sample_generator", fake_sample_generator)
    monkeypatch.setattr(sample_tools, "sample_generator_result", lambda result: {"status": "success"})
    sample_tools.register_tools(mcp, config)

    result = mcp.tools[sample_tools.TOOL_NAME](
        domain_name="gripper",
        output_dir="samples/run",
        batch_name="batch",
        configs=[],
    )

    assert result == {"status": "success"}
    assert captured["output_dir"] == (output_root / "samples" / "run").resolve()


def test_registered_sample_tool_rejects_output_dir_escape(tmp_path):
    output_root = tmp_path / "mcp-output"
    config = ServerConfig(workspace_root=tmp_path, output_root=output_root)
    mcp = FakeMCP()
    sample_tools.register_tools(mcp, config)

    with pytest.raises(ValueError):
        mcp.tools[sample_tools.TOOL_NAME](
            domain_name="gripper",
            output_dir="../outside",
            batch_name="batch",
            configs=[],
        )
