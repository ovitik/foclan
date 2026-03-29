from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import DuplicateBranch, ParseError
from .ir import Back, Branch, Bridge, Fork, In, Merge, Out, Program, Record, ShapeDecl, StatementT, Step

DEPTH_RE = re.compile(r"^d(\d+)$")


def parse_program(source: str) -> Program:
    try:
        return _parse_program_strict(source)
    except ParseError as exc:
        recovered = _try_recover_program(source, exc)
        if recovered is not None:
            return recovered
        raise


def _parse_program_strict(source: str) -> Program:
    parser = _Parser(source.splitlines(), source)
    return parser.parse()


@dataclass
class _Parser:
    raw_lines: list[str]
    source: str

    def __post_init__(self) -> None:
        self.index = 0
        self.branches: dict[str, Branch] = {}
        self.pending_branches: set[str] = set()

    def parse(self) -> Program:
        main_flow, stop_token, stop_line_no = self._parse_flow(scope=(), stop_tokens=None)
        if stop_token:
            raise ParseError(f"Line {stop_line_no}: unexpected {stop_token}.")
        resolved_main_flow, resolved_branches = _resolve_program_references(tuple(main_flow), self.branches)
        return Program(main_flow=resolved_main_flow, branches=resolved_branches, source=self.source)

    def _parse_flow(
        self,
        scope: tuple[str, ...],
        stop_tokens: set[str] | None,
    ) -> tuple[list[StatementT], str | None, int | None]:
        flow: list[StatementT] = []

        while self.index < len(self.raw_lines):
            line_no = self.index + 1
            line = _normalize_line(self.raw_lines[self.index])
            if not line:
                self.index += 1
                continue

            tokens = line.split()
            op = tokens[0]

            if stop_tokens and op in stop_tokens:
                self.index += 1
                return flow, op, line_no

            if op in {"end", "endns"}:
                raise ParseError(f"Line {line_no}: unexpected {op}.")

            if op == "branch":
                self._parse_branch(tokens, line_no, scope)
                continue

            if op == "bridge":
                flow.append(self._parse_bridge(tokens, line_no))
                continue

            if op == "namespace":
                if len(tokens) != 2:
                    raise ParseError(f"Line {line_no}: namespace requires exactly one name.")
                namespace_parts = tuple(_normalize_name(tokens[1]).split("."))
                self.index += 1
                inner_flow, stop_token, _ = self._parse_flow(scope + namespace_parts, {"endns", "end"})
                if stop_token not in {"endns", "end"}:
                    raise ParseError(f"Line {line_no}: namespace '{tokens[1]}' is missing a closing end.")
                flow.extend(inner_flow)
                continue

            statement = _parse_statement(line=line, line_no=line_no, scope=scope)
            if isinstance(statement, Fork):
                self.pending_branches.update(statement.branch_names)
            flow.append(statement)
            self.index += 1

        return flow, None, None

    def _parse_branch(self, tokens: list[str], line_no: int, scope: tuple[str, ...]) -> None:
        if len(tokens) != 2:
            raise ParseError(f"Line {line_no}: branch requires exactly one name.")
        branch_name = self._infer_branch_definition_name(tokens[1], scope)
        if branch_name in self.branches:
            raise DuplicateBranch(f"Line {line_no}: branch '{branch_name}' is defined more than once.")
        self.pending_branches.discard(branch_name)

        self.index += 1
        branch_scope = tuple(branch_name.split("."))
        branch_flow, stop_token, _ = self._parse_flow(scope=branch_scope, stop_tokens={"end"})
        if stop_token != "end":
            raise ParseError(f"Line {line_no}: branch '{branch_name}' is missing a closing end.")

        self.branches[branch_name] = Branch(name=branch_name, flow=tuple(branch_flow), line_no=line_no)

    def _parse_bridge(self, tokens: list[str], line_no: int) -> Bridge:
        if len(tokens) != 2:
            raise ParseError(f"Line {line_no}: bridge requires exactly one runtime name.")
        runtime = _normalize_name(tokens[1])
        self.index += 1
        body_lines: list[str] = []

        while self.index < len(self.raw_lines):
            current_line = _normalize_line(self.raw_lines[self.index])
            if current_line == "end":
                self.index += 1
                return Bridge(
                    label=None,
                    line_no=line_no,
                    runtime=runtime,
                    source="\n".join(body_lines).strip(),
                )
            body_lines.append(self.raw_lines[self.index].rstrip("\r\n"))
            self.index += 1

        raise ParseError(f"Line {line_no}: bridge '{runtime}' is missing a closing end.")

    def _infer_branch_definition_name(self, token: str, scope: tuple[str, ...]) -> str:
        normalized = _normalize_name(token)
        if normalized.startswith("."):
            return _join_scope(scope, normalized[1:])
        if "." in normalized:
            return normalized

        qualified = _qualify_name(normalized, scope)
        if qualified in self.pending_branches:
            return qualified

        scope_prefix = ".".join(scope)
        candidates = []
        for candidate in self.pending_branches:
            if scope_prefix and not candidate.startswith(f"{scope_prefix}."):
                continue
            if candidate.endswith(f".{normalized}"):
                candidates.append(candidate)
        if len(candidates) == 1:
            return candidates[0]

        return qualified


def _normalize_line(line: str) -> str:
    return line.split("#", 1)[0].strip()


def _parse_statement(line: str, line_no: int, scope: tuple[str, ...]) -> StatementT:
    tokens = line.split()
    label: str | None = None
    if tokens and tokens[0].startswith("@"):
        if len(tokens[0]) == 1:
            raise ParseError(f"Line {line_no}: empty label.")
        label = tokens[0][1:]
        tokens = tokens[1:]
        if not tokens:
            raise ParseError(f"Line {line_no}: label must be followed by an instruction.")

    op = tokens[0]
    args = tuple(tokens[1:])

    if op == "in":
        if len(args) != 1:
            raise ParseError(f"Line {line_no}: in requires exactly one input name.")
        return In(label=label, line_no=line_no, name=args[0])

    if op == "out":
        if args:
            raise ParseError(f"Line {line_no}: out does not accept arguments.")
        return Out(label=label, line_no=line_no)

    if op == "shape":
        if not args:
            raise ParseError(f"Line {line_no}: shape requires at least one path.")
        return ShapeDecl(
            label=label,
            line_no=line_no,
            paths=tuple(_normalize_name(path) for path in args),
        )

    if op == "fork":
        if len(args) < 2:
            raise ParseError(f"Line {line_no}: fork requires a depth and at least one branch.")
        match = DEPTH_RE.fullmatch(args[0])
        if not match:
            raise ParseError(f"Line {line_no}: invalid fork depth '{args[0]}'.")
        return Fork(
            label=label,
            line_no=line_no,
            depth=int(match.group(1)),
            raw_depth=args[0],
            branch_names=tuple(_qualify_name(name, scope) for name in args[1:]),
        )

    if op == "merge":
        if len(args) < 2:
            raise ParseError(f"Line {line_no}: merge requires a mode and at least one branch.")
        return _build_merge(
            label=label,
            line_no=line_no,
            mode=args[0],
            branch_tokens=args[1:],
            scope=scope,
        )

    if op in {"pack", "append", "zip", "choose"}:
        minimum = 2 if op in {"zip", "choose"} else 1
        if len(args) < minimum:
            raise ParseError(f"Line {line_no}: {op} requires at least {minimum} branch{'es' if minimum > 1 else ''}.")
        return _build_merge(
            label=label,
            line_no=line_no,
            mode=op,
            branch_tokens=args,
            scope=scope,
        )

    if op == "record":
        if args and all("=" in field_spec for field_spec in args):
            return _build_merge(
                label=label,
                line_no=line_no,
                mode="pack",
                branch_tokens=args,
                scope=scope,
            )
        if len(args) < 2:
            raise ParseError(f"Line {line_no}: record requires an output name and at least one field branch.")
        output_name = _normalize_name(args[0])
        field_keys: list[str] = []
        branch_names: list[str] = []
        for field_spec in args[1:]:
            if "=" in field_spec:
                field_key, branch_token = field_spec.split("=", 1)
                if not field_key or not branch_token:
                    raise ParseError(f"Line {line_no}: invalid record field '{field_spec}'.")
                field_keys.append(_normalize_name(field_key))
                branch_names.append(_qualify_name(branch_token, scope))
            else:
                field_keys.append(_local_output_key(field_spec))
                branch_names.append(_qualify_name(field_spec, scope))
        return Record(
            label=label,
            line_no=line_no,
            output_name=output_name,
            branch_names=tuple(branch_names),
            field_keys=tuple(field_keys),
        )

    if op == "back":
        if len(args) != 1:
            raise ParseError(f"Line {line_no}: back requires exactly one target label.")
        return Back(label=label, line_no=line_no, target_label=args[0])

    if op in {"branch", "end", "namespace", "endns", "bridge"}:
        raise ParseError(f"Line {line_no}: unexpected '{op}'.")

    return Step(label=label, line_no=line_no, op=op, args=args)


def _build_merge(
    label: str | None,
    line_no: int,
    mode: str,
    branch_tokens: tuple[str, ...],
    scope: tuple[str, ...],
) -> Merge:
    branch_names: list[str] = []
    output_keys: list[str] = []
    for token in branch_tokens:
        if mode == "pack" and "=" in token:
            output_path, branch_token = token.split("=", 1)
            if not output_path or not branch_token:
                raise ParseError(f"Line {line_no}: invalid pack mapping '{token}'.")
            branch_names.append(_qualify_name(branch_token, scope))
            output_keys.append(_normalize_name(output_path))
            continue

        branch_names.append(_qualify_name(token, scope))
        if mode == "pack":
            output_keys.append(_local_output_key(token))

    return Merge(
        label=label,
        line_no=line_no,
        mode=mode,
        branch_names=tuple(branch_names),
        output_keys=tuple(output_keys) if mode == "pack" else None,
    )


def _qualify_name(token: str, scope: tuple[str, ...]) -> str:
    normalized = _normalize_name(token)
    if normalized.startswith("."):
        return _join_scope(scope, normalized[1:])
    if "." in normalized:
        return normalized
    return _join_scope(scope, normalized)


def _local_output_key(token: str) -> str:
    normalized = _normalize_name(token)
    return normalized.rsplit(".", 1)[-1]


def _normalize_name(token: str) -> str:
    return token.replace("::", ".")


def _join_scope(scope: tuple[str, ...], name: str) -> str:
    if not scope:
        return name
    return ".".join((*scope, name))


def _try_recover_program(source: str, initial_error: ParseError) -> Program | None:
    seen = {source}
    queue: list[tuple[str, ParseError]] = [(source, initial_error)]
    successes: list[Program] = []

    while queue and len(seen) <= 12:
        current_source, current_error = queue.pop(0)
        for candidate_source in _repair_candidates(current_source, current_error):
            if candidate_source in seen:
                continue
            seen.add(candidate_source)
            try:
                program = _parse_program_strict(candidate_source)
            except ParseError as next_error:
                queue.append((candidate_source, next_error))
            else:
                successes.append(program)

    if len(successes) == 1:
        return successes[0]
    return None


def _repair_candidates(source: str, error: ParseError) -> list[str]:
    text = str(error)
    candidates: list[str] = []
    if "missing a closing endns." in text:
        candidates.append(source.rstrip() + "\nendns\n")
    if "missing a closing end." in text:
        candidates.append(source.rstrip() + "\nend\n")
    return candidates


def _resolve_program_references(
    main_flow: tuple[StatementT, ...],
    branches: dict[str, Branch],
) -> tuple[tuple[StatementT, ...], dict[str, Branch]]:
    branch_names = set(branches)
    resolved_main_flow = _resolve_flow(main_flow, branch_names)
    resolved_branches = {
        name: Branch(name=branch.name, flow=_resolve_flow(branch.flow, branch_names), line_no=branch.line_no)
        for name, branch in branches.items()
    }
    return resolved_main_flow, resolved_branches


def _resolve_flow(flow: tuple[StatementT, ...], branch_names: set[str]) -> tuple[StatementT, ...]:
    resolved: list[StatementT] = []
    for index, statement in enumerate(flow):
        if isinstance(statement, Fork):
            resolved_branch_names = tuple(_resolve_branch_name(name, branch_names) for name in statement.branch_names)
            if index + 1 < len(flow):
                next_statement = flow[index + 1]
                if isinstance(next_statement, Merge) and next_statement.mode == "pack" and next_statement.output_keys:
                    next_resolved_branch_names = tuple(
                        _resolve_branch_name(name, branch_names) for name in next_statement.branch_names
                    )
                    next_resolved_branch_names, next_output_keys = _maybe_compact_pack_alias_pairs(
                        next_statement.mode,
                        next_resolved_branch_names,
                        next_statement.output_keys,
                    )
                    if (
                        len(resolved_branch_names) == len(next_output_keys)
                        and tuple(_local_output_key(name) for name in resolved_branch_names) == next_output_keys
                    ):
                        resolved_branch_names = next_resolved_branch_names
            resolved.append(
                Fork(
                    label=statement.label,
                    line_no=statement.line_no,
                    depth=statement.depth,
                    raw_depth=statement.raw_depth,
                    branch_names=resolved_branch_names,
                )
            )
        elif isinstance(statement, Merge):
            resolved_branch_names = tuple(_resolve_branch_name(name, branch_names) for name in statement.branch_names)
            resolved_branch_names, output_keys = _maybe_compact_pack_alias_pairs(
                statement.mode,
                resolved_branch_names,
                statement.output_keys,
            )
            resolved.append(
                Merge(
                    label=statement.label,
                    line_no=statement.line_no,
                    mode=statement.mode,
                    branch_names=resolved_branch_names,
                    output_keys=output_keys,
                )
            )
        elif isinstance(statement, Record):
            resolved_branch_names = tuple(
                _resolve_record_branch_name(branch_name, field_key, branch_names)
                for branch_name, field_key in zip(statement.branch_names, statement.field_keys, strict=True)
            )
            resolved.append(
                Record(
                    label=statement.label,
                    line_no=statement.line_no,
                    output_name=statement.output_name,
                    branch_names=resolved_branch_names,
                    field_keys=statement.field_keys,
                )
            )
        else:
            resolved.append(statement)
    return tuple(resolved)


def _resolve_branch_name(name: str, branch_names: set[str]) -> str:
    if name in branch_names:
        return name
    variants = _branch_name_variants(name)
    for candidate in variants:
        if candidate in branch_names:
            return candidate

    for candidate in variants:
        suffix_matches = [branch_name for branch_name in branch_names if branch_name.endswith(f".{candidate}")]
        if len(suffix_matches) == 1:
            return suffix_matches[0]
    return name


def _branch_name_variants(name: str) -> list[str]:
    parts = name.split(".")
    variants: list[str] = []

    def add(value: str) -> None:
        if value and value not in variants:
            variants.append(value)

    add(name)

    for index in range(1, len(parts)):
        add(".".join(parts[index:]))

    leaf = parts[-1]
    leaf_tokens = [token for token in leaf.split("_") if token]
    for index in range(1, len(leaf_tokens)):
        leaf_variant = "_".join(leaf_tokens[index:])
        add(leaf_variant)
        if len(parts) > 1:
            add(".".join([*parts[:-1], leaf_variant]))

    return variants


def _resolve_record_branch_name(name: str, field_key: str, branch_names: set[str]) -> str:
    resolved = _resolve_branch_name(name, branch_names)
    if resolved in branch_names:
        return resolved

    if field_key in branch_names:
        return field_key

    field_base = _singularize(field_key)
    candidate_patterns = (
        f"{field_key}_panel",
        f"{field_base}_panel",
        f"{field_key}_ns.panel",
        f"{field_base}_ns.panel",
    )
    matches = [candidate for candidate in candidate_patterns if candidate in branch_names]
    if len(matches) == 1:
        return matches[0]

    return resolved


def _maybe_compact_pack_alias_pairs(
    mode: str,
    branch_names: tuple[str, ...],
    output_keys: tuple[str, ...] | None,
) -> tuple[tuple[str, ...], tuple[str, ...] | None]:
    if mode != "pack" or output_keys is None or len(branch_names) < 2 or len(branch_names) % 2 != 0:
        return branch_names, output_keys

    compact_branches: list[str] = []
    compact_output_keys: list[str] = []

    for index in range(0, len(branch_names), 2):
        left_branch = branch_names[index]
        right_branch = branch_names[index + 1]
        left_key = output_keys[index]
        right_key = output_keys[index + 1]

        if left_branch != right_branch:
            return branch_names, output_keys
        if right_key != _local_output_key(right_branch):
            return branch_names, output_keys
        if left_key == right_key:
            return branch_names, output_keys

        compact_branches.append(left_branch)
        compact_output_keys.append(left_key)

    return tuple(compact_branches), tuple(compact_output_keys)


def _singularize(name: str) -> str:
    return name[:-1] if name.endswith("s") and len(name) > 1 else name
