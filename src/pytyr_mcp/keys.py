from __future__ import annotations

from enum import StrEnum


class Keys(StrEnum):
    """Keys used in serialized objects, ordered from envelopes to leaf values."""

    # Document and result envelope.
    SCHEMA_VERSION = "schema_version"
    TOOL = "tool"
    STATUS = "status"
    TASK = "task"
    CONTEXT = "context"

    # Record identity.
    ID = "id"
    INDEX = "index"
    NAME = "name"

    # Plan result.
    SOLVED = "solved"
    PLAN_COST = "plan_cost"
    PLAN_LENGTH = "plan_length"

    # Filesystem locations.
    DOMAIN_PATH = "domain_path"
    PLAN_PATH = "plan_path"
    TASK_PATH = "task_path"
