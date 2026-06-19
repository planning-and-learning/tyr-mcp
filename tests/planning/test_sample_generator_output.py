from __future__ import annotations

import json

from pytyr_mcp.planning.sample_generator.results import sample_generator_result
from pytyr_mcp.planning.sample_generator.service import (
    _batch_slug,
    _fresh_problem_dir,
    sample_generator,
    GeneratedProblem,
    InvalidGeneratorConfig,
    SampleGeneratorOptions,
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
    assert summary["generated"][0]["path"] == "batch/batch-001.pddl"
    assert "absolute_path" not in summary["generated"][0]
    assert result["items"] == summary["generated"]
    assert result["diagnostics"] == summary["invalid"]
    assert result["primary"]["prompt_summary"] == result["prompt_summary"]
    assert result["prompt_summary"]["counts"] == {"generated": 1, "invalid": 1}
    assert result["prompt_summary"]["summary_md"] == "summary.md"
    assert result["prompt_summary"]["generated"] == ["batch-001.pddl"]
    assert "items" not in result["prompt_summary"]


def test_sample_generator_result_refuses_existing_summary_json(tmp_path):
    output_dir = tmp_path / "sample_run"
    problem_dir = output_dir / "batch"
    problem_dir.mkdir(parents=True)
    domain = output_dir / "domain.pddl"
    generator = tmp_path / "generator.py"
    pddl = problem_dir / "batch-001.pddl"
    domain.write_text("(define (domain d))", encoding="utf-8")
    generator.write_text("def make_problem(): pass", encoding="utf-8")
    pddl.write_text("(define (problem p))", encoding="utf-8")
    (output_dir / "summary.json").write_text("stale\n", encoding="utf-8")

    import pytest

    with pytest.raises(FileExistsError):
        sample_generator_result(
            SampleGeneratorResult(
                domain_path=domain,
                problem_dir=problem_dir,
                generator_path=generator,
                signature="() -> str",
                generated=[GeneratedProblem(index=1, path=pddl, config={})],
                invalid=[],
            )
        )

    assert (output_dir / "summary.json").read_text(encoding="utf-8") == "stale\n"


def test_reused_sample_batch_allocates_child_batch(tmp_path):
    output_dir = tmp_path / "sample_run"
    first = output_dir / "batch"
    first.mkdir(parents=True)
    (first / "batch-001.pddl").write_text("old", encoding="utf-8")

    fresh = _fresh_problem_dir(output_dir, "batch")

    assert fresh == output_dir / "batch-002"
    assert (first / "batch-001.pddl").read_text(encoding="utf-8") == "old"


def test_reused_numbered_sample_batch_skips_occupied_child(tmp_path):
    output_dir = tmp_path / "sample_run"
    first = output_dir / "batch"
    second = output_dir / "batch-002"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    (first / "batch-001.pddl").write_text("old", encoding="utf-8")
    (second / "batch-001.pddl").write_text("also old", encoding="utf-8")

    fresh = _fresh_problem_dir(output_dir, "batch")

    assert fresh == output_dir / "batch-003"
    assert (first / "batch-001.pddl").read_text(encoding="utf-8") == "old"
    assert (second / "batch-001.pddl").read_text(encoding="utf-8") == "also old"


def test_sample_batch_name_is_slugged_inside_output_dir(tmp_path):
    output_dir = tmp_path / "sample_run"

    fresh = _fresh_problem_dir(output_dir, "../bad/name")

    assert _batch_slug("../bad/name") == "bad_name"
    assert fresh == output_dir / "bad_name"
    assert fresh.is_relative_to(output_dir)
    assert not (tmp_path / "bad").exists()


def test_existing_task_tree_forces_child_run(tmp_path):
    from pytyr_mcp.artifacts import fresh_output_dir

    output_dir = tmp_path / "sample_run"
    stale_tree = output_dir / "tasks"
    stale_tree.mkdir(parents=True)
    (stale_tree / "old.json").write_text("{}\n", encoding="utf-8")

    fresh = fresh_output_dir(output_dir)

    assert fresh == output_dir / "run-002"
    assert (stale_tree / "old.json").is_file()
    assert (output_dir / "run-002" / ".pytyr-mcp-output").is_file()


def test_fresh_output_dir_reserves_empty_directory(tmp_path):
    from pytyr_mcp.artifacts import fresh_output_dir

    output_dir = tmp_path / "sample_run"
    output_dir.mkdir()

    first = fresh_output_dir(output_dir)
    second = fresh_output_dir(output_dir)

    assert first == output_dir
    assert second == output_dir / "run-002"
    assert (output_dir / ".pytyr-mcp-output").is_file()
    assert (output_dir / "run-002" / ".pytyr-mcp-output").is_file()


def test_reused_sample_output_allocates_child_run(monkeypatch, tmp_path):
    import pytyr_mcp.planning.sample_generator.service as service_module

    output_dir = tmp_path / "sample_run"
    source_domain = tmp_path / "source-domain.pddl"
    generator = tmp_path / "generator.py"
    source_domain.write_text("(define (domain d))", encoding="utf-8")
    generator.write_text("def make_problem(n): pass", encoding="utf-8")

    monkeypatch.setattr(service_module, "get_generator_path", lambda domain_name: generator)
    monkeypatch.setattr(service_module, "get_generator_domain_path", lambda domain_name: source_domain)
    monkeypatch.setattr(service_module, "load_make_problem", lambda domain_name: (lambda n: f"(define (problem p{n}))"))

    opts = SampleGeneratorOptions(
        domain_name="gripper",
        output_dir=output_dir,
        batch_name="batch",
        configs=[{"n": 1}],
    )
    first = sample_generator(opts)
    first_result = sample_generator_result(first)
    second = sample_generator(opts)
    second_result = sample_generator_result(second)

    assert first_result["output_dir"] == output_dir.as_posix()
    assert second_result["output_dir"] == (output_dir / "run-002").as_posix()
    assert (output_dir / "summary.json").is_file()
    assert (output_dir / "run-002" / "summary.json").is_file()
    assert first.problem_dir == output_dir / "batch"
    assert second.problem_dir == output_dir / "run-002" / "batch"


def test_sample_generator_uses_slugged_batch_names(monkeypatch, tmp_path):
    import pytyr_mcp.planning.sample_generator.service as service_module

    output_dir = tmp_path / "sample_run"
    source_domain = tmp_path / "source-domain.pddl"
    generator = tmp_path / "generator.py"
    source_domain.write_text("(define (domain d))", encoding="utf-8")
    generator.write_text("def make_problem(n): pass", encoding="utf-8")

    monkeypatch.setattr(service_module, "get_generator_path", lambda domain_name: generator)
    monkeypatch.setattr(service_module, "get_generator_domain_path", lambda domain_name: source_domain)
    monkeypatch.setattr(service_module, "load_make_problem", lambda domain_name: (lambda n: f"(define (problem p{n}))"))

    result = sample_generator(SampleGeneratorOptions(
        domain_name="gripper",
        output_dir=output_dir,
        batch_name="../bad/name",
        configs=[{"n": 1}],
    ))
    payload = sample_generator_result(result)

    assert result.problem_dir == output_dir / "bad_name"
    assert result.generated[0].path == output_dir / "bad_name" / "bad_name-001.pddl"
    assert payload["generated"][0]["path"] == "bad_name/bad_name-001.pddl"
    configs = json.loads((output_dir / "bad_name" / "configs.json").read_text(encoding="utf-8"))
    assert configs["generated"][0]["path"] == "bad_name/bad_name-001.pddl"
    assert not (tmp_path / "bad").exists()
