from __future__ import annotations

import argparse
import json
import sys
from io import StringIO
from pathlib import Path
from typing import Any

from .api import parse_program, run_program_text, validate_program
from .benchmarking import list_public_suites, run_benchmark
from .extensions import list_installed_extensions, load_host_functions
from .examples import get_current_example, list_current_examples, load_example_env, load_example_source
from .prompting import load_prompt_bundle
from .scaffolding import write_scaffold


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="foclan")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a Foclan 1.0 program.")
    run_parser.add_argument("program", type=Path)
    run_parser.add_argument("--env", required=True, type=Path)
    run_parser.add_argument("--dotenv", nargs="?", const=Path(".env"), type=Path)

    validate_parser = subparsers.add_parser("validate", help="Validate a Foclan 1.0 program.")
    validate_parser.add_argument("program", type=Path)

    prompt_parser = subparsers.add_parser("prompt", help="Render the Foclan 1.0 production prompt bundle.")
    prompt_parser.add_argument("--anti-overthinking", action="store_true")
    prompt_parser.add_argument("--task")
    prompt_parser.add_argument("--inputs-file", type=Path)

    init_parser = subparsers.add_parser("init", help="Write Codex or Cursor integration files into a project.")
    init_parser.add_argument("target", choices=("codex", "cursor", "all", "project"))
    init_parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    init_parser.add_argument("--force", action="store_true")

    extensions_parser = subparsers.add_parser("extensions", help="Inspect installed host-function extensions.")
    extensions_subparsers = extensions_parser.add_subparsers(dest="extensions_command", required=True)
    extensions_subparsers.add_parser("list", help="List installed extensions and host functions.")

    examples_parser = subparsers.add_parser("examples", help="Work with current Foclan 1.0 examples.")
    examples_subparsers = examples_parser.add_subparsers(dest="examples_command", required=True)

    examples_subparsers.add_parser("list", help="List current examples.")

    examples_validate = examples_subparsers.add_parser("validate", help="Validate one example or all current examples.")
    examples_validate.add_argument("name", nargs="?")

    examples_run = examples_subparsers.add_parser("run", help="Run a current example with its default env.")
    examples_run.add_argument("name")
    examples_run.add_argument("--dotenv", nargs="?", const=Path(".env"), type=Path)

    benchmark_parser = subparsers.add_parser("benchmark", help="Run the public exact-output benchmark.")
    benchmark_subparsers = benchmark_parser.add_subparsers(dest="benchmark_command", required=True)

    benchmark_subparsers.add_parser("list-suites", help="List bundled public benchmark suites.")

    benchmark_run = benchmark_subparsers.add_parser("run", help="Run the bundled public benchmark.")
    benchmark_run.add_argument("--provider", choices=("openai", "anthropic", "google"), required=True)
    benchmark_run.add_argument("--model", required=True)
    benchmark_run.add_argument("--languages", nargs="+", default=["foclan", "python"], choices=("foclan", "python"))
    benchmark_run.add_argument("--suite", default="main-106")
    benchmark_run.add_argument("--difficulties", nargs="*")
    benchmark_run.add_argument("--sample-size", type=int)
    benchmark_run.add_argument("--seed", type=int, default=42)
    benchmark_run.add_argument("--max-output-tokens", type=int, default=2000)
    benchmark_run.add_argument("--reasoning-effort", default="none")
    benchmark_run.add_argument("--anti-overthinking", action="store_true")
    benchmark_run.add_argument("--parallelism", type=int, default=4)
    benchmark_run.add_argument("--timeout-seconds", type=float, default=60.0)
    benchmark_run.add_argument("--output-dir", type=Path, default=Path("benchmark-results"))
    benchmark_run.add_argument("--dotenv", nargs="?", const=Path(".env"), type=Path)

    args = parser.parse_args(argv)

    if args.command == "run":
        if args.dotenv is not None:
            _load_dotenv(args.dotenv)
        env = _load_json(args.env)
        source = _read_text(args.program)
        result = run_program_text(source, env=env, host_functions=load_host_functions())
        print(json.dumps(result.value, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.command == "validate":
        source = _read_text(args.program)
        program = parse_program(source)
        result = validate_program(program)
        print(json.dumps({"ok": True, "max_branch_depth": result.max_branch_depth}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "prompt":
        bundle = load_prompt_bundle()
        inputs_json = None
        if args.inputs_file is not None:
            inputs_json = _read_text(args.inputs_file).strip()
        _safe_print(
            bundle.assemble(
                include_anti_overthinking=args.anti_overthinking,
                task_text=args.task,
                inputs_json=inputs_json,
            )
        )
        return 0

    if args.command == "init":
        written = write_scaffold(args.target, project_dir=args.project_dir, force=args.force)
        payload = {"project_dir": str(args.project_dir), "written": [str(path) for path in written]}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "extensions":
        if args.extensions_command == "list":
            payload = [
                {
                    "name": extension.name,
                    "description": extension.description,
                    "host_functions": sorted(extension.host_functions),
                }
                for extension in list_installed_extensions()
            ]
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

    if args.command == "examples":
        if args.examples_command == "list":
            payload = [
                {
                    "name": entry.name,
                    "program": entry.program_hint,
                    "env": entry.env_hint,
                    "description": entry.description,
                    "requires_extensions": list(entry.requires_extensions),
                }
                for entry in list_current_examples()
            ]
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.examples_command == "validate":
            entries = (get_current_example(args.name),) if args.name else list_current_examples()
            payload = []
            for entry in entries:
                source = load_example_source(entry)
                program = parse_program(source)
                result = validate_program(program)
                payload.append({"name": entry.name, "ok": True, "max_branch_depth": result.max_branch_depth})
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.examples_command == "run":
            entry = get_current_example(args.name)
            installed_extensions = {extension.name for extension in list_installed_extensions()}
            missing_extensions = [name for name in entry.requires_extensions if name not in installed_extensions]
            if missing_extensions:
                joined = ", ".join(missing_extensions)
                raise RuntimeError(
                    f"Example '{entry.name}' requires missing extension(s): {joined}. "
                    "Install the optional package(s) and retry."
                )
            if args.dotenv is not None:
                _load_dotenv(args.dotenv)
            source = load_example_source(entry)
            env = load_example_env(entry)
            result = run_program_text(source, env=env, host_functions=load_host_functions())
            print(json.dumps(result.value, ensure_ascii=False, indent=2, sort_keys=True))
            return 0

    if args.command == "benchmark":
        if args.benchmark_command == "list-suites":
            print(json.dumps(list(list_public_suites()), ensure_ascii=False, indent=2))
            return 0

        if args.benchmark_command == "run":
            if args.dotenv is not None:
                _load_dotenv(args.dotenv)
            report = run_benchmark(
                provider=args.provider,
                model=args.model,
                languages=tuple(args.languages),
                suite=args.suite,
                difficulties=tuple(args.difficulties) if args.difficulties else None,
                sample_size=args.sample_size,
                seed=args.seed,
                max_output_tokens=args.max_output_tokens,
                reasoning_effort=args.reasoning_effort,
                include_anti_overthinking=args.anti_overthinking,
                parallelism=args.parallelism,
                timeout_seconds=args.timeout_seconds,
                output_dir=args.output_dir,
            )
            print(
                json.dumps(
                    {
                        "suite": report["suite"],
                        "provider": report["provider"],
                        "model": report["model"],
                        "reasoning_effort": report["reasoning_effort"],
                        "overall_summary": report["overall_summary"],
                        "json_path": report["json_path"],
                        "markdown_path": report["markdown_path"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

    raise AssertionError(f"Unsupported command {args.command}")


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(_read_text(path))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist.")
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise RuntimeError(
            "Loading .env files requires python-dotenv. Install foclan-llm or python-dotenv."
        ) from exc
    text = path.read_text(encoding="utf-8-sig")
    load_dotenv(stream=StringIO(text), override=False)


def _safe_print(text: str) -> None:
    try:
        print(text)
    except BrokenPipeError:
        try:
            sys.stdout.close()
        finally:
            raise SystemExit(0)
