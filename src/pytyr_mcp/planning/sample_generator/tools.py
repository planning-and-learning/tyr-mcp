from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from pytyr_mcp.config import ServerConfig
from pytyr_mcp.paths import server_output_dir
from pytyr_mcp.planning.sample_generator.results import describe_generator_result, sample_generator_result
from pytyr_mcp.planning.sample_generator.service import SampleGeneratorOptions, describe_make_problem, get_generator_path, sample_generator

TOOL_NAME = "tyr.planning.sample_generator"
DESCRIBE_TOOL_NAME = "tyr.planning.describe_generator"


def register_tools(mcp: FastMCP, config: ServerConfig) -> None:

    @mcp.tool(name=DESCRIBE_TOOL_NAME)
    def describe_generator(domain_name: str) -> dict[str, Any]:
        """Return the make_problem signature and source path for a planning benchmark generator."""
        return describe_generator_result(
            domain_name=domain_name,
            generator_path=get_generator_path(domain_name),
            signature=describe_make_problem(domain_name),
        )

    @mcp.tool(name=TOOL_NAME)
    def generate_samples(
        domain_name: str,
        output_dir: str,
        batch_name: str,
        configs: list[dict[str, Any]],
        allow_invalid: bool = False,
    ) -> dict[str, Any]:
        """Generate PDDL sample problems from a planning benchmark generator."""
        result = sample_generator(
            SampleGeneratorOptions(
                domain_name=domain_name,
                output_dir=server_output_dir(config.output_root, output_dir),
                batch_name=batch_name,
                configs=configs,
                allow_invalid=allow_invalid,
            )
        )
        return sample_generator_result(result)
