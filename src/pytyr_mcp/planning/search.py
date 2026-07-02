from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from collections.abc import Iterable, Sequence
from typing import Protocol, cast

from pytyr.planning import SearchStatus
from pytyr.planning.lifted import (
    AxiomEvaluatorFactory,
    FFRPGHeuristic,
    StateRepositoryFactory,
    SuccessorGeneratorFactory,
    gbfs_lazy,
)

from pytyr_mcp.context import TaskContext
from pytyr_mcp.defaults import PROVE_SEARCH_BUDGET, SearchBudget
from pytyr_mcp.dumping import DumpFormat, DumpResult, allocate_output_dir
from pytyr_mcp.json_types import JsonObject


class PlanLike(Protocol):
    def get_length(self) -> int: ...

    def get_cost(self) -> float: ...


class StateLike(Protocol):
    def static_atoms(self) -> Iterable[object]: ...

    def fluent_facts(self) -> Iterable[object]: ...

    def derived_atoms(self) -> Iterable[object]: ...

    def static_fterm_values(self) -> Iterable[object]: ...

    def fluent_fterm_values(self) -> Iterable[object]: ...


class NodeLike(Protocol):
    def get_state(self) -> StateLike: ...


class LabeledNodeLike(Protocol):
    label: object
    node: NodeLike


class TracePlanLike(PlanLike, Protocol):
    def get_start_node(self) -> NodeLike: ...

    def get_labeled_succ_nodes(self) -> Sequence[LabeledNodeLike]: ...


@dataclass(frozen=True, slots=True)
class FindSatisficingPlanResult:
    id: str
    context: TaskContext
    search_status: SearchStatus
    solved: bool
    plan: object | None
    plan_length: int | None
    plan_cost: float | None

    @property
    def status(self) -> str:
        return "success" if self.solved else "failure"

    def dump(
        self,
        output_dir: str | Path,
        *,
        formats: tuple[DumpFormat, ...] = (DumpFormat.JSON,),
        include_plan_text: bool = False,
    ) -> DumpResult:
        output_path = allocate_output_dir(output_dir)
        files: list[Path] = []
        plan_path = (
            output_path / "plan.txt" if include_plan_text and self.plan is not None else None
        )
        result_payload, task_payload = result_json(self, plan_path=plan_path)
        if DumpFormat.JSON in formats:
            result_path = output_path / "result.json"
            task_path = output_path / "task.json"
            from pytyr_mcp.artifacts import write_json

            write_json(result_path, result_payload)
            write_json(task_path, task_payload)
            files.extend([result_path, task_path])
        if plan_path is not None:
            write_plan_text(plan_path, self)
            files.append(plan_path)
        if DumpFormat.MD in formats:
            summary_path = output_path / "summary.md"
            write_summary_markdown(summary_path, self, plan_path=plan_path)
            files.append(summary_path)
        return DumpResult(output_dir=output_path, files=tuple(files))


def next_result_id(context: TaskContext) -> str:
    domain = context.domain_context
    index = domain.next_result_index
    domain.next_result_index += 1
    return f"result_{index:06d}"


def _required_budget_values(budget: SearchBudget, *, name: str) -> tuple[int, float]:
    if budget.max_num_states is None or budget.max_time_seconds is None:
        raise ValueError(f"{name} requires max_num_states and max_time_seconds")
    return budget.max_num_states, budget.max_time_seconds


def find_satisficing_plan(
    context: TaskContext,
    *,
    search_budget: SearchBudget = PROVE_SEARCH_BUDGET,
) -> FindSatisficingPlanResult:
    axiom_evaluator = AxiomEvaluatorFactory().create(context.task, context.execution_context)
    state_repository = StateRepositoryFactory().create(context.task, axiom_evaluator)
    successor_generator = SuccessorGeneratorFactory().create(
        context.task, context.execution_context, state_repository
    )
    heuristic = FFRPGHeuristic(context.task, context.execution_context)

    max_num_states, max_time_seconds = _required_budget_values(
        search_budget, name="find_satisficing_plan search_budget"
    )
    search_options = gbfs_lazy.Options()
    search_options.max_num_states = max_num_states
    search_options.max_time = timedelta(seconds=max_time_seconds)

    search_result = gbfs_lazy.find_solution(
        context.task, successor_generator, heuristic, search_options
    )
    plan = search_result.plan
    typed_plan = None if plan is None else cast(PlanLike, plan)
    return FindSatisficingPlanResult(
        id=next_result_id(context),
        context=context,
        search_status=search_result.status,
        solved=search_result.status == SearchStatus.SOLVED,
        plan=plan,
        plan_length=None if typed_plan is None else typed_plan.get_length(),
        plan_cost=None if typed_plan is None else typed_plan.get_cost(),
    )


def result_json(
    result: FindSatisficingPlanResult,
    *,
    plan_path: Path | None,
) -> tuple[JsonObject, JsonObject]:
    task: JsonObject = {
        "schema_version": 1,
        "name": result.context.problem_file.name,
        "path": result.context.problem_file.as_posix(),
        "status": result.search_status.name,
        "solved": result.solved,
        "plan_length": result.plan_length,
        "plan_cost": result.plan_cost,
        "plan_path": None if plan_path is None else plan_path.resolve().as_posix(),
    }
    result_payload: JsonObject = {
        "schema_version": 1,
        "id": result.id,
        "tool": "tyr.planning.find_satisficing_plan",
        "status": result.status,
        "context": {"id": result.context.id, "index": result.context.index},
        "task": task,
    }
    return result_payload, task


def write_plan_text(path: Path, result: FindSatisficingPlanResult) -> None:
    with path.open("x", encoding="utf-8") as fh:
        fh.write(plan_trace_text(result).rstrip() + "\n")


def plan_trace_text(result: FindSatisficingPlanResult) -> str:
    if result.plan is None:
        return ""

    plan = cast(TracePlanLike, result.plan)
    actions = [line.strip() for line in str(result.plan).splitlines() if line.strip()]
    labeled_nodes = list(plan.get_labeled_succ_nodes())
    nodes = [plan.get_start_node(), *(labeled.node for labeled in labeled_nodes)]

    lines = [
        "[metadata]",
        f"status: {result.search_status.name}",
        f"solved: {result.solved}",
        f"plan_length: {result.plan_length}",
        f"plan_cost: {result.plan_cost}",
        "",
        "[trace]",
    ]
    for index, node in enumerate(nodes):
        action = "<initial>" if index == 0 else action_text(actions, labeled_nodes, index - 1)
        lines.extend(
            [
                f"[step {index}]",
                "[action]",
                action,
                "[facts]",
            ]
        )
        facts = state_facts(node.get_state())
        lines.extend(facts if facts else ["<none>"])
        lines.append("")
    return "\n".join(lines)


def action_text(
    rendered_actions: Sequence[str],
    labeled_nodes: Sequence[LabeledNodeLike],
    index: int,
) -> str:
    if index < len(rendered_actions):
        return rendered_actions[index]
    if index < len(labeled_nodes):
        return str(labeled_nodes[index].label).strip()
    return "<unknown>"


def state_facts(state: StateLike) -> list[str]:
    facts: list[str] = []
    for values in (
        state.static_atoms(),
        state.fluent_facts(),
        state.derived_atoms(),
        state.static_fterm_values(),
        state.fluent_fterm_values(),
    ):
        facts.extend(str(value).strip() for value in values)
    return sorted(fact for fact in facts if fact)


def write_summary_markdown(
    path: Path,
    result: FindSatisficingPlanResult,
    *,
    plan_path: Path | None,
) -> None:
    lines = [
        "# tyr.planning.find_satisficing_plan",
        "",
        f"Status: `{result.status}`",
        "",
        "## Plan Metadata",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Task | `{result.context.problem_file.name}` |",
        f"| Search status | `{result.search_status.name}` |",
        f"| Solved | `{result.solved}` |",
        f"| Plan length | `{result.plan_length}` |",
        f"| Plan cost | `{result.plan_cost}` |",
        f"| Plan file | `{'' if plan_path is None else plan_path.name}` |",
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
