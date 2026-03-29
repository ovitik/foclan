from __future__ import annotations

from typing import Any

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
    "top",
    "sort",
    "take",
    "uniq",
    "keys",
    "len",
    "argmax",
    "most_common",
    "const",
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


def run_program_text(source: str, env: dict[str, Any], host_functions: dict[str, Any] | None = None):
    _enforce_v1_subset(source)
    return _run_program_text(source, env=env, host_functions=host_functions)


def _enforce_v1_subset(source: str) -> None:
    for line_no, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        tokens = line.split()
        if tokens[0].startswith("@"):
            tokens = tokens[1:]
            if not tokens:
                raise ValueError(f"Line {line_no}: label must be followed by an instruction.")

        op = tokens[0]
        if op in {"branch", "end", "out"}:
            continue
        if op == "merge":
            raise ValueError(
                f"Line {line_no}: Foclan 1.0 recommended dialect does not allow explicit 'merge'. "
                "Use pack/append/zip/choose directly."
            )
        if op not in SUPPORTED_DEFAULT_OPS and op not in SUPPORTED_ADVANCED_OPS:
            raise ValueError(f"Line {line_no}: op '{op}' is outside the Foclan 1.0 product subset.")
