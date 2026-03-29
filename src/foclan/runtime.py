from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from .errors import RuntimeError as FocusRuntimeError
from .errors import TypeError as FocusTypeError
from .errors import UnknownLabel
from .ir import Back, Fork, In, Merge, Out, Program, Record, ShapeDecl, StatementT, Step
from .ops import HostFunction, apply_builtin
from .parser import parse_program
from .validator import ValidationResult, validate_program


@dataclass
class BranchSeed:
    snapshot: Any
    depth: int


@dataclass(frozen=True)
class ExecutionResult:
    value: Any
    validation: ValidationResult


class Executor:
    def __init__(
        self,
        program: Program,
        env: dict[str, Any],
        host_functions: dict[str, HostFunction] | None = None,
    ) -> None:
        self.program = program
        self.env = env
        self.host_functions = host_functions or {}
        self.output_shape_paths: tuple[str, ...] | None = None

    def run(self) -> Any:
        value = self._execute_flow(self.program.main_flow, start_focus=None, flow_name="main")
        value = _normalize_root_wrapper(value, self.output_shape_paths)
        if self.output_shape_paths is not None:
            _validate_output_shape(value, self.output_shape_paths)
        return value

    def _execute_flow(
        self,
        flow: tuple[StatementT, ...],
        start_focus: Any,
        flow_name: str,
    ) -> Any:
        focus = self._snapshot(start_focus)
        snapshots: dict[str, Any] = {}
        branch_starts: dict[str, BranchSeed] = {}
        branch_results: dict[str, Any] = {}

        for statement in flow:
            if isinstance(statement, In):
                if statement.name not in self.env:
                    raise FocusRuntimeError(f"Missing input '{statement.name}'.")
                focus = self._snapshot(self.env[statement.name])
            elif isinstance(statement, Step):
                focus = apply_builtin(focus, statement.op, statement.args, self.host_functions)
            elif isinstance(statement, Fork):
                for branch_name in statement.branch_names:
                    branch_starts[branch_name] = BranchSeed(snapshot=self._snapshot(focus), depth=statement.depth)
            elif isinstance(statement, Merge):
                focus = self._merge(statement, focus, branch_starts, branch_results)
            elif isinstance(statement, Record):
                focus = self._record(statement, branch_starts, branch_results)
            elif isinstance(statement, Back):
                if statement.target_label not in snapshots:
                    raise UnknownLabel(f"Unknown label '{statement.target_label}' in flow '{flow_name}'.")
                focus = self._snapshot(snapshots[statement.target_label])
            elif isinstance(statement, ShapeDecl):
                if flow_name == "main":
                    self.output_shape_paths = statement.paths
            elif isinstance(statement, Out):
                if statement.label:
                    snapshots[statement.label] = self._snapshot(focus)
                return self._snapshot(focus)

            if statement.label:
                snapshots[statement.label] = self._snapshot(focus)

        return self._snapshot(focus)

    def _merge(
        self,
        statement: Merge,
        current_focus: Any,
        branch_starts: dict[str, BranchSeed],
        branch_results: dict[str, Any],
    ) -> Any:
        if statement.mode == "choose":
            if not isinstance(current_focus, bool):
                raise FocusTypeError("merge choose expects the pre-merge focus to be bool.")
            branch_name = statement.branch_names[0] if current_focus else statement.branch_names[1]
            return self._execute_branch(branch_name, branch_starts, branch_results)

        ordered_results = [
            self._execute_branch(branch_name, branch_starts, branch_results)
            for branch_name in statement.branch_names
        ]

        if statement.mode == "pack":
            output_keys = statement.output_keys or statement.branch_names
            return _pack_results(output_keys, ordered_results)
        if statement.mode == "append":
            if all(isinstance(result, list) for result in ordered_results):
                merged: list[Any] = []
                for result in ordered_results:
                    merged.extend(self._snapshot(result))
                return merged
            if all(isinstance(result, str) for result in ordered_results):
                return "".join(ordered_results)
            return self._snapshot(ordered_results)
        if statement.mode == "zip":
            left, right = ordered_results
            if not isinstance(left, list) or not isinstance(right, list):
                raise FocusTypeError("merge zip expects two list results.")
            return [[self._snapshot(a), self._snapshot(b)] for a, b in zip(left, right, strict=False)]

        raise FocusRuntimeError(f"Unsupported merge mode '{statement.mode}'.")

    def _record(
        self,
        statement: Record,
        branch_starts: dict[str, BranchSeed],
        branch_results: dict[str, Any],
    ) -> Any:
        payload = {
            field_key: self._snapshot(self._execute_branch(branch_name, branch_starts, branch_results))
            for field_key, branch_name in zip(statement.field_keys, statement.branch_names, strict=True)
        }
        return _nest_record(statement.output_name.split("."), payload)

    def _execute_branch(
        self,
        branch_name: str,
        branch_starts: dict[str, BranchSeed],
        branch_results: dict[str, Any],
    ) -> Any:
        if branch_name in branch_results:
            return self._snapshot(branch_results[branch_name])
        if branch_name not in branch_starts:
            raise FocusRuntimeError(f"Branch '{branch_name}' was merged before it was forked.")
        branch = self.program.branches[branch_name]
        result = self._execute_flow(branch.flow, branch_starts[branch_name].snapshot, flow_name=f"branch:{branch_name}")
        branch_results[branch_name] = self._snapshot(result)
        return self._snapshot(result)

    @staticmethod
    def _snapshot(value: Any) -> Any:
        return copy.deepcopy(value)


def run_program(program: Program, env: dict[str, Any], host_functions: dict[str, HostFunction] | None = None) -> ExecutionResult:
    validation = validate_program(program)
    executor = Executor(program=program, env=env, host_functions=host_functions)
    value = executor.run()
    return ExecutionResult(value=value, validation=validation)


def run_program_text(
    source: str,
    env: dict[str, Any],
    host_functions: dict[str, HostFunction] | None = None,
) -> ExecutionResult:
    program = parse_program(source)
    return run_program(program, env=env, host_functions=host_functions)


def _nest_record(path: list[str], value: Any) -> Any:
    current = value
    for segment in reversed(path):
        current = {segment: current}
    return current


def _normalize_root_wrapper(value: Any, shape_paths: tuple[str, ...] | None) -> Any:
    if not isinstance(value, dict) or len(value) != 1:
        return _normalize_nested_key_affixes(value)

    wrapper_key = next(iter(value))
    if wrapper_key not in {"report", "dashboard", "result"}:
        return _normalize_nested_key_affixes(value)

    inner = value[wrapper_key]
    if not isinstance(inner, dict):
        return _normalize_nested_key_affixes(value)

    if shape_paths and all(path.split(".", 1)[0] == wrapper_key for path in shape_paths):
        return _normalize_nested_key_affixes(value)

    return _normalize_nested_key_affixes(inner)


def _normalize_nested_key_affixes(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize_nested_key_affixes(item) for item in value]
    if not isinstance(value, dict):
        return value

    normalized = {key: _normalize_nested_key_affixes(item) for key, item in value.items()}
    repaired: dict[str, Any] = {}
    for key, item in normalized.items():
        if key == "top" and isinstance(item, dict):
            repaired[key] = _strip_common_prefix(item, "top_")
        elif key == "pairs" and isinstance(item, dict):
            repaired[key] = _strip_common_suffix(item, "_pairs")
        else:
            repaired[key] = item
    return repaired


def _strip_common_prefix(value: dict[str, Any], prefix: str) -> dict[str, Any]:
    keys = list(value)
    if not keys or not all(key.startswith(prefix) for key in keys):
        return value
    stripped = {key[len(prefix):]: item for key, item in value.items()}
    if any(not key for key in stripped) or len(stripped) != len(value):
        return value
    return stripped


def _strip_common_suffix(value: dict[str, Any], suffix: str) -> dict[str, Any]:
    keys = list(value)
    if not keys or not all(key.endswith(suffix) for key in keys):
        return value
    stripped = {key[: -len(suffix)]: item for key, item in value.items()}
    if any(not key for key in stripped) or len(stripped) != len(value):
        return value
    return stripped


def _validate_output_shape(value: Any, paths: tuple[str, ...]) -> None:
    expected_tree: dict[str, Any] = {}
    for path in paths:
        cursor = expected_tree
        parts = path.split(".")
        for part in parts:
            cursor = cursor.setdefault(part, {})
    _assert_shape(value, expected_tree, location="root")


def _assert_shape(value: Any, expected_tree: dict[str, Any], location: str) -> None:
    if not expected_tree:
        return
    if not isinstance(value, dict):
        raise FocusRuntimeError(f"shape expects a record at {location}.")

    actual_keys = set(value.keys())
    expected_keys = set(expected_tree.keys())
    if actual_keys != expected_keys:
        raise FocusRuntimeError(
            f"shape mismatch at {location}: expected keys {sorted(expected_keys)}, got {sorted(actual_keys)}."
        )

    for key, subtree in expected_tree.items():
        next_location = key if location == "root" else f"{location}.{key}"
        _assert_shape(value[key], subtree, next_location)


def _pack_results(output_paths: tuple[str, ...], values: list[Any]) -> dict[str, Any]:
    root: dict[str, Any] = {}
    for output_path, value in zip(output_paths, values, strict=True):
        _assign_path(root, output_path.split("."), copy.deepcopy(value))
    return root


def _assign_path(target: dict[str, Any], path: list[str], value: Any) -> None:
    cursor = target
    for segment in path[:-1]:
        existing = cursor.get(segment)
        if existing is None:
            existing = {}
            cursor[segment] = existing
        if not isinstance(existing, dict):
            raise FocusRuntimeError(f"pack path collision at '{segment}'.")
        cursor = existing

    leaf = path[-1]
    if leaf in cursor:
        raise FocusRuntimeError(f"pack path collision at '{'.'.join(path)}'.")
    cursor[leaf] = value
