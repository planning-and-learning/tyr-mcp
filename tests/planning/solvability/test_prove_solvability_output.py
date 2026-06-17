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
