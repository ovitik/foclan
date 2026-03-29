from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from foclan.extensions import HostExtension


class IOConfigError(ValueError):
    pass


def register_host_functions() -> HostExtension:
    return HostExtension(
        name="foclan-io",
        description="Read and write text, JSON, JSONL, and CSV files from Foclan.",
        host_functions={
            "read_text": read_text,
            "write_text": write_text,
            "read_json": read_json,
            "write_json": write_json,
            "read_jsonl": read_jsonl,
            "read_csv": read_csv,
            "write_csv": write_csv,
        },
    )


def read_text(focus: Any, *args: Any) -> str:
    _reject_args("read_text", args)
    request = _normalize_request(focus)
    path = _require_path(request)
    encoding = str(request.get("encoding", "utf-8"))
    return path.read_text(encoding=encoding)


def write_text(focus: Any, *args: Any) -> dict[str, Any]:
    _reject_args("write_text", args)
    request = _normalize_request(focus)
    path = _require_path(request)
    if "content" not in request:
        raise IOConfigError("write_text requires 'content'.")
    encoding = str(request.get("encoding", "utf-8"))
    _ensure_parent(path)
    content = _stringify(request["content"])
    path.write_text(content, encoding=encoding)
    return {"path": str(path), "written": True, "bytes": path.stat().st_size}


def read_json(focus: Any, *args: Any) -> Any:
    _reject_args("read_json", args)
    request = _normalize_request(focus)
    path = _require_path(request)
    encoding = str(request.get("encoding", "utf-8"))
    return json.loads(path.read_text(encoding=encoding))


def write_json(focus: Any, *args: Any) -> dict[str, Any]:
    _reject_args("write_json", args)
    request = _normalize_request(focus)
    path = _require_path(request)
    if "content" not in request:
        raise IOConfigError("write_json requires 'content'.")
    encoding = str(request.get("encoding", "utf-8"))
    indent = int(request.get("indent", 2))
    _ensure_parent(path)
    path.write_text(json.dumps(request["content"], ensure_ascii=False, indent=indent), encoding=encoding)
    return {"path": str(path), "written": True, "bytes": path.stat().st_size}


def read_jsonl(focus: Any, *args: Any) -> list[Any]:
    _reject_args("read_jsonl", args)
    request = _normalize_request(focus)
    path = _require_path(request)
    encoding = str(request.get("encoding", "utf-8"))
    rows: list[Any] = []
    for line in path.read_text(encoding=encoding).splitlines():
        stripped = line.strip()
        if stripped:
            rows.append(json.loads(stripped))
    return rows


def read_csv(focus: Any, *args: Any) -> list[dict[str, str]]:
    _reject_args("read_csv", args)
    request = _normalize_request(focus)
    path = _require_path(request)
    encoding = str(request.get("encoding", "utf-8"))
    delimiter = str(request.get("delimiter", ","))
    with path.open("r", encoding=encoding, newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter=delimiter)]


def write_csv(focus: Any, *args: Any) -> dict[str, Any]:
    _reject_args("write_csv", args)
    request = _normalize_request(focus)
    path = _require_path(request)
    rows = request.get("rows")
    if not isinstance(rows, list):
        raise IOConfigError("write_csv requires 'rows' to be a list of records.")
    encoding = str(request.get("encoding", "utf-8"))
    delimiter = str(request.get("delimiter", ","))
    fieldnames = request.get("fieldnames")
    if fieldnames is None:
        fieldnames = _infer_fieldnames(rows)
    if not isinstance(fieldnames, list) or not all(isinstance(name, str) for name in fieldnames):
        raise IOConfigError("write_csv fieldnames must be a list of strings.")
    _ensure_parent(path)
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        for row in rows:
            if not isinstance(row, dict):
                raise IOConfigError("write_csv rows must be records.")
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    return {"path": str(path), "written": True, "rows": len(rows), "bytes": path.stat().st_size}


def _normalize_request(focus: Any) -> dict[str, Any]:
    if not isinstance(focus, dict):
        raise IOConfigError("foclan-io host functions expect a record focus.")
    return focus


def _require_path(request: dict[str, Any]) -> Path:
    path_value = request.get("path")
    if not isinstance(path_value, str) or not path_value.strip():
        raise IOConfigError("I/O request must include non-empty string 'path'.")
    return Path(path_value)


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _reject_args(name: str, args: tuple[Any, ...]) -> None:
    if args:
        raise IOConfigError(f"{name} does not accept positional arguments.")


def _infer_fieldnames(rows: list[Any]) -> list[str]:
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise IOConfigError("write_csv rows must be records.")
        for key in row:
            if not isinstance(key, str):
                raise IOConfigError("write_csv row keys must be strings.")
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    return fieldnames


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)
