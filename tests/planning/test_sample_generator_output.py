from __future__ import annotations

import json

from pytyr_mcp.planning.sample_generator.results import sample_generator_result
from pytyr_mcp.planning.sample_generator.service import (
    GeneratedProblem,
    InvalidGeneratorConfig,
    SampleGeneratorResult,
)


def test_sample_generator_result_writes_summary_and_indexes_artifacts(tmp_path):
    output_dir = tmp_path / "sample_run"
    problem_dir = output_dir / "batch"
    problem_dir.mkdir(parents=True)
    domain = output_dir / "domain.pddl"
    generator = tmp_path / "generator.py"
    configs = problem_dir / "configs.json"
    pddl = problem_dir / "batch-001.pddl"
    domain.write_text("(define (domain d))", encoding="utf-8")
    generator.write_text("def make_problem(): pass", encoding="utf-8")
    configs.write_text("{}\n", encoding="utf-8")
    pddl.write_text("(define (problem p))", encoding="utf-8")

    result = sample_generator_result(
        SampleGeneratorResult(
            domain_path=domain,
            problem_dir=problem_dir,
            generator_path=generator,
            signature="(n: int) -> str",
            generated=[GeneratedProblem(index=1, path=pddl, config={"n": 1})],
            invalid=[InvalidGeneratorConfig(index=2, config={"n": 0}, reason="bad")],
        )
    )

    assert result["status"] == "failure"
    assert result["primary"]["generated_count"] == 1
    assert result["primary"]["invalid_count"] == 1
    assert result["artifacts"]["summary_json"] == "summary.json"
    assert result["artifacts"]["summary_md"] == "summary.md"
    assert result["artifacts"]["configs_json"] == "batch/configs.json"
    assert (output_dir / result["artifacts"]["summary_json"]).is_file()
    assert (output_dir / result["artifacts"]["summary_md"]).is_file()

    summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["counts"] == {"generated": 1, "invalid": 1}
    assert summary["generated"][0]["path"] == pddl.as_posix()
    assert result["items"] == summary["generated"]
    assert result["diagnostics"] == summary["invalid"]
