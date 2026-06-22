from __future__ import annotations

import json

from pytyr_mcp.artifacts import write_solvability_summary
from pytyr_mcp.planning.solvability.service import TOOL_NAME


def _task(path: str = "problems/p01.pddl") -> dict:
    return {
        "name": "p01.pddl",
        "path": path,
        "status": "SOLVED",
        "solved": True,
        "plan_length": 2,
        "plan_cost": 2.0,
        "plan": None,
    }


def test_prove_solvability_summary_links_task_file(tmp_path):
    result = write_solvability_summary(
        tool=TOOL_NAME,
        status="success",
        output_dir=tmp_path,
        metadata={"domain_file": "domain.pddl", "problem_file": "problems/p01.pddl"},
        task=_task(),
    )

    assert result["successful"] is True
    assert result["task_name"] == "p01.pddl"
    assert result["task_status"] == "SOLVED"
    assert result["solved"] is True
    assert result["primary"]["successful"] is True
    assert result["primary"]["prompt_summary"] == result["prompt_summary"]
    assert result["prompt_summary"]["task_name"] == "p01.pddl"
    assert result["prompt_summary"]["summary_md"] == (tmp_path / "summary.md").as_posix()
    assert result["summary"]["task"]["path"] == (tmp_path / "task.json").as_posix()
    assert "task" not in result
    assert "items" not in result
    assert "tasks" not in result
    summary = json.loads((tmp_path / "summary.json").read_text())
    task = json.loads((tmp_path / summary["task"]["path"]).read_text())
    assert task["name"] == "p01.pddl"
    assert task["solved"] is True


def test_write_json_refuses_existing_artifact(tmp_path):
    import pytest
    from pytyr_mcp.artifacts import write_json

    target = tmp_path / "summary.json"
    target.write_text("stale\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_json(target, {"status": "new"})

    assert target.read_text(encoding="utf-8") == "stale\n"


def test_reused_solvability_output_allocates_child_run(tmp_path):
    first = write_solvability_summary(
        tool=TOOL_NAME,
        status="success",
        output_dir=tmp_path,
        metadata={"domain_file": "domain.pddl", "problem_file": "problems/p01.pddl"},
        task=_task(),
    )
    second = write_solvability_summary(
        tool=TOOL_NAME,
        status="success",
        output_dir=tmp_path,
        metadata={"domain_file": "domain.pddl", "problem_file": "problems/p01.pddl"},
        task=_task(),
    )

    assert first["output_dir"] == tmp_path.as_posix()
    assert second["output_dir"] == (tmp_path / "run-002").as_posix()
    assert (tmp_path / "summary.json").is_file()
    assert (tmp_path / "task.json").is_file()
    assert (tmp_path / "run-002" / "summary.json").is_file()
    assert (tmp_path / "run-002" / "task.json").is_file()


def test_reused_solvability_output_relativizes_absolute_task_path_to_child_run(tmp_path):
    problem = tmp_path / "problems" / "p01.pddl"
    problem.parent.mkdir()
    problem.write_text("(define (problem p01))", encoding="utf-8")

    write_solvability_summary(
        tool=TOOL_NAME,
        status="success",
        output_dir=tmp_path / "out",
        metadata={"domain_file": "domain.pddl", "problem_file": problem.as_posix()},
        task=_task(problem.as_posix()),
    )
    second = write_solvability_summary(
        tool=TOOL_NAME,
        status="success",
        output_dir=tmp_path / "out",
        metadata={"domain_file": "domain.pddl", "problem_file": problem.as_posix()},
        task=_task(problem.as_posix()),
    )

    child = tmp_path / "out" / "run-002"
    summary = json.loads((child / "summary.json").read_text(encoding="utf-8"))
    task = json.loads((child / summary["task"]["path"]).read_text(encoding="utf-8"))
    assert second["output_dir"] == child.as_posix()
    assert task["path"] == problem.as_posix()
