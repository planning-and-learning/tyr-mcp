from __future__ import annotations

from pathlib import Path

from pytyr_mcp.context import DomainContext, TaskContext
from pytyr_mcp.context import create_domain_context as _create_domain_context
from pytyr_mcp.context import create_task_context as _create_task_context
from pytyr_mcp.defaults import PROVE_SEARCH_BUDGET, SearchBudget
from pytyr_mcp.planning.search import FindSatisficingPlanResult
from pytyr_mcp.planning.search import find_satisficing_plan as _find_satisficing_plan


def create_domain_context(domain_file: str | Path) -> DomainContext:
    return _create_domain_context(domain_file)


def create_task_context(
    domain_context: DomainContext,
    problem_file: str | Path,
    *,
    num_threads: int = 1,
) -> TaskContext:
    return _create_task_context(domain_context, problem_file, num_threads=num_threads)


def find_satisficing_plan(
    context: TaskContext,
    *,
    search_budget: SearchBudget = PROVE_SEARCH_BUDGET,
) -> FindSatisficingPlanResult:
    return _find_satisficing_plan(context, search_budget=search_budget)
