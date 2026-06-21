from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
import re
import inspect
import json
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import FunctionType, ModuleType

from pytyr_mcp.artifacts import fresh_output_dir
from pytyr_mcp.json_types import JsonObject, JsonValue
from pytyr_mcp.paths import relative_to


_BATCH_NAME_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _batch_slug(batch_name: str) -> str:
    return _BATCH_NAME_RE.sub("_", str(batch_name)).strip("_") or "batch"


def benchmark_root() -> Path:
    return Path(os.environ.get("PYTYR_MCP_BENCHMARK_ROOT", Path.cwd() / "data" / "planning-benchmarks")).resolve()


def generator_root() -> Path:
    return benchmark_root() / "generators" / "classical"


@dataclass(frozen=True)
class GeneratedProblem:
    index: int
    path: Path
    config: JsonObject


@dataclass(frozen=True)
class InvalidGeneratorConfig:
    index: int
    config: JsonObject
    reason: str
    error_type: str = "Error"
    error_category: str = "invalid_config"


@dataclass(frozen=True)
class SampleGeneratorOptions:
    domain_name: str
    output_dir: Path
    batch_name: str
    configs: Sequence[Mapping[str, JsonValue]]
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



def load_make_problem(domain_name: str) -> FunctionType:
    module = load_generator_module(domain_name)
    make_problem = getattr(module, "make_problem", None)
    if not isinstance(make_problem, FunctionType):
        raise AttributeError(f"{get_generator_path(domain_name)} does not define make_problem as a function")
    return make_problem



def _generator_signature(make_problem: FunctionType) -> str:
    return str(inspect.signature(make_problem))


def _call_generator(make_problem: FunctionType, config: Mapping[str, JsonValue]) -> str:
    result = make_problem(**dict(config))
    if result is None:
        raise ValueError("make_problem returned None")
    if not isinstance(result, str):
        raise TypeError(f"make_problem returned {type(result).__name__}, expected str")
    return result

def describe_make_problem(domain_name: str) -> str:
    return _generator_signature(load_make_problem(domain_name))


def _reserve_problem_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        return path.is_dir() and not any(path.iterdir())
    return True


def _fresh_problem_dir(output_dir: Path, batch_name: str) -> Path:
    slug = _batch_slug(batch_name)
    problem_dir = output_dir / slug
    if _reserve_problem_dir(problem_dir):
        return problem_dir
    for index in range(2, 10000):
        candidate = output_dir / f"{slug}-{index:03d}"
        if _reserve_problem_dir(candidate):
            return candidate
    raise RuntimeError(f"could not allocate fresh sample batch directory under {output_dir}")



def sample_generator(options: SampleGeneratorOptions) -> SampleGeneratorResult:
    make_problem = load_make_problem(options.domain_name)
    signature = _generator_signature(make_problem)
    generator_path = get_generator_path(options.domain_name)
    source_domain_path = get_generator_domain_path(options.domain_name)
    if not source_domain_path.exists():
        raise FileNotFoundError(f"Generator domain not found: {source_domain_path}")

    output_dir = fresh_output_dir(options.output_dir)
    batch_slug = _batch_slug(options.batch_name)
    problem_dir = _fresh_problem_dir(output_dir, batch_slug)

    domain_path = output_dir / "domain.pddl"
    with source_domain_path.open("rb") as source, domain_path.open("xb") as target:
        shutil.copyfileobj(source, target)

    generated: list[GeneratedProblem] = []
    invalid: list[InvalidGeneratorConfig] = []

    for index, config in enumerate(options.configs, start=1):
        config_dict = dict(config)
        try:
            problem = _call_generator(make_problem, config_dict)
        except Exception as exc:  # noqa: BLE001 - report generator feedback to the outer loop.
            invalid_config = InvalidGeneratorConfig(
                index=index,
                config=config_dict,
                reason=str(exc),
                error_type=type(exc).__name__,
                error_category="invalid_config" if isinstance(exc, TypeError | ValueError) else "generator_error",
            )
            invalid.append(invalid_config)
            if options.allow_invalid:
                continue
            break

        problem_path = problem_dir / f"{batch_slug}-{index:03d}.pddl"
        with problem_path.open("x", encoding="utf-8") as fh:
            fh.write(problem)
        generated.append(GeneratedProblem(index=index, path=problem_path, config=config_dict))

    metadata_path = problem_dir / "configs.json"
    metadata = {
        "domain_name": options.domain_name,
        "generator_path": str(generator_path),
        "signature": signature,
        "generated": [
            {"index": problem.index, "path": relative_to(problem.path, output_dir), "config": problem.config}
            for problem in generated
        ],
        "invalid": [
            {
                "index": item.index,
                "config": item.config,
                "reason": item.reason,
                "error_type": item.error_type,
                "error_category": item.error_category,
            }
            for item in invalid
        ],
    }
    with metadata_path.open("x", encoding="utf-8") as fh:
        fh.write(json.dumps(metadata, indent=2, sort_keys=True) + "\n")

    return SampleGeneratorResult(
        domain_path=domain_path,
        problem_dir=problem_dir,
        generator_path=generator_path,
        signature=signature,
        generated=generated,
        invalid=invalid,
    )
