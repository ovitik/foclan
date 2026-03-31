from __future__ import annotations

from typing import Any

from .bridges import load_bridge_runtimes
from .extensions import load_host_functions
from .parser import parse_program as _parse_program
from .runtime import run_program_text as _run_program_text
from .validator import validate_program as _validate_program


SUPPORTED_DEFAULT_OPS = {
    "in",
    "out",
    "fork",
    "branch",
    "end",
    "pack",
    "append",
    "zip",
    "choose",
    "keep",
    "drop",
    "where_true",
    "where_false",
    "where_eq",
    "where_gt",
    "map",
    "group",
    "count",
    "count_by",
    "count_rows",
    "count_map",
    "top",
    "sort",
    "sort_desc",
    "take",
    "uniq",
    "keys",
    "len",
    "argmax",
    "most_common",
    "const",
    "call",
    "bridge",
}

SUPPORTED_ADVANCED_OPS = {
    "namespace",
    "record",
    "shape",
    "back",
    "where_neq",
    "where_lt",
    "zip_fields",
    "get",
    "id",
}


def parse_program(source: str):
    program = _parse_program(source)
    _enforce_v1_subset(source)
    return program


def validate_program(program):
    return _validate_program(program)


def run_program_text(
    source: str,
    env: dict[str, Any],
    host_functions: dict[str, Any] | None = None,
    bridge_runtimes: dict[str, Any] | None = None,
):
    _enforce_v1_subset(source)
    resolved_host_functions = host_functions if host_functions is not None else load_host_functions()
    return _run_program_text(
        source,
        env=env,
        host_functions=resolved_host_functions,
        bridge_runtimes=bridge_runtimes if bridge_runtimes is not None else load_bridge_runtimes(),
    )


def _enforce_v1_subset(source: str) -> None:
    in_bridge = False
    for line_no, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.lstrip("\ufeff").split("#", 1)[0].strip()
        if not line:
            continue

        if in_bridge:
            if line == "end":
                in_bridge = False
            continue

        tokens = line.split()
        if tokens[0].startswith("@"):
            tokens = tokens[1:]
            if not tokens:
                raise ValueError(f"Line {line_no}: label must be followed by an instruction.")

        op = tokens[0]
        if op in {"branch", "end", "out"}:
            continue
        if op == "bridge":
            if len(tokens) != 2:
                raise ValueError(f"Line {line_no}: bridge requires exactly one runtime name.")
            in_bridge = True
            continue
        if op == "merge":
            raise ValueError(
                f"Line {line_no}: Foclan 1.0 recommended dialect does not allow explicit 'merge'. "
                "Use pack/append/zip/choose directly."
            )
        if op not in SUPPORTED_DEFAULT_OPS and op not in SUPPORTED_ADVANCED_OPS:
            raise ValueError(f"Line {line_no}: op '{op}' is outside the Foclan 1.0 product subset.")
    if in_bridge:
        raise ValueError("bridge block is missing a closing end.")
