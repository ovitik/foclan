import json
from pathlib import Path

from foclan.extensions import HostExtension
from foclan_io import register_host_functions
from foclan_io import io_ops


def test_register_host_functions_returns_extension() -> None:
    extension = register_host_functions()
    assert isinstance(extension, HostExtension)
    assert extension.name == "foclan-io"
    assert "read_json" in extension.host_functions


def test_read_write_json_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    write_result = io_ops.write_json({"path": str(path), "content": {"ok": True, "items": [1, 2]}})
    assert write_result["written"] is True
    assert io_ops.read_json({"path": str(path)}) == {"ok": True, "items": [1, 2]}


def test_read_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    path.write_text('{"a":1}\n{"a":2}\n', encoding="utf-8")
    assert io_ops.read_jsonl({"path": str(path)}) == [{"a": 1}, {"a": 2}]


def test_read_write_csv(tmp_path: Path) -> None:
    path = tmp_path / "rows.csv"
    io_ops.write_csv({"path": str(path), "rows": [{"name": "Alice", "city": "Prague"}, {"name": "Bob", "city": "Brno"}]})
    assert io_ops.read_csv({"path": str(path)}) == [
        {"name": "Alice", "city": "Prague"},
        {"name": "Bob", "city": "Brno"},
    ]
