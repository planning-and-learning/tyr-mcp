from __future__ import annotations

import io
from contextlib import redirect_stdout
from datetime import timedelta
from pathlib import Path

from pypddl.formalism import ParserOptions
from pyyggdrasil.execution import ExecutionContext
from pytyr.formalism.planning import Parser
from pytyr.planning import SearchStatus
from pytyr.planning.lifted import (
    AxiomEvaluatorFactory,
    FFRPGHeuristic,
    StateRepositoryFactory,
    SuccessorGeneratorFactory,
    Task,
    gbfs_lazy,
)

from pytyr_mcp.artifacts import write_solvability_summary
from pytyr_mcp.json_types import JsonObject
from pytyr_mcp.planning.solvability.schemas import ProveSolvabilityOptions

TOOL_NAME = "tyr.planning.prove_solvability"


def status_name(status: SearchStatus) -> str:
    return status.name


def _prove_one(
    *,
    parser: Parser,
    parser_options: ParserOptions,
    problem_path: Path,
    execution_context: ExecutionContext,
    max_num_states: int,
    max_time_seconds: float,
    include_plan: bool,
) -> JsonObject:
    formalism_task = parser.parse_task(problem_path, parser_options)
    task = Task(formalism_task)
    axiom_evaluator = AxiomEvaluatorFactory().create(task, execution_context)
    state_repository = StateRepositoryFactory().create(task, axiom_evaluator)
    successor_generator = SuccessorGeneratorFactory().create(task, execution_context, state_repository)
    heuristic = FFRPGHeuristic(task, execution_context)

    search_options = gbfs_lazy.Options()
    search_options.max_num_states = max_num_states
    search_options.max_time = timedelta(seconds=max_time_seconds)

    search_result = gbfs_lazy.find_solution(task, successor_generator, heuristic, search_options)
    plan = search_result.plan
    return {
        "name": problem_path.name,
        "path": problem_path.as_posix(),
        "status": status_name(search_result.status),
        "solved": search_result.status == SearchStatus.SOLVED,
        "plan_length": None if plan is None else plan.get_length(),
        "plan_cost": None if plan is None else plan.get_cost(),
        "plan": None if plan is None or not include_plan else str(plan),
    }


def prove_solvability(options: ProveSolvabilityOptions) -> JsonObject:
    domain_path = Path(options.domain_file).resolve()
    problem_path = Path(options.problem_file).resolve()
    output_dir = Path(options.output_dir).resolve()
    execution_context = ExecutionContext(options.num_threads)
    parser_options = ParserOptions()
    parser = Parser(domain_path, parser_options)
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        task = _prove_one(
            parser=parser,
            parser_options=parser_options,
            problem_path=problem_path,
            execution_context=execution_context,
            max_num_states=options.max_num_states,
            max_time_seconds=options.max_time_seconds,
            include_plan=options.include_plans,
        )
        print(
            f"[1/1] {problem_path.name}: {task['status']} "
            f"(plan_length={task['plan_length']})",
            flush=True,
        )
    return write_solvability_summary(
        tool=TOOL_NAME,
        status="success" if task["solved"] else "failure",
        output_dir=output_dir,
        metadata={
            "domain_file": domain_path.as_posix(),
            "problem_file": problem_path.as_posix(),
            "num_threads": options.num_threads,
            "max_num_states": options.max_num_states,
            "max_time_seconds": options.max_time_seconds,
            "include_plans": options.include_plans,
        },
        task=task,
        stdout=stdout.getvalue(),
    )
