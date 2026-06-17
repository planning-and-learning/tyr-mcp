from __future__ import annotations

import os
from dataclasses import dataclass


PLANNING_SOLVABILITY_TOOLS = frozenset({"tyr.planning.prove_solvability"})
PLANNING_SAMPLE_TOOLS = frozenset({"tyr.planning.sample_generator", "tyr.planning.describe_generator"})
PLANNING_TOOLS = PLANNING_SOLVABILITY_TOOLS | PLANNING_SAMPLE_TOOLS
ALL_TOOLS = PLANNING_TOOLS

ROLE_TOOLS = {
    "planning/solvability": PLANNING_SOLVABILITY_TOOLS,
    "planning.solvability": PLANNING_SOLVABILITY_TOOLS,
    "planning/sample": PLANNING_SAMPLE_TOOLS,
    "planning.sample": PLANNING_SAMPLE_TOOLS,
    "planning": PLANNING_TOOLS,
    "all": ALL_TOOLS,
}


@dataclass(frozen=True)
class Role:
    name: str
    allowed_tools: frozenset[str]

    def allows(self, tool_name: str) -> bool:
        return tool_name in self.allowed_tools


def load_role() -> Role:
    name = os.environ.get("PYTYR_MCP_ROLE", "all")
    try:
        allowed_tools = ROLE_TOOLS[name]
    except KeyError as exc:
        allowed = ", ".join(sorted(ROLE_TOOLS))
        raise ValueError(f"Unknown PYTYR_MCP_ROLE: {name}. Expected one of: {allowed}") from exc
    return Role(name=name, allowed_tools=allowed_tools)
