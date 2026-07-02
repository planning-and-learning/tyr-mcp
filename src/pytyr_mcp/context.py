from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from pypddl.formalism import ParserOptions
from pyyggdrasil.execution import ExecutionContext
from pytyr.formalism.planning import Parser, PlanningDomain, PlanningTask
from pytyr.planning.lifted import Task


class TaskParser(Protocol):
    def parse_task(self, task_filepath: str, parser_options: ParserOptions) -> PlanningTask: ...


@dataclass(slots=True)
class DomainContext:
    id: str
    domain_file: Path
    parser: Parser
    planning_domain: PlanningDomain
    next_task_index: int = 1
    next_result_index: int = 1


@dataclass(slots=True)
class TaskContext:
    id: str
    domain_context: DomainContext
    index: int
    problem_file: Path
    execution_context: ExecutionContext
    task: Task


def create_domain_context(domain_file: str | Path) -> DomainContext:
    domain_path = Path(domain_file).resolve()
    parser_options = ParserOptions()
    parser = Parser(domain_path, parser_options)
    return DomainContext(
        id="domain_000001",
        domain_file=domain_path,
        parser=parser,
        planning_domain=parser.get_domain(),
    )


def create_task_context(
    domain_context: DomainContext,
    problem_file: str | Path,
    *,
    num_threads: int = 1,
) -> TaskContext:
    problem_path = Path(problem_file).resolve()
    index = domain_context.next_task_index
    domain_context.next_task_index += 1
    execution_context = ExecutionContext(num_threads)
    # pytyr exposes this nanobind overload with PathLike[Unknown]; narrow it at the boundary.
    parser = cast(TaskParser, domain_context.parser)
    formalism_task = parser.parse_task(problem_path.as_posix(), ParserOptions())
    return TaskContext(
        id=f"task_{index:06d}",
        domain_context=domain_context,
        index=index,
        problem_file=problem_path,
        execution_context=execution_context,
        task=Task(formalism_task),
    )
