from __future__ import annotations

from fastmcp import FastMCP

from pytyr_mcp.config import ServerConfig
from pytyr_mcp.paths import server_output_dir
from pytyr_mcp.planning.solvability.schemas import ProveSolvabilityOptions
from pytyr_mcp.planning.solvability.service import TOOL_NAME
from pytyr_mcp.planning.solvability.service import prove_solvability as run_prove_solvability


def register_tools(mcp: FastMCP, config: ServerConfig) -> None:

    @mcp.tool(name=TOOL_NAME)
    def prove_solvability(
        domain_file: str,
        problem_file: str,
        output_dir: str,
        num_threads: int = 1,
        max_num_states: int = 100_000,
        max_time_seconds: float = 5.0,
        include_plans: bool = False,
    ) -> dict:
        """Prove PDDL task solvability with pytyr lifted GBFS lazy search and hFF."""
        return run_prove_solvability(
            ProveSolvabilityOptions(
                domain_file=domain_file,
                problem_file=problem_file,
                output_dir=server_output_dir(config.output_root, output_dir).as_posix(),
                num_threads=num_threads,
                max_num_states=max_num_states,
                max_time_seconds=max_time_seconds,
                include_plans=include_plans,
            )
        )
