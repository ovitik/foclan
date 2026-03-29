from __future__ import annotations

import ast
import json
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .api import run_program_text
from .prompting import load_prompt_bundle
from .resources import read_json_object


SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "getattr": getattr,
    "hasattr": hasattr,
    "int": int,
    "isinstance": isinstance,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "range": range,
    "reversed": reversed,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}

DISALLOWED_CALLS = {"eval", "exec", "open", "compile", "__import__", "input"}

PYTHON_GUIDE = """Write only Python code. No prose. No markdown fences.
Requirements:
- Define `def solve(inputs):`.
- Return the final result directly from `solve`.
- Use only the Python standard library.
- Do not import modules.
- Keep the code deterministic.
- Match the exact requested output shape.
- Do not print.
- Do not add explanations.
"""


@dataclass(frozen=True)
class PublicEvalTask:
    task_id: str
    title: str
    description: str
    difficulty: str
    env: dict[str, Any]
    expected: Any


@dataclass(frozen=True)
class ProviderUsage:
    input_tokens: int | None
    cached_tokens: int | None
    output_tokens: int | None
    reasoning_tokens: int | None
    total_tokens: int | None
    resolved_model: str | None


@dataclass(frozen=True)
class GeneratedResponse:
    text: str
    usage: ProviderUsage


@dataclass(frozen=True)
class BenchmarkCaseResult:
    task_id: str
    title: str
    difficulty: str
    language: str
    provider: str
    model: str
    reasoning_effort: str
    correct: bool
    error_free: bool
    error: str | None
    visible_code_chars: int | None
    visible_code_lines: int | None
    input_tokens: int | None
    cached_tokens: int | None
    output_tokens: int | None
    reasoning_tokens: int | None
    total_tokens: int | None
    latency_s: float
    resolved_model: str | None
    response_text: str | None
    code: str | None
    expected: Any
    actual: Any


def list_public_suites() -> tuple[str, ...]:
    return ("main-106",)


def load_public_tasks(
    suite: str = "main-106",
    difficulties: tuple[str, ...] | None = None,
    sample_size: int | None = None,
    seed: int = 42,
) -> list[PublicEvalTask]:
    payload = read_json_object("benchmarks", f"{suite}.json")
    tasks = [
        PublicEvalTask(
            task_id=row["task_id"],
            title=row["title"],
            description=row["description"],
            difficulty=row["difficulty"],
            env=row["env"],
            expected=row["expected"],
        )
        for row in payload["tasks"]
    ]
    if difficulties:
        allowed = set(difficulties)
        tasks = [task for task in tasks if task.difficulty in allowed]
    if not tasks:
        raise ValueError("No benchmark tasks matched the requested suite or difficulty filter.")
    if sample_size is not None and sample_size < len(tasks):
        generator = random.Random(seed)
        tasks = generator.sample(tasks, sample_size)
        tasks.sort(key=lambda task: task.task_id)
    return tasks


def run_benchmark(
    *,
    provider: str,
    model: str,
    languages: tuple[str, ...],
    suite: str,
    difficulties: tuple[str, ...] | None,
    sample_size: int | None,
    seed: int,
    max_output_tokens: int,
    reasoning_effort: str,
    include_anti_overthinking: bool,
    parallelism: int,
    timeout_seconds: float,
    output_dir: Path,
) -> dict[str, Any]:
    tasks = load_public_tasks(
        suite=suite,
        difficulties=difficulties,
        sample_size=sample_size,
        seed=seed,
    )
    jobs = [(language, task) for language in languages for task in tasks]
    ordered: list[BenchmarkCaseResult | None] = [None] * len(jobs)

    with ThreadPoolExecutor(max_workers=max(1, parallelism)) as executor:
        futures = {
            executor.submit(
                _run_case,
                provider=provider,
                model=model,
                language=language,
                task=task,
                reasoning_effort=reasoning_effort,
                max_output_tokens=max_output_tokens,
                include_anti_overthinking=include_anti_overthinking,
                timeout_seconds=timeout_seconds,
            ): index
            for index, (language, task) in enumerate(jobs)
        }
        for future in as_completed(futures):
            ordered[futures[future]] = future.result()

    results = [row for row in ordered if row is not None]
    report = _build_report(
        results=results,
        suite=suite,
        provider=provider,
        model=model,
        reasoning_effort=reasoning_effort,
        sample_size=sample_size,
        seed=seed,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / f"benchmark-{timestamp}.json"
    md_path = output_dir / f"benchmark-{timestamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    report["json_path"] = str(json_path)
    report["markdown_path"] = str(md_path)
    return report


def _run_case(
    *,
    provider: str,
    model: str,
    language: str,
    task: PublicEvalTask,
    reasoning_effort: str,
    max_output_tokens: int,
    include_anti_overthinking: bool,
    timeout_seconds: float,
) -> BenchmarkCaseResult:
    started = time.perf_counter()
    response_text: str | None = None
    code: str | None = None
    actual: Any = None
    error: str | None = None
    usage = ProviderUsage(
        input_tokens=None,
        cached_tokens=None,
        output_tokens=None,
        reasoning_tokens=None,
        total_tokens=None,
        resolved_model=None,
    )

    try:
        system_prompt, user_prompt = _build_generation_prompt(
            language=language,
            task=task,
            include_anti_overthinking=include_anti_overthinking,
        )
        generated = _generate_code(
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
            timeout_seconds=timeout_seconds,
        )
        response_text = generated.text
        usage = generated.usage
        code = _extract_code(response_text)
        actual = _execute_candidate(language=language, code=code, env=task.env)
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"

    correct = error is None and _values_equal(actual, task.expected)
    latency_s = time.perf_counter() - started
    return BenchmarkCaseResult(
        task_id=task.task_id,
        title=task.title,
        difficulty=task.difficulty,
        language=language,
        provider=provider,
        model=model,
        reasoning_effort=reasoning_effort,
        correct=correct,
        error_free=error is None,
        error=error,
        visible_code_chars=len(code) if code is not None else None,
        visible_code_lines=len([line for line in code.splitlines() if line.strip()]) if code is not None else None,
        input_tokens=usage.input_tokens,
        cached_tokens=usage.cached_tokens,
        output_tokens=usage.output_tokens,
        reasoning_tokens=usage.reasoning_tokens,
        total_tokens=usage.total_tokens,
        latency_s=latency_s,
        resolved_model=usage.resolved_model,
        response_text=response_text,
        code=code,
        expected=task.expected,
        actual=actual,
    )


def _build_generation_prompt(
    *,
    language: str,
    task: PublicEvalTask,
    include_anti_overthinking: bool,
) -> tuple[str, str]:
    if language == "foclan":
        bundle = load_prompt_bundle()
        return (
            "You are an exact code generator.",
            bundle.assemble(
                include_anti_overthinking=include_anti_overthinking,
                task_text=task.description,
                inputs_json=json.dumps(task.env, ensure_ascii=False, indent=2, sort_keys=True),
            ),
        )

    return (
        "You are an exact Python code generator.",
        "\n\n".join(
            [
                PYTHON_GUIDE.strip(),
                "Task:",
                task.description,
                "Inputs:",
                "```json",
                json.dumps(task.env, ensure_ascii=False, indent=2, sort_keys=True),
                "```",
            ]
        ),
    )


def _generate_code(
    *,
    provider: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_output_tokens: int,
    reasoning_effort: str,
    timeout_seconds: float,
) -> GeneratedResponse:
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Benchmarking requires httpx. Install foclan-llm or install foclan with benchmark dependencies."
        ) from exc

    provider = provider.lower()
    if provider == "openai":
        body: dict[str, Any] = {
            "model": model,
            "instructions": system_prompt,
            "input": user_prompt,
            "max_output_tokens": max_output_tokens,
        }
        if reasoning_effort != "none":
            body["reasoning"] = {"effort": reasoning_effort}
        started = time.perf_counter()
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {_require_env('OPENAI_API_KEY')}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=timeout_seconds,
        )
        elapsed = time.perf_counter() - started
        response.raise_for_status()
        payload = response.json()
        text = _extract_openai_text(payload)
        usage = payload.get("usage") if isinstance(payload, dict) else None
        return GeneratedResponse(
            text=text,
            usage=ProviderUsage(
                input_tokens=_int_or_none(usage, "input_tokens"),
                cached_tokens=_int_or_none(usage.get("input_tokens_details"), "cached_tokens")
                if isinstance(usage, dict)
                else None,
                output_tokens=_int_or_none(usage, "output_tokens"),
                reasoning_tokens=_int_or_none(usage.get("output_tokens_details"), "reasoning_tokens")
                if isinstance(usage, dict)
                else None,
                total_tokens=_int_or_none(usage, "total_tokens"),
                resolved_model=str(payload.get("model")) if isinstance(payload, dict) and payload.get("model") else model,
            ),
        )

    if provider == "anthropic":
        body = {
            "model": model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": max_output_tokens,
        }
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": _require_env("ANTHROPIC_API_KEY"),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=body,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        usage = payload.get("usage") if isinstance(payload, dict) else None
        return GeneratedResponse(
            text=_extract_anthropic_text(payload),
            usage=ProviderUsage(
                input_tokens=_int_or_none(usage, "input_tokens"),
                cached_tokens=None,
                output_tokens=_int_or_none(usage, "output_tokens"),
                reasoning_tokens=None,
                total_tokens=(
                    (_int_or_none(usage, "input_tokens") or 0) + (_int_or_none(usage, "output_tokens") or 0)
                    if isinstance(usage, dict)
                    else None
                ),
                resolved_model=str(payload.get("model")) if isinstance(payload, dict) and payload.get("model") else model,
            ),
        )

    if provider == "google":
        body = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"maxOutputTokens": max_output_tokens},
        }
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={
                "x-goog-api-key": _require_env("GEMINI_API_KEY", "GOOGLE_API_KEY"),
                "Content-Type": "application/json",
            },
            json=body,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        usage = payload.get("usageMetadata") if isinstance(payload, dict) else None
        return GeneratedResponse(
            text=_extract_google_text(payload),
            usage=ProviderUsage(
                input_tokens=_int_or_none(usage, "promptTokenCount"),
                cached_tokens=None,
                output_tokens=_int_or_none(usage, "candidatesTokenCount"),
                reasoning_tokens=_int_or_none(usage, "thoughtsTokenCount"),
                total_tokens=_int_or_none(usage, "totalTokenCount"),
                resolved_model=str(payload.get("modelVersion")) if isinstance(payload, dict) and payload.get("modelVersion") else model,
            ),
        )

    raise ValueError(f"Unsupported provider '{provider}'.")


def _extract_openai_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    if chunks:
        return "".join(chunks).strip()
    if payload.get("status") == "incomplete":
        details = payload.get("incomplete_details")
        raise RuntimeError(f"OpenAI response incomplete: {json.dumps(details, ensure_ascii=False)}")
    raise RuntimeError("OpenAI response did not contain output text.")


def _extract_anthropic_text(payload: dict[str, Any]) -> str:
    chunks = [
        block["text"]
        for block in payload.get("content", [])
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)
    ]
    if chunks:
        return "".join(chunks).strip()
    raise RuntimeError("Anthropic response did not contain text content.")


def _extract_google_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    for candidate in payload.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        for part in content.get("parts", []):
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                chunks.append(part["text"])
    if chunks:
        return "".join(chunks).strip()
    raise RuntimeError("Google response did not contain text content.")


def _extract_code(text: str) -> str:
    match = re.search(r"```(?:[a-zA-Z0-9_+-]+)?\s*(.*?)```", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def _execute_candidate(language: str, code: str, env: dict[str, Any]) -> Any:
    if language == "python":
        return _run_python_solution(code, env)
    return run_program_text(code, env).value


def _run_python_solution(code: str, env: dict[str, Any]) -> Any:
    tree = ast.parse(code, mode="exec")
    _validate_python_ast(tree)

    solve_functions = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "solve"
    ]
    if len(solve_functions) != 1:
        raise ValueError("Python solution must define exactly one solve(inputs) function.")
    if len(solve_functions[0].args.args) != 1:
        raise ValueError("solve must take exactly one argument.")

    globals_dict = {"__builtins__": SAFE_BUILTINS, "__name__": "foclan_benchmark_eval"}
    locals_dict: dict[str, Any] = {}
    exec(compile(tree, filename="<llm-python-solution>", mode="exec"), globals_dict, locals_dict)
    solve = locals_dict.get("solve") or globals_dict.get("solve")
    if not callable(solve):
        raise ValueError("solve(inputs) was not created.")
    payload = json.loads(json.dumps(env))
    return solve(payload)


def _validate_python_ast(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.Import,
                ast.ImportFrom,
                ast.Global,
                ast.Nonlocal,
                ast.AsyncFunctionDef,
                ast.Await,
                ast.With,
                ast.AsyncWith,
                ast.ClassDef,
            ),
        ):
            raise ValueError(f"Disallowed Python construct: {type(node).__name__}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError("Dunder attribute access is not allowed.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in DISALLOWED_CALLS:
            raise ValueError(f"Disallowed call: {node.func.id}")


def _values_equal(actual: Any, expected: Any) -> bool:
    return _normalize_value(actual) == _normalize_value(expected)


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize_value(inner) for key, inner in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, float):
        return round(value, 9)
    return value


def _build_report(
    *,
    results: list[BenchmarkCaseResult],
    suite: str,
    provider: str,
    model: str,
    reasoning_effort: str,
    sample_size: int | None,
    seed: int,
) -> dict[str, Any]:
    overall_rows: list[dict[str, Any]] = []
    difficulty_rows: list[dict[str, Any]] = []
    overall_grouped: dict[str, list[BenchmarkCaseResult]] = {}
    difficulty_grouped: dict[tuple[str, str], list[BenchmarkCaseResult]] = {}

    for result in results:
        overall_grouped.setdefault(result.language, []).append(result)
        difficulty_grouped.setdefault((result.language, result.difficulty), []).append(result)

    for language, rows in sorted(overall_grouped.items()):
        overall_rows.append({"language": language, **_summarize_rows(rows)})
    for (language, difficulty), rows in sorted(difficulty_grouped.items()):
        difficulty_rows.append({"language": language, "difficulty": difficulty, **_summarize_rows(rows)})

    return {
        "suite": suite,
        "provider": provider,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "sample_size": sample_size,
        "seed": seed,
        "overall_summary": overall_rows,
        "difficulty_summary": difficulty_rows,
        "cases": [asdict(result) for result in results],
    }


def _summarize_rows(rows: list[BenchmarkCaseResult]) -> dict[str, Any]:
    return {
        "cases": len(rows),
        "correct": sum(1 for row in rows if row.correct),
        "errors": sum(1 for row in rows if not row.error_free),
        "accuracy": sum(1 for row in rows if row.correct) / len(rows) if rows else 0.0,
        "error_free_rate": sum(1 for row in rows if row.error_free) / len(rows) if rows else 0.0,
        "avg_visible_code_chars": _avg(row.visible_code_chars for row in rows),
        "avg_visible_code_lines": _avg(row.visible_code_lines for row in rows),
        "avg_input_tokens": _avg(row.input_tokens for row in rows),
        "avg_cached_tokens": _avg(row.cached_tokens for row in rows),
        "avg_output_tokens": _avg(row.output_tokens for row in rows),
        "avg_reasoning_tokens": _avg(row.reasoning_tokens for row in rows),
        "avg_total_tokens": _avg(row.total_tokens for row in rows),
        "avg_latency_s": _avg(row.latency_s for row in rows),
    }


def _avg(values: Any) -> float | None:
    items = [value for value in values if value is not None]
    if not items:
        return None
    return sum(items) / len(items)


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Foclan Benchmark",
        "",
        f"- Suite: `{report['suite']}`",
        f"- Provider: `{report['provider']}`",
        f"- Model: `{report['model']}`",
        f"- Reasoning effort: `{report['reasoning_effort']}`",
        f"- Sample size: `{report['sample_size']}`",
        f"- Seed: `{report['seed']}`",
        "",
        "## Overall",
        "",
        "| Language | Cases | Correct | Errors | Accuracy | Error-free | Avg code chars | Avg code lines | Avg input tokens | Avg cached tokens | Avg output tokens | Avg reasoning tokens | Avg total tokens | Avg latency (s) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["overall_summary"]:
        lines.append(
            "| {language} | {cases} | {correct} | {errors} | {accuracy:.2%} | {error_free_rate:.2%} | {avg_visible_code_chars:.1f} | {avg_visible_code_lines:.1f} | {avg_input_tokens:.1f} | {avg_cached_tokens:.1f} | {avg_output_tokens:.1f} | {avg_reasoning_tokens:.1f} | {avg_total_tokens:.1f} | {avg_latency_s:.3f} |".format(
                language=row["language"],
                cases=row["cases"],
                correct=row["correct"],
                errors=row["errors"],
                accuracy=row["accuracy"],
                error_free_rate=row["error_free_rate"],
                avg_visible_code_chars=row["avg_visible_code_chars"] or 0.0,
                avg_visible_code_lines=row["avg_visible_code_lines"] or 0.0,
                avg_input_tokens=row["avg_input_tokens"] or 0.0,
                avg_cached_tokens=row["avg_cached_tokens"] or 0.0,
                avg_output_tokens=row["avg_output_tokens"] or 0.0,
                avg_reasoning_tokens=row["avg_reasoning_tokens"] or 0.0,
                avg_total_tokens=row["avg_total_tokens"] or 0.0,
                avg_latency_s=row["avg_latency_s"] or 0.0,
            )
        )
    lines.extend(
        [
            "",
            "## By Difficulty",
            "",
            "| Language | Difficulty | Cases | Correct | Errors | Accuracy | Avg code chars | Avg output tokens | Avg latency (s) |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report["difficulty_summary"]:
        lines.append(
            "| {language} | {difficulty} | {cases} | {correct} | {errors} | {accuracy:.2%} | {avg_visible_code_chars:.1f} | {avg_output_tokens:.1f} | {avg_latency_s:.3f} |".format(
                language=row["language"],
                difficulty=row["difficulty"],
                cases=row["cases"],
                correct=row["correct"],
                errors=row["errors"],
                accuracy=row["accuracy"],
                avg_visible_code_chars=row["avg_visible_code_chars"] or 0.0,
                avg_output_tokens=row["avg_output_tokens"] or 0.0,
                avg_latency_s=row["avg_latency_s"] or 0.0,
            )
        )
    return "\n".join(lines) + "\n"


def _require_env(*names: str) -> str:
    import os

    for name in names:
        value = os.getenv(name)
        if value:
            return value
    joined = " or ".join(names)
    raise RuntimeError(f"Missing required API key in environment: {joined}.")


def _int_or_none(container: dict[str, Any] | None, key: str) -> int | None:
    if not isinstance(container, dict):
        return None
    value = container.get(key)
    if value is None:
        return None
    return int(value)
