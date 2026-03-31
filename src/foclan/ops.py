from __future__ import annotations

import builtins
import json
from dataclasses import dataclass
from typing import Any, Callable

from .errors import RuntimeError as FocusRuntimeError
from .errors import TypeError as FocusTypeError
from .errors import UnknownOp

HostFunction = Callable[..., Any]


@dataclass(frozen=True)
class BuiltinSpec:
    min_args: int
    max_args: int | None


BUILTIN_SPECS: dict[str, BuiltinSpec] = {
    "id": BuiltinSpec(0, 0),
    "const": BuiltinSpec(1, None),
    "get": BuiltinSpec(1, None),
    "len": BuiltinSpec(0, 0),
    "keys": BuiltinSpec(0, 0),
    "vals": BuiltinSpec(0, 0),
    "eq": BuiltinSpec(1, None),
    "neq": BuiltinSpec(1, None),
    "gt": BuiltinSpec(1, None),
    "lt": BuiltinSpec(1, None),
    "not": BuiltinSpec(0, 0),
    "keep": BuiltinSpec(1, 1),
    "drop": BuiltinSpec(1, 1),
    "where_true": BuiltinSpec(1, 1),
    "where_false": BuiltinSpec(1, 1),
    "where_eq": BuiltinSpec(2, None),
    "where_neq": BuiltinSpec(2, None),
    "where_gt": BuiltinSpec(2, None),
    "where_lt": BuiltinSpec(2, None),
    "map": BuiltinSpec(1, 1),
    "group": BuiltinSpec(1, 1),
    "count": BuiltinSpec(0, 0),
    "count_by": BuiltinSpec(1, 1),
    "count_rows": BuiltinSpec(1, 1),
    "count_map": BuiltinSpec(1, 1),
    "top": BuiltinSpec(1, 1),
    "argmax": BuiltinSpec(1, 1),
    "argmin": BuiltinSpec(1, 1),
    "most_common": BuiltinSpec(1, 1),
    "sort": BuiltinSpec(0, 1),
    "sort_desc": BuiltinSpec(0, 1),
    "take": BuiltinSpec(1, 1),
    "flat": BuiltinSpec(0, 0),
    "uniq": BuiltinSpec(0, 0),
    "zip_fields": BuiltinSpec(2, 2),
    "lower": BuiltinSpec(0, 0),
    "upper": BuiltinSpec(0, 0),
    "trim": BuiltinSpec(0, 0),
    "split": BuiltinSpec(1, None),
    "join": BuiltinSpec(1, None),
    "call": BuiltinSpec(1, None),
}

ZERO_ARG_ELEMENT_OPS = {"id", "lower", "upper", "trim", "len", "keys", "vals", "not"}


def apply_builtin(
    focus: Any,
    op: str,
    args: tuple[str, ...],
    host_functions: dict[str, HostFunction] | None = None,
) -> Any:
    if op not in BUILTIN_SPECS:
        raise UnknownOp(f"Unknown op '{op}'.")

    if op == "id":
        return focus
    if op == "const":
        return parse_literal(_join_args(args))
    if op == "get":
        return _get(focus, parse_literal(_join_args(args)))
    if op == "len":
        try:
            return len(focus)
        except builtins.TypeError as exc:
            raise FocusTypeError("len expects a sized focus.") from exc
    if op == "keys":
        return list(_require_dict(focus, "keys").keys())
    if op == "vals":
        return list(_require_dict(focus, "vals").values())
    if op == "eq":
        return focus == parse_literal(_join_args(args))
    if op == "neq":
        return focus != parse_literal(_join_args(args))
    if op == "gt":
        return focus > parse_literal(_join_args(args))
    if op == "lt":
        return focus < parse_literal(_join_args(args))
    if op == "not":
        return not focus
    if op == "keep":
        field = args[0]
        return [item for item in _require_list(focus, "keep") if _truthy_field(item, field)]
    if op == "drop":
        field = args[0]
        return [item for item in _require_list(focus, "drop") if not _truthy_field(item, field)]
    if op == "where_true":
        return [item for item in _require_record_list(focus, "where_true") if bool(item.get(args[0]))]
    if op == "where_false":
        return [item for item in _require_record_list(focus, "where_false") if not bool(item.get(args[0]))]
    if op == "where_eq":
        field = args[0]
        target = parse_literal(_join_args(args[1:]))
        return [item for item in _require_record_list(focus, "where_eq") if item.get(field) == target]
    if op == "where_neq":
        field = args[0]
        target = parse_literal(_join_args(args[1:]))
        return [item for item in _require_record_list(focus, "where_neq") if item.get(field) != target]
    if op == "where_gt":
        field = args[0]
        target = parse_literal(_join_args(args[1:]))
        return [item for item in _require_record_list(focus, "where_gt") if item.get(field) > target]
    if op == "where_lt":
        field = args[0]
        target = parse_literal(_join_args(args[1:]))
        return [item for item in _require_record_list(focus, "where_lt") if item.get(field) < target]
    if op == "map":
        selector = args[0]
        items = _require_list(focus, "map")
        return [_map_item(item, selector) for item in items]
    if op == "group":
        field = args[0]
        return _group_by(_require_list(focus, "group"), field)
    if op == "count":
        return _count(focus)
    if op == "count_by":
        return _count(_group_by(_require_record_list(focus, "count_by"), args[0]))
    if op == "count_rows":
        return _count_rows(_require_record_list(focus, "count_rows"), args[0])
    if op == "count_map":
        return _count_map(_require_record_list(focus, "count_map"), args[0])
    if op == "top":
        field = args[0]
        items = _require_list(focus, "top")
        if not items:
            raise FocusRuntimeError("top expects a non-empty list.")
        return max(items, key=lambda item: _sort_key(item, field))
    if op == "argmax":
        field = args[0]
        items = _require_list(focus, "argmax")
        if not items:
            raise FocusRuntimeError("argmax expects a non-empty list.")
        return max(items, key=lambda item: _sort_key(item, field))
    if op == "argmin":
        field = args[0]
        items = _require_list(focus, "argmin")
        if not items:
            raise FocusRuntimeError("argmin expects a non-empty list.")
        return min(items, key=lambda item: _sort_key(item, field))
    if op == "most_common":
        field = args[0]
        counted = _count(_group_by(_require_record_list(focus, "most_common"), field))
        if not counted:
            raise FocusRuntimeError("most_common expects a non-empty list.")
        return max(counted, key=lambda item: _sort_key(item, "count")).get(field)
    if op == "sort":
        items = _require_list(focus, "sort")
        if args and items and all(isinstance(item, dict) for item in items):
            field = args[0]
            return sorted(items, key=lambda item: _sort_key(item, field))
        if items and all(isinstance(item, dict) for item in items):
            if all("count" in item for item in items):
                return sorted(
                    items,
                    key=lambda item: (-int(item.get("count", 0)), json.dumps(item, sort_keys=True, ensure_ascii=False)),
                )
            return sorted(items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
        return sorted(items)
    if op == "sort_desc":
        items = _require_list(focus, "sort_desc")
        if args and items and all(isinstance(item, dict) for item in items):
            field = args[0]
            return sorted(
                items,
                key=lambda item: (_sort_key(item, field), json.dumps(item, sort_keys=True, ensure_ascii=False)),
                reverse=True,
            )
        if items and all(isinstance(item, dict) for item in items):
            if all("count" in item for item in items):
                return sorted(
                    items,
                    key=lambda item: (-int(item.get("count", 0)), json.dumps(item, sort_keys=True, ensure_ascii=False)),
                )
            return list(reversed(sorted(items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))))
        return sorted(items, reverse=True)
    if op == "take":
        count = parse_literal(args[0])
        if not isinstance(count, int):
            raise FocusTypeError("take expects an integer count.")
        if isinstance(focus, list):
            return focus[:count]
        if isinstance(focus, str):
            return focus[:count]
        raise FocusTypeError("take expects a list or string focus.")
    if op == "flat":
        flattened: list[Any] = []
        for item in _require_list(focus, "flat"):
            if isinstance(item, list):
                flattened.extend(item)
            else:
                flattened.append(item)
        return flattened
    if op == "uniq":
        seen: set[str] = set()
        unique: list[Any] = []
        for item in _require_list(focus, "uniq"):
            marker = json.dumps(item, sort_keys=True, ensure_ascii=False, default=repr)
            if marker in seen:
                continue
            seen.add(marker)
            unique.append(item)
        return unique
    if op == "zip_fields":
        field_a, field_b = args
        return [[item.get(field_a), item.get(field_b)] for item in _require_record_list(focus, "zip_fields")]
    if op == "lower":
        return _require_text(focus, "lower").lower()
    if op == "upper":
        return _require_text(focus, "upper").upper()
    if op == "trim":
        return _require_text(focus, "trim").strip()
    if op == "split":
        return _require_text(focus, "split").split(_string_arg(args))
    if op == "join":
        return _string_arg(args).join(str(item) for item in _require_list(focus, "join"))
    if op == "call":
        if not host_functions or args[0] not in host_functions:
            raise FocusRuntimeError(f"Unknown host function '{args[0]}'.")
        parsed_args = [parse_literal(arg) for arg in args[1:]]
        return host_functions[args[0]](focus, *parsed_args)

    raise UnknownOp(f"Unknown op '{op}'.")


def parse_literal(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _join_args(args: tuple[str, ...]) -> str:
    return " ".join(args)


def _string_arg(args: tuple[str, ...]) -> str:
    value = parse_literal(_join_args(args))
    return str(value)


def _require_dict(value: Any, op: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FocusTypeError(f"{op} expects a record focus.")
    return value


def _require_list(value: Any, op: str) -> list[Any]:
    if not isinstance(value, list):
        raise FocusTypeError(f"{op} expects a list focus.")
    return value


def _require_text(value: Any, op: str) -> str:
    if not isinstance(value, str):
        raise FocusTypeError(f"{op} expects a text focus.")
    return value


def _require_record_list(value: Any, op: str) -> list[dict[str, Any]]:
    items = _require_list(value, op)
    if not all(isinstance(item, dict) for item in items):
        raise FocusTypeError(f"{op} expects a list of records.")
    return items


def _truthy_field(item: Any, field: str) -> bool:
    if not isinstance(item, dict):
        raise FocusTypeError("keep/drop expect a list of records.")
    return bool(item.get(field))


def _map_item(item: Any, selector: str) -> Any:
    if isinstance(item, dict):
        if selector in item:
            return item.get(selector)
        if selector in ZERO_ARG_ELEMENT_OPS:
            return apply_builtin(item, selector, ())
        return item.get(selector)
    if selector in ZERO_ARG_ELEMENT_OPS:
        return apply_builtin(item, selector, ())
    raise FocusTypeError(f"map field '{selector}' expects record items.")


def _group_by(items: list[Any], field: str) -> list[dict[str, Any]]:
    groups: dict[Any, list[Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise FocusTypeError("group expects a list of records.")
        key = item.get(field)
        groups.setdefault(key, []).append(item)

    grouped: list[dict[str, Any]] = []
    for key, group_items in groups.items():
        grouped.append({"key": key, field: key, "items": group_items})
    return grouped


def _count(focus: Any) -> Any:
    if isinstance(focus, list):
        if focus and all(
            isinstance(item, dict) and isinstance(item.get("items"), list) and "key" in item
            for item in focus
        ):
            counted: list[dict[str, Any]] = []
            for item in focus:
                enriched = dict(item)
                enriched["count"] = len(item["items"])
                counted.append(enriched)
            return counted
        return len(focus)
    if isinstance(focus, dict) and isinstance(focus.get("items"), list):
        return len(focus["items"])
    raise FocusTypeError("count expects a list or a grouped record.")


def _count_rows(items: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    counts: dict[Any, int] = {}
    for item in items:
        key = item.get(field)
        counts[key] = counts.get(key, 0) + 1
    return [{field: key, "count": count} for key, count in counts.items()]


def _count_map(items: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = _object_key(item.get(field))
        counts[key] = counts.get(key, 0) + 1
    return counts


def _sort_key(item: Any, field: str) -> Any:
    if not isinstance(item, dict):
        raise FocusTypeError("top/sort with a field expect record items.")
    return item.get(field)


def _get(focus: Any, key: Any) -> Any:
    if isinstance(focus, dict):
        return focus.get(str(key), focus.get(key))
    if isinstance(focus, list) and isinstance(key, int):
        return focus[key]
    raise FocusTypeError("get expects a record focus or a list index.")


def _object_key(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return "null"
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=repr)
