from __future__ import annotations

import json
from pathlib import Path

import pytyr_mcp as public
from pytyr.planning import SearchStatus

from pytyr_mcp import DumpFormat, FindSatisficingPlanResult, PROVE_SEARCH_BUDGET, SearchBudget


def test_public_api_exports_context_and_plan_search_names() -> None:
    assert public.DumpFormat is DumpFormat
    assert public.FindSatisficingPlanResult is FindSatisficingPlanResult
    assert public.SearchBudget is SearchBudget
    assert public.PROVE_SEARCH_BUDGET is PROVE_SEARCH_BUDGET
    assert callable(public.create_domain_context)
    assert callable(public.create_task_context)
    assert callable(public.find_satisficing_plan)


def test_find_satisficing_plan_result_dump_writes_requested_files(tmp_path: Path) -> None:
    domain_path = tmp_path / "domain.pddl"
    problem_path = tmp_path / "p01.pddl"
    domain_path.write_text(
        """(define (domain seq)
  (:requirements :strips)
  (:predicates (done))
  (:action finish :parameters () :precondition () :effect (done)))
""",
        encoding="utf-8",
    )
    problem_path.write_text(
        """(define (problem p01)
  (:domain seq)
  (:init)
  (:goal (done)))
""",
        encoding="utf-8",
    )

    domain = public.create_domain_context(domain_path)
    task = public.create_task_context(domain, problem_path)
    result = public.find_satisficing_plan(task)

    assert task.domain_context is domain
    assert result.context is task
    assert result.search_status is SearchStatus.SOLVED
    assert result.solved is True

    dumped = result.dump(
        tmp_path / "artifacts",
        formats=(DumpFormat.JSON, DumpFormat.MD),
        include_plan_text=True,
    )

    assert dumped.files == (
        tmp_path / "artifacts" / "result.json",
        tmp_path / "artifacts" / "task.json",
        tmp_path / "artifacts" / "plan.txt",
        tmp_path / "artifacts" / "summary.md",
    )
    payload = json.loads((tmp_path / "artifacts" / "result.json").read_text(encoding="utf-8"))
    task_payload = json.loads((tmp_path / "artifacts" / "task.json").read_text(encoding="utf-8"))
    assert payload["tool"] == "tyr.planning.find_satisficing_plan"
    assert payload["task"]["solved"] is True
    assert task_payload["plan_path"] == (tmp_path / "artifacts" / "plan.txt").as_posix()
    plan_text = (tmp_path / "artifacts" / "plan.txt").read_text(encoding="utf-8")
    assert "[trace]" in plan_text
    assert "[facts]" in plan_text
    assert "(done )" in plan_text
    summary = (tmp_path / "artifacts" / "summary.md").read_text(encoding="utf-8")
    assert "## Plan Metadata" in summary
    assert "| Plan length |" in summary
