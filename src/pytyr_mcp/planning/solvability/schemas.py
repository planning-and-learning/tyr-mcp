from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProveSolvabilityOptions:
    domain: str
    problem_dir: str
    output_dir: str
    num_threads: int = 1
    max_num_states: int = 100_000
    max_time_seconds: float = 5.0
    include_plans: bool = False
