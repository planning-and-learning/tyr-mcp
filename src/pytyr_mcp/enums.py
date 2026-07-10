from __future__ import annotations

from enum import StrEnum


class DumpFormat(StrEnum):
    JSON = "json"
    MD = "md"


class RunStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
