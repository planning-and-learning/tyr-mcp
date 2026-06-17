from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
import inspect
import json
import shutil
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any




def benchmark_root() -> Path:
    return Path(os.environ.get("PYTYR_MCP_BENCHMARK_ROOT", Path.cwd() / "data" / "planning-benchmarks")).resolve()


def generator_root() -> Path:
    return benchmark_root() / "generators" / "classical"


@dataclass(frozen=True)
class GeneratedProblem:
    index: int
    path: Path
    config: dict[str, Any]


@dataclass(frozen=True)
class InvalidGeneratorConfig:
    index: int
    config: dict[str, Any]
    reason: str


@dataclass(frozen=True)
class SampleGeneratorOptions:
    domain_name: str
    output_dir: Path
    batch_name: str
    configs: Sequence[Mapping[str, Any]]
    allow_invalid: bool = False


@dataclass(frozen=True)
class SampleGeneratorResult:
    domain_path: Path
    problem_dir: Path
    generator_path: Path
    signature: str
    generated: list[GeneratedProblem]
    invalid: list[InvalidGeneratorConfig]

    @property
    def is_successful(self) -> bool:
        return not self.invalid


def get_generator_path(domain_name: str) -> Path:
    return generator_root() / domain_name / "generator.py"


def get_generator_domain_path(domain_name: str) -> Path:
    return generator_root() / domain_name / "domain.pddl"


def load_generator_module(domain_name: str) -> ModuleType:
    generator_path = get_generator_path(domain_name)
    if not generator_path.exists():
        raise FileNotFoundError(f"Generator not found: {generator_path}")

    module_name = f"_prompt_prove_patch_generator_{domain_name}"
    spec = importlib.util.spec_from_file_location(module_name, generator_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import generator from {generator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_make_problem(domain_name: str) -> Callable[..., str | None]:
    module = load_generator_module(domain_name)
    make_problem = getattr(module, "make_problem", None)
    if not callable(make_problem):
        raise AttributeError(f"{get_generator_path(domain_name)} does not define callable make_problem")
    return make_problem


def describe_make_problem(domain_name: str) -> str:
    make_problem = load_make_problem(domain_name)
    return str(inspect.signature(make_problem))


def sample_generator(options: SampleGeneratorOptions) -> SampleGeneratorResult:
    make_problem = load_make_problem(options.domain_name)
    signature = str(inspect.signature(make_problem))
    generator_path = get_generator_path(options.domain_name)
    source_domain_path = get_generator_domain_path(options.domain_name)
    if not source_domain_path.exists():
        raise FileNotFoundError(f"Generator domain not found: {source_domain_path}")

    output_dir = options.output_dir
    problem_dir = output_dir / options.batch_name
    output_dir.mkdir(parents=True, exist_ok=True)
    problem_dir.mkdir(parents=True, exist_ok=True)

    domain_path = output_dir / "domain.pddl"
    shutil.copyfile(source_domain_path, domain_path)

    generated: list[GeneratedProblem] = []
    invalid: list[InvalidGeneratorConfig] = []
    for path in problem_dir.glob("*.pddl"):
        path.unlink()

    for index, config in enumerate(options.configs, start=1):
        config_dict = dict(config)
        try:
            problem = make_problem(**config_dict)
            if problem is None:
                raise ValueError("make_problem returned None")
        except Exception as exc:  # noqa: BLE001 - report generator feedback to the outer loop.
            invalid_config = InvalidGeneratorConfig(index=index, config=config_dict, reason=str(exc))
            invalid.append(invalid_config)
            if options.allow_invalid:
                continue
            break

        problem_path = problem_dir / f"{options.batch_name}-{index:03d}.pddl"
        problem_path.write_text(problem, encoding="utf-8")
        generated.append(GeneratedProblem(index=index, path=problem_path, config=config_dict))

    metadata_path = problem_dir / "configs.json"
    metadata = {
        "domain_name": options.domain_name,
        "generator_path": str(generator_path),
        "signature": signature,
        "generated": [
            {"index": problem.index, "path": str(problem.path), "config": problem.config}
            for problem in generated
        ],
        "invalid": [
            {"index": item.index, "config": item.config, "reason": item.reason}
            for item in invalid
        ],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return SampleGeneratorResult(
        domain_path=domain_path,
        problem_dir=problem_dir,
        generator_path=generator_path,
        signature=signature,
        generated=generated,
        invalid=invalid,
    )
