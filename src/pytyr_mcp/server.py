from __future__ import annotations

from typing import Protocol, TypeAlias

from fastmcp import FastMCP

from pytyr_mcp.config import ServerConfig, load_config
from pytyr_mcp.planning.solvability.tools import TOOL_NAME as PROVE_SOLVABILITY_TOOL
from pytyr_mcp.planning.solvability.tools import register_tools as register_solvability_tools
from pytyr_mcp.planning.sample_generator.tools import TOOL_NAME as SAMPLE_GENERATOR_TOOL
from pytyr_mcp.planning.sample_generator.tools import register_tools as register_sample_generator_tools
from pytyr_mcp.roles import Role, load_role

ServerInfo: TypeAlias = dict[str, str | list[str]]


class Registrar(Protocol):
    def __call__(self, mcp: FastMCP, config: ServerConfig) -> None: ...


REGISTRARS: dict[str, Registrar] = {
    PROVE_SOLVABILITY_TOOL: register_solvability_tools,
    SAMPLE_GENERATOR_TOOL: register_sample_generator_tools,
}


def create_server(config: ServerConfig | None = None, role: Role | None = None) -> FastMCP:
    config = config or load_config()
    role = role or load_role()
    mcp = FastMCP("pytyr-mcp")

    for tool_name, register in REGISTRARS.items():
        if role.allows(tool_name):
            register(mcp, config)

    @mcp.tool(name="pytyr_mcp.server_info")
    def server_info() -> ServerInfo:
        return {
            "name": "pytyr-mcp",
            "role": role.name,
            "allowed_tools": sorted(role.allowed_tools),
            "workspace_root": config.workspace_root.as_posix(),
            "output_root": config.output_root.as_posix(),
        }

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
