from __future__ import annotations

import ast
import json
import multiprocessing as mp
from dataclasses import dataclass
from typing import Any

from foclan.bridges import BridgeExecutionPolicy, BridgeRuntime


class PythonBridgeError(RuntimeError):
    pass


def register_bridge_runtime() -> BridgeRuntime:
    return BridgeRuntime(
        name="python",
        description="Constrained Python bridge runtime for narrow focus-to-result transforms.",
        handler=run_python_bridge,
        default_policy=BridgeExecutionPolicy(
            timeout_seconds=1.0,
            allow_imports=False,
            allow_filesystem=False,
            allow_network=False,
        ),
    )


def run_python_bridge(source: str, focus: Any, policy: BridgeExecutionPolicy) -> Any:
    _validate_python_bridge_source(source, policy)
    queue: mp.Queue[dict[str, Any]] = mp.get_context("spawn").Queue()
    process = mp.get_context("spawn").Process(target=_child_run_python_bridge, args=(queue, source, focus))
    process.start()
    process.join(policy.timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        raise PythonBridgeError(f"Python bridge timed out after {policy.timeout_seconds:.2f}s.")

    if queue.empty():
        raise PythonBridgeError("Python bridge ended without returning a result.")

    payload = queue.get()
    if payload["status"] == "error":
        raise PythonBridgeError(payload["message"])
    return payload["result"]


def _child_run_python_bridge(queue: mp.Queue[dict[str, Any]], source: str, focus: Any) -> None:
    try:
        namespace = {"focus": focus}
        safe_builtins = _safe_builtins()
        exec(compile(source, "<foclan-python-bridge>", "exec"), {"__builtins__": safe_builtins}, namespace)
        if "result" not in namespace:
            raise PythonBridgeError("Python bridge must assign 'result'.")
        normalized_result = _normalize_json_value(namespace["result"])
    except Exception as exc:  # pragma: no cover - child-process wrapper
        queue.put({"status": "error", "message": str(exc)})
        return

    queue.put({"status": "ok", "result": normalized_result})


def _validate_python_bridge_source(source: str, policy: BridgeExecutionPolicy) -> None:
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as exc:  # pragma: no cover - exercised through runtime path
        raise PythonBridgeError(f"Python bridge syntax error: {exc.msg}") from exc

    forbidden = (
        ast.Import,
        ast.ImportFrom,
        ast.With,
        ast.AsyncWith,
        ast.Try,
        ast.Raise,
        ast.ClassDef,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.Global,
        ast.Nonlocal,
        ast.Delete,
        ast.Await,
        ast.Yield,
        ast.YieldFrom,
    )
    if policy.allow_imports:
        forbidden = tuple(node for node in forbidden if node not in {ast.Import, ast.ImportFrom})

    for node in ast.walk(tree):
        if isinstance(node, forbidden):
            raise PythonBridgeError(f"Python bridge disallows node type {type(node).__name__}.")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise PythonBridgeError("Python bridge disallows dunder names.")
        if isinstance(node, ast.Attribute) and str(getattr(node, "attr", "")).startswith("__"):
            raise PythonBridgeError("Python bridge disallows dunder attribute access.")


def _safe_builtins() -> dict[str, Any]:
    return {
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "dict": dict,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "int": int,
        "isinstance": isinstance,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "range": range,
        "reversed": reversed,
        "round": round,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
    }


def _normalize_json_value(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False))
    except TypeError as exc:
        raise PythonBridgeError("Python bridge result must be JSON-serializable.") from exc
