from __future__ import annotations

import json

from pytyr_mcp.artifacts import write_solvability_summary
from pytyr_mcp.planning.solvability.service import TOOL_NAME


def test_prove_solvability_summary_links_task_files(tmp_path):
    result = write_solvability_summary(
        tool=TOOL_NAME,
        status="failure",
        output_dir=tmp_path,
        metadata={"domain": "domain.pddl", "problem_dir": "problems"},
        tasks=[
            {
                "name": "p01.pddl",
                "path": "problems/p01.pddl",
                "status": "SOLVED",
                "solved": True,
                "plan_length": 2,
                "plan_cost": 2.0,
                "plan": None,
            },
            {
                "name": "p02.pddl",
                "path": "problems/p02.pddl",
                "status": "TIMEOUT",
                "solved": False,
                "plan_length": None,
                "plan_cost": None,
                "plan": None,
            },
        ],
    )

    assert result["counts"] == {"tasks": 2, "solved": 1, "unsolved": 1, "statuses": 2}
    summary = json.loads((tmp_path / "summary.json").read_text())
    task_path = tmp_path / summary["tasks"][1]["path"]
    task = json.loads(task_path.read_text())
    assert task["name"] == "p02.pddl"
    assert task["solved"] is False


def test_write_json_refuses_existing_artifact(tmp_path):
    import pytest
    from pytyr_mcp.artifacts import write_json

    target = tmp_path / "summary.json"
    target.write_text("stale\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_json(target, {"status": "new"})

    assert target.read_text(encoding="utf-8") == "stale\n"


def test_reused_solvability_output_allocates_child_run(tmp_path):
    task = {
        "name": "p01.pddl",
        "path": "problems/p01.pddl",
        "status": "SOLVED",
        "solved": True,
        "plan_length": 2,
        "plan_cost": 2.0,
        "plan": None,
    }

    first = write_solvability_summary(
        tool=TOOL_NAME,
        status="success",
        output_dir=tmp_path,
        metadata={"domain": "domain.pddl", "problem_dir": "problems"},
        tasks=[task],
    )
    second = write_solvability_summary(
        tool=TOOL_NAME,
        status="success",
        output_dir=tmp_path,
        metadata={"domain": "domain.pddl", "problem_dir": "problems"},
        tasks=[task],
    )

    assert first["output_dir"] == tmp_path.as_posix()
    assert second["output_dir"] == (tmp_path / "run-002").as_posix()
    assert (tmp_path / "summary.json").is_file()
    assert (tmp_path / "run-002" / "summary.json").is_file()


def test_reused_solvability_output_relativizes_absolute_task_paths_to_child_run(tmp_path):
    problem = tmp_path / "problems" / "p01.pddl"
    problem.parent.mkdir()
    problem.write_text("(define (problem p01))", encoding="utf-8")
    task = {
        "name": "p01.pddl",
        "path": problem.as_posix(),
        "status": "SOLVED",
        "solved": True,
        "plan_length": 2,
        "plan_cost": 2.0,
        "plan": None,
    }

    write_solvability_summary(
        tool=TOOL_NAME,
        status="success",
        output_dir=tmp_path / "out",
        metadata={"domain": "domain.pddl", "problem_dir": problem.parent.as_posix()},
        tasks=[task],
    )
    second = write_solvability_summary(
        tool=TOOL_NAME,
        status="success",
        output_dir=tmp_path / "out",
        metadata={"domain": "domain.pddl", "problem_dir": problem.parent.as_posix()},
        tasks=[task],
    )

    child = tmp_path / "out" / "run-002"
    summary = json.loads((child / "summary.json").read_text(encoding="utf-8"))
    task_json = json.loads((child / summary["tasks"][0]["path"]).read_text(encoding="utf-8"))
    assert second["output_dir"] == child.as_posix()
    assert task_json["path"] == "<omitted: outside output_dir>"
    assert summary["by_status"]["SOLVED"]["tasks"][0]["path"] == "<omitted: outside output_dir>"
