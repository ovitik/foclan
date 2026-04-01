from __future__ import annotations

from dataclasses import dataclass

from .errors import DuplicateLabel, InvalidBackTarget, InvalidMerge, ParseError, UnknownBranch, UnknownLabel
from .ir import Back, Bridge, Fork, In, Merge, Out, Program, Record, ShapeDecl, StatementT, Step
from .ops import BUILTIN_SPECS, ZERO_ARG_ELEMENT_OPS, parse_literal

SHAPE_UNKNOWN = "unknown"
SHAPE_RECORD = "record"
SHAPE_TEXT = "text"
SHAPE_BOOL = "bool"
SHAPE_LIST_RECORDS = "list_records"
SHAPE_GROUPED_LIST = "grouped_list"
SHAPE_LIST_SCALAR = "list_scalar"
SHAPE_LIST_ANY = "list_any"
SHAPE_SCALAR = "scalar"

LIST_SHAPES = {SHAPE_LIST_RECORDS, SHAPE_GROUPED_LIST, SHAPE_LIST_SCALAR, SHAPE_LIST_ANY}


@dataclass(frozen=True)
class ValidationResult:
    max_branch_depth: int


def validate_program(program: Program) -> ValidationResult:
    assigned_branches: dict[str, str] = {}
    max_branch_depth = 0

    def validate_flow(
        flow: tuple[StatementT, ...],
        flow_name: str,
        expected_fork_depth: int,
        start_shape: str,
    ) -> None:
        nonlocal max_branch_depth

        labels: dict[str, int] = {}
        label_shapes: dict[str, str] = {}
        branch_input_shapes: dict[str, str] = {}
        shape_decl_count = 0
        seen_out = False
        current_shape = start_shape

        for index, statement in enumerate(flow):
            if statement.label:
                if statement.label in labels:
                    raise DuplicateLabel(
                        f"Line {statement.line_no}: label '{statement.label}' is duplicated in flow '{flow_name}'."
                    )
                labels[statement.label] = index

        for index, statement in enumerate(flow):
            if isinstance(statement, In):
                current_shape = SHAPE_UNKNOWN
            elif isinstance(statement, Step):
                _validate_builtin_arity(statement.op, statement.args, statement.line_no)
                current_shape = _next_shape_for_step(current_shape, statement)
            elif isinstance(statement, Back):
                if statement.target_label not in labels:
                    raise UnknownLabel(
                        f"Line {statement.line_no}: label '{statement.target_label}' does not exist in flow '{flow_name}'."
                    )
                if labels[statement.target_label] >= index:
                    raise InvalidBackTarget(
                        f"Line {statement.line_no}: back target '{statement.target_label}' must be earlier in flow '{flow_name}'."
                    )
                current_shape = label_shapes[statement.target_label]
            elif isinstance(statement, Fork):
                if statement.depth < expected_fork_depth:
                    raise ParseError(
                        f"Line {statement.line_no}: fork depth inside '{flow_name}' must be at least d{expected_fork_depth}, got {statement.raw_depth}."
                    )
                max_branch_depth = max(max_branch_depth, statement.depth)
                for branch_name in statement.branch_names:
                    if branch_name not in program.branches:
                        raise UnknownBranch(f"Line {statement.line_no}: branch '{branch_name}' is not defined.")
                    if branch_name in assigned_branches:
                        owner = assigned_branches[branch_name]
                        raise ParseError(
                            f"Line {statement.line_no}: branch '{branch_name}' is already owned by flow '{owner}'."
                        )
                    assigned_branches[branch_name] = flow_name
                    branch_input_shapes[branch_name] = current_shape
            elif isinstance(statement, Merge):
                _validate_merge(statement)
                for branch_name in statement.branch_names:
                    _validate_branch_reference(program, assigned_branches, flow_name, statement.line_no, branch_name)
                current_shape = _shape_after_merge(statement.mode, current_shape)
            elif isinstance(statement, Record):
                _validate_record(statement)
                for branch_name in statement.branch_names:
                    _validate_branch_reference(program, assigned_branches, flow_name, statement.line_no, branch_name)
                current_shape = SHAPE_RECORD
            elif isinstance(statement, ShapeDecl):
                if flow_name != "main":
                    raise ParseError(f"Line {statement.line_no}: shape declarations are only allowed in the main flow.")
                if seen_out:
                    raise ParseError(f"Line {statement.line_no}: shape must appear before out.")
                shape_decl_count += 1
                if shape_decl_count > 1:
                    raise ParseError(f"Line {statement.line_no}: only one shape declaration is allowed.")
                _validate_shape_decl(statement)
            elif isinstance(statement, Bridge):
                if not statement.runtime:
                    raise ParseError(f"Line {statement.line_no}: bridge runtime name must be non-empty.")
                if not statement.source.strip():
                    raise ParseError(f"Line {statement.line_no}: bridge '{statement.runtime}' body must not be empty.")
                current_shape = SHAPE_UNKNOWN
            elif isinstance(statement, Out):
                seen_out = True

            if statement.label:
                label_shapes[statement.label] = current_shape

        for statement in flow:
            if isinstance(statement, Fork):
                for branch_name in statement.branch_names:
                    branch = program.branches[branch_name]
                    validate_flow(
                        branch.flow,
                        f"branch:{branch_name}",
                        statement.depth + 1,
                        branch_input_shapes.get(branch_name, SHAPE_UNKNOWN),
                    )

    validate_flow(program.main_flow, "main", 1, SHAPE_UNKNOWN)

    dangling = [name for name in program.branches if name not in assigned_branches]
    if dangling:
        raise UnknownBranch(f"Branches are defined but never forked: {', '.join(sorted(dangling))}.")

    return ValidationResult(max_branch_depth=max_branch_depth)


def _validate_builtin_arity(op: str, args: tuple[str, ...], line_no: int) -> None:
    if op not in BUILTIN_SPECS:
        return
    spec = BUILTIN_SPECS[op]
    if len(args) < spec.min_args:
        raise ParseError(f"Line {line_no}: op '{op}' expects at least {spec.min_args} args.")
    if spec.max_args is not None and len(args) > spec.max_args:
        raise ParseError(f"Line {line_no}: op '{op}' expects at most {spec.max_args} args.")


def _validate_branch_reference(
    program: Program,
    assigned_branches: dict[str, str],
    flow_name: str,
    line_no: int,
    branch_name: str,
) -> None:
    if branch_name not in program.branches:
        raise UnknownBranch(f"Line {line_no}: branch '{branch_name}' is not defined.")
    owner = assigned_branches.get(branch_name)
    if owner != flow_name:
        raise InvalidMerge(f"Line {line_no}: branch '{branch_name}' cannot be used from flow '{flow_name}'.")


def _validate_merge(statement: Merge) -> None:
    count = len(statement.branch_names)
    if statement.mode not in {"pack", "append", "zip", "choose"}:
        raise InvalidMerge(f"Line {statement.line_no}: unknown merge mode '{statement.mode}'.")
    if statement.mode in {"zip", "choose"} and count != 2:
        raise InvalidMerge(f"Line {statement.line_no}: merge {statement.mode} requires exactly two branches.")
    if statement.mode in {"pack", "append"} and count < 1:
        raise InvalidMerge(f"Line {statement.line_no}: merge {statement.mode} requires at least one branch.")
    if statement.mode == "pack" and statement.output_keys is not None:
        if len(set(statement.output_keys)) != len(statement.output_keys):
            raise ParseError(f"Line {statement.line_no}: merge pack output keys must be unique.")
        _validate_output_paths(statement.line_no, statement.output_keys)


def _validate_record(statement: Record) -> None:
    if not statement.output_name or any(not part for part in statement.output_name.split(".")):
        raise ParseError(f"Line {statement.line_no}: record output name must be a non-empty dotted path.")
    if len(statement.branch_names) != len(statement.field_keys):
        raise ParseError(f"Line {statement.line_no}: record field keys must match branch count.")
    if len(set(statement.field_keys)) != len(statement.field_keys):
        raise ParseError(f"Line {statement.line_no}: record field keys must be unique.")
    if any("." in key or not key for key in statement.field_keys):
        raise ParseError(f"Line {statement.line_no}: record field keys must be simple non-empty names.")


def _validate_shape_decl(statement: ShapeDecl) -> None:
    seen: set[str] = set()
    for path in statement.paths:
        if not path or any(not part for part in path.split(".")):
            raise ParseError(f"Line {statement.line_no}: shape paths must be non-empty dotted paths.")
        if path in seen:
            raise ParseError(f"Line {statement.line_no}: duplicate shape path '{path}'.")
        seen.add(path)
    for path in statement.paths:
        for other in statement.paths:
            if path == other:
                continue
            if other.startswith(f"{path}."):
                raise ParseError(
                    f"Line {statement.line_no}: shape path '{path}' cannot also be a parent of '{other}'."
                )


def _validate_output_paths(line_no: int, paths: tuple[str, ...]) -> None:
    for path in paths:
        if not path or any(not part for part in path.split(".")):
            raise ParseError(f"Line {line_no}: pack output paths must be non-empty dotted paths.")
    for path in paths:
        for other in paths:
            if path == other:
                continue
            if other.startswith(f"{path}.") or path.startswith(f"{other}."):
                raise ParseError(
                    f"Line {line_no}: pack output path '{path}' conflicts with '{other}'."
                )


def _shape_after_merge(mode: str, current_shape: str) -> str:
    if mode == "pack":
        return SHAPE_RECORD
    if mode in {"append", "zip"}:
        return SHAPE_LIST_ANY
    if mode == "choose":
        return SHAPE_UNKNOWN
    return current_shape


def _next_shape_for_step(current_shape: str, statement: Step) -> str:
    op = statement.op
    line_no = statement.line_no

    if op not in BUILTIN_SPECS:
        return SHAPE_UNKNOWN

    if op == "id":
        return current_shape
    if op == "const":
        return _infer_literal_shape(parse_literal(" ".join(statement.args)))
    if op == "get":
        _ensure_shape(line_no, op, current_shape, {SHAPE_RECORD, *LIST_SHAPES})
        return SHAPE_UNKNOWN
    if op == "len":
        _ensure_shape(line_no, op, current_shape, {SHAPE_RECORD, SHAPE_TEXT, *LIST_SHAPES})
        return SHAPE_SCALAR
    if op == "keys":
        _ensure_shape(line_no, op, current_shape, {SHAPE_RECORD})
        return SHAPE_LIST_SCALAR
    if op == "vals":
        _ensure_shape(line_no, op, current_shape, {SHAPE_RECORD})
        return SHAPE_LIST_ANY
    if op in {"eq", "neq", "gt", "lt", "not"}:
        return SHAPE_BOOL
    if op in {"keep", "drop", "where_true", "where_false", "where_eq", "where_neq", "where_gt", "where_lt"}:
        _ensure_shape(line_no, op, current_shape, {SHAPE_LIST_RECORDS, SHAPE_GROUPED_LIST})
        return SHAPE_LIST_RECORDS if current_shape != SHAPE_GROUPED_LIST else SHAPE_GROUPED_LIST
    if op == "map":
        _ensure_shape(line_no, op, current_shape, LIST_SHAPES)
        if current_shape in {SHAPE_LIST_RECORDS, SHAPE_GROUPED_LIST}:
            return SHAPE_LIST_SCALAR
        if current_shape == SHAPE_LIST_SCALAR and statement.args and statement.args[0] in ZERO_ARG_ELEMENT_OPS:
            return SHAPE_LIST_SCALAR
        return SHAPE_LIST_ANY
    if op == "group":
        _ensure_shape(line_no, op, current_shape, {SHAPE_LIST_RECORDS})
        return SHAPE_GROUPED_LIST
    if op == "count":
        if current_shape == SHAPE_GROUPED_LIST:
            return SHAPE_LIST_RECORDS
        _ensure_shape(line_no, op, current_shape, LIST_SHAPES | {SHAPE_RECORD})
        if current_shape in LIST_SHAPES:
            return SHAPE_SCALAR
        return SHAPE_UNKNOWN
    if op == "count_by":
        _ensure_shape(line_no, op, current_shape, {SHAPE_LIST_RECORDS})
        return SHAPE_LIST_RECORDS
    if op == "count_rows":
        _ensure_shape(line_no, op, current_shape, {SHAPE_LIST_RECORDS})
        return SHAPE_LIST_RECORDS
    if op == "count_map":
        _ensure_shape(line_no, op, current_shape, {SHAPE_LIST_RECORDS})
        return SHAPE_RECORD
    if op in {"top", "argmax", "argmin"}:
        _ensure_shape(line_no, op, current_shape, {SHAPE_LIST_RECORDS, SHAPE_GROUPED_LIST, SHAPE_LIST_ANY})
        return SHAPE_RECORD
    if op == "most_common":
        _ensure_shape(line_no, op, current_shape, {SHAPE_LIST_RECORDS, SHAPE_GROUPED_LIST, SHAPE_LIST_ANY})
        return SHAPE_SCALAR
    if op in {"sort", "sort_desc"}:
        allowed = {SHAPE_LIST_RECORDS, SHAPE_GROUPED_LIST, SHAPE_LIST_ANY}
        if not statement.args:
            allowed |= {SHAPE_LIST_SCALAR}
        _ensure_shape(line_no, op, current_shape, allowed)
        return current_shape if current_shape != SHAPE_UNKNOWN else SHAPE_LIST_ANY
    if op == "take":
        _ensure_shape(line_no, op, current_shape, LIST_SHAPES | {SHAPE_TEXT})
        return current_shape
    if op == "flat":
        _ensure_shape(line_no, op, current_shape, LIST_SHAPES)
        return SHAPE_LIST_ANY
    if op == "uniq":
        _ensure_shape(line_no, op, current_shape, LIST_SHAPES)
        return current_shape if current_shape != SHAPE_UNKNOWN else SHAPE_LIST_ANY
    if op == "zip_fields":
        _ensure_shape(line_no, op, current_shape, {SHAPE_LIST_RECORDS, SHAPE_GROUPED_LIST})
        return SHAPE_LIST_ANY
    if op in {"lower", "upper", "trim"}:
        _ensure_shape(line_no, op, current_shape, {SHAPE_TEXT})
        return SHAPE_TEXT
    if op == "split":
        _ensure_shape(line_no, op, current_shape, {SHAPE_TEXT})
        return SHAPE_LIST_SCALAR
    if op == "join":
        _ensure_shape(line_no, op, current_shape, LIST_SHAPES)
        return SHAPE_TEXT
    if op == "call":
        return SHAPE_UNKNOWN
    if op in {"python", "python_from", "sql", "sql_from"}:
        return SHAPE_UNKNOWN

    return SHAPE_UNKNOWN


def _ensure_shape(line_no: int, op: str, current_shape: str, allowed: set[str]) -> None:
    if current_shape == SHAPE_UNKNOWN:
        return
    if current_shape not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ParseError(
            f"Line {line_no}: op '{op}' expects focus shape in {{{expected}}}, got {_shape_label(current_shape)}."
        )


def _infer_literal_shape(value: object) -> str:
    if isinstance(value, dict):
        return SHAPE_RECORD
    if isinstance(value, str):
        return SHAPE_TEXT
    if isinstance(value, bool):
        return SHAPE_BOOL
    if isinstance(value, list):
        if not value:
            return SHAPE_LIST_ANY
        if all(isinstance(item, dict) for item in value):
            return SHAPE_LIST_RECORDS
        if all(not isinstance(item, (dict, list)) for item in value):
            return SHAPE_LIST_SCALAR
        return SHAPE_LIST_ANY
    return SHAPE_SCALAR


def _shape_label(shape: str) -> str:
    return shape.replace("_", " ")
