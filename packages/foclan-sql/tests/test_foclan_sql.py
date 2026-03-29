from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from foclan_sql.sql_ops import SQLConfigError, register_host_functions, sql_exec, sql_query


def test_register_host_functions_returns_extension() -> None:
    extension = register_host_functions()
    assert extension.name == "foclan-sql"
    assert set(extension.host_functions) == {"sql_query", "sql_exec"}


def test_sql_query_and_exec_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    connection = sqlite3.connect(db_path)
    connection.execute("create table users(id integer primary key, name text, city text)")
    connection.commit()
    connection.close()

    exec_result = sql_exec(
        {
            "path": str(db_path),
            "sql": "insert into users(name, city) values (:name, :city)",
            "params": {"name": "Ada", "city": "Prague"},
        }
    )
    assert exec_result["ok"] is True
    assert exec_result["rowcount"] == 1

    rows = sql_query(
        {
            "path": str(db_path),
            "sql": "select name, city from users order by name",
        }
    )
    assert rows == [{"name": "Ada", "city": "Prague"}]


def test_sql_query_supports_dsn_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "env.db"
    connection = sqlite3.connect(db_path)
    connection.execute("create table items(id integer primary key, label text)")
    connection.execute("insert into items(label) values ('x')")
    connection.commit()
    connection.close()

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    rows = sql_query(
        {
            "dsn_env": "DATABASE_URL",
            "sql": "select label from items",
        }
    )
    assert rows == [{"label": "x"}]


def test_sql_query_rejects_missing_connection() -> None:
    with pytest.raises(SQLConfigError, match="must include one of"):
        sql_query({"sql": "select 1"})
