from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from foclan.extensions import HostExtension


class SQLConfigError(ValueError):
    pass


class SQLOperationError(RuntimeError):
    pass


def register_host_functions() -> HostExtension:
    return HostExtension(
        name="foclan-sql",
        description="Run deterministic SQL query and exec steps from Foclan.",
        host_functions={
            "sql_query": sql_query,
            "sql_exec": sql_exec,
        },
    )


def sql_query(focus: Any, *args: Any) -> list[dict[str, Any]]:
    _reject_args("sql_query", args)
    request = _normalize_request(focus)
    sql = _require_sql(request)
    params = _normalize_params(request.get("params"))
    with _open_connection(request) as connection:
        try:
            cursor = connection.execute(sql, params)
            rows = cursor.fetchall()
        except sqlite3.Error as exc:
            raise SQLOperationError(f"SQL query failed: {exc}") from exc
    return [dict(row) for row in rows]


def sql_exec(focus: Any, *args: Any) -> dict[str, Any]:
    _reject_args("sql_exec", args)
    request = _normalize_request(focus)
    sql = _require_sql(request)
    params = _normalize_params(request.get("params"))
    with _open_connection(request) as connection:
        try:
            cursor = connection.execute(sql, params)
            connection.commit()
        except sqlite3.Error as exc:
            raise SQLOperationError(f"SQL exec failed: {exc}") from exc
    return {
        "rowcount": int(cursor.rowcount if cursor.rowcount != -1 else 0),
        "lastrowid": cursor.lastrowid,
        "ok": True,
    }


def _normalize_request(focus: Any) -> dict[str, Any]:
    if not isinstance(focus, dict):
        raise SQLConfigError("foclan-sql host functions expect a record focus.")
    return focus


def _require_sql(request: dict[str, Any]) -> str:
    sql = request.get("sql")
    if not isinstance(sql, str) or not sql.strip():
        raise SQLConfigError("SQL request must include non-empty string 'sql'.")
    return sql


def _normalize_params(value: Any) -> dict[str, Any] | list[Any] | tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return value
    raise SQLConfigError("'params' must be a record or list.")


def _open_connection(request: dict[str, Any]) -> sqlite3.Connection:
    connect_target, uri = _resolve_connection_target(request)
    try:
        connection = sqlite3.connect(connect_target, uri=uri)
    except sqlite3.Error as exc:
        raise SQLOperationError(f"Failed to open SQLite connection: {exc}") from exc
    connection.row_factory = sqlite3.Row
    return connection


def _resolve_connection_target(request: dict[str, Any]) -> tuple[str, bool]:
    if "path" in request:
        path = request["path"]
        if not isinstance(path, str) or not path.strip():
            raise SQLConfigError("'path' must be a non-empty string.")
        return str(Path(path)), False

    dsn = request.get("dsn")
    if dsn is None:
        dsn_env = request.get("dsn_env")
        if dsn_env is not None:
            if not isinstance(dsn_env, str) or not dsn_env.strip():
                raise SQLConfigError("'dsn_env' must be a non-empty string.")
            dsn = os.getenv(dsn_env)
            if not dsn:
                raise SQLConfigError(f"Missing required environment variable '{dsn_env}' for SQL connection.")

    if not isinstance(dsn, str) or not dsn.strip():
        raise SQLConfigError("SQL request must include one of: 'path', 'dsn', or 'dsn_env'.")

    if dsn == "sqlite:///:memory:":
        return ":memory:", False
    if dsn.startswith("sqlite:///"):
        return dsn[len("sqlite:///") :], False
    if dsn.startswith("file:"):
        return dsn, True

    raise SQLConfigError(
        "Unsupported SQL connection string. Use 'path', 'sqlite:///:memory:', 'sqlite:///path.db', or 'file:' URIs."
    )


def _reject_args(name: str, args: tuple[Any, ...]) -> None:
    if args:
        raise SQLConfigError(f"{name} does not accept positional arguments.")
